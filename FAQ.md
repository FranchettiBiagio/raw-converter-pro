# Domande Frequenti (FAQ)

**Franchetti Raw Converter Pro v2.53.0**

---

## 📋 Generali

### D: È davvero gratuito? Anche per uso commerciale?
**R:** Sì. Licenza **MIT** — uso libero personale e commerciale. Attribuzione apprezzata ma non obbligatoria oltre la licenza.

### D: Devo installarlo?
**R:** No. È **portatile** — singolo `.exe` (~62 MB). Doppio clic e funziona. Nessun installer, nessun registro, nessuna cartella AppData.

### D: Funziona su Mac / Linux?
**R:** Solo Windows 10/11 x64 attualmente. Il codice sorgente è multipiattaforma; contributi per build native benvenuti.

### D: Perché ~62 MB per un "semplice convertitore"?
**R:** Include **runtime Python 3.12 completo** + **LibRaw** (decodifica RAW C++) + **scikit-image** (Lab processing) + **Pillow** (imaging) + **NumPy** + **customtkinter** + **watchdog** + **piexif** + **requests**. Zero dipendenze esterne = funziona ovunque.

### D: I miei file RAW originali vengono modificati?
**R:** **Mai.** L'app li apre in **sola lettura**. Scrive solo i nuovi JPEG nella cartella di destinazione scelta.

---

## 🔧 Tecnici

### D: Quali formati RAW supporta esattamente?
**R:** 25+ formati via **LibRaw 0.21+** con demosaic **AMaZE** quando disponibile nella build, altrimenti fallback automatico **AHD / PPG / LINEAR**:
- Sony: ARW, SRF, SR2
- Canon: CR2, CR3, CRW
- Nikon: NEF, NRW
- Fujifilm: RAF
- Olympus/OM System: ORF
- Panasonic: RW2, RAW
- Adobe/Universale: DNG
- Pentax: PEF, Samsung: SRW, Sigma: X3F, Hasselblad: 3FR, Imacon: FFF, Leica: RWL, Kodak: DCR/K25/KDC, Leaf: MOS, Minolta: MRW

### D: Preserva i metadati EXIF (GPS, impostazioni, orientamento)?
**R:** **Sì, dalla v2.50.1.** Estrazione binaria EXIF completa con correzione orientamento (`Orientation=1`). Funziona anche sui RAW (ARW testato).

### D: Posso scegliere la posizione del watermark?
**R:** **Sì, dalla v2.51.** Cinque posizioni: basso/alto a destra o sinistra, centro. Margine proporzionale e ombra per leggibilità.

### D: C'è una versione a riga di comando (CLI)?
**R:** La GUI è il metodo principale. Dalla v2.53 sono disponibili due modalità diagnostiche: `--converti-test <sorgente> <uscita>` e `--batch-test <sorgente> <cartella>`.

### D: Supporta profili colore (Adobe RGB, ProPhoto)?
**R:** **No: l'output è sempre sRGB con profilo ICC incorporato.** Le opzioni Adobe RGB/ProPhoto non erano realmente implementate e sono state rimosse per evitare risultati errati.

### D: Quanto è veloce?
**R:** Dipende dalla CPU. Un RAW Sony A7S da 24 MP richiede circa 10–12 s per core; il batch usa **tutti i core logici** (fino a ~3× su 6 file, misurato su i9-12900H). Con 20 core si elaborano decine di file al minuto.

### D: Quanta RAM usa?
**R:** Picco ~1–1,5 GB per processo (RAW 24 MP). Il numero di processi viene ridotto automaticamente se la RAM libera non basta.

### D: Cos'è la pipeline CIE L*a*b*?
**R:** Introdotta nella v2.50.1. Elaborazione in spazio **CIE L*a*b*** (separazione Luminanza/Crominanza):
- Contrasto sigmoidale (curva logistica a "S")
- Vivacità selettiva (solo toni spenti)
- Nitidezza Unsharp Mask su solo canale L (zero aloni colorati)
- Output con profilo ICC sRGB embedded

---

## 🎨 Watermark

### D: Il watermark si vede su foto chiare?
**R:** Sì. **Testo bianco 80% opacità + ombra nera 1px 50% opacità**. Leggibile su qualsiasi sfondo.

### D: Posso usare caratteri speciali/emoji?
**R:** Sì, **Unicode completo**. Es: `© Franchetti 2025`, `📸 Mario Rossi`, `@handle | sito.com`, `日本語 OK`.

### D: Quale font usa?
**R:** Prova `Arial Bold` → `Arial` → `DejaVuSans` → font bitmap di sistema. Dimensione 8–600.

### D: Posso regolare l'opacità?
**R:** Sì per il logo (slider 0–100%). Il testo usa un'opacità fissa dell'85% con ombra nera per restare leggibile su ogni sfondo.

### D: Posso usare un logo invece del testo?
**R:** **Sì.** Carica PNG trasparente → scaling proporzionale (15% lato lungo) → alpha compositing. Un logo illeggibile viene ignorato senza bloccare la conversione.

---

## 📁 File e Output

### D: Se il file JPG esiste già, cosa succede?
**R:** Dipende dalla politica scelta: **Rinomina** (default) aggiunge `_1`, `_2`…; **Salta** non converte; **Sovrascrivi** sostituisce il file. Due foto dello stesso batch non scrivono mai sullo stesso file.

### D: Posso mantenere la struttura delle cartelle?
**R:** L'output è **flat** nella cartella scelta; le foto con lo stesso nome vengono rinominate automaticamente per non sovrascriversi.

### D: Quale qualità JPEG consigliate?
**R:** **90** (default) = equilibrio ottimale. 75–80 per web/social, 90–95 per stampa/portfolio, 100 non consigliato (file molto più grandi senza guadagno visivo).

### D: Posso convertire in PNG/WebP invece di JPEG?
**R:** **Sì.** Formati disponibili: JPEG, PNG, TIFF e WEBP. Tutti con profilo ICC sRGB incorporato.

### D: Come funziona il tethering Wi-Fi?
**R:** Due modalità: **Hot-Folder** (monitora una cartella e converte automaticamente i file appena arrivano, aspettando la fine della scrittura) e **Sony A7S** (connessione Wi-Fi DIRECT, scatto remoto e download).

### D: Quali servizi cloud supporta?
**R:** **Telegram** (Bot API `sendPhoto`) e **Dropbox** (`files/upload`) sono operativi. Google Drive, Meta e SwissTransfer sono predisposti ma non attivi in questa versione: vengono saltati senza errori.

---

## 🔒 Privacy & Sicurezza

### D: L'app si connette a Internet?
**R:** **Solo se attivi Cloud Dispatch** (opzionale, esplicito). Altrimenti 100% offline.

### D: Vengono raccolti dati?
**R:** **Zero.** Nessuna telemetria, analytics, crash reporting, registrazione, aggiornamenti auto. File originali mai modificati.

### D: È firmato digitalmente?
**R:** **No** (costo certificato EV ~$300-600/anno). Verifica SHA-256 su GitHub Releases. Firma EV prevista per produzione enterprise.

### D: Windows SmartScreen blocca l'avvio?
**R:** Normale per eseguibili non firmati EV. "Ulteriori informazioni" → "Esegui comunque". Hash SHA-256 verificabile su GitHub Releases.

---

## 🛠️ Build & Sviluppo

### D: Come compilo da sorgente?
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
python build_exe.py
```

### D: Requisiti build?
- Python 3.12+
- Windows 10/11 x64 (per build .exe nativo)
- Dipendenze in `requirements.txt`

### D: Come aggiungere un formato RAW?
I formati dipendono da **LibRaw** (upstream). Aggiorna `rawpy`/`LibRaw` alla versione più recente.

---

## 📞 Supporto v2.53.0

| Canale | Scopo |
|--------|-------|
| **GitHub Issues** | Bug reports, crash, feature request |
| **GitHub Discussions** | Domande, workflow, tips |
| **Email** | `support@franchetti.dev` (security, licensing) |

---

*FAQ v2.53.0 — 26 Ottobre 2026 — Aggiornata ad ogni release*