# Firma del setup con Azure Artifact Signing — guida operativa

Questa guida porta dal "file `NotSigned`" alla firma valida di **installer,
EXE dell'app e uninstaller**, cioè l'unico requisito che manca per inviare
Franchetti Raw Converter Pro al Microsoft Store come pacchetto EXE.

Tempo realistico: **1–3 settimane** (la variabile è la validazione
dell'identità, non la parte tecnica: la configurazione sulla macchina è già
pronta e richiede pochi minuti).

---

## 0. In sintesi

| # | Passo | Dove | Tempo |
|---|---|---|---|
| 1 | Abbonamento Azure **pay-as-you-go** | portale Azure | 5 min |
| 2 | Registrare `Microsoft.CodeSigning` | portale Azure / CLI | 2 min |
| 3 | Creare **Artifact Signing account** (region West Europe, SKU Basic) | portale Azure | 5 min |
| 4 | **Identity validation** (Organization) | portale Azure (solo portale) | 1–20 gg lavorativi |
| 5 | Creare **certificate profile** Public Trust | portale Azure | 5 min |
| 6 | Assegnare il ruolo **Artifact Signing Certificate Profile Signer** | portale Azure | 2 min |
| 7 | `.\tools\sign_and_build.ps1 -Mode Azure ...` | questa macchina | 5–10 min |
| 8 | Verifica, upload, aggiornamento Partner Center | questa macchina | 15 min |

Costo indicativo: **circa 9,99 USD/mese** per lo SKU Basic (verifica il
[listino aggiornato](https://azure.microsoft.com/pricing/details/artifact-signing/)).
Nessun token fisico, nessuna chiave privata sul disco.

---

## 1. Prima di tutto: chi può attivarlo (vincolo geografico)

I certificati **Public Trust** di Artifact Signing sono disponibili per le
**organizzazioni** in: Stati Uniti, Canada, Unione Europea, Regno Unito,
Australia, Nuova Zelanda, Giappone, Corea del Sud, Singapore, Svizzera,
Norvegia, Israele. Le **persone fisiche** sono accettate **solo se residenti
negli Stati Uniti o in Canada**.

Conseguenza per un publisher italiano:

| Situazione | Percorso |
|---|---|
| Hai **partita IVA / ditta individuale / società** (anche "FranchettiAcademy" come attività registrata) | ✅ Artifact Signing con **Organization identity validation**: usa la ragione sociale e la P.IVA come *business identifier*. Il certificato riporterà la ragione sociale, non il nome commerciale — allo Store non importa: conta la catena di fiducia. |
| Sei una **persona fisica senza attività registrata** | ❌ Public Trust individuale non disponibile in Italia → serve un certificato **IV/OV** da una CA commerciale (sezione 12). |

> L'identity validation di tipo Organization **non** richiede un billing
> account Azure di tipo "Organization"; richiede però un'entità legale
> verificabile, un sito web e un'email su dominio dell'ente.

---

## 2. Cosa è già pronto su questa macchina

Verificato il 13/11/2026:

| Componente | Stato | Percorso / versione |
|---|---|---|
| Windows | ✅ Windows 11 Pro 22631 | — |
| `winget` | ✅ 1.29.380 | — |
| .NET runtime 8 e 10 | ✅ presenti | `C:\Program Files\dotnet` |
| Visual C++ Redistributable | ✅ presente | `vcruntime140.dll` |
| `signtool.exe` | ✅ installato | `C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe` |
| dlib Artifact Signing | ✅ installata | `tools\artifactsigning\1.0.151\bin\x64\Azure.CodeSigning.Dlib.dll` |
| Pipeline di firma | ✅ pronta | `tools\sign_and_build.ps1` |
| Certificato Azure | ❌ da attivare | sezioni 3–7 |

Test già eseguito: `signtool` carica la dlib, legge `metadata.json` e arriva
all'autenticazione Azure. Manca solo l'account con il certificato.

Se ti serve riscaricare la dlib su un'altra macchina:

```powershell
.\tools\get-artifact-signing-client.ps1
```

---

## 3. Passo 1 — abbonamento Azure idoneo

Serve un abbonamento **pay-as-you-go** (o Enterprise Agreement). Gli
abbonamenti **free, trial e sponsored non sono supportati**: la creazione
dell'account fallisce con un errore esplicito.

Se hai solo un abbonamento trial: portale Azure → **Subscriptions** →
**Upgrade** a pay-as-you-go.

Serve anche un **tenant Microsoft Entra** (va bene quello creato con
l'abbonamento).

---

## 4. Passo 2 — registrare il resource provider

Portale Azure → **Subscriptions** → la tua sottoscrizione → **Settings** →
**Resource providers** → `Microsoft.CodeSigning` → **Register**.

In alternativa:

```powershell
az provider register --namespace "Microsoft.CodeSigning"
az provider show --namespace "Microsoft.CodeSigning"      # atteso: Registered
az extension add --name artifact-signing
```

---

## 5. Passo 3 — creare l'account Artifact Signing

Portale Azure → cerca **Artifact Signing Accounts** → **Create**.

| Campo | Valore consigliato |
|---|---|
| Subscription | la tua pay-as-you-go |
| Resource group | `rg-franchetti-signing` (nuovo) |
| Account name | `franchetti-signing` (3–24 caratteri, unico, inizia con lettera) |
| Region | **West Europe** (`weu`) |
| Pricing | **Basic** |

Regioni UE disponibili: West Europe (`weu`), North Europe (`neu`),
Switzerland North (`swn`), Poland Central (`plc`).

> **Regione ed endpoint devono coincidere.** Con West Europe l'endpoint è
> `https://weu.codesigning.azure.net`. Un disallineamento produce un `403`
> difficile da diagnosticare.

Equivalente CLI:

```powershell
az group create --name rg-franchetti-signing --location westeurope
az artifact-signing create -n franchetti-signing -l westeurope -g rg-franchetti-signing --sku Basic
```

---

## 6. Passo 4 — identity validation (Organization)

Si può fare **solo dal portale**, non da CLI.

1. Nell'account Artifact Signing → **Identity validations** → **Organization**
   → tipo **Public** → **New Identity**.
2. Compila il modulo con i dati **esatti** dell'entità legale:

| Campo | Cosa inserire |
|---|---|
| Organization Name | ragione sociale / ditta individuale come da visura |
| Website url | il tuo sito (es. `https://franchettibiagio.github.io/raw-converter-pro/`) |
| Primary Email | email **su dominio dell'attività**, monitorata, che accetta link esterni |
| Secondary Email | diversa dalla primaria, stesso dominio |
| Business Identifier | **partita IVA** (o codice fiscale/REA secondo il paese) |
| Seller ID | il **Seller ID di Partner Center** (obbligatorio per i clienti Store) |
| Address | sede legale completa |
| First/Last Name | chi rappresenta l'entità, come sul documento d'identità |

3. Controlla **Certificate subject preview** — quello sarà il nome sul
   certificato, non modificabile dopo.
4. **Create**.

Poi:

- arriva un'email di verifica alla primary email: il link **scade dopo 7
  giorni**; se scade, va rifatta la richiesta da zero;
- lo stato passa a **Action Required** quando servono documenti o la verifica
  dell'identità della persona (Verified ID via Microsoft Authenticator);
- la validazione richiede **1–20 giorni lavorativi** e non è accelerabile;
- i documenti devono essere emessi negli ultimi 12 mesi e non scadere prima
  di 2 mesi.

**Dove trovare il Seller ID:** Partner Center → **Account settings** →
**Account details** → *Seller ID* (formato numerico). Serve perché lo Store
verifica che il certificato appartenga allo stesso publisher.

---

## 7. Passo 5 — certificate profile

Nell'account → **Certificate profiles** → **Create** → tipo **Public Trust**.

| Campo | Valore |
|---|---|
| Certificate Profile Name | `frc-public` (5–100 caratteri) |
| Certificate Type | autocompilato |
| Program Type | **None** |
| Verified CN and O | l'identity validation appena completata |
| Include street address / postal code | facoltativi |

Il profilo è il contenitore dei certificati a breve scadenza che il servizio
emette per ogni firma. **Non** va rinnovato a mano: si rinnova da solo finché
l'identity validation è valida.

---

## 8. Passo 6 — permesso per firmare

Sull'account Artifact Signing (o sul resource group) → **Access control
(IAM)** → **Add role assignment** → ruolo
**Artifact Signing Certificate Profile Signer** → assegnalo al tuo utente.

Senza questo ruolo `signtool` restituisce `403`.

Nota: per creare le identity validation serve anche il ruolo
**Artifact Signing Identity Verifier**.

---

## 9. Passo 7 — firmare su questa macchina

Con account `franchetti-signing`, profilo `frc-public`, region West Europe:

```powershell
cd C:\FranchettiRawConverterPro
.\tools\sign_and_build.ps1 -Mode Azure -Account franchetti-signing -Profile frc-public
```

Cosa fa lo script:

1. crea `tools\metadata.json` (endpoint + account + profilo + correlation id);
2. firma `dist\FranchettiRawConverterPro.exe` con SHA-256 e timestamp
   `http://timestamp.acs.microsoft.com` (obbligatorio: i certificati Artifact
   Signing durano **3 giorni**);
3. genera `sign_tool.iss` e ricompila l'installer con `/DSIGN`, firmando
   anche l'uninstaller;
4. verifica le firme ed esce con codice `1` se una non è valida;
5. stampa gli SHA-256 dei due file.

La prima esecuzione apre il browser per l'accesso Azure (DefaultAzureCredential):
accedi con l'utente che ha il ruolo del passo 6. Sulle esecuzioni successive
la sessione viene riusata.

Se la compilazione va a buon fine vedrai:

```
Verifica firme:
  Valid      C:\FranchettiRawConverterPro\dist\FranchettiRawConverterPro.exe
  Valid      C:\FranchettiRawConverterPro\Output\Franchetti_Raw_Converter_Setup_v2.58.1.exe
```

---

## 10. Passo 8 — verifica indipendente

```powershell
& "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe" `
   verify /pa /v "Output\Franchetti_Raw_Converter_Setup_v2.58.1.exe"

Get-AuthenticodeSignature "Output\Franchetti_Raw_Converter_Setup_v2.58.1.exe" |
  Format-List Status, StatusMessage, SignerCertificate, TimeStamperCertificate
```

Deve risultare `Valid` (non `UnknownError`, non `NotSigned`) e deve esserci un
**timestamp**.

---

## 11. Dopo la firma: pubblicazione

1. **Non sovrascrivere** l'asset della release `v2.58.1` già pubblicata: il
   file cambiato va su un URL nuovo, es.
   `https://github.com/FranchettiBiagio/raw-converter-pro/releases/download/v2.58.1-store/Franchetti_Raw_Converter_Setup_v2.58.1.exe`
2. Aggiorna in Partner Center → **Packages** → **Package URL**.
3. Aggiorna `SHA256SUMS.txt` e le note di rilascio (gli hash cambiano).
4. Mantieni i parametri silent: `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`.
5. Invia per la certificazione.

---

## 12. Errori comuni

| Errore | Causa | Rimedio |
|---|---|---|
| `403` | ruolo mancante, endpoint ≠ regione, profilo non attivo, identity validation non `Completed`, nome account/profilo errato in `metadata.json` | controlla i cinque punti in ordine |
| `SignerSign() failed` `0x80004005` | dlib non caricata, credenziali escluse tutte, versione signtool vecchia | verifica `/dlib`, `metadata.json`, signtool ≥ 10.0.22621.755 |
| `No certificates were found that met all the given criteria` | signtool sta cercando un certificato locale invece della dlib | percorso `/dlib` sbagliato o dlib x86 con signtool x64 |
| `401` / `MsalUiRequiredException` | cache credenziali | `az logout` + `az login`, oppure `ExcludeCredentials` |
| Nessun errore ma file non firmato | .NET runtime mancante | installa .NET 8/10 runtime |
| `Unhandled managed exception ... At least one credential type must be included` | tutti i metodi di autenticazione esclusi in `metadata.json` | rimuovi `ExcludeCredentials` o lascia almeno `AzureCliCredential` |
| Firma valida ma "scaduta" dopo pochi giorni | manca il timestamp | usa `/tr http://timestamp.acs.microsoft.com /td SHA256` (già impostato) |

---

## 13. Alternativa senza Azure: certificato IV/OV su token

Se non hai un'entità legale, l'unica strada per lo Store è un certificato
**IV (Individual Validation)** o **OV** emesso da una CA pubblica:

| CA | Prodotto | Costo indicativo | Tempi |
|---|---|---|---|
| Certum | Code Signing Individual (IV) | ~150–250 €/anno | 1–3 giorni |
| Sectigo / reseller | OV Code Signing | ~250–400 €/anno | 3–7 giorni |
| DigiCert / GlobalSign | OV/EV Code Signing | ~350–600 €/anno | 3–10 giorni |

Dal 2023 la chiave privata deve stare su **token/HSM**: non è più possibile
un `.pfx` esportabile per i certificati OV/IV pubblici.

Con il certificato installato in `Cert:\CurrentUser\My`:

```powershell
.\tools\sign_and_build.ps1 -Mode Store -Thumbprint <THUMBPRINT>
```

In alternativa, se il provider consegna un PFX con chiave esportabile
(alcuni IV lo permettono):

```powershell
.\tools\sign_and_build.ps1 -Mode Pfx -PfxPath C:\certs\frc.pfx -PfxPassword "***"
```

In entrambi i casi valgono gli stessi requisiti Store: catena al Microsoft
Trusted Root Program, timestamp, firma di installer + EXE + uninstaller.

---

## 14. Checklist finale

- [ ] Abbonamento Azure pay-as-you-go attivo
- [ ] `Microsoft.CodeSigning` registrato (`Registered`)
- [ ] Artifact Signing account in West Europe, SKU Basic
- [ ] Identity validation **Completed**
- [ ] Certificate profile Public Trust attivo
- [ ] Ruolo *Artifact Signing Certificate Profile Signer* assegnato
- [ ] `.\tools\sign_and_build.ps1 -Mode Azure` termina con `Valid` su entrambi i file
- [ ] `signtool verify /pa /v` valido + timestamp presente
- [ ] Installer firmato caricato su URL versionato nuovo
- [ ] `Package URL` aggiornato in Partner Center
- [ ] `SHA256SUMS.txt` e note di rilascio aggiornati
- [ ] Sottomissione inviata per la certificazione
