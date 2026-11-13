# Note per la certificazione — testo pronto

Da incollare in Partner Center → **Submission options** (o *Notes for
certification*) quando si invia il pacchetto MSIX.

Contenuto verificato sul codice di `main.py` il 13/11/2026.

---

## Versione inglese (consigliata)

> **App:** Franchetti Raw Converter Pro — desktop RAW converter for
> photographers.
>
> **Package:** MSIX, x64, desktop full-trust application (`runFullTrust`),
> single executable, no services, no drivers, no startup tasks.
>
> **No account required.** The app works fully offline for conversion; there
> is no login, no subscription and no license check.
>
> **No telemetry.** The app does not collect analytics, crash reports,
> advertising identifiers or personal data.
>
> **Network usage (only user-initiated):**
>
> 1. **Camera tethering** — when the user starts tethering, the app talks to a
>    Sony camera on the **local network** (camera HTTP API).
> 2. **Sharing/upload** — when the user explicitly configures a Telegram bot
>    token or Dropbox credentials and presses the share/upload button, files
>    are sent to that service. Nothing is uploaded automatically.
>
> **Data storage:** settings and presets are stored in
> `%APPDATA%\FranchettiRawConverterPro`. Converted files are written only to
> the folder chosen by the user. Original photos are never modified.
>
> **How to test (no credentials or sample files needed):**
>
> 1. Launch the app from the Start menu.
> 2. Open any RAW, JPEG or TIFF image (drag & drop or "Apri").
> 3. Select one of the built-in presets.
> 4. Choose an output folder and start the conversion.
> 5. Verify that the converted file appears in the output folder.
>
> **Hardware:** no special hardware required. Camera tethering is optional and
> can be ignored during review.
>
> **Uninstall:** removes the application only; user documents and converted
> images are left untouched.

---

## Versione italiana

> **App:** Franchetti Raw Converter Pro — convertitore RAW desktop per
> fotografi.
>
> **Pacchetto:** MSIX, x64, applicazione desktop full-trust
> (`runFullTrust`), singolo eseguibile, nessun servizio, nessun driver,
> nessuna attività di avvio automatico.
>
> **Nessun account richiesto.** L'app funziona interamente offline per la
> conversione; non ci sono login, abbonamenti o verifiche di licenza.
>
> **Nessuna telemetria.** L'app non raccoglie statistiche, segnalazioni di
> errore, identificatori pubblicitari o dati personali.
>
> **Uso della rete (solo su azione dell'utente):**
>
> 1. **Tethering fotocamera** — quando l'utente avvia il tethering, l'app
>    comunica con una fotocamera Sony sulla **rete locale** (API HTTP della
>    fotocamera).
> 2. **Condivisione/upload** — quando l'utente configura esplicitamente un
>    token bot Telegram o le credenziali Dropbox e preme il pulsante di invio,
>    i file vengono inviati a quel servizio. Nessun upload automatico.
>
> **Dove sono salvati i dati:** impostazioni e preset in
> `%APPDATA%\FranchettiRawConverterPro`. I file convertiti vengono scritti
> solo nella cartella scelta dall'utente. Le foto originali non vengono mai
> modificate.
>
> **Come provare l'app (nessuna credenziale o immagine di esempio
> necessaria):**
>
> 1. Avviare l'app dal menu Start.
> 2. Aprire un'immagine RAW, JPEG o TIFF (trascinamento o "Apri").
> 3. Selezionare uno dei preset inclusi.
> 4. Scegliere una cartella di output e avviare la conversione.
> 5. Verificare che il file convertito compaia nella cartella di output.
>
> **Hardware:** nessun hardware particolare richiesto. Il tethering è
> opzionale e può essere ignorato durante la revisione.
>
> **Disinstallazione:** rimuove solo l'applicazione; documenti e immagini
> convertite restano invariati.

---

## Dichiarazioni da tenere coerenti

| Affermazione | Verifica nel codice |
|---|---|
| Nessun login / licenza | nessun controllo di account o chiave |
| Nessuna telemetria | nessun SDK analytics, nessun invio automatico |
| Rete solo locale o su azione utente | API Sony su rete locale; Telegram/Dropbox solo su pulsante |
| Dati in `%APPDATA%` | `cartella_dati_utente()` in `main.py` |
| Originali mai modificati | output in cartella separata scelta dall'utente |
| Nessuna scrittura nel registro | nessun uso di `winreg` |
| Nessun avvio automatico / updater | nessuna voce di startup, nessun download di eseguibili |

Se in futuro viene aggiunto un controllo aggiornamenti o un servizio di
telemetria, queste note vanno aggiornate **prima** dell'invio.
