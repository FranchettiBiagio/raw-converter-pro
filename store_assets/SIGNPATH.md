# SignPath Foundation — stato della domanda

## Invio

| | |
| --- | --- |
| Data invio | 22 novembre 2026 |
| Modulo | https://signpath.org/apply (HubSpot) |
| Esito | «Form submitted — Thank you, we'll be in touch soon.» |
| Email di contatto | reportage@libero.it |
| Nome utente richiesto | Biagio Franchetti |
| Progetto | Franchetti Raw Converter Pro |
| Repository | https://github.com/FranchettiBiagio/raw-converter-pro |
| Homepage inviata | https://franchettibiagio.github.io/franchetti-raw-converter-site/ |
| Download inviato | https://franchettibiagio.github.io/franchetti-raw-converter-site/#scarica |
| Privacy inviata | https://github.com/FranchettiBiagio/raw-converter-pro/blob/main/PRIVACY.md |
| Licenza | MIT (`LICENSE`), componenti in `THIRD_PARTY_LICENSES.md` |

Copia dei valori inviati: `C:\Users\Administrator\Downloads\signpath_modulo.md`.

## Cosa non toccare in attesa

SignPath verifica l'origine delle build guardando il repository **nel momento
della firma**. Fino all'approvazione:

- non rinominare il repository e non spostarlo su un'altra organizzazione;
- non cambiare la licenza;
- `.github/workflows/windows-release.yml` deve restare sulla branch `main`;
- non cancellare `CODE_SIGNING_POLICY.md` (è linkato dal modulo e dal sito);
- la frase «Firma gratuita fornita da SignPath.io, certificato di SignPath
  Foundation» deve restare nel footer della pagina di download.

## Dopo l'approvazione: configurazione (circa 30 minuti)

1. **Account SignPath** con accesso GitHub, MFA attiva.
2. **Organization**: `Franchetti`.
3. **Project**: slug `raw-converter-pro`, collegato a
   `github.com/FranchettiBiagio/raw-converter-pro`.
4. **GitHub App di SignPath**: installata solo su questo repository.
5. **Artifact configuration**: creata dall'interfaccia partendo da una build
   reale («create from build»), non scritta a mano. Deve coprire `*.exe`
   (exe e installer usano lo stesso nome di politica).
   Bozza di riferimento, se serve incollarla:

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <artifact-configuration xmlns="http://signpath.io/artifact-configuration" version="1">
     <zip-file>
       <pe-file path="*.exe" />
     </zip-file>
   </artifact-configuration>
   ```

   Con restrizioni sui metadati: `product-name` = `Franchetti Raw Converter Pro`,
   `product-version` = `2.58.2.0`.

6. **Signing policy**: slug `release-signing`, tipo Authenticode, con
   approvazione manuale (come richiesto dalle condizioni OSS).
7. **Token API**: creato per l'utente, salvato come secret GitHub
   `SIGNPATH_API_TOKEN`.
8. **Variabili del repository** (Settings → Secrets and variables → Actions →
   Variables):

   | Variabile | Valore |
   | --- | --- |
   | `SIGNPATH_ORGANIZATION_ID` | GUID dell'organizzazione |
   | `SIGNPATH_PROJECT_SLUG` | `raw-converter-pro` |
   | `SIGNPATH_SIGNING_POLICY_SLUG` | `release-signing` |
   | `SIGNPATH_ARTIFACT_CONFIGURATION_SLUG` | slug della configurazione |

9. **Prova**: Actions → *Windows release* → Run workflow. I due passi
   `Firma l'exe (SignPath)` e `Firma l'installer (SignPath)` devono passare da
   *skipped* a *success*.

## Cosa cambia dopo la prima firma

- L'installer firmato è quello da caricare su franchettitv.it e da dare a
  Partner Center come *Package URL* per la 2.58.2 (policy 10.2.9 risolta).
- Sparisce l'avviso SmartScreen sui download dal sito.
- Il tag `v2.58.2` crea la release firmata con `SHA256SUMS.txt` e la politica
  di firma nelle note.

## Se chiedono chiarimenti

Rispondere lo stesso giorno, citando il Product ID se la domanda riguarda lo
Store: `XP9CJZTBCW6VS7`. Le richieste tipiche sono: conferma MFA, chiarimento
sul processo di build, richiesta di un artefatto di prova.

Se rifiutano: restano due strade già valutate — riprovare dopo aver accumulato
uso reale (installazioni Store, recensioni pubbliche), oppure certificato
commerciale. La strada MSIX come prodotto nuovo resta esclusa perché
comporterebbe perdere recensioni, installazioni e link del prodotto attuale.
