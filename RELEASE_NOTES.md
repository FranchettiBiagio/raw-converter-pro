# Release Notes v2.58.0

**Franchetti Raw Converter Pro** - Release v2.58.0  
**Data**: 2 Novembre 2026  
**Build**: 2.58.0.0

---

## Prestazioni adattive, senza interruttori finti

La nuova finestra **PRESTAZIONI** (pulsante sotto `USA TUTTI I CORE`) legge i
core **fisici** e **logici** del PC e la RAM libera. Da qui scegli:

- **Veloce**: tutti i core logici e denoise leggero, per consegnare prima;
- **Bilanciato**: core fisici, qualità predefinita;
- **Massima qualità**: denoise e nitidezza più curati per stampe e consegne.

Il numero di processi è automatico per impostazione predefinita, ma lo slider
permette di forzarlo. Il batch non avvia più un pool multi-processo per due
JPEG minuscoli: la soglia tiene conto di peso e numero di file, quindi i batch
piccoli restano sequenziali e veloci.

Il pulsante **BENCHMARK SUI MIEI FILE** elabora 1-2 file reali in una cartella
temporanea (gli originali sono solo letti) e misura il tempo vero. Da lì arriva
una stima del batch e, durante la conversione, la barra mostra **file/min** ed
**ETA** calcolati sul lavoro già completato.

---

## Galleria cliente con selezione

Ogni sessione FTP crea una cartella separata per **Originali**,
**Anteprime_Cliente** e **Galleria_Cliente**. In `Galleria_Cliente` viene
scritto un file `index.html` autonomo:

- miniature delle anteprime;
- caselle per selezionare le foto preferite;
- pulsante **Copia selezione** e **Scarica elenco .txt**;
- nessun server o servizio esterno: funziona da cartella condivisa o chiavetta.

La galleria si aggiorna a ogni anteprima e si apre dal tab **Wi-Fi FTP**.

---

## Copyright anche nei metadati

Il copyright non è più solo sovrapposto all'immagine. Con l'interruttore
**Scrivi copyright nei metadati EXIF/IPTC** viene scritto in:

- **EXIF**: `Artist`, `Copyright`, `ImageDescription`;
- **IPTC**: `By-line`, `Copyright Notice`, `Caption-Abstract`, `Object Name`.

Vale sia per il batch sia per le anteprime FTP. L'autore si imposta in
**AVANZATE**; il testo usa lo stesso campo del watermark e, se vuoto, il
predefinito `© Franchetti <anno>`.

---

## Invio automatico opzionale

Nel tab **Wi-Fi FTP** c'è un interruttore per inviare automaticamente le
anteprime ai canali cloud già attivi (Telegram/Dropbox) subito dopo la
creazione. È spento per default: nessun upload a sorpresa.

---

## Quick win di qualità e UX

- anteprima PRIMA/DOPO con **contain**: le foto verticali non perdono più testa
  e piedi;
- overlay FTP sempre con **Pillow**, quindi `©`, accenti e Unicode sono corretti;
- testi lunghi troncati con ellissi, senza uscire dall'immagine;
- log di pyftpdlib ridotti e nessun messaggio duplicato nel tab Log;
- cartelle FTP organizzate per sessione/data;
- rimossa la variabile inutilizzata dell'anteprima.

---

## Compatibilità

Nessuna nuova dipendenza: IPTC viene scritto direttamente nel blocco APP13,
senza `iptcinfo3`. Restano richiesti `pyftpdlib` e OpenCV come nella 2.57.

---

## Download v2.58.0

- **Portable**: `FranchettiRawConverterPro.exe` (91,9 MB)
- **Installer**: `Franchetti_Raw_Converter_Setup_v2.58.0.exe` (93,5 MB)

Gli hash SHA-256 aggiornati sono riportati in `SHA256SUMS.txt` e nella pagina
della release GitHub.

---

# Archivio v2.57.0

**Franchetti Raw Converter Pro** - Release v2.57.0  
**Data**: 2 Novembre 2026  
**Build**: 2.57.0.0

---

## Smart Batch: ogni foto riceve la sua correzione

La 2.57.0 rende il batch davvero intelligente. Prima di convertire, il programma
può leggere **tutti i file** e preparare un piano di correzione diverso per ogni
immagine. Non è un preset unico applicato a tutto: esposizione, luci, ombre,
contrasto, colore e denoise vengono scelti in base ai dati reali della foto.

Il flusso è semplice:

1. seleziona la cartella o i file;
2. premi **ANALIZZA FILE**;
3. controlla la tabella con stato e correzioni suggerite;
4. lascia attiva **Usa correzioni per file** e avvia il batch.

L'analisi **non modifica mai gli originali** e può essere ignorata in qualsiasi
momento deselezionando la casella.

---

## Interfaccia semplificata: tutto nella finestra di conversione

La scheda **Sviluppo RAW** è stata rimossa. Ora la schermata **Batch** contiene:

- **anteprima PRIMA / DOPO** integrata, aggiornata mentre sposti gli slider;
- **correzioni rapide** a un clic;
- pulsante **AVANZATE** che apre una finestra separata con tutti gli slider,
  la curva tonale, lo split toning, i nomi file, il watermark e i preset.

L'anteprima decodifica il RAW **una sola volta** e riusa la base ridotta: gli
slider non rileggono il file a ogni movimento. L'originale non viene mai
modificato. Il pulsante **APRI ANTEPRIMA GRANDE** mostra il confronto a piena
finestra.

---

## Nuovo Wi-Fi FTP: scatta, invia, ricevi l'anteprima cliente

La nuova scheda **Wi-Fi FTP** accende un server FTP integrato nel programma,
senza software esterni:

- ascolta sull'IP locale del PC, porta **2121**;
- utente **camera**, password **1234**;
- la fotocamera scrive nella cartella **Originali**;
- appena un file è completo, il programma lo sviluppa in background.

Pipeline automatica:

1. sviluppo RAW con `use_camera_wb=True` e `use_camera_matrix=True`;
2. Fujifilm → demosaicizzazione **AAHD (qualità 12)**, altri marchi → **AHD (3)**;
3. ridimensionamento del lato lungo a **2000 px** con Lanczos;
4. nome file originale in basso a sinistra e copyright/watermark in basso a
   destra, testo bianco su bordo nero più spesso per la massima leggibilità;
5. JPEG qualità **85** in **Anteprime_Cliente**.

L'interruttore **RICEZIONE WI-FI FTP** mostra subito IP, porta, utente e
password; spegnendolo il server viene chiuso e la porta 2121 liberata.

> **Compatibilità onesta:** Nikon, Canon, Fujifilm e molti modelli Sony con
> trasferimento FTP integrato possono inviare direttamente. I modelli senza
> client FTP nella fotocamera non possono farlo da soli: in quel caso restano
> disponibili l'app del produttore, la scheda o la cartella monitorata. Il
> Bluetooth non trasferisce RAW di alta qualità in modo universale e non viene
> simulato.

---

## Correzioni rapide

Nella finestra di conversione **Batch** c'è la scheda **CORREZIONI RAPIDE**:

| Pulsante | Effetto |
|---|---|
| **CONTRASTO NATURALE** | Contrasto, chiarezza e neri più incisivi senza effetto HDR |
| **SALVA LUCI** | Attiva la protezione delle alte luci e riduce luci/bianchi |
| **COLORE PIÙ RICCO** | Vivacità, saturazione e canali HSL più presenti |
| **SOVRAESPOSTA** | Esposizione e luci più basse per recuperare una foto chiara |
| **SOTTOESPOSTA** | Esposizione, ombre e neri più alti per una foto scura |
| **ANNULLA CORREZIONI** | Ripristina tutti i valori precedenti alle correzioni rapide |

Le correzioni sono **cumulative**, aggiornano gli slider esistenti e sono
**reversibili in blocco**. Il pulsante **SALVA LUCI** diventa verde quando la
protezione è attiva.

---

## Protezione luci: comprimere, non scurire

Il nuovo parametro `proteggi_luci` applica una curva di spalla alle alte luci:

- sotto la soglia l'immagine resta identica;
- sopra la soglia i toni chiari vengono compressi, così il cielo, il vestito
  bianco o la pelle illuminata mantengono separazione;
- il bianco pieno resta bianco: non è un semplice abbassamento globale
  dell'esposizione;
- il recupero avviene prima della fase colore e del denoise.

> Se il RAW o il JPEG è **completamente bruciato**, il dettaglio non esiste più:
> nessun algoritmo può ricostruirlo. La protezione luci lavora sui dati ancora
> presenti, non sui pixel già saturi.

---

## Come funziona l'analisi

Per ogni file il programma misura:

- luminanza mediana e percentili 1–5% / 95–99%;
- clipping delle alte luci e delle ombre;
- clipping reale del sensore RAW, quando disponibile;
- ampiezza dell'istogramma (contrasto);
- saturazione media e percentuale di incarnati;
- rumore stimato e ISO;
- origine RAW o immagine standard.

I RAW vengono decodificati a **mezza risoluzione** con la stessa resa
auto-bright della conversione finale. Le immagini standard vengono ridotte a
1200 px per l'analisi. Il risultato è veloce ma rappresentativo.

Le regole sono conservative:

- foto scura → esposizione +, ombre +, denoise più prudente;
- foto chiara → esposizione −, luci −;
- alte luci critiche → protezione luci, bianchi −;
- ombre chiuse → ombre +, neri +;
- contrasto basso → contrasto e chiarezza +;
- colore spento → vivacità +, saturazione contenuta;
- ISO alto o rumore alto → denoise più deciso, nitidezza conservativa;
- foto già bilanciata → **OK**, nessuna correzione.

---

## Tabella di analisi

Dopo **ANALIZZA FILE** si apre una finestra con:

- nome file;
- stato **OK / CORREGGI / CRITICO / ERRORE**;
- motivo della correzione;
- EV, luci, ombre, contrasto, colore e denoise suggeriti.

Il riepilogo indica quanti file sono stati analizzati, quanti vanno corretti,
quanti sono già corretti e quanti sono critici.

---

## Correzioni di qualità

Questa release non si limita ad aggiungere pulsanti: durante la validazione sono
emersi due difetti reali della pipeline, corretti prima del rilascio.

- **Vivacità selettiva corretta.** La formula precedente spostava i canali verso
  il massimo, quindi **riduceva** la saturazione: su un incarnato la crominanza
  scendeva da 0,300 a 0,237 e su un colore saturo da 0,700 a 0,357. Ora la
  crominanza viene scalata attorno alla luminanza, con più incisività sui toni
  spenti e quasi nessun effetto sui colori già saturi. Su una foto reale la
  crominanza media passa da 0,095 a 0,126 (**+33%**) senza schiarire la pelle.
- **Protezione luci C1.** La curva di spalla ora usa un innesto cubico di
  Hermite: valore e pendenza sono continui nel punto di soglia. Su un gradiente
  liscio l'artefatto di continuità scende di oltre **100 volte**, il bianco
  resta **1,0** e i toni sotto 0,68 restano **identici**.
- **Nessuna regressione nascosta.** Con `vivacità = 0` e `proteggi_luci`
  disattivato, l'output è **pixel per pixel identico alla 2.56.0**.

---

## Test

- Analisi di **4 RAW Sony reali**: circa **1,3 s** in parallelo.
- Analisi di **44 file misti** (4 RAW + 40 JPEG): circa **3,7 s**.
- Batch di **4 RAW** con piano per-file a 600 px, 4 processi: **4/4 OK** in
  circa **5,9 s**.
- Verifica visiva su foto sottoesposta, sovraesposta, notturna e con alte luci
  critiche.
- Batch parallelo e sequenziale con correzioni per file: nessun errore, nessun
  file temporaneo residuo.

---

## Compatibilità

- **Windows 10/11 x64**, portable o installer.
- I file originali non vengono mai modificati.
- L'EXIF viene preservato nei formati supportati.
- Le configurazioni e il flusso di lavoro delle versioni precedenti restano
  validi.
- Il profilo predefinito resta **3000 px, JPEG 90, denoise automatico**.
- Senza analisi il flusso di lavoro è quello della 2.56.0: il piano per-file è
  opzionale.
- Con **vivacità 0** e **protezione luci disattivata** l'output è pixel per
  pixel identico alla 2.56.0. La resa predefinita cambia solo per la correzione
  della vivacità, che ora aumenta davvero il colore invece di ridurlo.

---

## Download

- **Portable**: [FranchettiRawConverterPro.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe)
- **Installer**: [Franchetti_Raw_Converter_Setup_v2.57.0.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/Franchetti_Raw_Converter_Setup_v2.57.0.exe)
- **Release**: [v2.57.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.57.0)

## Integrità

Gli hash SHA-256 aggiornati sono riportati in `SHA256SUMS.txt` e nella pagina
della release.

Per assistenza, salva il **Log** e descrivi il passaggio che ha causato il
problema.
