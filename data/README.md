# Test data

Inputs used by the experiments. Each file is plain JSON with a `_comment` field
explaining what the set is for.

## A note on `inputs/vulgarity_v2.json`

This file contains Czech colloquial expressions and mild profanity, plus three
texts with personal insults and a threat.

**These are test inputs for a content moderation classifier.** The whole point of
the experiment is to measure whether a cultural norm written into `criteria` can
(a) stop flagging ordinary Czech informal speech as offensive, while (b) still
blocking texts that attack a person. Both halves need real examples.

The strongest Czech profanity was deliberately left out. Everything here is at the
level you would encounter in an ordinary pub conversation or a frustrated support
ticket.

See [`../findings/06-cultural-norm.cs.md`](../findings/06-cultural-norm.cs.md) for
what was measured and why.

## Structure

| Path | Used by |
|---|---|
| `inputs/texts.json` | 01 — three primitives |
| `inputs/variants.json` | 03 — one word at a time |
| `inputs/routing_queries.json` | 05 — tool routing |
| `inputs/bilingual.json` | 09 — Czech vs English |
| `inputs/vulgarity_v2.json` | 10 — cultural norm |
| `inputs/stories.json` | 07, 08 — scales |
| `questions/sentiment.json` | 01, 02, 03 |
| `domains/d*.json` | 06 — six domains |
