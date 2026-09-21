# Dvě rodiny, dvě pohádky, opačná rozhodnutí

### Nejostřejší kontrast, který se nám podařilo naměřit

*Měřeno 21. 9. 2026 · `jev-1.13.0` · 2 příběhy × 3 profily × 5 běhů*

---

## Co jsme hledali

Předchozí testy ukazovaly, že profil výsledkem hne. Chyběl ale případ, kde je ten
posun tak ostrý, že **mění rozhodnutí na opačné** — a kde obecný klasifikátor
nemá šanci si toho všimnout.

Zadání znělo: najít dvojici obsahů, kde

1. **bez profilu projde obojí** s vysokým skóre
2. **profil A** jeden pustí a druhý zakáže
3. **profil B** to má přesně obráceně

---

## Situace

Dvě rodiny, obě s dítětem 5–7 let. Obě naprosto běžné.

**Rodina A** — šestiletá dcera má skutečný strach z pavouků a hmyzu. Ne preferenci;
po pohádce s pavoukem neusne. Jinak snese i napínavý příběh.

**Rodina B** — šestiletý syn miluje zvířata, všechna. Rodiče ale teď nezvládnou
příběhy, kde je někdo vyloučený z kolektivu — přesně tohle řeší ve škole.

**Dvě pohádky**, obě zcela neškodné:

| | Děj |
|---|---|
| **Pavoučice Anička** | Pavoučice si staví pavučinu v kůlně, vítr ji roztrhá, brouk ji povzbudí, postaví novou, dívají se na ni spolu do setmění. |
| **Zajíček Ondra** | Zajíčka nevezmou do hry, sedí u plotu, přisedne si k němu nejmenší zaječice, jdou hledat ostružiny, druhý den ho chtějí oba týmy. |

Žádné násilí, nic strašidelného, obě končí dobře. **Na tom je to postavené** — obecný
klasifikátor na nich nemá co najít.

---

## Výsledek

| Příběh | bez profilu | Rodina A | Rodina B |
|---|---|---|---|
| **Pavoučice Anička** | **0,912** → pustit | **0,006** → NEPOUŠTĚT | **0,721** → pustit s pozn. |
| **Zajíček Ondra** | **0,759** → pustit s pozn. | **0,889** → pustit | **0,035** → NEPOUŠTĚT |

**Dokonalý kříž.** Obě podmínky splněny: bez profilu projde obojí, s profily
dostane každá rodina opačné rozhodnutí na tomtéž obsahu.

Rozpětí **0,006 až 0,889** na dvou pohádkách, které se liší jen tématem —
ne tónem, ne násilností, ne vyzněním.

### Jistota modelu

| | úroveň | confidence |
|---|---|---|
| Anička / Rodina A | **0 ze 4** (úplné dno) | **1,000** |
| Ondra / Rodina B | **0 ze 4** (úplné dno) | 0,990 |

Model si v obou případech byl prakticky jistý. Nešlo o váhání mezi úrovněmi —
příběh přesně odpovídal popisu nejnižší úrovně dané rodiny.

---

## Proč to funguje

Nejnižší úroveň rodiny A:

> *„V příběhu vystupuje pavouk, hmyz nebo podobný tvor jako postava, je popsaný do
> detailu nebo ukázaný zblízka. Naše dcera má z těchhle zvířat silný strach a po
> takové pohádce neusne, ať je napsaná jakkoli laskavě."*

Poslední část věty je důležitá: *„ať je napsaná jakkoli laskavě"*. Bez ní by model
mohl usoudit, že vlídně podaný pavouk problém nedělá.

Nejvyšší úroveň téže rodiny končí:

> *„…smutné nebo těžké momenty jsou v pořádku, dokud platí tahle podmínka."*

To je druhá polovina definice — **rodina nechce měkčí svět, chce jednu konkrétní věc.**
Kdyby tam ta věta nebyla, klesl by i Ondra, který je pro ně naprosto v pořádku (0,889).

Rodina B má obrácenou logiku a ve své nejvyšší úrovni výslovně píše:

> *„…zvířata jakéhokoli druhu, včetně hmyzu a pavouků, jsou pro něj úplně v pořádku."*

Proto Anička dostala 0,721 a ne dno.

---

## Kaskáda

**Krok 1 — brána (Noul):** *„Je to vůbec dětská pohádka?"* Obě 0,98.
Brána je společná pro všechny rodiny a profil ji nepřebije.

**Krok 2 — stupnice (Score):** sem se dostane jen to, co prošlo branou.
Tady platí úrovně dané rodiny.

**Krok 3 — prahy (kód):** ≥0,80 pustit · ≥0,55 s poznámkou · ≥0,30 zeptat se
rodiče · <0,30 nepouštět. **Druhá nezávislá vrstva personalizace** — prahy si může
každá rodina nastavit jinak, bez modelu.

---

## Co z toho plyne

**1. Obecný klasifikátor by tu nepomohl.** Oba příběhy jsou správně vyhodnocené
jako neškodné. Chyba není v modelu — chybí mu informace, kterou má jen ta rodina.

**2. Není to klíčové slovo.** Filtr na slovo „pavouk" by udělal totéž pro Aničku,
ale zablokoval by i dokument o včelách, který by ta rodina milovala. Tohle je
posouzení obsahu, ne shoda řetězce.

**3. Musí se popsat obě strany.** Bez věty *„smutné momenty jsou v pořádku"*
by stupnice rodiny A sjela dolů úplně všechno.

**4. Ostrost je v konkrétnosti.** Rodiče nepopisují míru („jsme přísní"),
popisují **jednu konkrétní situaci a proč**. To model umí zachytit.

---

## Omezení

- **Dva příběhy, dva profily.** Ukazuje mechanismus v nejčistší podobě,
  neměří přesnost na širším obsahu.
- **Profily jsem psal já**, ne skuteční rodiče.
- **Příběhy jsem psal já**, tedy tak, aby trefily danou citlivost. V reálném
  provozu by obsah takhle čistě rozdělený nebyl.
- **Prahy jsou zvolené**, ne odvozené z dat.

Co je doložené robustně: **tentýž obsah dostane opačné rozhodnutí podle toho,
jak je napsaná stupnice** — a rozdíl je 0,006 vs. 0,889, tedy přes celou škálu.

---

📄 Data: [results/test_14_fobie.json](../results/test_14_fobie.json) ·
Skript: [test_14_fobie.py](../experiments/11_personalised_scales.py)
