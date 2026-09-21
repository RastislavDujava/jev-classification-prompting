"""
TEST 12 — Výkon na češtině proti angličtině

Dokumentace varuje: "English is the primary training language and where accuracy
is currently best. Other languages are handled but not equally well."

Dosud jsme měli jen jednu větu. Tenhle test měří na 15 párech, kde KAŽDÁ položka
existuje v češtině i angličtině se shodným obsahem.

Měříme dvě věci:
  1. PŘESNOST -- liší se počet správných odpovědí mezi jazyky?
  2. SHODA hodnot -- dá model na tentýž obsah podobné číslo v obou jazycích?

Druhá věc je pro praxi důležitější: když stavíte klasifikátor pro české uživatele
a ladíte práh na anglických datech, musíte vědět, jestli se přenese.

Zadání otázky je VŽDY anglicky -- mění se jen jazyk hodnoceného textu.
(Varianta s českým zadáním je v části 3.)

Spusť: ▶ (bez argumentů)
"""

import json
import statistics
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, save_result

RUNS = 5
THRESHOLD = 0.5

HERE = Path(__file__).parent
PAIRS = json.loads((HERE / "../data/inputs/bilingual.json").read_text(encoding="utf-8"))["pairs"]

# Zadání anglicky -- mění se jen jazyk textu ve `state`.
QUESTION_EN = {
    "type": "noul",
    "instructions": "Is the author of this message expressing dissatisfaction with a product or service?",
    "criteria": {
        "true": "The author is complaining: reporting a problem, expressing frustration, "
                "or criticising what they received. This includes polite or indirect "
                "complaints, sarcasm, and understatement.",
        "false": "The author is not complaining: they are satisfied, neutral, asking a "
                 "question, or describing a problem that happened to someone else or did "
                 "not happen at all.",
    },
}

# Totéž zadání v češtině -- pro část 3.
QUESTION_CS = {
    "type": "noul",
    "instructions": "Vyjadřuje autor této zprávy nespokojenost s produktem nebo službou?",
    "criteria": {
        "true": "Autor si stěžuje: hlásí problém, vyjadřuje frustraci nebo kritizuje to, "
                "co dostal. Patří sem i zdvořilé nebo nepřímé stížnosti, sarkasmus "
                "a zlehčování.",
        "false": "Autor si nestěžuje: je spokojený, neutrální, ptá se na něco, nebo "
                 "popisuje problém, který se stal někomu jinému nebo se nestal vůbec.",
    },
}


def measure(text: str, question: dict) -> dict:
    vals = [ask(text, {"q": question})["answers"]["q"]["noul"] for _ in range(RUNS)]
    return {"avg": round(statistics.mean(vals), 3),
            "spread": round(max(vals) - min(vals), 3),
            "runs": vals}


print("=" * 100)
print(f"TEST 12 — ČEŠTINA vs. ANGLIČTINA  ({len(PAIRS)} párů × {RUNS} běhů)")
print("=" * 100)

results = {}

# --- ČÁST 1+2: anglické zadání, oba jazyky textu --------------------------
print("\n" + "=" * 100)
print("ZADÁNÍ ANGLICKY, TEXT V OBOU JAZYCÍCH")
print("=" * 100)
head = f"\n{'ID':<24} {'čekáme':>7} {'EN':>7} {'CS':>7} {'rozdíl':>8} {'shoda':>7}"
print(head)
print("-" * len(head))

ok_en = ok_cs = 0
diffs = []

for p in PAIRS:
    r_en = measure(p["en"], QUESTION_EN)
    r_cs = measure(p["cs"], QUESTION_EN)
    results[p["id"]] = {"note": p["note"], "expected": p["expected"],
                        "en": r_en, "cs": r_cs}

    pred_en = r_en["avg"] > THRESHOLD
    pred_cs = r_cs["avg"] > THRESHOLD
    ok_en += pred_en == p["expected"]
    ok_cs += pred_cs == p["expected"]
    diff = r_cs["avg"] - r_en["avg"]
    diffs.append(abs(diff))
    agree = pred_en == pred_cs

    mark_en = "✓" if pred_en == p["expected"] else "✗"
    mark_cs = "✓" if pred_cs == p["expected"] else "✗"
    print(f"{p['id']:<24} {str(p['expected']):>7} "
          f"{r_en['avg']:>6.3f}{mark_en} {r_cs['avg']:>6.3f}{mark_cs} "
          f"{diff:>+8.3f} {'✓' if agree else '✗ LIŠÍ':>7}")

n = len(PAIRS)
print(f"\n{'PŘESNOST':<24} EN: {ok_en}/{n} ({ok_en/n*100:.0f}%)   "
      f"CS: {ok_cs}/{n} ({ok_cs/n*100:.0f}%)")
print(f"{'PRŮMĚRNÝ |rozdíl|':<24} {statistics.mean(diffs):.3f}")
print(f"{'MAXIMÁLNÍ |rozdíl|':<24} {max(diffs):.3f}")
agreements = sum(1 for p in PAIRS
                 if (results[p['id']]['en']['avg'] > THRESHOLD) ==
                    (results[p['id']]['cs']['avg'] > THRESHOLD))
print(f"{'SHODA ROZHODNUTÍ':<24} {agreements}/{n} ({agreements/n*100:.0f}%)")

# --- ČÁST 3: české zadání na český text -----------------------------------
print("\n" + "=" * 100)
print("ČÁST 3 — POMŮŽE ČESKÉ ZADÁNÍ NA ČESKÝ TEXT?")
print("=" * 100)
print(f"\n{'ID':<24} {'čekáme':>7} {'CS text/EN zadání':>18} {'CS text/CS zadání':>18} {'rozdíl':>8}")
print("-" * 82)

ok_cscs = 0
for p in PAIRS:
    r = measure(p["cs"], QUESTION_CS)
    results[p["id"]]["cs_question_cs"] = r
    pred = r["avg"] > THRESHOLD
    ok_cscs += pred == p["expected"]
    prev = results[p["id"]]["cs"]["avg"]
    mark = "✓" if pred == p["expected"] else "✗"
    print(f"{p['id']:<24} {str(p['expected']):>7} {prev:>17.3f} "
          f"{r['avg']:>17.3f}{mark} {r['avg'] - prev:>+8.3f}")

print(f"\n{'PŘESNOST':<24} CS text + EN zadání: {ok_cs}/{n} ({ok_cs/n*100:.0f}%)   "
      f"CS text + CS zadání: {ok_cscs}/{n} ({ok_cscs/n*100:.0f}%)")

# --- Shrnutí --------------------------------------------------------------
print("\n" + "=" * 100)
print("SHRNUTÍ")
print("=" * 100)
print(f"""
  Anglický text, anglické zadání:   {ok_en}/{n}  ({ok_en/n*100:.0f} %)
  Český text, anglické zadání:      {ok_cs}/{n}  ({ok_cs/n*100:.0f} %)
  Český text, české zadání:         {ok_cscs}/{n}  ({ok_cscs/n*100:.0f} %)

  Průměrný rozdíl hodnot mezi jazyky: {statistics.mean(diffs):.3f}
  Shoda rozhodnutí napříč jazyky:     {agreements}/{n}

  Práh šumu modelu je 0,05 — rozdíly pod touto hranicí nejsou efekt jazyka.
""")

# Kde se to rozešlo nejvíc
worst = sorted(PAIRS, key=lambda p: -abs(results[p["id"]]["cs"]["avg"] -
                                          results[p["id"]]["en"]["avg"]))[:4]
print("  Největší rozdíly mezi jazyky:")
for p in worst:
    r = results[p["id"]]
    d = r["cs"]["avg"] - r["en"]["avg"]
    print(f"    {p['id']:<24} {d:>+7.3f}   {p['note']}")

save_result("test_12_cestina", {
    "pairs": PAIRS, "results": results,
    "question_en": QUESTION_EN, "question_cs": QUESTION_CS,
    "accuracy": {"en_text_en_q": ok_en, "cs_text_en_q": ok_cs,
                 "cs_text_cs_q": ok_cscs, "total": n},
    "mean_abs_diff": round(statistics.mean(diffs), 3),
    "decision_agreement": agreements,
})
print("\nUloženo: results/test_12_cestina.json")
