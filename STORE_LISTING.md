# Scheda Negozio uptodown.dev / FileCR / Itch.io / SourceForge

**Franchetti Raw Converter Pro v2.55.0**  
*Convertitore RAW professionale Enterprise per Windows — Pipeline Y/Cb/Cr, Tethering multi-marca, Cloud Dispatch*

---

## Titolo Breve (max 80 caratteri)
**Franchetti Raw Converter Pro - RAW → JPEG Pipeline Y/Cb/Cr, Tethering, Cloud**

## Descrizione Breve (max 300 caratteri)
Suite Enterprise per sviluppo RAW (25+ formati) con pipeline Y/Cb/Cr (contrasto sigmoidale, vivacità selettiva, nitidezza su canale L), tethering automatico multi-marca (hot-folder), watermark proporzionale, EXIF preservation e dispatch cloud simultaneo (Telegram, Google Drive, Meta). Portable, MIT license.

---

## Descrizione Completa (Markdown)

### 🎯 **Per fotografi professionisti e studi che vogliono controllo totale e automazione**

Franchetti Raw Converter Pro v2.55.0 è una **suite Enterprise completa** che trasforma file RAW in JPEG ottimizzati attraverso una **pipeline matematica in spazio Y/Cb/Cr**, con automazione **tethering multi-marca** e **distribuzione cloud multi-canale** integrata. Tutto in un singolo eseguibile portable (~78 MB), open source (MIT), zero telemetria.

---

### 📸 **Formati RAW Supportati (25+)**

| Marchio | Estensioni |
|---------|------------|
| **Sony** | ARW, SRF, SR2 |
| **Canon** | CR2, CR3, CRW |
| **Nikon** | NEF, NRW |
| **Fujifilm** | RAF |
| **Olympus/OM System** | ORF |
| **Panasonic** | RW2, RAW |
| **Universale** | DNG |
| **Altri** | PEF, SRW, X3F, 3FR, FFF, RWL, DCR, K25, KDC, MOS, MRW |

*Basato su **LibRaw 0.21+** con algoritmo **AMaZE** per demosaicing di massima qualità.*

---

### 🧠 **Nuova Pipeline Y/Cb/Cr (v2.55.0)**

| Fase | Descrizione | Parametro |
|------|-------------|-----------|
| **1. Sviluppo RAW** | LibRaw nativo, demosaic AMaZE, WB camera, sRGB 8-bit | `use_camera_wb` |
| **2. Normalizzazione** | Float32 [0,1] per calcolo matematico puro | — |
| **3. Contrasto Sigmoidale** | Curva logistica a "S" protegge luci/ombre | `contrasto` 0.1–1.0 |
| **4. Vivacità Selettiva** | Satura solo toni spenti, preserva incarnati | `vivacita` 0.0–1.0 |
| **5. RGB → Y/Cb/Cr** | Separazione Luminanza (Y) / Crominanza (Cb,Cr) | — |
| **6. Denoise ibrido** | Guided filter + non-local means solo nelle zone piatte | `nr_luminanza` 88, `nr_colore` 92 |
| **7. Nitidezza controllata Y** | Solo canale Y, soglia sul rumore, zero aloni colorati | `raggio` 0.5–4.0, `quantità` 0.5–5.0 |
| **8. Y/Cb/Cr → RGB** | Riconversione corretta | — |
| **9. Quantizzazione** | uint8 + profilo ICC sRGB embedded | `qualita_jpeg` 50–100 |

**Vantaggio Y/Cb/Cr**: Luminanza e crominanza separate → nitidezza pura su dettaglio, zero artefatti cromatici.

---

### 📡 **Tethering automatico multi-marca — Hot-Folder (v2.55.0)**

| Funzione | Dettaglio |
|----------|-----------|
| **Monitoraggio** | `watchdog` Observer su cartella configurata |
| **Formati rilevati** | `.arw, .cr2, .cr3, .nef, .raf, .dng, .orf, .rw2` |
| **Buffer rete** | 1.5s delay per completamento scrittura wireless |
| **Elaborazione** | Pipeline completa automatica al rilevamento file |
| **Output** | `{nome}_PRO.jpg` in `Output_Ottimizzati/` |
| **Log live** | Console GUI con timestamp real-time |

**Workflow**: Scatta → File arriva via Wi-Fi → Elaborazione Y/Cb/Cr → JPEG + Watermark + EXIF → Cloud Dispatch → Notifica GUI.

---

### ☁️ **Cloud Dispatch Multi-Canale Simultaneo**

| Canale | API | Configurazione UI |
|--------|-----|-------------------|
| **Telegram** | Bot API `sendPhoto` | Bot Token + Chat ID |
| **Google Drive** | Drive API v3 multipart | Folder ID / API Key |
| **Meta (IG/FB)** | Graph API `media_publish` | Access Token + Account ID |

Tutti e tre i canali vengono attivati **in parallelo** al completamento di ogni elaborazione.

---

### 🏷️ **Watermark Professionale Proporzionale**

- **Scaling intelligente**: Logo al 15% lato lungo, ridimensionamento Lanczos
- **Alpha compositing**: Fusione canale alpha nativo, opacità configurabile (0–1)
- **Posizione**: Basso-destra con margine 20px
- **Formato logo**: PNG trasparente (richiesto)

---

### 🔧 **EXIF Preservation**

- Estrazione blocchi EXIF binari originali (piexif)
- Correzione `Orientation = 1` (rotazione corretta)
- Preservazione GPS, impostazioni camera, timestamp
- Iniezione in JPEG finale post-elaborazione

---

### ⚙️ **Elaborazione Batch Enterprise**

- **Ricorsivo**: Cartella radice + tutte le sotto-cartelle
- **Multi-thread**: `ProcessPoolExecutor` per throughput massimo
- **GUI reattiva**: Coda thread-safe, progress bar real-time, cancellabile
- **Nominazione**: Mantieni originale / Prefisso personalizzato / Anti-collisione (`_1`, `_2`…)

---

### 💻 **Enterprise Dark GUI (CustomTkinter)**

| Area | Contenuto |
|------|-----------|
| **Sinistra** | Pipeline Y/Cb/Cr: Slider Contrasto, Vivacità, Nitidezza (live update) |
| | Watermark: Carica logo PNG, preview path |
| **Destra** | Tethering: Selezione cartella tethering/hot-folder, Avvia/Disattiva monitoraggio |
| | Cloud: Campi Token/ID per Telegram, Google Drive, Meta |
| **Basso** | Console Log: Timestamp, color-coding, auto-scroll |

---

### 🔒 **Privacy & Sicurezza (by design)**

| Cosa | Franchetti Raw Converter Pro v2.55.0 |
|------|--------------------------------------|
| **Rete** | Solo se attivi Cloud Dispatch (opzionale) |
| **Telemetria** | ❌ Nessuna |
| **Crash reporting** | ❌ Nessuno |
| **Aggiornamenti auto** | ❌ Manuali |
| **Registro Windows** | ❌ Mai scritto |
| **Dati personali** | ❌ Mai raccolti |
| **File originali** | ✅ Solo lettura, mai modificati |

### Requisiti di Sistema v2.55.0

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| **OS** | Windows 10 1809+ | Windows 11 24H2+ |
| **Architettura** | x64 | x64 |
| **RAM** | 2 GB | 8 GB+ |
| **Disco** | 100 MB liberi | 1 GB+ liberi (SSD) |
| **CPU** | Qualsiasi x64 | Multi-core (i5/Ryzen 5+) |

---

## 📥 **Download e Installazione**

**Nessuna installazione richiesta — Portable al 100%:**

1. Scarica `FranchettiRawConverterPro.exe` (~78 MB)
2. Doppio clic per avviare
3. (Opzionale) Crea collegamento su Desktop/Menu Start

*Windows SmartScreen al primo avvio: "Ulteriori informazioni" → "Esegui comunque"*

---

## 📚 **Documentazione Completa**

- [Manuale Utente](USER_MANUAL.md) — Guida passo-passo con screenshot
- [Specifiche Tecniche](TECHNICAL_SPECS.md) — Architettura, benchmark, formati
- [Guida Installazione](INSTALLATION_GUIDE.md) — Deployment enterprise (GPO, Intune)
- [FAQ](FAQ.md) — Risposte alle domande frequenti
- [Changelog](CHANGELOG.md) — Storico versioni (v2.55.0)
- [Privacy Policy](PRIVACY.md) — Zero data collection
- [Security Policy](SECURITY.md) — Responsible disclosure

---

## 🏷️ **Tag/Parole Chiave (SEO)**

`raw converter` `raw to jpeg` `batch image converter` `copyright watermark` `ycbcr color pipeline` `tethering wifi` `hot folder` `cloud automation` `sony arw` `canon cr3` `nikon nef` `fujifilm raf` `olympus orf` `photography software` `portable` `no-install` `privacy` `open source` `mit license` `italian` `franchetti`

---

## 📂 **Categoria**

**Fotografia > Strumenti di conversione**  
**Utility > Elaborazione immagini**  
**Developer Tools > Image Processing**

---

## 🌐 **Lingue**

- Italiano (GUI completa + documentazione)
- Inglese (documentazione tecnica)

---

## 💰 **Licenza**

**MIT License** — Gratuito per uso personale e commerciale.  
Attribuzione apprezzata: *"Franchetti Raw Converter Pro by Franchetti"*

---

## 🔗 **Link Ufficiali**

- **Sito web / GitHub Pages**: https://franchettibiagio.github.io/raw-converter-pro/
- **GitHub Repository**: https://github.com/FranchettiBiagio/raw-converter-pro
- **Release / Download**: https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.55.0
- **Direct Download**: https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe
- **FileCR**: https://filecr.com/windows/franchetti-raw-converter-pro/
- **Itch.io**: https://franchetti.itch.io/franchetti-raw-converter-pro
- **SourceForge**: https://sourceforge.net/projects/franchetti-raw-converter-pro/
- **Segnalazione bug**: https://github.com/FranchettiBiagio/raw-converter-pro/issues
- **Sicurezza**: security@franchetti.dev

---

## 📸 **Screenshot Richiesti (per uptodown.dev / FileCR / Itch.io)**

| # | Screenshot | Descrizione |
|---|------------|-------------|
| 1 | **Schermata principale** | GUI dual-colonna completa (Pipeline Y/Cb/Cr + Tethering/Cloud) |
| 2 | **Pipeline Y/Cb/Cr** | Slider Contrasto, Vivacità, Nitidezza + Watermark |
| 3 | **Tethering & Cloud** | Cartella tethering/hot-folder, Token API, Pulsante Avvia Monitoraggio |
| 4 | **Elaborazione Live** | Hot-folder rilevamento → Log console real-time |
| 5 | **Watermark dettaglio** | Zoom angolo basso-destra con logo proporzionale |
| 6 | **Risultato** | Esplora risorse con JPEG `_PRO.jpg` generati |

*Risoluzione consigliata: 1920×1080 (16:9), formato PNG, <500KB cadauno*

---

## 📋 **Checklist Pubblicazione (tutti gli store)**

- [x] Titolo ottimizzato SEO (v2.55.0 + keywords)
- [x] Descrizione breve < 300 caratteri
- [x] Descrizione completa Markdown con feature highlights
- [x] Tag/keywords pertinenti (25+ termini)
- [x] Categoria corretta (Photography > Conversion Tools)
- [x] Requisiti sistema chiari (min/consigliato)
- [x] Licenza specificata (MIT)
- [x] Link ufficiali (GitHub, Releases, Sito, Bugs)
- [x] Privacy/Security policy linkate
- [x] Screenshot preparati (6 richiesti)
- [x] File `.exe` testato su Windows 10/11 pulito
- [x] SHA-256 verificato e documentato
- [x] Nessun falso positivo antivirus (VirusTotal 0/70+)
- [x] UPX compression attiva (~78 MB)
- [x] Version metadata embedded (v2.55.0.0)

---

*Scheda pronta per copia-incolla su uptodown.dev, FileCR, Itch.io, SourceForge — Gennaio 2025 (v2.55.0)*