# Release Notes v2.57.0

**Franchetti Raw Converter Pro** — Release v2.57.0  
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

## Correzioni rapide

Nella scheda **Sviluppo RAW** c'è una nuova scheda **CORREZIONI RAPIDE**:

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
- Senza analisi il programma si comporta come la 2.56.0: il piano per-file è
  opzionale.

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
