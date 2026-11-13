# Pubblicare v2.58.1 come EXE — percorso gratuito già accettato dallo Store

Verifica eseguita il **13/11/2026** sui file reali, non sulla documentazione.

---

## 1. Cosa abbiamo trovato

| File verificato | Firma Authenticode |
|---|---|
| Installer GitHub `v2.50.1` | ❌ `NotSigned` |
| Installer GitHub `v2.58.0` | ❌ `NotSigned` |
| Installer GitHub `v2.58.1` | ❌ `NotSigned` |
| Installer **distribuito dallo Store** (v1.0.0, scaricato con `winget download`) | ❌ `NotSigned` |
| EXE installato dallo Store in `C:\Program Files (x86)\...` | ❌ `NotSigned` |
| `unins000.exe` installato dallo Store | ❌ `NotSigned` |

Hash dell'installer Store v1.0.0:
`87a6afa7803fbcdb5ea0d01373bc0c3a77718c5543584b9dc4bfd65e1bcf15bf`

Il manifest con cui lo Store lo distribuisce riporta:

```yaml
InstallerType: exe
Scope: machine
InstallerSwitches:
  Silent: /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
```

**Conclusione:** la versione vecchia non è mai stata firmata digitalmente.
"Inno Setup" **compila** l'installer, non lo firma. Non è stato usato alcun
certificato, né gratuito né a pagamento. Lo Store ha accettato e distribuisce
tuttora un installer senza firma.

---

## 2. Documentazione Microsoft contro realtà

La pagina *App package requirements for MSI/EXE app* dice che installer e
tutti i PE devono essere firmati con un certificato che catena al Microsoft
Trusted Root Program.

Nella pratica, per questo prodotto la verifica **non è stata applicata**:
la scheda è live dal 21/09/2026 e Microsoft stessa distribuisce un file
`NotSigned`. Non sappiamo se la regola verrà applicata in futuro, ma il
percorso che ha già funzionato è disponibile di nuovo a costo zero.

> ⚠️ Rischio residuo: se la certificazione della nuova sottomissione rifiuta
> il pacchetto per firma mancante, si passa al percorso MSIX (già pronto) o a
> SignPath Foundation. Nessun lavoro fatto va perso.

---

## 3. Procedura consigliata (gratis, stesso metodo)

1. Partner Center → prodotto `XP9CJZTBCW6VS7` → **Packages**.
2. Crea/aggiorna la sottomissione e inserisci come **Package URL**:
   ```
   https://github.com/FranchettiBiagio/raw-converter-pro/releases/download/v2.58.1/Franchetti_Raw_Converter_Setup_v2.58.1.exe
   ```
   L'URL è versionato e il file non cambia più: requisito soddisfatto.
3. **Installer parameters**:
   ```
   /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
   ```
4. Architettura: **x64**. Tipo: **EXE**.
5. Attendi la validazione della URL **senza inviare**. Se Partner Center non
   segnala errori di firma, la strada è percorribile.
6. Compila le note di certificazione (vedi
   [`MSIX_CERTIFICATION_NOTES.md`](MSIX_CERTIFICATION_NOTES.md), la parte
   senza riferimenti MSIX).
7. **Salva** e **Invia per la certificazione**.

Se la validazione o la certificazione rifiuta per firma mancante:

- non modificare la scheda già live (la versione precedente resta pubblicata);
- riprendi il percorso MSIX: `store_assets\MSIX_MIGRATION.md`.

---

## 4. Mettere in attesa la richiesta MSIX

La richiesta `2611130050000788` chiede la conversione del tipo prodotto a
MSIX. Se vogliamo prima provare il percorso EXE, va messa in attesa per
evitare che Microsoft converta il prodotto mentre carichiamo l'EXE.

Testo da inviare nella richiesta (o via email di risposta):

> **English**
>
> Hello,
> regarding support request 2611130050000788, please put the request on hold
> and do not change the product package type at this time. After reviewing the
> live product, I am verifying whether I can keep the existing EXE/MSI package
> type for the next update.
> I will confirm whether the conversion to MSIX is still needed.
> Thank you.

> **Italiano**
>
> Buongiorno,
> in merito alla richiesta 2611130050000788, vi chiedo di metterla in attesa e
> di non modificare il tipo di pacchetto del prodotto. Sto verificando se posso
> mantenere il tipo EXE/MSI esistente per il prossimo aggiornamento.
> Vi confermerò se la conversione a MSIX è ancora necessaria.
> Grazie.

Se il test EXE va a buon fine, la richiesta può essere chiusa. Se fallisce,
si risponde chiedendo di procedere con la conversione.

---

## 5. Cosa NON cambia rispetto alla versione vecchia

- Nessun certificato da acquistare.
- Nessun account Azure.
- Nessuna build in CI.
- Stesso installer Inno, stessi parametri silent, stesso URL versionato.
- La scheda, le recensioni e le installazioni esistenti restano.

## 6. Differenze tecniche da conoscere

| Aspetto | v1.0.0 sullo Store | v2.58.1 da caricare |
|---|---|---|
| Scope installer | machine (`Program Files (x86)`) | per-utente (`%LOCALAPPDATA%\Programs`) |
| Firma | assente | assente (come prima) |
| Payload | EXE non firmato | EXE non firmato |
| Silent install | `/VERYSILENT ...` | identico |

Lo scope per-utente è accettato dallo Store; se la certificazione dovesse
segnalarlo, si ricompila l'installer con `PrivilegesRequired=admin` solo per
la variante Store.

---

## 7. Checklist

- [x] Verificato che l'installer Store v1.0.0 è `NotSigned`
- [x] Verificato che gli installer GitHub v2.50.1–v2.58.1 sono `NotSigned`
- [x] Verificato che il payload installato è `NotSigned`
- [x] Individuato l'URL versionato v2.58.1
- [ ] Richiesta MSIX messa in attesa
- [ ] Package URL v2.58.1 inserito in Partner Center
- [ ] Validazione della URL superata
- [ ] Sottomissione inviata
- [ ] Certificazione superata
