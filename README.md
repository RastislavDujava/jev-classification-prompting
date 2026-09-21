# Jev Classification Research

**How much of a classifier's behaviour is yours to define?**

Reproducible experiments on [TypeSafe's Jev](https://docs.typesafe.ai/), a System One
model that returns typed decisions instead of text. Every number here comes from a real
API call, and every experiment runs with one command.

> **Status:** active research, started 21 September 2026 — six days after Jev's launch.
> More experiments land over the next two weeks.

---

## The short version

A classifier draws a line somewhere. If you don't write that line, it was written for
you — by training data and by the model authors' choices.

**That default line is not neutral. It belongs to someone.** These experiments measure
whose it is, how far it sits from what real people want, and how much of it you can move.

Across six domains and 1,180 API calls:

| | naive question | criteria written properly |
|---|---|---|
| **Accuracy** | **70%** (57/82) | **96%** (79/82) |

The gap is not the model getting smarter. It's the difference between accepting the
model's built-in norm and stating your own.

---

## Main findings

### 1. `criteria` is the strongest lever in the API

Same text, same question, different definition of what counts as vulgar:

| | without a cultural norm | with one |
|---|---|---|
| `is_vulgar` | **0.98** | **0.13** |
| moderation action | `flag_for_review` | **`allow`** |

Not a single character of the input changed. → [findings/01](findings/README.md#01)

**An ablation shows which part carries the effect:**

| variant | shift |
|---|---|
| better `instructions`, unchanged `criteria` | −0.04 |
| vague instruction ("be lenient") | −0.12 |
| **explicit list of terms** | **−0.82** |
| full norm (list + cultural explanation) | −0.85 |

Concrete lists move the model. Attitudes don't. And defining what *passes* is roughly
**3.5× more effective** than extending what fails (−0.70 vs −0.20).

### 2. The model has a bias, and it is measurable

Routing "answer from training, or search the web?":

| query | naive classifier |
|---|---|
| "Who is the **current** Pope?" | **0.43** ✗ below threshold |
| "Who was the Pope during WWII?" | 0.08 ✓ |
| "Who is the **current** US president?" | **0.43** ✗ |
| "Who won the 2020 election?" | 0.09 ✓ |

The model gets every historical question right and every *current* one wrong — even
though the word "current" is right there. **It does not distinguish "I know this" from
"I knew this at training time."**

Naive: 66.7%. Two paragraphs in `criteria`: 100%. → [findings/02](findings/README.md#02)

### 3. The question type decides more than the wording

Same story about a dog dying, asked two ways:

| | value | operational decision |
|---|---|---|
| **Noul** "is it suitable?" | 0.690 | **publish** |
| **Score** "how suitable?" | second-lowest level | **flag, needs an adult** |

A Noul returns *the probability that the answer is yes*. A Score returns *a position on
a scale*. Different quantities — they cannot be subtracted from each other, and picking
the wrong one flips the outcome. → [findings/03](findings/README.md#03)

### 4. Numbers written into criteria do nothing

Anchoring a Noul with "0.55–0.70 means X, 0.15–0.30 means Y" does **not** work. We kept
the descriptions word for word and only changed the numbers, including a fully inverted
scale:

| number set | measured |
|---|---|
| original | 0.759 |
| shifted down | 0.778 |
| **inverted** | **0.804** |

Spread: 0.045. **The descriptions do all the work; the numbers are ignored.**
If you need a scale, use a Score — that's what it's for.

---

## What it costs

Measured, not quoted from the docs:

| | |
|---|---|
| Price | $0.042 per 1M input tokens, **output free** |
| One classification (~500 tokens) | **$0.00002** |
| Full ablation study | **~$0.004** |
| All 1,180 calls in this repo | **~$0.05** |
| Latency (from Czechia) | median **1.1 s**, p95 1.8 s |
| Parallel questions | **20 questions ≈ 1 question** (0.73 s) |

> ⚠️ **On latency:** measured from a residential connection in the Czech Republic.
> A US benchmark reports p50 of 378 ms; the ~0.7 s difference is network round-trip.
> TypeSafe has no EU region. **These numbers measure the distance to Virginia, not the
> model.** Run the scripts yourself to get your own.

---

## Reproduce it

```bash
git clone https://github.com/RastislavDujavaPiccard/jev-classification-research
cd jev-classification-research
pip install -r requirements.txt
cp .env.example .env     # add your key from console.typesafe.ai
python experiments/01_primitives.py
```

Every experiment runs without arguments. Raw JSON for every run is in `results/`,
so any number in `findings/` can be traced back to the call that produced it.

---

## Methodology

- **5–10 runs per variant**, medians rather than means
- **Interleaved execution** — variants alternate, so a network slowdown can't land on one group
- **Noise floor 0.05**, measured: the model varies ±0.01–0.03 between identical runs
- **A shift counts as proven** only if it both crosses a decision boundary *and* exceeds the noise floor

Details in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Honest limitations

- **Small samples.** 5–15 items per domain. This demonstrates mechanisms, not accuracy.
- **Single annotator.** Expected answers are my judgement, not a validated ground truth.
- **One model version.** `jev-1.13.0`, six days after launch. Later versions will differ.
- **Latency is geography.** See above.
- **Contradicting work exists.** [leepokai/llm-prompt-techniques-on-jev](https://github.com/leepokai/llm-prompt-techniques-on-jev)
  found few-shot examples *neutral or harmful* on academic benchmarks. That is not a
  contradiction — see below.

### Why both results are right

leepokai tested tasks with an **objectively correct answer** (LegalBench, MMLU-Pro).
There, examples add nothing the model doesn't already have, and dilute the signal.

These experiments test tasks where **the correct answer depends on a norm** — what counts
as vulgar, what a parent allows, what your jurisdiction requires. There, examples and
definitions carry information the model cannot have.

Their own framing explains it: *information-carrying* techniques work, *wording* techniques
don't. A cultural norm is information. "Be more lenient" is wording.

---

## The sharpest result: two families, opposite verdicts

Two ordinary families with six-year-olds. **Family A**'s daughter has a real fear of
spiders — she doesn't sleep after a story with one in it. **Family B**'s son loves
animals, but his parents can't do stories where someone is left out of a group; he's
going through that at school.

Two gentle children's stories: a spider rebuilding her torn web, and a rabbit who isn't
picked for a game and then is. No violence, no death, both end warmly.

| story | no profile | Family A | Family B |
|---|---|---|---|
| **Spider rebuilds her web** | **0.912** → publish | **0.006** → DO NOT SHOW | **0.721** → publish |
| **Rabbit left out of a game** | **0.759** → publish | **0.889** → publish | **0.035** → DO NOT SHOW |

A perfect cross. **Without a profile both stories pass. With profiles, each family gets
the opposite verdict on the same content** — and the model was essentially certain both
times (confidence 1.000 and 0.990).

This is not keyword filtering. A filter on "spider" would do the same job for Family A,
and would also block a documentary about bees they'd love.

→ [findings](findings/README.md#09--personalised-scales-the-sharpest-contrast)

---

## Two findings worth calling out

### Czech performs as well as English on this task

The docs warn that English is the primary training language. Measured on 15 bilingual
pairs where each item exists in both languages with matching content:

| | accuracy | mean absolute difference |
|---|---|---|
| English text | **15/15** | — |
| Czech text | **15/15** | **0.036** |
| Decision agreement | **15/15** | — |

Eight of fifteen returned **identical values** in both languages, including sarcasm,
conditionals and two Czech idioms with no direct English equivalent.

**A threshold tuned on English data transfers.** One exception — negation — sits closer
to the boundary in Czech (0.464 vs 0.022); see [findings](findings/README.md#05--czech-vs-english).

### A cultural norm has to work in both directions

A norm that moves everything down is not calibration, it is moderation switched off.
Measured on 9 mild texts that should pass and 3 boundary texts that must not:

| | mean shift | outcome |
|---|---|---|
| Mild Czech colloquialisms | **−0.456** | moved down ✓ |
| Personal insults and a threat | **+0.329** | **boundary held 3/3** ✓ |

The clearest case: *"I'll come for it personally and you won't like it"* — a threat with
no profanity at all. Without the norm it scored **0.040** (correctly: no vulgar words).
With the norm, **0.420** and `block`, because the norm states the axis:

> *"What matters is whether a PERSON is being attacked, not whether a coarse word appears."*

Three of twelve moderation decisions changed, **all three out of the human review queue** —
one released, two blocked. The norm shrank the queue from both sides.

---

## In progress

- **Personalised classifiers** — same content, different user profiles, opposite decisions. A two-stage cascade: binary gate, then a scale written in the user's own terms. Early results are striking; publishing once the sample is larger.
- **Comparison against Gemini 2.5 Flash with context caching** — the obvious question nobody has measured properly

---

## License

Code MIT · Text and data CC BY 4.0

Not affiliated with TypeSafe AI. Independent research by a prompt engineer who wanted to
know what these classifiers actually do.

**Found a mistake?** Open an issue. Numbers that survive scrutiny are worth more than
numbers that don't get any.
