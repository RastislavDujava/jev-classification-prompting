"""
TEST 5 — Délka instructions: co dělá s odpovědí, s rychlostí a s cenou?

Dvě otázky naráz, protože se snadno zamění:

  A) MĚNÍ PŘÍKLADY ODPOVĚĎ?     -> to je prompt engineering kritérií
  B) STOJÍ DÉLKA SAMA LATENCI?  -> to je cena, kterou za něj platíš

Aby šly rozlišit, běží dvě řady o stejných délkách:
  "priklady"  = few-shot příklady hraničních případů (nese význam)
  "neutralni" = text o provozu pipeline, o vulgaritě neříká nic (jen zabírá tokeny)

Když se odpověď hne jen u řady "priklady", je to obsahem, ne délkou.
Když latence roste v obou stejně, je to délkou, ne obsahem.

Metodika:
  - všechny varianty nad TÝMŽ vstupním textem
  - běhy se PROKLÁDAJÍ (round-robin), aby výkyv sítě v čase nepadl na jednu skupinu
  - medián a p95 místo průměru (odolné vůči jednotlivému výkyvu)

Spusť: ▶ (bez argumentů)
"""

import statistics
import time

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, save_result

RUNS = 10
PRICE_PER_INPUT_TOKEN = 0.042 / 1_000_000

STATE = (
    "Ty vole, ta appka zase spadla. Už je to potřetí dneska, do prdele. "
    "Fakt nechápu, jak může být takový blbost v produkci."
)

BASE_INSTRUCTION = "Does this text contain vulgar or profane language?"

# ŘADA 1: příklady hraničních případů. Nesou význam -- učí model, kde je hranice.
EXAMPLES = """
Example: "Ta appka je super, díky!" -> not vulgar, plain praise with no profanity.
Example: "Do prdele, zase to spadlo." -> mild Czech colloquialism, tolerated in informal register.
Example: "Vy jste debilové." -> vulgar, direct personal insult aimed at a person.
Example: "Ty vole, to je paráda!" -> not vulgar, 'ty vole' here is an enthusiastic filler.
Example: "Jděte do piče." -> vulgar, strongest Czech profanity used aggressively.
"""

# ŘADA 2: neutrální výplň. O vulgaritě neříká nic, jen zabírá stejné místo.
NEUTRAL = """
This classification task is part of a larger content pipeline.
The pipeline was designed in several stages over multiple quarters.
Downstream systems consume the result for reporting and archival purposes.
Operational teams review aggregate statistics on a weekly cadence.
Records are retained according to the standard retention schedule.
"""


def build(block: str, target_tokens: int) -> str:
    """Poskládá instructions zhruba na cílovou délku opakováním bloku."""
    text = BASE_INSTRUCTION + "\n"
    while len(text) / 4 < target_tokens:  # ~4 znaky/token, přesnou délku vezmeme z usage
        text += block
    return text


def question(instructions: str) -> dict:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {
            "true": "Genuinely offensive language: personal insults or strongest profanity.",
            "false": "Clean, or only mild Czech colloquialisms.",
        },
    }


SIZES = [0, 500, 2000, 5000]
VARIANTS = {"holá otázka": BASE_INSTRUCTION}
for size in SIZES[1:]:
    VARIANTS[f"příklady ~{size}"] = build(EXAMPLES, size)
for size in SIZES[1:]:
    VARIANTS[f"neutrální ~{size}"] = build(NEUTRAL, size)

print("=" * 96)
print(f"TEST 5 — DÉLKA INSTRUCTIONS ({RUNS} běhů na variantu, prokládaně)")
print("=" * 96)
print(f'\nVstup (stejný pro všechny): "{STATE[:64]}..."')
print(f"Variant: {len(VARIANTS)}  |  Volání celkem: {len(VARIANTS) * RUNS}\n")

measurements = {name: {"lat": [], "noul": [], "tok": None} for name in VARIANTS}

started = time.perf_counter()
for round_no in range(RUNS):
    for name, instructions in VARIANTS.items():
        result = ask(STATE, {"is_vulgar": question(instructions)})
        measurements[name]["lat"].append(result["_latency_s"])
        measurements[name]["noul"].append(result["answers"]["is_vulgar"]["noul"])
        measurements[name]["tok"] = result["usage"]["input_tokens"]
    print(f"  kolo {round_no + 1}/{RUNS}")
total = time.perf_counter() - started
print(f"\n{len(VARIANTS) * RUNS} volání za {total:.1f}s\n")

header = (f"{'VARIANTA':<18} {'in_tok':>7} {'medián':>8} {'min':>7} {'max':>7} "
          f"{'p95':>7} {'σ':>7} {'noul':>7} {'$/1000':>9}")
print(header)
print("-" * len(header))

rows = {}
for name, data in measurements.items():
    lat = sorted(data["lat"])
    rows[name] = {
        "input_tokens": data["tok"],
        "median_s": round(statistics.median(lat), 3),
        "min_s": round(min(lat), 3),
        "max_s": round(max(lat), 3),
        "p95_s": round(lat[int(len(lat) * 0.95) - 1], 3),
        "stdev_s": round(statistics.stdev(lat), 3),
        "noul_avg": round(statistics.mean(data["noul"]), 4),
        "noul_all": data["noul"],
        "cost_per_1000_usd": round(data["tok"] * PRICE_PER_INPUT_TOKEN * 1000, 4),
        "latencies": data["lat"],
    }
    r = rows[name]
    if name.startswith("neutrální ~500"):
        print("-" * len(header))
    print(f"{name:<18} {r['input_tokens']:>7,} {r['median_s']:>7.3f}s {r['min_s']:>6.3f}s "
          f"{r['max_s']:>6.3f}s {r['p95_s']:>6.3f}s {r['stdev_s']:>6.3f}s "
          f"{r['noul_avg']:>7.3f} ${r['cost_per_1000_usd']:>8.4f}")

# --- Vyhodnocení ------------------------------------------------------------
base = rows["holá otázka"]

print("\n" + "=" * 96)
print("A) MĚNÍ OBSAH ODPOVĚĎ?  (stejná délka, jiný obsah)")
print("=" * 96)
print(f"\n{'délka':<10} {'s příklady':>12} {'neutrální':>12} {'rozdíl':>10}")
print("-" * 48)
print(f"{'holá':<10} {base['noul_avg']:>12.3f} {'—':>12} {'—':>10}")
for size in SIZES[1:]:
    ex = rows[f"příklady ~{size}"]["noul_avg"]
    nu = rows[f"neutrální ~{size}"]["noul_avg"]
    print(f"{'~' + str(size):<10} {ex:>12.3f} {nu:>12.3f} {ex - nu:>+10.3f}")

print("\n" + "=" * 96)
print("B) STOJÍ DÉLKA LATENCI?  (medián proti holé otázce)")
print("=" * 96)
print(f"\n{'VARIANTA':<18} {'tokeny':>9} {'medián':>9} {'rozdíl':>9} {'cena':>9}")
print("-" * 60)
for name, r in rows.items():
    print(f"{name:<18} {r['input_tokens'] / base['input_tokens']:>8.1f}× "
          f"{r['median_s']:>8.3f}s {r['median_s'] - base['median_s']:>+8.3f}s "
          f"{r['cost_per_1000_usd'] / base['cost_per_1000_usd']:>8.1f}×")

ex_spread = max(rows[f"příklady ~{s}"]["noul_avg"] for s in SIZES[1:]) - \
            min(rows[f"příklady ~{s}"]["noul_avg"] for s in SIZES[1:])
nu_spread = max(rows[f"neutrální ~{s}"]["noul_avg"] for s in SIZES[1:]) - \
            min(rows[f"neutrální ~{s}"]["noul_avg"] for s in SIZES[1:])

print(f"\nRozptyl odpovědí uvnitř řady 'příklady':  {ex_spread:.3f}")
print(f"Rozptyl odpovědí uvnitř řady 'neutrální': {nu_spread:.3f}")

path = save_result("test_5_delka_vs_rychlost", rows)
print(f"\nUloženo: {path}")
print("""
JAK ČÍST:
  Hne-li se odpověď jen u řady 'příklady' -> za změnu může OBSAH, ne délka.
  Roste-li latence v obou řadách stejně   -> za zpomalení může DÉLKA, ne obsah.
  p95 = pomalejší konec, to co uvidí nejhůř obsloužený uživatel.
""")
