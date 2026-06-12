# CLAUDE.md — Pitná voda 2026 · Program konference

## Účel projektu

Web s programem konference **Pitná voda 2026** (1.–4. června 2026, Hotel Palcát, Tábor).
Pořadatel: ENVI-PUR s.r.o. a W&ET Team, České Budějovice.
Kontakt: konference@envi-pur.cz · www.konference-pitnavoda.cz

---

## Struktura repozitáře

```
pitna-voda-2026-program/
├── index.html                  # Hlavní stránka — program konference (4 dny, záložky)
├── panel-kdo-po-nas.html       # Stránka diskusního panelu SOVAK/CzWA (středa 17:00–18:30)
├── generate_pdf.py             # Generátor PDF programu (ReportLab, DejaVu fonty)
├── vercel.json                 # Konfigurace deploymentu + bezpečnostní hlavičky
├── .env                        # Přihlašovací údaje pro Gmail (NIKDY necommitnout heslo)
├── www/
│   └── program-pitna-voda-2026.pdf   # Aktuální publikovaná verze PDF (pevný název)
└── archiv/
    └── program-pitna-voda-2026-vDDMMYYYY.pdf   # Datované verze
```

---

## Technický stack

- **Frontend**: čisté HTML + CSS + vanilla JS — žádný build systém, žádné npm závislosti
- **Fonty**: Google Fonts — `Outfit` (nadpisy, číslice) + `Source Sans 3` (text) / na `panel-kdo-po-nas.html` navíc `Montserrat` + `Source Serif 4`
- **Deployment**: Vercel (auto-deploy z větve `main` na GitHubu)
- **PDF**: Python 3 + ReportLab + python-dotenv (`pip install reportlab python-dotenv`)
- **Verze souborů**: prefix `v30`, `v31` … atd. v názvech souborů mimo repozitář; uvnitř repozitáře pevné názvy

---

## Design systém — CSS proměnné (index.html)

```css
--navy:      #1A3660   /* tmavě modrá — hlavní barva */
--navy-dark: #0f2040
--navy-mid:  #2B4E8C
--cyan:      #0BAAD4   /* akcent */
--cyan-lt:   #D0EEF8   /* keynote řádky */
--blue-lt:   #E2EAF7   /* sekce */
--green:     #C3EAAE   /* diskusní bloky, green řádky */
--peach:     #FAE4D6   /* firemní přednášky */
--pink:      #F4D0EC   /* oběd */
--bg:        #F0F4FA
--text:      #192035
--muted:     #5A6A85
--border:    #D8E2EF
```

`panel-kdo-po-nas.html` používá vlastní (ale kompatibilní) sadu proměnných s `--navy: #1F3864`.

---

## Typy řádků programu (index.html i generate_pdf.py)

| Třída / typ | Barva pozadí | Použití |
|---|---|---|
| `row-day` | `--navy` (bílý text) | Nadpis dne |
| `row-section` | `--blue-lt` | Název bloku přednášek |
| `row-keynote` | `--cyan-lt` | Úvodní přednáška dne |
| `row-pres` | bílá | Standardní přednáška |
| `row-firmy` | `--peach` | Firemní prezentace |
| `row-bdisc` | `--green` | Diskuse k bloku |
| `row-green` | `--green` | Diskusní blok / speciální akce |
| `row-lunch` | `--pink` | Oběd |
| `row-util` | bílá | Ostatní (registrace, zahájení…) |

---

## Program — přehled dnů

| Den | Datum | Klíčový přednášející |
|---|---|---|
| Pondělí | 1. 6. 2026 | Ing. Vilém Žák — Adaptace vodárenství (keynote) |
| Úterý | 2. 6. 2026 | doc. Ing. Petr Dolejš — Koagulace (50 let výzkumu) |
| Středa | 3. 6. 2026 | doc. RNDr. Martin Pivokonský — Hydrochemie + panel SOVAK/CzWA |
| Čtvrtek | 4. 6. 2026 | RNDr. Jindřich Duras — Voda propojuje |

Tematické bloky: Strategický rámec / Resilience / Aktivní uhlí / Technologie / Membrány / Hygiena / Mikrobiologie / Mikropolutanty / PFAS / Infrastruktura.

---

## Generování PDF

```bash
# Nainstaluj závislosti (jednorázově)
pip install reportlab python-dotenv --break-system-packages

# Vygeneruje PDF s dnešním datumem do archiv/ a zkopíruje do www/
python3 generate_pdf.py
```

- Výstup `archiv/program-pitna-voda-2026-vDDMMYYYY.pdf` (datovaná verze)
- Výstup `www/program-pitna-voda-2026.pdf` (pevný název pro web)
- Fonty: DejaVu Sans z `/usr/share/fonts/truetype/dejavu` (nutné pro českou diakritiku)
- Odesílání e-mailem: funkce `send_pdf_email()` existuje, ale je **zakomentována**; aktivuje se po nastavení `GMAIL_APP_PASSWORD` v `.env`

---

## Konfigurace e-mailu (.env)

```
GMAIL_USER=pavel.dobias79@gmail.com
GMAIL_APP_PASSWORD=          # App heslo z myaccount.google.com/apppasswords
RECIPIENT_EMAIL=konference@envi-pur.cz
```

Soubor `.env` **necommitnout** do Gitu. Heslo se generuje na Google účtu jako „App password".

---

## Deployment (Vercel)

- Automatický deploy při push do `main`
- `vercel.json` nastavuje bezpečnostní hlavičky (CSP, X-Frame-Options, Referrer-Policy…)
- Web je statický — žádný server-side kód, žádné API routes
- PDF soubory v `www/` jsou součástí deploymentu a dostupné přímo přes URL

---

## Důležité konvence

1. **Jazyky**: veškerý obsah (HTML, komentáře, commit messages) v **češtině**
2. **Verzování**: soubory mimo repozitář (`.docx`, samostatné `.html`) dostávají suffix `_v30`, `_v31` apod. Soubory v repozitáři mají pevné názvy.
3. **Konzistentnost stylu**: nové stránky/komponenty drží barvy a fonty definované výše — `panel-kdo-po-nas.html` je příklad druhé stránky se zachovanou identitou
4. **Bezpečnost**: `X-Frame-Options: SAMEORIGIN` — stránky nelze vkládat do iframu na cizích doménách
5. **JavaScript**: minimální, bez frameworků — automatické přepínání dnů podle aktuálního data (funkce `openCurrentOrNextDay`)

---

## Časté úkoly

### Aktualizace přednášky v programu
Edituj `index.html` — hledej sekci s příslušným dnem a časem, uprav text v `<div class="pres-title">` nebo `<div class="pres-authors">`. Stejnou změnu proveď v `generate_pdf.py` ve funkci `build_program()`.

### Přidání nové přednášky
V `index.html` přidej `<tr class="row-pres">` se správnou časovou buňkou. V `generate_pdf.py` přidej odpovídající `rows.append(row_pres(...))`.

### Vygenerování a odeslání PDF
Viz sekce „Generování PDF" výše. Po přidání App hesla do `.env` odkomentuj `send_pdf_email(dated_output)` na konci `generate_pdf.py`.

### Přidání nové stránky
Kopíruj strukturu `panel-kdo-po-nas.html` — zachovej navbar s odkazem zpět na `index.html`, stejný favicon (SVG kapka) a shodnou barevnou paletu.
