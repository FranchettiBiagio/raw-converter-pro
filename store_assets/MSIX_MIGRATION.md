# Da EXE/MSI a MSIX — pubblicazione gratuita sullo Store

Percorso scelto: **MSIX firmato da Microsoft Store**. Zero certificati,
zero abbonamenti, zero SmartScreen. Il pacchetto viene firmato localmente con
un certificato self-signed solo per i test; Microsoft lo ri-firma con il
proprio certificato dopo la certificazione.

Stato: pacchetto **costruito, firmato e installato con successo** su questa
macchina il 13/11/2026.

---

## 1. Perché MSIX

| Voce | EXE/MSI | MSIX |
|---|---|---|
| Certificato Authenticode | obbligatorio, a pagamento | **non serve** |
| Firma | tua, con CA pubblica | Microsoft ri-firma |
| SmartScreen | dipende dalla reputazione | non si applica |
| Aggiornamenti | gestiti dall'app/installer | gestiti dallo Store |
| Costo | 0 € solo con SignPath (firma a nome terzi) | **0 €** |

Riferimento Microsoft: per i pacchetti MSIX lo Store applica la firma e non
richiede alcun certificato allo sviluppatore.

---

## 2. Cosa è già pronto nel repository

| File | Ruolo |
|---|---|
| `msix/AppxManifest.xml.template` | manifest con segnaposto `{{IDENTITY_NAME}}`, `{{PUBLISHER}}`, `{{VERSION}}` |
| `tools/build_msix.py` | crea layout, asset tile da `icon_512.png`, esegue `makeappx pack` |
| `tools/sign_msix_dev.ps1` | certificato self-signed, firma, installazione di prova |
| `tools/build_store_msix.ps1` | build + firma + verifica con l'identità reale di Partner Center |
| `Output/FranchettiRawConverterPro_2.58.1.0_x64.msix` | pacchetto generato (circa 95 MB) |

Strumenti: `makeappx.exe` e `signtool.exe` da *Windows SDK Build Tools*
(`tools/sdkbuildtools`, ignorato da git).

### Comandi

```powershell
# Build del pacchetto (identita' provvisoria)
python tools\build_msix.py

# Firma + installazione di prova (richiede shell amministratore)
.\tools\sign_msix_dev.ps1 -Package "Output\FranchettiRawConverterPro_2.58.1.0_x64.msix" -Install

# Disinstallazione della copia di prova
Get-AppxPackage -Name "FranchettiAcademy.FranchettiRawConverterPro" | Remove-AppxPackage
```

### Verifica eseguita

- `makeappx pack` → pacchetto x64 creato.
- `signtool sign` → firma applicata (self-signed, `UnknownError` atteso finché
  il certificato non è nei trust store).
- `Add-AppxPackage` → installazione in `C:\Program Files\WindowsApps\...`.
- Avvio da `shell:AppsFolder\...!App` → finestra
  `Franchetti Raw Converter Pro v2.58.1`.
- Disinstallazione → completata, nessun residuo.

> Nota tecnica: `signtool` ignora i certificati senza EKU **Code Signing**
> (`1.3.6.1.5.5.7.3.3`) e restituisce
> `No certificates were found that met all the given criteria`. Lo script
> crea il certificato con `-Type CodeSigningCert`, quindi il problema non si
> ripresenta. Per l'installazione di prova il certificato va inserito in
> `LocalMachine\TrustedPeople` **e** `LocalMachine\Root`, altrimenti
> `Add-AppxPackage` fallisce con `0x800B0109`.

> Nota Store: Microsoft documenta che per la distribuzione via Store la firma
> è gestita dal servizio. Il pacchetto che carichiamo è comunque firmato con
> subject **identico** a `Package/Identity/Publisher`, che è la forma
> validata in upload; dopo la certificazione Microsoft ri-firma il pacchetto
> con il proprio certificato.

---

## 3. Il vincolo di Partner Center

Il prodotto attuale `XP9CJZTBCW6VS7` è di tipo **EXE/MSI**. Partner Center
**non permette di cambiare il tipo di pacchetto** di un prodotto esistente:
la pagina *Packages* accetta solo un URL di installer, non un `.msix`.

Due strade:

### A. Richiesta al supporto Microsoft (mantiene ID, recensioni, installazioni)

Partner Center → **Help + support** → **New support request** →
*Publishing and submissions* → *App package / package type*.

Testo completo, campi da compilare e risposte alle domande tipiche:
[`PARTNER_CENTER_MSIX_SUPPORT_REQUEST.md`](PARTNER_CENTER_MSIX_SUPPORT_REQUEST.md).

Testo pronto (inglese):

> Subject: Change existing product package type from EXE/MSI to MSIX
>
> Hello,
> I publish the app "Franchetti Raw Converter Pro" (product ID
> XP9CJZTBCW6VS7) as an EXE/MSI package. I have built an MSIX package for the
> same app and I would like to publish future updates as MSIX, keeping the
> existing product ID, reviews and installs.
> Could you please convert the product package type from EXE/MSI to MSIX, or
> advise the correct procedure?
> The MSIX package is ready: identity
> FranchettiAcademy.FranchettiRawConverterPro, version 2.58.1.0, x64,
> desktop full-trust application.
> Thank you.

Tempi tipici: alcuni giorni lavorativi. Se il supporto rifiuta, resta la
strada B.

**Stato:** richiesta aperta il **13/11/2026**, numero
**2611130050000788**, risposta prevista entro 8 ore, contatto via email
(`reportage@libero.it`).

### B. Nuovo prodotto MSIX (nessuna attesa, si riparte da zero)

1. Partner Center → **New product** → **MSIX or PWA app**.
2. Nome disponibile: `Franchetti Raw Converter Pro`.
3. In **Product identity** compaiono i due valori da usare nel manifest:

| Campo Partner Center | Esempio | Uso nel manifest |
|---|---|---|
| Package/Identity/Name | `12345FranchettiAcademy.FranchettiRawConverterPro` | `Identity/@Name` |
| Package/Identity/Publisher | `CN=1A2B3C4D-....` | `Identity/@Publisher` |

4. Ricompila, firma e verifica con un solo comando:

```powershell
.\tools\build_store_msix.ps1 `
  -Identity "12345FranchettiAcademy.FranchettiRawConverterPro" `
  -Publisher "CN=1A2B3C4D-...."
```

5. Carica il `.msix` in **Packages** (il publisher deve combaciare
   **esattamente** con `Package/Identity/Publisher`, altrimenti errore
   *invalid package publisher name*).
6. Microsoft ri-firma e pubblica.

> Il nome visualizzato nella scheda resta `Franchetti Academy`; cambia solo
> l'identità tecnica del pacchetto.

---

## 4. Cosa cambia per l'utente (e per l'app)

| Aspetto | Comportamento MSIX | Impatto |
|---|---|---|
| Cartella di installazione | `C:\Program Files\WindowsApps\...` in sola lettura | l'app non deve scrivere accanto all'EXE ✅ |
| Dati utente | `%APPDATA%\FranchettiRawConverterPro` | invariato ✅ |
| Preset | JSON in `%APPDATA%` | invariati ✅ |
| Aggiornamenti | gestiti dallo Store | niente updater interno ✅ |
| Avvio | menu Start / ricerca | funziona ✅ |
| Installazione "portable" | non più possibile | accettato |
| Disinstallazione | Impostazioni → App | funziona ✅ |
| Accesso a file RAW | pieno (full-trust) | invariato ✅ |
| Registro di sistema | nessuna scrittura | già così ✅ |
| Avvio automatico | non usato | già così ✅ |

Verifiche già fatte sul codice: manifest dell'EXE `asInvoker`, nessun uso di
`winreg`, nessuna scrittura in `Program Files`, nessun updater che scarica
eseguibili, dati solo in `%APPDATA%`.

### Cosa **non** cambia

- Le funzioni dell'app (conversione RAW, preset, batch, tethering).
- La lingua (italiano) e la categoria (Foto e video).
- Privacy policy e supporto (`reportage@libero.it`).
- Il fatto che gli originali non vengano mai modificati.

---

## 5. Requisiti della scheda Store per MSIX

Da compilare in Partner Center:

- **Package**: upload del `.msix` (non URL).
- **Architecture**: x64 (dedotta dal pacchetto).
- **Capabilities**: `runFullTrust` dichiarata nel manifest.
- **Privacy policy URL**: obbligatoria (già presente).
- **Note per la certificazione**: usa il testo pronto in
  [`MSIX_CERTIFICATION_NOTES.md`](MSIX_CERTIFICATION_NOTES.md) (EN/IT).
  Dichiara che è un'app desktop completa, senza telemetria, con rete usata
  solo per tethering locale o condivisione avviata dall'utente.
- **Screenshot**: quelli già pronti in `store_assets/`.
- **Età**: 3+ (nessun contenuto sensibile).

---

## 6. Procedura di rilascio (dopo la prima pubblicazione)

1. Aggiorna `VERSION` (es. `2.58.2.0`; l'ultimo numero deve restare `0`).
2. Ricompila l'EXE (`python build_exe.py`).
3. Un solo comando per build, firma e verifica con l'identità reale:

```powershell
.\tools\build_store_msix.ps1 `
  -Identity "<Package/Identity/Name>" `
  -Publisher "<Package/Identity/Publisher>" `
  -Version "2.58.2.0"
```

4. Carica in Partner Center → **Packages** → **Submit for certification**.
5. Aggiorna `CHANGELOG.md`, `RELEASE_NOTES.md`, `SHA256SUMS.txt`.

Lo script estrae il manifest dal pacchetto e verifica che identità, publisher,
versione e architettura coincidano con i valori richiesti, e che il firmatario
corrisponda al publisher.

La versione MSIX **deve aumentare** a ogni invio; lo Store rifiuta versioni
uguali o inferiori.

---

## 7. Rollback

Se la certificazione MSIX viene rifiutata:

- il prodotto EXE/MSI esistente resta pubblicato e invariato;
- si può continuare a distribuire l'installer su GitHub;
- in alternativa si riapre la strada **SignPath Foundation** (gratis) o
  **Certum Open Source** (25–49 €/anno), documentate in
  `CODE_SIGNING_FREE.md`.

Nessuna modifica al codice è irreversibile: il packaging MSIX è additivo.

---

## 8. Checklist

- [x] Manifest MSIX con `runFullTrust` e asset grafici
- [x] Script di build (`tools/build_msix.py`)
- [x] Script di firma e test (`tools/sign_msix_dev.ps1`)
- [x] Pacchetto 2.58.1.0 generato
- [x] Firma self-signed applicata
- [x] Installazione di prova riuscita
- [x] Avvio dell'app riuscito
- [x] Disinstallazione pulita
- [ ] Richiesta al supporto Partner Center (tipo pacchetto) **oppure** nuovo prodotto MSIX
- [ ] Identità reale (`Package/Identity/Name` + `Publisher`) inserita nel manifest
- [ ] Pacchetto ricompilato e firmato con l'identità reale
- [ ] Upload in Partner Center e invio per certificazione
- [ ] Scheda Store aggiornata con screenshot e note di certificazione
