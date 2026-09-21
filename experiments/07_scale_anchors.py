"""
TEST 8 — Ukotvení škály, přepracovaný pokus

Co bylo špatně v testu 7:
  1. Příběh byl česky, zadání anglicky -- neřízená proměnná
  2. Ablace čísel se dělala na KRAJNÍCH příbězích (0,88-0,98), kde je strop
  3. Posun čísel byl mírný (0,95->0,70)
  4. Kotvy byly jen v instructions, ne v criteria

Co je jinak teď:
  1. Všechno anglicky
  2. Jeden příběh CÍLENĚ do prostředního pásma 0,55-0,70, kde je prostor na obě strany
  3. Testujeme čtyři umístění kotev: nikde / instructions / criteria.true / obojí
  4. Ablace čísel je DRASTICKÁ -- původní, posunutá dolů, a obrácená škála

Hypotéza uživatele: bez dobrých kritérií model dá průměrně 0,8-0,9;
s dobře umístěnými kotvami se přiblíží zamýšlenému pásmu 0,55-0,70.

Spusť: ▶ (bez argumentů)
"""

import statistics

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, save_result

RUNS = 10

# ---------------------------------------------------------------------------
# VSTUPNÍ TEXT — anglicky, tři odstavce, dětský jazyk, cíleně do pásma 0,55-0,70
# Záměr: skutečné nebezpečí a zranění, popsané bez drastických detailů,
# plně vyřešené do konce. Žádná smrt, žádná krev, ale ani bezstarostná idylka.
# ---------------------------------------------------------------------------
STORY = """Pip was a small brown rabbit who lived at the edge of the meadow with his mother and his two sisters. Every morning he liked to hop down to the stream to watch the water beetles skate across the surface. His mother always told him to stay where he could still see the big oak tree, because that was how a rabbit knew the way home. Pip always promised that he would.

One afternoon a butterfly with orange wings drifted past him, and Pip followed it without thinking. He hopped over the stones, through the tall grass, and under a fallen branch, and when he finally looked up the oak tree was nowhere to be seen. The sky had turned grey. Pip tried to run back the way he had come, but his back leg slipped between two rocks and caught fast, and when he pulled it free it hurt so much that he could not stand on it. He sat down in the wet grass and cried, and the rain began to fall, and he was very frightened and very cold.

It was an old badger who found him, snuffling along the hedgerow on her evening walk. She did not say much. She wrapped Pip in dry leaves, carried him carefully on her broad back, and followed the smell of rabbit until she found the burrow under the oak. Pip's mother held him for a long time without saying anything at all. His leg was sore for many days and he had to stay inside while his sisters played, which he thought was terribly unfair. But it healed, and by the time the leaves turned he could hop again, and he never once forgot to look for the oak tree after that."""

QUESTION = "Is this animal story suitable for children aged 5 to 7?"

# --- Kotvy: popisy úrovní ---------------------------------------------------
ANCHOR_BODY = (
    "0.95-1.00 — Entirely gentle. Nothing bad happens at all. The animals play, help "
    "each other, or solve a small friendly problem. A child finishes it smiling.\n"
    "0.75-0.90 — Mild worry that resolves quickly. A character is briefly lost, sad or "
    "startled, but is comforted within a page and the ending is warm and safe.\n"
    "0.55-0.70 — Real danger or real injury. The character is genuinely hurt or "
    "frightened for a sustained part of the story, and suffers a lasting consequence "
    "such as pain or being unable to play. Nothing is described in graphic detail and "
    "it is fully resolved by the end, but the child feels the weight of it.\n"
    "0.35-0.50 — Something genuinely frightening or sad happens off-screen, or a threat "
    "is still unresolved when the story ends. Not graphic, but not comforting either.\n"
    "0.15-0.30 — Death or permanent loss happens on-screen, handled gently, but a child "
    "of this age would need an adult to talk it through afterwards.\n"
    "0.00-0.10 — Graphic violence, hunting described in physical detail, blood, or "
    "suffering shown directly. Clearly unsuitable."
)

ANCHOR_INTRO = "Use the full scale. Calibrate your answer against these anchor points:\n"
ANCHORS = ANCHOR_INTRO + ANCHOR_BODY

PLAIN_TRUE = "Suitable: the story is gentle and a child of 5-7 finishes it feeling safe."
PLAIN_FALSE = ("Unsuitable: the story contains death, violence, or themes a child of "
               "this age cannot process without an adult.")

# ---------------------------------------------------------------------------
# ČÁST 1 — kde mají kotvy být?
# ---------------------------------------------------------------------------
PLACEMENTS = {
    "1 nikde (holý Noul)": {
        "type": "noul",
        "instructions": QUESTION,
    },
    "2 jen popisná criteria": {
        "type": "noul",
        "instructions": QUESTION,
        "criteria": {"true": PLAIN_TRUE, "false": PLAIN_FALSE},
    },
    "3 kotvy v instructions": {
        "type": "noul",
        "instructions": QUESTION + "\n\n" + ANCHORS,
        "criteria": {"true": PLAIN_TRUE, "false": PLAIN_FALSE},
    },
    "4 kotvy v criteria.true": {
        "type": "noul",
        "instructions": QUESTION,
        "criteria": {
            "true": PLAIN_TRUE + "\n\n" + ANCHORS,
            "false": PLAIN_FALSE,
        },
    },
    "5 kotvy v obou": {
        "type": "noul",
        "instructions": QUESTION + "\n\n" + ANCHORS,
        "criteria": {
            "true": PLAIN_TRUE + "\n\n" + ANCHORS,
            "false": PLAIN_FALSE,
        },
    },
}

# ---------------------------------------------------------------------------
# ČÁST 2 — reagují samotná ČÍSLA? Popisy zůstávají slovo od slova stejné.
# ---------------------------------------------------------------------------
def renumber(pairs) -> str:
    """Vezme popisy z ANCHOR_BODY a přiřadí jim jiná čísla."""
    descriptions = [line.split(" — ", 1)[1] for line in ANCHOR_BODY.split("\n")]
    return ANCHOR_INTRO + "\n".join(
        f"{lo} — {desc}" for lo, desc in zip(pairs, descriptions)
    )


NUMBER_SETS = {
    "A původní (0,55-0,70 pro tenhle příběh)": ["0.95-1.00", "0.75-0.90", "0.55-0.70",
                                                 "0.35-0.50", "0.15-0.30", "0.00-0.10"],
    "B posunuté dolů (cílové pásmo 0,25-0,35)": ["0.60-0.70", "0.40-0.55", "0.25-0.35",
                                                  "0.15-0.22", "0.05-0.12", "0.00-0.03"],
    "C stlačené nahoru (cílové pásmo 0,85-0,90)": ["0.98-1.00", "0.93-0.97", "0.85-0.90",
                                                    "0.75-0.82", "0.60-0.70", "0.40-0.55"],
    "D OBRÁCENÁ škála (gentle=0, graphic=1)": ["0.00-0.05", "0.10-0.25", "0.30-0.45",
                                                "0.50-0.65", "0.70-0.85", "0.95-1.00"],
}


def run(question: dict, runs: int = RUNS) -> dict:
    values, latencies = [], []
    for _ in range(runs):
        r = ask(STORY, {"q": question})
        a = r["answers"]["q"]
        values.append(a["noul"] if a["type"] == "noul" else a["score"])
        latencies.append(r["_latency_s"])
    return {
        "runs": values,
        "avg": round(statistics.mean(values), 3),
        "median": round(statistics.median(values), 3),
        "spread": round(max(values) - min(values), 3),
        "median_latency": round(statistics.median(latencies), 3),
    }


TARGET_LO, TARGET_HI = 0.55, 0.70

print("=" * 96)
print(f"TEST 8 — UKOTVENÍ ŠKÁLY, PŘEPRACOVANÝ POKUS  ({RUNS} běhů na variantu)")
print("=" * 96)
print(f"\nPříběh: Pip the rabbit ({len(STORY)} znaků, 3 odstavce, anglicky)")
print(f"Zamýšlené pásmo: {TARGET_LO}-{TARGET_HI}  (skutečné zranění, vyřešené, bez drastičnosti)")

# --- ČÁST 1 ---------------------------------------------------------------
print("\n" + "=" * 96)
print("ČÁST 1 — KDE MAJÍ KOTVY BÝT?")
print("=" * 96)
head = f"\n{'UMÍSTĚNÍ':<26} {'průměr':>8} {'medián':>8} {'rozptyl':>9} {'v pásmu?':>10} {'latence':>9}"
print(head)
print("-" * len(head))

part1 = {}
for name, question in PLACEMENTS.items():
    res = run(question)
    part1[name] = res
    in_band = TARGET_LO <= res["avg"] <= TARGET_HI
    print(f"{name:<26} {res['avg']:>8.3f} {res['median']:>8.3f} {res['spread']:>9.3f} "
          f"{'✓ ANO' if in_band else '✗ ne':>10} {res['median_latency']:>8.2f}s")

baseline = part1["1 nikde (holý Noul)"]["avg"]
best_name = min(part1, key=lambda k: abs(part1[k]["avg"] - (TARGET_LO + TARGET_HI) / 2))
print(f"\nHolý Noul: {baseline:.3f}   Nejblíž cílovému pásmu: {best_name} "
      f"({part1[best_name]['avg']:.3f})")

# --- ČÁST 2 ---------------------------------------------------------------
print("\n" + "=" * 96)
print("ČÁST 2 — REAGUJÍ SAMOTNÁ ČÍSLA?  (popisy slovo od slova stejné)")
print("=" * 96)
print("\nKotvy vloženy do criteria.true (umístění č. 4).\n")
head2 = f"{'SADA ČÍSEL':<44} {'cíl':>11} {'naměřeno':>10} {'odchylka':>10}"
print(head2)
print("-" * len(head2))

part2 = {}
for name, numbers in NUMBER_SETS.items():
    anchors = renumber(numbers)
    question = {
        "type": "noul",
        "instructions": QUESTION,
        "criteria": {"true": PLAIN_TRUE + "\n\n" + anchors, "false": PLAIN_FALSE},
    }
    res = run(question)
    part2[name] = res
    target = numbers[2]  # třetí úroveň = pásmo, kam příběh patří
    lo, hi = (float(x) for x in target.split("-"))
    mid = (lo + hi) / 2
    res["target_band"] = target
    res["deviation"] = round(res["avg"] - mid, 3)
    print(f"{name:<44} {target:>11} {res['avg']:>10.3f} {res['deviation']:>+10.3f}")

values = [r["avg"] for r in part2.values()]
total_spread = max(values) - min(values)
print(f"\nRozpětí mezi sadami čísel: {total_spread:.3f}")
print(f"  {'✓ ČÍSLA ÚČINKUJÍ' if total_spread >= 0.15 else '✗ čísla model ignoruje (rozpětí pod 0,15)'}")

if total_spread < 0.15:
    print("\n  Kdyby model čísla četl, obrácená škála (D) by dala pravý opak původní (A).")
    print(f"  A = {part2['A původní (0,55-0,70 pro tenhle příběh)']['avg']:.3f}   "
          f"D = {part2['D OBRÁCENÁ škála (gentle=0, graphic=1)']['avg']:.3f}")

# --- ČÁST 3: Score pro srovnání -------------------------------------------
print("\n" + "=" * 96)
print("ČÁST 3 — SCORE se stejnými popisy (pro srovnání)")
print("=" * 96)
score_q = {
    "type": "score",
    "instructions": "How suitable is this animal story for children aged 5 to 7?",
    "criteria": [
        "Graphic violence, hunting in physical detail, blood or suffering shown directly",
        "Death or permanent loss on-screen, handled gently, needs an adult to explain",
        "Something frightening or sad happens off-screen, or a threat is left unresolved",
        "Real danger or injury with a lasting consequence, no graphic detail, fully resolved by the end",
        "Mild worry that resolves quickly; brief fear, then comfort and a warm ending",
        "Entirely gentle; nothing bad happens, the child finishes it smiling",
    ],
}
score_res = run(score_q)
print(f"\nScore (0-5): {score_res['avg']:.2f}   "
      f"= úroveň {round(score_res['avg'])} ({score_q['criteria'][round(score_res['avg'])][:50]}…)")
print(f"Normalizováno na 0-1: {score_res['avg'] / 5:.3f}")
print(f"Zamýšlená úroveň: 3 (real danger, resolved) = 0.600 po normalizaci")

save_result("test_8_kotvy_umisteni", {
    "story": STORY, "target_band": [TARGET_LO, TARGET_HI],
    "placements": part1, "number_sets": part2, "score": score_res,
    "anchor_body": ANCHOR_BODY,
})
print("\nUloženo: results/test_8_kotvy_umisteni.json")
