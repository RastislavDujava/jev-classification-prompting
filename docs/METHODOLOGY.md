# Methodology

How these numbers were produced, and what they can and cannot support.

---

## The noise floor

Before measuring any effect, we measured the model's own variance: eight identical
calls with identical input.

| input | `noul` spread | `score` spread | `choice` |
|---|---|---|---|
| mild complaint | 0.030 | 0.020 | stable |
| mixed review | 0.010 | 0.050 | stable |
| polite anger | **0.000** | 0.040 | stable |

**The model is not bit-deterministic.** It varies by ±0.01–0.03 between identical runs.

Everything in this repo therefore uses **0.05 as a noise floor**. A difference smaller
than that is not reported as an effect.

Some measurements *are* perfectly stable — the key cultural-norm pair returned 0.980
six times and 0.130 six times with zero variance. Determinism cannot be assumed in
general, but it does occur.

---

## Runs and aggregation

- **5–10 runs per variant**, depending on how much the result mattered
- **Medians, not means**, for latency — a single network spike would distort a mean
- **Means for values**, since the model's own variance is small and symmetric
- **Spread reported** (max − min) so instability is visible rather than hidden

---

## Interleaving

When comparing variants, runs are **interleaved round-robin** rather than grouped:

```
round 1: A, B, C, D
round 2: A, B, C, D
...
```

Not:

```
A ×10, then B ×10, ...
```

**Why:** these calls cross the Atlantic. If the network slowed down halfway through a
grouped run, the entire slowdown would land on the later variants and look exactly
like an effect of whatever we changed.

---

## What counts as "proven"

In the six-domain run, a pair counts as proven only when **both** hold:

1. The number of correct answers increased (the decision boundary was crossed)
2. The shift exceeded the 0.05 noise floor

A number moving without a decision changing is reported as "values moved, decision
didn't" — it is not a result.

---

## Controls

Wherever a claim could have a simpler explanation, there is a control:

| Claim | Control |
|---|---|
| "Examples change the answer" | Semantically neutral filler of the same length, which changed nothing (0.013) |
| "The cultural norm calibrates" | Boundary cases that must **not** move — they moved the other way, 3/3 |
| "The scale is meaningful" | A story all profiles agree on — spread 0.019 |
| "Criteria numbers are ignored" | Identical descriptions, inverted numbers — spread 0.045 |
| "The bias is real" | Paired questions with near-identical wording and opposite correct answers |

A result without a control is stated as an observation, not a finding.

---

## Threshold

Unless stated otherwise, **0.5** separates yes from no for Noul answers, and Score
values are normalised to 0–1 by dividing by the top level index.

This is a convention for reporting, not a recommendation. In production, thresholds
should be tuned on your own labelled data, and the uncertain band routed to a human.

---

## Quantities that must not be mixed

**A Noul value and a Score value are different quantities.**

- Noul returns the **probability that the answer is yes**
- Score returns a **position on a scale**

An earlier draft of finding 03 subtracted one from the other and reported "a difference
of 0.49". That was wrong and is corrected in the document, with the original claim left
visible. What stands is that the two question types lead to **opposite operational
decisions** on the same text — which is a statement about decisions, not about the
difference between two numbers.

Similarly, `confidence` measures how concentrated a probability distribution is.
It is **not** the probability of being correct.

---

## Known weaknesses

| Weakness | Consequence |
|---|---|
| **Small samples** (5–15 per domain) | Demonstrates mechanisms, not accuracy. A small effect would be invisible. |
| **Single annotator** | Expected answers are one person's judgement. On ambiguous items this is stated. |
| **Author wrote both the texts and the criteria** | Risk of unconsciously writing inputs that suit the hypothesis. Controls mitigate but don't eliminate this. |
| **One model version** | `jev-1.13.0`. The version is recorded in every document. |
| **Latency measured from Czechia** | Reflects distance to the US region, not model speed. |
| **No held-out set** | Criteria were written, tested, and sometimes adjusted on the same items. |

That last one matters most. For a production classifier, write the criteria on one set
and measure on another you haven't seen.

---

## Reproducing

```bash
pip install -r requirements.txt
cp .env.example .env     # add your key
python experiments/01_primitives.py
```

Every script runs without arguments and writes raw JSON to `results/`. Numbers in
`findings/` can be traced back to the call that produced them.

Total cost of the full suite: **about $0.05**.

Running it yourself will produce slightly different numbers — that is the point of
reporting a noise floor.
