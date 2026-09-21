"""
TEST 14 — Ostrý kontrast: tentýž příběh, opačné rozhodnutí

Cíl: najít případ, kde
  - bez profilu projde OBOJÍ s vysokým skóre
  - s profilem A projde jeden a zakáže se druhý
  - s profilem B je to obráceně

Zvolená situace: dvě rodiny, obě s dítětem 5-7 let.

  Rodina 1 -- dcera má silný strach z pavouků a hmyzu. Po pohádce s pavoukem
              nespí. Jinak snese i napínavý příběh.
  Rodina 2 -- syn se nebojí zvířat vůbec, má je rád. Rodiče ale nechtějí
              příběhy, kde je někdo vyloučený z kolektivu nebo se mu ostatní
              posmívají -- ve škole to řeší.

Příběhy jsou obě naprosto běžné, neškodné dětské pohádky. Žádné násilí,
žádná smrt. Přesně proto, že obecný klasifikátor na nich nic nenajde.

Spusť: ▶ (bez argumentů)
"""

import statistics

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from jev_client import ask, save_result

RUNS = 5

# ---------------------------------------------------------------------------
# PŘÍBĚHY — obě zcela neškodné, ale každý trefí jinou rodinnou citlivost
# ---------------------------------------------------------------------------
STORIES = {
    "spider": {
        "label": "Pavoučice Anička (pavouk jako hlavní hrdina)",
        "text": (
            "Anička was a small house spider who lived in the corner of the garden shed. "
            "Every morning she spun a new web between the flowerpots, and every morning "
            "the dew made it shine like glass.\n\n"
            "One day the wind tore her web apart. Anička sat on the windowsill with her "
            "eight legs tucked under her and did not know what to do. A beetle walking "
            "past stopped and said that a torn web only means it is time to build a "
            "better one, and that he had watched her build the last one and it was the "
            "finest in the whole shed.\n\n"
            "So Anička started again. She worked all afternoon, and when she finished, "
            "the new web stretched all the way from the watering can to the old bicycle. "
            "The beetle came back to look at it and they sat together until it got dark."
        ),
    },
    "excluded": {
        "label": "Zajíček, kterého nevzali do hry (vyloučení z kolektivu)",
        "text": (
            "Ondra the rabbit came to the meadow where the other young rabbits were "
            "playing a chasing game. He asked if he could join. They looked at each "
            "other and said the teams were already even, and went back to running.\n\n"
            "Ondra sat down by the fence and watched. When they laughed at something he "
            "could not hear, he felt his ears go hot. He stayed there for a long time, "
            "pulling at the grass and pretending he did not mind.\n\n"
            "After a while the smallest rabbit came over and sat down next to him without "
            "saying anything. Then she asked if he wanted to look for the blackberries "
            "she had found near the stream. They went together, and the next day both "
            "teams wanted Ondra on their side."
        ),
    },
}

QUESTION = "How suitable is this children's story for a child aged 5 to 7 in this family?"

# ---------------------------------------------------------------------------
# PROFIL 0 — žádný. Obecná stupnice, jak by ji napsal kdokoli.
# ---------------------------------------------------------------------------
GENERIC_LEVELS = [
    "Not appropriate for a young child: violence, death, or frightening content",
    "Questionable: some upsetting or intense moments",
    "Mostly fine: a gentle story with a small problem",
    "Fully appropriate: calm, kind, and reassuring throughout",
]

# ---------------------------------------------------------------------------
# PROFIL 1 — dcera se bojí pavouků a hmyzu
# ---------------------------------------------------------------------------
FAMILY_1_LEVELS = [
    "A spider, insect or similar creature appears as a character, is described in "
    "physical detail, or is shown close up. Our daughter has a strong fear of these "
    "animals and will not sleep after a story like this, however kindly it is written.",
    "Spiders or insects are mentioned in passing, or an animal is described in a way "
    "that could bring them to mind",
    "No spiders or insects anywhere, but the story has frightening or distressing "
    "moments of another kind",
    "No spiders or insects, and any problem in the story is small and quickly resolved",
    "No spiders or insects at all, and the story is warm and calm throughout. "
    "Sad or difficult moments are fine as long as this condition holds.",
]

# ---------------------------------------------------------------------------
# PROFIL 2 — syn řeší vyloučení z kolektivu ve škole
# ---------------------------------------------------------------------------
FAMILY_2_LEVELS = [
    "A character is excluded from a group, left out of a game, laughed at, or made to "
    "feel unwanted by others. Our son is going through this at school and a story like "
    "this upsets him badly, even when it ends well.",
    "A character is alone or lonely for part of the story, without other characters "
    "causing it",
    "No exclusion or social rejection, but the story has frightening or distressing "
    "moments of another kind",
    "No exclusion of any kind, and any problem in the story is small and quickly resolved",
    "No exclusion at all, and the story is warm and calm throughout. Animals of any "
    "kind, including insects and spiders, are completely fine for him.",
]

PROFILES = {
    "0 BEZ PROFILU": GENERIC_LEVELS,
    "1 RODINA A (fobie z pavouků)": FAMILY_1_LEVELS,
    "2 RODINA B (řeší vyloučení)": FAMILY_2_LEVELS,
}

# Brána z předchozího testu — je to vůbec dětský příběh?
GATE = {
    "type": "noul",
    "instructions": "Is this text a children's story: a short narrative written for a child audience, with characters and events a young reader can follow?",
    "criteria": {
        "true": "A narrative written for children: simple language, a clear story with "
                "characters and events, the kind of text that would appear in a picture "
                "book or a bedtime story collection.",
        "false": "Not a children's story: business writing, news, technical text, or a "
                 "narrative written for adults.",
    },
}

ROUTING = [
    (0.80, "PUSTIT"),
    (0.55, "PUSTIT s poznámkou"),
    (0.30, "ZEPTAT SE RODIČE"),
    (0.00, "NEPOUŠTĚT"),
]


def route(n):
    for t, label in ROUTING:
        if n >= t:
            return label
    return ROUTING[-1][1]


def run_gate(text):
    vals = [ask(text, {"q": GATE})["answers"]["q"]["noul"] for _ in range(RUNS)]
    m = statistics.mean(vals)
    return {"avg": round(m, 3), "passes": m > 0.5}


def run_score(text, levels):
    q = {"type": "score", "instructions": QUESTION, "criteria": levels}
    raw, conf, probs = [], [], None
    for _ in range(RUNS):
        a = ask(text, {"q": q})["answers"]["q"]
        raw.append(a["score"])
        conf.append(a["confidence"])
        probs = a["probabilities"]
    top = len(levels) - 1
    m = statistics.mean(raw)
    return {"raw": round(m, 2), "top": top, "normalized": round(m / top, 3),
            "level": round(m), "confidence": round(statistics.mean(conf), 3),
            "spread": round(max(raw) - min(raw), 2), "probs": probs}


print("=" * 100)
print(f"TEST 14 — OSTRÝ KONTRAST: tentýž příběh, opačné rozhodnutí  ({RUNS} běhů)")
print("=" * 100)

results = {}

# --- KROK 1: brána --------------------------------------------------------
print("\n" + "=" * 100)
print("KROK 1 — BRÁNA: je to vůbec dětský příběh?")
print("=" * 100)
print(f"\n{'PŘÍBĚH':<48} {'noul':>8} {'projde?':>10}")
print("-" * 70)
for sid, s in STORIES.items():
    g = run_gate(s["text"])
    results[sid] = {"label": s["label"], "gate": g, "scores": {}}
    print(f"{s['label'][:46]:<48} {g['avg']:>8.3f} {'✓ ANO' if g['passes'] else '✗ NE':>10}")

# --- KROK 2: stupnice -----------------------------------------------------
print("\n" + "=" * 100)
print("KROK 2 — STUPNICE: jak moc vhodný PRO TUHLE RODINU?")
print("=" * 100)
head = f"\n{'PŘÍBĚH':<34}"
for p in PROFILES:
    head += f" {p:>30}"
print(head)
print("-" * len(head))

for sid, s in STORIES.items():
    row = f"{s['label'][:32]:<34}"
    for pname, levels in PROFILES.items():
        r = run_score(s["text"], levels)
        results[sid]["scores"][pname] = r
        row += f" {r['normalized']:>18.3f} ({r['level']}/{r['top']})"
    print(row)

# --- KROK 3: rozhodnutí ---------------------------------------------------
print("\n" + "=" * 100)
print("KROK 3 — ROZHODNUTÍ")
print("=" * 100)
print("\n  ≥0,80 pustit │ ≥0,55 pustit s poznámkou │ ≥0,30 zeptat se rodiče │ <0,30 nepouštět\n")
head2 = f"{'PŘÍBĚH':<34}"
for p in PROFILES:
    head2 += f" {p[:28]:<30}"
print(head2)
print("-" * len(head2))

for sid, s in STORIES.items():
    row = f"{s['label'][:32]:<34}"
    for pname in PROFILES:
        row += f" {route(results[sid]['scores'][pname]['normalized']):<30}"
    print(row)

# --- Vyhodnocení ----------------------------------------------------------
print("\n" + "=" * 100)
print("VYHODNOCENÍ")
print("=" * 100)

gen = {sid: results[sid]["scores"]["0 BEZ PROFILU"]["normalized"] for sid in STORIES}
print(f"\nBEZ PROFILU — obojí projde?")
for sid in STORIES:
    print(f"  {results[sid]['label'][:44]:<46} {gen[sid]:.3f}  {route(gen[sid])}")
both_pass = all(v >= 0.55 for v in gen.values())
print(f"  → {'✓ ANO, obojí by prošlo' if both_pass else '✗ ne, liší se už bez profilu'}")

print(f"\nS PROFILY — nastal překlopení?")
for sid in STORIES:
    a = results[sid]["scores"]["1 RODINA A (fobie z pavouků)"]["normalized"]
    b = results[sid]["scores"]["2 RODINA B (řeší vyloučení)"]["normalized"]
    ra, rb = route(a), route(b)
    flip = "✓ OPAČNÉ ROZHODNUTÍ" if ra != rb else "= stejné"
    print(f"  {results[sid]['label'][:40]:<42} A:{a:.3f} {ra:<22} B:{b:.3f} {rb:<22} {flip}")

print(f"""
CO HLEDÁME:
  Bez profilu obojí vysoko → obecný klasifikátor mezi rodinami nerozliší
  S profily křížem → každá rodina dostane svoje rozhodnutí na tomtéž obsahu
""")

save_result("test_14_fobie", {
    "stories": {k: v["text"] for k, v in STORIES.items()},
    "labels": {k: v["label"] for k, v in STORIES.items()},
    "profiles": PROFILES, "gate": GATE, "routing": ROUTING,
    "results": results,
})
print("Uloženo: results/test_14_fobie.json")
