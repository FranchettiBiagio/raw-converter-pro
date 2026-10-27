# Franchetti Raw Converter Pro v2.55.0

[![Version](https://img.shields.io/badge/version-2.55.0-blue.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/actions)
[![Size](https://img.shields.io/badge/size-62%20MB-orange.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/releases)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

> **Guida completa:** [GUIDA_COMPLETA.md](GUIDA_COMPLETA.md) - ogni funzione spiegata in modo elementare, con le impostazioni consigliate per web, stampa, ritratto, paesaggio e foto notturne. Versione HTML: [docs/guida.html](docs/guida.html).

> **Enterprise RAW Suite** — Pipeline Y/Cb/Cr e denoise ISO, Tethering automatico multi-marca, Cloud Dispatch multi-canale, Watermark professionale, EXIF preservation. Portable, Open Source (MIT), Zero telemetria.

---

## 🎯 Caratteristiche Principali v2.55.0

### 🧠 **Nuova Pipeline Y/Cb/Cr e denoise ISO (Avanzata)**
| Fase | Descrizione | Controllo |
|------|-------------|-----------|
| **Sviluppo RAW** | LibRaw nativo, demosaic **AMaZE** con fallback automatico AHD/PPG/LINEAR, WB camera, sRGB 8-bit | `use_camera_wb` |
| **Contrasto Sigmoidale** | Curva logistica a "S" protegge luci/ombre senza clipping | `contrasto` 0.1–1.0 |
| **Vivacità Selettiva** | Satura solo toni spenti, preserva incarnati | `vivacita` 0.0–1.0 |
| **Y/Cb/Cr** | Luminanza (Y) e crominanza (Cb, Cr) separate, senza conversioni di colore costose | - |
| **Rimuovi grana ISO** | Guided filter Y/Cb/Cr + **non-local means solo nelle zone piatte**; crominanza a metà risoluzione; forza automatica dall'ISO | pulsante **RIMUOVI GRANA (AUTO ISO)**, attivo di default |
| **Nitidezza controllata** | Solo canale Y, con maschera e soglia sul rumore: niente grana amplificata | `raggio` 0.5–4.0, `quantità` 0.5–5.0 |
| **Output** | uint8 + profilo ICC sRGB embedded; default 3000 px / qualità 90 | `qualita_jpeg` 50–100 |

> **Novita' v2.55.0**: profilo predefinito **3000 px / JPEG 90 / denoise automatico**, **denoise ibrido** (guided filter + non-local means solo nelle zone piatte), **nitidezza protetta dal rumore**, preset aggiornati, **RIMUOVI GRANA** spostato subito sotto **PIU' LUMINOSA** e tethering multi-marca. I file restano leggeri (in genere 0,6–1,3 MB) anche a 3000 px.

> **Perche' Y/Cb/Cr?** Lavorare sulla luminanza permette nitidezza e denoise senza aloni colorati; la crominanza, piu' sporca di rumore, viene pulita separatamente e a meta' risoluzione.

### 🚀 **Elaborazione Multi-Core (v2.55.0)**
- **Tutti i core logici**: `ProcessPoolExecutor` con un processo per core disponibile
- **Limite di sicurezza**: il numero di processi si riduce automaticamente se la RAM libera non basta
- **Isolamento errori**: un file corrotto non blocca gli altri; ogni output viene scritto su file temporaneo e pubblicato solo a conversione completata
- **Annullamento immediato**: i processi in corso vengono terminati e i file parziali rimossi
- **Misura reale (v2.55.0)**: 4 RAW Sony A7S da 24 MP a **3000 px** con denoise automatico in **12,8 s** totali; JPEG da 0,6–0,9 MB. I preset a risoluzione originale (Stampa Fine Art / Archivio) richiedono circa 40-45 s per foto perché il denoise non-locale lavora anche a 24 MP.

### 📡 **Tethering automatico multi-marca — Hot-Folder (v2.55.0)**
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

### 🔧 **EXIF Preservation**
- Estrazione blocchi EXIF binari originali (piexif)
- Correzione `Orientation = 1` (rotazione corretta)
- Preservazione GPS, impostazioni camera, timestamp
- Iniezione in JPEG finale post-elaborazione

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

*Basato su **LibRaw 0.21+**: usa **AMaZE** quando incluso nella build, altrimenti ripiega automaticamente su **AHD**, **PPG** o **LINEAR** (il Log indica l'algoritmo usato).*

---

### ⚙️ **Elaborazione Batch Enterprise**
- **Ricorsivo**: Cartella radice + tutte le sotto-cartelle (la cartella di output viene esclusa)
- **Multi-core**: `ProcessPoolExecutor` su tutti i core logici, con limite basato sulla RAM libera
- **GUI reattiva**: Coda thread-safe, progress bar real-time, conteggio OK/Errori/Saltati, annullamento immediato
- **Nominazione**: Mantieni originale / Prefisso e suffisso personalizzati / Anti-collisione (`_1`, `_2`…) / Salta / Sovrascrivi
- **Robustezza**: parametri di configurazione ripuliti automaticamente; un file corrotto non interrompe il batch

### 🎨 **Enterprise Dark GUI (CustomTkinter)**
| Tab | Contenuto |
|-----|-----------|
| **Batch** | Sorgente/destinazione, preset dimensioni, qualità, formato, nomi, watermark, EXIF, PIÙ LUMINOSA, multi-core, avvio/annullamento e progresso |
| **Sviluppo RAW** | Slider completi (tono, colore, dettaglio, Lab, effetti), colore ombre/luci, logo, anteprima |
| **Tethering & Cloud** | Cartella multi-marca, avvio monitoraggio, connessione Sony A7S, scatto e scarica, credenziali cloud |
| **Log** | Console con timestamp, color-coding, svuota e salva log |

---

## 🚀 Quick Start

### Download v2.55.0
| Metodo | Link |
|--------|------|
| **GitHub Releases** | [Download v2.55.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.55.0) |
| **Portable (consigliato)** | [FranchettiRawConverterPro.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe) |
| **Installer Windows** | [Setup v2.55.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/Franchetti_Raw_Converter_Setup_v2.55.0.exe) |
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
4. **AVVIA CONVERSIONE**: i file vengono elaborati in parallelo su tutti i core; la barra mostra OK, errori e saltati
5. **Tab Sviluppo RAW**: regola tono, colore, dettaglio ed effetti con gli slider e applica i preset
6. **Tab Tethering & Cloud**: monitora la cartella del software Canon/Nikon/Fujifilm/Panasonic/OM System/Leica oppure connetti la Sony A7S; Telegram/Dropbox inviano l'output

---

## 📋 Requisiti di Sistema v2.55.0

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| **OS** | Windows 10 1809+ | Windows 11 24H2+ |
| **Architettura** | x64 | x64 |
| **RAM** | 2 GB | 8 GB+ |
| **Disco** | 100 MB liberi | 1 GB+ liberi (SSD per batch) |
| **CPU** | Qualsiasi x64 | Multi-core (i5/Ryzen 5+) |
| **Display** | 1024×768 | 1920×1080+ |

*Singolo `.exe` ~78 MB. Nessun .NET Framework, VC++ Redistributables o diritti admin richiesti.*

---

## 🏗️ Architettura v2.55.0

```
┌─────────────────────────────────────────────────────────────┐
│              FranchettiRawConverterPro.exe                  │
│  (PyInstaller --onefile --windowed, ~78 MB)                 │
├─────────────────────────────────────────────────────────────┤
│  GUI Layer (CustomTkinter - Dark Mode)                      │
│  ├── Tab Batch: preset, formati, nomi, watermark, EXIF      │
│  ├── Tab Sviluppo RAW: slider Y/Cb/Cr, colore, logo             │
│  ├── Tab Tethering & Cloud: multi-marca, Sony, cloud        │
│  └── Tab Log: timestamp, color-coding, auto-scroll          │
├─────────────────────────────────────────────────────────────┤
│  ImageEngine                                                │
│  ├── rawpy (LibRaw; AMaZE → AHD → PPG → LINEAR) — RAW→RGB  │
│  ├── scikit-image — Y/Cb/Cr, guided filter, non-local means │
│  ├── Nitidezza controllata su canale Y (soglia rumore)      │
│  ├── Pillow — Watermark alpha composite, JPEG/PNG/TIFF/WEBP │
│  ├── piexif — EXIF extraction & injection                   │
│  └── NumPy — Array bridge float32                           │
├─────────────────────────────────────────────────────────────┤
│  Elaborazione parallela                                      │
│  ├── ProcessPoolExecutor (tutti i core logici)              │
│  ├── Scrittura atomica: file .tmp + os.replace              │
│  └── Annullamento: terminate dei processi figli             │
├─────────────────────────────────────────────────────────────┤
│  Background Services                                         │
│  ├── RawHotFolderHandler (watchdog.Observer)                │
│  │   └── on_created/on_moved → attesa dimensione → Engine  │
│  └── CloudDispatcher                                        │
│      ├── Telegram Bot API (operativo)                       │
│      ├── Dropbox API (operativo)                            │
│      └── Google Drive / Meta / SwissTransfer (predisposti)  │
└─────────────────────────────────────────────────────────────┘
```

### Dipendenze (bundled in .exe)

| Libreria | Versione | Scopo |
|----------|----------|-------|
| **rawpy** | 0.27+ | LibRaw Python bindings (AMaZE quando disponibile, fallback AHD/PPG/LINEAR) |
| **LibRaw** | 0.21+ | RAW decoding C++ |
| **scikit-image** | 0.24+ | Y/Cb/Cr, guided filter, non-local means, nitidezza controllata |
| **customtkinter** | 5.2+ | Modern Dark GUI |
| **watchdog** | 4.0+ | Filesystem events |
| **Pillow** | 12.3+ | Imaging, Watermark, JPEG |
| **piexif** | 1.1+ | EXIF binary manipulation |
| **requests** | 2.31+ | REST API calls |
| **NumPy** | 2.5+ | Array operations float32 |

---

## 🔒 Privacy & Sicurezza (by design)

| Caratteristica | Franchetti Raw Converter Pro v2.55.0 |
|----------------|--------------------------------------|
| **Rete** | Solo se attivi Cloud Dispatch (opzionale, esplicito) |
| **Telemetria** | ❌ Nessuna |
| **Crash reporting** | ❌ Nessuno |
| **Aggiornamenti auto** | ❌ Manuali |
| **Registro Windows** | ❌ Mai scritto |
| **Dati personali** | ❌ Mai raccolti |
| **File originali** | ✅ Solo lettura, mai modificati |

Vedi [PRIVACY.md](PRIVACY.md) e [SECURITY.md](SECURITY.md) per dettagli.

---

## 📋 Requisiti di Sistema

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| **OS** | Windows 10 1809+ | Windows 11 24H2+ |
| **Architettura** | x64 | x64 |
| **RAM** | 2 GB | 8 GB+ |
| **Disco** | 100 MB liberi | 1 GB+ liberi (SSD per batch) |
| **CPU** | Qualsiasi x64 | Multi-core (i5/Ryzen 5+) |
| **Display** | 1024×768 | 1920×1080+ |

*Singolo `.exe` ~78 MB. Nessun .NET Framework, VC++ Redistributables o diritti admin richiesti.*

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
| [Changelog](CHANGELOG.md) | Storico versioni (v2.55.0) |
| [Privacy Policy](PRIVACY.md) | Zero data collection |
| [Security Policy](SECURITY.md) | Responsible disclosure |
| [Release Notes](RELEASE_NOTES.md) | Note complete v2.55.0 |

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
# Output: dist/FranchettiRawConverterPro.exe (~78 MB)
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

- **LibRaw Team** — Eccezionale libreria decodifica RAW (AMaZE)
- **rawpy Maintainers** — Binding Python per LibRaw
- **scikit-image Team** — Elaborazione Y/Cb/Cr professionale
- **CustomTkinter** — Modern Dark UI framework
- **Watchdog** — Filesystem events cross-platform
- **Pillow Contributors** — Imaging library robusta
- **Python Software Foundation** — Runtime solido

---

## 📞 Supporto v2.55.0

| Canale | Scopo |
|--------|-------|
| **GitHub Issues** | Bug reports, crash, feature request |
| **GitHub Discussions** | Domande, workflow, tips |
| **Email** | `support@franchetti.dev` (security, licensing) |

---

## 📊 Statistiche v2.55.0

| Metrica | Valore |
|---------|--------|
| **Lines of Code** | ~3.000 (Python monolitico) |
| **Dimensione Executable** | ~78 MB |
| **Avvio** | ~5–10 s (estrazione onefile) |
| **Velocità Conversione** | ~2 MP/s per core; fino a 3× con multi-core |
| **Memoria** | ~300 MB–1,5 GB per processo (RAW 24 MP) |

---

<div align="center">

**Made with ❤️ per fotografi professionisti da Franchetti**

**v2.55.0 — 27 Ottobre 2026**

[![GitHub](https://img.shields.io/badge/GitHub-FranchettiBiagio%2Fraw--converter--pro-181717?logo=github)](https://github.com/FranchettiBiagio/raw-converter-pro)
[![Download](https://img.shields.io/badge/Download-v2.55.0-0066cc?logo=github)](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.55.0)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>
