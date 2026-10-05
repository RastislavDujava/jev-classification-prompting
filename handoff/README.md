# Jev API — handoff pack

Everything another session needs to work with the TypeSafe Jev API, in one folder.
Self-contained: nothing here imports from the rest of this repository.

**No API key is included.** See [Getting a key running](#getting-a-key-running) below.

---

## Read in this order

| # | File | Why |
|---|---|---|
| 1 | [reference/API.md](reference/API.md) | The whole API on one screen, plus every number we measured. Start here. |
| 2 | [jev_client.py](jev_client.py) | Working client, ~150 lines. Run it directly as a smoke test. |
| 3 | [official-skill/SKILL.md](official-skill/SKILL.md) | TypeSafe's own agent skill — their house style for writing questions. |
| 4 | [reference/LIMITY_criteria.cs.md](reference/LIMITY_criteria.cs.md) | Hard limits, documented vs. verified against the live API. 🇨🇿 |
| 5 | [official-docs/](official-docs/) | Full vendor documentation, 22 files. Reference, not reading. |
| 6 | [reference/PRIKLADY.cs.md](reference/PRIKLADY.cs.md) | Line-by-line walkthrough of a request for a newcomer. 🇨🇿 |

Findings from our own research live one level up in [../findings/](../findings/) and
[../README.md](../README.md). This folder is the API toolkit; that is the research.

---

## The thirty-second version

One endpoint. One request shape. Nothing else to learn.

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

```json
{
  "state":     "the text being judged",
  "model":     "jev-latest",
  "questions": { "my_id": { "type": "noul", "instructions": "..." } }
}
```

```json
{
  "model":   "jev-1.13.0",
  "answers": { "my_id": { "type": "noul", "noul": 0.65 } },
  "usage":   { "input_tokens": 494, "output_tokens": 81 }
}
```

Jev is **not generative**. It returns typed decisions with probabilities — never text.

### Three primitives

| Type | Returns | `criteria` shape | Has `confidence` |
|---|---|---|---|
| **Noul** | `noul`: P(answer is yes), 0–1 | optional `{true, false}` | **no** |
| **Choice** | `choice` + `probabilities` summing to 1 | required map, ≤ 255 options | yes |
| **Score** | `score`: weighted average + `legend` + `probabilities` | required **ordered array**, 2–10 levels | yes |

Each question has three parts: `type` (which primitive), `instructions` (what to judge),
`criteria` (what the answers mean).

---

## Six things that will bite you

1. **Question IDs are never sent to the model.** Naming a question `is_angry` while
   `instructions` asks something else means the model follows `instructions`. The entire
   meaning has to live inside the question.

2. **Noul 0.5 means "yes and no are equally likely"** — not "medium intensity". This is
   the single most common mistake.

3. **The noise floor is 0.05.** The model is not bit-deterministic; identical calls vary
   by ±0.01–0.03. Never treat a smaller difference as an effect, and never build
   thresholds on three decimal places.

4. **Questions run in parallel and cannot see each other.** Twenty questions cost roughly
   the latency of one, because `state` is sent once and shared. Batch anything independent.

5. **Noul and Score are different quantities.** One is a probability, the other a position
   on a scale. Do not subtract them. A threshold tuned on a Noul does not transfer to a
   Choice, and `P(x) + P(¬x)` does not equal 1.

6. **`confidence` is not the probability of being correct.** It measures how concentrated
   the distribution is. Use it to route, not to trust.

---

## Where to put the prompt engineering

This is the main finding of the research in this repo, and it is worth knowing before
writing a single question:

> **`criteria` carries the effect. `instructions` is nearly inert.**
> In an ablation on the same input, rewriting `instructions` moved the result by −0.04
> (noise). Rewriting `criteria` moved it by **−0.82**.

So when a classification comes back wrong, the fix almost always belongs in `criteria` —
in what the answers *mean* — not in rephrasing the question. Concrete lists and named
boundary cases move the model; stated attitudes ("be lenient") do not. For a Score, each
rung must describe a **situation**, not a degree: *"real danger with a lasting
consequence, resolved by the end"* works, *"moderately severe"* gives the model nothing
to match against.

Full evidence: [../findings/01-criteria-ablation.cs.md](../findings/01-criteria-ablation.cs.md).

---

## Getting a key running

The key is **not** in this folder and must not be committed. `.env` is gitignored at the
repo root.

```bash
pip install requests

# either
export TYPESAFE_API_KEY=apikey_...        # PowerShell: $env:TYPESAFE_API_KEY="apikey_..."
# or create a .env file anywhere at or above this folder, containing
#   TYPESAFE_API_KEY=apikey_...

python jev_client.py
```

`jev_client.py` resolves the key from, in order: an explicit `api_key=` argument, the
`TYPESAFE_API_KEY` environment variable, then a `.env` file searched upward from the
client's own location.

Expected output (your numbers will differ slightly — that is the noise floor):

```
model   jev-1.13.0
latency 0.885 s   tokens 494
  negative   noul=0.650
  sentiment  negative (conf=0.990) [negative=0.990, neutral=0.010, ...]
  anger      score=1.10 ~ "Mildly irritated or inconvenienced" (conf=0.870)
```

---

## Operational facts

| | |
|---|---|
| Endpoint | `POST https://api.typesafe.ai/v1/systemone` |
| Auth | `Authorization: Bearer <key>` |
| Model pinned at | `jev-1.13.0` (requested as `jev-latest`) |
| Price | **$0.042 / 1M input tokens, output free** — a ~500-token call is ~$0.00002 |
| Latency | median ~0.9–1.2 s from Czechia, occasional spikes to 10 s. Set a timeout and retry. |
| Region | US only; no EU region. The latency above is distance, not model speed. |
| Rate limits | 1,200 requests/min · 250,000 tokens/s |
| Context | 64k tokens total · 32k for `state` + the longest single question |
| Verified caps | 255 Choice options (256 fails) · 10 Score levels (11 fails) · 32,796 tokens OK |
| `criteria` length | **no separate limit** — 191,750 characters accepted |
| Input | text only |

### Errors

| Status | Meaning | Action |
|---|---|---|
| `401` | bad key | check the `Authorization` header |
| `422` | malformed request | the body names the offending field |
| `429` | rate limited | exponential backoff |
| `529` | overloaded | backoff and retry |

`jev_client.py` already retries 429/529 and network timeouts with 2/4/8 s backoff.

---

## Is Jev the right tool?

Six questions. Five or six yes means a good fit; three or four means decompose it;
zero to two means use something else.

1. Is the AI *deciding*, not *creating*?
2. Can the answer space be defined up front?
3. Is it one focused judgement?
4. Is all the information in `state`?
5. Could an expert judge it quickly?
6. Will software consume the result directly?

> **Code calculates. Jev judges. Reasoning models reason and generate.**

Known weak spots: literal reading of under-specified conditions, arithmetic and counting,
date and time reasoning, indirection (a property of a property), large noisy `state`,
and anything generative. Details in
[official-docs/model-jaggedness_jev-1.13.md](official-docs/model-jaggedness_jev-1.13.md).

---

## Provenance

- Vendor docs mirrored 19 Sep 2026 from docs.typesafe.ai; the official skill is MIT,
  see [official-skill/LICENSE](official-skill/LICENSE). Links *inside* `official-docs/`
  are site-absolute (`/primitives`) and won't resolve locally — the filenames map onto
  those paths, so `/primitives/choice` is `primitives_choice.md`. A few of those pages
  were not mirrored; check docs.typesafe.ai for them.
- All measured numbers come from real runs in this repo against `jev-1.13.0`, not from
  the documentation. Raw JSON in [../results/](../results/), method and known weaknesses
  in [../docs/METHODOLOGY.md](../docs/METHODOLOGY.md).
- Three files are Czech, marked 🇨🇿 above. Everything else is English.
