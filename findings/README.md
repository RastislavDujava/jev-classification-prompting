# Findings

Full write-ups are in Czech (`*.cs.md`) — that is the language they were drafted in,
and translating 3,000 lines would introduce errors I can't check. **Each finding is
summarised in English below**, with the numbers, the method and the exact prompts.
The raw JSON in `../results/` is language-neutral, so anything here can be verified
directly.

If a specific write-up matters to you and you don't read Czech, open an issue and
I'll translate that one.

---

## 00 — Related work

Six days after launch, the only comparable measurement work is
[leepokai/llm-prompt-techniques-on-jev](https://github.com/leepokai/llm-prompt-techniques-on-jev):
15+ prompting techniques across LegalBench, BIG-Bench Hard, MMLU-Pro and CLERC.

**They found few-shot examples neutral or harmful.** We found them useful. Both hold,
because we test different things — see the README section *"Why both results are right"*.

Their most useful contribution is a distinction we adopt: **information-carrying**
techniques (examples, decompositions, rewritten instructions) work; **wording**
techniques (roles, emotional appeals, "think step by step") don't, because Jev reads
once and generates no intermediate reasoning.

Everything else published so far — DataCamp, InfoWorld, Langfuse, Braintrust, Pydantic —
is overview or integration material without experiments.

→ [`00-related-work.cs.md`](00-related-work.cs.md)

---

## 01 — Criteria ablation

**The strongest lever in the API, and which part of it carries the effect.**

Same Czech text, same question, only the definition of "vulgar" changes:

| | without a cultural norm | with one |
|---|---|---|
| `is_vulgar` | **0.98** | **0.13** |
| moderation action | `flag_for_review` | **`allow`** |

Taking the definition apart (3 runs each, same input):

| variant | `is_vulgar` | shift |
|---|---|---|
| baseline, generic criteria | 0.980 | — |
| Czech context in `instructions` only | 0.943 | −0.04 |
| vague guidance: *"be lenient about Czech speech"* | 0.863 | −0.12 |
| **explicit list of terms, no explanation** | **0.163** | **−0.82** |
| full norm (list + cultural explanation) | 0.133 | −0.85 |
| full norm, but generic `instructions` | 0.160 | −0.82 |
| **`false` branch only** (exceptions defined) | 0.283 | **−0.70** |
| **`true` branch only** (prohibitions extended) | 0.780 | **−0.20** |
| norm placed in `state` instead of `criteria` | 0.093 | −0.89 |

**Four things follow:**

1. The concrete list does ~96% of the work. The thoughtful cultural explanation added 0.03 — noise.
2. `instructions` alone are nearly inert (−0.04). The work happens in `criteria`.
3. **Defining what passes is ~3.5× more effective than extending what fails** (−0.70 vs −0.20).
4. A norm in `state` works too, slightly better. Use `criteria` for a stable norm,
   `state` when it varies per tenant.

**Stability:** 6 runs of the key pair gave zero variance (0.980 ×6, 0.130 ×6).

→ [`01-criteria-ablation.cs.md`](01-criteria-ablation.cs.md) ·
data: [`../results/test_4_kulturni_norma.json`](../results/test_4_kulturni_norma.json)

---

## 02 — The model has a measurable bias

**Task:** should this query be answered from training, or does it need a web search?

15 queries, paired so that near-identical wording has opposite correct answers:

| query | naive classifier | correct? |
|---|---|---|
| "Who is the **current** Pope?" | **0.430** | ✗ below threshold |
| "Who was the Pope during WWII?" | 0.077 | ✓ |
| "Who is the **current** US president?" | **0.430** | ✗ |
| "Who won the 2020 US election?" | 0.087 | ✓ |
| "Who is the CEO of OpenAI?" | **0.350** | ✗ |
| "What is the capital of France?" | 0.030 | ✓ |

**Every historical question right. Every current one wrong.** The model does not
distinguish *"I know this"* from *"I knew this at training time"* — it has a stored
answer and treats it as current knowledge.

One exception: "latest React version" was correct even naively (0.917). **The bias is
domain-specific** — the model knows software versions go stale, but not that people
leave office.

| variant | accuracy |
|---|---|
| naive | **10/15 (66.7%)** |
| criteria explaining knowledge cutoff | **15/15 (100%)** |
| criteria + 6 examples | 15/15 (100%) |

**Isolating what fixed it** (8 control queries):

| `instructions` | `criteria` | accuracy |
|---|---|---|
| naive | naive | 38% |
| **improved** | naive | **38%** |
| naive | **improved** | **100%** |
| naive + 6 examples | naive | 88% |

Improving `instructions` alone changed nothing. **Examples were not needed here** —
well-written criteria reached 100% on their own. The key sentence:

> *"Even if the model has a confident answer stored, that answer may now be outdated."*

→ [`02-model-bias.cs.md`](02-model-bias.cs.md) ·
data: [`../results/test_6_tool_routing.json`](../results/test_6_tool_routing.json)

---

## 03 — The question type decides more than the wording

Same children's story (a boy's old dog dies on screen, buried under an apple tree):

| | value | operational decision |
|---|---|---|
| **Noul** — "is it suitable?" | 0.690 | **publish** |
| **Score** — "how suitable?" | second-lowest of 6 levels | **flag, needs an adult** |

> ⚠️ These are **different quantities** and must not be subtracted. A Noul returns the
> probability that the answer is yes; a Score returns a position on a scale. An earlier
> draft compared them numerically — that was wrong, and is corrected in the write-up.
> What stands is that the two tools lead to opposite operational decisions.

The docs are explicit: *"A value of 0.5 does not mean medium skill. Use a Score to
measure skill along defined levels."*

**Scale granularity** (5 stories, normalised to 0–1):

| levels | range | mean confidence | ordering correct? |
|---|---|---|---|
| 3 | 0.603 | **0.800** | **✗ NO** |
| **4** | **0.914** | 0.888 | ✓ |
| 6 | 0.796 | 0.902 | ✓ |
| 10 | 0.764 | **0.928** | ✓ |

Three levels got the ordering wrong — it placed off-screen loss below on-screen death —
and had the lowest confidence, i.e. the model signalled its own uncertainty.
**Use at least four.**

→ [`03-question-type.cs.md`](03-question-type.cs.md) ·
data: [`../results/test_9_jemnost_skaly.json`](../results/test_9_jemnost_skaly.json)

---

## 04 — Numbers written into criteria do nothing

Anchoring a Noul with explicit bands ("0.55–0.70 means real danger, resolved") does
**not** work. Keeping the descriptions word for word and changing only the numbers:

| number set for the target band | measured |
|---|---|
| original (0.55–0.70) | 0.759 |
| shifted down (0.25–0.35) | 0.778 |
| compressed up (0.85–0.90) | 0.772 |
| **fully inverted** (gentle=0, graphic=1) | **0.804** |

**Spread across all four: 0.045.** An inverted scale should have produced the opposite
of the original. It produced a slightly higher number.

**The descriptions do all the work.** Anchor placement barely matters either —
`instructions` 0.741, `criteria.true` 0.764, both 0.785.

For comparison, a Score with the same descriptions landed at 3.34/5 — level 3,
*"real danger with a lasting consequence, fully resolved"* — which is exactly the
intended band. **If you need a scale, use the type that has one.**

→ [`04-scale-anchors.cs.md`](04-scale-anchors.cs.md) ·
data: [`../results/test_8_kotvy_umisteni.json`](../results/test_8_kotvy_umisteni.json)

---

## 05 — Czech vs English

The docs warn that English is the primary training language. **On this task, the
difference was not measurable.**

15 bilingual pairs — each item exists in both languages with matching content.
Question always in English; only the text language changes.

| | accuracy | mean absolute difference |
|---|---|---|
| English text | **15/15 (100%)** | — |
| Czech text | **15/15 (100%)** | **0.036** |
| Decision agreement | **15/15 (100%)** | — |

Eight of fifteen items returned **identical values** in both languages.
The set deliberately includes sarcasm, negation, conditional mood, third-person
reports, complaints with no emotional vocabulary, and two Czech idioms with no direct
English equivalent — all handled equivalently.

**One exception — negation:**

| | value |
|---|---|
| EN: *"The parcel did not arrive late and nothing was missing"* | 0.022 |
| CS: *"Zásilka nedorazila pozdě a nic nechybělo"* | **0.464** |

Both are formally correct (below the 0.5 threshold), but the Czech version sits close
to the boundary. Czech requires double negation — *"a nic nechybělo"* carries a
negative on both the verb and the pronoun — and the model may be accumulating negative
signals. **This is a hypothesis from one example, not a demonstrated mechanism.**

**Translating the question into Czech did not help** (15/15 either way), except on that
one negation item, where it moved 0.464 → 0.342.

**Practical:** a threshold tuned on English data transfers. Test negative constructions
separately.

→ [`05-czech-language.cs.md`](05-czech-language.cs.md) ·
data: [`../results/test_12_cestina.json`](../results/test_12_cestina.json)

---

## 06 — A cultural norm must work in both directions

A norm that moves everything down is not calibration, it's moderation turned off.
This set tests both halves: 9 mild texts that should be allowed, 3 boundary texts
that must not be.

**Mild expressions — mean shift −0.456:**

| text | without norm | with norm |
|---|---|---|
| *"Do prdele, zase to spadlo"* | 0.744 | 0.066 |
| *"Ta nová funkce je kravina"* | 0.660 | 0.090 |
| **"Konečně to funguje, kurva!"** (a thank-you) | **0.980** → `flag` | **0.108** → `allow` |
| *"Oh crap… third damn time"* (English) | 0.916 | 0.176 |

**Boundary cases — mean shift +0.329, held 3/3:**

| text | without norm | with norm | action |
|---|---|---|---|
| *"Vy jste naprostí idioti…"* | 0.598 | **0.960** | block → **block** |
| *"Vy jste debilové…"* | 0.704 | **0.950** | flag → **block** |
| **"I'll come for it personally and you won't like it"** | **0.040** | **0.420** | flag → **block** |

**The last row is the important one.** That text contains no profanity at all —
it's a threat written in clean language. Without the norm it scored 0.040: *"no vulgar
language"*, which is true. A classifier asking *"does this contain swear words?"*
would publish it.

The norm states the axis explicitly:

> *"What matters is whether a PERSON is being attacked, not whether a coarse word appears."*

The model adopted that axis. It stopped counting words and started asking who is the target.

**Three of twelve moderation decisions changed — all correctly, and all three had been
sitting in `flag_for_review`.** The norm shrank the human review queue from both sides.

**Cross-language spillover:** the norm speaks only about Czech, yet the English text
dropped from 0.916 to 0.176. Criteria shift the overall sensitivity threshold rather
than filtering listed words. Bound the effect explicitly if you need it narrow.

→ [`06-cultural-norm.cs.md`](06-cultural-norm.cs.md) ·
data: [`../results/test_13_vulgarita_v2.json`](../results/test_13_vulgarita_v2.json)

---

## 07 — Limits and cost

Verified against both the documentation and the live API:

| | documented | measured |
|---|---|---|
| `state` + longest question | 32k tokens | ✅ 32,796 OK, more → `max_tokens_exceeded` |
| `state` + all questions | 64k tokens | — |
| Choice options | max 255 | ✅ 255 OK, 256 → error |
| Score levels | 2–10 | ✅ 10 OK, 11 → error |
| **`criteria` length** | **no separate limit** | ✅ 191,750 characters accepted |

The token budget is **shared** between `state` and the questions — it is not 32k each.

**Cost:** $0.042 per 1M input tokens, output free. One classification ≈ $0.00002.
The full ablation study cost about $0.004.

**But length is paid on every call.** 30,000 tokens of criteria ≈ $0.13 per 1,000 calls;
at a million calls a month that is $1,260 for a norm that never changes. The ablation
exists to tell you what you can cut.

→ [`07-limits-and-cost.cs.md`](07-limits-and-cost.cs.md)

---

## 08 — Content vs length in the question

Do longer `instructions` slow things down, and do examples change the answer?
These are separate questions, so the test runs two series of equal length —
one with few-shot examples, one with semantically neutral filler.

**Examples change the answer. Neutral text of the same length does not:**

| length | with examples | neutral filler | difference |
|---|---|---|---|
| bare question | 0.925 | — | — |
| ~500 tokens | **0.353** | 0.898 | −0.545 |
| ~2,000 tokens | 0.332 | 0.888 | −0.556 |
| ~5,000 tokens | 0.304 | 0.885 | −0.581 |

The neutral series moved by 0.013 total — noise. **The shift is content, not length.**

**Diminishing returns:** the first 5 examples produced −0.572; the next 45 added −0.049.
Roughly **12:1 in favour of the first few**. (Caveat: our 50 examples were the same
five repeated. Fifty *distinct* examples might do better — untested.)

**Latency:** flat up to ~2,000 tokens; **+0.28 s at ~5,000**, and identical in both
series — so that cost is length, not content. 15.8× more tokens gave only 1.27× the
response time, because input processing is parallel rather than sequential.

→ [`08-length-vs-content.cs.md`](08-length-vs-content.cs.md) ·
data: [`../results/test_5_delka_vs_rychlost.json`](../results/test_5_delka_vs_rychlost.json)

---

## 09 — Personalised scales: the sharpest contrast

Two ordinary families, two harmless children's stories, opposite decisions.

**Family A** — six-year-old daughter with a real fear of spiders and insects.
Doesn't sleep after a story with one in it. Handles everything else fine.

**Family B** — six-year-old son who loves animals. His parents can't do stories
where someone is excluded from a group; he's going through that at school.

**Story 1:** a house spider's web is torn by the wind; a beetle encourages her; she
rebuilds it and they watch it together until dark.
**Story 2:** a young rabbit is told the teams are already even; he sits by the fence;
the smallest rabbit comes and sits with him; the next day both teams want him.

Both are gentle, both end warmly, neither contains violence or death.

| story | no profile | Family A | Family B |
|---|---|---|---|
| **Anička the spider** | **0.912** → publish | **0.006** → DO NOT SHOW | **0.721** → publish w/ note |
| **Ondra the rabbit** | **0.759** → publish w/ note | **0.889** → publish | **0.035** → DO NOT SHOW |

A perfect cross. Without a profile both stories pass; with profiles each family gets
the opposite verdict on the same content. Range **0.006 to 0.889**, and the model was
essentially certain both times (confidence 1.000 and 0.990) — these were not borderline
placements, each story matched that family's bottom level exactly.

**Why the descriptions matter.** Family A's bottom level ends *"…however kindly it is
written"* — without that clause a gently-written spider might not register. Their top
level ends *"sad or difficult moments are fine as long as this condition holds"* —
without that, the rabbit story would have sunk too, and it scored 0.889.

**This is not keyword filtering.** A filter on the word "spider" would do the same job
for Family A, and would also block a documentary about bees they would love.

**Cascade:** a shared gate (*is this even a children's story?* — both 0.98, and no
profile can override it), then the family's scale, then thresholds in ordinary code —
a second layer of personalisation that needs no model at all.

→ [`09-personalised-scales.cs.md`](09-personalised-scales.cs.md) ·
data: [`../results/test_14_fobie.json`](../results/test_14_fobie.json)

---

## Six domains, 1,180 calls

The largest single run. Six domains, each with paired opposites, three question
variants (naive / informed criteria / criteria + examples), five runs each.

| domain | naive | informed | proven pairs |
|---|---|---|---|
| Web search vs. own knowledge | 70% | **100%** | 6/10 |
| Cultural norms | 75% | 90% | 3/10 |
| Professional jargon vs. real alarm | 67% | **100%** | 4/6 |
| Legal differences between jurisdictions | 75% | **100%** | 3/6 |
| Date and number formats | 62% | 88% | 2/4 |
| Personal norm | 60% | **100%** | 4/5 |
| **Total** | **70%** | **96%** | **22/41** |

A pair counts as *proven* only if the number of correct answers increased **and**
the shift exceeded the 0.05 noise floor.

**Strongest individual shifts:** clinical language misread as an emergency (+0.92),
"crash" as outage vs. road accident (+0.66), EU working-time rules (+0.61),
authorised penetration test read as an attack (+0.60).

**Where criteria helped least:** cultural norms — but not because the technique failed.
The model already knew several of those norms (chopsticks, business cards, gift-giving)
and got them right naively. **Cultural knowledge is present but unevenly activated.**

data: [`../results/domains_run.json`](../results/domains_run.json)

---

## In progress

- **Personalised classifiers.** Same content, different user profiles, opposite
  decisions. A two-stage cascade (binary gate → personalised scale → thresholds in code).
  Early numbers are striking; publishing once the sample is larger.
- **Larger cultural sample.** The current set is too small to claim anything.
- **Comparison against Gemini 2.5 Flash with context caching.** The obvious question
  nobody has measured properly yet.
