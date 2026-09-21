# Čeština vs. angličtina

### Dokumentace varuje. Měření to nepotvrdilo.

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 15 dvojjazyčných párů × 5 běhů*

---

## Co dokumentace slibuje

> *„English is the primary training language and where accuracy is currently best.
> Other languages, including CJK scripts, are handled but not equally well; test on
> your own content before relying on Jev for a non-English workload."*
> — [models.md](https://docs.typesafe.ai/models)

Rozumné varování. Tenhle test ho bere vážně a měří, o kolik je čeština horší.

---

## Výsledek

| | přesnost | průměrný rozdíl |
|---|---|---|
| **Anglický text** | **15/15 (100 %)** | — |
| **Český text** | **15/15 (100 %)** | 0,036 |
| **Shoda rozhodnutí** | **15/15 (100 %)** | — |

**Na téhle úloze nebyl rozdíl měřitelný.** Přesnost shodná, rozhodnutí shodná,
průměrný rozdíl hodnot 0,036 — pod prahem šumu, který jsme naměřili dřív (0,05).

---

## Metoda

15 dvojic, kde **každá položka existuje v češtině i angličtině se shodným obsahem**.
Úloha: *„vyjadřuje autor nespokojenost s produktem nebo službou?"*

Zadání otázky bylo **vždy anglicky** — měnil se jen jazyk hodnoceného textu.
Díky tomu měříme jazyk textu, ne jazyk zadání.

Sada záměrně obsahuje případy, kde se dá čekat problém:

| Typ | Proč je těžký |
|---|---|
| Sarkasmus | Slova říkají opak toho, co text znamená |
| Negace | Test, jestli model nereaguje jen na klíčová slova |
| Podmiňovací způsob | Stížnost, která se nekoná |
| Třetí osoba | Stěžuje si někdo jiný |
| Bez emocionálních slov | Stížnost složená z holých faktů |
| **České idiomy** | *„byl jsem úplně vedle"*, *„ani ťuk"* — bez přímého ekvivalentu |
| **Zlehčení** | *„nebylo to úplně ono"* — typicky české |

---

## Hodnoty položku po položce

| Položka | čekáme | EN | CS | rozdíl |
|---|---|---|---|---|
| Jasná stížnost | ano | 0,990 | 0,990 | 0,000 |
| Jasná pochvala | ne | 0,020 | 0,020 | 0,000 |
| Neutrální konstatování | ne | 0,040 | 0,040 | 0,000 |
| Zdvořilý vztek | ano | 0,960 | 0,960 | 0,000 |
| Sarkasmus | ano | 0,990 | 0,980 | −0,010 |
| Smíšené hodnocení | ano | 0,960 | 0,960 | 0,000 |
| **Negace** | ne | **0,022** | **0,464** | **+0,442** |
| Podmiňovací způsob | ne | 0,040 | 0,040 | 0,000 |
| Třetí osoba | ne | 0,124 | 0,136 | +0,012 |
| Bez emocionálních slov | ano | 0,980 | 0,974 | −0,006 |
| **Český idiom** | ano | 0,960 | 0,956 | −0,004 |
| **Zlehčení** | ano | 0,950 | 0,950 | 0,000 |
| Formální obchodní | ano | 0,980 | 0,980 | 0,000 |
| Nadšená neformální | ne | 0,092 | 0,022 | −0,070 |
| Dotaz, ne stížnost | ne | 0,030 | 0,030 | 0,000 |

**Osm z patnácti položek má rozdíl přesně 0,000.** Model u nich dal na oba jazyky
identické číslo.

---

## Jediná výjimka: negace

> CS: *„Zásilka nedorazila pozdě a nic nechybělo. Všechno proběhlo bez problémů."*
> EN: *„The parcel did not arrive late and nothing was missing. Everything went without a problem."*

| | hodnota |
|---|---|
| Anglicky | **0,022** |
| Česky | **0,464** |
| Rozdíl | **+0,442** |

**Obojí je formálně správně** (pod prahem 0,5, tedy „nestěžuje si"), ale česká verze
skončila **těsně u hranice**. Anglická byla jednoznačná.

Nabízí se vysvětlení v **dvojité negaci**, kterou čeština vyžaduje: *„a nic nechybělo"*
obsahuje zápor u slovesa i u zájmena, zatímco angličtina má *„nothing was missing"*
se záporem jediným. Model zřejmě sčítá negativní signály.

**Je to ale hypotéza z jednoho příkladu**, ne prokázaný mechanismus. Na tvrzení by
bylo potřeba víc negací různého typu.

**Praktický důsledek:** 0,464 by při prahu 0,5 prošlo, ale s rezervou 0,036. Kdo staví
českou moderaci, měl by u negativních formulací počítat s menší rezervou než u angličtiny.

---

## Část 3: pomůže české zadání na český text?

Zkusili jsme přeložit i `instructions` a `criteria` do češtiny:

| | přesnost |
|---|---|
| Český text + anglické zadání | 15/15 |
| Český text + **české zadání** | 15/15 |

**Beze změny.** Většina hodnot se pohnula o méně než 0,01.

Jedinou položkou, kde se to projevilo, byla opět negace: 0,464 → **0,342**,
tedy **o 0,12 dál od prahu**. České zadání tam pomohlo, ale je to jediný případ.

**Závěr:** psát zadání česky není potřeba. Jestli to u negací pomáhá systematicky,
by chtělo vlastní měření.

---

## Co z toho plyne

**1. Varování v dokumentaci se na této úloze nepotvrdilo.** To neznamená, že je
špatné — znamená to, že klasifikace sentimentu a stížností je úloha, kde čeština
modelu nedělá problém.

**2. Práh vyladěný na angličtině se přenese.** Průměrný rozdíl 0,036 je pod šumem.
Pro praxi je to důležitější než samotná přesnost: můžete ladit na anglických datech
a nasadit na česká.

**3. Idiomy a zlehčení zvládl.** *„Byl jsem úplně vedle"* (0,956) a *„nebylo to úplně
ono"* (0,950) — obojí správně jako stížnost, prakticky shodně s angličtinou.

**4. Zadání překládat netřeba.** Ušetří to práci i tokeny.

**5. Negace si zaslouží pozornost.** Jediná položka s rozdílem nad šumem.
Kdo dělá českou moderaci, ať si otestuje negativní formulace zvlášť.

---

## Omezení

- **Jedna úloha.** Sentiment/stížnosti. Jiné domény mohou dopadnout jinak —
  zvlášť tam, kde záleží na odborné terminologii nebo právním jazyce.
- **15 párů.** Ukazuje, že velký rozdíl neexistuje. Malý by tenhle vzorek nezachytil.
- **Překlady jsem dělal já.** Snažil jsem se o významovou shodu, ale u idiomů
  je „shodný obsah" vždy trochu věc výkladu.
- **Jeden hodnotitel** referenčních odpovědí.
- **Negace = jeden příklad.** Vysvětlení dvojitým záporem je hypotéza.

---

📄 Data: [results/test_12_cestina.json](../results/test_12_cestina.json) ·
Skript: [test_12_cestina.py](../experiments/09_czech_vs_english.py) ·
Texty: [inputs/bilingual.json](../data/inputs/bilingual.json)
