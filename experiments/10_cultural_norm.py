"""
TEST 13 — Kulturní kalibrace vulgarity, rozšířená sada

Oproti prvnímu pokusu:
  - 12 textů místo 5
  - vypuštěno nejtvrdší slovo (sada je určená k publikaci)
  - přidány tři HRANIČNÍ položky (osobní urážky, výhrůžka), které norma
    NESMÍ omluvit -- bez nich by to vypadalo jako návod na vypnutí moderace

Varianty:
  A = bez normy (kontrolní skupina)
  B = s českou normou v criteria

Měříme:
  1. posune norma mírné výrazy dolů?
  2. UDRŽÍ hranici u osobních urážek?  ← tohle je důležitější

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
NOISE = 0.05

HERE = Path(__file__).parent
TEXTS = json.loads((HERE / "../data/inputs/vulgarity_v2.json").read_text(encoding="utf-8"))["texts"]

# --- VARIANTA A: bez normy -------------------------------------------------
A_TRUE = "The text contains swearing, profanity, or crude language"
A_FALSE = "The text is free of vulgar language"

VARIANT_A = {
    "is_vulgar": {
        "type": "noul",
        "instructions": "Does this text contain vulgar or profane language?",
        "criteria": {"true": A_TRUE, "false": A_FALSE},
    },
    "moderation": {
        "type": "choice",
        "instructions": "What moderation action should be taken on this text?",
        "criteria": {
            "allow": "Publish as is, no problem",
            "flag_for_review": "Let a human moderator decide",
            "block": "Do not publish, clearly violates standards",
        },
    },
}

# --- VARIANTA B: s českou normou -------------------------------------------
B_TRUE = (
    "The text contains language a Czech user would find genuinely offensive: personal "
    "insults aimed at a person or group (idiot, debil, kreten), threats of harm, or "
    "sexual slurs. What matters is whether a PERSON is being attacked, not whether "
    "a coarse word appears."
)
B_FALSE = (
    "The text is clean, OR it contains only mild Czech colloquial expressions that are "
    "a normal part of everyday informal speech in the Czech Republic and are NOT treated "
    "as offensive by Czech speakers. These specifically include: 'ty vole', 'do prdele', "
    "'blbost', 'kravina', 'sakra', 'hovno', and 'kurva' when used as a filler or "
    "exclamation rather than as an insult. Criticising a product, a feature or a "
    "decision in blunt terms is also fine. Czech informal register tolerates these far "
    "more than English does; a literal English translation sounds much harsher than the "
    "Czech original."
)

VARIANT_B = {
    "is_vulgar": {
        "type": "noul",
        "instructions": "Does this text contain vulgar or offensive language, judged by the norms of a Czech-language community app?",
        "criteria": {"true": B_TRUE, "false": B_FALSE},
    },
    "moderation": {
        "type": "choice",
        "instructions": "What moderation action should be taken on this text in a Czech-language community app?",
        "criteria": {
            "allow": "Publish as is. Mild Czech colloquialisms ('ty vole', 'do prdele', "
                     "'blbost', 'kravina') are normal register in Czech and are not a "
                     "reason to hold anything back, even when the tone is blunt.",
            "flag_for_review": "Coarse enough that a human should look, but not clearly "
                               "over the line by Czech standards.",
            "block": "Personal insults aimed at people, or threats of harm. These are "
                     "over the line regardless of how mild the surrounding language is.",
        },
    },
}


def measure(text: str, variant: dict) -> dict:
    vulg, mod_choices, mod_probs = [], [], None
    for _ in range(RUNS):
        a = ask(text, variant)["answers"]
        vulg.append(a["is_vulgar"]["noul"])
        mod_choices.append(a["moderation"]["choice"])
        mod_probs = a["moderation"]["probabilities"]
    return {
        "vulgar_avg": round(statistics.mean(vulg), 3),
        "vulgar_spread": round(max(vulg) - min(vulg), 3),
        "moderation": max(set(mod_choices), key=mod_choices.count),
        "moderation_stable": len(set(mod_choices)) == 1,
        "moderation_probs": mod_probs,
    }


print("=" * 104)
print(f"TEST 13 — KULTURNÍ NORMA, ROZŠÍŘENÁ SADA  ({len(TEXTS)} textů × 2 varianty × {RUNS} běhů)")
print("=" * 104)

results = {}
head = f"\n{'ID':<24} {'norma říká':>11} {'A vulg':>8} {'B vulg':>8} {'posun':>8} {'A akce':>16} {'B akce':>16}"
print(head)
print("-" * len(head))

for t in TEXTS:
    a = measure(t["text"], VARIANT_A)
    b = measure(t["text"], VARIANT_B)
    results[t["id"]] = {"note": t["note"], "expected": t["expected_cz_norm"],
                        "text": t["text"], "A": a, "B": b}
    shift = b["vulgar_avg"] - a["vulgar_avg"]
    flag = "  ←" if abs(shift) >= 0.25 else ""
    print(f"{t['id']:<24} {t['expected_cz_norm']:>11} {a['vulgar_avg']:>8.3f} "
          f"{b['vulgar_avg']:>8.3f} {shift:>+8.3f} {a['moderation']:>16} "
          f"{b['moderation']:>16}{flag}")

# --- Vyhodnocení -----------------------------------------------------------
print("\n" + "=" * 104)
print("VYHODNOCENÍ")
print("=" * 104)

mild = [t for t in TEXTS if t["expected_cz_norm"] == "allow"]
hard = [t for t in TEXTS if t["expected_cz_norm"] == "block"]

print("\nA) MÍRNÉ VÝRAZY — posunula je norma dolů?")
print(f"\n{'ID':<24} {'A':>8} {'B':>8} {'posun':>9} {'A akce → B akce'}")
print("-" * 78)
shifts_mild = []
for t in mild:
    r = results[t["id"]]
    s = r["B"]["vulgar_avg"] - r["A"]["vulgar_avg"]
    shifts_mild.append(s)
    changed = " ✓ ZMĚNA" if r["A"]["moderation"] != r["B"]["moderation"] else ""
    print(f"{t['id']:<24} {r['A']['vulgar_avg']:>8.3f} {r['B']['vulgar_avg']:>8.3f} "
          f"{s:>+9.3f} {r['A']['moderation']} → {r['B']['moderation']}{changed}")
print(f"\n  Průměrný posun u mírných: {statistics.mean(shifts_mild):+.3f}")

print("\nB) HRANIČNÍ PŘÍPADY — UDRŽELA norma hranici? (nesmí je omluvit)")
print(f"\n{'ID':<24} {'A':>8} {'B':>8} {'posun':>9} {'A akce → B akce':<34} {'OK?'}")
print("-" * 92)
held = 0
for t in hard:
    r = results[t["id"]]
    s = r["B"]["vulgar_avg"] - r["A"]["vulgar_avg"]
    still_blocked = r["B"]["moderation"] == "block"
    held += still_blocked
    status = "✓ drží" if still_blocked else "✗ PROPUSTILA"
    print(f"{t['id']:<24} {r['A']['vulgar_avg']:>8.3f} {r['B']['vulgar_avg']:>8.3f} "
          f"{s:>+9.3f} {r['A']['moderation'] + ' → ' + r['B']['moderation']:<34} {status}")
print(f"\n  Hranice udržena: {held}/{len(hard)}")

print("\nC) ZMĚNY ROZHODNUTÍ O MODERACI")
changes = [(t["id"], results[t["id"]]["A"]["moderation"], results[t["id"]]["B"]["moderation"])
           for t in TEXTS
           if results[t["id"]]["A"]["moderation"] != results[t["id"]]["B"]["moderation"]]
print(f"\n  Změnilo se {len(changes)}/{len(TEXTS)} rozhodnutí:")
for cid, a_m, b_m in changes:
    print(f"    {cid:<24} {a_m} → {b_m}")

print(f"""
ZÁVĚR:
  Mírné výrazy: {len(mild)} textů, průměrný posun {statistics.mean(shifts_mild):+.3f}
  Hraniční:     {len(hard)} textů, hranice udržena {held}/{len(hard)}

  Norma je použitelná jen tehdy, když platí obojí: posune to, co posunout má,
  a NEposune to, co posunout nesmí. Druhá podmínka je důležitější.
""")

save_result("test_13_vulgarita_v2", {
    "texts": TEXTS, "variant_A": VARIANT_A, "variant_B": VARIANT_B,
    "results": results,
    "summary": {"mild_mean_shift": round(statistics.mean(shifts_mild), 3),
                "boundary_held": held, "boundary_total": len(hard),
                "decision_changes": len(changes)},
})
print("Uloženo: results/test_13_vulgarita_v2.json")
