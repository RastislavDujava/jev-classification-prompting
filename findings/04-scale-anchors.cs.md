# Jde ukotvit číselnou škálu Noulu?

### Test kalibrace stupnice pomocí kotev v `criteria`

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 8 příběhů × 4 varianty × 3 běhy = 96 volání*

---

## Otázka

Few-shot příklady v předchozích testech učily model, **kde je hranice**.
Tenhle test zkouší jinou věc: ukotvit **celou stupnici** — říct modelu,
co znamená 0,2, co 0,5, co 0,9 — a ověřit, jestli se těch čísel drží.

Úloha: *„Je tenhle příběh o zvířatech vhodný pro děti 5–7 let?"*
Kvalitativní posouzení, kde neexistuje jedna správná odpověď, ale existuje **pořadí**:
krutý příběh musí dostat míň než laskavý.

---

## Odpověď krátce

**Ne, čísla v kotvách model neposlouchá. Ale popisy v nich fungují velmi dobře.**

A na úlohy tohoto typu je **Score výrazně lepší nástroj než ukotvený Noul.**

---

## Čtyři varianty

| | Co obsahuje |
|---|---|
| **A holý Noul** | jen otázka, žádná definice |
| **B popisný** | `criteria` popisují, co je vhodné a co ne — **bez čísel** |
| **C s kotvami** | `instructions` přiřazují **konkrétní čísla** konkrétním situacím |
| **D Score** | nativní stupnice se šesti popsanými úrovněmi |

Znění kotev ve variantě C:

```
Use the full scale. Calibrate your answer against these anchor points:
0.95-1.00 — Entirely gentle. Nothing bad happens at all.
0.75-0.90 — Mild worry that resolves. Briefly lost, sad or scared, then comforted.
0.55-0.70 — Real peril or injury, no detail, fully resolved by the end.
0.35-0.50 — Frightening or sad event off-screen, or unresolved threat.
0.15-0.30 — Death or permanent loss on-screen, handled gently.
0.00-0.10 — Graphic violence, blood, suffering shown directly.
```

---

## Naměřené hodnoty

| Příběh | můj odhad | A holý | B popisný | C s kotvami | D Score |
|---|---|---|---|---|---|
| s1 laskavý (myška a knoflík) | 0,95 | 0,930 | 0,967 | 0,980 | **1,000** |
| s2 mírná obava (ztracené káčátko) | 0,80 | 0,940 | 0,960 | 0,980 | **0,800** |
| s3 zranění vyřešené (veverka) | 0,60 | 0,927 | 0,927 | 0,893 | **0,628** |
| s4 predace mimo scénu (liška a slepice) | 0,35 | **0,560** | 0,187 | 0,193 | **0,337** |
| s5 smrt na scéně (starý pes Rex) | 0,15 | **0,463** | 0,163 | 0,157 | **0,200** |
| s6 drastický (vlk a srna) | 0,03 | 0,117 | 0,040 | 0,033 | **0,000** |
| s7 strašidelný bez újmy (sova na půdě) | 0,50 | 0,833 | 0,817 | 0,860 | **0,828** |
| s8 složité téma (kůň Blesk) | 0,25 | 0,337 | 0,190 | 0,200 | **0,304** |

### Souhrn

| Varianta | rozpětí | σ | pořadí ρ | odchylka od odhadu | stabilita |
|---|---|---|---|---|---|
| A holý Noul | 0,823 | 0,315 | 0,952 | **0,190** | 0,030 |
| B popisný | 0,927 | 0,418 | **0,976** | 0,133 | 0,010 |
| C s kotvami | 0,947 | 0,423 | 0,952 | 0,135 | 0,020 |
| **D Score** | **1,000** | 0,352 | 0,929 | **0,069** | 0,010 |

---

## Co z toho plyne

### 1. Kotvicí čísla model ignoruje — doloženo

Nejdřív se zdálo, že C funguje (odchylka klesla z 0,190 na 0,135). Ale to zlepšení
přinesly **popisy**, ne čísla — varianta B, která žádná čísla nemá, dopadla stejně (0,133).

Ověřil jsem to přímo: vzal jsem tytéž popisy a **přepsal jen čísla** — horní konec
z „0,95–1,00" na „0,70–0,80":

| Příběh | původní kotvy | posunuté kotvy | rozdíl |
|---|---|---|---|
| s1 laskavý | 0,980 | 0,980 | **±0,000** |
| s2 mírná obava | 0,977 | 0,963 | −0,013 (šum) |
| s3 zranění | 0,890 | 0,890 | **±0,000** |

**Model nezareagoval vůbec.** Kdyby čísla četl jako pokyn, s1 by kleslo z 0,98 na ~0,75.
Zůstalo na 0,98.

Dává to smysl: Noul **není skóre kvality**. Je to pravděpodobnost, že odpověď na
otázku zní ano. Model neodpovídá na *„jak moc je to vhodné"*, ale na *„je to vhodné?"* —
a 0,98 znamená „skoro jistě ano", ne „vhodnost 98 %".

To je zároveň důvod, proč čísla v `criteria` nemohou fungovat: žádají po modelu,
aby výstup použil jako stupnici, kterou tento typ otázky nemá.

### 2. Popisy v kotvách fungují výborně

Přechod z A na B srazil odchylku z 0,190 na 0,133 a zvedl rozpětí z 0,82 na 0,93.

Nejlépe je to vidět na dvou příbězích:

| Příběh | A holý | B popisný | posun |
|---|---|---|---|
| s4 predace mimo scénu | 0,560 | **0,187** | **−0,37** |
| s5 smrt na scéně | 0,463 | **0,163** | **−0,30** |

Bez definice model označil příběh, kde **liška sežere slepici**, za vhodný pro pětileté
(0,56, nad prahem). A příběh, kde **umírá pes**, dal na 0,46 — těsně pod prahem, tedy
prakticky „nevím".

Po doplnění popisu spadly oba správně dolů. **To je stejný jev jako v ostatních
doménách: model má vlastní výchozí normu, a ta nemusí být tvoje.**

### 3. Na tenhle typ úlohy patří Score, ne Noul

Score vyhrálo v tom, na čem záleží:

- **Odchylka 0,069** proti 0,133–0,190 u Noulu — dvakrát blíž mé představě
- **Rozpětí 1,000** — využilo celou stupnici od 0,000 do 1,000
- **Stabilita 0,010** — nejspolehlivější

Je to logické: Score **má stupnici nativně**. Vrací vážený průměr přes popsané úrovně,
takže 0,628 doopravdy znamená „mezi úrovní 3 a 4". U Noulu je 0,628 pravděpodobnost,
což je jiná veličina.

Jediné, v čem Score prohrálo, je pořadí (ρ = 0,929 proti 0,976 u B). Způsobil to
jediný příběh — s7 (strašidelný bez újmy), kde všechny varianty daly kolem 0,83,
zatímco já čekal 0,50. Tam se spíš mýlil můj odhad než model: v příběhu se nakonec
nic zlého nestane, jen zpočátku straší.

### 4. Pořadí drží model i bez pomoci

Spearmanova korelace neklesla pod 0,93 v žádné variantě, včetně holého Noulu.
**Model rozumí, že krutý příběh je méně vhodný než laskavý, i bez jediné instrukce.**

Co se definicí mění, není pořadí, ale **kde leží hranice** a **jak se stupnice roztáhne**.

---

## Praktický závěr

| Chceš… | Použij |
|---|---|
| Rozhodnutí ano/ne s prahem | **Noul** + popisná `criteria` |
| Míru na stupnici, se kterou dál počítáš | **Score** s popsanými úrovněmi |
| Přiřadit konkrétní čísla konkrétním situacím | **nejde** — čísla model ignoruje |

**Tři pravidla, která z toho plynou:**

1. **Nepiš do `criteria` konkrétní čísla.** Neúčinkují. Napiš popisy situací.
2. **Potřebuješ-li stupnici, sáhni po Score.** Ukotvený Noul je oklika, která stojí
   tokeny a nefunguje pořádně.
3. **Popisy krajů stupnice se vyplatí i u Score.** Úrovně musí popisovat konkrétní
   situace, ne „nízká/střední/vysoká".

Toto zjištění sedí k tomu, co přiznává i dokumentace modelu: *„nepoužívejte `score`
k rekonstrukci přesného čísla interpolací mezi úrovněmi — model je v numerické
kalibraci slabý."* Náš test ukazuje tutéž slabinu z druhé strany: číslo v zadání
model nepřečte jako cíl.

---

## Poznámka k metodě

Sloupec „můj odhad" **není pravda**, jen referenční bod. U s7 se ukázalo, že chybný
byl spíš odhad než model. Pro publikovatelný výsledek by bylo potřeba víc hodnotitelů
a shoda mezi nimi — osm příběhů a jeden odhadce na tvrzení o přesnosti nestačí.

Co je doložené robustně, je **necitlivost na kotvicí čísla** — to je přímé měření
se dvěma variantami lišícími se jen čísly, a rozdíl vyšel nulový.

---

📄 Data: [results/test_7_kotvy_skaly.json](../results/test_7_kotvy_skaly.json) ·
Skript: [test_7_kotvy_skaly.py](../experiments/07_scale_anchors.py) ·
Příběhy: [inputs/stories.json](../data/inputs/stories.json)
