# Franchetti Raw Converter Pro v2.58.0

[![Version](https://img.shields.io/badge/version-2.58.0-blue.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/actions)
[![Size](https://img.shields.io/badge/size-92%20MB-orange.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/releases)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

> **Guida completa:** [GUIDA_COMPLETA.md](GUIDA_COMPLETA.md) - ogni funzione spiegata in modo elementare, con le impostazioni consigliate per web, stampa, ritratto, paesaggio e foto notturne. Versione HTML: [docs/guida.html](docs/guida.html).

> **Enterprise RAW Suite** — Pipeline Y/Cb/Cr e denoise ISO, Tethering automatico multi-marca, Cloud Dispatch multi-canale, Watermark professionale, EXIF preservation. Portable, Open Source (MIT), Zero telemetria.

---

## 🧠 Smart Batch v2.58.0 — analisi e correzioni rapide

- **ANALIZZA FILE**: legge tutti i RAW/JPEG, misura esposizione, clipping, contrasto, colore, incarnati, rumore e ISO, poi propone un piano **diverso per ogni foto**.
- **Correzioni per file**: il batch unisce le impostazioni globali con i suggerimenti del singolo file; la casella **Usa correzioni per file** rende il piano opzionale.
- **Correzioni rapide**: **CONTRASTO NATURALE**, **SALVA LUCI**, **COLORE PIÙ RICCO**, **SOVRAESPOSTA**, **SOTTOESPOSTA** e **ANNULLA CORREZIONI**. Aggiornano gli slider esistenti e sono reversibili in blocco.
- **Protezione luci**: curva di spalla **C1** (Hermite) che comprime le alte luci senza perdere il punto bianco e senza scalini di pendenza. Non è un semplice abbassamento dell'esposizione.
- **Vivacità corretta**: la crominanza viene scalata attorno alla luminanza, quindi i toni spenti si arricchiscono davvero e i colori già saturi restano stabili.
- **Limite dichiarato**: se il RAW/JPEG è completamente bruciato, il dettaglio non esiste e non può essere recuperato.

---

## ⚡ Prestazioni adattive v2.58.0 — i core giusti, non tutti per forza

La finestra **PRESTAZIONI** si apre dal tab Batch, sotto `USA TUTTI I CORE`, e
legge dal PC i **core fisici**, i **core logici** e la **RAM libera** (API
Windows, senza `psutil`).

| Profilo | Core usati | Denoise / nitidezza | Quando usarlo |
|---------|-----------|---------------------|---------------|
| **Veloce** | tutti i core logici | più leggeri (70 / 80, nitidezza 0.70) | consegne rapide, social, anteprime |
| **Bilanciato** | core fisici | predefiniti (88 / 92, nitidezza 0.90) | uso quotidiano |
| **Massima qualità** | core fisici | più curati (95 / 96, nitidezza 1.10) | stampe, archivio, lavori finiti |

I profili non sono cosmetici: cambiano davvero il numero di processi e
l'intensità di denoise e nitidezza.

- **Numero processi automatico**: calcolato da core e RAM libera; lo slider
  permette di forzarlo quando serve.
- **Soglia multicore intelligente**: un pool multi-processo parte solo se il
  peso stimato del batch lo giustifica. Due JPEG minuscoli restano
  sequenziali; un batch di RAW pesanti usa tutti i processi disponibili.
- **BENCHMARK SUI MIEI FILE**: elabora 1–2 file reali in una cartella
  temporanea (gli originali sono solo letti) e misura il tempo vero.
- **Stima e avanzamento**: prima del batch mostra la durata prevista; durante
  la conversione la barra indica **file/min** ed **ETA** sul lavoro già fatto.
- **Override manuale rispettato**: se scegli tu il numero di processi, la
  scelta vince sull'euristica dei batch piccoli.

---

## 🖼️ Galleria cliente v2.58.0 — il cliente sceglie le foto

Ogni sessione FTP crea cartelle separate per **Originali**,
**Anteprime_Cliente** e **Galleria_Cliente**. Nella galleria viene scritto un
`index.html` autonomo, senza server e senza servizi esterni:

- miniature delle anteprime con caricamento `lazy`;
- caselle di selezione per ogni foto;
- **Seleziona tutte**, **Deseleziona**, **Copia selezione** e
  **Scarica elenco .txt**;
- contatore delle foto selezionate;
- funziona da cartella condivisa, chiavetta USB o allegato compresso.

La galleria si rigenera a ogni anteprima ricevuta e si apre dal tab
**Wi-Fi FTP**.

---

## © Copyright nei metadati EXIF/IPTC

Con l'interruttore **Scrivi copyright nei metadati EXIF/IPTC** il copyright non
resta solo sovrapposto all'immagine:

| Blocco | Campi scritti |
|--------|---------------|
| **EXIF** | `Artist`, `Copyright`, `ImageDescription` |
| **IPTC** | `By-line`, `Copyright Notice`, `Caption-Abstract`, `Object Name` |

Vale sia per il batch sia per le anteprime FTP. L'autore si imposta in
**AVANZATE**; il testo usa lo stesso campo del watermark e, se vuoto, il
predefinito `© Franchetti <anno>`. L'IPTC viene scritto direttamente nel blocco
APP13/Photoshop 3.0: nessuna dipendenza aggiuntiva.

---

## ☁️ Invio automatico opzionale

Nel tab **Wi-Fi FTP** un interruttore invia automaticamente le anteprime ai
canali cloud già attivi (Telegram/Dropbox) appena sono pronte. È **spento per
default**: nessun upload a sorpresa.

---

## ✨ Quick win di qualità e UX (v2.58.0)

- Anteprima PRIMA/DOPO con **`contain`**: le foto verticali non perdono più
  testa e piedi.
- Overlay FTP sempre con **Pillow**: `©`, accenti e Unicode corretti anche
  senza OpenCV.
- Testi lunghi troncati con ellissi, senza uscire dall'immagine.
- Log di `pyftpdlib` ridotti a WARNING e nessun messaggio duplicato nel tab
  **Log**.
- Cartelle FTP organizzate per sessione/data.
- Rimossa la variabile inutilizzata dell'anteprima.

---

## 🔌 Interfaccia 2.58.0 — una sola finestra per convertire

- La scheda **Sviluppo RAW** è stata rimossa: la schermata **Batch** contiene l'anteprima **PRIMA / DOPO** e le correzioni rapide.
- **AVANZATE** apre una finestra separata con tutti gli slider, curva tonale, split toning, nomi file, watermark e preset.
- L'anteprima decodifica il RAW una sola volta e riusa la base ridotta; l'originale non viene toccato.
- **APRI ANTEPRIMA GRANDE** mostra il confronto a piena finestra, ridimensionabile.

---

## 📶 Wi-Fi FTP v2.58.0 — scatta, invia, ricevi l'anteprima

La scheda **Wi-Fi FTP** accende un server FTP integrato (nessun software esterno):

| Voce | Valore |
|------|--------|
| **IP** | IP locale del PC, rilevato automaticamente |
| **Porta** | `2121` |
| **Utente** | `camera` |
| **Password** | `1234` |
| **Cartella originale** | `Immagini\FranchettiRawConverterPro\Tethering\Originali\<sessione>` |
| **Anteprime cliente** | `...\Tethering\Anteprime_Cliente\<sessione>` |
| **Galleria cliente** | `...\Tethering\Galleria_Cliente\<sessione>\index.html` |

Ogni avvio del server crea una **sessione** datata (`AAAA-MM-GG_HHMMSS`), così
i file di sessioni diverse non si mescolano. Ogni file completo viene sviluppato
con **WB e matrice camera**, Fujifilm con **AAHD 12** e gli altri marchi con
**AHD 3**, ridotto a **2000 px** sul lato lungo con Lanczos, sovrapposto con
**nome file** (sinistra) e **copyright/watermark** (destra) e salvato in
**JPEG qualità 85**. Se attivo, il copyright viene scritto anche nei metadati
**EXIF/IPTC**. La galleria HTML della sessione viene rigenerata a ogni
anteprima. Spegnendo l'interruttore il server viene chiuso e la porta liberata.

> **Compatibilità:** Nikon, Canon, Fujifilm e molti modelli Sony con FTP integrato inviano direttamente. I modelli senza client FTP usano l'app del produttore, la scheda o la cartella monitorata. Il Bluetooth non trasferisce RAW di alta qualità in modo universale: non viene simulato.

---

## 🎯 Caratteristiche Principali v2.58.0

### 🧠 **Nuova Pipeline Y/Cb/Cr e denoise ISO (Avanzata)**
| Fase | Descrizione | Controllo |
|------|-------------|-----------|
| **Sviluppo RAW** | **rawpy/LibRaw**, WB e matrice camera automatiche, **AHD** per Bayer e **AAHD 12** per Fujifilm X-Trans, output BGR pronto per OpenCV | `use_camera_wb` |
| **Contrasto Sigmoidale** | Curva logistica a "S" protegge luci/ombre senza clipping | `contrasto` 0.1–1.0 |
| **Vivacità Selettiva** | Satura solo toni spenti, preserva incarnati | `vivacita` 0.0–1.0 |
| **Y/Cb/Cr** | Luminanza (Y) e crominanza (Cb, Cr) separate, senza conversioni di colore costose | - |
| **Rimuovi grana ISO** | Guided filter Y/Cb/Cr + **non-local means solo nelle zone piatte**; crominanza a metà risoluzione; forza automatica dall'ISO | pulsante **RIMUOVI GRANA (AUTO ISO)**, attivo di default |
| **Nitidezza controllata** | Solo canale Y, con maschera e soglia sul rumore: niente grana amplificata | `raggio` 0.5–4.0, `quantità` 0.5–5.0 |
| **Output** | uint8 + profilo ICC sRGB embedded; default 3000 px / qualità 90 | `qualita_jpeg` 50–100 |

> **Novita' v2.58.0**: **Smart Batch** con analisi per file, piano di correzione opzionale, correzioni rapide reversibili e **protezione luci** con curva di spalla. Il ponte RAW **rawpy/LibRaw** resta alla base: WB e matrice colore della fotocamera, **AHD** per Bayer e **AAHD 12** per Fujifilm X-Trans.
>
> **Profilo predefinito (dalla 2.55.0)**: **3000 px / JPEG 90 / denoise automatico**, denoise ibrido (guided filter + non-local means solo nelle zone piatte), nitidezza protetta dal rumore. I file restano leggeri (in genere 0,6–1,3 MB) anche a 3000 px.

> **Perche' Y/Cb/Cr?** Lavorare sulla luminanza permette nitidezza e denoise senza aloni colorati; la crominanza, piu' sporca di rumore, viene pulita separatamente e a meta' risoluzione.

### 🚀 **Elaborazione Multi-Core adattiva (v2.58.0)**
- **Profili prestazioni**: Veloce (core logici), Bilanciato (core fisici) e Massima qualità, con denoise e nitidezza coerenti
- **Numero processi automatico**: calcolato da core fisici/logici e RAM libera; slider manuale disponibile
- **Soglia intelligente**: il pool `ProcessPoolExecutor` parte solo se peso e numero di file lo giustificano; i batch piccoli restano sequenziali, salvo override manuale
- **Benchmark reale**: misura 1–2 file dell'utente in una cartella temporanea e produce stima, **file/min** ed **ETA**
- **Limite di sicurezza**: il numero di processi si riduce automaticamente se la RAM libera non basta
- **Isolamento errori**: un file corrotto non blocca gli altri; ogni output viene scritto su file temporaneo e pubblicato solo a conversione completata
- **Annullamento immediato**: i processi in corso vengono terminati e i file parziali rimossi
- **Misura indicativa**: 4 RAW Sony A7S da 24 MP a **3000 px** con denoise automatico in **12,8 s** totali; JPEG da 0,6–0,9 MB. I preset a risoluzione originale (Stampa Fine Art / Archivio) richiedono circa 40-45 s per foto perché il denoise non-locale lavora anche a 24 MP.

### 📡 **Tethering automatico multi-marca — Hot-Folder (v2.58.0)**
- **Tutte le marche**: Canon, Nikon, Fujifilm, Panasonic, OM System, Leica e altre. Usa il software di tethering del produttore e monitora la sua cartella di destinazione.
- **Sony**: oltre all'hot-folder è disponibile il controllo Wi-Fi diretto (Smart Remote Control).
- **Watchdog Observer** monitora cartella in tempo reale (`watchdog` library)
- **Formati rilevati**: RAW (`.arw, .cr2, .cr3, .nef, .raf, .dng, .orf, .rw2`, …) e immagini standard (`.jpg, .jpeg, .png, .tif, .tiff, .webp`)
- **Attesa scrittura**: il file viene elaborato solo quando la dimensione resta stabile
- **Anti-loop**: ignora la cartella di output e i file `_PRO`
- **Workflow**: Scatta → Software produttore/hot-folder → Pipeline Y/Cb/Cr completa → immagine `_PRO` → Cloud Dispatch → Notifica GUI live

### ☁️ **Cloud Dispatch**
| Canale | Stato | Configurazione UI |
|--------|-------|-------------------|
| **Telegram** | ✅ Operativo (`sendPhoto`) | Bot Token + Chat ID |
| **Dropbox** | ✅ Operativo (`files/upload`) | Access Token |
| **Google Drive** | ⚠️ Predisposto, non attivo in questa versione | API Key / Folder ID |
| **Meta (IG/FB)** | ⚠️ Predisposto, non attivo in questa versione | Access Token + Account ID |
| **SwissTransfer** | ⚠️ Predisposto, non attivo in questa versione | Email |

Telegram e Dropbox vengono eseguiti al completamento di ogni elaborazione; i canali non attivi vengono saltati senza generare errori.

### 🏷️ **Watermark Professionale Proporzionale**
- **Scaling intelligente**: Logo al 15% lato lungo, ridimensionamento Lanczos
- **Alpha compositing**: Fusione canale alpha nativo, opacità configurabile (0–1)
- **Posizione**: 5 posizioni (basso/alto a destra o sinistra, centro) con margine proporzionale
- **Formato**: PNG trasparente richiesto

### 🔧 **EXIF Preservation & Copyright nei metadati**
- Estrazione blocchi EXIF binari originali (piexif)
- Correzione `Orientation = 1` (rotazione corretta)
- Preservazione GPS, impostazioni camera, timestamp
- Iniezione in JPEG finale post-elaborazione
- **Copyright EXIF**: `Artist`, `Copyright`, `ImageDescription`
- **Copyright IPTC**: `By-line`, `Copyright Notice`, `Caption-Abstract`, `Object Name` scritti direttamente in APP13/Photoshop 3.0, senza dipendenze aggiuntive

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

*Basato su **rawpy/LibRaw 0.21+**: usa **AHD** (qualità 3) per i sensori Bayer e **AAHD** (qualità 12) per Fujifilm X-Trans; WB e matrice colore vengono letti dalla fotocamera. Il Log indica algoritmo e fallback usati.*

---

### ⚙️ **Elaborazione Batch Enterprise**
- **Ricorsivo**: Cartella radice + tutte le sotto-cartelle (la cartella di output viene esclusa)
- **Multi-core adattivo**: profili Veloce/Bilanciato/Massima qualità, processi automatici da core e RAM, override manuale; pool solo quando il batch lo giustifica
- **GUI reattiva**: Coda thread-safe, progress bar real-time con **file/min** ed **ETA**, conteggio OK/Errori/Saltati, annullamento immediato
- **Nominazione**: Mantieni originale / Prefisso e suffisso personalizzati / Anti-collisione (`_1`, `_2`…) / Salta / Sovrascrivi
- **Robustezza**: parametri di configurazione ripuliti automaticamente; un file corrotto non interrompe il batch

### 🎨 **Enterprise Dark GUI (CustomTkinter)**
| Tab | Contenuto |
|-----|-----------|
| **Batch** | Sorgente/destinazione, anteprima PRIMA/DOPO, correzioni rapide, preset dimensioni, qualità, formato, EXIF, pannello **PRESTAZIONI**, avvio/annullamento e progresso con ETA |
| **AVANZATE** | Finestra separata: slider completi (tono, colore, dettaglio, effetti), curva tonale, split toning, nomi, watermark, logo, preset, autore copyright |
| **Wi-Fi FTP** | Interruttore server FTP, IP/porta/credenziali, sessione, cartelle Originali/Anteprime/Galleria, copyright EXIF/IPTC, invio automatico cloud |
| **Tethering & Cloud** | Cartella multi-marca, avvio monitoraggio, connessione Sony A7S, scatto e scarica, credenziali cloud |
| **Log** | Console con timestamp, color-coding, svuota e salva log |

---

## 🚀 Quick Start

### Download v2.58.0
| Metodo | Link |
|--------|------|
| **GitHub Releases** | [Download v2.58.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.58.0) |
| **Portable (consigliato)** | [FranchettiRawConverterPro.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe) |
| **Installer Windows** | [Setup v2.58.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/Franchetti_Raw_Converter_Setup_v2.58.0.exe) |
| **FileCR** | [FileCR Page](https://filecr.com/windows/franchetti-raw-converter-pro/) |
| **Itch.io** | [Itch.io Page](https://franchetti.itch.io/franchetti-raw-converter-pro) |
| **SourceForge** | [SourceForge Project](https://sourceforge.net/projects/franchetti-raw-converter-pro/) |

### Esegui
```cmd
# Nessuna installazione richiesta
FranchettiRawConverterPro.exe
```

### Workflow Base
1. **Avvia** l'applicazione
2. **Tab Batch**: scegli sorgente e destinazione; il profilo predefinito è **3000 px, JPEG 90, denoise automatico** (puoi scegliere "Originale" per la stampa)
3. **Opzioni**: prefisso/suffisso, watermark, EXIF, **PIÙ LUMINOSA**, **RIMUOVI GRANA (AUTO ISO)** e **USA TUTTI I CORE** (attivi di default)
4. **AVVIA CONVERSIONE**: il batch sceglie automaticamente quanti processi usare; la barra mostra OK, errori, saltati, file/min ed ETA
5. **AVANZATE**: regola tono, colore, dettaglio ed effetti con gli slider, imposta nomi, watermark e autore copyright, applica i preset
6. **Wi-Fi FTP**: accendi l'interruttore e inserisci nella fotocamera IP, porta `2121`, utente `camera`, password `1234`; le anteprime e la galleria finiscono nella sessione corrente
7. **Tethering & Cloud**: monitora la cartella del software Canon/Nikon/Fujifilm/Panasonic/OM System/Leica oppure connetti la Sony A7S; Telegram/Dropbox inviano l'output

---

## 📋 Requisiti di Sistema v2.58.0

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| **OS** | Windows 10 1809+ | Windows 11 24H2+ |
| **Architettura** | x64 | x64 |
| **RAM** | 2 GB | 8 GB+ |
| **Disco** | 150 MB liberi | 1 GB+ liberi (SSD per batch) |
| **CPU** | Qualsiasi x64 | Multi-core (i5/Ryzen 5+) |
| **Display** | 1024×768 | 1920×1080+ |
| **Rete** | Solo per Wi-Fi FTP e Cloud | LAN Wi-Fi/Ethernet per il tethering |

*Singolo `.exe` ~92 MB (include OpenCV headless per la ricezione FTP). Nessun .NET Framework, VC++ Redistributables o diritti admin richiesti.*

---

## 🏗️ Architettura v2.58.0

```
┌─────────────────────────────────────────────────────────────┐
│              FranchettiRawConverterPro.exe                  │
│  (PyInstaller --onefile --windowed, ~92 MB)                 │
├─────────────────────────────────────────────────────────────┤
│  GUI Layer (CustomTkinter - Dark Mode)                      │
│  ├── Tab Batch: preset, formati, anteprima, correzioni      │
│  ├── PRESTAZIONI: profili, core, RAM, slider, benchmark     │
│  ├── AVANZATE: slider completi, nomi, watermark, preset     │
│  ├── Tab Wi-Fi FTP: sessione, anteprime, galleria cliente   │
│  ├── Tab Tethering & Cloud: multi-marca, Sony, cloud        │
│  └── Tab Log: timestamp, color-coding, auto-scroll          │
├─────────────────────────────────────────────────────────────┤
│  ImageEngine                                                │
│  ├── rawpy/LibRaw — AHD/AAHD 12, WB e matrice camera        │
│  ├── scikit-image — Y/Cb/Cr, guided filter, non-local means │
│  ├── Nitidezza controllata su canale Y (soglia rumore)      │
│  ├── Pillow — Watermark alpha composite, JPEG/PNG/TIFF/WEBP │
│  ├── piexif — EXIF extraction, injection e copyright        │
│  ├── IPTC — scrittura diretta APP13/Photoshop 3.0           │
│  ├── Galleria cliente — index.html autonomo con checkbox    │
│  └── NumPy — Array bridge float32                           │
├─────────────────────────────────────────────────────────────┤
│  Elaborazione parallela adattiva                            │
│  ├── ProcessPoolExecutor con profili Veloce/Bilanciato/Qual.│
│  ├── Soglia multicore su peso e numero file                 │
│  ├── Benchmark reale, stima, file/min ed ETA                │
│  ├── Scrittura atomica: file .tmp + os.replace              │
│  └── Annullamento: terminate dei processi figli             │
├─────────────────────────────────────────────────────────────┤
│  Background Services                                        │
│  ├── RawHotFolderHandler (watchdog.Observer)                │
│  │   └── on_created/on_moved → attesa dimensione → Engine   │
│  └── CloudDispatcher                                        │
│      ├── Telegram Bot API (operativo)                       │
│      ├── Dropbox API (operativo)                            │
│      └── Google Drive / Meta / SwissTransfer (predisposti)  │
└─────────────────────────────────────────────────────────────┘
```

### Dipendenze (bundled in .exe)

| Libreria | Versione | Scopo |
|----------|----------|-------|
| **rawpy** | 0.27+ | LibRaw Python bindings (AHD, AAHD 12 per X-Trans, WB e matrice camera) |
| **LibRaw** | 0.21+ | RAW decoding C++ |
| **scikit-image** | 0.24+ | Y/Cb/Cr, guided filter, non-local means, nitidezza controllata |
| **customtkinter** | 5.2+ | Modern Dark GUI |
| **watchdog** | 4.0+ | Filesystem events |
| **Pillow** | 12.3+ | Imaging, Watermark, JPEG |
| **piexif** | 1.1+ | EXIF binary manipulation e copyright |
| **pyftpdlib** | 2.0+ | Server FTP integrato (Wi-Fi FTP) |
| **OpenCV headless** | 4.10+ | Pipeline BGR, resize e overlay FTP |
| **requests** | 2.31+ | REST API calls |
| **NumPy** | 2.5+ | Array operations float32 |

---

## 🔒 Privacy & Sicurezza (by design)

| Caratteristica | Franchetti Raw Converter Pro v2.58.0 |
|----------------|--------------------------------------|
| **Rete** | Solo se attivi Cloud Dispatch o Wi-Fi FTP (opzionali, espliciti) |
| **Telemetria** | ❌ Nessuna |
| **Crash reporting** | ❌ Nessuno |
| **Aggiornamenti auto** | ❌ Manuali |
| **Registro Windows** | ❌ Mai scritto |
| **Dati personali** | ❌ Mai raccolti |
| **File originali** | ✅ Solo lettura, mai modificati |

Vedi [PRIVACY.md](PRIVACY.md) e [SECURITY.md](SECURITY.md) per dettagli.

---

## 📖 Documentazione

| Documento | Descrizione |
|-----------|-------------|
| [Guida Completa Illustrata](GUIDA_COMPLETA.md) | **Tutte le funzioni spiegate in modo elementare + impostazioni consigliate** |
| [Guida Completa in HTML](docs/guida.html) | Versione web della guida, stampabile |
| [Manuale Utente](USER_MANUAL.md) | Guida completa con screenshot |
| [Specifiche Tecniche](TECHNICAL_SPECS.md) | Architettura, algoritmi, formati |
| [Guida Installazione](INSTALLATION_GUIDE.md) | Deployment enterprise (GPO, Intune) |
| [FAQ](FAQ.md) | Domande frequenti & troubleshooting |
| [Changelog](CHANGELOG.md) | Storico versioni (v2.58.0) |
| [Privacy Policy](PRIVACY.md) | Zero data collection |
| [Security Policy](SECURITY.md) | Responsible disclosure |
| [Release Notes](RELEASE_NOTES.md) | Note complete v2.58.0 |

---

## 🛠️ Building from Source

### Prerequisiti
```cmd
# Python 3.12+ richiesto
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

### Build
```cmd
python build_exe.py
# Output: dist/FranchettiRawConverterPro.exe (~92 MB)
```

### Sviluppo
```cmd
python main.py  # Esegui da sorgente
```

---

## 🤝 Contributing

Contributi benvenuti! Leggi [CONTRIBUTING.md](CONTRIBUTING.md) per linee guida.

### Setup Sviluppo
1. Fork repository
2. Crea feature branch: `git checkout -b feature/amazing-feature`
2. Commit: `git commit -m 'Add amazing feature'`
3. Push: `git push origin feature/amazing-feature`
4. Apri Pull Request

---

## 📄 Licenza

Distribuito sotto licenza **MIT**. Vedi [LICENSE](LICENSE) per testo completo.

```
Copyright (c) 2024-2026 Franchetti

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🙏 Ringraziamenti

- **LibRaw Team** - Eccezionale libreria decodifica RAW
- **rawpy Maintainers** — Binding Python per LibRaw
- **scikit-image Team** — Elaborazione Y/Cb/Cr professionale
- **CustomTkinter** — Modern Dark UI framework
- **Watchdog** — Filesystem events cross-platform
- **Pillow Contributors** — Imaging library robusta
- **Python Software Foundation** — Runtime solido

---

## 📞 Supporto v2.58.0

| Canale | Scopo |
|--------|-------|
| **GitHub Issues** | Bug reports, crash, feature request |
| **GitHub Discussions** | Domande, workflow, tips |
| **Email** | `support@franchetti.dev` (security, licensing) |

---

## 📊 Statistiche v2.58.0

| Metrica | Valore |
|---------|--------|
| **Lines of Code** | ~7.400 (Python monolitico) |
| **Dimensione Executable** | ~92 MB |
| **Avvio** | ~5–10 s (estrazione onefile) |
| **Velocità Conversione** | ~2 MP/s per core; pool adattivo fino a tutti i core fisici |
| **Memoria** | ~300 MB–1,5 GB per processo (RAW 24 MP) |

---

<div align="center">

**Made with ❤️ per fotografi professionisti da Franchetti**

**v2.58.0 - 2 Novembre 2026**

[![GitHub](https://img.shields.io/badge/GitHub-FranchettiBiagio%2Fraw--converter--pro-181717?logo=github)](https://github.com/FranchettiBiagio/raw-converter-pro)
[![Download](https://img.shields.io/badge/Download-v2.58.0-0066cc?logo=github)](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.58.0)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>
