"""
TEST 3 — Manipulace: co udělá jedno slovo navíc?

Bere základní větu a její varianty (test/inputs/variants.json), pouští je přes
stejné otázky a ukazuje ROZDÍL proti základu. Tady se učíš, na co je model
citlivý a co ho nechá chladným.

Obsahuje i pokusy o prompt injection -- state není defaultně brán jako nepřátelský,
takže tohle je reálný bezpečnostní test, ne akademická hříčka.

Spusť: ▶ (bez argumentů)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, load_json, save_result

data = load_json("../data/inputs/variants.json")
questions = load_json("../data/questions/sentiment.json")
variants = data["variants"]

print("=" * 100)
print("TEST 3 — MANIPULACE VSTUPU")
print("=" * 100)
print(f"\nZÁKLAD: \"{data['base']}\"\n")

results = {}
baseline = None

header = f"{'VARIANTA':<34} {'noul':>6} {'Δ':>7}  {'choice':<9} {'score':>6} {'Δ':>7}"
print(header)
print("-" * 100)

for label, text in variants.items():
    result = ask(text, questions)
    results[label] = {"text": text, "answers": result["answers"]}

    noul = result["answers"]["negative_emotion"]["noul"]
    choice = result["answers"]["sentiment_category"]["choice"]
    score = result["answers"]["anger_level"]["score"]

    if baseline is None:
        baseline = (noul, score)
        d_noul = d_score = ""
    else:
        d_noul = f"{noul - baseline[0]:+.3f}"
        d_score = f"{score - baseline[1]:+.2f}"

    flag = "  <<<" if baseline and abs(noul - baseline[0]) >= 0.25 else ""
    print(f"{label:<34} {noul:>6.3f} {d_noul:>7}  {choice:<9} {score:>6.2f} {d_score:>7}{flag}")

path = save_result("test_3_manipulace", results)
print("\n" + "=" * 100)
print(f"Uloženo: {path}")
print("""
JAK ČÍST:
  Δ    = rozdíl proti základní větě
  <<<  = posun noulu o 0,25 a víc, tedy slovo, které měří reálnou váhu

NA CO SE DÍVAT:
  - Zabraly intenzifikátory ('slightly' vs 'unacceptably')?
  - Prorazila prompt injection, nebo model ustál?
  - Zvládl negaci a podmiňovací způsob -- nebo reaguje jen na klíčová slova?
  - Jak dopadla čeština proti angličtině? (dokumentace přiznává slabší výkon)

DÁL: uprav si test/inputs/variants.json a spusť znovu. To je celá smyčka učení.
""")
