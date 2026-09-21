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

**Úloha:** moderace obsahu v české komunitní aplikaci. Dostanete příspěvek, rozhodnete,
jestli obsahuje urážlivý jazyk. Binární, takže Noul — to číslo je P(tohle je vulgární).

**Vstup**, po celou dobu stejný:

> *„Ty vole, ta appka zase spadla. Už je to potřetí dneska, do prdele."*

Mírné české hovorové výrazy — hospodský rejstřík, pro českého mluvčího neurážlivé.
Jejich doslovné anglické ekvivalenty jsou ale podstatně hrubší, a model se svou normu
naučil z angličtiny.

**Naivní kritéria:**

```
instructions: „Obsahuje tenhle text vulgární nebo sprostý jazyk?"
criteria:
  true  → „Text obsahuje nadávky, vulgarismy nebo hrubý jazyk"
  false → „Text je bez vulgárního jazyka"
```

**S kulturní normou zapsanou do větve `false`** — pojmenuje konkrétní výrazy a řekne,
že jsou v češtině běžný rejstřík:

| | naivní kritéria | s normou |
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

**Co se pokazí bez toho:** příspěvek se označí. Lidský moderátor ho musí přečíst,
rozhodnout, že byl v pořádku, a pustit ho — kvůli větě, nad kterou český mluvčí ani
nemrkne. Udělejte to ve velkém a fronta na kontrolu se vám zaplní falešnými poplachy,
za kterými čekají skutečné případy.

**Kde promptovat:** větev `false` v `criteria`.
**Jak:** pojmenovat ty konkrétní výrazy. Ne „buď benevolentní k hovorové mluvě", ale
ten výčet — *„ty vole", „do prdele", „blbost", „kravina", „sakra"* — a rovnou napsat,
že je Češi za urážlivé nepovažují.
**Proč tam:** model nemá jak znát rejstřík vaší komunity. Otázka to neunese; ta jen
říká, co se má rozhodnout. Kritéria říkají, co ty odpovědi znamenají — a „urážlivé"
znamená v Praze něco jiného než v trénovacích datech.

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

**Co se pokazí bez toho:** píšete čím dál delší seznam zákazů, klasifikátor je
postupně přísnější a nakonec filtruje věci, o které ho nikdo neprosil. To dovolení
je to, co drží hranici na místě.

**Kde promptovat:** větev `false`, nebo nejvyšší příčka žebříku u Score.
**Jak:** zakončit to dovolení výslovným „i když" — *„smutné nebo těžké momenty jsou
v pořádku, dokud platí tahle podmínka"*. Jedna věta.
**Proč tam:** model přichází se silnými představami o tom, co je špatně. Přidávat
k nim je zbytečné. Co si odvodit nemůže, je kde končí vaše tolerance — a ta existuje,
jen když ji napíšete.

📄 [Plný zápis](findings/01-criteria-ablation.cs.md)

---

## 3 — Typ otázky rozhoduje, kam se uživatel vejde

**Proč na tom záleží:** zvolit špatný typ není chyba ve formulaci. Je to volba tvaru,
ve kterém není místo pro člověka, pro kterého to stavíte.

**Úloha:** appka s pohádkami z části 4 — rozhodnout, jestli příběh položíte před
šestileté dítě.

Položte to jako **Noul**, otázku ano/ne, a dostanete P(odpověď zní ano):

```
instructions: „Je tenhle příběh vhodný pro dítě od 5 do 7 let?"

pohádka o pavoučici   0,910 → zobrazit
pohádka o zajíčkovi   0,892 → zobrazit
```

Obojí správně — a obojí nepoužitelné, když stavíte pro konkrétní dítě. To číslo není
fakt o tom příběhu; je to názor modelu na šestileté děti obecně, stlačený do jedné
hodnoty s cizím prahem už zabudovaným uvnitř.

**Score** bere tutéž otázku plus *kritéria*: úrovně od nejhorší po nejlepší, každá
jedna věta, kterou píšete vy. Model rozdělí 100 % pravděpodobnosti mezi ně.
**Čtyři nebo pět míst, kde můžete říct, co myslíte — místo jednoho.**

Tentýž příběh položený oběma způsoby vede k opačným provozním rozhodnutím — umírající
pes čte Noul jako 0,690 *(publikovat)* a Score ho zařadí na druhou nejnižší
z šesti úrovní *(označit, potřebuje dospělého)*.

> ⚠️ Hodnoty Noulu a polohy na Score jsou **různé veličiny** a nesmí se od sebe
> odečítat. Noul vrací pravděpodobnost, že odpověď zní ano; Score vrací polohu na
> stupnici. V rané verzi tohohle výzkumu jsem to spletl — oprava je v zápisu.

**Co se pokazí bez toho:** dostanete jedno číslo, které vypadá rozhodně a není.
Každý uživatel vašeho produktu zdědí stejný práh — a to jediné místo, kam jste mohli
dát jeho preferenci, tedy definice odpovědi, má prostor přesně na jednu větu.

**Kde promptovat:** pole `criteria` u Score, jedna věta na příčku.
**Jak:** od nejhorší po nejlepší, každá příčka konkrétní situace, ne stupeň intenzity.
*„Skutečné nebezpečí nebo zranění s trvalým následkem, do konce vyřešené"* funguje;
*„středně závažné"* ne — model nemá co s čím porovnat.
**Proč tam:** Noul vám dá jednu definici. Score čtyři nebo pět — a preference má
stupně, takže potřebuje místo, které stupně má.

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

**Úloha:** dostanete příběh, rozhodnete, jestli ho ukázat tomuhle konkrétnímu dítěti.
Score, protože „vhodné" má stupně — otázka zůstává pevně *„Jak moc je tenhle příběh
vhodný pro dítě od 5 do 7 let v téhle rodině?"* a mění se jen kritéria.

**Žebřík dítěte 1**, pět příček od nejhorší:

```
[0] v příběhu vystupuje pavouk, hmyz nebo podobný tvor jako postava, je
    popsaný do detailu nebo ukázaný zblízka. Naše dcera má z těchhle zvířat
    silný strach a po takové pohádce neusne, AŤ JE NAPSANÁ JAKKOLI LASKAVĚ
[1] pavouci nebo hmyz zmínění mimochodem
[2] nic z toho, ale příběh je strašidelný jinak
[3] nic z toho a případný problém je malý a rychle vyřešený
[4] vůbec nic z toho, celé vlídné a klidné. SMUTNÉ NEBO TĚŽKÉ MOMENTY JSOU
    V POŘÁDKU, dokud platí tahle podmínka
```

Žebřík dítěte 2 je zrcadlový: nejnižší příčka je *„postava je vyloučená z kolektivu,
nevzali ji do hry, smějí se jí nebo jí dávají najevo, že ji nechtějí — náš syn si
tímhle prochází ve škole"*; nejvyšší říká výslovně, že *„zvířata jakéhokoli druhu,
včetně hmyzu a pavouků, jsou pro něj úplně v pořádku."*

Napsané obecně — *„[0] nevhodné: násilí, smrt, strašidelný obsah … [3] plně vhodné:
klidné, laskavé, uklidňující"* — **obě pohádky projdou pro obě děti.** S vlastním
žebříkem každého dítěte rozdělí model 100 % pravděpodobnosti přes pět příček takhle:

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

**Co se pokazí bez toho:** obecný žebřík ukáže obě pohádky oběma dětem. Jedno dítě
neusne; druhé si čte o vyloučení z kolektivu zrovna ten týden, kdy se mu to děje.
Ani jeden rodič se to nedozví, protože pro systém obě pohádky prošly.

**Kde promptovat:** v příčkách — a jen tam. Otázka zůstává napříč uživateli stejná,
stejně tak kód i prahy.
**Jak:** vyzpovídejte toho člověka. „Kterou pohádku byste mu nečetli a proč?"
Jeho odpověď, skoro doslova, se stane nejnižší příčkou. Co by pořád rád četl,
se stane nejvyšší.
**Proč tam:** je to jediná část requestu, která se může lišit uživatel od uživatele,
aniž by se měnilo cokoli jiného. Právě to z toho dělá personalizaci, a ne větvení
ve vašem kódu.

**Není to filtrování podle klíčových slov.** Filtr na slovo „pavouk" by udělal totéž
pro dítě 1 a zablokoval by i dokument o včelách, který by milovali.

📄 [Plný zápis](findings/09-personalised-scales.cs.md) ·
▶ `python experiments/11_personalised_scales.py`

---

## 5 — Model neví, co neví

**Proč na tom záleží:** když stavíte agenta, jedno z prvních rozhodnutí je, jestli
zavolat nástroj na vyhledávání, nebo nechat LLM odpovědět z trénovacích dat. Hledání
stojí čas a peníze; odpověď z paměti je okamžitá a zadarmo. Tak si na to postavíte
klasifikátor — a ten má slepou skvrnu.

**Úloha:** dostanete uživatelský dotaz, rozhodnete *zavolat vyhledávání* nebo
*odpovědět z vlastních znalostí modelu*. Binární, takže Noul, který vrací
pravděpodobnost, že odpověď na otázku zní ano.

**Naivní verze — otázka, kterou napíše každý jako první:**

```
instructions: „Vyžaduje zodpovězení tohoto dotazu vyhledávání na internetu?"

criteria:
  true  → „Dotaz potřebuje k zodpovězení vyhledávání na webu"
  false → „Model může odpovědět z vlastních znalostí"
```

To je kruhem — kritéria přeříkávají otázku místo toho, aby cokoli definovala.
Patnáct dotazů, spárovaných tak, aby skoro totožná formulace měla opačnou správnou
odpověď. **To číslo je P(potřebuje hledat); nad 0,5 znamená poslat na vyhledávání:**

| dotaz | správná odpověď | naměřeno | |
|---|---|---|---|
| „Kdo byl papežem za druhé světové?" | z paměti | 0,077 | ✓ |
| „Kdo je **současný** papež?" | **hledat** | **0,430** | ✗ odpoví ze zastaralé paměti |
| „Kdo vyhrál volby 2020?" | z paměti | 0,087 | ✓ |
| „Kdo je **současný** prezident USA?" | **hledat** | **0,430** | ✗ |
| „Jaké je hlavní město Francie?" | z paměti | 0,030 | ✓ |
| „Kdo je CEO OpenAI?" | **hledat** | **0,350** | ✗ |

**Každý uzavřený fakt správně. Každý živý špatně** — i se slovem „současný" přímo
v dotazu. Model má uloženou odpověď a vnímá ji jako znalost, ne jako snímek s datem.

A není to plošné: *„nejnovější verze Reactu"* vyšla správně i naivně (0,917).
**Ten bias je doménově specifický** — naučil se, že čísla verzí zastarávají, ne že
lidé odcházejí z funkcí.

**Oprava — stejná otázka, přepsaná kritéria:**

```
criteria:
  true  → „Odpověď závisí na informaci, která se mohla od sběru trénovacích
           dat změnit. Patří sem: současní držitelé funkcí (prezidenti, CEO,
           papežové), živá data (počasí, ceny, výsledky), nejnovější verze
           softwaru, aktuální tržní doporučení a současný stav firem nebo
           produktů. I KDYŽ MÁ MODEL ULOŽENOU ODPOVĚĎ A JE SI JISTÝ, TA
           ODPOVĚĎ UŽ MŮŽE BÝT ZASTARALÁ."

  false → „Odpověď je v čase stálá a od trénování se nezměnila. Patří sem:
           uzavřené historické události, fyzikální a matematické konstanty,
           zavedená vědecká vysvětlení, překlad mezi jazyky a programátorské
           postupy stabilní roky."
```

Ta věta velkými písmeny nese celou váhu. Říká modelu, že **jeho vlastní jistota není
důkaz aktuálnosti** — což je přesně ta slepá skvrna, vyslovená nahlas.

```
                              před      po
„Kdo je současný papež?"      0,43  →  0,88   ✓ už hledá
„Papež za druhé světové?"     0,08  →  0,05   ✓ pořád nehledá
„Současný prezident USA?"     0,43  →  0,93   ✓
„Kdo vyhrál 2020?"            0,09  →  0,09   ✓ beze změny
```

**66,7 % → 100 %.** A všimněte si, co se **ne**pohnulo: historické otázky zůstaly, kde
byly. Kritéria z routeru neudělala panikáře, naučila ho rozlišovat.

**Izolační běh** potvrzuje, kde se ta práce odehrála — přepsání `instructions` při
ponechání kruhových kritérií: **38 % → 38 %.** Přepsání jen kritérií: **38 % → 100 %.**

Šest ukázkových příkladů navrch nezměnilo nic — už to bylo na stropě, čistý náklad.

**Co se pokazí bez toho:** třetina dotazů se zodpoví ze zastaralé paměti, sebejistě,
bez hledání a bez upozornění. Uživatel se zeptá, kdo je papež, a váš agent mu to
řekne — přesně podle stavu k trénovacímu cutoffu. Nikdo na to nepřijde, dokud si
někdo nestěžuje.

**Kde promptovat:** v obou větvích `criteria`.
**Jak:** do `true` vyjmenovat kategorie, které se mění — držitelé funkcí, živá data,
čísla verzí, tržní doporučení — a pak přidat tu větu, co nese váhu: *„i když má model
uloženou odpověď a je si jistý, ta odpověď už může být zastaralá."* Do `false`
vyjmenovat, co se opravdu nemění.
**Proč tam:** model nedokáže pozorovat vlastní cutoff. Zevnitř je „vím to" a „věděl
jsem to při trénování" nerozlišitelné. Nepřidáváte fakta — říkáte mu, že jeho jistota
není důkaz.

📄 [Plný zápis](findings/02-model-bias.cs.md) ·
▶ `python experiments/05_tool_routing.py`

---

## 6 — Čísla napsaná do kritérií nedělala nic

**Proč na tom záleží:** je to ta zjevná věc, kterou zkusíte, a je to slepá ulička.
Ušetřete si odpoledne.

**Úloha:** ohodnotit dětský příběh o zajíčkovi, který si poraní nohu a uzdraví se —
skutečné nebezpečí, žádné drastické detaily, do konce vyřešené. Chtěl jsem, aby to
skončilo v konkrétním pásmu, tak jsem modelu zkusil říct, co které pásmo znamená,
uvnitř kritérií:

```
instructions: „Je tenhle zvířecí příběh vhodný pro děti od 5 do 7 let?"
              + „Použij celou škálu. Kalibruj podle těchto kotev:
                 0,95-1,00 — úplně vlídné, nic zlého se nestane
                 0,75-0,90 — mírná obava, která se rychle vyřeší
                 0,55-0,70 — skutečné nebezpečí nebo zranění, vyřešené
                 0,35-0,50 — něco strašidelného mimo scénu, nebo nevyřešené
                 0,15-0,30 — smrt nebo trvalá ztráta na scéně
                 0,00-0,10 — drastické násilí, krev, utrpení"
```

Pak jsem nechal ty popisy **slovo od slova stejné** a měnil jen čísla:

| sada čísel pro cílové pásmo | naměřeno |
|---|---|
| původní (0,55–0,70) | 0,759 |
| posunutá dolů (0,25–0,35) | 0,778 |
| stlačená nahoru (0,85–0,90) | 0,772 |
| **úplně obrácená** (vlídné = 0, drastické = 1) | **0,804** |

Rozpětí přes všechny čtyři: **0,045**. Obrácená škála měla dát pravý opak původní.
Dala o chlup vyšší číslo.

**Popisy dělají všechnu práci. Čísla jsou dekorace.**

**Co se pokazí, když to zkusíte i tak:** navenek nic. Odpovědi vypadají věrohodně,
vy předpokládáte, že kalibrace zabrala, a stavíte prahy nad škálou, kterou model
nikdy nepřijal. To je horší než zjevné selhání.

**Kde promptovat:** tady ne. Když potřebujete stupnici, použijte Score — ty úrovně
tou stupnicí *jsou* a poloha se vrátí jako číslo, aniž byste o něj žádali.
**Proč:** Noul vrací pravděpodobnost, že odpověď zní ano. Chtít po něm, aby tuhle
pravděpodobnost použil jako hodnocení, znamená chtít po něm zakódovat veličinu,
kterou ta otázka nemá.

📄 [Plný zápis](findings/04-scale-anchors.cs.md) ·
▶ `python experiments/07_scale_anchors.py`

---

## 7 — Příklady buď nesou informaci, nebo nenesou nic

**Proč na tom záleží:** „přidej few-shot příklady" je reflex. Někdy je to odpověď,
někdy jen tokeny.

**Úloha:** stejná otázka na vulgaritu jako v části 1, stejný český vstup. Tentokrát
jsem do `instructions` přidal few-shot příklady — dvojice jako *„'Vy jste debilové' →
vulgární, přímá osobní urážka"* — a měřil, jestli ten posun způsobil obsah příkladů,
nebo prostě to, že request narostl.

**Kontrolní skupina:** stejně dlouhý blok textu o provozu pipeline, který o vulgaritě
neříká vůbec nic. Dvě řady, shodné počty tokenů:

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

**Kde promptovat:** v `instructions`, připojené za otázku — ale až když si změříte,
že samotná kritéria nestačí.
**Jak:** hraniční případy, ne typické. Dvojice, které leží po obou stranách té hranice,
na které vám záleží. Pět nebo šest je ten užitečný rozsah.
**Proč tam a ne v kritériích:** kritéria definují, co odpovědi *znamenají*; příklady
ukazují, jak ta hranice *vypadá* na reálném vstupu. Sáhněte po nich, když nedokážete
to pravidlo čistě vyslovit — když se přistihnete, jak píšete „poznáte to, až to
uvidíte", to je ten signál.

**Co se pokazí, když je přidáte i tak:** nic se nezlepší a každé volání stojí víc.
V části 5 byly příklady čistá režie na úloze, která už byla na 100 %.

**K latenci:** plochá do ~2 000 tokenů, **+0,28 s při ~5 000**, shodně v obou řadách.
15,8× víc tokenů stálo jen 1,27× delší odezvu, protože zpracování vstupu je paralelní.

📄 [Plný zápis](findings/08-length-vs-content.cs.md) ·
▶ `python experiments/04_length_vs_content.py`

---

## 8 — Norma musí působit oběma směry

**Proč na tom záleží:** norma, která posune všechno dolů, není kalibrace, ale vypnutá
moderace. Tohle je test, který vám řekne, kterou z nich jste napsali.

**Úloha:** stejné české moderační zadání jako v části 1, ale otestované pořádně.
Devět mírných textů, které norma *má* pustit, a tři hraniční, které **nesmí** —
dvě osobní urážky a jedna výhrůžka.

**Norma pojmenovává osu, místo aby vyjmenovávala slova:**

```
criteria:
  true  → „jazyk, který by český uživatel považoval za skutečně urážlivý:
           osobní urážky mířené na člověka nebo skupinu, výhrůžky ublížením
           nebo sexuální nadávky. ZÁLEŽÍ NA TOM, JESTLI JE NAPADÁN ČLOVĚK,
           NE JESTLI SE V TEXTU OBJEVÍ HRUBÉ SLOVO."
  false → „čisté, NEBO jen mírné české hovorové výrazy, které jsou běžná
           neformální mluva: 'ty vole', 'do prdele', 'blbost', 'kravina',
           'sakra' … Kritizovat produkt nebo rozhodnutí natvrdo je taky
           v pořádku."
```

Výsledky, rozdělené podle toho, do které skupiny text patří:

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

**Co se pokazí bez té druhé poloviny:** napíšete normu, která filtr uvolní, nasadíte
ji a zjistíte, že jste uvolnili i to, co jste chtěli zachytit. Norma, která působí jen
jedním směrem, není kalibrace — je to vypnutá moderace přes několik mezikroků.

**Kde promptovat:** v obou větvích, a pak v testovací sadě s oběma druhy vstupu.
**Jak:** vyslovit tu *osu*, ne seznam slov. *„Záleží na tom, jestli je napadán člověk"*
zachytilo výhrůžku, která neobsahovala jediný vulgarismus — žádný seznam by to nedokázal.
**Proč tam:** seznam je konečný a vždycky se najde někdo, kdo napíše větu, na kterou
jste nepomysleli. Osa generalizuje.

**Vždycky testujte hraniční případy.** Devět textů, které mají projít, vám samo o sobě
neřekne nic; teprve ty tři, které projít nesmí, vám řeknou, jestli jste napsali
kalibraci, nebo obcházku.

**Pozor na přesah:** norma mluví výhradně o češtině, a přesto anglický testovací text
klesl z 0,916 na 0,176. Kritéria posouvají celkový práh citlivosti, ne filtr na
vyjmenovaná slova. Když chcete úzký efekt, ohraničte ho výslovně.

📄 [Plný zápis](findings/06-cultural-norm.cs.md) ·
▶ `python experiments/10_cultural_norm.py`

---

## 9 — Čeština si tady vedla stejně jako angličtina

**Proč na tom záleží:** dokumentace varuje před neanglickým obsahem. Na téhle úloze se
to v číslech neprojevilo — což se hodí vědět, když stavíte pro neanglický trh.

**Úloha:** dostanete zákaznickou zprávu, rozhodnete, jestli autor vyjadřuje
nespokojenost s produktem nebo službou. Noul, s kritérii, která výslovně pokrývají
i nepřímé stížnosti:

```
instructions: „Vyjadřuje autor této zprávy nespokojenost s produktem nebo
               službou?"
criteria:
  true  → „Autor si stěžuje: hlásí problém, vyjadřuje frustraci nebo
           kritizuje to, co dostal. Patří sem i zdvořilé nebo nepřímé
           stížnosti, sarkasmus a zlehčování."
  false → „Nestěžuje si: je spokojený, neutrální, ptá se na něco, nebo
           popisuje problém, který se stal někomu jinému nebo se nestal
           vůbec."
```

**Otázka zůstala po celou dobu anglicky** — měnil se jen jazyk hodnoceného textu.
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

**Kde promptovat:** ne v překladu — v kritériích, stejně jako všude jinde. Napsat
otázku česky nepřineslo nic. Co *záleželo*, bylo zpátky v části 1: říct modelu, jak
český neformální rejstřík vlastně zní.
**Proč:** ta mezera není v porozumění jazyku, ale v normách. Model čte česky dobře.
Co nemá, je český cit pro to, co je hrubé.

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
