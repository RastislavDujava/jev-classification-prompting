"""
TEST 9 — Jemnost stupnice: kolik úrovní má Score mít?

Zjištění z testu 8: Noul dal 0,903 ("ano, vhodné"), Score dalo 0,667
("skutečné nebezpečí s následkem"). Stejný příběh, stejná otázka,
jiný TYP otázky -- a úplně jiné rozhodnutí.

Tenhle test jde dál a ptá se:
  1. Platí ten rozdíl Noul vs. Score napříč VÍCE příběhy, nebo to byla náhoda?
  2. Mění se výsledek s počtem úrovní? (3 / 4 / 6 / 10)
  3. Kolik úrovní ještě model rozliší, než se stupnice "rozmaže"?

Všechny příběhy i zadání anglicky.

Spusť: ▶ (bez argumentů)
"""

import statistics

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, save_result

RUNS = 5

# ---------------------------------------------------------------------------
# PŘÍBĚHY — anglicky, napříč celou škálou vhodnosti pro děti 5-7
# ---------------------------------------------------------------------------
STORIES = {
    "gentle": {
        "expected": "nejvyšší",
        "text": (
            "Milly the mouse found a lost blue button in the meadow. It shone in the "
            "sunlight and was almost as big as she was. She rolled it all the way home "
            "and stood it up on its edge, and it made a perfect little table.\n\n"
            "She invited her friend the hedgehog for tea. They had to sit very close "
            "together because the table was so small, and when the hedgehog laughed his "
            "spines rattled against the button and made a tiny drumming sound.\n\n"
            "They laughed so much that the tea went cold, so they made a fresh pot and "
            "drank it watching the sun go down behind the grass."
        ),
    },
    "mild_worry": {
        "expected": "vysoká",
        "text": (
            "Quinn the duckling wandered further from the pond than he ever had before, "
            "following a line of ants to see where they were going. When he looked up, "
            "the reeds all looked the same and he could not tell which way was home.\n\n"
            "He sat down and felt very small. He did not cry, but his beak wobbled a "
            "little. Then an old turtle came out from under a log and asked him what was "
            "wrong. She told him that home was always downhill, because that was where "
            "water went.\n\n"
            "Quinn waddled downhill and there was the pond, and his mother, who had been "
            "looking for him. She tucked him under her wing and he fell asleep before he "
            "could even tell her about the ants."
        ),
    },
    "real_injury": {  # tenhle byl v testu 8 -- Pip
        "expected": "střední",
        "text": (
            "Pip was a small brown rabbit who lived at the edge of the meadow. Every "
            "morning he hopped down to the stream to watch the water beetles. His mother "
            "always told him to stay where he could still see the big oak tree, because "
            "that was how a rabbit knew the way home.\n\n"
            "One afternoon a butterfly drifted past and Pip followed it without thinking. "
            "When he finally looked up the oak tree was nowhere to be seen. He tried to "
            "run back, but his back leg slipped between two rocks and caught fast, and "
            "when he pulled it free it hurt so much that he could not stand on it. He sat "
            "down in the wet grass and cried, and the rain began to fall.\n\n"
            "It was an old badger who found him. She wrapped him in dry leaves and carried "
            "him home on her broad back. His leg was sore for many days and he had to stay "
            "inside while his sisters played, which he thought was terribly unfair. But it "
            "healed, and he never once forgot to look for the oak tree after that."
        ),
    },
    "loss_offscreen": {
        "expected": "nízká",
        "text": (
            "The fox came to the hen house on three nights in a row. The hens heard him "
            "walking around outside in the dark, and they pressed themselves into the "
            "corner and did not make a sound.\n\n"
            "On the third morning the farmer found a hole in the wire fence, and when he "
            "counted the hens there were only eleven where there had been twelve. Nobody "
            "said anything about the twelfth hen. The farmer mended the fence and went "
            "back to the house.\n\n"
            "For a long time afterwards the hens would not go out into the yard, even "
            "when the sun was warm. They stayed near the door where they could get back "
            "inside quickly."
        ),
    },
    "death_onscreen": {
        "expected": "velmi nízká",
        "text": (
            "Rex the old dog could not walk any more. He lay in his kennel and his "
            "breathing was slow and heavy, and he did not lift his head when the boy came "
            "out with his bowl.\n\n"
            "The boy sat down beside him and stroked his head all afternoon. He told Rex "
            "about the rabbit they had chased together when Rex was young, and about the "
            "time Rex had swum out into the lake after a stick and come back with a duck "
            "feather on his nose instead.\n\n"
            "In the evening Rex breathed out and did not breathe in again. The boy buried "
            "him under the apple tree, and stood there for a long time after the sun had "
            "gone down."
        ),
    },
}

QUESTION_NOUL = "Is this animal story suitable for children aged 5 to 7?"
QUESTION_SCORE = "How suitable is this animal story for children aged 5 to 7?"

# ---------------------------------------------------------------------------
# STUPNICE — tytéž hranice, různě jemné dělení. VŽDY od nejhoršího k nejlepšímu.
# ---------------------------------------------------------------------------
SCALES = {
    "3 úrovně": [
        "Not suitable: death, violence or loss that a child of this age cannot process alone",
        "Needs care: real danger, injury or fear that an adult should be ready to talk about",
        "Fully suitable: gentle throughout, the child finishes it feeling safe",
    ],
    "4 úrovně": [
        "Graphic or distressing: death, violence or permanent loss shown directly",
        "Heavy: something frightening or sad happens, or a threat is left unresolved",
        "Real danger or injury, described without detail and fully resolved by the end",
        "Entirely gentle: nothing bad happens, the child finishes it smiling",
    ],
    "6 úrovní": [
        "Graphic violence, hunting in physical detail, blood or suffering shown directly",
        "Death or permanent loss on-screen, handled gently, needs an adult to explain",
        "Something frightening or sad happens off-screen, or a threat is left unresolved",
        "Real danger or injury with a lasting consequence, no graphic detail, fully resolved by the end",
        "Mild worry that resolves quickly: brief fear or sadness, then comfort and a warm ending",
        "Entirely gentle: nothing bad happens, the child finishes it smiling",
    ],
    "10 úrovní": [
        "Graphic violence with physical detail: blood, wounds, or suffering shown directly",
        "Violence or killing shown on-screen without graphic detail",
        "Death of a main character shown on-screen, handled gently and with care",
        "Death or permanent loss that happens off-screen but is clearly understood",
        "A threat or danger that is never resolved; the story ends unsettled",
        "Something frightening happens off-screen; the ending is safe but subdued",
        "Real injury or danger with a lasting consequence, fully resolved by the end",
        "Brief real danger, resolved quickly, no lasting consequence",
        "Mild worry or being briefly lost, comforted within a page, warm ending",
        "Entirely gentle: nothing bad happens at all, the child finishes it smiling",
    ],
}


def run_noul(text: str) -> dict:
    q = {"type": "noul", "instructions": QUESTION_NOUL}
    vals = [ask(text, {"q": q})["answers"]["q"]["noul"] for _ in range(RUNS)]
    return {"avg": round(statistics.mean(vals), 3),
            "spread": round(max(vals) - min(vals), 3), "runs": vals}


def run_score(text: str, levels: list) -> dict:
    q = {"type": "score", "instructions": QUESTION_SCORE, "criteria": levels}
    raw, confs, probs = [], [], []
    for _ in range(RUNS):
        a = ask(text, {"q": q})["answers"]["q"]
        raw.append(a["score"])
        confs.append(a["confidence"])
        probs.append(a["probabilities"])
    top = len(levels) - 1
    return {
        "raw": round(statistics.mean(raw), 3),
        "normalized": round(statistics.mean(raw) / top, 3),
        "level": round(statistics.mean(raw)),
        "confidence": round(statistics.mean(confs), 3),
        "spread": round(max(raw) - min(raw), 3),
        "runs": raw,
        "last_probs": probs[-1],
    }


print("=" * 100)
print(f"TEST 9 — JEMNOST STUPNICE  ({len(STORIES)} příběhů × {len(SCALES)} stupnic × {RUNS} běhů)")
print("=" * 100)

results = {}

# --- Část 1: Noul jako baseline -------------------------------------------
print("\n" + "=" * 100)
print("ČÁST 1 — NOUL: 'je to vhodné?'  (binární otázka)")
print("=" * 100)
print(f"\n{'PŘÍBĚH':<20} {'očekáváme':<14} {'noul':>8} {'rozptyl':>9}   interpretace")
print("-" * 92)

for sid, story in STORIES.items():
    res = run_noul(story["text"])
    results.setdefault(sid, {})["noul"] = res
    verdict = "ANO, vhodné" if res["avg"] > 0.5 else "NE, nevhodné"
    print(f"{sid:<20} {story['expected']:<14} {res['avg']:>8.3f} {res['spread']:>9.3f}   {verdict}")

# --- Část 2: Score s různou jemností --------------------------------------
print("\n" + "=" * 100)
print("ČÁST 2 — SCORE: 'jak moc je to vhodné?'  (normalizováno na 0-1 pro srovnání)")
print("=" * 100)
head = f"\n{'PŘÍBĚH':<20} {'noul':>8}"
for sname in SCALES:
    head += f" {sname:>11}"
print(head)
print("-" * len(head))

for sid, story in STORIES.items():
    row = f"{sid:<20} {results[sid]['noul']['avg']:>8.3f}"
    for sname, levels in SCALES.items():
        res = run_score(story["text"], levels)
        results[sid][sname] = res
        row += f" {res['normalized']:>11.3f}"
    print(row)

# --- Část 3: vyhodnocení ---------------------------------------------------
print("\n" + "=" * 100)
print("ČÁST 3 — VYHODNOCENÍ")
print("=" * 100)

# Rozdíl Noul vs Score
print("\nA) ROZDÍL NOUL vs. SCORE (6 úrovní) — kde se rozhodnutí rozchází?")
print(f"\n{'PŘÍBĚH':<20} {'noul':>8} {'score':>8} {'rozdíl':>9}   {'co to mění'}")
print("-" * 86)
for sid in STORIES:
    n = results[sid]["noul"]["avg"]
    s = results[sid]["6 úrovní"]["normalized"]
    d = s - n
    note = ""
    if n > 0.5 and s < 0.5:
        note = "Noul říká ANO, Score říká spíš ne"
    elif abs(d) >= 0.2:
        note = f"posun o {abs(d):.2f} — Score je {'přísnější' if d < 0 else 'mírnější'}"
    print(f"{sid:<20} {n:>8.3f} {s:>8.3f} {d:>+9.3f}   {note}")

# Rozlišovací schopnost stupnic
print("\nB) ROZLIŠOVACÍ SCHOPNOST — využije model celou stupnici?")
print(f"\n{'STUPNICE':<14} {'rozpětí':>9} {'σ':>8} {'confidence':>12} {'stabilita':>11}")
print("-" * 58)
scale_stats = {}
for sname in SCALES:
    vals = [results[sid][sname]["normalized"] for sid in STORIES]
    confs = [results[sid][sname]["confidence"] for sid in STORIES]
    spreads = [results[sid][sname]["spread"] for sid in STORIES]
    scale_stats[sname] = {
        "range": round(max(vals) - min(vals), 3),
        "stdev": round(statistics.stdev(vals), 3),
        "mean_confidence": round(statistics.mean(confs), 3),
        "max_spread": round(max(spreads), 3),
    }
    st = scale_stats[sname]
    print(f"{sname:<14} {st['range']:>9.3f} {st['stdev']:>8.3f} {st['mean_confidence']:>12.3f} "
          f"{st['max_spread']:>11.3f}")

# Shoda pořadí mezi stupnicemi
print("\nC) SHODA POŘADÍ — dávají různě jemné stupnice stejné pořadí příběhů?")
order_ref = sorted(STORIES, key=lambda s: results[s]["6 úrovní"]["normalized"])
print(f"\n  referenční pořadí (6 úrovní, od nejhoršího): {' < '.join(order_ref)}")
for sname in SCALES:
    order = sorted(STORIES, key=lambda s: results[s][sname]["normalized"])
    same = "✓ shodné" if order == order_ref else "✗ LIŠÍ SE: " + " < ".join(order)
    print(f"  {sname:<14} {same}")

save_result("test_9_jemnost_skaly", {
    "stories": {k: v["text"] for k, v in STORIES.items()},
    "scales": SCALES, "results": results, "scale_stats": scale_stats,
})
print("\nUloženo: results/test_9_jemnost_skaly.json")
