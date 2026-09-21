"""
Sdílený klient pro TypeSafe Jev API.

Celé API je JEDEN endpoint a JEDEN tvar requestu:

    POST https://api.typesafe.ai/v1/systemone
    Authorization: Bearer <API_KEY>

    {
      "state":     <co se hodnotí>       -- string | object | array
      "model":     "jev-latest",
      "questions": {<id>: <otázka>, ...} -- mapa otázek, běží PARALELNĚ
    }

Odpověď má stejné klíče jako questions:

    {
      "model": "jev-1.13.0",
      "answers": {<id>: <odpověď>, ...},
      "usage": {"input_tokens": N, "output_tokens": M}
    }
"""

import json
import os
import time
from pathlib import Path

import requests

API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
REPO_DIR = Path(__file__).parent.parent  # kořen repozitáře


def load_api_key() -> str:
    """Načte klíč z .env v kořeni projektu (TYPESAFE_API_KEY=...)."""
    env_path = REPO_DIR / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TYPESAFE_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"TYPESAFE_API_KEY nenalezen v {env_path}")


def load_json(relative_path: str) -> dict:
    """Načte JSON z test/ a zahodí klíče začínající podtržítkem (komentáře)."""
    data = json.loads((REPO_DIR / "experiments" / relative_path).resolve().read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


def ask(state, questions: dict, api_key: str = None, timeout: int = 60,
        retries: int = 4) -> dict:
    """
    Jeden API call. Vrátí odpověď obohacenou o naměřenou latenci.

    state     -- text nebo struktura k vyhodnocení
    questions -- mapa {id: definice_otazky}; všechny běží paralelně v jednom callu

    Při síťovém timeoutu nebo přetížení (429/529) opakuje s exponenciálním
    odstupem -- při dlouhých bězích jinak spadne celá dávka na jednom výpadku.
    """
    if api_key is None:
        api_key = load_api_key()

    payload = {"state": state, "model": MODEL, "questions": questions}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    last_error = None
    for attempt in range(retries):
        if attempt:
            time.sleep(2 ** attempt)  # 2, 4, 8 s
        try:
            started = time.perf_counter()
            response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
            elapsed = time.perf_counter() - started

            if response.status_code in (429, 529):
                last_error = f"HTTP {response.status_code} (přetíženo)"
                continue
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:400]}")

            result = response.json()
            result["_latency_s"] = round(elapsed, 3)
            result["_attempts"] = attempt + 1
            return result

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = f"{type(exc).__name__}"

    raise RuntimeError(f"Nezdařilo se po {retries} pokusech: {last_error}")


def format_answer(answer: dict) -> str:
    """Čitelný jednořádkový zápis odpovědi podle jejího typu."""
    kind = answer["type"]

    if kind == "noul":
        # Noul nemá confidence -- jen pravděpodobnost ano (0-1).
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


def save_result(name: str, data) -> Path:
    """Uloží výsledek do test/results/ pro pozdější porovnání."""
    out_dir = REPO_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
