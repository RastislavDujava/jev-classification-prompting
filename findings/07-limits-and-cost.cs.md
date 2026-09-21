# Limity `criteria` — co říká dokumentace a co ukázal test

*Ověřeno 21. 9. 2026 · model `jev-1.13.0` · dokumentace + vlastní měření proti živému API*

---

## Krátká odpověď

**Samostatný limit na délku `criteria` v dokumentaci neexistuje a v praxi se neprojevuje.**
`criteria` je součástí tokenového rozpočtu otázky a naráží až na obecný limit kontextu.

Limity, které pro `criteria` skutečně platí, jsou **na počty, ne na délku**:

| Limit | Hodnota | Zdroj | Ověřeno |
|---|---|---|---|
| Délka `criteria` samotné | **žádný samostatný** | — | ✅ 191 750 znaků prošlo |
| `state` + nejdelší otázka | **32k tokenů** | dokumentace | ✅ 32 796 OK, víc = chyba |
| `state` + všechny otázky | **64k tokenů** | dokumentace | — |
| Počet options u Choice | **255** | dokumentace | ✅ 255 OK, 256 = chyba |
| Počet úrovní u Score | **2–10** | dokumentace | ✅ 10 OK, 11 = chyba |

Prakticky: **do `criteria` se vejde zhruba 190 000 znaků**, tedy asi 75 normostran.
Norma z našeho experimentu má 600 znaků — jsme na **0,3 % limitu**.

---

## Co říká dokumentace

Z [models.md](https://docs.typesafe.ai/models):

> **Context length:** 64k tokens per request; 32k tokens for `state` plus the longest question
>
> *„Jev ingests the `state` once and evaluates every question against it in parallel.
> The 64k budget covers the `state` plus all questions combined; the 32k budget applies
> to the `state` plus the single longest question."*

Dva rozpočty, které se liší účelem:

- **32k** — strop pro jednu otázku (`state` + ta nejdelší z nich). Tenhle limit tě omezuje při psaní dlouhé normy.
- **64k** — strop pro celé volání (`state` + všechny otázky dohromady). Tenhle limit tě omezuje při velkém počtu otázek.

O `criteria` jako takové **se nikde nepíše žádné samostatné omezení délky**.
Prohledal jsem [api.md](https://docs.typesafe.ai/api), [models.md](https://docs.typesafe.ai/models),
[primitives.md](https://docs.typesafe.ai/primitives) a stránky všech tří primitiv — limity na délku
textu v `criteria` tam nejsou.

### Limity, které dokumentace uvádí

[primitives_choice.md:355](https://docs.typesafe.ai/primitives/choice):
> *„A Choice question accepts up to 255 options, and adding options costs a few tokens each,
> so give the model the full list of teams, categories, or products rather than a shortlist."*

[primitives_score.md:272](https://docs.typesafe.ai/primitives/score):
> *„`criteria`: An ordered array of level descriptions… Needs at least two levels and takes up to 10."*

[primitives.md:444](https://docs.typesafe.ai/primitives):
> *„The number of questions in one request is limited only by the request's token budget,
> which the state and the questions share. The budget is around 32,000 tokens,
> roughly 150,000 characters of English text."*

---

## Vlastní měření

### 1. Kde je strop délky `criteria`

Do větve `false` jsem opakovaně vkládal stejnou větu a zvětšoval ji, `state` zůstal krátký:

| Délka `criteria` | Stav | `input_tokens` |
|---|---|---|
| 94 400 znaků | ✅ OK | 16 296 |
| 141 600 znaků | ✅ OK | 24 296 |
| 177 000 znaků | ✅ OK | 30 296 |
| **191 750 znaků** | ✅ **OK** | **32 796** ← poslední průchozí |
| 212 400 znaků | ❌ HTTP 400 | — |

Chyba při překročení:
```json
{"detail": {"error_type": "max_tokens_exceeded"}}
```

**Hranice sedí na dokumentovaných 32k tokenech** pro `state` + nejdelší otázku.
Žádný dřívější, skrytý limit specifický pro `criteria` neexistuje.

### 2. Rozpočet je sdílený se `state`

Ověřeno s dlouhým `state` (~75 000 znaků):

| `state` | `criteria` | Stav | `input_tokens` |
|---|---|---|---|
| 75 000 znaků | 118 znaků | ✅ OK | 18 315 |
| 75 000 znaků | 472 000 znaků | ❌ HTTP 400 | — |

**Není to tedy „32k pro state a zvlášť 32k pro criteria".** Sdílejí jeden rozpočet.
Čím delší text hodnotíš, tím míň místa zbývá na definici — a naopak.

### 3. Počty u Choice a Score

| Test | Výsledek |
|---|---|
| Choice, 255 options | ✅ OK (5 431 tokenů) |
| Choice, 256 options | ❌ `Too many choices. Must have at most 255 choices.` |
| Score, 10 úrovní | ✅ OK |
| Score, 11 úrovní | ❌ `Too many score levels. Must have at most 10 levels.` |

Dokumentované počty platí přesně. Chybové hlášky jsou konkrétní a srozumitelné.

---

## Co z toho plyne pro psaní norem

**Délka není omezení, kterého by ses musel bát.** Norma z našeho experimentu
(600 znaků) využívá 0,3 % dostupného místa. I velmi podrobná definice s desítkami
příkladů se pohodlně vejde.

**Skutečné omezení je jinde — v účinnosti.** Ablační studie v [REPORT_kriteria.md](01-criteria-ablation.cs.md)
ukázala, že delší text automaticky neznamená lepší výsledek:

| Varianta | Posun |
|---|---|
| Jen výčet slov (kratší) | −0,82 |
| Výčet + vysvětlení kontextu (delší) | −0,85 |

Přidání celé vysvětlující věty posunulo o 0,03, tedy na hranici šumu.
**Limit tě nezastaví dřív, než tě zastaví klesající užitek.**

**Na co si dát pozor:**

1. **Dlouhý `state` ukrajuje z místa na otázku.** Hodnotíš-li dlouhé dokumenty,
   zbývá míň na definici. Rozpočet je společný.

2. **Dlouhá `criteria` se platí při každém volání.** Účtuje se vstup ($0,042/M tokenů),
   takže 30 000 tokenů v definici stojí ~0,13 centu za volání. Při milionu volání
   měsíčně je to 1 260 dolarů jen za normu, která se nemění. Vyplatí se ji zkrátit
   na to, co skutečně účinkuje — což ukáže ablace.

3. **Dokumentace varuje před balastem.** [Jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
   uvádí *„large state full of irrelevant detail"* jako jeden z devíti režimů selhání
   a mluví o *context rot*. Týká se to sice `state`, ale nafouknutá `criteria`
   plná nepodstatných vět jsou stejný problém.

4. **Latence roste.** V měření: 94 400 znaků → 1,93 s, zatímco krátká definice → ~1,2 s.

---

## Reprodukce

Testy byly jednorázové sondy, neuložené jako trvalý skript. Postup:

```python
word = "The text contains only mild Czech colloquial expressions... "
for reps in [800, 1200, 1500, 1800]:
    payload = {
        "state": "Ty vole, do prdele.",
        "model": "jev-latest",
        "questions": {"q": {
            "type": "noul",
            "instructions": "Vulgar?",
            "criteria": {"true": "Yes.", "false": word * reps}
        }}
    }
    # POST https://api.typesafe.ai/v1/systemone
```

Poslední průchozí volání vrátilo `input_tokens: 32796`; následující skončilo
`HTTP 400 {"detail": {"error_type": "max_tokens_exceeded"}}`.

---

*Limity se mohou s dalšími verzemi modelu změnit — dokumentace u rate limitů výslovně
upozorňuje, že se „adjust dynamically". Měřeno na `jev-1.13.0` dne 21. 9. 2026.*
