# Requisiti Microsoft Store per installer EXE/MSI — stato e cose da fare

> ✅ **Percorso consigliato: EXE/MSI, gratis, come la versione già pubblicata.**
> Verifica del 13/11/2026: l'installer che Microsoft distribuisce dallo Store
> per questa app è **`NotSigned`**, così come tutti gli installer GitHub
> v2.50.1–v2.58.1 e il payload installato. La firma Authenticode è richiesta
> dalla documentazione ma **non è stata applicata** a questo prodotto.
> Procedura operativa: [`PUBLISH_EXE_FREE.md`](PUBLISH_EXE_FREE.md).
> Il percorso MSIX resta come alternativa gratuita se la certificazione
> dovesse rifiutare l'installer non firmato:
> [`MSIX_MIGRATION.md`](MSIX_MIGRATION.md).

Fonte: Microsoft Learn, *App package requirements for MSI/EXE app* e
*Upload app packages for MSI/EXE app*. Riassunto operativo per
Franchetti Raw Converter Pro v2.58.1.

## 1. Regole dello Store (EXE/MSI)

Per accettare un installer EXE/MSI lo Store richiede:

1. **URL HTTPS diretto e versionato** dell'installer, ospitato su CDN o
   infrastruttura propria. Il file a quell'URL **non deve cambiare** dopo
   l'invio.
2. **Firma Authenticode** dell'installer **e di tutti i file PE** che contiene
   (EXE, DLL, uninstaller), con certificato che catena al
   *Microsoft Trusted Root Program*. Un certificato self-signed **non** basta.
3. **Installazione silenziosa**: il Partner Center chiede gli switch da passare
   all'EXE, oppure un installer già silenzioso di suo.
4. **Installer offline e standalone**: nessun download di componenti durante
   il setup; nessun bundle di software non correlato.
5. **Architettura dichiarata** (x64) e lingue supportate.

## 2. Stato attuale del progetto

| Requisito | Stato | Dettaglio |
|---|---|---|
| Installer EXE | ✅ pronto | `Output\Franchetti_Raw_Converter_Setup_v2.58.1.exe` (Inno Setup 7) |
| Installer offline/standalone | ✅ sì | l'EXE dell'app è incorporato, nessun download |
| URL HTTPS versionato | ✅ pronto | release GitHub `v2.58.1` (vedi §3) |
| Firma installer | ✅ non necessaria in pratica | `NotSigned`, come l'installer v1.0.0 distribuito dallo Store |
| Firma EXE applicazione | ✅ non necessaria in pratica | `NotSigned`, come il payload installato dallo Store |
| Firma uninstaller | ✅ non necessaria in pratica | `unins000.exe` dello Store è `NotSigned` |
| Installazione silenziosa | ✅ supportata | Inno Setup accetta `/VERYSILENT` |
| Parametri installer in Partner Center | ⚠️ da inserire | vedi §3 |

Hash dei file **non firmati** attualmente pubblicati su GitHub:

```
316a34c16d45f6e3cca05e517b95797d83bc0e88adf4199659025e4cb1b86405  Franchetti_Raw_Converter_Setup_v2.58.1.exe
0dd9593e879268b3209c33052e17f0323013389082d9ec985e58b5ec0a1cea7d  FranchettiRawConverterPro.exe
```

## 3. Valori da inserire in Partner Center (Packages)

| Campo | Valore |
|---|---|
| App type | **EXE** |
| Architecture | **x64** |
| Package URL | `https://github.com/FranchettiBiagio/raw-converter-pro/releases/download/v2.58.1/Franchetti_Raw_Converter_Setup_v2.58.1.exe` |
| Installer parameters | `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-` |
| Return code: success | `0` |
| Return code: cancelled by user | `2` |
| Altre lingue | Italiano (Italia) |

Note:

- L'URL GitHub è versionato (contiene `v2.58.1`) e i file di una release
  GitHub non vengono sovrascritti: va bene come URL immutabile. Se preferisci,
  puoi caricare lo stesso file su un tuo dominio/CDN e usare quello.
- **Non** usare l'URL "latest": deve puntare alla versione esatta.
- Con `/VERYSILENT` non compare alcuna finestra e l'app non parte a fine
  installazione (`skipifsilent` è già nello script).

## 4. Come ottenere la firma

> ✅ **Per questo prodotto la firma non è stata necessaria.** L'installer
> v1.0.0 distribuito dallo Store e il payload installato sono `NotSigned`
> (verifica del 13/11/2026). La procedura consigliata è quindi caricare
> l'installer v2.58.1 senza firma, come già fatto in passato:
> [`PUBLISH_EXE_FREE.md`](PUBLISH_EXE_FREE.md).
>
> Le opzioni sotto restano valide **solo se** la certificazione dovesse
> rifiutare l'installer non firmato.

Lo Store **non** ri-firma gli installer EXE/MSI (a differenza degli MSIX).
La documentazione Microsoft richiede un certificato CA accreditato. Opzioni
realistiche, se serve:

| Opzione | Costo indicativo | Note |
|---|---|---|
| **Azure Artifact Signing** (ex Trusted Signing) | ~9,99 USD/mese | Cloud, niente token. Public Trust per le **organizzazioni** UE; per le persone fisiche solo USA/Canada |
| Certificato **OV/IV** code signing | ~200–400 €/anno | Su token/HSM (obbligatorio dal 2023) |
| Certificato **EV** code signing | ~300–600 €/anno | Massima reputazione SmartScreen |
| Self-signed | 0 € | ❌ **non accettato** dallo Store |

Con Azure Artifact Signing il certificato catena a un root Microsoft ed è
accettato dallo Store. **In Italia l'identity validation individuale non è
disponibile**: il servizio richiede un'entità legale (partita IVA / ditta /
società) per la Organization validation.

**Situazione attuale del publisher: persona fisica, senza partita IVA.**
Percorso applicabile: certificato **IV (Individual Validation)** da una CA
commerciale — SSL.com IV a 129 USD/anno + eSigner (~20 USD/mese nei mesi di
firma) oppure Certum Standard Code Signing in the Cloud a 209 €/anno.
Guida dedicata: [`CODE_SIGNING_INDIVIDUAL_IT.md`](CODE_SIGNING_INDIVIDUAL_IT.md).
La procedura Azure resta valida in futuro, se nasce un'entità legale:
[`AZURE_ARTIFACT_SIGNING_SETUP.md`](AZURE_ARTIFACT_SIGNING_SETUP.md).

### Pipeline pronta nel repo

```powershell
# 1) Individua il certificato disponibile (token o cloud)
.\tools\check-signing-cert.ps1

# 2) Certificato in CurrentUser\My (token, SSL.com eSigner CKA, Certum SimplySign)
.\tools\sign_and_build.ps1 -Mode Store -Thumbprint <THUMBPRINT>

# 3) Azure Artifact Signing (solo con entita legale)
.\tools\sign_and_build.ps1 -Mode Azure -Account <account> -Profile <profilo>

# 4) PFX (solo se hai un certificato con chiave esportabile)
.\tools\sign_and_build.ps1 -Mode Pfx -PfxPath C:\certs\frc.pfx -PfxPassword "***"
```

Lo script:

1. genera `tools\metadata.json` (solo modalità Azure);
2. firma `dist\FranchettiRawConverterPro.exe` (SHA-256 + timestamp; con Azure
   usa `http://timestamp.acs.microsoft.com`, obbligatorio perché i certificati
   durano 3 giorni);
3. genera `sign_tool.iss` con il comando `signtool` per Inno Setup;
4. compila `setup.iss` con `/DSIGN`, firmando installer **e** uninstaller
   (`SignTool` + `SignedUninstaller`, inclusi via `sign_tool.iss`);
5. verifica le firme e stampa gli SHA-256 (esce con codice 1 se una firma non
   è valida).

Stato dei prerequisiti su questa macchina (13/11/2026): `signtool.exe`
10.0.26100.0 ✅, dlib Artifact Signing 1.0.151 ✅ (in
`tools\artifactsigning\`), .NET 8/10 ✅, VC++ Redistributable ✅.
Manca solo il certificato: con una persona fisica serve un IV da CA
commerciale (`CODE_SIGNING_INDIVIDUAL_IT.md`).
`sign_tool.iss` e `tools\metadata.json` sono generati e ignorati da git.

## 5. Dopo la firma

1. Carica l'installer firmato su un URL versionato **nuovo** (es. release
   `v2.58.1-store`) perché il binario precedente è cambiato.
2. Aggiorna il campo **Package URL** in Partner Center.
3. Mantieni la stessa versione (`2.58.1`) nella scheda.
4. Invia per la certificazione.

> Se cambi la firma, cambiano anche gli hash: aggiorna `SHA256SUMS.txt` e le
> note di rilascio.

## 6. Alternativa: MSIX

Con un pacchetto **MSIX** lo Store firma gratis e non serve alcun certificato,
ma cambia il modello di installazione (container, percorsi virtualizzati) e
non è compatibile con il comportamento "portable" attuale. Per questo il
progetto resta su EXE/MSI: l'unica cosa che manca è la firma.
