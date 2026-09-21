"""
TEST 2 — Stabilita: stejný vstup N×

Otázka: vrátí Jev na IDENTICKÝ vstup vždy identická čísla?
Pokud ano, každý rozdíl v testu 3 je způsoben ZMĚNOU TEXTU, ne šumem modelu.
To je předpoklad, bez kterého manipulační testy nedávají smysl.

Spusť: ▶ (bez argumentů)
"""

import statistics

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, load_json, save_result

RUNS = 8
TEXTS_TO_TEST = ["mild_negative", "mixed", "polite_but_angry"]

texts = load_json("../data/inputs/texts.json")
questions = load_json("../data/questions/sentiment.json")

print("=" * 78)
print(f"TEST 2 — STABILITA ({RUNS}× stejný vstup)")
print("=" * 78)

results = {}

for name in TEXTS_TO_TEST:
    text = texts[name]
    print(f"\n{'-' * 78}\nVSTUP [{name}]\n  \"{text}\"\n")

    runs = [ask(text, questions) for _ in range(RUNS)]
    results[name] = runs

    nouls = [r["answers"]["negative_emotion"]["noul"] for r in runs]
    scores = [r["answers"]["anger_level"]["score"] for r in runs]
    choices = [r["answers"]["sentiment_category"]["choice"] for r in runs]
    latencies = [r["_latency_s"] for r in runs]

    print(f"  noul    {[f'{v:.3f}' for v in nouls]}")
    print(f"          rozptyl: {max(nouls) - min(nouls):.4f}")
    print(f"  score   {[f'{v:.2f}' for v in scores]}")
    print(f"          rozptyl: {max(scores) - min(scores):.4f}")
    print(f"  choice  {set(choices)}  {'STABILNÍ' if len(set(choices)) == 1 else 'KOLÍSÁ!'}")
    print(f"  latence min={min(latencies):.3f}s  medián={statistics.median(latencies):.3f}s  "
          f"max={max(latencies):.3f}s")

    deterministic = (max(nouls) - min(nouls) == 0
                     and max(scores) - min(scores) == 0
                     and len(set(choices)) == 1)
    print(f"\n  => {'DETERMINISTICKÉ (bit-identické)' if deterministic else 'KOLÍSÁ mezi běhy'}")

path = save_result("test_2_stabilita", results)
print("\n" + "=" * 78)
print(f"Uloženo: {path}")
print("""
PROČ TO MĚŘÍME:
  Je-li model deterministický, pak každá změna čísla v testu 3 pochází
  z úpravy textu -- ne z náhody. Bez toho by manipulační test neměl výpovědní hodnotu.
""")
