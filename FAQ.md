# Domande Frequenti (FAQ)

**Franchetti Raw Converter Pro v2.50.1**

---

## 📋 Generali

### D: È davvero gratuito? Anche per uso commerciale?
**R:** Sì. Licenza **MIT** — uso libero personale e commerciale. Attribuzione apprezzata ma non obbligatoria oltre la licenza.

### D: Devo installarlo?
**R:** No. È **portatile** — singolo `.exe` (~23 MB). Doppio clic e funziona. Nessun installer, nessun registro, nessuna cartella AppData.

### D: Funziona su Mac / Linux?
**R:** Solo Windows 10/11 x64 attualmente. Il codice sorgente è multipiattaforma; contributi per build native benvenuti.

### D: Perché ~23 MB per un "semplice convertitore"?
**R:** Include **runtime Python 3.12 completo** + **LibRaw** (decodifica RAW C++) + **scikit-image** (Lab processing) + **Pillow** (imaging) + **NumPy** + **customtkinter** + **watchdog** + **piexif** + **requests**. Zero dipendenze esterne = funziona ovunque.

### D: I miei file RAW originali vengono modificati?
**R:** **Mai.** L'app li apre in **sola lettura**. Scrive solo i nuovi JPEG nella cartella di destinazione scelta.

---

## 🔧 Tecnici

### D: Quali formati RAW supporta esattamente?
**R:** 25+ formati via **LibRaw 0.21+** con algoritmo **AMaZE**:
- Sony: ARW, SRF, SR2
- Canon: CR2, CR3, CRW
- Nikon: NEF, NRW
- Fujifilm: RAF
- Olympus/OM System: ORF
- Panasonic: RW2, RAW
- Adobe/Universale: DNG
- Pentax: PEF, Samsung: SRW, Sigma: X3F, Hasselblad: 3FR, Imacon: FFF, Leica: RWL, Kodak: DCR/K25/KDC, Leaf: MOS, Minolta: MRW

### D: Preserva i metadati EXIF (GPS, impostazioni, orientamento)?
**R:** **Sì, v2.50.1.** Estrazione binaria EXIF completa con correzione orientamento (`Orientation=1`).

### D: Posso scegliere la posizione del watermark?
**R:** **v2.50.1: Basso destra** (margine 20px, scaling proporzionale 15% lato lungo). Griglia 9 posizioni prevista per v2.51.

### D: C'è una versione a riga di comando (CLI)?
**R:** **v2.50.1: No, solo GUI Enterprise (CustomTkinter).** CLI prevista per v2.51.

### D: Supporta profili colore (Adobe RGB, ProPhoto)?
**R:** **v2.50.1: Output sRGB con profilo ICC embedded.** Gestione Adobe RGB/ProPhoto prevista per v2.51.

### D: Quanto è veloce?
**R:** Dipende CPU (decodifica LibRaw è single-thread per file, multi-thread per batch):
| CPU | 24 MP → 1920px |
|-----|----------------|
| i5-8250U (4C/8T) | ~80 file/min |
| i7-11700 (8C/16T) | ~180 file/min |
| Ryzen 7 5800X (8C/16T) | ~220 file/min |
| i9-13900K (24C/32T) | ~400 file/min |

### D: Quanta RAM usa?
**R:** Picco ~400–600 MB per file (24-45 MP), rilasciato subito dopo. Batch 1000+ file = memoria stabile, niente leak.

### D: Cos'è la pipeline CIE L*a*b*?
**R:** Nuova in v2.50.1. Elaborazione in spazio **CIE L*a*b*** (separazione Luminanza/Crominanza):
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
**R:** Prova `Arial.ttf` → fallback `DejaVuSans.ttf` → fallback font bitmap di sistema. Dimensione 8–48 pt.

### D: Posso regolare l'opacità?
**R:** **v2.50.1: Sì, slider opacità logo 0–100%.** Testo fisso 80% (design choice per leggibilità).

### D: Posso usare un logo invece del testo?
**R:** **Sì, v2.50.1.** Carica PNG trasparente → scaling proporzionale (15% lato lungo) → alpha compositing.

---

## 📁 File e Output

### D: Se il file JPG esiste già, cosa succede?
**R:** Aggiunge automaticamente `_1`, `_2`, `_3`… al nome (es: `IMG_0001_1.jpg`). **Mai sovrascrive.**

### D: Posso mantenere la struttura delle cartelle?
**R:** **v2.50.1: Output flat in `Output_Ottimizzati/`.** Mirror folder structure prevista per v2.51.

### D: Quale qualità JPEG consigliate?
**R:** **85** (default) = equilibrio ottimale. 75–80 per web/social, 90–95 per stampa/portfolio, 100 non consigliato (file 2-3x senza guadagno visivo).

### D: Posso convertire in PNG/WebP invece di JPEG?
**R:** **v2.50.1: Solo JPEG (sRGB, progressive, quality 50-100).** PNG/WebP previsti per v2.51.

### D: Come funziona il tethering Wi-Fi?
**R:** **v2.50.1: Hot-Folder automatico.** Seleziona cartella Wi-Fi fotocamera → "ATTIVA SERVER" → scatta → elaborazione automatica Lab + watermark + EXIF → cloud dispatch parallelo (Telegram/Drive/Meta) → notifica GUI live.

### D: Quali servizi cloud supporta?
**R:** **v2.50.1: Dispatch parallelo su 3 canali:**
- **Telegram** (Bot API sendPhoto)
- **Google Drive** (Drive API v3 multipart)
- **Meta** (Graph API Instagram/Facebook)

---

## 🔒 Privacy & Sicurezza

### D: L'app si connette a Internet?
**R:** **Solo se attivi Cloud Dispatch** (opzionale, esplicito). Altrimenti 100% offline.

### D: Vengono raccolti dati?
**R:** **Zero.** Nessuna telemetria, analytics, crash reporting, registrazione, aggiornamenti auto. File originali mai modificati.

### D: È firmato digitalmente?
**R:** **v2.50.1: No** (costo certificato EV ~$300-600/anno). Verifica SHA-256 su GitHub Releases. Firma EV prevista per produzione enterprise.

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

## 📞 Supporto v2.50.1

| Canale | Scopo |
|--------|-------|
| **GitHub Issues** | Bug reports, crash, feature request |
| **GitHub Discussions** | Domande, workflow, tips |
| **Email** | `support@franchetti.dev` (security, licensing) |

---

*FAQ v2.50.1 — Gennaio 2025 — Aggiornata ad ogni release*