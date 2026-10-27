# Guida Screenshot per uptodown.dev / Store

**Franchetti Raw Converter Pro v2.55.0**

---

## 📸 Specifiche Richieste

| Parametro | Valore |
|-----------|--------|
| **Risoluzione** | 1920×1080 (Full HD) minimo |
| **Formato** | PNG (lossless) o JPEG 95% |
| **DPI** | 96 (standard web) |
| **Lingua UI** | Italiano (primario) |
| **Tema** | Sistema (chiaro/scuro) — preferibile chiaro |
| **Sfondo** | Desktop pulito, niente icone personali |
| **Watermark screenshot** | Nessuno (l'app aggiunge il suo) |

---

## 🎬 Elenco Screenshot Obbligatori (5)

### 1. Schermata Principale — "Prima della conversione"
**Nome file**: `01_main_window.png`
**Contenuto**:
- Finestra app massimizzata (1920×1080)
- Sezione **1. Sorgente RAW** con 8-12 file caricati (misti ARW, NEF, CR2, RAF)
- Sezione **2. Destinazione** con percorso visibile (es. `C:\Users\Foto\Convertiti`)
- Sezione **3. Opzioni** con valori default visibili (1920, 85, © Franchetti, 14, ☑ Mantieni nome)
- Pulsanti **▶ AVVIA** e **⏹ ANNULLA** (disabilitato)
- Log vuoto con placeholder "Pronto"
- **Scopo**: Mostrare interfaccia completa, pulita, pronta all'uso

---

### 2. Pannello Opzioni Dettagliato — "Configurazione"
**Nome file**: `02_options_panel.png`
**Contenuto**:
- Focus su sezione **3. Opzioni Conversione**
- Menu a tendina **Dimensione max** aperto (mostra preset 640–4000 + 0)
- Spinbox **Qualità JPG** su 90
- Campo **Testo Copyright** con testo esempio: `© Mario Rossi 2024 | mariorossi.photo`
- Spinbox **Font size** su 16
- Checkbox **Mantieni nome** spuntato + prefisso `MR_`
- **Scopo**: Dimostrare granularità controllo, supporto Unicode, flessibilità naming

---

### 3. Conversione in Corso — "Progresso tempo reale"
**Nome file**: `03_conversion_progress.png`
**Contenuto**:
- Barra progresso al ~60% (es. 42/70 file)
- Label status: `42/70 - OK: DSC_0042.NEF → DSC_0042.jpg (3000x2000)`
- Log visibile con **colorazione**:
  - 🟢 Righe verdi "OK: ..."
  - 🔵 Righe blu "=== AVVIO ==="
  - 🟠 Eventuale riga arancio "⏹ Annullamento..."
- Pulsante **⏹ ANNULLA** abilitato (evidenziato)
- **Scopo**: Mostrare feedback tempo reale, log colorato, cancellabilità

---

### 4. Risultato in Esplora Risorse — "Output finale"
**Nome file**: `04_output_folder.png`
**Contenuto**:
- Finestra Esplora Risorse (Win+E) sulla cartella destinazione
- Vista **Dettagli** o **Icone grandi**
- 15-20 file `.jpg` visibili (nomi originali mantenuti)
- Colonne: Nome, Data modifica, Tipo (JPEG), Dimensioni (es. 450 KB, 1.2 MB)
- Barro percorso mostra cartella scelta
- **Scopo**: Prova tangibile output, dimensioni ragionevoli, nomi preservati

---

### 5. Dettaglio Watermark — "Zoom angolo basso destra"
**Nome file**: `05_watermark_detail.png`
**Contenuto**:
- Un singolo JPEG aperto in **Visualizzatore foto Windows** o **Photos**
- **Zoom 100% (1:1)** o **200%** sull'angolo **basso destro**
- Watermark visibile: `© Mario Rossi 2024 | mariorossi.photo`
- Leggibile su sfondo sia chiaro che scuro (se foto ha zone miste)
- Font size 14-16 pt, posizione margine 1%
- **Scopo**: Dimostrare qualità watermark, leggibilità, discrezione professionale

---

## 🎬 Screenshot Opzionali / Bonus

| # | Nome | Descrizione |
|---|------|-------------|
| 6 | `06_file_selection.png` | Dialog "Seleziona cartella" o "Seleziona file" aperto |
| 7 | `07_dark_mode.png` | App con tema scuro Windows (se supportato) |
| 8 | `08_error_handling.png` | Log con errore rosso + continuazione batch |
| 9 | `10_comparison.png` | Affiancato: RAW originale (anteprima) vs JPEG output |

---

## 🛠️ Come Catturarli (Windows)

### Strumenti Integrati
| Metodo | Scorciatoia | Note |
|--------|-------------|------|
| **Strumento ritaglio** | `Win + Shift + S` | Seleziona area → salva PNG |
| **Stampa schermo** | `Print` → Incolla in Paint → Salva | Tutto schermo |
| **Solo finestra attiva** | `Alt + Print` → Incolla | Solo finestra app |
| **Xbox Game Bar** | `Win + G` → Cattura | Anche per video demo |

### Consigli Qualità
1. **Scala DPI 100%** (Impostazioni → Schermo → Scala 100%)
2. **Nascondi barra applicazioni** (tasto destro → Impostazioni → Nascondi automaticamente)
3. **Pulisci desktop** (niente file personali visibili)
4. **Usa dati realistici** — foto vere, nomi file credibili
5. **Niente info sensibili** — nessun percorso reale utente, niente email vere nei watermark demo

---

## 📁 Consegna

### Cartella di consegna
```
screenshots/
├── 01_main_window.png
├── 02_options_panel.png
├── 03_conversion_progress.png
├── 04_output_folder.png
├── 05_watermark_detail.png
└── README_SCREENSHOTS.md (questo file)
```

### Checklist Pre-Caricamento
- [ ] Tutte 5 obbligatorie presenti
- [ ] Risoluzione ≥ 1920×1080
- [ ] Formato PNG
- [ ] Nessun dato personale visibile
- [ ] UI in italiano
- [ ] Watermark demo credibile (non "Test")
- [ ] Log mostra successi (verdi), non solo errori
- [ ] Barra progresso > 0% e < 100%
- [ ] Nomi file output realistici

---

## 🎥 Video Demo (Opzionale per uptodown.dev)

**Specifiche**:
- Durata: 30-60 secondi
- Risoluzione: 1920×1080 @ 30 fps
- Formato: MP4 (H.264)
- Audio: Nessuno o musica royalty-free bassa
- Contenuto: Avvio → Selezione cartella → Opzioni → Avvio → Progresso → Apertura cartella output → Zoom watermark

**Tool registrazione**: Xbox Game Bar (`Win+G`), OBS Studio, ShareX

---

## 📋 Checklist Pubblicazione Store

| Piattaforma | Screenshot Richiesti | Note |
|-------------|---------------------|------|
| **uptodown.dev** | 5 obbligatori + 1 icona 512×512 | Icona = `icon.ico` estrattata o `icon_512.png` |
| **Microsoft Store** | 4+ screenshot + 1 wide banner (2340×1200) | Requisiti stricte |
| **GitHub Releases** | 3-5 nelle release notes | Allegati binari |
| **Sito web** | Hero (1920×800) + 3 feature shots | WebP ottimizzato |

---

*Guida Screenshot v2.55.0 — Gennaio 2025*