# Firma del setup senza partita IVA — persona fisica in Italia

Sei una persona fisica: **Azure Artifact Signing non è percorribile**. I
certificati *Public Trust* del servizio Microsoft sono disponibili per le
organizzazioni dell'Unione Europea, ma per le **persone fisiche solo se
residenti negli Stati Uniti o in Canada**.

Non è un problema: lo Store accetta qualsiasi certificato **Authenticode**
che catena al *Microsoft Trusted Root Program*, quindi basta un certificato
**IV (Individual Validation)** emesso da una CA commerciale. È il prodotto
pensato esattamente per chi sviluppa senza un'entità legale.

---

## 1. Cosa ti serve esattamente

| Requisito | Dettaglio |
|---|---|
| Tipo certificato | **IV code signing** (Individual Validation) |
| Standard | CA/Browser Forum Code Signing BR |
| Chiave privata | **obbligatoriamente** su token FIPS o cloud HSM (dal giugno 2023 non esistono più `.pfx` scaricabili) |
| Validazione | documento d'identità governativo + verifica dell'indirizzo |
| Cosa firma | EXE, installer, uninstaller (Authenticode / signtool) |
| Cosa **non** richiede | partita IVA, ragione sociale, dominio aziendale |

Il certificato riporterà il **tuo nome e cognome** (es. `BIAGIO FRANCHETTI`):
è normale e corretto. Allo Store interessa solo che la catena di firma sia
attendibile; per i pacchetti EXE/MSI **non** è richiesta la corrispondenza
tra soggetto del certificato e nome del publisher (`FranchettiAcademy`).

---

## 2. Opzioni a confronto (prezzi verificati il 13/11/2026)

| Provider | Prodotto | Prezzo | Chiave | Tempi | Note |
|---|---|---|---|---|---|
| **SSL.com** | IV Code Signing | **129 USD/anno** + eSigner | Cloud (eSigner) o YubiKey (+379 USD) | 3–5 giorni | Interfaccia e supporto in inglese, tutto online, nessuna spedizione |
| **Certum** (Asseco, UE) | Standard Code Signing in the Cloud | **209 €/anno** | Cloud SimplySign incluso | 1–3 giorni | Azienda UE, prezzo unico annuale, fatturazione europea |
| Certum | Standard Code Signing – set | 169 € + supporto fisico | Card + lettore | 3–7 giorni | Serve un lettore di smart card |
| Certum | Open Source Code Signing in the Cloud | 49 €/anno | Cloud | 1–3 giorni | ⚠️ solo progetti open source; verifica i termini prima di acquistare |
| SSL.com | EV Sole Proprietor | ~400–500 USD/anno | Token/cloud | 5–10 giorni | Reputazione SmartScreen immediata; non necessario per lo Store |

**Consiglio pratico:** SSL.com IV + eSigner.
Costo del primo rilascio: **129 USD** di certificato + **20 USD** per il primo
mese di eSigner (i primi 30 giorni sono gratis) ≈ **150 USD**, senza hardware
da spedire. Se pubblichi poche volte l'anno puoi attivare eSigner solo nel
mese in cui firmi.

**Alternativa europea:** Certum a 209 €/anno, prezzo unico, senza abbonamento
mensile: conviene se prevedi più release nell'anno o preferisci un fornitore
UE.

---

## 3. Percorso A — SSL.com IV + eSigner

1. **Ordine** — <https://www.ssl.com/products/software-integrity/code-signing/iv/>
   → durata 1 anno → *Key storage*: **eSigner Cloud Signing** → completa
   l'acquisto.
2. **Validazione identità** — carichi documento d'identità e prova
   dell'indirizzo; SSL.com può chiamarti per conferma. Tempi 3–5 giorni
   (esiste l'opzione expedited a pagamento).
3. **Certificato emesso** — appare nel tuo account SSL.com.
4. **eSigner** — attiva l'abbonamento (30 giorni gratis). Installa
   **eSigner CKA (Cloud Key Adapter)** dal sito SSL.com: registra un provider
   crittografico Windows, così `signtool.exe` vede il certificato cloud come
   se fosse locale.
5. **Enrollment** — apri eSigner CKA, fai login e “enroll” il certificato:
   comparirà in `Cert:\CurrentUser\My`.
6. **Trova il thumbprint**:
   ```powershell
   .\tools\check-signing-cert.ps1
   ```
7. **Firma**:
   ```powershell
   .\tools\sign_and_build.ps1 -Mode Store -Thumbprint <THUMBPRINT>
   ```

> Durante la firma eSigner CKA deve essere in esecuzione e autenticato.
> Se signtool non vede il certificato, riapri CKA e ripeti l'enroll.

---

## 4. Percorso B — Certum Cloud (SimplySign)

1. **Ordine** — <https://shop.certum.eu/standard-code-signing-in-the-cloud.html>
   (209 €/anno).
2. **Validazione** — documento d'identità; Certum può richiedere una video
   verifica. Tempi 1–3 giorni.
3. **SimplySign Desktop** — scarica l'app dall'area clienti e accedi: il
   certificato viene presentato a Windows come una smart card virtuale.
4. **Thumbprint e firma** — come sopra:
   ```powershell
   .\tools\check-signing-cert.ps1
   .\tools\sign_and_build.ps1 -Mode Store -Thumbprint <THUMBPRINT>
   ```

> Con SimplySign la firma funziona solo mentre l'app è aperta e connessa.
> Alcune versioni richiedono di selezionare la carta virtuale al primo uso.

---

## 5. Cosa cambia nel risultato

Dopo la firma, `Get-AuthenticodeSignature` restituirà `Valid` e nella
finestra UAC / proprietà del file comparirà:

```
Firmato da: BIAGIO FRANCHETTI
Timestamp:  <data>
```

Non comparirà più “Autore sconosciuto”. È esattamente ciò che lo Store
verifica.

### SmartScreen

Un certificato IV **non** ha reputazione iniziale: i download diretti da
GitHub possono mostrare l'avviso SmartScreen finché non accumuli download
puliti. L'installazione tramite Microsoft Store non passa da SmartScreen.
Se l'avviso sui download diretti è un problema, l'unica scorciatoia è un
certificato **EV** (o EV Sole Proprietor), più costoso.

---

## 6. Dopo la firma

1. Carica l'installer firmato su un URL nuovo e immutabile (es. release
   `v2.58.1-store`). Non sovrascrivere l'asset della `v2.58.1`.
2. Partner Center → **Packages** → aggiorna **Package URL**.
3. Aggiorna `SHA256SUMS.txt` e le note di rilascio.
4. Parametri silent invariati:
   `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`
5. Invia per la certificazione.

---

## 7. Riepilogo costi e tempi

| Voce | Costo | Tempo |
|---|---|---|
| Certificato IV SSL.com (1 anno) | 129 USD | validazione 3–5 gg |
| eSigner (solo nei mesi di firma) | 20 USD/mese | attivazione immediata |
| **Totale primo rilascio** | **~150 USD** | **~1 settimana** |
| Alternativa Certum cloud | 209 €/anno tutto incluso | 1–3 gg |

---

## 8. Checklist

- [ ] Certificato IV acquistato (SSL.com o Certum)
- [ ] Identità validata
- [ ] Chiave disponibile: eSigner CKA attivo **oppure** SimplySign connesso
- [ ] `.\tools\check-signing-cert.ps1` mostra il certificato con EKU Code Signing
- [ ] `.\tools\sign_and_build.ps1 -Mode Store -Thumbprint ...` → `Valid` su EXE e installer
- [ ] `signtool verify /pa /v` valido + timestamp presente
- [ ] Installer caricato su URL nuovo, `Package URL` aggiornato
- [ ] `SHA256SUMS.txt` e note di rilascio aggiornati
- [ ] Sottomissione inviata
