# Asset Microsoft Store — Franchetti Raw Converter Pro v2.58.1

Questa cartella contiene **tutto il materiale grafico** pronto per la scheda
Microsoft Store esistente (`XP9CJZTBCW6VS7`), insieme al testo già pronto in
[`../STORE_LISTING_MICROSOFT.md`](../STORE_LISTING_MICROSOFT.md).

Tutti gli screenshot sono **catture reali** dell'app 2.58.1 in esecuzione su
Windows 11, riprese con `PrintWindow` (nessun overlay di sistema, nessun
mockup, nessuna immagine generata con AI). Le foto visibili nell'anteprima
sono immagini libere di Unsplash usate come soggetti di prova.

---

## 1. Contenuto della cartella

```
store_assets/
├── screenshots/            9 immagini 1920x1080 (PNG, 16:9)
│   ├── 01_batch_1920x1080.png
│   ├── 02_anteprima_1920x1080.png
│   ├── 03_avanzate_1920x1080.png
│   ├── 04_preset_1920x1080.png
│   ├── 05_smartbatch_1920x1080.png
│   ├── 06_prestazioni_1920x1080.png
│   ├── 07_tethering_1920x1080.png
│   ├── 08_wifi_ftp_1920x1080.png
│   └── 09_log_1920x1080.png
├── hero/
│   └── hero_2340x1200.png  Immagine hero / banner (PNG)
├── logos/
│   ├── logo_300x300.png    Logo Store (formato richiesto)
│   ├── logo_1080x1080.png  Logo alta risoluzione (opzionale)
│   └── logo_2160x2160.png  Logo altissima risoluzione (opzionale)
└── README.md
```

**Formati e limiti rispettati**

| Asset | Dimensioni | Formato | Note |
|---|---|---|---|
| Screenshot | 1920×1080 | PNG | 16:9, entro il minimo 1366×768 |
| Hero | 2340×1200 | PNG | ratio 1.95:1 |
| Logo Store | 300×300 | PNG | sfondo trasparente |
| Logo grande | 1080×1080 / 2160×2160 | PNG | ricampionati dal logo 512 px |

---

## 2. Ordine consigliato degli screenshot

Il Partner Center mostra le immagini nell'ordine di caricamento. Carica in
questo ordine (i primi 4 sono quelli che vedono quasi tutti):

| # | File | Messaggio |
|---|---|---|
| 1 | `01_batch_1920x1080.png` | La schermata principale: batch RAW→JPEG con Prima/Dopo |
| 2 | `02_anteprima_1920x1080.png` | Anteprima grande, conversione bianco e nero |
| 3 | `03_avanzate_1920x1080.png` | Controllo di esposizione, toni e colore |
| 4 | `04_preset_1920x1080.png` | Preset, watermark, nomi file, LUT 3D |
| 5 | `05_smartbatch_1920x1080.png` | Smart Batch: analisi e correzioni per foto |
| 6 | `06_prestazioni_1920x1080.png` | Profili di prestazione e benchmark |
| 7 | `07_tethering_1920x1080.png` | Tethering multi-marca e Cloud |
| 8 | `08_wifi_ftp_1920x1080.png` | Wi-Fi FTP: scatto e anteprima |
| 9 | `09_log_1920x1080.png` | Log e diagnostica |

> Se vuoi caricarne solo 8, salta `09_log_1920x1080.png`: è utile ma è la meno
> visiva. Il minimo richiesto dal Microsoft Store è 4 screenshot.

---

## 3. Aggiornamento della scheda su Partner Center

La scheda esiste già: **non creare un nuovo prodotto** e **non serve un nuovo
pacchetto**. Si aggiornano solo testo e immagini della sottomissione esistente.

1. Apri <https://partner.microsoft.com/dashboard> e accedi con l'account
   publisher `FranchettiAcademy`.
2. Vai in **Apps and games** → **Franchetti Raw Converter Pro**
   (`XP9CJZTBCW6VS7`).
3. Apri la sottomissione in corso (o **Update** / **Aggiorna** sulla
   sottomissione pubblicata).
4. **Store listing / Informazioni sullo Store** (lingua `Italiano (Italia)`):
   - **Nome prodotto**: `Franchetti Raw Converter Pro` (non cambiarlo).
   - **Descrizione breve**: incolla il blocco da
     `STORE_LISTING_MICROSOFT.md` → *Descrizione breve*.
   - **Descrizione completa**: incolla il blocco *Descrizione completa*.
     Incolla come testo semplice: il Partner Center non interpreta Markdown.
   - **Novità della versione**: incolla il blocco *Novità della versione 2.58.1*.
   - **Caratteristiche principali**: incolla le 20 righe, una per voce.
   - **Parole chiave**: incolla le 7 righe, una per voce.
   - **Categoria**: `Foto e video` (o `Fotografia`, se disponibile).
   - **Sito web**: `https://franchettibiagio.github.io/raw-converter-pro/`
   - **Informativa sulla privacy**:
     `https://github.com/FranchettiBiagio/raw-converter-pro/blob/main/PRIVACY.md`
   - **Supporto**: `https://github.com/FranchettiBiagio/raw-converter-pro/issues`
     (in alternativa l'email `reportage@libero.it` già presente).
5. **Screenshot / Immagini dello Store**:
   - Elimina i 3 screenshot vecchi (non sono 16:9).
   - Carica i file `screenshots/01…09` nell'ordine della tabella.
   - Ogni immagine deve risultare 1920×1080: il Partner Center la accetta
     senza ritagli.
6. **Immagine hero** (se il campo è presente nella tua sottomissione):
   carica `hero/hero_2340x1200.png`.
7. **Logo / App icon** (se richiesto): carica `logos/logo_300x300.png`.
8. **Note sulla versione**: incolla l'URL
   `https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.58.1`
   oppure il testo breve delle note.
9. **Pacchetto**: lascia l'installer già presente
   (`WPM` / Inno Setup). Non serve ricaricarlo se la sottomissione punta già a
   `Franchetti_Raw_Converter_Setup_v2.58.1.exe`.
   - **App type**: EXE; **Architecture**: x64
   - **Package URL**:
     `https://github.com/FranchettiBiagio/raw-converter-pro/releases/download/v2.58.1/Franchetti_Raw_Converter_Setup_v2.58.1.exe`
   - **Installer parameters**:
     `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`
   - Dettagli e requisiti di firma: `STORE_SUBMISSION_REQUIREMENTS.md`
10. **Salva** → **Invia per la certificazione** (Submit for certification).

> ⚠️ **Firma obbligatoria.** Lo Store non ri-firma gli installer EXE/MSI:
> installer, EXE dell'app e uninstaller devono essere firmati con un
> certificato CA accreditato. Al momento i file sono `NotSigned`: senza firma
> la sottomissione viene rifiutata. La pipeline è pronta in
> `tools/sign_and_build.ps1`; per una persona fisica in Italia serve un
> certificato IV (`CODE_SIGNING_INDIVIDUAL_IT.md`), requisiti generali in
> `STORE_SUBMISSION_REQUIREMENTS.md`.

### Dopo l'invio

- La certificazione richiede in genere da alcune ore a 3 giorni lavorativi.
- Lo Store può richiedere modifiche: controlla l'email dell'account publisher.
- Quando è pubblicata, la pagina
  <https://apps.microsoft.com/detail/xp9cjztbcw6vs7> mostrerà i nuovi testi e
  i nuovi screenshot.

---

## 4. Controlli rapidi prima dell'invio

- [ ] Nome prodotto invariato: `Franchetti Raw Converter Pro`
- [ ] Descrizione breve ≤ 1.000 caratteri
- [ ] Descrizione completa ≤ 10.000 caratteri
- [ ] Caratteristiche: 20 voci, ciascuna ≤ 200 caratteri
- [ ] Parole chiave: 7 voci, ciascuna ≤ 30 caratteri
- [ ] Nessun Markdown incollato (niente `**`, `#`, backtick)
- [ ] Screenshot caricati in ordine, tutti 1920×1080
- [ ] Vecchi screenshot non 16:9 rimossi
- [ ] URL privacy e supporto aperti e raggiungibili
- [ ] Installer EXE/MSI già collegato alla sottomissione
- [ ] Età / classificazione invariata

---

## 5. Come sono stati prodotti gli asset

- Catture: app 2.58.1 avviata su Windows 11, finestra 1600×947, cattura
  `PrintWindow` client-only (`PW_CLIENTONLY | PW_RENDERFULLCONTENT`) per
  escludere overlay di sistema e barra del titolo.
- Composizione: `tools/build_store_assets.py` (PIL) aggiunge sfondo, titolo e
  card arrotondata, senza alterare il contenuto dell'interfaccia.
- Sorgenti grezze: `%TEMP%\opencode\store_shots\final_raw\`.
- Per rigenerare: `python tools/build_store_assets.py`.

Le foto di esempio nelle anteprime provengono da Unsplash (licenza Unsplash):
Alexander Shustov, Benjamin Combs, Roberto Nickson, Alexey Topolyanskiy,
Roksolana Zasiadko, Desi Mendoza, veeterzy. Non rappresentano clienti reali.
