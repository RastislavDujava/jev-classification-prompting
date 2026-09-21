# Volba typu otázky mění rozhodnutí

### Noul vs. Score — a proč na tom záleží víc než na formulaci

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 5 příběhů × 4 stupnice × 5 běhů = 125 volání · vše anglicky*

---

> ⚠️ **Oprava metodiky (21. 9. 2026).** První verze tohoto dokumentu odečítala hodnotu
> Noulu od normalizovaného Score a mluvila o „rozdílu 0,49". **To bylo chybně** — Noul je
> pravděpodobnost, že odpověď zní ano; Score je poloha na stupnici. Různé veličiny,
> různé jednotky, nelze je odečítat. Tabulka níže je opravená: uvádí, k jakému
> **provoznímu rozhodnutí** každý nástroj vede, ne rozdíl čísel.
>
> Navazující správně postavený pokus: *(druhá vlna, zatím nepublikováno)*.

## Nález v jedné tabulce

Stejný text. Stejná úloha. Jiný **typ** otázky — a jiné provozní rozhodnutí.

| Příběh | Noul „je to vhodné?" | rozhodnutí | Score „jak moc?" | rozhodnutí |
|---|---|---|---|---|
| Laskavý (myška a knoflík) | 0,936 | pustit | 1,000 | nejvyšší úroveň |
| Mírná obava (ztracené káčátko) | 0,928 | pustit | 0,801 | vysoko |
| Skutečné zranění (králík Pip) | 0,902 | pustit | 0,681 | střed |
| Ztráta mimo scénu (liška a slepice) | 0,500 | na hraně | 0,346 | nízko |
| **Smrt na scéně (starý pes Rex)** | **0,690** | **pustit** | **0,204** | **druhá nejnižší** |

**Poslední řádek je ten podstatný.** Příběh, kde na scéně umírá pes a chlapec ho pohřbívá
pod jabloní, dostal od Noulu **0,690** — nad prahem 0,5, tedy „ano, je vhodný".

Tentýž příběh zařadilo Score na **druhou nejnižší úroveň** — „smrt na scéně, dítě
potřebuje dospělého, aby to s ním probral".

**Dva nástroje, opačné provozní rozhodnutí.** Kdo postaví moderaci na Noulu s prahem 0,5,
pustí tenhle příběh pětiletým dětem bez varování.

---

## Proč to tak je

Není to chyba modelu. Jsou to dvě různé veličiny:

| | Noul | Score |
|---|---|---|
| Otázka | *Je to vhodné?* | *Jak moc je to vhodné?* |
| Vrací | **pravděpodobnost, že odpověď zní ano** | **polohu na stupnici** |
| `0,69` znamená | „na 69 % je odpověď ano" | — |
| `0,20` znamená | — | „leží to nízko na stupnici" |

Noul u příběhu o Rexovi odpovídá: *„je to dětská knížka? asi ano, spíš ano"*.
A má svým způsobem pravdu — je to laskavě napsaný příběh o zvířátku.

Score odpovídá na jinou otázku: *„kam na stupnici od drastického po idylický to patří?"*
A tam smrt na scéně patří nízko, ať je napsaná jakkoli citlivě.

**Binární otázka nedokáže zachytit míru.** Když se ptáš ano/ne, dostaneš ano/ne —
i když skutečná odpověď zní „ano, ale".

---

## Co dělá jemnost stupnice

| Stupnice | rozpětí | σ | confidence | pořadí sedí? |
|---|---|---|---|---|
| 3 úrovně | 0,603 | 0,296 | 0,800 | **✗ NE** |
| **4 úrovně** | **0,914** | **0,389** | 0,888 | ✓ |
| 6 úrovní | 0,796 | 0,327 | 0,902 | ✓ |
| 10 úrovní | 0,764 | 0,333 | **0,928** | ✓ |

### Tři úrovně jsou málo

Jediná stupnice, která **popletla pořadí příběhů**. Umístila „ztrátu mimo scénu"
níž než „smrt na scéně" — tedy přesně obráceně, než dává smysl.

Důvod je vidět v číslech: `death_onscreen` dostal 0,421 a `loss_offscreen` 0,397.
Obojí spadlo do prostřední úrovně, která byla tak široká, že v ní model nedokázal
rozlišit. Zároveň má tahle stupnice **nejnižší confidence (0,800)** — model sám
signalizoval, že si není jistý.

### Čtyři stačí, deset nepřidá

Od čtyř úrovní nahoru je pořadí stabilní a rozpětí velké. Deset úrovní má
**nejvyšší confidence (0,928)**, ale rozpětí se nezlepšilo (0,764 proti 0,914 u čtyř).

Dokumentace povoluje 2–10 úrovní a radí: *„použij tolik úrovní, kolik dokážeš
odlišně popsat"*. Naše měření to potvrzuje — **omezením není model, ale to, jestli
umíš deset úrovní smysluplně rozepsat.**

---

## Praktický dopad

### Tentýž obsah, tři různá rozhodnutí

Příběh o Rexovi, podle zvoleného nástroje:

```
Noul, práh 0,5        → 0,690  → PUBLIKOVAT
Score 3 úrovně        → 0,421  → hraniční
Score 6 úrovní        → 0,204  → OZNAČIT, vyžaduje dospělého
```

**Volba typu otázky rozhodla víc než jakákoli formulace kritérií.**
V předchozích testech jsme posouvali čísla o 0,3–0,8 přepisem `criteria`.
Tady stačilo změnit `"type"` a rozhodnutí se otočilo.

### Kdy co použít

| Potřebuju | Typ | Proč |
|---|---|---|
| Rozhodnutí s prahem (spam / ne spam) | **Noul** | binární úloha, binární nástroj |
| Prioritu, závažnost, kvalitu, vhodnost | **Score** | má pořadí, tedy potřebuje stupnici |
| Zařadit do kategorie bez pořadí | **Choice** | kategorie se vylučují |

**Varovný příznak:** když do otázky píšeš slovo *„jak moc"*, *„nakolik"*, *„do jaké míry"*
— patří to na Score, i kdyby se to dalo zformulovat jako ano/ne.

### Pravidla pro Score

1. **Minimálně čtyři úrovně.** Tři nespolehlivě rozlišují a mají nejnižší confidence.
2. **Úrovně popisují konkrétní situace**, ne stupně intenzity.
   - ❌ „nízká / střední / vysoká"
   - ✅ „skutečné zranění s trvalým následkem, bez drastických detailů, vyřešené do konce"
3. **Pořadí od nejhoršího k nejlepšímu** (nebo naopak, ale důsledně).
4. **Nepiš do popisů čísla.** Model je ignoruje — doloženo v
   [VYSLEDEK_kotvy_skaly.md](04-scale-anchors.cs.md). Stupnice je dána strukturou, ne textem.
5. **Sleduj confidence.** Nízká znamená, že sousední úrovně jdou od sebe těžko odlišit —
   tedy že je máš popsané špatně.

---

## Souvislost s ostatními nálezy

Tohle doplňuje obrázek ze zbytku práce:

| Co se mění | Dopad | Kde doloženo |
|---|---|---|
| **Typ otázky** (Noul → Score) | **obrací provozní rozhodnutí** | tento dokument |
| Obsah `criteria` (definice, výjimky) | 0,3–0,85 | [REPORT_kriteria.md](01-criteria-ablation.cs.md) |
| Few-shot příklady v zadání | 0,2–0,55 | [SROVNANI_bez_a_s_priklady.md](08-length-vs-content.cs.md) |
| Čísla v popisech úrovní | **0,00** | [VYSLEDEK_kotvy_skaly.md](04-scale-anchors.cs.md) |
| Formulace `instructions` samotná | 0,04 | [VYSLEDEK_tool_routing.md](02-model-bias.cs.md) |

**Pořadí podle síly:** typ otázky > obsah criteria > příklady >> formulace instructions > čísla.

(Řádky 2–5 jsou posuny *uvnitř téže veličiny*, tedy porovnatelné mezi sebou.
První řádek porovnatelný není — proto je popsaný slovy, ne číslem.)

To je pro praxi obrácené pořadí, než jak se k tomu obvykle přistupuje. Nejvíc času
se věnuje formulaci otázky — a ta je předposlední. Nejdůležitější rozhodnutí,
**jaký typ otázky vůbec položit**, padne většinou v první minutě bez rozmyslu.

---

## Omezení

- **Pět příběhů** je málo na tvrzení o přesnosti. Doložený je *rozdíl mezi typy*,
  ne absolutní správnost kteréhokoli z nich.
- **Sloupec „očekáváme"** je můj odhad, ne ověřená pravda. Co je doloženo bez něj:
  Noul a Score se u téhož textu rozcházejí až o 0,49.
- **Jedna doména** (vhodnost pro děti). Jestli platí i jinde, je otevřená otázka —
  ale mechanismus (pravděpodobnost vs. poloha na stupnici) je obecný.

---

📄 Data: [results/test_9_jemnost_skaly.json](../results/test_9_jemnost_skaly.json) ·
Skript: [test_9_jemnost_skaly.py](../experiments/08_noul_vs_score.py)
