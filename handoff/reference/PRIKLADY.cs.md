# Příklady — jak se skládá API call, řádek po řádku

> Psáno pro tebe: pro prompt inženýra, který klasifikátory umí, ale dělal je promptem.
> Žádný žargon. Každý řádek vysvětlený.

---

## 0. Než začneme: co se změnilo proti tomu, co znáš

Takhle jsi psal klasifikátor dosud:

```
Jsi klasifikátor sentimentu. Vrať JSON ve tvaru:
{"sentiment": "positive|negative", "confidence": 0.0-1.0}

Příklad 1: vstup "Skvělé!" -> {"sentiment":"positive","confidence":0.95}
Příklad 2: vstup "Hrozné." -> {"sentiment":"negative","confidence":0.92}
...dalších 15 příkladů...

Text k vyhodnocení: "Balík dorazil pozdě."
```

Jeden dlouhý text, ve kterém je **všechno naráz**: role, tvar výstupu, příklady i vstup.
A pak doufáš, že model vrátí platný JSON.

U Jeva je to **rozdělené do pojmenovaných polí**:

| Co jsi psal do promptu | Kam to patří u Jeva |
|---|---|
| „Jsi klasifikátor sentimentu" | ❌ nikam — odpadá |
| „Vrať JSON ve tvaru {...}" | ❌ nikam — **tvar výstupu je daný typem otázky** |
| 15 příkladů vstup→výstup | ❌ nikam — **odpadá, model je na to trénovaný** |
| „Rozhodni, jestli je text negativní" | ✅ `instructions` |
| „positive = pochvala, negative = stížnost" | ✅ `criteria` |
| Text k vyhodnocení | ✅ `state` |

**Tři věci, které ti odpadnou:**

1. **Nemusíš popisovat tvar výstupu.** Řekneš „tohle je otázka typu `choice`" a tvar odpovědi je tím dán. Nejde ho rozbít.
2. **Nemusíš psát příklady.** Žádný few-shot. Model je natrénovaný přímo na rozhodování.
3. **Nemusíš parsovat a ošetřovat chyby.** Nemůže přijít rozbitý JSON ani vymyšlená kategorie.

**Jedna věc, kterou naopak získáš:** místo jednoho čísla `confidence`, které si model vycucal,
dostaneš **skutečné rozdělení pravděpodobností** přes všechny možnosti. To je zásadní
rozdíl a vrátím se k němu v sekci 5.

---

## 1. Celý příklad — vstup

Reálný call. Zákaznická recenze na deset řádků, pět otázek naráz.

```json
{
  "state": "I ordered the XR-200 wireless headphones on March 3rd as a birthday present for my daughter, and they arrived two days later, which I was honestly impressed by. The packaging was excellent — everything was well protected and the unboxing felt premium. My daughter loved the design and the sound quality was genuinely good for the price, with deep bass and clear vocals.\n\nThe problem started about ten days in. The right earcup began cutting out intermittently, usually after about twenty minutes of use. I tried re-pairing them, resetting them, and using three different devices, and the issue persisted. I contacted your support team on March 18th through the web form and received an automated acknowledgement, but no human reply. I followed up on March 22nd and again on March 27th. It is now April 2nd and I have still not heard from anyone.\n\nI am not asking for anything unreasonable here. The product is clearly defective and it is still well within the warranty period. I would like either a replacement unit or a full refund. What I would really like is for somebody to actually respond to me, because the silence is far more frustrating than the faulty product itself.",

  "model": "jev-latest",

  "questions": {
    "negative_emotion": {
      "type": "noul",
      "instructions": "Does this text express negative emotion toward the company or its service?",
      "criteria": {
        "true": "The author expresses dissatisfaction, anger, frustration, or disappointment",
        "false": "The author is neutral, factual, or positive"
      }
    },

    "wants_refund": {
      "type": "noul",
      "instructions": "Is the author requesting a refund or a replacement?"
    },

    "primary_issue": {
      "type": "choice",
      "instructions": "What is the main problem the author is reporting?",
      "criteria": {
        "product_defect":       "The item itself is faulty or broken",
        "shipping":             "Delivery was late, damaged, or lost",
        "support_unresponsive": "The company failed to reply or help",
        "billing":              "A charge, refund, or invoice problem",
        "none":                 "No clear problem is reported"
      }
    },

    "urgency": {
      "type": "score",
      "instructions": "How urgently does this case need a human response?",
      "criteria": [
        "No response needed",
        "Routine, can wait a week",
        "Should be answered within two days",
        "Needs a response today"
      ]
    },

    "churn_risk": {
      "type": "score",
      "instructions": "How likely is this customer to stop buying from the company?",
      "criteria": [
        "Loyal, very likely to buy again",
        "Neutral",
        "At risk of leaving",
        "Almost certainly lost"
      ]
    }
  }
}
```

---

## 2. Celý příklad — výstup

Tohle se skutečně vrátilo. Za **1,26 sekundy**, 830 vstupních tokenů.

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "negative_emotion": {
      "type": "noul",
      "noul": 0.98
    },
    "wants_refund": {
      "type": "noul",
      "noul": 0.98
    },
    "primary_issue": {
      "type": "choice",
      "choice": "support_unresponsive",
      "confidence": 0.7,
      "probabilities": {
        "support_unresponsive": 0.77,
        "product_defect":       0.23,
        "shipping":             0.0,
        "billing":              0.0,
        "none":                 0.0
      }
    },
    "urgency": {
      "type": "score",
      "score": 2.88,
      "confidence": 0.88,
      "legend": {
        "0": "No response needed",
        "1": "Routine, can wait a week",
        "2": "Should be answered within two days",
        "3": "Needs a response today"
      },
      "probabilities": { "0": 0.0, "1": 0.0, "2": 0.12, "3": 0.88 }
    },
    "churn_risk": {
      "type": "score",
      "score": 2.72,
      "confidence": 0.72,
      "legend": {
        "0": "Loyal, very likely to buy again",
        "1": "Neutral",
        "2": "At risk of leaving",
        "3": "Almost certainly lost"
      },
      "probabilities": { "0": 0.0, "1": 0.0, "2": 0.28, "3": 0.72 }
    }
  },
  "usage": { "input_tokens": 830, "output_tokens": 132 }
}
```

---

## 3. Vstup řádek po řádku

### `"state": "I ordered the XR-200..."`

**Co to je:** text, který se hodnotí. Tvůj „vstup na konci promptu".

**Jak nad tím přemýšlet:** představ si, že máš kolegu-experta a dáváš mu papír do ruky.
`state` je ten papír. Všechno, co potřebuje vědět, musí být na něm — model nemá paměť
předchozích callů, nemá přístup k tvé databázi, nic si nedohledá.

**Jak je dlouhý:** tenhle má 1 177 znaků, tři odstavce. Vejde se **32 000 tokenů**,
tedy zhruba 120 000 znaků — nějakých 25 normostran. Deset řádků je úplná drobnost.

**Důležité:** `state` **nemusí být text.** Může to být struktura:

```json
"state": {
  "ticket_id": "T-4491",
  "customer": { "name": "Nováková", "tier": "premium", "since": "2019" },
  "messages": [
    { "from": "customer", "text": "The right earcup keeps cutting out." },
    { "from": "agent",    "text": "Have you tried re-pairing?" },
    { "from": "customer", "text": "Three times. Still broken." }
  ]
}
```

A pak se v otázce odkážeš na konkrétní místo zpětnými apostrofy:

```json
"instructions": "Is the customer in `messages` escalating in frustration?"
```

**To je pro tebe zajímavé:** promptem jsi musel strukturu popisovat slovy.
Tady ji prostě pošleš a ukážeš na ni prstem.

> ⚠️ **Jedno pravidlo, které platí opačně, než bys čekal:** čím míň balastu ve `state`, tím líp.
> U velkých modelů „víc kontextu neuškodí". Tady **uškodí** — nesouvisející text
> přesnost zhoršuje (dokumentace tomu říká *context rot*). Pošli jen to, co otázka potřebuje.
> Máš-li tisícistránkový dokument, napřed si v kódu vyfiltruj relevantní pasáže.

### `"model": "jev-latest"`

**Co to je:** který model to zpracuje. Tady měl uživatel dotaz — **není to Claude.**
TypeSafe je jiná firma a Jev je jejich vlastní model. Claude ani GPT tohle API neumí.

**Co tam psát:** vždycky `"jev-latest"`. Je to alias, který ukazuje na aktuální verzi
(dnes `jev-1.13.0`). Ve skriptu to bude konstanta, kterou nastavíš jednou a už na ni nesáhneš.

**Proč to v odpovědi vypadá jinak:** poslal jsi `jev-latest`, vrátilo se `jev-1.13.0`.
API ti říká, která konkrétní verze to počítala. Užitečné, až vyjde 1.14 a čísla se pohnou —
budeš vědět, čím byl který výsledek naměřený.

### `"questions": { ... }`

**Tohle je to, co ti bylo nejasné. Rozeberu to pomalu.**

`questions` je **seznam otázek**, na které se ptáš toho samého papíru.
Ne jedna otázka — kolik chceš.

Zapisuje se jako mapa (slovník):

```
"questions": {
    "nazev_otazky_1":  { ...definice... },
    "nazev_otazky_2":  { ...definice... },
    "nazev_otazky_3":  { ...definice... }
}
```

**Ten název si vymýšlíš ty.** `negative_emotion`, `mojeOtazka`, `q1` — cokoliv.
Je to jen štítek, pod kterým si pak najdeš odpověď:

```
POŠLEŠ:  questions.urgency  = {otázka na urgenci}
VRÁTÍ:   answers.urgency    = {odpověď na urgenci}
         ↑ stejný název
```

V kódu pak:
```python
if result["answers"]["urgency"]["score"] > 2.5:
    alert_manager()
```

> 🔑 **Nejdůležitější věta celého dokumentu:**
> **Název otázky se modelu NEPOSÍLÁ.**
>
> Model nevidí, že jsi otázku pojmenoval `negative_emotion`. Vidí jen `instructions`
> a `criteria`. Kdybys otázku pojmenoval `is_angry`, ale do instructions napsal
> „Je text psaný anglicky?", model odpoví na tu angličtinu.
>
> **Celý význam musí být uvnitř otázky.** Název je jen šuplík pro tvůj kód.

**Proč pět otázek naráz, a ne pět callů:** protože **běží současně** a stojí skoro stejně
jako jedna. Naměřeno v této složce: 1 otázka ~0,9 s, 20 otázek 0,73 s. `state` se posílá
jednou a sdílí se mezi všemi.

**Ale pozor — otázky na sebe nevidí.** Nemůžeš napsat „pokud jsi u první otázky odpověděl
ano, pak…". Každá dostane papír samostatně a odpovídá nezávisle. Logiku mezi nimi
si uděláš v kódu, až máš všechny odpovědi.

---

## 4. Tři typy otázek — a kdy který

Každá otázka má stejné tři složky:

```
type          ← které primitivum (noul / choice / score)
instructions  ← co má posoudit
criteria      ← možné odpovědi (tvar se liší podle typu)
```

### Noul = „platí to?"

```json
"negative_emotion": {
  "type": "noul",
  "instructions": "Does this text express negative emotion toward the company or its service?",
  "criteria": {
    "true":  "The author expresses dissatisfaction, anger, frustration, or disappointment",
    "false": "The author is neutral, factual, or positive"
  }
}
```

| Řádek | Význam |
|---|---|
| `"type": "noul"` | ano/ne otázka. Vrátí jedno číslo 0–1. |
| `"instructions"` | Samotná otázka. Piš ji tak, aby šla zodpovědět ano/ne. |
| `"criteria"` | **Nepovinné.** Upřesňuje, co znamená ano a co ne. |

**Odpověď:** `{"type": "noul", "noul": 0.98}`

**Jak číst to číslo:** 0,98 znamená *„na 98 % ano"*.

> ⚠️ **Nejčastější omyl, a tebe se týká přímo:** noul **není intenzita**.
> 0,5 neznamená „středně naštvaný". Znamená **„nevím, je to tak půl na půl"**.
> Chceš-li měřit míru, potřebuješ `score`, ne noul.

**Kdy Noul:** když se ptáš na přítomnost vlastnosti. Je to spam? Obsahuje to osobní údaj?
Žádá zákazník refundaci?

**Kdy jeden Noul na každý label:** když může platit **víc věcí naráz**. Ticket může být
zároveň o vadě i o mlčící podpoře. Pak nedělej `choice`, ale tři samostatné nouly —
každý může být vysoký.

**Všimni si:** `wants_refund` v příkladu nemá `criteria` vůbec. Otázka „Is the author
requesting a refund or a replacement?" je sama o sobě jednoznačná. Přidávej criteria,
až když vidíš, že model chápe hranici jinak než ty.

### Choice = „která jedna z nich?"

```json
"primary_issue": {
  "type": "choice",
  "instructions": "What is the main problem the author is reporting?",
  "criteria": {
    "product_defect":       "The item itself is faulty or broken",
    "shipping":             "Delivery was late, damaged, or lost",
    "support_unresponsive": "The company failed to reply or help",
    "billing":              "A charge, refund, or invoice problem",
    "none":                 "No clear problem is reported"
  }
}
```

| Řádek | Význam |
|---|---|
| `"type": "choice"` | Vyber přesně jednu možnost. |
| `"instructions"` | Podle čeho vybírat. |
| `"criteria"` | **Povinné.** Vlevo název kategorie (dostaneš zpátky), vpravo popis pro model. |

**Odpověď:**
```json
{
  "choice": "support_unresponsive",
  "confidence": 0.7,
  "probabilities": {
    "support_unresponsive": 0.77,
    "product_defect":       0.23,
    "shipping": 0.0, "billing": 0.0, "none": 0.0
  }
}
```

**Tohle je místo, kde Jev ukázal, co umí.** Recenze je na první pohled o vadném sluchátku.
Model ale dal **77 % mlčící podpoře** a jen 23 % vadě produktu — protože zákazník
v poslední větě sám píše: *„the silence is far more frustrating than the faulty product itself."*
Model to přečetl a vyhodnotil správně, co je **hlavní** problém.

**Proč `probabilities` stojí za pozornost:** vidíš nejen vítěze, ale **celé rozložení**.
Tady 77/23 znamená „hlavně podpora, ale vada v tom taky hraje". To je informace,
kterou ti samotný label `support_unresponsive` nedá.

**`none` na konci — to je ten trik, na který se zapomíná.** Choice tě nutí vybrat jednu
možnost. Když do seznamu nedáš „nic z toho", model **musí** vybrat něco, i když nic nesedí,
a ty dostaneš nesmysl s vysokou jistotou. **Vždycky dej únikovou možnost**, pokud si nejsi
naprosto jistý, že jedna z kategorií platí vždycky.

**Kdy Choice:** směrování do fronty, výběr kategorie, volba dalšího kroku. Když
kategorie **vylučují jedna druhou**.

### Score = „jak moc?"

```json
"urgency": {
  "type": "score",
  "instructions": "How urgently does this case need a human response?",
  "criteria": [
    "No response needed",
    "Routine, can wait a week",
    "Should be answered within two days",
    "Needs a response today"
  ]
}
```

| Řádek | Význam |
|---|---|
| `"type": "score"` | Umísti na stupnici. |
| `"instructions"` | Jakou vlastnost měřit. |
| `"criteria"` | **Povinné, je to POLE** — na pořadí záleží! Od nejmenšího k největšímu. |

**Odpověď:**
```json
{
  "score": 2.88,
  "confidence": 0.88,
  "legend": {"0": "No response needed", "1": "Routine...", "2": "...two days", "3": "...today"},
  "probabilities": {"0": 0.0, "1": 0.0, "2": 0.12, "3": 0.88}
}
```

**Jak číst 2,88:** stupnice je 0–3. Výsledek 2,88 leží **mezi** úrovní 2 a 3, blízko trojce.
Čti to jako *„skoro určitě dnes, s malou příměsí ještě to jde dva dny"*.

**Odkud se 2,88 vzalo:** je to vážený průměr. `0×0,0 + 1×0,0 + 2×0,12 + 3×0,88 = 2,88`.
Model rozdělil jistotu mezi úrovně a tohle je těžiště.

**`legend`** ti jen vrací tvoje popisky očíslované, ať si v kódu nemusíš pamatovat pořadí.

> ⚠️ **Past, do které spadneš, když budeš přemýšlet jako u běžného skóre:**
> `score` **nepoužívej k rekonstrukci přesného čísla.** Když uděláš stupnici
> „0 Kč / 500 Kč / 5000 Kč" a vyjde 1,5, **neznamená to 2 750 Kč.** Model není kalkulačka
> a mezi úrovněmi neinterpoluje lineárně. Na práh („je to nad 2?") je to v pořádku,
> na dopočítání hodnoty ne.

**Jak psát úrovně:** každá musí **popisovat konkrétní situaci** a dávat smysl samostatně.

- ❌ špatně: `["1", "2", "3", "4", "5"]` — model neví, co je 3
- ❌ špatně: `["nízká", "střední", "vysoká"]` — vůči čemu?
- ✅ dobře: `["Needs no response", "Can wait a week", "Within two days", "Today"]`

**Kdy Score:** míra, závažnost, priorita, kvalita — cokoliv, co má **přirozené pořadí**.

---

## 5. Confidence — tady je největší rozdíl proti tvým promptům

Psal jsi `{"sentiment": "negative", "confidence": 0.92}` a model ti to číslo **vymyslel**.
Bylo to slovo jako každé jiné, které mu vyšlo jako pravděpodobné pokračování textu.
Nemělo oporu ve výpočtu.

Tady je `confidence` **odvozena z rozdělení pravděpodobností**. Měří, jak je rozdělení
soustředěné.

Porovnej dvě odpovědi z našeho příkladu:

```
urgency:     probabilities {2: 0.12, 3: 0.88}   confidence 0.88   ← soustředěné
primary_issue: probabilities {support: 0.77, defect: 0.23}  confidence 0.70   ← rozprostřené
```

Model si je urgencí jistější než kategorií problému. A má pravdu — ta recenze **opravdu**
je o obojím, vadě i mlčení. Nízká confidence tady není chyba, je to **správný popis
nejednoznačného vstupu**.

**Dvě věci, které je třeba si zapamatovat:**

1. **Noul confidence nemá.** Jen číslo 0–1. Když potřebuješ vědět, jak jistý si model je
   u ano/ne otázky, vodítkem je vzdálenost od 0,5 — 0,98 je jisté, 0,55 není.

2. **Confidence není pravděpodobnost správnosti.** Říká „rozdělení je soustředěné",
   ne „mám pravdu". Model může být soustředěně vedle.

**Praktický vzorec, který na tom postavíš** — nezávislý benchmark zjistil, že model se
nikdy nemýlil s confidence 1,0:

```python
if answer["confidence"] >= 0.90:
    zpracuj_automaticky()
elif answer["confidence"] >= 0.60:
    posli_cloveku()
else:
    eskaluj_na_silnejsi_model()
```

Tohle je věc, kterou jsi s vymyšlenou confidence ve svých promptech dělat nemohl.

---

## 6. Jak poznat, že otázka je napsaná dobře

**Jedno rozhodnutí na otázku.** Tohle je nejčastější chyba:

- ❌ „Je text negativní a chce zákazník refundaci?" — dvě otázky v jedné, odpověď nepoužitelná
- ✅ dvě samostatné otázky, výsledky spojíš v kódu: `if neg > 0.7 and refund > 0.5:`

**Model čte doslova.** Odpoví na otázku, kterou jsi napsal — ne na tu, kterou jsi myslel.

Z dokumentace pochází rada, která je podle mě nejužitečnější věta o práci s tímhle modelem:

> *Když se díváš na špatnou odpověď a přistihneš se, jak vysvětluješ, co jsi vlastně myslel —
> to vysvětlení je ta chybějící polovina zadání.*

Máš tedy hotovou smyčku ladění: špatná odpověď → řekni nahlas, cos myslel → **napiš to
do `instructions` nebo `criteria`** → zkus znovu.

**`criteria` musí souhlasit s `instructions`.** Když se v instructions ptáš „je to naléhavé?"
a v criteria napíšeš `true: "není to naléhavé"`, model se zamotá. Ber criteria jako
pokračování věty, ne jako samostatný text.

**Co do otázky nepatří:**
- ❌ „Odpověz ve formátu JSON" — tvar je daný typem
- ❌ „Jsi expert na zákaznický servis" — role nic nepřidá
- ❌ příklady vstup→výstup — few-shot tu nefunguje
- ❌ „Buď objektivní" — nemá to efekt

---

## 7. Slovníček: tvoje pojmy → pojmy Jeva

Aby ses to po mně uměl dobře ptát:

| Když řekneš… | Myslíš tím | V API |
|---|---|---|
| „vstup", „text k hodnocení" | co se posuzuje | `state` |
| „prompt", „zadání" | co se má rozhodnout | `instructions` |
| „kategorie", „labely", „rubrika" | možné odpovědi | `criteria` |
| „klasifikátor" | jedna otázka | jedna položka v `questions` |
| „ano/ne klasifikátor" | binární | `type: "noul"` |
| „multi-class klasifikátor" | jedna z N | `type: "choice"` |
| „rating", „škála", „priorita" | míra | `type: "score"` |
| „multi-label" | víc labelů naráz | **víc noulů**, ne choice |
| „confidence" | jistota | `confidence` (u noulu není) |
| „logprobs", „rozložení" | pravděpodobnosti | `probabilities` |
| „batch" | víc otázek naráz | víc položek v `questions` (1 call!) |

**Až mi budeš zadávat práci, stačí říct třeba:**

> „Udělej klasifikátor na příchozí maily: multi-class do pěti front, k tomu ano/ne
> jestli je to stížnost, a škálu priority 0–3. Všechno v jednom callu."

Z toho vím přesně, že chceš jeden `choice` s pěti možnostmi plus `none`, jeden `noul`
a jeden `score` se čtyřmi úrovněmi — v jednom requestu.

---

## 8. Shrnutí na jednu obrazovku

```json
{
  "state":     "CO se hodnotí — text nebo struktura",
  "model":     "jev-latest",
  "questions": {
    "muj_nazev": {
      "type":         "noul | choice | score",
      "instructions": "CO se má rozhodnout",
      "criteria":     "MOŽNÉ ODPOVĚDI — tvar podle typu"
    }
  }
}
```

| | Noul | Choice | Score |
|---|---|---|---|
| **Otázka** | Platí to? | Která z nich? | Jak moc? |
| **`criteria`** | `{true, false}` — nepovinné | mapa — povinné | pole — povinné |
| **Vrací** | číslo 0–1 | label + rozdělení + conf | průměr + legend + rozdělení + conf |
| **Confidence** | ❌ nemá | ✅ | ✅ |
| **Víc naráz** | ✅ jeden na label | ❌ jen jedna | — |
| **Past** | 0,5 = nevím, ne „středně" | chybí `none` | neinterpoluj čísla |

**Pět vět, které si odnést:**

1. `state` je papír, který dáváš expertovi. Jen to, co potřebuje — balast škodí.
2. Název otázky se modelu **neposílá**. Význam patří do `instructions`.
3. Otázky v jednom callu běží **současně** a **nevidí na sebe**.
4. Tvar výstupu **nepopisuješ** — je daný typem a nejde rozbít.
5. `confidence` je **spočítaná** z rozdělení, ne vymyšlená. Postav na ní směrování.

---

📄 Technická reference: [API.md](API.md) · Spustitelné testy: [README.md](../README.md)
