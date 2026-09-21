# Tool routing: model má vlastní bias, a jde zlomit

### Klasifikace „odpovědět z vlastních znalostí, nebo googlit?"

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 15 dotazů × 3 varianty × 3 běhy = 135 volání*

---

## Proč právě tahle úloha

Předchozí testy ukázaly posun na vulgaritě, kde **objektivně správná odpověď neexistuje** —
záleží na kulturní normě. Namítnout se dá, že jsme jen přesvědčili model o svém názoru.

Tool routing je jiný. **Správná odpověď existuje** a jde ji ověřit: buď se ta informace
od trénování změnila, nebo ne. A zároveň jde o doménu, kde model **musí** mít vlastní bias —
rozhoduje o tom, co sám neví.

Když se na téhle úloze ukáže posun, není to otázka názoru. Je to **měřitelná chyba
a její oprava**.

---

## Hlavní výsledek

| Varianta zadání | Přesnost | Chybné dotazy |
|---|---|---|
| **A — naivní** | **10/15 (66,7 %)** | pope_current, ceo_openai, best_laptop, current_us_president, company_acquired |
| **B — poučená (bez příkladů)** | **15/15 (100 %)** | — |
| **C — poučená + 6 příkladů** | **15/15 (100 %)** | — |

**Naivní zadání se plete v jednom z tří případů. A plete se systematicky —
ve všech pěti případech stejným směrem: neposílá na vyhledávání to, co by mělo.**

---

## Bias, který jsme hledali

Nejlépe je vidět na dvojicích, kde je otázka formulačně skoro totožná,
ale správná odpověď opačná:

| Dvojice | A naivní | B poučená | C s příklady |
|---|---|---|---|
| „current Pope" vs. „Pope during WWII" | **0,43** / 0,08 | 0,88 / 0,05 | 0,95 / 0,05 |
| „current US president" vs. „who won 2020" | **0,43** / 0,09 | 0,93 / 0,09 | 0,96 / 0,13 |
| „CEO of OpenAI" vs. „capital of France" | **0,35** / 0,03 | 0,89 / 0,03 | 0,92 / 0,03 |
| „latest React version" vs. „sort in Python" | 0,92 / 0,04 | 0,96 / 0,03 | 0,97 / 0,03 |

### Čtení

**Historickou stranu trefil model vždycky** (0,03–0,09 ve všech variantách).
Ví, že papež za druhé světové války se už nezmění.

**Aktuální stranu netrefil.** „Who is the current Pope?" dostalo jen **0,43** — tedy
pod prahem, model by odpověděl z vlastní hlavy. Přitom slovo *current* tam přímo stojí.

**Co to prozrazuje:** model má uloženou odpověď a vnímá ji jako znalost, kterou má.
Nerozlišuje mezi *„vím to"* a *„věděl jsem to v době trénování"*.
To je přesně ten bias z tréninkových dat, který jsi předpokládal.

Zajímavá výjimka: **„latest React version" trefil i naivní varianta (0,92).**
U softwarových verzí model ví, že zastarávají. U lidí ve funkcích ne.
Bias tedy není plošný — je **doménově specifický**.

### Nejtěžší případ

`company_acquired` („Has Figma been acquired?") — naivní 0,32, poučená 0,57,
s příklady 0,61. Ani nejlepší varianta se nedostala vysoko.

Je to pochopitelné: akvizice je něco mezi událostí a stavem. Model má v datech
nějakou verzi příběhu a nemá signál, že se mohl změnit. **Pro produkci by tenhle
dotaz patřil do pásma nejistoty, ne k automatickému rozhodnutí.**

---

## Překvapení: příklady nebyly potřeba

Toto je nález, který mění původní tezi.

Rozložil jsem zadání na části a měřil, co přesně opravu způsobilo
(8 kontrolních dotazů, 2 běhy):

| Varianta | `instructions` | `criteria` | Přesnost |
|---|---|---|---|
| A | naivní | naivní | **3/8 (38 %)** |
| A2 | **poučená** | naivní | **3/8 (38 %)** |
| A3 | naivní | **poučená** | **8/8 (100 %)** |
| B | poučená | poučená | 8/8 (100 %) |
| C2 | naivní **+ 6 příkladů** | naivní | 7/8 (88 %) |

### Co z toho plyne

**1. Opravu způsobila `criteria`, ne `instructions`.**
Vylepšení samotných `instructions` (A2) nepřineslo **vůbec nic** — 38 % jako předtím.
Vylepšení samotných `criteria` (A3) dalo rovnou **100 %**.

To je silné potvrzení dřívější ablace u vulgarity, kde `instructions` přinesly −0,04
a `criteria` −0,82. **Těžiště práce je v `criteria`, a to napříč doménami.**

**2. Dobře napsaná `criteria` stačila. Příklady nepřidaly nic.**
B (bez příkladů) i C (s příklady) daly shodně 100 %. Na této úloze byly příklady zbytečné.

**3. Příklady samy o sobě fungují, ale hůř než criteria.**
C2 — příklady vložené do naivního zadání — dalo 88 %. Tedy zlepšení z 38 %,
ale pořád horší než 100 % z dobře napsaných criteria.

### Jak to sladit s tezí o příkladech

Původní teze zněla: *„bias jde zlomit příklady"*. Přesnější formulace po tomto měření:

> **Bias jde zlomit tím, že modelu dodáš chybějící informaci. Příklady jsou jen
> jeden ze způsobů, jak to udělat — a ne vždy nejúčinnější.**

Rozhodující je, **co** informace říká, ne **jakou formou** přijde:

| Co chybělo | Nejúčinnější forma |
|---|---|
| **Pojem** („stará se informace od trénování?") | ✅ vysvětlení v `criteria` |
| **Hranice** („`ty vole` patří do kategorie mírné") | ✅ příklady |

U vulgarity nešlo pojem vysvětlit — *„mírné české výrazy"* je prázdná kategorie,
dokud neřekneš které. Proto tam zabraly příklady.

U tool routingu **šlo** pojem vysvětlit: *„informace, která se mohla od trénování změnit"*
je popsatelné pravidlo. Proto stačila `criteria` a příklady byly navíc.

**To přesně odpovídá rozlišení, které zavedl [leepokai](https://github.com/leepokai/llm-prompt-techniques-on-jev)** —
information-carrying vs. wording. Obojí, co u nás zabralo, nese informaci.
Co nezabralo (A2, samotné instructions), ji nenese.

---

## Úplné výsledky

| Dotaz | správně | A naivní | B poučená | C příklady |
|---|---|---|---|---|
| Who is the current Pope? | search | **0,430** ✗ | 0,883 ✓ | 0,947 ✓ |
| Who was the Pope during WWII? | model | 0,077 ✓ | 0,050 ✓ | 0,047 ✓ |
| What is the capital of France? | model | 0,030 ✓ | 0,027 ✓ | 0,030 ✓ |
| Who is the CEO of OpenAI? | search | **0,350** ✗ | 0,887 ✓ | 0,920 ✓ |
| How do I sort dicts in Python? | model | 0,040 ✓ | 0,030 ✓ | 0,030 ✓ |
| Latest stable version of React? | search | 0,917 ✓ | 0,960 ✓ | 0,970 ✓ |
| Weather in Prague right now? | search | 0,970 ✓ | 0,980 ✓ | 0,983 ✓ |
| Explain photosynthesis | model | 0,040 ✓ | 0,030 ✓ | 0,030 ✓ |
| Apple's stock price? | search | 0,953 ✓ | 0,973 ✓ | 0,980 ✓ |
| Boiling point of water? | model | 0,040 ✓ | 0,030 ✓ | 0,033 ✓ |
| Best laptop for programming? | search | **0,340** ✗ | 0,797 ✓ | 0,840 ✓ |
| Who won 2020 US election? | model | 0,087 ✓ | 0,093 ✓ | 0,133 ✓ |
| Who is the current US president? | search | **0,430** ✗ | 0,930 ✓ | 0,960 ✓ |
| How to say hello in Japanese? | model | 0,030 ✓ | 0,020 ✓ | 0,030 ✓ |
| Has Figma been acquired? | search | **0,320** ✗ | 0,570 ✓ | 0,607 ✓ |

### Pozorování k prahu

Správné odpovědi jsou většinou velmi vyhraněné — buď pod 0,10, nebo nad 0,90.
Výjimky jsou `company_acquired` (0,57–0,61) a `best_laptop` (0,80–0,84).

**Pro produkci:** práh 0,5 by fungoval, ale pásmo 0,4–0,7 si zaslouží zvláštní
zacházení — buď vyhledat pro jistotu (vyhledávání je levnější než špatná odpověď),
nebo eskalovat.

---

## Přesné znění variant

### A — naivní

```json
{
  "type": "noul",
  "instructions": "Does answering this user query require searching the internet?",
  "criteria": {
    "true": "The query needs a web search to answer",
    "false": "The AI model can answer from its own knowledge"
  }
}
```

Napsané, jak by to napsal kdokoliv. Věcné, srozumitelné — a chybuje ve 33 % případů.

### B — poučená

```json
{
  "type": "noul",
  "instructions": "Does answering this user query require calling a web search tool, rather than relying on the model's own trained knowledge?",
  "criteria": {
    "true": "The answer depends on information that may have changed since the model's training data was collected. This includes: current office holders (presidents, CEOs, popes), live data (weather, prices, scores), latest software versions, current market recommendations, and the present status of companies or products. Even if the model has a confident answer stored, that answer may now be outdated.",
    "false": "The answer is stable over time and will not have changed since training. This includes: historical events that are settled, physical and mathematical constants, established scientific explanations, language translation, and programming techniques that have been stable for years."
  }
}
```

Klíčová věta je poslední ve větvi `true`:

> *„Even if the model has a confident answer stored, that answer may now be outdated."*

Ta přímo adresuje bias — říká modelu, že **jeho vlastní jistota není důkaz aktuálnosti**.

### C — s příklady

Totéž jako B, plus do `instructions`:

```
Examples of the distinction:
"Who is the current Pope?" -> search. Popes change; a stored answer may be stale.
"Who was the Pope during World War II?" -> model. A settled historical fact.
"Who is the CEO of Microsoft?" -> search. Leadership changes over time.
"Who founded Microsoft?" -> model. Founding facts never change.
"What is the latest version of Node.js?" -> search. Version numbers drift constantly.
"How do I read a file in Node.js?" -> model. The technique has been stable for years.
```

Na této úloze nepřineslo nic navíc (100 % → 100 %). Hodnoty se posunuly
o 0,03–0,06 výš, ale žádné rozhodnutí se nezměnilo.

---

## Praktický závěr

**1. Bias existuje a je měřitelný.** Naivní klasifikátor 66,7 %, u aktuálních
osobností pod prahem. Nejde o náhodný šum — je systematický a jednosměrný.

**2. Opravit ho jde levně.** Dva odstavce v `criteria` = 100 %.
Cena: +250 tokenů na volání, ~2 centy na tisíc volání.

**3. `criteria` jsou to, na čem záleží.** Vylepšení `instructions` samo nepřineslo nic.
Ověřeno napříč dvěma různými doménami.

**4. Volba nástroje závisí na tom, co chybí.** Chybí-li pojem, vysvětli ho.
Chybí-li hranice, ukaž příklady. Nemá smysl sahat po příkladech automaticky.

**5. Pro tvůj starý klasifikátor:** ten „fakt dost obrovský" prompt patrně řešil
totéž, co tu zvládly dva odstavce — jen se to muselo prokousat skrz formát výstupu,
few-shot příklady a instrukce k parsování. Tady zůstala jen definice.

---

## Co by stálo za doměření

- **Kolik z těch dvou odstavců je nosných?** Ablace jako u vulgarity — najít minimální účinnou definici.
- **Větší sada.** 15 dotazů je málo na publikovatelnou přesnost; 50–100 by dalo jistější čísla.
- **Kategorie, kde bias přetrvá i po opravě.** `company_acquired` zůstalo na 0,61 — existují další?
- **Choice místo Noulu.** Tři cesty (`model` / `search` / `ask_user`) místo binárního rozhodnutí.
- **Adversariální dotazy.** Co dotaz, který vypadá historicky, ale není?
  („Kolik zemí má EU?" — mění se pomalu, ale mění.)

---

📄 Data: [results/test_6_tool_routing.json](../results/test_6_tool_routing.json) ·
Skript: [test_6_tool_routing.py](../experiments/05_tool_routing.py) ·
Dotazy: [inputs/routing_queries.json](../data/inputs/routing_queries.json)
