# Výzkum klasifikace na modelu Jev

**Kolik z chování klasifikátoru si určujete vy?**

Reprodukovatelné pokusy s modelem [Jev od TypeSafe](https://docs.typesafe.ai/) — System One
modelem, který vrací typovaná rozhodnutí místo textu. Každé číslo tady pochází ze
skutečného volání API a každý pokus se spouští jedním příkazem.

> **Stav:** probíhající výzkum, zahájen 21. 9. 2026 — šest dní po vydání modelu.
> Další pokusy přibývají v následujících dvou týdnech.

---

## Krátce

Klasifikátor někde vede hranici. Když ji nenapíšete vy, napsal ji za vás někdo jiný —
trénovací data a rozhodnutí autorů modelu.

**Ta výchozí hranice není neutrální. Je něčí.** Tyhle pokusy měří čí, jak daleko je od
toho, co chtějí skuteční lidé, a kolik z ní jde posunout.

Napříč šesti doménami a 1 180 voláními API:

| | naivní zadání | pořádně napsaná criteria |
|---|---|---|
| **Přesnost** | **70 %** (57/82) | **96 %** (79/82) |

Ten rozdíl není tím, že by model zmoudřel. Je to rozdíl mezi přijetím jeho vestavěné
normy a vyslovením té vlastní.

---

## Hlavní zjištění

### 1. `criteria` je nejsilnější páka v celém API

Stejný text, stejná otázka, jiná definice toho, co se počítá jako vulgární:

| | bez kulturní normy | s normou |
|---|---|---|
| `is_vulgar` | **0,98** | **0,13** |
| rozhodnutí o moderaci | `flag_for_review` | **`allow`** |

Vstupní text se nezměnil ani o písmeno. → [findings/01](findings/01-criteria-ablation.cs.md)

**Ablace ukazuje, která část nese účinek:**

| varianta | posun |
|---|---|
| lepší `instructions`, criteria beze změny | −0,04 |
| vágní pokyn („buď benevolentní") | −0,12 |
| **konkrétní výčet výrazů** | **−0,82** |
| plná norma (výčet + kulturní vysvětlení) | −0,85 |

Konkrétní výčty modelem hnou. Postoje ne. A definovat, co **projde**, je zhruba
**3,5× účinnější** než rozšiřovat, co neprojde (−0,70 vs. −0,20).

### 2. Model má bias, a je měřitelný

Směrování „odpovědět z tréninku, nebo hledat na webu?":

| dotaz | naivní klasifikátor |
|---|---|
| „Kdo je **současný** papež?" | **0,43** ✗ pod prahem |
| „Kdo byl papežem za druhé světové?" | 0,08 ✓ |
| „Kdo je **současný** prezident USA?" | **0,43** ✗ |
| „Kdo vyhrál volby 2020?" | 0,09 ✓ |

Model trefí každou historickou otázku a žádnou současnou — přestože slovo „současný"
je přímo v zadání. **Nerozlišuje mezi „vím to" a „věděl jsem to v době trénování."**

Naivní zadání: 66,7 %. Dva odstavce v `criteria`: 100 %. → [findings/02](findings/02-model-bias.cs.md)

### 3. Typ otázky rozhoduje víc než formulace

Tentýž příběh o umírajícím psovi, položený dvěma způsoby:

| | hodnota | provozní rozhodnutí |
|---|---|---|
| **Noul** „je to vhodné?" | 0,690 | **publikovat** |
| **Score** „jak moc vhodné?" | druhá nejnižší úroveň | **označit, potřebuje dospělého** |

Noul vrací *pravděpodobnost, že odpověď zní ano*. Score vrací *polohu na stupnici*.
Různé veličiny — nelze je od sebe odečítat, a volba té špatné obrátí výsledek.
→ [findings/03](findings/03-question-type.cs.md)

### 4. Čísla napsaná do criteria nedělají nic

Ukotvit Noul větami „0,55–0,70 znamená X, 0,15–0,30 znamená Y" **nefunguje**. Nechali
jsme popisy slovo od slova stejné a měnili jen čísla, včetně úplně obrácené škály:

| sada čísel | naměřeno |
|---|---|
| původní | 0,759 |
| posunutá dolů | 0,778 |
| **obrácená** | **0,804** |

Rozpětí: 0,045. **Všechnu práci odvedou popisy, čísla model ignoruje.**
Když potřebujete stupnici, použijte Score — od toho tam je.

---

## Kolik to stojí

Naměřeno, ne převzato z dokumentace:

| | |
|---|---|
| Cena | $0,042 za 1M vstupních tokenů, **výstup zdarma** |
| Jedna klasifikace (~500 tokenů) | **$0,00002** |
| Celá ablační studie | **~$0,004** |
| Všech 1 180 volání v tomhle repu | **~$0,05** |
| Latence (z ČR) | medián **1,1 s**, p95 1,8 s |
| Paralelní otázky | **20 otázek ≈ 1 otázka** (0,73 s) |

> ⚠️ **K latenci:** měřeno z domácí linky v České republice. Americký benchmark uvádí
> p50 378 ms; rozdíl ~0,7 s je síťový round-trip. TypeSafe nemá EU region.
> **Tahle čísla měří vzdálenost do Virginie, ne model.** Pusťte si skripty sami
> a dostanete svoje.

---

## Jak si to pustit

```bash
git clone https://github.com/RastislavDujavaPiccard/jev-classification-research
cd jev-classification-research
pip install -r requirements.txt
cp .env.example .env     # doplňte klíč z console.typesafe.ai
python experiments/01_primitives.py
```

Každý pokus běží bez argumentů. Syrový JSON z každého běhu je v `results/`, takže
libovolné číslo z `findings/` se dá dohledat až k volání, které ho vyrobilo.

---

## Metodika

- **5–10 běhů na variantu**, mediány místo průměrů
- **Prokládané spouštění** — varianty se střídají, aby zpomalení sítě nepadlo na jednu skupinu
- **Práh šumu 0,05**, naměřený: model kolísá o ±0,01–0,03 mezi identickými běhy
- **Posun se počítá jako prokázaný**, jen když zároveň překročí rozhodovací hranici *a* překoná šum

Podrobnosti v [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Poctivá omezení

- **Malé vzorky.** 5–15 položek na doménu. Ukazuje to mechanismy, ne přesnost.
- **Jeden hodnotitel.** Očekávané odpovědi jsou můj úsudek, ne ověřená pravda.
- **Jedna verze modelu.** `jev-1.13.0`, šest dní po vydání. Další verze budou jiné.
- **Latence je zeměpis.** Viz výše.
- **Existuje práce s opačným závěrem.** [leepokai/llm-prompt-techniques-on-jev](https://github.com/leepokai/llm-prompt-techniques-on-jev)
  zjistil, že few-shot příklady jsou na akademických benchmarcích *neutrální až škodlivé*.
  Není to rozpor — viz níže.

### Proč mají pravdu oba

leepokai testoval úlohy s **objektivně správnou odpovědí** (LegalBench, MMLU-Pro).
Tam příklady nepřidávají nic, co model už nemá, a jen ředí signál.

Tyhle pokusy testují úlohy, kde **správná odpověď závisí na normě** — co se počítá jako
vulgární, co rodič dovolí, co vyžaduje vaše jurisdikce. Tam příklady a definice nesou
informaci, kterou model mít nemůže.

Vysvětluje to jejich vlastní rozlišení: techniky, které *nesou informaci*, fungují;
techniky, které jen *přeformulují*, ne. Kulturní norma je informace. „Buď benevolentnější"
je přeformulování.

---

## Nejostřejší výsledek: dvě rodiny, opačné verdikty

Dvě běžné rodiny se šestiletými dětmi. Dcera **rodiny A** má skutečný strach z pavouků —
po pohádce s pavoukem neusne. Syn **rodiny B** miluje zvířata, ale jeho rodiče teď
nezvládnou příběhy, kde je někdo vyloučený z kolektivu; přesně tohle řeší ve škole.

Dvě laskavé pohádky: pavoučice si staví novou pavučinu, a zajíček, kterého nevezmou
do hry a pak vezmou. Žádné násilí, žádná smrt, obě končí dobře.

| příběh | bez profilu | Rodina A | Rodina B |
|---|---|---|---|
| **Pavoučice staví pavučinu** | **0,912** → pustit | **0,006** → NEPOUŠTĚT | **0,721** → pustit |
| **Zajíčka nevzali do hry** | **0,759** → pustit | **0,889** → pustit | **0,035** → NEPOUŠTĚT |

Dokonalý kříž. **Bez profilu projde obojí. S profily dostane každá rodina opačné
rozhodnutí na tomtéž obsahu** — a model si byl v obou případech prakticky jistý
(confidence 1,000 a 0,990).

Není to filtrování podle klíčových slov. Filtr na slovo „pavouk" by udělal totéž pro
rodinu A, ale zablokoval by i dokument o včelách, který by milovali.

→ [findings](findings/09-personalised-scales.cs.md)

---

## Dvě zjištění, která stojí za zvláštní zmínku

### Čeština si na této úloze vede stejně jako angličtina

Dokumentace varuje, že primárním trénovacím jazykem je angličtina. Měřeno na 15
dvojjazyčných párech, kde každá položka existuje v obou jazycích se shodným obsahem:

| | přesnost | průměrný rozdíl |
|---|---|---|
| Anglický text | **15/15** | — |
| Český text | **15/15** | **0,036** |
| Shoda rozhodnutí | **15/15** | — |

Osm z patnácti vrátilo **identickou hodnotu** v obou jazycích — včetně sarkasmu,
podmiňovacího způsobu a dvou českých idiomů bez přímého anglického ekvivalentu.

**Práh vyladěný na anglických datech se přenese.** Jediná výjimka — negace — leží
v češtině blíž hranici (0,464 vs. 0,022); viz [findings](findings/05-czech-language.cs.md).

### Kulturní norma musí působit oběma směry

Norma, která posune všechno dolů, není kalibrace, ale vypnutá moderace. Měřeno na
9 mírných textech, které mají projít, a 3 hraničních, které nesmí:

| | průměrný posun | výsledek |
|---|---|---|
| Mírné české hovorové výrazy | **−0,456** | posunuto dolů ✓ |
| Osobní urážky a výhrůžka | **+0,329** | **hranice udržena 3/3** ✓ |

Nejzřetelnější případ: *„Přijdu si pro ně osobně a nebude se vám to líbit"* — výhrůžka
bez jediného vulgarismu. Bez normy dostala **0,040** (správně: žádná sprostá slova).
S normou **0,420** a `block`, protože norma pojmenovává osu:

> *„Záleží na tom, jestli je napadán ČLOVĚK, ne jestli se v textu objeví hrubé slovo."*

Tři rozhodnutí ze dvanácti se změnila a **všechna tři odešla z fronty na moderátora** —
jedno ven, dvě zablokovat. Norma zmenšila frontu z obou stran.

---

## Probíhá

- **Personalizované klasifikátory** — stejný obsah, různé uživatelské profily, opačná rozhodnutí. Dvoukroková kaskáda: binární brána, pak stupnice rozepsaná uživatelovými slovy. První výsledky jsou výrazné; zveřejním, až bude vzorek větší.
- **Srovnání s Gemini 2.5 Flash s context cachingem** — otázka, kterou nikdo pořádně nezměřil

---

## Licence

Kód MIT · Texty a data CC BY 4.0

Bez vazby na TypeSafe AI. Nezávislý výzkum prompt inženýra, který chtěl vědět, co ty
klasifikátory vlastně dělají.

**Našli jste chybu?** Založte issue. Čísla, která obstojí v kritice, mají větší cenu
než čísla, která žádnou nedostanou.
