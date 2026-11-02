# Technical Specifications

**Franchetti Raw Converter Pro v2.58.0**

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
        demosaic_algorithm=AAHD if is_fujifilm else AHD,  # 12 / 3
        use_camera_wb=True,      # Camera white balance
        use_camera_matrix=True,  # Camera color profile (LibRaw default if not exposed)
        half_size=False,         # Full resolution
        no_auto_bright=False,    # Luminosità gestita dalla pipeline Y/Cb/Cr
        output_color=rawpy.ColorSpace.sRGB,
        output_bps=8             # 8-bit per channel
    )
    bgr = rgb[..., ::-1]         # BGR ready for OpenCV
```
- **Input**: 12-14 bit RAW (Bayer CFA or Fujifilm X-Trans)
- **Output**: 8-bit BGR numpy array (H×W×3); the internal photographic pipeline converts it back to RGB
- **Demosaicing**: AHD (quality 3) for Bayer, AAHD (quality 12) for Fujifilm X-Trans
- **Color**: camera WB + camera matrix, output sRGB
- **Brands**: Sony, Canon, Nikon, Fujifilm, Panasonic, OM System, Leica and other LibRaw-supported cameras

### Image Processing Pipeline (v2.58.0)
```
LibRaw decode -> BGR bridge -> RGB pipeline -> Lanczos resize -> tone (exposure/highlight shoulder) -> color -> hybrid denoise -> controlled sharpening -> watermark -> encode
```
- **Resampling**: Lanczos-3 before the pipeline, so the denoise works at the final size
- **Tone/color**: luminance-preserving exposure, sigmoid contrast, selective vibrance (chroma scaled around luminance, stronger on muted tones), HSL
- **Highlight protection** (`proteggi_luci`): C1 cubic Hermite shoulder that compresses values above 0.68, keeps slope continuity at the knee, preserves white at 1.0 and leaves lower tones untouched
- **Smart Batch**: optional per-file analysis (half-size decode, histogram/clipping/noise metrics) merged with global parameters at batch time
- **Denoise**: guided filter + detail coring; non-local means only in flat areas (skipped for images < 8 px on a side)
- **Sharpening**: luminance-only unsharp mask with a noise-derived threshold
- **Watermark**: Text rendering with alpha compositing
- **JPEG**: Optimized Huffman tables, progressive scan, quality 90 by default

### Wi-Fi FTP Ingestion Pipeline (v2.58.0)
```
FTP STOR -> on_file_received -> decode (camera WB/matrix) -> BGR -> Lanczos 2000px -> filename + copyright overlay (Pillow) -> JPEG q85 -> EXIF/IPTC -> Anteprime_Cliente/<session> -> gallery refresh -> optional cloud dispatch
```
- **Server**: `pyftpdlib.servers.FTPServer` on `0.0.0.0:2121`, local LAN IP resolved with a UDP socket; runs in a daemon thread.
- **Credentials**: user `camera`, password `1234`, full write permission on the `Originali` session folder.
- **Completion hook**: `FTPHandler.on_file_received` is used instead of polling the filesystem, so the pipeline starts only when the transfer is complete.
- **Session layout**: every server start creates `AAAA-MM-GG_HHMMSS`; `Originali`, `Anteprime_Cliente` and `Galleria_Cliente` each get a matching subfolder, so separate shoots never mix.
- **Decode**: `use_camera_wb=True`, `use_camera_matrix=True`; Fujifilm → AAHD (12), other brands → AHD (3).
- **Resize**: `ImageOps.contain` with Lanczos, longest side capped at 2000 px.
- **Overlay**: Pillow text rendering (Unicode-safe, `©` and accents correct without `cv2`); filename bottom-left, copyright bottom-right, long strings truncated with an ellipsis. White text over a black stroke/border.
- **Output**: JPEG quality 85 in `Anteprime_Cliente/<session>`; originals are never modified.
- **Metadata**: optional EXIF (`Artist`, `Copyright`, `ImageDescription`) and IPTC (`By-line`, `Copyright Notice`, `Caption-Abstract`, `Object Name`) written directly into APP13/Photoshop 3.0.
- **Gallery**: a self-contained `index.html` is regenerated in `Galleria_Cliente/<session>` after each preview (thumbnails, checkboxes, copy/download selection).
- **Cloud**: optional automatic dispatch of previews to active Telegram/Dropbox channels; disabled by default.
- **Shutdown**: `server.close_all()` and thread join; port 2121 is released.
- **Fallback**: Pillow handles resize/overlay/encode; the app still starts without `cv2`.

### Adaptive Parallel Processing (v2.58.0)
```python
processi = numero_processi_ottimale(
    numero_file, per_processo_mb=1200, profilo="Bilanciato", override=0
)
if conviene_elaborazione_parallela(files, parameters):
    with ProcessPoolExecutor(max_workers=processi) as pool: ...
```
- **Profiles**: `Veloce` (logical cores, lighter denoise/sharpening), `Bilanciato` (physical cores, defaults), `Massima qualità` (physical cores, stronger denoise/sharpening).
- **Physical vs logical cores**: detected through the Windows API with `ctypes` (`GetLogicalProcessorInformation`), no `psutil` dependency.
- **Memory guard**: `per_processo_mb` (default 1200 MB) caps the worker count against available RAM.
- **Adaptive threshold**: a pool is used only when the estimated batch weight justifies it (`>= 25 MP` equivalent, or `>= 8 files` and `>= 12 MP` equivalent). Small batches stay sequential.
- **Manual override**: when `processi_auto=False` and `processi_manuali > 1`, the user's choice wins over the small-batch heuristic.
- **Benchmark**: `benchmark_conversione` processes 1–2 real files in a temporary folder, reading originals only; results feed `stima_tempo_batch`, progress file/min and ETA.
- **Isolation**: each output is written to a temporary file and published atomically; a corrupt file does not stop the batch.

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
| Hybrid denoise | O(W×H) | Guided filter + NLM in flat areas |
| Watermark | O(text_pixels) | Negligible |
| JPEG encode | O(W×H) | libjpeg-turbo (SIMD) |

### Benchmarks (v2.58.0, measured)
| Source | Target | Result |
|--------|--------|--------|
| 4× RAW 24 MP | 3000px, denoise auto | **12,8 s** batch, 4/4 OK |
| 1× RAW 24 MP | 3000px, denoise auto | **8–9 s** |
| 1× RAW 24 MP | Original, TIFF, denoise auto | ~40-45 s |
| 1× RAW 24 MP | Original, JPEG 95, denoise auto | ~40-45 s |

| 1x Fujifilm RAF 26 MP | Original, JPEG, denoise auto | **38.45 s**, 6264x4176, 5.8 MB |
| Batch Sony + Fujifilm | Original, JPEG, denoise auto | **50.4 s**, 2/2 OK, 2 processi/20 core |
| 3× synthetic noisy JPEG 4.7 MP | 1500px, denoise off, 3 workers (override) | **1.18 s**, 3/3 OK |
| 3× JPEG 1.3 MP (GUI benchmark) | 3000px, defaults | **1.4 s/file**, batch **0:04**, **42.9 file/min** |

> Adaptive threshold measured on 5 small JPEGs (~0.3 MP each): the app keeps
> the batch sequential instead of spawning 5 workers; a 3-file noisy batch with
> manual override uses 3 workers and completes in 1.18 s.

### Memory Profile
| Phase | Peak RSS | Notes |
|-------|----------|-------|
| Idle | 40 MB | Python + GUI |
| Decode 24 MP | 350 MB | LibRaw workspace |
| Resize | 400 MB | Temporary buffers |
| Hybrid denoise | +600 MB | Guided filter + NLM working sets |
| Encode | 380 MB | JPEG buffers |
| **Per-file peak** | **~1–1,5 GB** | Released after each file |

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
- **Numero di processi**: adattivo (profili Veloce/Bilanciato/Massima qualità), core fisici o logici, ridotto in base alla RAM libera; pool solo se il peso del batch lo giustifica
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
| **Size** | ~92 MB |
| **Architecture** | x64 (PE32+) |
| **Subsystem** | Windows GUI (2) |
| **Dependencies** | None (fully bundled) |
| **Code signing** | Not signed (planned) |

---

## Version Information (Embedded)

| Field | Value |
|-------|-------|
| **FileVersion** | 2.58.0.0 |
| **ProductVersion** | 2.58.0.0 |
| **CompanyName** | Franchetti |
| **ProductName** | Franchetti Raw Converter Pro |
| **InternalName** | FranchettiRawConverterPro |
| **OriginalFilename** | FranchettiRawConverterPro.exe |
| **FileDescription** | Professional RAW converter with multi-core batch, Y/Cb/Cr pipeline and watermark |
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

## Limiti noti (v2.58.0)

| Voce | Stato |
|------|-------|
| Preservazione EXIF | ✅ Implementata (JPEG/ARW, orientamento normalizzato) |
| Copyright EXIF/IPTC | ✅ `Artist`, `Copyright`, `ImageDescription` + IPTC APP13 |
| Profilo colore | ✅ Solo sRGB con ICC incorporato (Adobe RGB/ProPhoto non supportati) |
| Posizioni watermark | ✅ Cinque posizioni + logo PNG |
| Preset | ✅ Web/Social, Stampa Fine Art, Archivio JPEG, Ritratto, Paesaggio, Bianco e Nero |
| Parallelismo | ✅ Adattivo: profili Veloce/Bilanciato/Massima qualità, core fisici/logici e limite RAM; pool solo se il batch lo giustifica |
| Galleria cliente | ✅ HTML autonomo per sessione, senza server |
| Cloud | ✅ Telegram e Dropbox; Google Drive/Meta/SwissTransfer non attivi |
| CR3 compresso | ⚠️ Alcuni file possono fallire (limite LibRaw upstream) |
| Firma del codice | ❌ Non firmato (verifica SHA-256 su GitHub Releases) |

---

## Qualità e prestazioni misurate

| Metrica | Valore |
|---------|--------|
| Avvio (onefile, cold) | ~5–10 s |
| UI | Reattiva durante il batch (thread separato + coda) |
| RAW Sony A7S 24 MP | ~8–9 s a 3000px con denoise |
| 4 RAW (4 processi) | 12,8 s (3000px, denoise automatico) |
| Preset full-res | ~40-45 s per foto (denoise non-locale su 24 MP) |
| Memoria | ~1–1,5 GB per processo, più buffer NLM |
| Crash rate nei test | 0% |

---

*Technical specs v2.58.0 — 2 Novembre 2026*