# Release Notes v2.58.2

**Franchetti Raw Converter Pro** - Release v2.58.2
**Data**: 18 Novembre 2026
**Build**: 2.58.2.0

---

## Manutenzione: log reperibili e build Linux che non si moltiplica

La 2.58.2 non cambia la resa delle immagini. Chiude due problemi concreti:
il file di log finiva in una cartella che su Linux spesso non esiste, e la
build Linux impacchettata poteva riaprire copie di sé stessa fino a esaurire
RAM e swap. Su Windows la pipeline, i parametri e gli output restano quelli
della 2.58.1.

---

## Il log ora è in una cartella valida su ogni sistema

Prima `franchetti_log.txt` veniva scritto in `~/Desktop`. Su Linux quella
cartella si chiama `Scrivania`, in tedesco `Schreibtisch`, e con un desktop
diverso non esiste affatto: il file semplicemente non compariva.

Ora il log va nella cartella dati dell'app, creata se manca:

| Sistema | Percorso |
|---|---|
| Windows | `%APPDATA%\FranchettiRawConverterPro\franchetti_log.txt` |
| Linux | `~/.local/share/FranchettiRawConverterPro/franchetti_log.txt` |
| macOS | `~/Library/Application Support/FranchettiRawConverterPro/franchetti_log.txt` |

Lo stesso vale per `sony_diagnosi.txt`, che prima finiva sul Desktop.

Su Windows il file non è più sul Desktop: se lo cercavi lì, ora è in
`%APPDATA%\FranchettiRawConverterPro`.

---

## Riga di avvio nel log

Ogni sessione inizia con una riga di contesto:

```text
Avvio: Python 3.12.8, win32, PID 1234, PPID 987, impacchettato=True,
metodo processi=spawn, argomenti=[]
```

Con versione di Python, PID, processo padre, metodo di avvio dei processi e
argomenti si riconosce subito un avvio anomalo o una copia indesiderata.

---

## Linux: perché l'applicazione si moltiplicava

Da **Python 3.14** il metodo predefinito per creare processi su Linux è
`forkserver` (prima era `fork`). `spawn` e `forkserver` non funzionano con un
eseguibile PyInstaller `--onefile`: ogni worker riapre il programma intero, che
si ri-estrae in `/tmp/_MEI…` e apre altri worker. Il risultato era un ciclo di
copie: `/tmp` piena, `libpython` non più trovato, `resource_tracker` che
rilancia, e alla fine il processo terminato dal sistema (`Ucciso`).

Cosa cambia nella 2.58.2:

- quando il programma è **impacchettato su Linux o macOS**, il batch usa i
  **thread** invece dei processi separati: il ciclo non può più partire;
- la build Linux passa a **`--onedir`**: i file restano accanto all'eseguibile
  e non vengono estratti in `/tmp` a ogni avvio;
- `build_exe.py` avvisa se la Python usata è **3.14 o superiore** e consiglia
  3.11 o 3.12;
- l'override manuale resta disponibile: `FRC_THREADS=1` forza i thread,
  `FRC_ONEFILE=1` riporta la build a `--onefile`.

La build Linux/macOS resta **sperimentale**: non è stata provata su tutte le
distribuzioni. L'avvio dalla sorgente (`python3 main.py`) non è interessato dal
problema.

---

## Diagnosi guidata su Linux

Nuovo script `tools/diagnosi_linux.sh`: avvia l'applicazione, campiona ogni tre
secondi memoria libera, numero di copie del processo e processi più pesanti,
poi chiude tutto e scrive un report in `~/diagnosi-frc.txt`.

```bash
bash tools/diagnosi_linux.sh
```

Serve a distinguere due casi che dal solo log si confondono: un ciclo di copie
dell'applicazione, oppure una crescita di memoria dentro un singolo processo.

---

## Cosa non cambia su Windows

- Pipeline Y/Cb/Cr, profili di prestazione, preset, LUT, XMP, Smart Batch,
  tethering, Cloud Dispatch e galleria cliente restano identici alla 2.58.1.
- Nessuna nuova dipendenza Python.
- Gli originali restano in sola lettura e non vengono mai modificati.
- I preset e le configurazioni salvate restano validi.

---

## Compatibilità

- **Windows 10/11 x64**, portable o installer.
- **Linux/macOS**: build sperimentale, richiede `python3-tk`.
- EXIF preservato nei formati supportati.
- Configurazioni e flussi di lavoro precedenti restano validi.

---

## Download v2.58.2

- **Portable**: `FranchettiRawConverterPro.exe`
- **Installer**: `Franchetti_Raw_Converter_Setup_v2.58.2.exe`
- **Pack preset**: `presets_pack.zip`

Gli hash SHA-256 sono pubblicati nella pagina della release.

---

## Cronologia

Le note complete delle versioni precedenti sono in
[`CHANGELOG.md`](CHANGELOG.md).

Per assistenza, allega il file `franchetti_log.txt` e descrivi il passaggio che
ha causato il problema.
