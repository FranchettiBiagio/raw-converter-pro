# Changelog

All notable changes to Franchetti Raw Converter Pro are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.55.0] - 2026-10-27

### Added
- **Denoise ibrido ISO**: al guided filter si aggiunge **non-local means** applicato solo alle zone piatte (cieli, pareti, ombre). I dettagli strutturati restano affidati al coring, quindi la grana sparisce senza effetto plastica.
- **Nitidezza controllata**: maschera con soglia stimata sul rumore. La nitidezza non amplifica più la grana nelle aree uniformi.
- **Profilo predefinito qualità**: **3000 px**, JPEG **90**, denoise automatico **ON**, riduzione rumore **88/92**, nitidezza **0,9 / 0,9**.
- **Tethering multi-marca**: istruzioni per Canon, Nikon, Fujifilm, Panasonic, OM System e Leica tramite software del produttore + hot-folder. Sony conserva il controllo Wi-Fi diretto.

### Changed
- **RIMUOVI GRANA (AUTO ISO)** spostato subito sotto **PIÙ LUMINOSA** sia nel tab Batch sia nel tab Sviluppo RAW; è attivo di default.
- Tutti i preset ora usano denoise automatico, 3000 px (dove previsto), nitidezza controllata e nessuna grana sintetica di default.
- **PIÙ LUMINOSA**: limite più conservativo sulle ombre profonde, vividezza ridotta e rimosso il micro-contrasto finale che faceva riemergere la grana. L'esposizione resta applicata alla sola luminanza.
- Intestazione aggiornata a **Tethering multi-marca**.

### Fixed
- **Grana residua a 100%** dopo ridimensionamento e nitidezza: il nuovo ordine curva → denoise → nitidezza e la soglia sul rumore eliminano il residuo nelle zone piatte.
- **Notturni con PIÙ LUMINOSA**: l'esposizione automatica non spinge più al massimo le ombre, evitando immagini innaturalmente chiare e rumorose.
- **JPEG troppo grandi**: il profilo 3000 px / qualità 90 mantiene i file in genere tra 0,6 e 1,3 MB.

### Performance
- 4 RAW Sony A7S da 24 MP a **3000 px** con denoise automatico: **12,8 s** totali in batch, output **743 / 639 / 609 / 915 KB**.
- Conversione singola 3000 px: circa **8–9 s**; preset full-res con denoise non-locale: circa **40-45 s** per foto.
- Testata la qualità al 100% su pareti, statue e ritratti: texture reale conservata, grana piatta rimossa.

### Documentation
- Aggiornati README, guida completa Markdown/HTML, FAQ, note di rilascio, version info e installer per la **2.55.0**.

---

## [2.54.0] - 2026-10-27

### Added
- **RIMUOVI GRANA (AUTO ISO)**: un clic nel tab Batch e nel tab Sviluppo RAW
  - denoise in **Y/Cb/Cr** con guided filter: pulisce le zone piatte e conserva bordi e micro-textura
  - crominanza elaborata a meta' risoluzione (4x piu' veloce) e ricostruita con interpolazione lineare
  - forza adattata all'ISO del RAW (ISO 1000/2000/3200 testati), con possibilita' di regolare a mano
  - preset: luminanza 60, colore 70, nitidezza 1.25, raggio 1.2
- **PIU' LUMINOSA**: ora aumenta anche la **vividezza** (circa +15% di saturazione media), con esposizione applicata alla sola luminanza per non spostare i colori
- **GUIDA_COMPLETA.md** e **GUIDA_COMPLETA.html**: guida elementare a ogni funzione e impostazione, inclusa nell'installer e nel menu Start

### Changed
- Il RAW viene ridimensionato **prima** della pipeline: tono, colore, denoise e nitidezza lavorano sulla risoluzione finale
- Rimosse le conversioni CIE Lab: curva tonale e nitidezza lavorano direttamente sulla luminanza Y
- Batch: thread OpenMP/BLAS limitati a 1 per processo, per evitare oversubscription della CPU
- Numero di processi scelto in base alla RAM libera, con stima maggiore per originali 24-60 MP e denoise attivo
- JPEG salvato senza `optimize=True`: elimina l'errore libjpeg `Suspension not allowed here` / `broken data stream` nei batch paralleli

### Performance
- 4 RAW Sony A7S da 24 MP a 1920 px: **5,6 s** normali, **5,9 s** con denoise, **6,1 s** con PIU' LUMINOSA
- 4 RAW a risoluzione originale: **14,2 s** normali, **20,8 s** con denoise
- Nessun errore, nessun output corrotto e nessun file temporaneo residuo nei test

---

## [2.53.0] - 2026-10-27

### Added
- **Elaborazione multi-core**: conversione batch con `ProcessPoolExecutor` su tutti i core logici
  - numero di processi limitato automaticamente dalla RAM libera e dal numero di file
  - interruttore **USA TUTTI I CORE (N processi)** nel tab Batch, attivo di default
  - scrittura atomica (file temporaneo + `os.replace`), nessun output corrotto in caso di errore o annullamento
  - annullamento reattivo: i processi figli vengono terminati entro 0,2 s e i file `.tmp` residui vengono rimossi
  - misura su RAW Sony A7S 24 MP: 6 file da 67,6 s a 22,1 s (3,06x); 12 file in 39,8 s
- Modalita' di test `--batch-test <sorgente> <cartella>` per verificare il batch parallelo da riga di comando

### Fixed
- **Salvataggio JPEG**: alcune immagini facevano fallire `optimize=True` con `OSError: broken data stream`; ora il salvataggio riprova automaticamente senza ottimizzazione
- **Logo corrotto o illeggibile**: non blocca piu' la conversione (viene ignorato con avviso nel Log)
- **PIÙ LUMINOSA**: nessuna divisione per zero sulle immagini completamente bianche; le immagini gia' ottimali restano invariate
- **EXIF**: orientamento corretto (`Orientation = 1`) su RAW e JPEG; testato su ARW reale (Make, ISO, orientamento)
- **Configurazione**: tutti i valori numerici vengono ripuliti e limitati; un JSON corrotto o incompleto non blocca piu' la conversione; ripristino completo di checkbox, campi e cloud
- **Nomi duplicati nel batch**: due file con lo stesso nome non scrivono mai sullo stesso output; "Sovrascrivi" sostituisce i file esistenti ma non due lavori dello stesso batch
- **Nomi generati** (`mantieni_nomi` disattivo): usano correttamente `IMG_0001`, `IMG_0002`, … invece del nome sorgente
- **Hot-folder**: elabora anche JPEG/PNG/TIFF/WEBP, attende la fine della scrittura, gestisce i file spostati e ignora la propria cartella di output e i file `_PRO`
- **Download Sony**: nomi file univoci, nessuna sovrascrittura
- **Formati**: normalizzati `JPG → JPEG` e `TIF → TIFF`; un formato sconosciuto ripiega su JPEG
- **Percorsi duplicati**: la lista sorgente con `;` viene deduplicata e la cartella di output esclusa dalla ricerca ricorsiva
- **Cartella di output superiore alla sorgente**: non esclude piu' tutti i file (l'esclusione scatta solo se l'output e' dentro la sorgente)
- **Protezione originali**: se il percorso di output coincide con il file sorgente, la conversione viene rifiutata senza sovrascrivere nulla
- **Immagini minuscole** (1x1, 2x2, 1x200): pipeline, watermark e logo senza errori
- **Preset**: sincronizza anche la casella EXIF
- **Cloud**: Google Drive, Meta e SwissTransfer sono chiaramente indicati come non attivi; Telegram e Dropbox restano operativi

### Changed
- Spazio colore fissato a **sRGB** (profilo ICC incorporato), coerente con l'output reale; rimosse le opzioni Adobe RGB/ProPhoto non implementate
- **Tab Batch a due colonne**: tutte le impostazioni, i preset e i comandi sono visibili senza scorrimento anche a 1024x720
- Intestazione compatta e sempre leggibile: `v2.53.0 | LibRaw | Multi-core | Tethering & Cloud`

---

## [2.52.1] - 2026-10-26

### Fixed
- **Conversione RAW non funzionante**: la libreria inclusa non supporta l'algoritmo AMAZE e ogni file terminava con `NotSupportedError`. Ora il programma prova AMAZE, poi AHD, PPG e LINEAR, memorizzando quello disponibile
- Aggiunta modalita' di test da riga di comando (`--converti-test`) per verificare la conversione senza aprire la finestra

---

## [2.52.0] - 2026-10-26

### Added
- **PIÙ LUMINOSA (BETA)**: correzione automatica dell'esposizione, attivabile nel tab Batch e nel tab Sviluppo RAW
  - schiarisce le foto scure portando la luminosità mediana verso il centro
  - riduce e comprime le alte luci delle foto troppo esposte
  - lascia invariate le foto gia' bilanciate
  - ginocchio morbido per non bruciare i bianchi; LUT a 256 livelli (circa 0,6 s su 24 MP)

---

## [2.51.4] - 2026-10-26

### Added
- **Batch**: il lato lungo si sceglie da misure pronte in ordine crescente (640, 800, 1024, 1200, 1600, 1920, 2048, 2560, 3000, 4000, 6000, Originale)
- La misura attiva e' evidenziata in verde; resta possibile scrivere un valore personalizzato

---

## [2.51.3] - 2026-10-26

### Fixed
- **Stato "connessa ma scatto non disponibile"**: se la A7S resta in uno stato intermedio, il programma esegue un ciclo `stopRecMode`/`startRecMode` e riattiva lo scatto remoto
- `SCATTA E SCARICA` verifica e riattiva la modalita' remota prima di scattare, invece di fallire
- Etichetta Sony distingue "pronta" da "raggiungibile ma non pronta"
- Connessione automatica all'avvio quando il PC e' gia' sulla rete `192.168.122.x`

### Added
- Log su file in `Desktop\franchetti_log.txt` per diagnosticare i problemi

---

## [2.51.2] - 2026-10-26

### Fixed
- **Connessione Sony A7S**: l'indirizzo dell'API non e' piu' fisso sulla porta 10000; viene letto dalla descrizione SSDP della fotocamera (sulla A7S e' `http://192.168.122.1:8080/sony`)
- Chiamate API compatibili sia con il servizio `system` sia con `camera` (la A7S non espone `system`)
- Dopo `startRecMode` il programma attende che la fotocamera sia pronta prima di dichiarare la connessione riuscita
- Aggiornamento dell'etichetta di stato Sony dal thread corretto

### Verified
- Test reale su Sony A7S (Smart Remote Control SR/4.30): connessione, scatto e download JPEG funzionanti

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