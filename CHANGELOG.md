# Changelog

All notable changes to Franchetti Raw Converter Pro are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.51.1] - 2026-10-26

### Added
- Pulsante **DIAGNOSI** nel tab Tethering: verifica IP del PC, rete 192.168.122.x, porta API 10000 e risposta della fotocamera, salvando il report in `Desktop\sony_diagnosi.txt`
- Diagnosi automatica quando la connessione Sony fallisce

### Fixed
- Connessione Sony: prova prima l'indirizzo diretto 192.168.122.1 e solo dopo SSDP, con messaggi di errore chiari

---

## [2.51.0] - 2026-10-26

### Added
- **Sony Wi-Fi tethering (Camera Remote API)**: ricerca SSDP della fotocamera, connessione all'API su porta 10000, comando di scatto e download immediato di JPEG/RAW
- Pulsanti **CONNETTI FOTOCAMERA** e **SCATTA E SCARICA** con log dettagliato
- Istruzioni integrate per Sony A7S (app Smart Remote Control + rete Wi-Fi DIRECT)
- I file scaricati vengono elaborati automaticamente dalla pipeline hot-folder

### Changed
- Tab Tethering: etichette corrette ("AVVIA MONITORAGGIO CARTELLA") e note esplicative sui limiti del Wi-Fi Sony
- Intestazione del programma con la dicitura sulle recensioni

### Fixed
- Finestra non piu tagliata: scaling DPI corretto e dimensionamento sull'area di lavoro di Windows
- Barra azioni e barra di stato sempre visibili

---

## [2.50.1] - 2025-01-25

### Added
- **Major architecture overhaul**: Complete rewrite with CIE L*a*b* color space processing pipeline
- **Advanced image engine**: Sigmoidal contrast curves, selective vibrance, unsharp masking in Lab space
- **Enterprise-grade tethering**: Wi-Fi hot-folder monitoring via Watchdog with 1.5s buffer
- **Multi-channel cloud dispatch**: Simultaneous upload to Telegram, Google Drive, Meta (Instagram/Facebook)
- **Watermark system**: Proportional logo scaling (15% long edge), configurable opacity, alpha compositing
- **EXIF preservation**: Binary EXIF extraction with orientation correction
- **Dark-mode Enterprise GUI**: CustomTkinter dual-column layout with live parameter sliders
- **Real-time log console**: Timestamped visual feedback for all operations

### Changed
- **Version numbering**: Switched to semantic v2.50.1 (Major.Minor.Patch)
- **Color processing**: Moved from basic RGB to CIE L*a*b* for perceptually uniform adjustments
- **Sharpening**: Now operates on L-channel only (no color halos/artifacts)
- **Distribution**: Single portable .exe (~23 MB) with embedded ICC profile

### Technical
- Python 3.12+, CustomTkinter, rawpy (LibRaw/AMaZE), scikit-image (Lab processing)
- Thread-safe Watchdog observer for background Wi-Fi tethering
- REST API integrations: Telegram Bot API, Google Drive API v3, Meta Graph API
- PyInstaller 6.x build with version metadata embedding

---

## [1.0.0] - 2024-09-18

### Added
- **Initial public release**
- **RAW format support**: 25+ formats (ARW, CR2, CR3, NEF, RAF, ORF, RW2, DNG, PEF, SRW, X3F, 3FR, FFF, RAW, RWL, DCR, K25, KDC, MOS, MRW, NRW)
- **Batch conversion engine** with recursive folder scanning
- **Lanczos high-quality resampling** for downscaling
- **Configurable JPEG quality** (50–100)
- **Copyright watermark system**:
  - Custom Unicode text support
  - Font size 8–48 pt
  - Bottom-right positioning with 1% margin
  - White text (80% opacity) + black shadow for universal readability
- **File naming options**:
  - Preserve original filenames
  - Custom prefix support
  - Auto-collision handling (`_1`, `_2`…)
- **Modern Windows 10/11 GUI** (tkinter/ttk):
  - Drag-and-drop inspired file selection
  - Real-time progress bar with percentage
  - Color-coded logging (success/error/info/warning)
  - Cancellable operations
- **Portable single-executable distribution** (32 MB)
- **Multi-threaded processing** — GUI remains responsive
- **No-install, no-registry, no-telemetry** design

### Technical
- Built with Python 3.12, PyInstaller 6.22
- Bundled dependencies: rawpy 0.27, Pillow 12.3, NumPy 2.5
- LibRaw 0.21+ for RAW decoding
- Thread-safe queue-based progress reporting

---

## [Unreleased] - Planned for v1.1

### Planned Features
- **Mirror folder structure** output option
- **EXIF preservation** (GPS, camera settings, orientation)
- **Color profile handling** (sRGB/Adobe RGB embedding)
- **Before/after preview pane** in GUI
- **Command-line interface** for automation
- **Preset profiles** (Web, Print, Archive, Social)
- **Multi-language support** (IT, EN, ES, FR, DE)
- **Custom watermark position** (9-point grid)
- **Watermark opacity slider**
- **Output format options** (JPEG, PNG, WebP)
- **Recursive progress estimation** for large folders

### Under Consideration
- **Video thumbnail extraction** (MP4, MOV → JPEG)
- **Sidecar XMP support** for non-destructive workflows
- **Shell extension** (right-click "Convert with Franchetti")
- **Auto-orient from EXIF** before watermark

---

## Version History Summary

| Version | Date | Type | Key Changes |
|---------|------|------|-------------|
| 2.50.1 | 2025-01-25 | Major | CIE Lab pipeline, tethering, cloud dispatch, watermark, EXIF |
| 1.0.0 | 2024-09-18 | Major | Initial release |
| 1.1.0 | TBD | Minor | EXIF, mirror output, presets, CLI |
| 1.2.0 | TBD | Minor | Preview, i18n, watermark positions |
| 2.0.0 | TBD | Major | Video, shell extension, XMP |

---

## Release Checklist (per version)

- [ ] Update version in `main.py`, `build_exe.py`, `version_info.txt`, `docs/index.html`
- [ ] Update CHANGELOG.md
- [ ] Run full test suite (manual + automated)
- [ ] Build signed executable
- [ ] Verify on clean Windows 10/11 VMs
- [ ] Create GitHub Release with artifacts
- [ ] Update uptodown.dev / FileCR / Itch.io listings
- [ ] Announce on channels

---

## Migration Guide

### From No Previous Version (Fresh Install)
Simply download and run `FranchettiRawConverterPro.exe`. No migration needed.

### Future Versions
Settings are stored in memory only (no config file). No migration required between versions.

---

## Deprecation Policy

- **Major versions** (x.0.0): May break CLI arguments, config formats
- **Minor versions** (x.y.0): Backward compatible, new features only
- **Patch versions** (x.y.z): Bug fixes only, fully compatible

Minimum support: **2 major versions** (current + previous).