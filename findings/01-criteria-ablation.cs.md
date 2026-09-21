# Umění psát `criteria`

### Report z experimentu s modelem Jev (TypeSafe AI)

*Měřeno 21. 9. 2026 · model `jev-1.13.0` · všechna čísla pocházejí z reálných volání API*

---

## Pro koho to je

Pro prompt inženýra, který zná klasifikaci přes LLM — psal systémový prompt, popisoval
v něm tvar výstupního JSONu, přidával few-shot příklady a pak parsoval odpověď.
Jev tu práci rozkládá jinak a tenhle report ukazuje, **kam se ta práce přesunula**.

Krátká odpověď: přesunula se do pole `criteria`. A je to páka mnohem silnější,
než se na první pohled zdá.

---

## Shrnutí pro spěchající

Zadali jsme model stejný text a stejnou otázku. Změnili jsme **pouze definici toho,
co považujeme za vulgární**. Výsledek:

| | bez kulturní normy | s kulturní normou |
|---|---|---|
| `is_vulgar` | **0,98** | **0,13** |
| rozhodnutí o moderaci | `flag_for_review` | **`allow`** |

Posun o **0,85 na škále 0–1**, tedy přes celý rozsah. Text zůstal nezměněný.

Tři nálezy, které z toho plynou:

1. **`criteria` je nejsilnější páka v celém API.** Silnější než formulace otázky.
2. **Účinek nese konkrétní výčet, ne obecný pokyn.** „Buď benevolentní" posunulo o 0,12. Výčet konkrétních slov posunul o 0,82.
3. **Efekt je deterministický.** Šest běhů, nulový rozptyl. Není to náhoda, je to nastavení.

---

## Obsah

1. [Co se změnilo proti klasickému promptování](#1-co-se-změnilo-proti-klasickému-promptování)
2. [Přesné zadání experimentu](#2-přesné-zadání-experimentu)
3. [Naměřené výsledky, text po textu](#3-naměřené-výsledky-text-po-textu)
4. [Ablační studie: která část criteria účinkuje](#4-ablační-studie-která-část-criteria-účinkuje)
5. [Teorie: proč to funguje](#5-teorie-proč-to-funguje)
6. [Pravidla pro psaní criteria](#6-pravidla-pro-psaní-criteria)
7. [Rizika a etika](#7-rizika-a-etika)
8. [Reprodukce](#8-reprodukce)

---

## 1. Co se změnilo proti klasickému promptování

Klasický LLM klasifikátor vypadá takto — jeden text, ve kterém je všechno najednou:

```
Jsi moderátor obsahu. Vrať JSON: {"vulgar": true|false, "confidence": 0.0-1.0}
Příklad: "Ty vole" -> {"vulgar": true, "confidence": 0.9}
...15 dalších příkladů...
Text: "Ty vole, ta appka zase spadla."
```

Jev to rozděluje do tří pojmenovaných polí:

| Klasický prompt | Jev |
|---|---|
| „Jsi moderátor obsahu" | — odpadá |
| „Vrať JSON ve tvaru {...}" | — odpadá, tvar je daný typem otázky |
| 15 few-shot příkladů | — odpadá |
| „Rozhodni, jestli je text vulgární" | → `instructions` |
| „vulgární = nadávky, sprostá slova" | → **`criteria`** |
| Text k vyhodnocení | → `state` |

**Podstatné je to, co zbylo.** Zmizel obal — role, formát, příklady. Zůstala otázka
a definice pojmů. A protože definice je teď samostatné pojmenované pole, dá se
**kontrolovaně měnit a měřit**, což v jednolitém promptu šlo těžko.

Tenhle report je o tom druhém poli.

---

## 2. Přesné zadání experimentu

### Testovaný text

```
Ty vole, ta appka zase spadla. Už je to potřetí dneska, do prdele.
Fakt nechápu, jak může být takový blbost v produkci.
```

Volba textu je záměrná. Obsahuje `ty vole`, `do prdele` a `blbost` — výrazy, které
jsou v české neformální mluvě běžné, ale jejichž doslovný anglický překlad
(*you ox*, *into the arse*, *stupidity*) zní podstatně hruběji než originál.
Právě tady se pozná, jestli jde norma posunout.

### Varianta A — bez normy (kontrolní skupina)

```json
{
  "type": "noul",
  "instructions": "Does this text contain vulgar or profane language?",
  "criteria": {
    "true":  "The text contains swearing, profanity, or crude language",
    "false": "The text is free of vulgar language"
  }
}
```

Takhle by otázku napsal kdokoliv. Je věcná, srozumitelná, zdánlivě neutrální.

### Varianta B — s normou

```json
{
  "type": "noul",
  "instructions": "Does this text contain vulgar or profane language, judged by the norms of a Czech-language community app?",
  "criteria": {
    "true": "The text contains language that a Czech user would find genuinely offensive: sexual slurs, aggressive insults directed at a person (debil, kretén, idiot), or the strongest Czech profanity (kurva as an insult, piča, zkurvený, mrdat).",
    "false": "The text is clean, OR it contains only mild Czech colloquial expressions that are a normal part of everyday informal speech in the Czech Republic and are NOT treated as offensive by Czech speakers. These specifically include: 'do prdele', 'ty vole', 'blbost', 'kravina', 'sakra', 'hovno', and 'kurva' when used as a filler or exclamation rather than as an insult. Czech informal register tolerates these far more than English does; a literal English translation sounds much harsher than the Czech original."
  }
}
```

**Co přesně se mezi A a B liší:**

- `instructions` — přibyl dovětek „judged by the norms of a Czech-language community app". Ablace níže ukáže, že tenhle dovětek sám o sobě dělá skoro nic.
- `criteria` — obě větve dostaly konkrétní obsah. **Tady je celý účinek.**

Kromě otázky `is_vulgar` běžely v témže volání ještě tři další
(`vulgarity_level` jako Score, `moderation_action` jako Choice, `is_positive` jako Noul),
každá ve variantě A i B. Otázky v jednom volání běží paralelně a nevidí na sebe.

### Metodika

- 3 běhy na kombinaci, porovnávají se průměry
- Práh šumu 0,05 (změřeno dříve: model kolísá ±0,01–0,03)
- Ověření stability: 6 běhů klíčové kombinace

---

## 3. Naměřené výsledky, text po textu

### 3.1 Mírný český text

> *„Ty vole, ta appka zase spadla. Už je to potřetí dneska, do prdele. Fakt nechápu, jak může být takový blbost v produkci."*

| Metrika | A (bez normy) | B (s normou) | posun |
|---|---|---|---|
| `is_vulgar` (Noul) | **0,980** | **0,133** | **−0,847** |
| `vulgarity_level` (Score 0–3) | 2,03 | 0,17 | **−1,87** |
| `is_positive` (Noul) | 0,020 | 0,043 | +0,023 (šum) |
| `moderation_action` (Choice) | `flag_for_review` | **`allow`** | **překlopeno** |

Rozdělení pravděpodobností u moderace — tady je vidět, jak se posunula celá váha:

```
A:  block 0,18  │  flag_for_review 0,58  │  allow 0,24
B:  block 0,00  │  flag_for_review 0,13  │  allow 0,87
```

Bez normy jde text lidskému moderátorovi. S normou projde rovnou ven.
V provozu je to rozdíl mezi frontou zahlcenou běžnou hospodskou mluvou a frontou,
ve které jsou jen skutečné problémy.

### 3.2 Přátelský text s vulgarismy

> *„Ty vole, to je paráda! Tohle jste vymysleli fakt dobře, klobouk dolů. Konečně to funguje jak má, kurva."*

| Metrika | A | B | posun |
|---|---|---|---|
| `is_vulgar` | **0,980** | **0,233** | **−0,747** |
| `vulgarity_level` | 2,01 | 1,07 | −0,94 |
| `is_positive` | 0,933 | 0,940 | +0,007 |
| `moderation_action` | `flag_for_review` | **`allow`** | **překlopeno** |

**Nejdůležitější řádek celého experimentu.** Text je pochvala — model to poznal v obou
variantách (`is_positive` 0,93). Přesto ho bez normy označil za vulgární a poslal k moderaci.

Prakticky: **spokojený zákazník by dostal svůj příspěvek zadržený, protože napsal „ty vole".**
Přesně tenhle typ falešného poplachu odrazuje uživatele komunitních aplikací — a bez
kulturní kalibrace vzniká systematicky, ne náhodně.

### 3.3 Silný český text — kontrola, že norma není vypínač

> *„Vy jste naprostí debilové, ta vaše zkurvená appka mi smazala data. Jděte do piče s takovým hnusem."*

| Metrika | A | B | posun |
|---|---|---|---|
| `is_vulgar` | 0,990 | 0,980 | −0,010 (šum) |
| `vulgarity_level` | 2,92 | 2,99 | +0,07 |
| `moderation_action` | `block` | `block` | beze změny |

Norma tento text **neomluvila**, a to je zásadní. Do `criteria` nebylo napsáno
„buď benevolentní", ale byly vyjmenovány konkrétní výrazy na obou stranách hranice.
Model hranici udržel: osobní urážky (`debilové`) a nejsilnější vulgarismy
(`piče`, `zkurvená`) zůstaly blokované.

Kdyby norma působila jako plošné zmírnění, klesl by i tento text. Neklesl.
**Jde tedy o přesný nástroj, ne o tupý posuvník.**

### 3.4 Čistý text — kontrola, že se nic nerozbilo

> *„Ta aplikace zase spadla. Už je to potřetí dneska. Nechápu, jak se něco takového mohlo dostat do produkce."*

| Metrika | A | B | posun |
|---|---|---|---|
| `is_vulgar` | 0,047 | 0,030 | −0,017 (šum) |
| `moderation_action` | `allow` | `allow` | beze změny |

### 3.5 Anglický mírný text — nezamýšlený přesah

> *„Oh crap, the app crashed again. Third damn time today. I don't get how this kind of rubbish ships to production."*

| Metrika | A | B | posun |
|---|---|---|---|
| `is_vulgar` | 0,937 | **0,343** | **−0,593** |
| `vulgarity_level` | 1,74 | 0,82 | −0,91 |

Norma byla formulovaná **výslovně o češtině**, přesto ovlivnila hodnocení anglického textu.
Model si z ní zjevně odnesl obecnější nastavení *„mírné nadávky nejsou problém"*
a vztáhl ho i na `crap` a `damn`.

**Praktický důsledek:** `criteria` nepůsobí jako přesný filtr na vyjmenovaná slova,
ale jako **posun celkového prahu citlivosti**. Kdo chce zmírnit jen jeden jazyk
a v ostatních zůstat přísný, musí to napsat výslovně — jinak se efekt rozlije.

### 3.6 Souhrnná tabulka

| Text | `is_vulgar` A → B | Moderace A → B |
|---|---|---|
| Mírný český | 0,98 → **0,13** | flag → **allow** |
| Přátelský s vulgarismy | 0,98 → **0,23** | flag → **allow** |
| Anglický mírný | 0,94 → **0,34** | allow → allow |
| Silný český | 0,99 → 0,98 | **block → block** |
| Čistý | 0,05 → 0,03 | allow → allow |

### 3.7 Stabilita efektu

Klíčová kombinace, 6 běhů:

```
A bez normy:  0,980  0,980  0,980  0,980  0,980  0,980   rozptyl 0,000
B s normou:   0,130  0,130  0,130  0,130  0,130  0,130   rozptyl 0,000
```

**Nulový rozptyl.** Na této úloze je model deterministický a naměřený rozdíl není šum.
(Jinde jsme drobné kolísání ±0,01–0,03 pozorovali, takže determinismus nelze
předpokládat plošně — ale zde platí.)

---

## 4. Ablační studie: která část criteria účinkuje

Sám posun je zajímavý, ale užitečnější je vědět, **co přesně ho způsobilo**.
Rozebrali jsme definici na části a měřili každou zvlášť. Stejný text, stejný model,
3 běhy na variantu.

| # | Varianta | `is_vulgar` | Posun vs. baseline |
|---|---|---|---|
| E1 | Baseline (obecné criteria) | **0,980** | — |
| E2 | Jen `instructions` s českým kontextem, **criteria vynechána** | 0,943 | −0,04 |
| E3 | Vágní pokyn: *„Be lenient about Czech informal speech"* | 0,863 | −0,12 |
| E4 | **Jen výčet slov**, bez vysvětlení kulturního kontextu | **0,163** | **−0,82** |
| E5 | Plná norma (varianta B) | **0,133** | **−0,85** |
| E6 | Plná norma, ale **obecné `instructions`** | 0,160 | −0,82 |
| E7 | Jen větev `false` (větev `true` vynechána) | 0,283 | −0,70 |
| E8 | Jen větev `true` (větev `false` vynechána) | 0,780 | −0,20 |
| — | Norma ve `state` místo v `criteria` | **0,093** | **−0,89** |

### Co z toho plyne

**Kontext v `instructions` skoro nic nedělá (E2: −0,04).**
Dovětek „judged by the norms of a Czech-language community app" zní dobře, ale sám
posune sotva nad úroveň šumu. Kdo napíše jen tohle a spolehne se na to, nedostane nic.

**Vágní pokyn je slabý (E3: −0,12).**
„Buď benevolentní k české neformální mluvě" je instrukce, jakou by člověk pochopil
okamžitě. Model posunul o 0,12 — směrem správným, ale prakticky bezvýznamně.
**Model nepotřebuje postoj, potřebuje hranici.**

**Konkrétní výčet nese prakticky celý účinek (E4: −0,82).**
Samotný seznam slov bez jakéhokoli kulturního vysvětlení udělal 96 % práce.

**Vysvětlení kontextu přidává málo (E5 vs. E4: −0,03).**
Věta o tom, že český rejstřík je tolerantnější než anglický, zní přesvědčivě, ale
měřitelně přidala 0,03 — na hraně šumu. **Hezky napsaná próza není to, co model posouvá.**

**`instructions` vs. `criteria` (E6 vs. E5: rozdíl 0,03).**
S plnou normou v `criteria` je skoro jedno, co je v `instructions`. Potvrzuje E2
z druhé strany: **těžiště práce je v `criteria`.**

**Nesymetrie větví (E7: −0,70 vs. E8: −0,20).**
Definovat, co **není** porušení, je zhruba 3,5× účinnější než definovat, co porušení je.
Model má patrně vlastní silnou představu o tom, co je vulgární; rozšířit ji dál
(E8) mění málo. Vymezit **výjimky** (E7) mění hodně.

> Toto je nejpřenositelnější nález celého reportu. Platí-li i v jiných doménách,
> znamená to: **energii věnuj popisu toho, co má projít, ne toho, co má spadnout.**

**Norma ve `state` funguje také (−0,89), dokonce o chlup silněji.**
Testováno se strukturovaným `state`:

```json
{
  "policy": "In this Czech community app, mild Czech colloquialisms are normal register...",
  "text": "Ty vole, ta appka zase spadla..."
}
```
a otázkou `"Does `text` contain vulgar language, judged by `policy`?"`.

**Kdy co použít:**

| | `criteria` | `state`|
|---|---|---|
| Norma je stabilní, platí pro všechna volání | ✅ | |
| Norma se mění podle tenanta, jazyka, fóra | | ✅ |
| Norma přichází z databáze / konfigurace | | ✅ |
| Chceš ji mít verzovanou u otázky | ✅ | |

Druhá varianta je zajímavá pro víceklientské nasazení: každý zákazník má vlastní
`policy`, otázky zůstanou stejné.

---

## 5. Teorie: proč to funguje

### 5.1 Vulgarita není vlastnost textu

Základní omyl, se kterým se k takové úloze přistupuje, je představa, že text
*nějakou vulgaritu má* a model ji *odhaluje* — jako když teploměr měří teplotu.

Data ukazují něco jiného. Týž text dostal 0,98 i 0,13. Neměnil se text, měnila se norma.

**Vulgarita je vztah mezi textem a normou, ne vlastnost textu.** Model nic neodhaluje;
model **porovnává** text s normou, kterou mu dáš. A když mu žádnou nedáš, použije
nějakou výchozí.

### 5.2 Výchozí norma existuje, i když ji nenapíšeš

Varianta A nevypadá, že by nějakou normu obsahovala. „Does this text contain vulgar
or profane language?" působí neutrálně. Ale neutrální není — jen je ta norma **implicitní**
a pochází z trénovacích dat, tedy převážně z angloamerického internetu.

Proto `ty vole` dostalo 0,98. Podle anglosaské normy to vulgární je. Podle české není.

**Pro produkt to znamená:** když norma není napsaná, nějaká tam stejně je a nejspíš
neodpovídá tvému publiku. Napsat ji není přizpůsobování modelu — je to **oprava
skryté výchozí hodnoty**.

### 5.3 Proč konkrétní výčet poráží vysvětlení

Ablace ukázala rozdíl mezi *„buď benevolentní"* (−0,12) a výčtem slov (−0,82).

Souvisí to s tím, jak dokumentace popisuje chování modelu: *„odpovídá na otázku,
kterou jsi napsal, ne na tu, kterou jsi myslel"*. Model čte doslova.
„Buď benevolentní" je postoj, ze kterého si musí hranici odvodit sám — a odvodí ji mělce.
Seznam slov hranici **určuje**.

Z dokumentace pochází rada, která je pro celou tuhle práci klíčová:

> *Když se díváš na špatnou odpověď a přistihneš se, jak vysvětluješ, co jsi vlastně
> myslel — to vysvětlení je ta chybějící polovina zadání.*

To dává hotovou smyčku ladění: špatná odpověď → řekni nahlas, cos myslel →
**napiš to do `criteria`** → změř znovu.

### 5.4 Co to znamená pro roli prompt inženýra

U klasického LLM klasifikátoru se energie rozdělovala mezi instrukci, formát výstupu,
few-shot příklady a ošetřování rozbitého JSONu. První a poslední tři položky u Jeva mizí.

Zbývá **volba otázky** a **definice pojmů**. A podle ablace nese hlavní váhu ta druhá.

Zároveň se ta práce stává **měřitelnou**. Definice je samostatné pole, takže se dá
měnit po částech a měřit dopad — jako v této ablaci. To v jednolitém promptu,
kde je všechno propletené, prakticky nešlo.

---

## 6. Pravidla pro psaní criteria

Odvozeno z měření výše.

### Pravidlo 1 — Vyjmenuj, nevysvětluj

```diff
- "false": "Be lenient about Czech informal speech"           // −0,12
+ "false": "...only: 'do prdele', 'ty vole', 'blbost',
+           'kravina', 'sakra', 'hovno'..."                    // −0,82
```

Příklady a výčty fungují. Postoje ne.

### Pravidlo 2 — Popisuj především to, co má projít

Vymezení výjimek (E7: −0,70) je ~3,5× účinnější než rozšiřování zakázaného (E8: −0,20).
Model už má vlastní představu o tom, co je špatně. Co potřebuje vědět, je **kde končí**.

### Pravidlo 3 — Drž obě strany hranice

Vyjmenovat jen povolené nestačí, pokud chceš zároveň udržet přísnost tam, kde má být.
Varianta B popsala obojí — a proto zmírnila mírný text a zároveň **zablokovala** urážky.

### Pravidlo 4 — `criteria` musí navazovat na `instructions`

Ber je jako pokračování věty, ne jako samostatný odstavec. Noul, kde `true` fakticky
znamená „ne", měří hůř — na to dokumentace výslovně upozorňuje.

### Pravidlo 5 — Efekt se rozlévá, ohranič ho

Norma o češtině zmírnila i angličtinu (−0,59). Chceš-li úzký efekt, napiš výslovně,
kde **neplatí**.

### Pravidlo 6 — Stabilní norma do `criteria`, proměnlivá do `state`

Viz tabulka v sekci 4.

### Pravidlo 7 — Měř, nehádej

Naměřený rozdíl mezi „to zní rozumně" a „to funguje" byl v ablaci **sedminásobný**
(E3 vs. E4). Intuice tady selhává. Ablace stojí pár haléřů.

### Šablona

```json
{
  "type": "noul",
  "instructions": "<jedna věcná otázka, ano/ne, bez postojů>",
  "criteria": {
    "true":  "<co JE porušení: konkrétní kategorie + příklady>",
    "false":  "<čisté> NEBO <výslovné výjimky: konkrétní výčet toho, co se toleruje a proč>"
  }
}
```

### Kontrolní seznam

- [ ] Obsahuje `criteria` **konkrétní příklady**, ne jen obecné pojmy?
- [ ] Je popsáno, co má **projít**, ne jen co má spadnout?
- [ ] Jsou popsané **obě** větve?
- [ ] Navazuje `criteria` logicky na `instructions`?
- [ ] Je ohraničeno, kde norma **neplatí**?
- [ ] Byla změřena **baseline bez normy** pro srovnání?
- [ ] Proběhla ablace — **víš, která část nese účinek**?
- [ ] Bylo ověřeno na textech, které **mají zůstat blokované**?

---

## 7. Rizika a etika

Tenhle report ukazuje, jak silně jde klasifikací pohnout. Totéž platí oběma směry
a stojí za to to pojmenovat.

### 7.1 Jde i opačně: zpřísnit

Ověřeno. Zadání *„v našem korporátním fóru je jakýkoli veřejný projev frustrace
porušením, i bez vulgarismů"*:

| Text | `is_vulgar` / porušení |
|---|---|
| Čistý stížnostní text (**bez jediné nadávky**) | **0,847** |
| Mírný český text s vulgarismy | 0,947 |

Text *„Ta aplikace zase spadla. Nechápu, jak se něco takového mohlo dostat do produkce."*
— naprosto slušný — dostal 0,85 jako porušení. Stačilo do `criteria` napsat,
že kritika je porušení.

**Takže: `criteria` neumí jen zmírňovat. Umí i udělat z běžné kritiky porušení pravidel.**
Systém, který takhle nakalibrujete, bude tiše mazat nepohodlnou zpětnou vazbu — a čísla
u toho budou vypadat stejně věrohodně jako v každém jiném případě.

### 7.2 Co si z toho odnést

**Definice je politické rozhodnutí, ne technický detail.** Rozhoduje o tom, čí projev
projde a čí ne. Nepatří proto k tomu, co se dolaďuje mimochodem — patří k tomu, co se
schvaluje, verzuje a dá se dohledat.

**Doporučení pro nasazení:**

- Definice **verzovat v gitu** spolu s kódem.
- U každé změny vést **naměřený dopad** na kontrolní sadě (kolik textů změnilo rozhodnutí).
- Držet **regresní sadu** textů, které musí zůstat blokované — varianta B v tomto reportu
  by jí prošla, silný text zůstal na `block`.
- Vědět, že model má **skrytou výchozí normu**. Nenapsat žádnou neznamená být neutrální.
- Confidence používat k směrování, ne jako důkaz správnosti: měří soustředěnost
  rozdělení, ne pravdivost.

---

## 8. Reprodukce

```
test/
├── inputs/vulgarity.json                  ← testované texty
├── questions/vulgarity_A_bez_normy.json   ← varianta A
├── questions/vulgarity_B_s_normou.json    ← varianta B
├── test_4_kulturni_norma.py               ← hlavní experiment (▶ bez argumentů)
└── results/test_4_kulturni_norma.json     ← surová data
```

Spuštění: otevřít `test_4_kulturni_norma.py` a stisknout ▶. Běh trvá ~40 s.

**Parametry:** model `jev-1.13.0`, endpoint `POST https://api.typesafe.ai/v1/systemone`,
3 běhy na kombinaci (6 u ověření stability), práh šumu 0,05.

**Cena:** celý experiment včetně ablace vyšel přibližně na **0,4 haléře**.
Vstup se účtuje $0,042 za milion tokenů, výstup je zdarma. Ablační studie je
tedy z nákladového hlediska prakticky zdarma — důvod ji vynechat neexistuje.

### Otevřené otázky

- **Kde přesně leží hranice?** Postupně ubírat slova z výčtu a hledat bod zlomu.
- **Jak krátká norma stačí?** E4 ukázal, že vysvětlení skoro nepřidává — kolik ze seznamu je nosných?
- **Platí nesymetrie větví i jinde?** Ověřit na doménách mimo vulgaritu (spam, off-topic, odborná kvalita).
- **Jak se chová `state` varianta při víceklientském nasazení?** Norma na tenanta, sdílené otázky.
- **Kalibrace confidence:** mění vložená norma i spolehlivost confidence, nebo jen polohu odpovědi?

---

*Model `jev-1.13.0` je čerstvý (vydán 15. 9. 2026) a jeho chování se s dalšími verzemi
může změnit. Čísla v tomto reportu platí pro tuto verzi a tyto texty; před nasazením
doporučujeme ověření na vlastních datech.*
