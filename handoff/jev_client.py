"""
Standalone client for the TypeSafe Jev System One API.

Self-contained on purpose: copy this single file anywhere and it works. It does
not import from the rest of this repository.

The whole API is ONE endpoint and ONE request shape:

    POST https://api.typesafe.ai/v1/systemone
    Authorization: Bearer <API_KEY>

    {
      "state":     <what is being judged>   -- string | object | array
      "model":     "jev-latest",
      "questions": {<id>: <question>, ...}  -- map of questions, run in PARALLEL
    }

The response uses the same keys you chose in `questions`:

    {
      "model": "jev-1.13.0",
      "answers": {<id>: <answer>, ...},
      "usage": {"input_tokens": N, "output_tokens": M}
    }

Key resolution order:
    1. explicit api_key argument
    2. TYPESAFE_API_KEY environment variable
    3. TYPESAFE_API_KEY=... in a .env file, searched upward from this file

Requires: requests
"""

import json
import os
import time
from pathlib import Path

import requests

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"

# Treat any difference below this as model noise, not an effect. Measured over
# eight identical calls per input; see reference/API.md section 4.
NOISE_FLOOR = 0.05


def load_api_key(api_key: str = None) -> str:
    """Resolve the API key from the argument, the environment, or a .env file."""
    if api_key:
        return api_key

    from_env = os.environ.get("TYPESAFE_API_KEY")
    if from_env:
        return from_env.strip()

    # Walk upward so the file works from a subdirectory too.
    for directory in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        env_path = directory / ".env"
        if not env_path.is_file():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TYPESAFE_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value

    raise RuntimeError(
        "No API key found. Set the TYPESAFE_API_KEY environment variable, "
        "or create a .env file containing TYPESAFE_API_KEY=..., "
        "or pass api_key= explicitly."
    )


def ask(state, questions: dict, api_key: str = None, timeout: int = 60,
        retries: int = 4) -> dict:
    """
    One API call. Returns the response enriched with the measured latency.

    state     -- text or structure to evaluate
    questions -- map of {id: question_definition}; all run in parallel in one call

    Retries with exponential backoff on network timeouts and on overload
    (429/529). Without this, a long batch dies on a single transient failure.
    """
    payload = {"state": state, "model": MODEL, "questions": questions}
    headers = {
        "Authorization": f"Bearer {load_api_key(api_key)}",
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(retries):
        if attempt:
            time.sleep(2 ** attempt)  # 2, 4, 8 s
        try:
            started = time.perf_counter()
            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            elapsed = time.perf_counter() - started

            if response.status_code in (429, 529):
                last_error = f"HTTP {response.status_code} (overloaded)"
                continue
            if response.status_code != 200:
                # 401 = bad key, 422 = malformed request; body names the field.
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:400]}")

            result = response.json()
            result["_latency_s"] = round(elapsed, 3)
            result["_attempts"] = attempt + 1
            return result

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = type(exc).__name__

    raise RuntimeError(f"Failed after {retries} attempts: {last_error}")


def format_answer(answer: dict) -> str:
    """Readable one-line rendering of an answer, by type."""
    kind = answer["type"]

    if kind == "noul":
        # A Noul has no confidence -- just P(yes), 0-1.
        return f"noul={answer['noul']:.3f}"

    if kind == "choice":
        probs = ", ".join(
            f"{opt}={p:.3f}"
            for opt, p in sorted(answer["probabilities"].items(), key=lambda x: -x[1])
        )
        return f"{answer['choice']} (conf={answer['confidence']:.3f}) [{probs}]"

    if kind == "score":
        probs = ", ".join(f"{lvl}={p:.3f}" for lvl, p in sorted(answer["probabilities"].items()))
        top = answer["legend"][str(round(answer["score"]))]
        return (
            f"score={answer['score']:.2f} ~ \"{top}\" "
            f"(conf={answer['confidence']:.3f}) [{probs}]"
        )

    return json.dumps(answer)


if __name__ == "__main__":
    # Smoke test: one state, all three primitives, one call.
    STATE = "The package arrived late and one item was missing."

    result = ask(STATE, {
        "negative": {
            "type": "noul",
            "instructions": "Does this text express negative emotion toward the company?",
            "criteria": {
                "true": "The author expresses dissatisfaction, anger, or frustration",
                "false": "The author is neutral, factual, or positive",
            },
        },
        "sentiment": {
            "type": "choice",
            "instructions": "What is the overall sentiment toward the company?",
            "criteria": {
                "positive": "Praise, satisfaction, or gratitude",
                "neutral": "Purely factual with no evaluative stance",
                "negative": "Complaint, criticism, or dissatisfaction",
                "mixed": "Contains both clearly positive and clearly negative evaluations",
            },
        },
        "anger": {
            "type": "score",
            "instructions": "How angry is the author of this text?",
            "criteria": [
                "Completely calm, no irritation at all",
                "Mildly irritated or inconvenienced",
                "Clearly frustrated and complaining",
                "Very angry, demanding, or hostile",
            ],
        },
    })

    print(f"model   {result['model']}")
    print(f"latency {result['_latency_s']} s   tokens {result['usage']['input_tokens']}")
    for qid, answer in result["answers"].items():
        print(f"  {qid:10} {format_answer(answer)}")
