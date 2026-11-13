# Partner Center → Packages — come si compila davvero (v2.58.1)

Fonte: Microsoft Learn, *Upload app packages for MSI/EXE app* e *App package
requirements for MSI/EXE app*, consultate il 13/11/2026.

Questo file corregge le indicazioni precedenti, che davano per obbligatoria la
sezione dei codici di ritorno e un campo versione inesistente.

## Regole verificate sulla documentazione

| Campo | Obbligatorio | Note |
|---|---|---|
| Package URL | ✅ sì | URL versionato, HTTPS, diretto, immutabile |
| Architecture | ✅ sì | x64 per questo prodotto |
| Languages | ✅ sì | Italiano (`it`, `it-it`) |
| App type | ✅ sì | EXE |
| Installer parameters | ✅ sì (per EXE) | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-` |
| **Installer handling — URL documentazione** | ✅ **sì** | La sezione ha l'asterisco: il campo obbligatorio è **solo l'URL** in alto |
| Codici di ritorno per scenario | ❌ no | Nessun asterisco: si possono lasciare vuoti |
| **Versione** | ❌ **non esiste** | *"Package version numbering for Win32 is not supported"*: la versione è quella dell'installer |

La sezione dei codici serve solo a far mostrare allo Store messaggi mirati
all'utente. Se compilata, ogni codice deve essere **unico** in tutta la pagina
(errore: *"Il pacchetto non può avere valori di codice di ritorno duplicati"*).
Se non compilata, non manca nulla.

**Verifica sugli screenshot ufficiali dell'interfaccia** (scaricati da
Microsoft Learn il 13/11/2026): l'intestazione è `Installer handling *` e sotto
c'è un unico campo, `Enter a valid URL`. Le caselle "EXE return code value"
degli otto scenari **non hanno asterisco**. L'errore *"Alcuni campi richiedono
la vostra attenzione"* con la sezione apparentemente compilata è causato dal
**campo URL lasciato vuoto**, non dai codici.

Valore da inserire:

```
https://jrsoftware.org/ishelp/topic_setupexitcodes.htm
```

## Flusso corretto della pagina

La pagina funziona in due passaggi, ed è qui che si creano i conflitti:

1. **Manage packages** → elenco dei pacchetti già presenti (contiene la 1.0.0).
2. **Add package** crea un *nuovo* pacchetto. Se esiste già un pacchetto con la
   stessa architettura + lingua, Partner Center risponde:
   *"Il pacchetto con l'architettura e il linguaggio forniti esiste già"*.
3. Per un **aggiornamento** non si usa "Add package": si **seleziona il
   pacchetto esistente** dall'elenco e si modifica il suo Package URL.
4. **Save draft** → si torna all'elenco dei pacchetti.
5. **Save All** → upload e validazione dell'URL.

## Procedura per la v2.58.1

1. **Packages** → **Manage packages**.
2. Nell'elenco, **seleziona il pacchetto già presente** (quello della 1.0.0,
   x64, italiano). Non creare un pacchetto nuovo.
3. Nel campo **Package URL** sostituisci il vecchio indirizzo con:
   ```
   https://www.franchettitv.it/downloads/Franchetti_Raw_Converter_Setup_v2.58.1.exe
   ```
4. Lascia invariati: Architecture `x64`, Languages `Italiano`, App type `EXE`.
5. Parametri: `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`.
6. **Svuota completamente la sezione "Installer handling"**: nessun codice,
   nessuna riga aggiuntiva.
7. **Save draft**, poi **Save All**.
8. Attendi l'esito della validazione dell'URL.

## Perché l'URL sul dominio proprio

`https://www.franchettitv.it/downloads/Franchetti_Raw_Converter_Setup_v2.58.1.exe`
risponde HTTP 200 diretto (`nginx/1.22.1`), 101.165.696 byte, TLS Let's Encrypt
valido fino all'11/02/2027, `Accept-Ranges: bytes`, SHA256
`316a34c16d45f6e3cca05e517b95797d83bc0e88adf4199659025e4cb1b86405`, identico
all'asset della release GitHub. L'asset GitHub reindirizza a
`objects.githubusercontent.com` e può far fallire il download del validatore.

## Codici di ritorno (solo se in futuro si volesse compilare la sezione)

Codici reali di Inno Setup 7 (`Setup Exit Codes`), da usare **uno solo per
riga**, senza ripetizioni:

| Codice | Significato Inno |
|---|---|
| 0 | Installazione completata |
| 1 | Setup non riuscito ad inizializzarsi |
| 2 | Annullamento prima dell'installazione |
| 3 | Errore fatale in preparazione |
| 4 | Errore fatale durante l'installazione |
| 5 | Annullamento durante l'installazione |
| 6 | Terminato dal debugger (mai in produzione) |
| 7 | Impossibile procedere |
| 8 | Impossibile procedere, serve riavvio |

La corrispondenza tra questi codici e gli scenari di Partner Center è una
scelta del singolo installer, non una regola imposta: è per questo che la
sezione è facoltativa.

## Attenzione: firma richiesta dalla documentazione

La pagina *App package requirements* impone che installer e tutti i PE siano
firmati con certificato che catena al Microsoft Trusted Root Program. La
versione 1.0.0 pubblicata sullo Store è però `NotSigned` e la scheda è live.
Resta quindi un rischio da verificare in certificazione: vedi
[`PUBLISH_EXE_FREE.md`](PUBLISH_EXE_FREE.md).
