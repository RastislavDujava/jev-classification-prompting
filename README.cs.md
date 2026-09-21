# Jev prompt engineering

**Klasifikátor někde vede hranici. Když ji nenapíšete vy, napsal ji někdo jiný.**

[Jev od TypeSafe](https://docs.typesafe.ai/) vyšel 15. 9. 2026. Negeneruje text —
pošlete mu obsah a typovanou otázku, on vrátí rozhodnutí s pravděpodobnostmi.
Kolem sekundy, dvě setiny centu za volání.

Prodává se to tak, že je to deterministické tam, kde jsou LLM mlhavá: typovaný výstup,
žádné vymyšlené kategorie, kalibrované pravděpodobnosti. Všechno pravda — a všechno
je to o **tvaru** odpovědi. Ten úsudek uvnitř je naučený, což znamená, že nese bias,
což znamená, že by se měl dát promptovat.

Tenhle repozitář je první pokus zjistit jak. Devět věcí, které jsem nejdřív udělal
špatně a pak si je změřil — ~1 300 volání API, každý skript spustitelný jedním
příkazem, každý syrový výsledek commitnutý.

Je to raná práce na modelu starém týden, od jednoho člověka, na malých vzorcích.
Berte to jako výchozí bod a metodu, kterou si můžete přepustit na vlastních datech,
**ne jako hotový fakt.** Kde si nejsem jistý, říkám to, a jednou už jsem se musel opravit.

> **Stav:** úvodní testování, pokračuje.
> Čísla platí pro `jev-1.13.0` a budou se s dalšími verzemi měnit.

---

## To jedno číslo

Napříč šesti doménami, 41 párových položek:

| | naivní otázka | pořádně napsaná kritéria |
|---|---|---|
| **Přesnost** | **70 %** (57/82) | **96 %** (79/82) |

Ten rozdíl není tím, že by model zmoudřel. Je to rozdíl mezi přijetím výchozího
nastavení a vyslovením toho, co doopravdy myslíte.

**Všechno níže je pokus přijít na to, jak to vyslovit.**

---

# Co jsem zatím zjistil

## 1 — Páka je podle všeho v kritériích, ne v otázce

**Proč na tom záleží:** většina lidí věnuje energii formulaci otázky. Změřeno je to
ta **nejméně** účinná věc, kterou můžete udělat.

Stejný text, stejná otázka, mění se jen definice toho, co je vulgární:

| | bez kulturní normy | s normou |
|---|---|---|
| `is_vulgar` | **0,98** | **0,13** |
| rozhodnutí o moderaci | `flag_for_review` | **`allow`** |

Ve vstupním textu se nezměnilo ani písmeno. Ablace ukazuje, která část definice nese účinek:

| co se změnilo | posun |
|---|---|
| lepší `instructions`, `criteria` beze změny | **−0,04** |
| vágní pokyn: *„buď benevolentní k české mluvě"* | −0,12 |
| **konkrétní výčet těch výrazů** | **−0,82** |
| výčet plus kulturní vysvětlení | −0,85 |

**Odnést si:** konkrétní výčty modelem hnou, postoje ne, a ten promyšlený odstavec,
na který jste byli nejvíc pyšní, má nejspíš cenu 0,03. Přepsání otázky má cenu 0,04 — šum.

📄 [Plný zápis](findings/01-criteria-ablation.cs.md) ·
▶ `python experiments/10_cultural_norm.py`

---

## 2 — Definujte, co má projít, ne jen co neprojde

**Proč na tom záleží:** je to zhruba 3,5× účinnější a je to opak toho, jak se píše
většina pravidel pro obsah.

Ze stejné ablace, definovaná vždy jen jedna větev kritérií:

| | posun |
|---|---|
| jen větev `true` — rozšiřování zakázaného | −0,20 |
| **jen větev `false` — pojmenování výjimek** | **−0,70** |

Model už má pevné představy o tom, co je špatně. Co potřebuje od vás, je **kde to končí**.

Ostřejší verze téhož je v personalizaci: žebřík, jehož nejvyšší příčka říká *„smutné
nebo těžké momenty jsou v pořádku, dokud platí tahle podmínka"*, se chová úplně jinak
než ten, který jen vyjmenovává zákazy. Bez té věty se celá škála posune do přísnosti
a začne filtrovat všechno mírně smutné.

**Odnést si:** napište to dovolení, ne jen zákaz.

📄 [Plný zápis](findings/01-criteria-ablation.cs.md)

---

## 3 — Typ otázky rozhoduje, kam se uživatel vejde

**Proč na tom záleží:** zvolit špatný typ není chyba ve formulaci. Je to volba tvaru,
ve kterém není místo pro člověka, pro kterého to stavíte.

Zeptejte se *„je tenhle příběh vhodný pro dítě od 5 do 7?"* — to je **Noul**, otázka
ano/ne — a dostanete jedno číslo s cizím prahem zabudovaným uvnitř:

```
pohádka o pavoučici   0,910 → zobrazit
pohádka o zajíčkovi   0,892 → zobrazit
```

Obojí správně. Obojí nepoužitelné, když stavíte pro konkrétní dítě.

**Score** bere tutéž otázku plus *kritéria*: úrovně od nejhorší po nejlepší, každá
jedna věta, kterou píšete vy. Model rozdělí 100 % pravděpodobnosti mezi ně.
**Čtyři nebo pět míst, kde můžete říct, co myslíte — místo jednoho.**

Tentýž příběh položený oběma způsoby vede k opačným provozním rozhodnutím — umírající
pes čte Noul jako 0,690 *(publikovat)* a Score ho zařadí na druhou nejnižší
z šesti úrovní *(označit, potřebuje dospělého)*.

> ⚠️ Hodnoty Noulu a polohy na Score jsou **různé veličiny** a nesmí se od sebe
> odečítat. Noul vrací pravděpodobnost, že odpověď zní ano; Score vrací polohu na
> stupnici. V rané verzi tohohle výzkumu jsem to spletl — oprava je v zápisu.

**K jemnosti:** tři úrovně popletly pořadí testovacích příběhů a měly nejnižší
confidence. Od čtyř to bylo stabilní. Používejte aspoň čtyři.

📄 [Plný zápis](findings/03-question-type.cs.md) ·
▶ `python experiments/08_noul_vs_score.py`

---

## 4 — Hyperpersonalizace žije v příčkách

**Proč na tom záleží:** tohle je ta lekce, která mění, co se dá postavit.

Dvě běžné rodiny se šestiletými dětmi. Jedna holčička má skutečný strach z pavouků —
po pohádce s pavoukem neusne. Jeden kluk miluje zvířata, ale jeho rodiče nezvládnou
příběhy, kde je někdo vyloučený z kolektivu; přesně tohle řeší ve škole.

Dvě laskavé pohádky, žádné násilí, obě končí dobře: pavoučice si staví novou pavučinu;
zajíčka nevezmou do hry a pak vezmou.

Napsané obecně **obě pohádky projdou pro obě děti**. Pak jeden žebřík na dítě, stejná
otázka, stejný kód, liší se jen kritéria:

```
DÍTĚ 1 (bojí se pavouků) — pravděpodobnost přes pět příček
                     [0]    [1]    [2]    [3]    [4]
pavoučice           98 %    2 %    0 %    0 %    0 %   →  NEPOUŠTĚT
zajíček              0 %    0 %    5 %   34 %   61 %   →  pustit

DÍTĚ 2 (nechávají ho stranou ve škole)
                     [0]    [1]    [2]    [3]    [4]
pavoučice            0 %   27 %    1 %   25 %   47 %   →  pustit
zajíček             91 %    6 %    0 %    2 %    1 %   →  NEPOUŠTĚT
```

Dokonalý kříž. **Pohádka, která je pro jedno dítě absolutní ne, je pro druhé v pohodě —
a obecný žebřík mávl obě dál.**

Dvě formulace v žebříku dítěte 1 dělají skutečnou práci a obě se dají přenést:

- **„ať je napsaná jakkoli laskavě"** — bez toho se vlídně napsaný pavouk vůbec
  neprojeví jako problém, protože se opravdu nic zlého neděje. Řekněte, že problém
  je ta *přítomnost*, ne zpracování.
- **„smutné nebo těžké momenty jsou v pořádku"** — viz část 2.

**Není to filtrování podle klíčových slov.** Filtr na slovo „pavouk" by udělal totéž
pro dítě 1 a zablokoval by i dokument o včelách, který by milovali.

📄 [Plný zápis](findings/09-personalised-scales.cs.md) ·
▶ `python experiments/11_personalised_scales.py`

---

## 5 — Model neví, co neví

**Proč na tom záleží:** jestli routujete mezi „odpověz z paměti" a „hledej na webu",
tohle je živá chyba ve vašem produktu právě teď.

Patnáct dotazů, spárovaných tak, aby skoro totožná formulace měla opačnou správnou odpověď:

| dotaz | naivní klasifikátor | |
|---|---|---|
| „Kdo byl papežem za druhé světové?" | 0,077 | ✓ |
| „Kdo je **současný** papež?" | **0,430** | ✗ pod prahem |
| „Kdo vyhrál volby 2020?" | 0,087 | ✓ |
| „Kdo je **současný** prezident USA?" | **0,430** | ✗ |

**Každou historickou otázku správně. Každou současnou špatně** — i se slovem „současný"
přímo v dotazu. Model má uloženou odpověď a vnímá ji jako znalost, ne jako snímek v čase.

A není to plošné: *„nejnovější verze Reactu"* vyšla správně i naivně (0,917).
**Ten bias je doménově specifický** — naučil se, že čísla verzí zastarávají, ne že
lidé odcházejí z funkcí.

Oprava byly dva odstavce v `criteria` a nosná věta zní:

> *„I když má model uloženou odpověď a je si jistý, ta odpověď už může být zastaralá."*

**66,7 % → 100 %.** Šest ukázkových příkladů přidaných navrch nezměnilo nic — už to
bylo na stropě, čistý náklad.

📄 [Plný zápis](findings/02-model-bias.cs.md) ·
▶ `python experiments/05_tool_routing.py`

---

## 6 — Čísla napsaná do kritérií nedělala nic

**Proč na tom záleží:** je to ta zjevná věc, kterou zkusíte, a je to slepá ulička.
Ušetřete si odpoledne.

Ukotvení výslovnými pásmy — *„0,55–0,70 znamená skutečné nebezpečí, vyřešené"* —
nefunguje. Popisy slovo od slova stejné, mění se jen čísla:

| sada čísel pro cílové pásmo | naměřeno |
|---|---|
| původní (0,55–0,70) | 0,759 |
| posunutá dolů (0,25–0,35) | 0,778 |
| stlačená nahoru (0,85–0,90) | 0,772 |
| **úplně obrácená** (vlídné = 0, drastické = 1) | **0,804** |

Rozpětí přes všechny čtyři: **0,045**. Obrácená škála měla dát pravý opak původní.
Dala o chlup vyšší číslo.

**Popisy dělají všechnu práci. Čísla jsou dekorace.** Když potřebujete stupnici,
použijte Score — ten ji má zabudovanou.

📄 [Plný zápis](findings/04-scale-anchors.cs.md) ·
▶ `python experiments/07_scale_anchors.py`

---

## 7 — Příklady buď nesou informaci, nebo nenesou nic

**Proč na tom záleží:** „přidej few-shot příklady" je reflex. Někdy je to odpověď,
někdy jen tokeny.

Dvě řady stejné délky — jedna few-shot příkladů, druhá sémanticky neutrální výplně:

| délka | s příklady | neutrální výplň |
|---|---|---|
| holá otázka | 0,925 | — |
| ~500 tokenů | **0,353** | 0,898 |
| ~5 000 tokenů | 0,304 | 0,885 |

Neutrální řada se pohnula celkem o 0,013. **Ten posun je obsahem, ne délkou.**

Všimněte si ale klesajícího užitku: prvních 5 příkladů dalo −0,572, dalších 45 přidalo
−0,049. Zhruba **12:1 ve prospěch prvních pár**.

A v páté části příklady nepřidaly vůbec nic — kritéria už byla na 100 %.

**Odnést si:** příklady fungují, když nesou informaci, kterou model nemá, typicky
hranici, kterou si nemůže odvodit. Na úlohách, které už umí, jsou nákladem. Sedí to na
zjištění [leepokaie](https://github.com/leepokai/llm-prompt-techniques-on-jev), že
few-shot je na akademických benchmarcích neutrální až škodlivý — viz *Související práce* níže.

**K latenci:** plochá do ~2 000 tokenů, **+0,28 s při ~5 000**, shodně v obou řadách.
15,8× víc tokenů stálo jen 1,27× delší odezvu, protože zpracování vstupu je paralelní.

📄 [Plný zápis](findings/08-length-vs-content.cs.md) ·
▶ `python experiments/04_length_vs_content.py`

---

## 8 — Norma musí působit oběma směry

**Proč na tom záleží:** norma, která posune všechno dolů, není kalibrace, ale vypnutá
moderace. Tohle je test, který vám řekne, kterou z nich jste napsali.

Devět mírných textů, které mají projít, tři hraniční, které nesmí:

| | průměrný posun | výsledek |
|---|---|---|
| Mírné české hovorové výrazy | **−0,456** | posunuto dolů ✓ |
| Osobní urážky a výhrůžka | **+0,329** | **hranice udržena 3/3** ✓ |

Nejzřetelnější případ: *„Přijdu si pro ně osobně a nebude se vám to líbit"* — výhrůžka
**bez jediného vulgarismu**. Bez normy dostala 0,040, správně: žádná sprostá slova.
S normou 0,420 a `block`, protože norma pojmenovává osu:

> *„Záleží na tom, jestli je napadán ČLOVĚK, ne jestli se v textu objeví hrubé slovo."*

Model tu osu přijal. Přestal počítat slova a začal se ptát, kdo je terčem.

**Tři rozhodnutí ze dvanácti se změnila — a všechna tři odešla *z* fronty na
moderátora.** Jedno ven, dvě zablokovat. Norma zmenšila frontu z obou stran.

**Pozor na přesah:** norma mluví výhradně o češtině, a přesto anglický testovací text
klesl z 0,916 na 0,176. Kritéria posouvají celkový práh citlivosti, ne filtr na
vyjmenovaná slova. Když chcete úzký efekt, ohraničte ho výslovně.

📄 [Plný zápis](findings/06-cultural-norm.cs.md) ·
▶ `python experiments/10_cultural_norm.py`

---

## 9 — Čeština si tady vedla stejně jako angličtina

**Proč na tom záleží:** dokumentace varuje před neanglickým obsahem. Na téhle úloze se
to v číslech neprojevilo — což se hodí vědět, když stavíte pro neanglický trh.

15 dvojjazyčných párů, každá položka existuje v obou jazycích se shodným obsahem:

| | přesnost | průměrný absolutní rozdíl |
|---|---|---|
| Anglický text | **15/15** | — |
| Český text | **15/15** | **0,036** |
| Shoda rozhodnutí | **15/15** | — |

**Osm z patnácti vrátilo v obou jazycích identickou hodnotu**, včetně sarkasmu,
podmiňovacího způsobu, hlášení ve třetí osobě a dvou českých idiomů bez přímého
anglického ekvivalentu.

**Prakticky:** práh vyladěný na anglických datech se přenese.

**Jediná výjimka — negace.** *„Zásilka nedorazila pozdě a nic nechybělo"* dostalo
v angličtině 0,022 a v češtině **0,464**. Obojí formálně správně, ale česká verze leží
blízko hranici. Čeština vyžaduje dvojitý zápor a model možná sčítá negativní signály —
*hypotéza z jednoho příkladu, ne prokázaný mechanismus.* Negativní konstrukce si
otestujte zvlášť.

Přeložit otázku do češtiny nepomohlo (15/15 tak i tak).

📄 [Plný zápis](findings/05-czech-language.cs.md) ·
▶ `python experiments/09_czech_vs_english.py`

---

## Limity a cena

| | dokumentováno | naměřeno |
|---|---|---|
| `state` + nejdelší otázka | 32k tokenů | ✅ 32 796 OK, víc → `max_tokens_exceeded` |
| Options u Choice | max 255 | ✅ 255 OK, 256 → chyba |
| Úrovně u Score | 2–10 | ✅ 10 OK, 11 → chyba |
| **Délka `criteria`** | **žádný samostatný limit** | ✅ 191 750 znaků prošlo |

Tokenový rozpočet je **sdílený** mezi `state` a otázkami — ne 32k na každé.

**Cena:** $0,042 za 1M vstupních tokenů, výstup zdarma. Jedna klasifikace ≈ $0,00002.
Celá sada v tomhle repu ≈ $0,05.

**Délku ale platíte při každém volání.** 30 000 tokenů kritérií ≈ $0,13 na 1 000 volání;
při milionu volání měsíčně je to $1 260 za normu, která se nemění. Ablace z první části existuje proto, aby vám řekla, co můžete vyhodit.

**Latence z ČR:** medián **1,1 s**, p95 1,8 s. Americký benchmark uvádí p50 378 ms —
rozdíl je síťový round-trip, TypeSafe nemá evropský region.
**Tahle čísla měří vzdálenost do Virginie, ne model.**

📄 [Plný zápis](findings/07-limits-and-cost.cs.md)

---

## Jak si to pustit

```bash
git clone https://github.com/RastislavDujava/jev-classification-prompting
cd jev-classification-prompting
pip install -r requirements.txt
cp .env.example .env     # váš klíč z console.typesafe.ai
python experiments/01_primitives.py
```

Každý pokus běží bez argumentů. Syrový JSON z každého běhu je v `results/`, takže
libovolné číslo výše se dá dohledat až k volání, které ho vyrobilo.

**Metoda:** 5–10 běhů na variantu · mediány místo průměrů · varianty prokládané, aby
zpomalení sítě nepadlo na jednu skupinu · **práh šumu 0,05**, naměřený — model kolísá
o ±0,01–0,03 mezi identickými běhy · posun se počítá, jen když překročí rozhodovací
hranici *a* překoná šum. Podrobnosti v [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Poctivá omezení

- **Malé vzorky.** 5–15 položek na doménu. Ukazuje to mechanismy, ne přesnost.
- **Jeden hodnotitel.** Očekávané odpovědi jsou můj úsudek, ne ověřená pravda.
- **Vstupy i kritéria jsem psal já** — reálné riziko, že jsem nevědomky psal testy,
  které se hodí k hypotéze. Kontroly to zmírňují, neodstraňují.
- **Žádná oddělená testovací sada.** Kritéria se psala a měřila na stejných položkách.
- **Jedna verze modelu**, šest dní po vydání.
- **Jednou jsem to už spletl** — porovnával jsem hodnoty Noulu s polohami na Score
  jako čísla. Oprava je vidět v lekci 3, ne potichu vygumovaná.

### Související práce a proč si odporuje

[leepokai/llm-prompt-techniques-on-jev](https://github.com/leepokai/llm-prompt-techniques-on-jev)
otestoval 15+ promptovacích technik na LegalBench, BIG-Bench Hard, MMLU-Pro a CLERC
a zjistil, že **few-shot příklady jsou neutrální až škodlivé**.

Není to rozpor. Testoval úlohy s **objektivně správnou odpovědí**, kde příklady
nepřidávají nic, co model nemá. Tyhle pokusy testují úlohy, kde **správná odpověď
závisí na normě** — co se počítá jako vulgární, co rodič dovolí, co vyžaduje vaše
jurisdikce. Tam příklady a definice nesou informaci, kterou model mít nemůže.

Vysvětluje to jejich vlastní rozlišení: techniky, které *nesou informaci*, fungují;
techniky, které jen *přeformulují*, ne. Kulturní norma je informace. „Buď benevolentnější"
je přeformulování.

---

## Probíhá

- **Větší kulturní vzorek** — současná sada je moc malá na jakékoli tvrzení
- **Srovnání s Gemini 2.5 Flash s context cachingem** — otázka, kterou nikdo
  pořádně nezměřil

---

## Licence

Kód MIT · Texty a data CC BY 4.0

Bez vazby na TypeSafe AI. Nezávislý výzkum prompt inženýra, který chtěl vědět, co ty
klasifikátory vlastně dělají.

**Našli jste chybu?** Založte issue. Čísla, která obstojí v kritice, mají větší cenu
než čísla, která nikdo nekontroluje.
