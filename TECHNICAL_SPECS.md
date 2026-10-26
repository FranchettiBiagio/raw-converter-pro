# Technical Specifications

**Franchetti Raw Converter Pro v2.53.0**

---

## Architecture Overview

```
Single-file executable (PyInstaller --onefile --windowed)
├── Embedded Python 3.12.10 runtime
├── Bundled extensions (.pyd/.dll)
│   ├── rawpy._rawpy (LibRaw 0.21+ bindings)
│   ├── PIL._imaging (Pillow 12.3 C core)
│   ├── numpy.core._multiarray_umath
│   └── _tkinter (Tcl/Tk 8.6)
└── Application code (bytecode in PYZ archive)
```

---

## Core Pipeline

### RAW Decoding (rawpy/LibRaw)
```python
with rawpy.imread(str(raw_path)) as raw:
    rgb = raw.postprocess(
        use_camera_wb=True,      # Camera white balance
        half_size=False,         # Full resolution
        no_auto_bright=False,    # Luminosità gestita dalla pipeline Lab
        output_bps=8             # 8-bit per channel
    )
```
- **Input**: 12-14 bit RAW (Bayer CFA)
- **Output**: 8-bit RGB numpy array (H×W×3)
- **Demosaicing**: LibRaw AHD (default, high quality)
- **Color space**: Camera-native → sRGB (implicit)

### Image Processing (Pillow)
```python
img = Image.fromarray(rgb, 'RGB')
if max_dim > 0:
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
if watermark:
    img = add_watermark(img, text, font_size)
img.save(out_path, 'JPEG', quality=q, optimize=True, progressive=True)
```
- **Resampling**: Lanczos-3 (high-quality downscaling)
- **Watermark**: Text rendering with alpha compositing
- **JPEG**: Optimized Huffman tables, progressive scan

### Watermark Algorithm
```
Position: (W - text_w - margin, H - text_h - margin)
margin = max(10, dimension // 100)  # 1% edge margin
Shadow: 1px offset, black @ 50% opacity
Text: White @ 78% opacity
Font: Arial/DejaVuSans fallback → default bitmap
```

---

## Supported Formats (LibRaw 0.21+)

| Extension | Manufacturer | Notes |
|-----------|--------------|-------|
| `.arw` | Sony | Full support |
| `.cr2` | Canon | Full support |
| `.cr3` | Canon | Partial (compressed CR3 limited) |
| `.nef` | Nikon | Full support |
| `.raf` | Fujifilm | Full support (X-Trans) |
| `.orf` | Olympus/OM | Full support |
| `.rw2` | Panasonic | Full support |
| `.dng` | Adobe/Universal | Full support |
| `.pef` | Pentax | Full support |
| `.srw` | Samsung | Full support |
| `.x3f` | Sigma | Foveon support |
| `.3fr` | Hasselblad | Full support |
| `.fff` | Imacon | Full support |
| `.raw` | Generic | Various |
| `.rwl` | Leica | Full support |
| `.dcr` | Kodak | Legacy |
| `.k25/.kdc` | Kodak | Legacy |
| `.mos` | Leaf | Medium format |
| `.mrw` | Minolta | Legacy |
| `.nrw` | Nikon | Coolpix RAW |

---

## Performance Characteristics

### Time Complexity
| Stage | Complexity | Dominant Factor |
|-------|------------|-----------------|
| RAW decode | O(W×H) | LibRaw C++ (un file per processo) |
| Resize | O(W×H) | Pillow Lanczos (SIMD optimized) |
| Watermark | O(text_pixels) | Negligible |
| JPEG encode | O(W×H) | libjpeg-turbo (SIMD) |

### Benchmarks (Typical)
| Source | Target | i7-11700 | Ryzen 5800X |
|--------|--------|----------|-------------|
| 6000×4000 (24 MP) | 1920px | 0.35 s | 0.28 s |
| 4000×3000 (12 MP) | 1920px | 0.18 s | 0.14 s |
| 8000×6000 (48 MP) | 1920px | 0.65 s | 0.52 s |

### Memory Profile
| Phase | Peak RSS | Notes |
|-------|----------|-------|
| Idle | 40 MB | Python + GUI |
| Decode 24 MP | 350 MB | LibRaw workspace |
| Resize | 400 MB | Temporary buffers |
| Encode | 380 MB | JPEG buffers |
| **Per-file peak** | **~400 MB** | Released after each file |

---

## File I/O

### Input Validation
```python
SUPPORTED_EXTENSIONS = {'.arw', '.cr2', '.cr3', '.nef', '.raf', 
    '.orf', '.rw2', '.dng', '.pef', '.srw', '.x3f', '.3fr', 
    '.fff', '.raw', '.rwl', '.dcr', '.k25', '.kdc', '.mos', 
    '.mrw', '.nrw'}
```
- Case-insensitive matching
- Extension allowlist only (no magic bytes check)

### Output Naming
```python
stem = raw_path.stem if keep_name else f"{prefix}{raw_path.stem}"
out_path = output_dir / f"{stem}.jpg"
# Collision: stem_1.jpg, stem_2.jpg...
```

---

## Modello di esecuzione (multi-core)

```
Main Thread (GUI)
├── Event loop (tkinter)
├── Dialoghi di selezione file
├── Aggiornamento progress bar / log (via coda)
└── root.after(120 ms, _processa_coda)

Worker Thread (daemon)
├── esegui_batch()
├── ProcessPoolExecutor(max_workers = numero_processi_ottimale())
│   ├── _converti_file_worker() × N processi
│   │   ├── ImageEngine.sviluppa_e_ottimizza()
│   │   ├── scrittura su file .tmp
│   │   └── os.replace() atomico
│   └── risultati raccolti con as_completed()
└── Callback → queue.put(('progress' | 'done' | 'log', ...))
```

- **Nessuno stato condiviso** tra processi: ogni file riceve una copia dei parametri
- **Comunicazione thread-safe** tramite coda; i processi figli non toccano Tk
- **Numero di processi**: tutti i core logici, ridotto in base alla RAM libera e ai file
- **Annullamento**: `cancel_event` + `terminate()` dei processi figli
- **Output atomico**: un file parziale non viene mai pubblicato

---

## Build Specification

### PyInstaller Configuration
```python
cmd = [
    "pyinstaller",
    "--onefile",              # Single executable
    "--windowed",             # No console (GUI)
    "--name=FranchettiRawConverterPro",
    "--clean",                # Clean cache
    "--noconfirm",            # Overwrite
    "--hidden-import=rawpy",
    "--hidden-import=rawpy._rawpy",
    "--hidden-import=numpy",
    "--hidden-import=PIL",
    "--hidden-import=PIL.Image",
    "--hidden-import=PIL.ImageDraw",
    "--hidden-import=PIL.ImageFont",
    "--hidden-import=PIL.ImageOps",
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.ttk",
    "--hidden-import=tkinter.filedialog",
    "--hidden-import=tkinter.messagebox",
    "--hidden-import=tkinter.scrolledtext",
    "main.py"
]
```

### Output
| Property | Value |
|----------|-------|
| **File** | `FranchettiRawConverterPro.exe` |
| **Size** | ~62 MB |
| **Architecture** | x64 (PE32+) |
| **Subsystem** | Windows GUI (2) |
| **Dependencies** | None (fully bundled) |
| **Code signing** | Not signed (planned) |

---

## Version Information (Embedded)

| Field | Value |
|-------|-------|
| **FileVersion** | 2.53.0.0 |
| **ProductVersion** | 2.53.0.0 |
| **CompanyName** | Franchetti |
| **ProductName** | Franchetti Raw Converter Pro |
| **InternalName** | FranchettiRawConverterPro |
| **OriginalFilename** | FranchettiRawConverterPro.exe |
| **FileDescription** | Professional RAW converter with multi-core batch, CIE Lab pipeline and watermark |
| **LegalCopyright** | Copyright © 2024-2026 Franchetti |
| **LegalTrademarks** | Franchetti™ |

---

## Compatibility Matrix

| OS Version | Status | Notes |
|------------|--------|-------|
| Windows 10 1809+ | ✅ Supported | Tested |
| Windows 10 21H2 | ✅ Supported | Tested |
| Windows 11 21H2 | ✅ Supported | Tested |
| Windows 11 22H2+ | ✅ Supported | Primary target |
| Windows 7/8.1 | ❌ Unsupported | Python 3.12 requirement |
| Windows ARM64 | ❌ Untested | x64 emulation may work |

---

## Limiti noti (v2.53.0)

| Voce | Stato |
|------|-------|
| Preservazione EXIF | ✅ Implementata (JPEG/ARW, orientamento normalizzato) |
| Profilo colore | ✅ Solo sRGB con ICC incorporato (Adobe RGB/ProPhoto non supportati) |
| Posizioni watermark | ✅ Cinque posizioni + logo PNG |
| Preset | ✅ Web/Social, Stampa Fine Art, Archivio JPEG, Ritratto, Paesaggio, Bianco e Nero |
| Parallelismo | ✅ Tutti i core logici, limite RAM |
| Cloud | ✅ Telegram e Dropbox; Google Drive/Meta/SwissTransfer non attivi |
| CR3 compresso | ⚠️ Alcuni file possono fallire (limite LibRaw upstream) |
| Firma del codice | ❌ Non firmato (verifica SHA-256 su GitHub Releases) |

---

## Qualità e prestazioni misurate

| Metrica | Valore |
|---------|--------|
| Avvio (onefile, cold) | ~5–10 s |
| UI | Reattiva durante il batch (thread separato + coda) |
| RAW Sony A7S 24 MP | ~10–12 s per core |
| 6 RAW (6 processi) | 22,1 s (3,06× rispetto a 67,6 s sequenziale) |
| 12 RAW (12 processi) | 39,8 s, 0 errori |
| Memoria | ~1–1,5 GB per processo |
| Crash rate nei test | 0% |

---

*Technical specs v2.53.0 — 26 Ottobre 2026*