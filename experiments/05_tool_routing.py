"""
TEST 6 — Tool routing: má model odpovědět sám, nebo googlit?

Proč právě tahle úloha: na rozdíl od vulgarity tu EXISTUJE objektivně správná
odpověď. Zároveň jde o doménu, kde model musí mít vlastní bias -- rozhoduje
o tom, co sám neví (knowledge cutoff). Pokud jde bias zlomit příklady,
uvidíme to jako nárůst přesnosti proti ručně označené sadě.

Tři varianty zadání, od nejnaivnější po nejpoučenější:
  A) NAIVNÍ   -- "potřebuje to vyhledávání?"          (jak by to napsal každý)
  B) POUČENÁ  -- criteria vysvětlují knowledge cutoff  (bez příkladů)
  C) PŘÍKLADY -- poučená + 6 hraničních příkladů

Měří se PŘESNOST proti expected labelům, ne posun jednoho čísla.

Spusť: ▶ (bez argumentů)
"""

import json
import statistics
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, save_result

RUNS = 3
THRESHOLD = 0.5  # noul > 0.5 -> "search"

data = json.loads((Path(__file__).parent / "../data/inputs/routing_queries.json").read_text(encoding="utf-8"))
QUERIES = data["queries"]

# --- A) NAIVNÍ: jak by otázku napsal někdo, kdo o knowledge cutoff nepřemýšlí ---
VARIANT_A = {
    "type": "noul",
    "instructions": "Does answering this user query require searching the internet?",
    "criteria": {
        "true": "The query needs a web search to answer",
        "false": "The AI model can answer from its own knowledge",
    },
}

# --- B) POUČENÁ: criteria vysvětlují, v čem je problém. Bez příkladů. ---
CUTOFF_TRUE = (
    "The answer depends on information that may have changed since the model's training "
    "data was collected. This includes: current office holders (presidents, CEOs, popes), "
    "live data (weather, prices, scores), latest software versions, current market "
    "recommendations, and the present status of companies or products. Even if the model "
    "has a confident answer stored, that answer may now be outdated."
)
CUTOFF_FALSE = (
    "The answer is stable over time and will not have changed since training. This includes: "
    "historical events that are settled, physical and mathematical constants, established "
    "scientific explanations, language translation, and programming techniques that have "
    "been stable for years."
)

VARIANT_B = {
    "type": "noul",
    "instructions": "Does answering this user query require calling a web search tool, rather than relying on the model's own trained knowledge?",
    "criteria": {"true": CUTOFF_TRUE, "false": CUTOFF_FALSE},
}

# --- C) PŘÍKLADY: totéž + hraniční dvojice, kde se naivní klasifikátor plete ---
EXAMPLES = """

Examples of the distinction:
"Who is the current Pope?" -> search. Popes change; a stored answer may be stale.
"Who was the Pope during World War II?" -> model. A settled historical fact.
"Who is the CEO of Microsoft?" -> search. Leadership changes over time.
"Who founded Microsoft?" -> model. Founding facts never change.
"What is the latest version of Node.js?" -> search. Version numbers drift constantly.
"How do I read a file in Node.js?" -> model. The technique has been stable for years.
"""

VARIANT_C = {
    "type": "noul",
    "instructions": VARIANT_B["instructions"] + EXAMPLES,
    "criteria": {"true": CUTOFF_TRUE, "false": CUTOFF_FALSE},
}

VARIANTS = {"A naivní": VARIANT_A, "B poučená": VARIANT_B, "C s příklady": VARIANT_C}

print("=" * 104)
print(f"TEST 6 — TOOL ROUTING ({len(QUERIES)} dotazů × {len(VARIANTS)} variant × {RUNS} běhů)")
print("=" * 104)

results = {name: {} for name in VARIANTS}

for round_no in range(RUNS):
    for name, question in VARIANTS.items():
        for q in QUERIES:
            r = ask(q["text"], {"needs_search": question})
            results[name].setdefault(q["id"], []).append(r["answers"]["needs_search"]["noul"])
    print(f"  kolo {round_no + 1}/{RUNS}")

# --- Tabulka po dotazech --------------------------------------------------
print("\n" + "=" * 104)
print("VÝSLEDKY PO DOTAZECH  (noul = pravděpodobnost 'potřebuje vyhledávání')")
print("=" * 104)
head = f"{'DOTAZ':<42} {'správně':>8} {'A':>7} {'B':>7} {'C':>7}   {'A/B/C hodnocení':<18}"
print(head)
print("-" * len(head))

scores = {name: {"correct": 0, "errors": []} for name in VARIANTS}

for q in QUERIES:
    row = f"{q['text'][:40]:<42} {q['expected']:>8}"
    marks = []
    for name in VARIANTS:
        avg = statistics.mean(results[name][q["id"]])
        predicted = "search" if avg > THRESHOLD else "model"
        ok = predicted == q["expected"]
        if ok:
            scores[name]["correct"] += 1
        else:
            scores[name]["errors"].append((q["id"], q["expected"], round(avg, 3)))
        row += f" {avg:>7.3f}"
        marks.append("✓" if ok else "✗")
    print(row + f"   {' '.join(marks):<18}")

# --- Přesnost --------------------------------------------------------------
print("\n" + "=" * 104)
print("PŘESNOST")
print("=" * 104)
total = len(QUERIES)
print(f"\n{'VARIANTA':<16} {'správně':>10} {'přesnost':>10}   chyby")
print("-" * 80)
for name in VARIANTS:
    c = scores[name]["correct"]
    errs = ", ".join(e[0] for e in scores[name]["errors"]) or "—"
    print(f"{name:<16} {c:>6}/{total:<4} {c / total * 100:>9.1f}%   {errs}")

# --- Kde je bias nejsilnější ----------------------------------------------
print("\n" + "=" * 104)
print("PÁROVÉ SROVNÁNÍ — tady se bias pozná nejlíp")
print("=" * 104)
pairs = [("pope_current", "pope_historical"), ("current_us_president", "who_won_election_us_2020"),
         ("react_latest", "python_sort"), ("ceo_openai", "capital_france")]
print(f"\n{'DVOJICE':<46} {'A':>16} {'B':>16} {'C':>16}")
print("-" * 98)
for a_id, b_id in pairs:
    qa = next(q for q in QUERIES if q["id"] == a_id)
    qb = next(q for q in QUERIES if q["id"] == b_id)
    line = f"{a_id + ' vs ' + b_id:<46}"
    for name in VARIANTS:
        va = statistics.mean(results[name][a_id])
        vb = statistics.mean(results[name][b_id])
        line += f" {va:>6.2f}/{vb:<6.2f} {'✓' if va > vb else '✗'} "
    print(line)
print("\n  Chceme vysoký rozdíl: první má být 'search', druhý 'model'.")

save_result("test_6_tool_routing", {
    "queries": QUERIES,
    "raw": results,
    "accuracy": {n: {"correct": s["correct"], "total": total, "errors": s["errors"]}
                 for n, s in scores.items()},
})
print(f"\nUloženo: results/test_6_tool_routing.json")
