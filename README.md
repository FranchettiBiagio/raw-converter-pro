# Franchetti Raw Converter Pro v2.51.1

[![Version](https://img.shields.io/badge/version-2.51.1-blue.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/actions)
[![Size](https://img.shields.io/badge/size-23%20MB-orange.svg)](https://github.com/FranchettiBiagio/raw-converter-pro/releases)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

> **Enterprise RAW Suite** — Pipeline CIE L*a*b*, Tethering Wi-Fi automatico, Cloud Dispatch multi-canale, Watermark professionale, EXIF preservation. Portable, Open Source (MIT), Zero telemetria.

---

## 🎯 Caratteristiche Principali v2.51.1

### 🧠 **Nuova Pipeline CIE L*a*b* (Avanzata)**
| Fase | Descrizione | Controllo |
|------|-------------|-----------|
| **Sviluppo RAW** | LibRaw nativo, algoritmo **AMaZE**, WB camera, sRGB 8-bit | `use_camera_wb` |
| **Contrasto Sigmoidale** | Curva logistica a "S" protegge luci/ombre senza clipping | `contrasto` 0.1–1.0 |
| **Vivacità Selettiva** | Satura solo toni spenti, preserva incarnati | `vivacita` 0.0–1.0 |
| **Lab Color Space** | Separazione Luminanza (L) / Crominanza (a,b) | — |
| **Nitidezza Unsharp L** | Solo canale L → zero aloni colorati | `raggio` 0.5–3.0, `quantità` 0.5–5.0 |
| **Output** | uint8 + profilo ICC sRGB embedded | `qualita_jpeg` 50–100 |

> **Perché Lab?** La separazione luminanza/crominanza permette nitidezza pura su dettaglio senza artefatti cromatici (aloni colorati tipici dello sharpening RGB).

### 📡 **Tethering Wi-Fi Automatico — Hot-Folder (v2.51.1)**
- **Watchdog Observer** monitora cartella in tempo reale (`watchdog` library)
- **Formati rilevati**: `.arw, .cr2, .cr3, .nef, .raf, .dng, .orf, .rw2`
- **Buffer rete**: 1.5s delay per completamento scrittura wireless
- **Workflow**: Scatta → File arriva via Wi-Fi → Pipeline Lab completa → JPEG `_PRO.jpg` → Cloud Dispatch → Notifica GUI live

### ☁️ **Cloud Dispatch Multi-Canale Simultaneo**
| Canale | API | Configurazione UI |
|--------|-----|-------------------|
| **Telegram** | Bot API `sendPhoto` | Bot Token + Chat ID |
| **Google Drive** | Drive API v3 multipart | Folder ID / API Key |
| **Meta (IG/FB)** | Graph API `media_publish` | Access Token + Account ID |

Tutti e tre i canali attivati **in parallelo** al completamento di ogni elaborazione.

### 🏷️ **Watermark Professionale Proporzionale**
- **Scaling intelligente**: Logo al 15% lato lungo, ridimensionamento Lanczos
- **Alpha compositing**: Fusione canale alpha nativo, opacità configurabile (0–1)
- **Posizione**: Basso-destra con margine 20px
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

*Basato su **LibRaw 0.21+** con algoritmo **AMaZE** per demosaicing di massima qualità.*

---

### ⚙️ **Elaborazione Batch Enterprise**
- **Ricorsivo**: Cartella radice + tutte le sotto-cartelle
- **Multi-thread**: `ProcessPoolExecutor` per throughput massimo
- **GUI reattiva**: Coda thread-safe, progress bar real-time, cancellabile
- **Nominazione**: Mantieni originale / Prefisso personalizzato / Anti-collisione (`_1`, `_2`…)

### 🎨 **Enterprise Dark GUI (CustomTkinter)**
| Area | Contenuto |
|------|-----------|
| **Sinistra** | Pipeline Lab: Slider Contrasto, Vivacità, Nitidezza (live update) |
| | Watermark: Carica logo PNG, preview path |
| **Destra** | Tethering: Selezione cartella Wi-Fi, Attiva/Disattiva server |
| | Cloud: Campi Token/ID per Telegram, Google Drive, Meta |
| **Basso** | Console Log: Timestamp, color-coding, auto-scroll |

---

## 🚀 Quick Start

### Download v2.51.1
| Metodo | Link |
|--------|------|
| **GitHub Releases** | [Download v2.51.1](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.51.1) |
| **Portable (consigliato)** | [FranchettiRawConverterPro.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe) |
| **Installer Windows** | [Setup v2.51.1](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/Franchetti_Raw_Converter_Setup_v2.51.1.exe) |
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
2. **Pipeline Lab (Sinistra)**: Regola Contrasto, Vivacità, Nitidezza con slider live
3. **Watermark (Opzionale)**: Carica logo PNG trasparente → regola opacità
4. **Tethering (Destra)**: Seleziona cartella Wi-Fi → "ATTIVA SERVER IN ASCOLTO WIRELESS"
5. **Cloud (Opzionale)**: Inserisci Token/ID per Telegram, Google Drive, Meta
6. **Scatta** → File elaborato automaticamente → JPEG + Watermark + EXIF → Cloud → Notifica GUI

---

## 📋 Requisiti di Sistema v2.51.1

| Componente | Minimo | Consigliato |
|------------|--------|-------------|
| **OS** | Windows 10 1809+ | Windows 11 24H2+ |
| **Architettura** | x64 | x64 |
| **RAM** | 2 GB | 8 GB+ |
| **Disco** | 100 MB liberi | 1 GB+ liberi (SSD per batch) |
| **CPU** | Qualsiasi x64 | Multi-core (i5/Ryzen 5+) |
| **Display** | 1024×768 | 1920×1080+ |

*Singolo `.exe` ~62 MB (UPX compressed). Nessun .NET Framework, VC++ Redistributables, diritti admin richiesti.*

---

## 🏗️ Architettura v2.51.1

```
┌─────────────────────────────────────────────────────────────┐
│              FranchettiRawConverterPro.exe                  │
│  (PyInstaller --onefile --windowed, UPX ~62 MB)            │
├─────────────────────────────────────────────────────────────┤
│  GUI Layer (CustomTkinter - Dark Mode)                      │
│  ├── Colonna Sinistra: Pipeline Lab + Watermark             │
│  │   ├── Slider: Contrasto, Vivacità, Nitidezza (live)      │
│  │   └── Watermark: Logo PNG, Opacità                        │
│  ├── Colonna Destra: Tethering Wi-Fi + Cloud Config         │
│  │   ├── Hot-Folder: Selezione, Attiva/Disattiva Server     │
│  │   └── Cloud API: Telegram, Google Drive, Meta Token/ID   │
│  └── Console Log: Timestamp, Color-coding, Auto-scroll      │
├─────────────────────────────────────────────────────────────┤
│  ImageEngine (Threaded Pipeline)                            │
│  ├── rawpy (LibRaw/AMaZE) — RAW → RGB                       │
│  ├── scikit-image — RGB ↔ CIE Lab conversion                │
│  ├── Unsharp Mask su canale L (skimage.filters)             │
│  ├── Pillow — Watermark alpha composite, JPEG encode        │
│  ├── piexif — EXIF binary extraction & injection            │
│  └── NumPy — Array bridge float32                           │
├─────────────────────────────────────────────────────────────┤
│  Background Services                                         │
│  ├── RawHotFolderHandler (watchdog.Observer)                │
│  │   └── on_created() → buffer 1.5s → ImageEngine → Cloud  │
│  └── CloudDispatcher (REST APIs paralleli)                  │
│      ├── Telegram Bot API                                    │
│      ├── Google Drive API v3                                 │
│      └── Meta Graph API                                      │
└─────────────────────────────────────────────────────────────┘
```

### Dipendenze (bundled in .exe)

| Libreria | Versione | Scopo |
|----------|----------|-------|
| **rawpy** | 0.27+ | LibRaw Python bindings (AMaZE) |
| **LibRaw** | 0.21+ | RAW decoding C++ |
| **scikit-image** | 0.24+ | CIE Lab, Unsharp Mask |
| **customtkinter** | 5.2+ | Modern Dark GUI |
| **watchdog** | 4.0+ | Filesystem events |
| **Pillow** | 12.3+ | Imaging, Watermark, JPEG |
| **piexif** | 1.1+ | EXIF binary manipulation |
| **requests** | 2.31+ | REST API calls |
| **NumPy** | 2.5+ | Array operations float32 |

---

## 🔒 Privacy & Sicurezza (by design)

| Caratteristica | Franchetti Raw Converter Pro v2.51.1 |
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

*Singolo `.exe` ~62 MB (UPX compressed). Nessun .NET Framework, VC++ Redistributables, diritti admin richiesti.*

---

## 📖 Documentazione

| Documento | Descrizione |
|-----------|-------------|
| [Manuale Utente](USER_MANUAL.md) | Guida completa con screenshot |
| [Specifiche Tecniche](TECHNICAL_SPECS.md) | Architettura, algoritmi, formati |
| [Guida Installazione](INSTALLATION_GUIDE.md) | Deployment enterprise (GPO, Intune) |
| [FAQ](FAQ.md) | Domande frequenti & troubleshooting |
| [Changelog](CHANGELOG.md) | Storico versioni (v2.51.1) |
| [Privacy Policy](PRIVACY.md) | Zero data collection |
| [Security Policy](SECURITY.md) | Responsible disclosure |
| [Release Notes](RELEASE_NOTES.md) | Note complete v2.51.1 |

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
# Output: dist/FranchettiRawConverterPro.exe (~62 MB UPX)
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
Copyright (c) 2024-2025 Franchetti

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🙏 Ringraziamenti

- **LibRaw Team** — Eccezionale libreria decodifica RAW (AMaZE)
- **rawpy Maintainers** — Binding Python per LibRaw
- **scikit-image Team** — Elaborazione CIE Lab professionale
- **CustomTkinter** — Modern Dark UI framework
- **Watchdog** — Filesystem events cross-platform
- **Pillow Contributors** — Imaging library robusta
- **Python Software Foundation** — Runtime solido

---

## 📞 Supporto v2.51.1

| Canale | Scopo |
|--------|-------|
| **GitHub Issues** | Bug reports, crash, feature request |
| **GitHub Discussions** | Domande, workflow, tips |
| **Email** | `support@franchetti.dev` (security, licensing) |

---

## 📊 Statistiche v2.51.1

| Metrica | Valore |
|---------|--------|
| **Lines of Code** | ~800 (Python monolitico) |
| **Dimensione Executable** | ~62 MB (UPX compressed) |
| **Avvio a freddo** | < 3 s (GUI Enterprise) |
| **Avvio a caldo** | < 1 s |
| **Velocità Conversione** | ~50–200 MP/s (CPU dipendente) |
| **Memoria** | 50–150 MB (batch dipendente) |

---

<div align="center">

**Made with ❤️ per fotografi professionisti da Franchetti**

**v2.51.1 — Gennaio 2025**

[![GitHub](https://img.shields.io/badge/GitHub-FranchettiBiagio%2Fraw--converter--pro-181717?logo=github)](https://github.com/FranchettiBiagio/raw-converter-pro)
[![Download](https://img.shields.io/badge/Download-v2.51.1-0066cc?logo=github)](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.51.1)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>