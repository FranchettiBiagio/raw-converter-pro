# Richiesta al supporto Partner Center — cambio tipo pacchetto EXE/MSI → MSIX

Percorso scelto: **mantenere il prodotto esistente** `XP9CJZTBCW6VS7`
(recensioni e installazioni) e chiedere a Microsoft di convertire il tipo di
pacchetto da EXE/MSI a MSIX.

---

## 1. Dove aprire la richiesta

1. Accedi a <https://partner.microsoft.com/dashboard>.
2. **Help + support** (icona `?` in basso a sinistra) → **New support request**.
3. Categoria: **Publishing and submissions** (o *Apps and games → Submission*,
   la voce esatta cambia leggermente in base all'account).
4. Argomento: **App package / package type** o **Update an existing app**.
5. Canale: **Online** (email). Non serve telefono.

> Se il modulo chiede il **product ID**, inserisci `XP9CJZTBCW6VS7`.
> Se chiede il **publisher**, inserisci `FranchettiAcademy`.

---

## 2. Testo pronto (inglese — usa questo)

> **Subject:** Change existing product package type from EXE/MSI to MSIX
>
> Hello,
>
> I publish the Windows desktop app **Franchetti Raw Converter Pro**
> (product ID: **XP9CJZTBCW6VS7**, publisher: **FranchettiAcademy**) as an
> EXE/MSI package.
>
> I have built a signed MSIX package for the same application and I would like
> to publish future updates as MSIX, **keeping the existing product ID,
> reviews and installs**.
>
> Package details:
>
> - Identity name (current test): `FranchettiAcademy.FranchettiRawConverterPro`
> - Version: `2.58.1.0`
> - Architecture: x64
> - Type: desktop full-trust application (`runFullTrust`), single EXE,
>   no services, no drivers, no telemetry
> - The package is signed with a certificate whose subject exactly matches
>   `Package/Identity/Publisher`; I understand the Store re-signs it
> - I will rebuild the package with the identity you assign
> - Data is stored only in `%APPDATA%\FranchettiRawConverterPro`
> - No registry writes, no auto-start, no self-updater
>
> The current listing is already published and uses the same name, icon,
> screenshots and privacy policy.
>
> Could you please:
>
> 1. convert the product package type from EXE/MSI to MSIX, or
> 2. tell me the correct procedure to keep the same product ID while moving to
>    MSIX?
>
> If the conversion assigns a new **Package/Identity/Name** and
> **Package/Identity/Publisher**, please provide those values so I can rebuild
> the package with the correct identity.
>
> Thank you,
> Biagio Franchetti
> FranchettiAcademy

---

## 3. Risposta italiana (se preferisci scrivere in italiano)

> **Oggetto:** Conversione tipo pacchetto da EXE/MSI a MSIX per prodotto esistente
>
> Buongiorno,
>
> pubblico l'app desktop **Franchetti Raw Converter Pro** (product ID
> **XP9CJZTBCW6VS7**, publisher **FranchettiAcademy**) come pacchetto EXE/MSI.
>
> Ho preparato un pacchetto MSIX firmato della stessa applicazione e vorrei
> pubblicare i prossimi aggiornamenti in formato MSIX **mantenendo lo stesso
> product ID, le recensioni e le installazioni esistenti**.
>
> Dettagli del pacchetto:
>
> - Identity name: `FranchettiAcademy.FranchettiRawConverterPro`
> - Versione: `2.58.1.0`
> - Architettura: x64
> - Applicazione desktop full-trust (`runFullTrust`), singolo EXE, nessun
>   servizio, nessun driver, nessuna telemetria
> - Dati salvati solo in `%APPDATA%\FranchettiRawConverterPro`
> - Nessuna scrittura nel registro, nessun avvio automatico, nessun updater
>
> La scheda è già pubblicata con lo stesso nome, icona, screenshot e privacy
> policy.
>
> Potete cortesemente:
>
> 1. convertire il tipo di pacchetto da EXE/MSI a MSIX, oppure
> 2. indicarmi la procedura corretta per mantenere lo stesso product ID
>    passando a MSIX?
>
> Se la conversione assegna un nuovo **Package/Identity/Name** e
> **Package/Identity/Publisher**, vi chiedo di comunicarmeli così posso
> ricompilare il pacchetto con l'identità corretta.
>
> Grazie,
> Biagio Franchetti
> FranchettiAcademy

---

## 4. Cosa può chiederti il supporto

| Richiesta tipica | Come rispondere |
|---|---|
| Conferma del product ID | `XP9CJZTBCW6VS7` |
| Perché MSIX | firma gratuita gestita dallo Store, aggiornamenti centralizzati |
| Se l'app è desktop completa | sì, `runFullTrust`, singolo EXE PyInstaller |
| Se cambiano le funzionalità | no, stesso binario |
| Se accetti un nuovo product ID | decidi tu: se vuoi conservare recensioni, chiedi di mantenerlo |
| Upload del pacchetto | non ancora: prima serve il tipo MSIX, poi carichi il `.msix` |

---

## 5. Dopo l'approvazione

1. Partner Center → prodotto → **Product identity**: annota
   **Package/Identity/Name** e **Package/Identity/Publisher**.
2. Ricompila, firma e verifica con un solo comando:

```powershell
cd C:\FranchettiRawConverterPro
.\tools\build_store_msix.ps1 `
  -Identity "<Package/Identity/Name>" `
  -Publisher "<Package/Identity/Publisher>"
```

Lo script controlla che il manifest nel pacchetto e il firmatario coincidano
con i valori indicati, e stampa lo SHA-256.

3. Partner Center → **Packages** → carica il `.msix`.
4. Verifica che la versione sia superiore all'ultima pubblicata.
5. Compila le **note per la certificazione** e invia.

> Il publisher del certificato deve combaciare **carattere per carattere**
> con `Package/Identity/Publisher`, altrimenti l'upload fallisce con
> *invalid package publisher name*. Lo script di firma usa esattamente il
> valore passato con `-Publisher`.

---

## 6. Se il supporto rifiuta

Passa al **nuovo prodotto MSIX** (sezione 3.B di `MSIX_MIGRATION.md`):
stesse operazioni, ma con un product ID nuovo. Il pacchetto e gli script sono
già pronti: cambiano solo i due valori di identità.
