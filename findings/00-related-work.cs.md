# Co už je o promptování `criteria` publikováno

*Rešerše k 21. 9. 2026 — šest dní po vydání modelu*

---

## Proč to čteme dřív, než postavíme testy

Dva důvody: nezkoumat znovu, co už někdo změřil, a hlavně — **jeden existující repo došel
k závěru, který vypadá v rozporu s naším měřením.** To je potřeba vyřešit, než z našich dat
uděláme článek.

---

## Hlavní nález: leepokai/llm-prompt-techniques-on-jev

**[github.com/leepokai/llm-prompt-techniques-on-jev](https://github.com/leepokai/llm-prompt-techniques-on-jev)**

Nejrelevantnější existující práce. Otestovali **15+ promptovacích technik** na čtyřech
akademických benchmarcích: LegalBench, BIG-Bench Hard, MMLU-Pro, CLERC.

Testovali mimo jiné přesně to, co nás zajímá: `LabeledFewShot` s k=5 a k=50,
`KNNFewShot` (výběr podle podobnosti) a many-shot s 50 označenými případy.

### Jejich výsledky

| Benchmark | Přímá otázka | S few-shot | Závěr |
|---|---|---|---|
| **BIG-Bench Hard** (23 úloh) | 90,6 % | 90,4 % | **neutrální až mírně horší** |
| **MMLU-Pro** (500 otázek) | 82,2 % | −2 až −5 bodů | **zhoršilo** |
| **LegalBench** `diversity_5` | 81,3 % | **94,7 %** (50 příkladů) | **výrazně zlepšilo** |
| LegalBench + GEPA optimalizace | — | 96–100 % | zlepšilo |

### Jejich klíčové rozlišení

Autoři zavádějí dělení, které je podle mě nejcennější myšlenka celé jejich práce:

| Typ techniky | Co dělá | Funguje? |
|---|---|---|
| **Information-carrying** | Dodá obsah, který model nemá — podmínky zákona, 50 precedentů, přepsané instrukce | ✅ Zabírá na těžkých úlohách |
| **Wording** | Přeformuluje bez přidání informace — role, emoce, „think step by step" | ❌ Nefunguje |

Proč wording nefunguje: **Jev negeneruje mezikroky.** Přečte jednou a odpoví.
Techniky, které u LLM fungují tím, že vynutí delší uvažování, tu nemají kde zabrat.

### Jejich hlavní závěr — a zdánlivý rozpor s námi

> *„Na úlohách, které Jev řeší už ze samotné otázky (BBH 91 %, MMLU-Pro),
> jsou tytéž techniky neutrální nebo negativní."*
>
> *„Příklady o nesouvisejících problémech ředí výkon na už vyřešených úlohách."*

**My jsme naměřili posun 0,93 → 0,44 přidáním pěti příkladů. Oni měřili −0,2 bodu.
Kdo má pravdu?**

Oba. Měříme jinou věc — a právě tohle je pro článek nejdůležitější:

| | leepokai | naše měření |
|---|---|---|
| **Úloha** | akademické benchmarky s **objektivně správnou odpovědí** | moderace, kde **správná odpověď závisí na normě** |
| **Co příklady dodávají** | nic navíc — model už odpověď zná | **definici hranice**, kterou model znát nemůže |
| **Existuje „správná" odpověď?** | ano, jedna | ne — závisí na komunitě |
| **Výsledek** | −0,2 bodu (ředění) | −0,49 (posun hranice) |

Jejich vlastní rámec to vysvětluje: naše příklady **jsou** information-carrying.
Nesou informaci *„v češtině je `ty vole` běžný rejstřík"*, kterou model z trénovacích
dat nemá. Zatímco u BBH příklady jen opakují, co model už umí.

> **Důsledek pro náš článek:** nesmíme tvrdit „few-shot na Jevu funguje".
> Musíme tvrdit přesněji: **few-shot funguje, když nese informaci, kterou model nemá —
> typicky definici hranice tam, kde žádná objektivně správná odpověď neexistuje.**
> A citovat leepokai jako doklad druhé strany.

Tohle náš článek naopak posílí. Bez toho rozlišení by byl napadnutelný.

### Další jejich nález, který se nám hodí

**„Where the options go is worth 5.8 points"** (MMLU-Pro). Umístění možností —
jestli jsou v `criteria`, nebo ve `state` — je o 5,8 bodu, tedy víc než většina
promptovacích technik. **Struktura otázky váží víc než formulace.**

---

## Co říká oficiální dokumentace

TypeSafe má vlastní doporučení, rozeseté po několika stránkách:

| Doporučení | Zdroj |
|---|---|
| Jedna atomická otázka = jeden úsudek | [primitives.md](https://docs.typesafe.ai/primitives) |
| `criteria` jsou pokračování `instructions`, nesmí si odporovat | [jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13) |
| Vždy přidat `other`/`none` s cestou k člověku | primitives_choice.md |
| Doménová pravidla a **hraniční případy** patří do `instructions` a `criteria` | [models.md](https://docs.typesafe.ai/models) |
| Filtrovat `state` — přesnost klesá s balastem (*context rot*) | jaggedness |
| Angličtina je primární, ostatní jazyky testovat na vlastním obsahu | models.md |

Pozoruhodné je, co tam **není**: dokumentace nikde neříká *„používejte few-shot příklady
v instructions"*. Zmiňuje „boundary cases", ale bez návodu, kolik jich a jak je psát.
Ani jediné číslo o tom, jaký to má efekt.

**To je mezera, do které naše práce zapadá.**

---

## Ostatní publikované zdroje

### Langfuse — Using TypeSafe's Jev for evals
[langfuse.com/blog/2026-09-18](https://langfuse.com/blog/2026-09-18-using-typesafes-jev-for-evals)

Nejblíž tématu ze všech blogů, ale **bez experimentů**. Uvádí užitečné pozorování:
nízká confidence (0,51) signalizovala, že dvě kategorie jsou od sebe těžko odlišitelné.
Tedy: *nízká confidence = špatně napsaná criteria*, což je použitelná diagnostika.

Výslovně ale: **žádná čísla porovnávající různé formulace criteria.**

### Ostatní

| Zdroj | Co přináší | Experimenty? |
|---|---|---|
| [Pydantic docs](https://pydantic.dev/docs/ai/models/typesafe/) | integrace | ne |
| [Braintrust](https://www.braintrust.dev/blog/evaluate-agent-responses-with-jev) | Jev jako evaluátor | ne |
| [Cloudflare AI docs](https://developers.cloudflare.com/ai/models/typesafe/jev/) | dostupnost | ne |
| [flaviocopes.com/jev](https://flaviocopes.com/jev/) | přehled | ne |
| [pearpages.com](https://pearpages.com/blog/2026/09/16/jev-sorted-what-typesafes-system-one-model-actually-is-and-what-is-still-just-a-claim) | kritický audit tvrzení | ne |
| [Anil-matcha/awesome-jev](https://github.com/Anil-matcha/awesome-jev-by-typesafe) | sbírka vzorů a promptů | ne |
| [SamuelSacco/jev-exploration](https://github.com/SamuelSacco/jev-exploration) | audit tvrzení, živé ukázky | částečně |

Jedno vyhledávání to shrnulo přímo:

> *„There appears to be limited public ablation research specifically on how wording
> changes in criteria affect Jev's classification results, though this is identified
> as an important area for evaluation."*

---

## Kde je mezera, kterou můžeme zaplnit

Co **už je** pokryté:
- Promptovací techniky na akademických benchmarcích (leepokai, důkladně)
- Obecná doporučení, jak psát otázky (dokumentace, blogy)
- Srovnání rychlosti a ceny proti LLM (několik benchmarků)

Co **není** pokryté nikde:

1. **Ablace criteria** — která část definice nese účinek. Naše měření
   (obecný pokyn −0,12 vs. výčet slov −0,82) nemá obdobu.
2. **Nesymetrie větví** — že definovat výjimky je ~3,5× účinnější než rozšiřovat zakázané.
3. **Kulturní kalibrace** — posun normy pro neanglické prostředí, měřený.
   Dokumentace jen varuje „testujte si to sami".
4. **Křivka nasycení příkladů** — kde je optimum. Máme náznak (5 vs. 50 = poměr 12:1),
   ale na opakované pětici, což je slabina.
5. **Cena kalibrace** — kolik stojí posun hranice v tokenech a latenci.
6. **Čeština** — o výkonu na češtině nepsal nikdo.

---

## Co to mění pro návrh testů

**1. Přeformulovat hlavní tezi.**
Ne „few-shot funguje", ale „**few-shot funguje, když nese informaci, kterou model nemá**".
Leepokai citovat jako protiváhu — posílí to věrohodnost.

**2. Přidat kontrolní úlohu, kde příklady nepomůžou.**
Vzít úlohu s objektivně správnou odpovědí (jazyk textu, přítomnost e-mailu) a ukázat,
že tam příklady nic nedají. Tím sami předvedeme obě strany a článek bude poctivý,
ne jednostranný.

**3. Opravit slabinu s 50 příklady.**
Naše „50 příkladů" byla opakovaná pětice. Leepokai používali 50 **různých**.
Musíme to přeměřit s různými, jinak je ten poměr 12:1 nekorektní.

**4. Testovat umístění, nejen formulaci.**
Jejich nález „umístění možností = 5,8 bodu" naznačuje, že `criteria` vs. `state`
může vážit víc než znění. Máme jedno měření (norma ve `state` −0,89 vs. criteria −0,85),
stojí za rozšíření.

**5. Měřit na sadě, ne na jedné větě.**
Všechna dosavadní čísla jsou z jednoho textu. Pro publikovatelný výsledek potřebujeme
20–50 ručně označených vzorků a měřit přesnost, ne posun jednoho čísla.

---

## Závěr rešerše

**Nikdo zatím nepublikoval systematickou ablaci criteria** ani měření kulturní kalibrace.
Téma je otevřené.

Zároveň existuje kvalitní práce (leepokai), která na akademických úlohách došla
k opačnému výsledku — a tu **musíme v článku zmínit a vysvětlit rozdíl**, ne ji obejít.
Rozdíl je vysvětlitelný jejich vlastním rámcem (information-carrying vs. wording)
a naše práce tím získá kontext místo toho, aby s ní byla v rozporu.

Model je šest dní starý. Za měsíc bude takových prací víc — teď je prostor.

---

*Rešerše provedena 21. 9. 2026. Zdroje jsou veřejné weby a repozitáře; čísla z nich
jsem nepřeměřoval a přebírám je tak, jak je autoři uvádějí.*
