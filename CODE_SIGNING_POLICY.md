# Politica di firma del codice — Franchetti Raw Converter Pro

**English version below: [Code signing policy (EN)](#code-signing-policy-en)**

Ultimo aggiornamento: 22 novembre 2026

---

## 1. Progetto

| | |
| --- | --- |
| Nome | Franchetti Raw Converter Pro |
| Repository | https://github.com/FranchettiBiagio/raw-converter-pro |
| Sito | https://franchettitv.it |
| Licenza | MIT (vedi [LICENSE](LICENSE)) |
| Natura | Progetto libero e gratuito, senza scopo di lucro, senza componenti proprietari e senza doppia licenza commerciale |
| Manutentore | Biagio Franchetti — GitHub [@FranchettiBiagio](https://github.com/FranchettiBiagio) |

Il programma converte file RAW in JPEG e viene distribuito come eseguibile
Windows portable, come installer e tramite Microsoft Store. Lo stesso sorgente
produce anche build Linux e macOS, dichiarate sperimentali.

## 2. Cosa viene firmato

Vengono firmati **solo** gli artefatti di rilascio prodotti dal repository
pubblico:

| Artefatto | Origine | Firma |
| --- | --- | --- |
| `FranchettiRawConverterPro.exe` | PyInstaller, da `main.py` alla revisione pubblicata | sì |
| `Franchetti_Raw_Converter_Setup_v<versione>.exe` | Inno Setup, contiene l'exe già firmato | sì |
| Pacchetto MSIX per Microsoft Store | `tools/build_msix.py` | no: lo Store lo ri-firma con il proprio certificato |
| Archivi Linux/macOS (`.tar.gz`, `.zip`) | build del sorgente | no: sono archivi di sorgente/binari non Windows |

Nessun altro file viene firmato. In particolare **non** vengono firmati file
compilati fuori dalla CI, né binari allegati a segnalazioni, né versioni di
prova.

## 3. Come si firma

La firma avviene esclusivamente tramite il servizio **SignPath**, con il
certificato di **SignPath Foundation** riservato ai progetti open source, e
solo attraverso il workflow pubblico del repository:

```
.github/workflows/windows-release.yml
```

Il processo, in ordine:

1. Il workflow parte da un tag `v*` o da un avvio manuale sulla branch `main`.
2. Su un runner GitHub-hosted (`windows-latest`) vengono installate le
   dipendenze da `requirements.txt` e PyInstaller compila `main.py`.
3. L'eseguibile non firmato viene caricato come artefatto del workflow e
   inviato a SignPath (`signpath/github-action-submit-signing-request`).
4. SignPath verifica l'origine: la richiesta è accettata solo se proviene da
   questo repository, da questo workflow e da quel commit.
5. L'exe firmato viene reinserito in `dist/`, Inno Setup costruisce
   l'installer, che viene inviato a sua volta per la firma.
6. Gli artefatti firmati vengono pubblicati con `SHA256SUMS.txt`.

Conseguenze, dichiarate come impegno:

- nessuna firma manuale o locale di build di rilascio;
- nessuna chiave privata conservata su PC personali: la chiave è gestita da
  SignPath;
- ogni richiesta di firma è tracciata (commit, workflow, artefatto, richiedente);
- una build non riproducibile dal sorgente pubblico non viene firmata.

## 4. Ruoli

| Ruolo | Chi | Responsabilità |
| --- | --- | --- |
| Author | Biagio Franchetti | Scrive il codice, apre le pull request |
| Reviewer | Biagio Franchetti (unico manutentore attuale) | Rilegge le modifiche prima del merge su `main` |
| Approver | Biagio Franchetti | Avvia il workflow di rilascio e approva le richieste di firma in SignPath |

Finché il progetto ha un solo manutentore, i tre ruoli coincidono. Se
arriveranno altri manutentori, l'approvazione di una richiesta di firma
richiederà una persona diversa da chi ha scritto il codice, e questa politica
sarà aggiornata prima del cambio.

## 5. Autenticazione

- Tutti gli account usati per il progetto (GitHub, SignPath, posta) hanno
  **autenticazione a più fattori** attiva.
- Il token API di SignPath è conservato solo come *secret* del repository
  GitHub e non è mai scritto nei file, nei log o nella documentazione.
- I workflow usano il `GITHUB_TOKEN` con permessi minimi (`contents: read`).

## 6. Come verificare una firma

Windows (PowerShell):

```powershell
Get-AuthenticodeSignature .\FranchettiRawConverterPro.exe | Format-List Status, SignerCertificate
```

Windows SDK:

```cmd
signtool verify /pa /v FranchettiRawConverterPro.exe
```

Atteso: `Status: Valid`, firmatario **SignPath Foundation**, catena fino a una
CA presente nel Microsoft Trusted Root Program.

L'hash SHA-256 pubblicato accanto al file serve a verificare che il binario sia
lo stesso uscito dalla build:

```cmd
certutil -hashfile FranchettiRawConverterPro.exe SHA256
```

## 7. Stato attuale

Il certificato di SignPath Foundation viene concesso su domanda e dopo
approvazione manuale. La domanda è stata preparata insieme a questa politica.
**Fino all'approvazione le release Windows restano non firmate** e questo è
scritto anche nelle note di rilascio: nessuna pagina dichiara una firma che
non esiste.

## 8. Segnalazioni

- Vulnerabilità o sospetto di manomissione: `security@franchetti.dev`
  (vedi [SECURITY.md](SECURITY.md)).
- Dubbi sulla firma o sull'origine di un binario: `support@franchetti.dev`.
- Modifiche a questa politica: pull request pubblica, con approvazione del
  manutentore e aggiornamento della data in testa al documento.

---

# Code signing policy (EN)

Last updated: 22 November 2026

## 1. Project

| | |
| --- | --- |
| Name | Franchetti Raw Converter Pro |
| Repository | https://github.com/FranchettiBiagio/raw-converter-pro |
| Website | https://franchettitv.it |
| License | MIT (see [LICENSE](LICENSE)) |
| Nature | Free and open-source project, non-commercial, no proprietary components, no commercial dual licensing |
| Maintainer | Biagio Franchetti — GitHub [@FranchettiBiagio](https://github.com/FranchettiBiagio) |

## 2. What gets signed

Only release artifacts built from the public repository are signed:

| Artifact | Origin | Signed |
| --- | --- | --- |
| `FranchettiRawConverterPro.exe` | PyInstaller, from `main.py` at the published revision | yes |
| `Franchetti_Raw_Converter_Setup_v<version>.exe` | Inno Setup, containing the already-signed exe | yes |
| MSIX package for Microsoft Store | `tools/build_msix.py` | no: the Store re-signs it |
| Linux/macOS source archives | source builds | no: not Windows binaries |

Nothing else is signed. Binaries built outside CI, test builds and files
attached to reports are never signed.

## 3. Signing process

Signing is performed exclusively through **SignPath**, using the
**SignPath Foundation** certificate for open-source projects, and only through
the public workflow `.github/workflows/windows-release.yml`:

1. The workflow is started by a `v*` tag or manually on `main`.
2. On a GitHub-hosted `windows-latest` runner, dependencies from
   `requirements.txt` and PyInstaller are installed and `main.py` is compiled.
3. The unsigned executable is uploaded as a workflow artifact and submitted to
   SignPath via `signpath/github-action-submit-signing-request`.
4. SignPath verifies origin: the request is accepted only from this
   repository, this workflow and that commit.
5. The signed exe is put back into `dist/`, Inno Setup builds the installer,
   which is submitted for signing in turn.
6. Signed artifacts are published together with `SHA256SUMS.txt`.

Commitments:

- no manual or local signing of release builds;
- no private signing key stored on personal machines (SignPath holds it);
- every signing request is traceable to a commit, a workflow run and a
  requester;
- a build that cannot be reproduced from the public source is not signed.

## 4. Roles

| Role | Who | Responsibility |
| --- | --- | --- |
| Author | Biagio Franchetti | Writes code, opens pull requests |
| Reviewer | Biagio Franchetti (currently sole maintainer) | Reviews changes before merge to `main` |
| Approver | Biagio Franchetti | Starts the release workflow and approves signing requests in SignPath |

While the project has a single maintainer these roles coincide. If further
maintainers join, approving a signing request will require someone other than
the author of the code, and this policy will be updated before that change.

## 5. Authentication

- Multi-factor authentication is enabled on every account used for the project
  (GitHub, SignPath, email).
- The SignPath API token is stored only as a GitHub repository secret and is
  never written to files, logs or documentation.
- Workflows use `GITHUB_TOKEN` with minimal permissions (`contents: read`).

## 6. Verifying a signature

```powershell
Get-AuthenticodeSignature .\FranchettiRawConverterPro.exe | Format-List Status, SignerCertificate
```

or, with the Windows SDK:

```cmd
signtool verify /pa /v FranchettiRawConverterPro.exe
```

Expected: `Status: Valid`, signer **SignPath Foundation**, chain to a CA in the
Microsoft Trusted Root Program. The published SHA-256 lets you confirm the
binary matches the build output.

## 7. Current status

The SignPath Foundation certificate is granted on application, after manual
review. The application has been prepared together with this policy.
**Until it is approved, Windows releases remain unsigned**, and release notes
say so: no page claims a signature that does not exist yet.

## 8. Reporting

- Vulnerabilities or suspected tampering: `security@franchetti.dev`
  (see [SECURITY.md](SECURITY.md)).
- Questions about a signature or a binary's origin: `support@franchetti.dev`.
- Changes to this policy: public pull request, maintainer approval, date at the
  top of this document updated.
