# Partner Center → Packages — valori da inserire (v2.58.1)

Pagina: **App e giochi → Franchetti Raw Converter Pro → Packages → Dettagli
del pacchetto**.

Valori verificati il 13/11/2026. Riutilizzabili per le versioni future
cambiando solo URL e versione.

## Campi

| Campo Partner Center | Valore |
|---|---|
| **URL del pacchetto** | `https://www.franchettitv.it/downloads/Franchetti_Raw_Converter_Setup_v2.58.1.exe` |
| **Architettura** | `x64` |
| **Parametri dell'installatore** | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-` |
| **Lingue** | Italiano (aggiungi English solo se la scheda è multilingua) |
| **Tipo di app** | `EXE` |
| **Checkbox "Installatore viene eseguito in modalità silenziosa, ma non richiede interruttori"** | ❌ **non selezionare** (forniamo noi gli interruttori) |
| **URL documentazione codici di ritorno** | `https://jrsoftware.org/ishelp/topic_setupexitcodes.htm` |

## Codici di ritorno EXE

Codici reali di Inno Setup 7 (`Setup Exit Codes`), non convenzioni MSI:

| Codice | Significato |
|---|---|
| `0` | Installazione completata con successo |
| `1` | Setup non riuscito ad inizializzarsi |
| `2` | Utente ha annullato prima dell'inizio dell'installazione |
| `3` | Errore fatale durante la preparazione della fase successiva |
| `4` | Errore fatale durante l'installazione |
| `5` | Utente ha annullato durante l'installazione / Abort |
| `6` | Processo terminato dal debugger (non applicabile in produzione) |
| `7` | La fase "Preparing to Install" ha stabilito che non si può procedere |
| `8` | Come 7, ma serve un riavvio per correggere il problema |

### Mappatura sugli scenari richiesti

| Scenario Partner Center | Valore | Note |
|---|---|---|
| Installazione riuscita | `0` | **obbligatorio**, è il codice che conta |
| Installazione annullata dall'utente | `2`, `5` | annullamento prima e durante |
| Riavvio richiesto | `8` | l'installer non richiede mai riavvio, ma il codice esiste |
| Applicazione esiste già | *(vuoto)* | Inno aggiorna e ritorna `0` |
| Installazione già in corso | *(vuoto)* | bloccata dal mutex di Inno, non gestita come scenario |
| Spazio su disco pieno | *(vuoto)* | errore generico `4` |
| Fallimento della rete | *(vuoto)* | l'installer è offline, nessuna rete coinvolta |
| Pacchetto rifiutato da policy | *(vuoto)* | errore generico `3`/`7` |
| Vari scenari di guasto | *(vuoto)* | errore generico `4` |

Se un campo non accetta il valore vuoto, usare il codice indicato nella colonna
"Note": sono i codici generici con cui Inno segnala quella classe di problema.

## Perché il dominio proprio e non GitHub

L'asset GitHub risponde con redirect verso `objects.githubusercontent.com`:
la validazione di Partner Center può fallire con errore di download.
`https://www.franchettitv.it/downloads/...` serve il file con HTTP 200 diretto,
`Accept-Ranges: bytes`, TLS Let's Encrypt valido, SHA256 identico all'asset
GitHub (`316a34c1…b86405`).

## Dopo la compilazione

1. **Salvare la bozza**.
2. Leggere eventuali errori di validazione (la verifica parte al salvataggio).
3. Compilare **Note per la certificazione** con
   [`CERTIFICATION_NOTES_EXE_v2.58.1.md`](CERTIFICATION_NOTES_EXE_v2.58.1.md).
4. **Invia per la certificazione**.
