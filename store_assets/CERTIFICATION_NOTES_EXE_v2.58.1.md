# Note per la certificazione — sottomissione EXE v2.58.1

Da incollare nel campo **Notes for certification** (Note per la certificazione)
in Partner Center. Contiene la versione inglese (usata dai tester) e quella
italiana.

Riferimenti della sottomissione:

| Campo | Valore |
|---|---|
| Prodotto | Franchetti Raw Converter Pro — `XP9CJZTBCW6VS7` |
| Versione attuale live | 1.0.0 |
| Nuova versione | 2.58.1 |
| Package URL | `https://github.com/FranchettiBiagio/raw-converter-pro/releases/download/v2.58.1/Franchetti_Raw_Converter_Setup_v2.58.1.exe` |
| SHA256 installer | `316a34c16d45f6e3cca05e517b95797d83bc0e88adf4199659025e4cb1b86405` |
| Tipo | EXE (Inno Setup 7), x64 |
| Parametri silent | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-` |
| Codice di ritorno successo | `0` |

---

## English (paste this)

```
Update of an existing Store product (currently 1.0.0) to version 2.58.1.

INSTALLER
The installer is a single offline Inno Setup executable, x64. It downloads
nothing during setup: the application binary and all its dependencies are
embedded in the installer. Silent switches: /VERYSILENT /SUPPRESSMSGBOXES
/NORESTART /SP-, exit code 0 on success, 2 on user cancel. No restart is
requested and none is required.

The installation is per-user and does not require elevation: files are placed
in %LOCALAPPDATA%\Programs\Franchetti Raw Converter Pro, a Start Menu shortcut
and an optional desktop shortcut are created, and a standard uninstaller is
installed. No services, no drivers, no kernel components, no scheduled tasks,
no registry keys outside the user's uninstall entry.

The installer is not Authenticode-signed, consistent with the package already
published for this product on the Store for version 1.0.0.

FUNCTIONALITY
Franchetti Raw Converter Pro is a desktop RAW converter for photographers. It
reads camera RAW files (Sony ARW, Canon CR2/CR3, Nikon NEF, Fujifilm RAF,
Olympus ORF, Panasonic RW2, DNG and others) and writes JPEG or TIFF files to
an output folder chosen by the user. Processing is batch and runs entirely on
the local CPU. The application never modifies, moves or deletes the original
RAW files: source files are only read.

The application works fully offline and does not require an account, a login,
a subscription or an internet connection. No telemetry, no analytics and no
network calls are performed. No user content is uploaded anywhere.

Presets are plain JSON data files created by the user; the application does
not execute them.

TESTING NOTES
No test account is needed. After installation, launch the app, drag a folder
containing RAW files onto the window (or use "Seleziona cartella"), choose an
output folder and press "Converti". A sample RAW file is not required: any
supported RAW file can be used. The app starts with an empty state and does
not require configuration.

The uninstaller removes the application directory completely.
```

---

## Italiano (per riferimento)

```
Aggiornamento di un prodotto già pubblicato sullo Store (versione 1.0.0) alla
versione 2.58.1.

INSTALLER
Installer Inno Setup unico e offline, x64. Non scarica nulla durante il setup:
il binario dell'applicazione e tutte le dipendenze sono incorporati.
Parametri silent: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-, codice di
uscita 0 in caso di successo, 2 in caso di annullamento. Nessun riavvio.

L'installazione è per-utente e non richiede elevazione: i file vanno in
%LOCALAPPDATA%\Programs\Franchetti Raw Converter Pro, vengono creati un
collegamento nel menu Start e uno opzionale sul desktop. Nessun servizio,
nessun driver, nessuna attività pianificata.

L'installer non è firmato Authenticode, coerentemente con il pacchetto già
pubblicato sullo Store per la versione 1.0.0 di questo prodotto.

FUNZIONALITÀ
Convertitore RAW desktop per fotografi: legge file RAW e scrive JPEG/TIFF in
una cartella di output scelta dall'utente. Elaborazione batch interamente su
CPU locale. I file originali non vengono mai modificati, spostati o cancellati.

L'applicazione funziona completamente offline, senza account, login o
abbonamento. Nessuna telemetria e nessuna chiamata di rete.

I preset sono file JSON di dati creati dall'utente e non vengono eseguiti.
```
