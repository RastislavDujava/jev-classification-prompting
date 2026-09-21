# Kulturní norma v `criteria` — rozšířená sada

### Posunout mírné výrazy a zároveň udržet hranici u urážek

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 12 textů × 2 varianty × 5 běhů = 120 volání*

---

## Proč znovu a co je jinak

První pokus měl 5 textů a ukazoval jen jednu stranu věci: že norma posune mírné výrazy dolů.
To je ale polovina úlohy. **Norma, která posune všechno, je vypnutá moderace, ne kalibrace.**

Rozšířená sada:

- **12 textů** místo 5
- **Vypuštěno nejtvrdší slovo** — sada je určená k publikaci
- **Přidány tři hraniční položky**, které norma *nesmí* omluvit: dvě osobní urážky
  a jedna výhrůžka bez jediného vulgarismu

---

## Hlavní výsledek

| | počet | průměrný posun | rozhodnutí |
|---|---|---|---|
| **Mírné výrazy** | 9 | **−0,456** | posunuto dolů ✓ |
| **Hraniční případy** | 3 | **+0,329** | **hranice udržena 3/3** ✓ |

Norma posunula obojí — ale **opačným směrem**. To je přesně to, co dobrá definice dělat má.

---

## Mírné výrazy

| Text | bez normy | s normou | posun |
|---|---|---|---|
| Čistá stížnost (kontrola) | 0,040 | 0,030 | −0,01 |
| *„Ty vole, ta appka zase spadla"* | 0,384 | 0,072 | −0,31 |
| *„Do prdele, zase to spadlo"* | 0,744 | 0,066 | **−0,68** |
| *„Tohle je úplná blbost"* | 0,536 | 0,092 | −0,44 |
| *„Ta nová funkce je kravina"* | 0,660 | 0,090 | −0,57 |
| *„Ty vole, to je paráda!"* (pochvala) | 0,268 | 0,042 | −0,23 |
| **„Konečně to funguje, kurva!"** (nadšení) | **0,980** | **0,108** | **−0,87** |
| *„Sakra, zase to nejde"* | 0,300 | 0,046 | −0,25 |
| *„Oh crap… third damn time"* (anglicky) | 0,916 | 0,176 | −0,74 |

### Nejsilnější případ

*„Konečně to funguje jak má, kurva! Díky za rychlou opravu."*

Bez normy: **0,980** a `flag_for_review`. Je to **poděkování za opravu** — a šlo by
lidskému moderátorovi.

S normou: **0,108** a `allow`. Posun **−0,87**, největší v celé sadě.

Rozdíl je v tom, že norma rozlišuje `kurva` **jako citoslovce** od `kurva` jako urážky.
To je rozlišení, které čeština dělá běžně a anglicky trénovaný model ne.

### Pochvala s hovorovými výrazy

*„Ty vole, to je paráda! Tohle jste vymysleli fakt dobře, klobouk dolů."*

0,268 → 0,042. Zajímavé je, že **v téhle sadě obstála i bez normy** (`allow` v obou
variantách) — na rozdíl od původního měření, kde skončila na `flag_for_review`.
Rozdíl dělá přeformulované zadání varianty A; ukazuje to, jak citlivé jsou tyhle
hraniční případy na drobné změny, a proč je potřeba měřit opakovaně.

### Přesah na angličtinu

Anglický text (*crap*, *damn*) klesl z 0,916 na 0,176, **ačkoli norma mluví výhradně o češtině.**
Potvrzuje to dřívější nález: `criteria` nepůsobí jako filtr na vyjmenovaná slova,
ale jako **posun celkového prahu citlivosti**. Kdo chce zmírnit jen jeden jazyk,
musí to napsat výslovně.

---

## Hraniční případy — tady se pozná dobrá norma

| Text | bez normy | s normou | posun | rozhodnutí |
|---|---|---|---|---|
| *„Vy jste naprostí idioti…"* | 0,598 | **0,960** | +0,36 | block → **block** ✓ |
| *„Vy jste debilové…"* | 0,704 | **0,950** | +0,25 | flag → **block** ✓ |
| **„Přijdu si pro ně osobně a nebude se vám to líbit"** | **0,040** | **0,420** | **+0,38** | flag → **block** ✓ |

### Tohle je nejdůležitější řádek celého měření

Poslední text **neobsahuje jediný vulgarismus**. Je to výhrůžka napsaná spisovně.

Bez normy dostal **0,040** — tedy „žádná vulgarita". A měl pravdu, žádná tam není.
Klasifikátor postavený na otázce *„obsahuje text sprostá slova?"* by ho pustil.

S normou **0,420** a rozhodnutí `block`, protože norma říká, na čem záleží:

> *„What matters is whether a PERSON is being attacked, not whether a coarse word appears."*

**Model tu osu přijal.** Přestal počítat slova a začal se ptát, jestli je někdo terčem.

To je ten samý mechanismus jako u rodičovské kontroly, jen v jiné doméně: **lidé
neměří intenzitu slov, měří vztah k lidem.** A ta osa jde modelu předat.

---

## Změny rozhodnutí

Ze 12 textů se změnila 3 rozhodnutí — a každé správným směrem:

| Text | bez normy | s normou |
|---|---|---|
| Nadšené poděkování s „kurva" | flag_for_review | **allow** |
| Osobní urážka („debilové") | flag_for_review | **block** |
| Výhrůžka bez vulgarismů | flag_for_review | **block** |

**Všechny tři byly v `flag_for_review`** — tedy ve frontě na lidského moderátora.
Norma je rozřadila: jedno ven, dvě zablokovat.

Prakticky: **norma nezmenšila jen falešné poplachy, ale i falešné propustky.**
Zmenšila frontu z obou stran.

---

## Co z toho plyne

**1. Dobrá norma působí oběma směry.** Mírné −0,46, hraniční +0,33. Kdyby posunula
všechno dolů, byla by to vypnutá moderace.

**2. Osa je důležitější než výčet.** Věta *„záleží na tom, jestli je napadán člověk,
ne jestli tam je hrubé slovo"* zachytila i výhrůžku, kterou žádný výčet slov obsáhnout nemohl.

**3. Fronta moderace se zmenšila z obou stran.** Tři případy, které šly člověku,
se rozřadily automaticky — a správně.

**4. Efekt se rozlévá mezi jazyky.** Norma o češtině zmírnila i angličtinu.
Ohraničit se musí výslovně.

---

## Omezení

- **12 textů** je pořád malý vzorek. Ukazuje mechanismus, ne přesnost.
- **Referenční odpovědi jsou můj úsudek.** U `v11` (výhrůžka) by někdo mohl
  namítnout, že „nebude se vám to líbit" není dost konkrétní na `block`.
- **Jedna norma, jeden jazyk.** Jestli platí poměr „mírné dolů / hraniční nahoru"
  v jiných doménách, je otevřená otázka.

---

📄 Data: [results/test_13_vulgarita_v2.json](../results/test_13_vulgarita_v2.json) ·
Skript: [test_13_vulgarita_v2.py](../experiments/10_cultural_norm.py) ·
Texty: [inputs/vulgarity_v2.json](../data/inputs/vulgarity_v2.json)
