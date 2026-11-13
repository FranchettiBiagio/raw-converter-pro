# Firma gratuita del setup — opzioni reali

> ✅ **Decisione presa: MSIX firmato gratuitamente dallo Store.**
> Procedura operativa, test già eseguiti e passi per Partner Center in
> [`MSIX_MIGRATION.md`](MSIX_MIGRATION.md). Questo documento resta come
> confronto tra le alternative gratuite.

Domanda: si può firmare l'installer **senza pagare**?

Risposta breve: **non esiste un certificato Authenticode gratuito rilasciato a
te**. Le CA pubbliche non emettono certificati di firma codice a titolo
gratuito (dal 2023 richiedono chiavi su hardware certificato, verifica
documentale e responsabilità legale).

Esistono però **due strade a costo zero**, con condizioni molto diverse.

---

## Opzione A — SignPath Foundation (gratis, mantiene EXE/MSI)

SignPath Foundation emette un certificato **a nome proprio** e lo mette a
disposizione dei progetti open source. La firma dice *SignPath Foundation*,
non *Franchetti*: è la fondazione che garantisce che il binario sia stato
costruito da quel repository.

### Condizioni (dai loro termini)

| Requisito | Stato del progetto |
|---|---|
| Licenza OSI, senza doppia licenza commerciale | ✅ MIT |
| Nessun componente proprietario | ✅ solo Python/PIL/PyInstaller e librerie OSS |
| Progetto già rilasciato nella forma da firmare | ✅ v2.58.1 su GitHub |
| Funzionalità documentate | ✅ scheda Store + README |
| Progetto mantenuto attivamente | ✅ |
| Repository pubblico e build verificabile in CI | ⚠️ **da creare** (GitHub Actions) |
| Pagina "Code signing policy" sul sito/repo | ⚠️ **da creare** |
| Ruoli dichiarati: author / reviewer / approver, MFA attivo | ⚠️ **da dichiarare** |
| Reputazione verificabile del progetto | ⚠️ punto più delicato: progetto nuovo |
| Approvazione manuale a ogni release | ✅ accettabile |

### Cosa cambia in pratica

1. La release **non** si compila più sul tuo PC: va costruita da GitHub
   Actions a partire dal repository pubblico, e firmata da SignPath nel
   contesto di quella build (loro verificano la provenienza).
2. Ogni release richiede un **click di approvazione** nel loro pannello.
3. Il nome visualizzato nella firma sarà **SignPath Foundation**.
4. Serve un workflow che compili `FranchettiRawConverterPro.exe` con
   PyInstaller e poi l'installer con Inno Setup.

### Rischi da conoscere

- **Possono rifiutare.** I termini dicono che per i programmi eseguibili
  richiedono "una certa reputazione verificabile": un progetto appena
  pubblicato può non bastare. Non c'è appello.
- **Uninstaller Inno**: `SignedUninstaller=yes` richiede il comando di firma
  *durante* la compilazione, cosa che SignPath non offre da GitHub Actions.
  Si può omettere (nella pratica molti installer Inno passano la
  certificazione senza uninstaller firmato) oppure passare a un **MSI WiX**,
  dove la disinstallazione la esegue `msiexec` (già firmato da Microsoft) e
  il problema non esiste.
- **Nome publisher diverso** da `FranchettiAcademy`. Per i pacchetti EXE/MSI
  Microsoft non richiede la corrispondenza tra soggetto del certificato e
  nome della scheda (a differenza degli MSIX), quindi la catena di fiducia
  basta. Resta un rischio teorico in certificazione.

### Tempi

Candidatura → revisione (giorni/settimane) → configurazione CI → prima
release firmata. Realistico: **2–4 settimane**.

---

## Opzione B — MSIX firmato dallo Store (gratis, ma cambia tutto il resto)

Microsoft ri-firma gratuitamente i pacchetti MSIX pubblicati sullo Store: zero
certificati, zero SmartScreen, zero costi. Microsoft stessa lo indica come
percorso raccomandato.

Ma nel tuo caso:

- il prodotto `XP9CJZTBCW6VS7` è di tipo **EXE/MSI** e Partner Center **non
  permette di cambiare il tipo di pacchetto**: serve un intervento del
  supporto Microsoft oppure un **nuovo prodotto** (nuovo ID, recensioni e
  installazioni azzerate);
- cambia il modello di installazione (cartella `WindowsApps`, aggiornamenti
  gestiti dallo Store, niente uso "portable"), esattamente il motivo per cui
  avevi scartato MSIX.

**Conclusione:** gratis sì, ma non è un aggiornamento della scheda esistente.

---

## Opzione C — quasi gratis: Certum Open Source

Certum vende un certificato per progetti open source a **25–49 €/anno**
(cloud SimplySign o su carta). Non è gratis, ma è l'ordine di grandezza di
una cena e ti dà un certificato **a tuo nome**, senza CI obbligatoria e senza
approvazioni per release.

| | SignPath | Certum OSS |
|---|---|---|
| Costo | 0 € | 25–49 €/anno |
| Nome nella firma | SignPath Foundation | il tuo nome |
| Build in CI obbligatoria | ✅ sì | ❌ no |
| Approvazione per release | ✅ sì | ❌ no |
| Rischio rifiuto | medio | basso (serve documentazione OSS) |

---

## Cosa serve comunque, in tutti i casi

- [ ] Repository pubblico con licenza OSI (già ✅ MIT)
- [ ] Build riproducibile da zero (oggi la build è solo locale)
- [ ] Firma di EXE app + installer (+ uninstaller o MSI)
- [ ] Upload su URL versionato nuovo e aggiornamento `Package URL`

---

## Raccomandazione

Se il vincolo "gratis" è assoluto: **SignPath Foundation** è l'unica strada
che conserva il prodotto EXE/MSI esistente. Va però accettato che la firma
sia a nome della fondazione e che le release passino dalla loro pipeline.

Se "gratis" significa "non voglio pagare un abbonamento" ma 25–49 € una volta
l'anno sono accettabili, **Certum Open Source** è molto più semplice e non
dipende da un'approvazione.
