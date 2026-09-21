# Příklady v `instructions`: mění odpověď, a co to stojí

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 70 volání, 10 běhů na variantu, prokládaně*

---

## Otázka a proč je potřeba měřit dvě věci

Teze: **few-shot příklady v `instructions` posunou klasifikaci.** Když modelu ukážeš,
kde je hranice, rozhodne jinak než bez nich.

Problém měření: dlouhé příklady jsou *zároveň* delší text. Kdybychom porovnali jen
„holá otázka" vs. „otázka + 5 000 tokenů příkladů", nešlo by rozhodnout, jestli
za posun může **obsah příkladů**, nebo prostě **délka vstupu**.

Proto běží **dvě řady o stejných délkách**:

| Řada | Obsah výplně | Co má měřit |
|---|---|---|
| **příklady** | *„Example: 'Vy jste debilové.' → vulgar, direct personal insult"* | vliv **obsahu** |
| **neutrální** | *„This classification task is part of a larger content pipeline…"* | vliv **délky** |

Neutrální řada o vulgaritě neříká vůbec nic — zabírá jen tokeny. Je to kontrolní skupina.

**Metodika:** týž vstupní text pro všechny varianty; běhy prokládané (round-robin),
aby případné zpomalení sítě v čase nepadlo celé na jednu skupinu; medián a p95
místo průměru.

---

## A) Příklady odpověď mění. Neutrální text ne.

Vstup: *„Ty vole, ta appka zase spadla. Už je to potřetí dneska, do prdele…"*

| Délka `instructions` | s příklady | neutrální | rozdíl |
|---|---|---|---|
| holá otázka | **0,925** | — | — |
| ~500 tokenů | **0,353** | 0,898 | **−0,545** |
| ~2 000 tokenů | **0,332** | 0,888 | **−0,556** |
| ~5 000 tokenů | **0,304** | 0,885 | **−0,581** |

**Čtení:** bez příkladů model text označí za vulgární (0,925). S pěti příklady, které
ukazují, že `ty vole` a `do prdele` jsou běžný neformální rejstřík, klesne na 0,353.

Stejně dlouhý neutrální text nezměnil **nic** (0,925 → 0,885, rozptyl 0,013 = šum).

> **To je ten důkaz.** Posun o 0,55 nezpůsobila délka — způsobil ho obsah.
> Kontrolní řada tuhle námitku vylučuje.

### Další příklady už skoro nepřidávají

Uvnitř řady „příklady" je celkový rozptyl jen **0,049**:

```
~500 tokenů (5 příkladů)    0,353
~2000 tokenů (20 příkladů)  0,332   -0,021
~5000 tokenů (50 příkladů)  0,304   -0,028
```

Prvních pět příkladů udělalo posun **−0,572**. Dalších čtyřicet pět přidalo **−0,049**.

**Poměr užitku je zhruba 12:1 ve prospěch prvních pár příkladů.** Opakování téhož
vzoru dál model neposouvá — hranice je už vymezená.

---

## B) Co to stojí

| Varianta | in_tok | medián | p95 | σ | $/1000 volání |
|---|---|---|---|---|---|
| holá otázka | 361 | **1,052 s** | 1,336 s | 0,174 | **$0,0152** |
| příklady ~500 | 941 | 1,127 s | 1,511 s | 0,829 | $0,0395 |
| příklady ~2000 | 2 565 | 1,080 s | 1,447 s | 0,985 | $0,1077 |
| příklady ~5000 | 5 697 | **1,337 s** | 1,832 s | 0,455 | **$0,2393** |
| neutrální ~500 | 727 | 1,033 s | 1,544 s | 0,582 | $0,0305 |
| neutrální ~2000 | 1 825 | 1,136 s | 1,506 s | 0,294 | $0,0767 |
| neutrální ~5000 | 3 960 | **1,330 s** | 1,706 s | 0,230 | $0,1663 |

### Latence

Do ~2 000 tokenů se latence prakticky nemění (rozdíly +0,03 až +0,08 s tonou v šumu,
σ je místy 0,8–0,9 s kvůli výkyvům sítě). Při **~5 000 tokenech přijde znatelný skok:
+0,28 s** proti holé otázce.

Zásadní je, že skok je **v obou řadách stejný** — příklady 1,337 s, neutrální 1,330 s.
**Za zpomalení tedy může délka, ne obsah.** Model počítá stejně dlouho, ať tomu textu
rozumí nebo ne.

Vztaženo k počtu tokenů je to mimochodem velmi dobré: **15,8× víc tokenů = jen 1,27× delší odezva.**
Zpracování vstupu je paralelní, ne sekvenční jako generování u LLM.

### Cena

Cena roste **lineárně s tokeny** — žádné překvapení, účtuje se vstup ($0,042/M).
Ale v absolutních číslech je to pořád nic: 5 000 tokenů příkladů = **24 centů za tisíc volání.**

Dopad se projeví až v objemu:

| Volání/měsíc | holá otázka | s ~5 000 tok. příkladů | rozdíl |
|---|---|---|---|
| 10 000 | $0,15 | $2,39 | +$2,24 |
| 1 000 000 | $15,20 | $239,30 | **+$224** |
| 10 000 000 | $152 | $2 393 | **+$2 241** |

---

## Co z toho plyne pro praxi

### 1. Ano, příklady jsou účinný nástroj

Posun o 0,55 na škále 0–1 je obrovský. Toho se obecným pokynem („buď benevolentní",
−0,12 v [předchozí ablaci](01-criteria-ablation.cs.md)) nedosáhne. **Konkrétní hraniční případy
jsou nejsilnější způsob, jak modelu sdělit, kde přesně leží hranice.**

### 2. Pět příkladů stačí, padesát je plýtvání

| | posun | cena/1000 |
|---|---|---|
| 5 příkladů (~500 tok.) | −0,572 | $0,040 |
| 50 příkladů (~5 000 tok.) | −0,621 | $0,239 |

Šestinásobná cena za 8 % navíc. **Optimum leží u prvních pár dobře zvolených příkladů.**

Pozn.: našich 50 příkladů bylo opakováním téže pětice. Padesát **různých** příkladů
pokrývajících různé hraniční případy by dopadlo nejspíš líp — ale to už je jiný experiment
a je potřeba ho udělat, ne předpokládat.

### 3. Kdy příklady použít a kdy ne

**Použij je, když:**
- Tvoje hranice se liší od obecné normy (kulturní kontext, oborový žargon, firemní pravidla)
- Model se systematicky plete v konkrétním typu případů
- Máš k dispozici reálné hraniční případy z provozu

**Nech to na modelu, když:**
- Úloha je obecná a model ji trefuje (pak příklady jen platíš)
- Nemáš ověřeno, že bez nich rozhoduje špatně
- Jde o malý objem, kde ladění stojí víc než užitek

**Klíčová otázka před přidáním příkladů:** *Změřil jsem baseline bez nich?*
Bez toho nevíš, jestli něco zlepšuješ, nebo jen platíš tokeny navíc.

### 4. Rozpočet na latenci

Do ~2 000 tokenů je latence prakticky zdarma. Nad 5 000 počítej s **+0,3 s**.
Pro interaktivní aplikaci to může být podstatné, pro dávkové zpracování ne.

---

## Poznámka k metodě

První verze tohoto testu měřila jen řadu „příklady" a zachytila posun 0,92 → 0,32.
To by samo o sobě nestačilo — chyběla kontrola vylučující, že za posun může délka.
Druhá řada s neutrální výplní ji doplňuje a teprve dohromady tvoří průkazné měření.

Stejná logika platí pro každé tvrzení o promptování: **když měníš dvě věci naráz
(obsah i délku), nevíš, která z nich zabrala.**

---

## Reprodukce

```
test/test_5_delka_vs_rychlost.py      ← skript (▶ bez argumentů, ~95 s)
test/results/test_5_delka_vs_rychlost.json  ← surová data včetně všech latencí
```

Parametry: model `jev-1.13.0`, 10 běhů na variantu, 7 variant, 70 volání celkem,
prokládané pořadí, cena počítána z `usage.input_tokens` × $0,042/M.

Celý běh stál přibližně **0,5 haléře**.

### Otevřené otázky

- **50 různých příkladů místo opakované pětice** — přidá víc než 0,049?
- **Kde je optimum?** Měřit 1, 2, 3, 5, 8, 13 příkladů a hledat bod nasycení.
- **Záleží na pořadí?** Mění se výsledek, když se příklady přeskládají?
- **Příklady vs. explicitní výčet slov** — co je účinnější na tokenu?
- **Platí poměr 12:1 i v jiných doménách** (spam, tonalita, odborná kvalita)?

---

*Měřeno na `jev-1.13.0` (vydán 15. 9. 2026). Chování se může s dalšími verzemi změnit.*
