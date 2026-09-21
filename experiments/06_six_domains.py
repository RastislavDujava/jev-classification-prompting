"""
Spustí všechny domény z data/domains/*.json proti Jev API.

Pro každý pár a každou variantu zadání provede RUNS běhů a uloží
syrová čísla i vyhodnocení do review_data.json, které čte review.html.

Doména 'personal' má zvláštní zacházení: varianty tam nejsou stupně
propracovanosti, ale ROZDÍLNÉ UŽIVATELSKÉ PROFILY. Horní půlka se hodnotí
přísným profilem, dolní uvolněným.

Spusť: ▶ (bez argumentů)
"""

import json
import statistics
import time
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask

RUNS = 5
THRESHOLD = 0.5
NOISE = 0.05  # posun pod touto hranicí je šum (změřeno v testu 2)

HERE = Path(__file__).parent
DOMAINS_DIR = HERE.parent / "data" / "domains"


def evaluate(text: str, variant: dict) -> dict:
    """Pustí jednu otázku RUNS× a vrátí souhrn. Selhání jednoho běhu běh nezastaví."""
    question = {
        "type": "noul",
        "instructions": variant["instructions"],
        "criteria": variant["criteria"],
    }
    runs, latencies, tokens, failures = [], [], None, 0
    for _ in range(RUNS):
        try:
            r = ask(text, {"q": question})
        except RuntimeError as exc:
            failures += 1
            print(f"      ! běh selhal: {exc}")
            continue
        runs.append(r["answers"]["q"]["noul"])
        latencies.append(r["_latency_s"])
        tokens = r["usage"]["input_tokens"]

    if not runs:  # ani jeden běh neprošel
        return {"runs": [], "avg": None, "spread": None, "median_latency": None,
                "input_tokens": None, "failures": failures, "failed": True}

    return {
        "failures": failures,
        "runs": runs,
        "avg": round(statistics.mean(runs), 3),
        "spread": round(max(runs) - min(runs), 3),
        "median_latency": round(statistics.median(latencies), 3),
        "input_tokens": tokens,
    }


def variant_for(domain: dict, vname: str, slot: str) -> dict:
    """U personalizace vybírá variantu podle profilu, jinak podle názvu."""
    if domain["domain_id"] == "personal" and vname == "B_profile":
        key = "B_strict_profile" if slot == "top" else "B_relaxed_profile"
        return domain["variants"][key]
    return domain["variants"][vname]


def variant_names(domain: dict) -> list:
    if domain["domain_id"] == "personal":
        return ["A_naive", "B_profile"]
    return list(domain["variants"].keys())


domains = []
for path in sorted(DOMAINS_DIR.glob("d*.json")):
    domains.append(json.loads(path.read_text(encoding="utf-8")))

total_calls = sum(
    len(d["pairs"]) * 2 * len(variant_names(d)) * RUNS for d in domains
)
print("=" * 90)
print(f"SPOUŠTÍM {len(domains)} domén · {sum(len(d['pairs']) for d in domains)} párů "
      f"· {RUNS} běhů = {total_calls} volání")
print("=" * 90)

started = time.perf_counter()
done_calls = 0

for domain in domains:
    vnames = variant_names(domain)
    labels = domain["answer_labels"]
    print(f"\n### {domain['title_cs']}  ({len(domain['pairs'])} párů, varianty: {', '.join(vnames)})")

    for pair in domain["pairs"]:
        pair["results"] = {}
        for slot in ("top", "bottom"):
            item = pair[slot]
            item_results = {}
            for vname in vnames:
                variant = variant_for(domain, vname, slot)
                res = evaluate(item["text"], variant)
                if res.get("failed"):
                    res["predicted"] = None
                    res["correct"] = False
                else:
                    predicted = labels["true"] if res["avg"] > THRESHOLD else labels["false"]
                    res["predicted"] = predicted
                    res["correct"] = predicted == item["expected"]
                # u personalizace si uložíme i použité znění, ať je v HTML vidět
                if domain["domain_id"] == "personal":
                    res["used_instructions"] = variant["instructions"]
                    res["used_criteria"] = variant["criteria"]
                item_results[vname] = res
                done_calls += RUNS
            pair["results"][slot] = item_results

        # Souhrn páru: zlepšila poučená varianta oproti naivní?
        first, last = vnames[0], vnames[-1]
        base_ok = sum(pair["results"][s][first]["correct"] for s in ("top", "bottom"))
        best_ok = sum(pair["results"][s][last]["correct"] for s in ("top", "bottom"))
        shifts = [
            abs(pair["results"][s][last]["avg"] - pair["results"][s][first]["avg"])
            for s in ("top", "bottom")
            if pair["results"][s][last]["avg"] is not None
            and pair["results"][s][first]["avg"] is not None
        ]
        shift = max(shifts) if shifts else 0.0
        pair["summary"] = {
            "baseline_correct": base_ok,
            "improved_correct": best_ok,
            "gain": best_ok - base_ok,
            "max_shift": round(shift, 3),
            "proven": (best_ok > base_ok) and (shift >= NOISE),
        }
        mark = "✓ PROKÁZÁNO" if pair["summary"]["proven"] else (
            "= beze změny" if pair["summary"]["gain"] == 0 else "✗ zhoršilo")
        print(f"  {pair['pair_id']:<22} {base_ok}/2 → {best_ok}/2  "
              f"posun {shift:>5.2f}  {mark}   [{done_calls}/{total_calls}]", flush=True)

    # Průběžné uložení po každé doméně -- výpadek sítě pak nesmaže hotovou práci.
    (HERE.parent / "results" / "domains_run.partial.json").write_text(
        json.dumps({"domains": domains}, indent=2, ensure_ascii=False), encoding="utf-8")

elapsed = time.perf_counter() - started

# --- Souhrn po doménách ---------------------------------------------------
print("\n" + "=" * 90)
print("SOUHRN PO DOMÉNÁCH")
print("=" * 90)
print(f"\n{'DOMÉNA':<34} {'naivní':>10} {'poučená':>10} {'prokázáno':>11}")
print("-" * 70)

for domain in domains:
    vnames = variant_names(domain)
    first, last = vnames[0], vnames[-1]
    n = len(domain["pairs"]) * 2
    base = sum(p["results"][s][first]["correct"] for p in domain["pairs"] for s in ("top", "bottom"))
    best = sum(p["results"][s][last]["correct"] for p in domain["pairs"] for s in ("top", "bottom"))
    proven = sum(1 for p in domain["pairs"] if p["summary"]["proven"])
    domain["domain_summary"] = {
        "baseline_accuracy": round(base / n, 3),
        "improved_accuracy": round(best / n, 3),
        "baseline_correct": base, "improved_correct": best, "total_items": n,
        "pairs_proven": proven, "pairs_total": len(domain["pairs"]),
    }
    print(f"{domain['title_cs'][:33]:<34} {base}/{n} {base/n*100:>5.0f}% "
          f"{best}/{n} {best/n*100:>5.0f}% {proven:>6}/{len(domain['pairs'])}")

out = {
    "generated": time.strftime("%Y-%m-%d %H:%M"),
    "model": "jev-1.13.0",
    "status": f"OTESTOVÁNO — {RUNS} běhů na variantu",
    "runs": RUNS,
    "threshold": THRESHOLD,
    "noise_floor": NOISE,
    "elapsed_s": round(elapsed, 1),
    "total_calls": total_calls,
    "domains": domains,
    "total_pairs": sum(len(d["pairs"]) for d in domains),
}
(HERE.parent / "results" / "domains_run.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\nHotovo za {elapsed/60:.1f} min · {total_calls} volání")
print(f"Uloženo: review_data.json")
