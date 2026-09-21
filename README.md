# Jev prompt engineering

**A classifier draws a line somewhere. If you don't write that line, someone else did.**

[TypeSafe's Jev](https://docs.typesafe.ai/) launched on 15 September 2026. It doesn't
generate text — you hand it content and a typed question, it returns a decision with
probabilities. A second, two hundredths of a cent per call.

It's sold as deterministic where LLMs are fuzzy: typed output, no hallucinated
categories, calibrated probabilities. All true — and all about the **shape** of the
answer. The judgement inside is learned, which means it carries a bias, which means
it should be promptable.

This repo is a first pass at finding out how. Nine things I got wrong, then measured —
~1,300 API calls, every script runnable with one command, every raw result committed.

It's early work on a model that's a week old, by one person, on small samples. Treat it
as a starting point and a method you can rerun on your own data, **not as established
fact.** Where I'm unsure I say so, and I've already had to correct myself once.

> **Status:** initial testing, still going.
> Numbers are for `jev-1.13.0` and will drift as the model does.

---

## The one number

Across six domains, 41 paired test items:

| | naive question | criteria written properly |
|---|---|---|
| **Accuracy** | **70%** (57/82) | **96%** (79/82) |

That gap isn't the model getting smarter. It's the difference between accepting a
default and stating what you actually mean.

**Everything below is an attempt to work out how to state it.**

---

# What I found so far

## 1 — The leverage seems to be in the criteria, not the question

**Why this matters:** most people spend their effort phrasing the question well.
Measured, that's the *least* effective thing you can do.

Same text, same question, only the definition of "vulgar" changes:

| | without a cultural norm | with one |
|---|---|---|
| `is_vulgar` | **0.98** | **0.13** |
| moderation action | `flag_for_review` | **`allow`** |

Not a character of the input changed. An ablation isolates which part of the definition
carries the effect:

| what changed | shift |
|---|---|
| better `instructions`, `criteria` untouched | **−0.04** |
| vague guidance: *"be lenient about Czech speech"* | −0.12 |
| **an explicit list of the terms** | **−0.82** |
| the list plus a cultural explanation | −0.85 |

**Take away:** concrete lists move the model, attitudes don't, and the thoughtful
paragraph you were proudest of writing is probably worth 0.03. Rewriting the question
is worth 0.04 — noise.

📄 [Full write-up](findings/01-criteria-ablation.cs.md) ·
▶ `python experiments/10_cultural_norm.py`

---

## 2 — Define what passes, not just what fails

**Why this matters:** it's roughly 3.5× more effective, and it's the opposite of how
most content policies are written.

From the same ablation, defining only one branch of the criteria:

| | shift |
|---|---|
| `true` branch only — extending what's prohibited | −0.20 |
| **`false` branch only — naming the exceptions** | **−0.70** |

The model already holds firm opinions about what's wrong. What it needs from you is
**where that ends**.

There's a second, sharper version of this in the personalisation work: a ladder whose
top rung says *"sad or difficult moments are fine as long as this condition holds"*
behaves completely differently from one that only lists prohibitions. Without that
sentence the whole scale drifts conservative and starts filtering everything mildly sad.

**Take away:** write the permission, not only the prohibition.

📄 [Full write-up](findings/01-criteria-ablation.cs.md)

---

## 3 — The question type decides where the user fits

**Why this matters:** picking the wrong type isn't a wording mistake. It's choosing a
shape with nowhere to put the person you're building for.

Ask *"is this story suitable for a child aged 5 to 7?"* — a **Noul**, a yes/no question —
and you get one number back, with somebody else's threshold baked into it:

```
spider story   0.910 → show
rabbit story   0.892 → show
```

Both correct. Both useless if you're building for a particular child.

A **Score** takes the same question plus *criteria*: levels worst to best, each a
sentence you write. The model spreads 100% of probability across them. **Four or five
places to say what you mean, instead of one.**

The same story, asked both ways, produces opposite operational decisions — a dog dying
on screen reads as 0.690 *(publish)* to a Noul and lands on the second-lowest rung of a
six-level Score *(flag, needs an adult)*.

> ⚠️ Noul values and Score positions are **different quantities** and must not be
> subtracted. A Noul returns the probability the answer is yes; a Score returns a
> position on a scale. An early draft of this research got that wrong — the correction
> is in the write-up.

**On granularity:** three levels got the ordering of test stories *wrong* and had the
lowest confidence. Four or more was stable. Use at least four.

📄 [Full write-up](findings/03-question-type.cs.md) ·
▶ `python experiments/08_noul_vs_score.py`

---

## 4 — Hyper-personalisation lives in the rungs

**Why this matters:** this is the one that changes what you can build.

Two ordinary families with six-year-olds. One girl has a real fear of spiders — she
won't sleep after a story with one in it. One boy loves animals, but his parents can't
do stories where someone is left out; he's going through that at school.

Two gentle stories, no violence, both end warmly: a spider rebuilds her torn web;
a rabbit isn't picked for a game, then is.

Written generically, **both stories pass for both children**. Then one ladder per child,
same question, same code, only the criteria differ:

```
CHILD 1 (afraid of spiders) — probability across the five rungs
                    [0]    [1]    [2]    [3]    [4]
spider story       98%     2%     0%     0%     0%   →  BLOCK
rabbit story        0%     0%     5%    34%    61%   →  show

CHILD 2 (being left out at school)
                    [0]    [1]    [2]    [3]    [4]
spider story        0%    27%     1%    25%    47%   →  show
rabbit story       91%     6%     0%     2%     1%   →  BLOCK
```

A perfect cross. **The story that's an absolute no for one child is fine for the other,
and the generic ladder waved both through.**

Two clauses in Child 1's ladder do the real work, and both generalise:

- **"however kindly it is written"** — without it, a gently-written spider doesn't
  register, because nothing bad actually happens. Say the *presence* is the problem,
  not the treatment.
- **"sad or difficult moments are fine"** — see section 2.

**This is not keyword filtering.** A filter on "spider" would do the same job for Child 1
and would also block the bee documentary they'd love.

📄 [Full write-up](findings/09-personalised-scales.cs.md) ·
▶ `python experiments/11_personalised_scales.py`

---

## 5 — The model doesn't know what it doesn't know

**Why this matters:** if you're routing between "answer from memory" and "search the
web", this is a live bug in your product right now.

Fifteen queries, paired so near-identical wording has opposite correct answers:

| query | naive classifier | |
|---|---|---|
| "Who was the Pope during WWII?" | 0.077 | ✓ |
| "Who is the **current** Pope?" | **0.430** | ✗ below threshold |
| "Who won the 2020 US election?" | 0.087 | ✓ |
| "Who is the **current** US president?" | **0.430** | ✗ |

**Every historical question right. Every current one wrong** — even with the word
"current" sitting in the query. The model has a stored answer and experiences it as
knowledge, not as a snapshot.

It isn't uniform, either: *"latest React version"* was correct even naively (0.917).
**The bias is domain-specific** — it learned that software versions go stale, not that
people leave office.

The fix was two paragraphs in `criteria`, and the load-bearing sentence is:

> *"Even if the model has a confident answer stored, that answer may now be outdated."*

**66.7% → 100%.** Six few-shot examples added on top changed nothing — already at
ceiling, pure cost.

📄 [Full write-up](findings/02-model-bias.cs.md) ·
▶ `python experiments/05_tool_routing.py`

---

## 6 — Numbers written into criteria did nothing

**Why this matters:** it's the obvious thing to try, and it's a dead end. Save yourself
the afternoon.

Anchoring with explicit bands — *"0.55–0.70 means real danger, resolved"* — does not
work. Keeping the descriptions word for word and changing only the numbers:

| number set for the target band | measured |
|---|---|
| original (0.55–0.70) | 0.759 |
| shifted down (0.25–0.35) | 0.778 |
| compressed up (0.85–0.90) | 0.772 |
| **fully inverted** (gentle = 0, graphic = 1) | **0.804** |

Spread across all four: **0.045**. An inverted scale should have produced the opposite
of the original. It produced a slightly higher number.

**The descriptions do all the work. The numbers are decoration.** If you need a scale,
use a Score — it has one built in.

📄 [Full write-up](findings/04-scale-anchors.cs.md) ·
▶ `python experiments/07_scale_anchors.py`

---

## 7 — Examples carry information, or they carry nothing

**Why this matters:** "add few-shot examples" is a reflex. Sometimes it's the answer,
sometimes it's just tokens.

Two series of identical length — one of few-shot examples, one of semantically neutral
filler:

| length | with examples | neutral filler |
|---|---|---|
| bare question | 0.925 | — |
| ~500 tokens | **0.353** | 0.898 |
| ~5,000 tokens | 0.304 | 0.885 |

The neutral series moved 0.013 in total. **The shift is content, not length.**

But note the diminishing returns: the first 5 examples produced −0.572, the next 45
added −0.049. Roughly **12:1 in favour of the first few**.

And in section 5, examples added nothing at all — the criteria had already reached 100%.

**Take away:** examples work when they carry information the model lacks, typically a
boundary it can't infer. On tasks it already solves, they're cost. This matches
[leepokai's](https://github.com/leepokai/llm-prompt-techniques-on-jev) finding that
few-shot is neutral-to-harmful on academic benchmarks — see *Related work* below.

**Latency note:** flat to ~2,000 tokens, **+0.28 s at ~5,000**, identical in both
series. 15.8× more tokens cost only 1.27× the response time, because input processing
is parallel.

📄 [Full write-up](findings/08-length-vs-content.cs.md) ·
▶ `python experiments/04_length_vs_content.py`

---

## 8 — A norm has to work in both directions

**Why this matters:** a norm that moves everything down isn't calibration, it's
moderation switched off. This is the test that tells you which one you wrote.

Nine mild texts that should pass, three boundary texts that must not:

| | mean shift | outcome |
|---|---|---|
| Mild Czech colloquialisms | **−0.456** | moved down ✓ |
| Personal insults and a threat | **+0.329** | **boundary held 3/3** ✓ |

The clearest case: *"I'll come for it personally and you won't like it"* — a threat with
**no profanity at all**. Without the norm it scored 0.040, correctly: no vulgar words.
With the norm, 0.420 and `block`, because the norm states the axis:

> *"What matters is whether a PERSON is being attacked, not whether a coarse word appears."*

The model adopted that axis. It stopped counting words and started asking who the target is.

**Three of twelve moderation decisions changed — all three moved *out* of the human
review queue.** One released, two blocked. The norm shrank the queue from both sides.

**Watch for spillover:** the norm speaks only about Czech, yet an English test text
dropped from 0.916 to 0.176. Criteria shift the overall sensitivity threshold rather
than filtering listed words. Bound the effect explicitly if you need it narrow.

📄 [Full write-up](findings/06-cultural-norm.cs.md) ·
▶ `python experiments/10_cultural_norm.py`

---

## 9 — Czech performed as well as English here

**Why this matters:** the docs warn about non-English content. On this task the warning
didn't show up in the numbers — which is worth knowing if you're building for a
non-English market.

15 bilingual pairs, each item existing in both languages with matching content:

| | accuracy | mean absolute difference |
|---|---|---|
| English text | **15/15** | — |
| Czech text | **15/15** | **0.036** |
| Decision agreement | **15/15** | — |

**Eight of fifteen returned identical values in both languages**, including sarcasm,
conditionals, third-person reports, and two Czech idioms with no direct English equivalent.

**Practical:** a threshold tuned on English data transfers.

**One exception — negation.** *"The parcel did not arrive late and nothing was missing"*
scored 0.022 in English and **0.464** in Czech. Both formally correct, but the Czech
version sits close to the boundary. Czech requires double negation, and the model may
be accumulating negative signals — *a hypothesis from one example, not a demonstrated
mechanism.* Test negative constructions separately.

Translating the question into Czech didn't help (15/15 either way).

📄 [Full write-up](findings/05-czech-language.cs.md) ·
▶ `python experiments/09_czech_vs_english.py`

---

## Limits and cost

| | documented | measured |
|---|---|---|
| `state` + longest question | 32k tokens | ✅ 32,796 OK, more → `max_tokens_exceeded` |
| Choice options | max 255 | ✅ 255 OK, 256 → error |
| Score levels | 2–10 | ✅ 10 OK, 11 → error |
| **`criteria` length** | **no separate limit** | ✅ 191,750 characters accepted |

The token budget is **shared** between `state` and questions — not 32k each.

**Cost:** $0.042 per 1M input tokens, output free. One classification ≈ $0.00002.
The full suite in this repo ≈ $0.05.

**But length is paid on every call.** 30,000 tokens of criteria ≈ $0.13 per 1,000 calls;
at a million calls a month that's $1,260 for a norm that never changes. The ablation in section 1 exists to tell you what you can cut.

**Latency from Czechia:** median **1.1 s**, p95 1.8 s. A US benchmark reports p50 of
378 ms — the difference is network round-trip, TypeSafe has no EU region.
**These numbers measure distance to Virginia, not the model.**

📄 [Full write-up](findings/07-limits-and-cost.cs.md)

---

## Reproduce it

```bash
git clone https://github.com/RastislavDujava/jev-classification-prompting
cd jev-classification-prompting
pip install -r requirements.txt
cp .env.example .env     # your key from console.typesafe.ai
python experiments/01_primitives.py
```

Every experiment runs without arguments. Raw JSON for every run is in `results/`, so
any number above traces back to the call that produced it.

**Method:** 5–10 runs per variant · medians not means · variants interleaved so a
network slowdown can't land on one group · **noise floor 0.05**, measured — the model
varies ±0.01–0.03 between identical runs · a shift counts only if it crosses a decision
boundary *and* clears the floor. Details in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Honest limitations

- **Small samples.** 5–15 items per domain. This demonstrates mechanisms, not accuracy.
- **Single annotator.** Expected answers are my judgement, not validated ground truth.
- **I wrote both the inputs and the criteria** — a real risk of unconsciously writing
  tests that suit the hypothesis. Controls mitigate it; they don't eliminate it.
- **No held-out set.** Criteria were written and measured on the same items.
- **One model version**, six days after launch.
- **I got it wrong once already** — comparing Noul values to Score positions
  numerically. The correction is visible in section 3 rather than quietly edited out.

### Related work, and why it disagrees

[leepokai/llm-prompt-techniques-on-jev](https://github.com/leepokai/llm-prompt-techniques-on-jev)
tested 15+ prompting techniques across LegalBench, BIG-Bench Hard, MMLU-Pro and CLERC,
and found **few-shot examples neutral or harmful**.

That's not a contradiction. They tested tasks with an **objectively correct answer**,
where examples add nothing the model doesn't have. These experiments test tasks where
**the correct answer depends on a norm** — what counts as vulgar, what a parent allows,
what your jurisdiction requires. There, examples and definitions carry information the
model cannot have.

Their own framing explains it: *information-carrying* techniques work, *wording*
techniques don't. A cultural norm is information. "Be more lenient" is wording.

---

## In progress

- **Larger cultural sample** — the current set is too small to claim anything
- **Comparison against Gemini 2.5 Flash with context caching** — the obvious question
  nobody has measured properly

---

## License

Code MIT · Text and data CC BY 4.0

Not affiliated with TypeSafe AI. Independent research by a prompt engineer who wanted
to know what these classifiers actually do.

**Found a mistake?** Open an issue. Numbers that survive scrutiny are worth more than
numbers nobody checks.
