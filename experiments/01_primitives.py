"""
TEST 1 — Tři primitiva nad stejnými vstupy

Co ukazuje:
  - jak vypadá syrový API call (vypíše request i response pro první vstup)
  - jak se liší Noul / Choice / Score na stejném textu
  - že všechny tři otázky běží v JEDNOM callu paralelně

Spusť: ▶ (bez argumentů)
"""

import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, format_answer, load_json, save_result

texts = load_json("../data/inputs/texts.json")
questions = load_json("../data/questions/sentiment.json")

print("=" * 78)
print("TEST 1 — TŘI PRIMITIVA NAD STEJNÝM VSTUPEM")
print("=" * 78)

# --- Ukázka syrového requestu pro první vstup -------------------------------
first_key = next(iter(texts))
print("\n### JAK VYPADÁ REQUEST (POST https://api.typesafe.ai/v1/systemone)\n")
print(json.dumps(
    {"state": texts[first_key], "model": "jev-latest", "questions": questions},
    indent=2, ensure_ascii=False,
))

results = {}

for name, text in texts.items():
    result = ask(text, questions)
    results[name] = result

    print("\n" + "-" * 78)
    print(f"VSTUP [{name}]")
    print(f'  "{text}"')
    print(f"VÝSTUP  ({result['_latency_s']}s, "
          f"{result['usage']['input_tokens']} in / {result['usage']['output_tokens']} out)")

    for qid, answer in result["answers"].items():
        print(f"  {qid:<20} {format_answer(answer)}")

    # U prvního vstupu ukážeme i syrovou odpověď, ať je vidět přesný tvar.
    if name == first_key:
        print("\n  ### SYROVÁ ODPOVĚĎ (tvar, který parsuješ v kódu):")
        raw = {k: v for k, v in result.items() if k != "_latency_s"}
        for line in json.dumps(raw, indent=2, ensure_ascii=False).splitlines():
            print("  " + line)

path = save_result("test_1_primitiva", results)
print("\n" + "=" * 78)
print(f"Uloženo: {path}")
print("""
CO SI ODNÉST:
  Noul   -> jedno číslo 0-1, ŽÁDNÁ confidence. Absolutní: může být nízký pro vše.
  Choice -> jedna možnost + rozdělení (součet 1) + confidence. Relativní: porovnává options.
  Score  -> vážený průměr, MŮŽE padnout mezi úrovně, + confidence.
  Všechny tři přišly v JEDNOM callu -- otázky na sebe nevidí.
""")
