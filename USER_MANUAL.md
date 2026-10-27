# User Manual

**Franchetti Raw Converter Pro v2.54.0**  
> **Guida in italiano, semplice e completa:** [GUIDA_COMPLETA.md](GUIDA_COMPLETA.md) - tutte le funzioni e le impostazioni consigliate. Versione HTML: [GUIDA_COMPLETA.html](GUIDA_COMPLETA.html).

*Complete guide for photographers — Enterprise Edition*

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Step-by-Step Workflow](#step-by-step-workflow)
4. [Advanced Options](#advanced-options)
5. [Batch Processing Tips](#batch-processing-tips)
6. [Watermark Best Practices](#watermark-best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [FAQ](#faq)

---

## Getting Started

### Download & Run

1. Download `FranchettiRawConverterPro.exe` from:
   - **GitHub Releases**: https://github.com/franchetti/raw-converter-pro/releases
   - **uptodown.dev**: https://www.uptodown.dev/apps/franchetti-raw-converter-pro

2. **No installation needed** — just double-click the `.exe`

3. **Windows SmartScreen** may warn on first run:
   - Click "More info" → "Run anyway"
   - This is normal for new unsigned executables

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 10 1809+ | Windows 11 22H2+ |
| **CPU** | x64 (any) | Multi-core |
| **RAM** | 2 GB | 8 GB+ |
| **Disk** | 100 MB free | 1 GB+ free |
| **Display** | 1024×768 | 1920×1080+ |

---

## Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Franchetti Raw Converter Pro v2.54.0                    [×] [−] [□] │
├─────────────────────────────────────────────────────────────────┤
│  Franchetti Raw Converter Pro                                   │
│  Converti RAW → JPG ridotto + watermark copyright               │
├─────────────────────────────────────────────────────────────────┤
│  1. SORGENTE RAW                                    [📁] [📄] [🗑️] │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📄 IMG_0001.ARW (Pictures)                              │   │
│  │ 📄 IMG_0002.ARW (Pictures)                              │   │
│  │ 📄 DSC_0003.NEF (Camera)                                │   │
│  │ ...                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  42 file RAW trovati (5 nuovi)          💡 Trascina qui...    │
├─────────────────────────────────────────────────────────────────┤
│  2. DESTINAZIONE                                                  │
│  [ C:\Users\Franchetti\Pictures\Converted          ] [Scegli] [Apri] │
├─────────────────────────────────────────────────────────────────┤
│  3. OPZIONI CONVERSIONE                                           │
│  Dimensione max (px lato lungo): [1920 ▼] (0 = nessuna riduzione)│
│  Qualità JPG (1-100):              [85]  (85 = ottimo equilibrio)│
│  Testo Copyright:                  [© Franchetti 2024        ]   │
│  Dimensione font watermark:        [14]  (14 = piccolo, discreto)│
│  ☑ Mantieni nome file originale    Prefisso: [FR_         ]     │
├─────────────────────────────────────────────────────────────────┤
│  [▶ AVVIA CONVERSIONE]          [⏹ ANNULLA]    ████████░░ 67%   │
│  Pronto                                                        │
├─────────────────────────────────────────────────────────────────┤
│  LOG                                                            │
│  ████████████████████████████████████████████████████████████   │
│  === AVVIO CONVERSIONE ===                    [INFO]           │
│  File da processare: 42                                     │
│  OK: IMG_0001.ARW → IMG_0001.jpg (1920x1280)        [SUCCESS] │
│  OK: IMG_0002.ARW → IMG_0002.jpg (1920x1280)        [SUCCESS] │
│  ERRORE DSC_0003.NEF: Unsupported format              [ERROR]  │
│  ...                                                            │
└─────────────────────────────────────────────────────────────────┘
```

### UI Elements

| Area | Purpose |
|------|---------|
| **Header** | App name, version, subtitle |
| **1. Sorgente RAW** | File list, add/remove buttons, count |
| **2. Destinazione** | Output folder path, browse/open buttons |
| **3. Opzioni** | All conversion parameters |
| **Actions** | Start/Cancel buttons, progress bar, status |
| **Log** | Real-time color-coded activity log |

---

## Step-by-Step Workflow

### Basic Conversion (5 Steps)

#### Step 1: Select Source Files
- **Folder**: Click `📁 Seleziona Cartella` → chooses folder, scans recursively for RAW files
- **Files**: Click `📄 Seleziona File` → multi-select specific RAW files
- **Clear**: Click `🗑️ Svuota Lista` to start over

> **Tip**: Folder scanning finds files in subfolders too. Use "Seleziona File" for precise control.

#### Step 2: Choose Output Folder
- Click `Scegli Cartella` → pick destination
- Click `Apri` to open folder in Explorer after conversion

#### Step 3: Configure Options (Optional)
| Setting | Default | When to Change |
|---------|---------|----------------|
| **Dimensione max** | 1920 | Web: 1920, Print: 3000+, Archive: 0 |
| **Qualità JPG** | 85 | 90-95 for prints, 75-80 for web |
| **Copyright** | `© Franchetti` | Your name/brand/year |
| **Font size** | 14 | 10-12 subtle, 16-20 visible |
| **Mantieni nome** | ON | OFF for batch rename with prefix |

#### Step 4: Start Conversion
- Click `▶ AVVIA CONVERSIONE`
- Progress bar updates in real-time
- Log shows each file result

#### Step 5: Retrieve Results
- Click `Apri` next to output path
- Find JPEGs ready to use

---

## Advanced Options

### Dimension Presets

| Preset | Use Case | Long Edge |
|--------|----------|-----------|
| 640 | Thumbnails, email | 640 px |
| 800 | Old web, forums | 800 px |
| 1024 | Standard web | 1024 px |
| 1280 | HD ready (720p) | 1280 px |
| 1600 | High-res web | 1600 px |
| **1920** | **Full HD (1080p)** | **1920 px** |
| 2048 | 2K reference | 2048 px |
| 2560 | 1440p / QHD | 2560 px |
| 3000 | Print (A4 @ 300 DPI) | 3000 px |
| 4000 | Large print | 4000 px |
| **0** | **Original resolution** | **No resize** |

> **Aspect ratio** is always preserved. A 6000×4000 image at 1920 becomes 1920×1280.

### JPEG Quality Guide

| Quality | File Size | Visual Quality | Best For |
|---------|-----------|----------------|----------|
| 75 | Small | Good | Web, email, social |
| **85** | **Balanced** | **Excellent** | **General purpose** |
| 90 | Larger | Near-lossless | Portfolio, clients |
| 95 | Large | Virtually lossless | Archive, print prep |
| 100 | Largest | Maximum | Not recommended (diminishing returns) |

> **Recommendation**: 85 is the sweet spot. Difference from 95 is invisible at normal viewing but 30-50% smaller files.

### Watermark Configuration

#### Text Examples
```
© Franchetti 2024
© John Doe Photography
Photo by Jane Smith | www.janesmith.photo
Franchetti Studio • All Rights Reserved
© 2024 Franchetti | franchetti.dev
```

#### Font Size Guide
| Size | Appearance | Best For |
|------|------------|----------|
| 8-10 | Very subtle | Proofs, contact sheets |
| **12-14** | **Professional, discreet** | **General use** |
| 16-20 | Visible | Social media, web |
| 24-32 | Prominent | Proofs, watermarks |
| 36-48 | Heavy | Deterrent, branding |

> **Position**: Always bottom-right with 1% margin. Shadow ensures readability on any background.

### Naming Options

| Setting | Behavior | Example Output |
|---------|----------|----------------|
| **Mantieni nome** ON | `IMG_0001.ARW` → `IMG_0001.jpg` | Original names |
| **Mantieni nome** OFF, Prefix `FR_` | `IMG_0001.ARW` → `FR_IMG_0001.jpg` | Prefixed |
| **Mantieni nome** OFF, Prefix empty | `IMG_0001.ARW` → `IMG_0001.jpg` | Same as ON |

> **Collision handling**: If `IMG_0001.jpg` exists, creates `IMG_0001_1.jpg`, `IMG_0001_2.jpg`, etc.

---

## Batch Processing Tips

### Large Folders (1000+ files)

1. **Use folder selection** — recursive scan is optimized
2. **Set output to fast SSD** — reduces I/O bottleneck
3. **Close other apps** — frees RAM for processing
4. **Don't minimize** — keep window visible for progress

### Performance Expectations

| Hardware | Speed (24 MP RAW → 1920px JPG) |
|----------|--------------------------------|
| 4 core | ~20 file/min |
| 8 core | ~40 file/min |
| 20 core (i9-12900H) | ~60–100 file/min |

> **Nota**: ogni file viene decodificato in un processo separato; il batch usa tutti i core logici disponibili, con un limite basato sulla RAM libera. Misura reale: 6 RAW da 24 MP in 22,1 s con 6 processi (3,06× rispetto al sequenziale).

### Memory Management

- **Per-process memory**: ~1–1,5 GB durante la decodifica di un RAW da 24 MP
- **Peak batch memory**: circa 1,2 GB per processo attivo; il programma riduce i processi se la RAM non basta
- **Large batches**: No accumulation — each file processed independently

---

## Watermark Best Practices

### Professional Photographers

```text
# Minimal, professional
© Your Name 2024

# With contact
© Your Name | yoursite.com

# Studio branding
YourStudio • All Rights Reserved
```

### Social Media / Web

```text
# Include handle
@yourhandle | yoursite.com

# Brand + year
YourBrand © 2024
```

### Copyright Protection

```text
# Strong deterrent
© Your Name 2024 • All Rights Reserved • Unauthorized Use Prohibited

# With registration hint
© Your Name 2024 • Registered Copyright • yoursite.com
```

### Font Size by Output

| Output Medium | Recommended Size |
|---------------|------------------|
| Instagram (1080×1080) | 14-16 pt |
| Facebook (2048×2048) | 16-18 pt |
| Website (1920px) | 14-16 pt |
| Print (3000px+) | 24-32 pt |
| Email (1200px) | 12-14 pt |

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| **App won't start** | Missing VC++ runtime | Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| **App won't start** | Antivirus blocking | Add exception for `.exe` |
| **No files found** | Wrong folder / no RAW | Verify folder contains supported formats |
| **Conversion fails** | Corrupted RAW file | Check log for specific error, skip file |
| **Watermark not visible** | Font size too small / white on white | Increase font size, check position |
| **Output folder empty** | Permission denied | Run as admin or choose writable folder |
| **Progress stuck** | Single huge file | Wait — large files take time |
| **Crash on start** | Incompatible Windows | Requires Win 10 1809+ |

### Error Messages

| Log Entry | Meaning | Action |
|-----------|---------|--------|
| `ERRORE file.ARW: Unsupported format` | LibRaw can't decode | File may be corrupted or unsupported variant |
| `ERRORE file.NEF: Cannot decode` | Nikon NEF issue | Try Nikon software first |
| `ERRORE file.CR3: Not supported` | Canon CR3 (compressed) | Update rawpy/LibRaw (future version) |
| `ERRORE: Permission denied` | Output folder locked | Choose different folder, check permissions |

### Log

Il tab **Log** mostra ogni operazione con orario (`[HH:MM:SS]`) ed è accompagnato da due pulsanti:
**Svuota log** e **Salva log su file**. Lo stesso contenuto viene scritto nel file
`franchetti_log.txt` sul Desktop per diagnosi successive.

---

## Input da tastiera

L'interfaccia è progettata per il mouse. I campi di testo (dimensione massima,
qualità, prefisso, suffisso, nome watermark, credenziali) sono modificabili
direttamente; non sono presenti scorciatoie globali.

---

## FAQ

### General

**Q: Is it really free?**  
A: Yes, MIT license — free for personal and commercial use.

**Q: Does it modify my original RAW files?**  
A: Never. Only reads them. Originals untouched.

**Q: Can I use it on Mac/Linux?**  
A: Windows only currently. Source code is cross-platform; PRs welcome for native builds.

**Q: Why 62 MB for a simple tool?**  
A: Bundles Python runtime + LibRaw + Pillow + NumPy + scikit-image + CustomTkinter for zero-dependency execution.

### Technical

**Q: Which RAW formats exactly?**  
A: See [README.md](README.md) — 25+ formats via LibRaw 0.21+.

**Q: Does it preserve EXIF?**  
A: **Yes** — EXIF preserved (GPS, camera settings, orientation) with `Orientation` normalized to 1.

**Q: Can I add custom watermark positions?**  
A: **Yes** — five positions (bottom/top left/right, center), proportional margin and shadow. Logo PNG supported.

**Q: Is there a command-line version?**  
A: The GUI is the main interface. Diagnostic modes: `--converti-test` and `--batch-test`.

**Q: How to verify file integrity?**  
A: Check SHA-256 on GitHub Releases page.

### Licensing

**Q: Can I bundle this with my product?**  
A: Yes, MIT license allows commercial redistribution with attribution.

**Q: Do I need to credit Franchetti?**  
A: License requires keeping copyright notice. Attribution appreciated but not mandated beyond license.

---

## Support

| Channel | Best For |
|---------|----------|
| **GitHub Issues** | Bugs, crashes, feature requests |
| **GitHub Discussions** | Questions, tips, workflows |
| **Email** | `support@franchetti.dev` (licensing, security) |

When reporting issues, include:
- Windows version (`winver`)
- App version (About dialog)
- Steps to reproduce
- Log output (copy from log panel)
- Sample RAW file (if possible, <50 MB)

---

*Manual v2.54.0 — 27 Ottobre 2026*