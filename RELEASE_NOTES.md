# Release Notes v2.58.1

**Franchetti Raw Converter Pro** - Release v2.58.1  
**Data**: 12 Novembre 2026  
**Build**: 2.58.1.0

---

## Preset nativi, LUT e sviluppo più veloce

La 2.58.1 aggiunge un sistema di preset portabile, l'import XMP in beta, le
LUT 3D `.cube` e un profilo **Veloce** sensibilmente più rapido. Windows resta
il target principale: la pipeline predefinita non cambia.

---

## Preset `.frcpreset`: solo dati, mai codice

Un preset è un file JSON leggibile con:

- nome, autore, descrizione, tag e versione minima dell'app;
- una sezione `look` con tono, colore, curva, denoise, nitidezza, grana,
  vignettatura e split toning;
- una sezione `output` facoltativa con formato, lato lungo, qualità ed EXIF.

Non può contenere percorsi, cartelle, credenziali cloud, FTP o copyright.
Applicarlo non cambia mai il flusso di lavoro e non tocca gli originali.

I sei preset storici sono migrati nel nuovo formato:

| Preset | Output | Uso |
|---|---|---|
| Web / Social | JPEG 2048 px, q90 | web e social |
| Stampa Fine Art | TIFF pieno, q100 | stampa |
| Archivio JPEG | JPEG pieno, q95, EXIF | archivio |
| Ritratto | JPEG 3000 px, q92 | persone |
| Paesaggio | JPEG 3000 px, q92 | natura |
| Bianco e Nero | JPEG 3000 px, q92 | monocromo |

In **AVANZATE** puoi salvare il look corrente, importare, esportare, eliminare
e applicare un preset con anteprima. I preset personali stanno nella cartella
dati dell'utente, non accanto all'EXE.

---

## Pacchetti scaricabili con checksum

Un pacchetto è uno ZIP (o una cartella) con `manifest.json` e i file
`.frcpreset`. Ogni voce ha un checksum **SHA-256**: se non corrisponde, il file
viene rifiutato. L'importazione è sempre manuale, nessun download automatico.

Il pack ufficiale di esempio è in
[`presets_pack/`](presets_pack/README.md): Cinema caldo, Paesaggio freddo,
Ritratto soft.

---

## Import XMP (beta)

I preset Lightroom `.xmp` vengono letti e mappati in modo parziale:

- esposizione, luci, ombre, bianchi, neri, contrasto;
- vivacità, saturazione, chiarezza, dehaze;
- riduzione rumore, nitidezza, vignettatura, grana;
- saturazione selettiva rosso/verde/blu e split toning.

Restano fuori profili camera, curve puntuali, texture e film simulation. L'app
lo dice chiaramente prima di applicare il preset. Non è una conversione 1:1 e
non promette una resa identica a Lightroom.

---

## LUT 3D `.cube`

Le LUT creative si applicano con interpolazione trilineare e intensità
regolabile. Il calcolo avviene a blocchi, così una foto da 24-60 MP non alloca
centinaia di MB. Se il file non è leggibile, l'immagine resta invariata e il
log lo segnala.

La LUT non entra nei preset: un preset resta un file di dati, non un
riferimento a un percorso del computer.

---

## Profilo Veloce: -39% sul test

Il collo di bottiglia era il denoise non-locale. Nel profilo **Veloce** ora
lavora a metà risoluzione e la stima del rumore usa un ritaglio centrale di
1024 px. Misura su RAW sintetico da 24 MP portato a 3000 px:

| Scenario | Prima | Dopo |
|---|---|---|
| Pipeline completa, Bilanciato | 8,8 s | 8,8 s |
| Pipeline completa, Veloce | 9,1 s | 5,4 s |

Nel test, l'output di **Bilanciato** resta identico pixel per pixel: la stima
campionata e il denoise a metà risoluzione sono attivi solo in **Veloce**.
Gli altri profili mantengono la resa precedente.

Le micro-ottimizzazioni (luminanza riusata tra le fasi, stima del rumore
condivisa) non cambiano i valori elaborati.

---

## Linux: correzioni sperimentali

- filtro file **`.RAF` maiuscolo** nel dialogo di apertura;
- core fisici letti da `/proc/cpuinfo` (prima una VM da 2 vCPU restava a un
  solo processo);
- memoria disponibile da `/proc/meminfo`;
- chiusura del pool con `wait=True` per non lasciare semafori;
- `gc.collect()` + `malloc_trim(0)` per restituire memoria al sistema;
- messaggio di dipendenza mancante più chiaro;
- build Linux/macOS documentata come **sperimentale**.

Su Windows il comportamento resta quello della 2.58.0.

---

## Compatibilità

- **Windows 10/11 x64**, portable o installer.
- Gli originali non vengono mai modificati.
- EXIF preservato nei formati supportati.
- Configurazioni e flussi di lavoro precedenti restano validi.
- Nessuna nuova dipendenza Python: LUT, XMP e preset usano la libreria standard.
- La build Linux/macOS è sperimentale e richiede `python3-tk`.

---

## Download v2.58.1

- **Portable**: `FranchettiRawConverterPro.exe`
- **Installer**: `Franchetti_Raw_Converter_Setup_v2.58.1.exe`
- **Pack preset**: `presets_pack.zip`

Gli hash SHA-256 aggiornati sono riportati in `SHA256SUMS.txt` e nella pagina
della release GitHub.

---

## Cronologia

Le note complete delle versioni precedenti sono in
[`CHANGELOG.md`](CHANGELOG.md).

Per assistenza, salva il **Log** e descrivi il passaggio che ha causato il
problema.
