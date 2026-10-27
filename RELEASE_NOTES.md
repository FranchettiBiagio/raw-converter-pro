# Release Notes v2.55.0

**Franchetti Raw Converter Pro** — Release v2.55.0  
**Data**: 27 Ottobre 2026  
**Build**: 2.55.0.0

---

## Il profilo predefinito ora punta sulla qualità

La 2.55.0 nasce per rispondere a un problema concreto: gli ingrandimenti al 100%
mostravano ancora grana e dettagli impastati, soprattutto dopo il ridimensionamento
e la nitidezza.

Il nuovo profilo predefinito è:

| Impostazione | Valore |
|---|---|
| Lato massimo | **3000 px** |
| Formato | **JPEG** |
| Qualità | **90** |
| RIMUOVI GRANA (AUTO ISO) | **attivo** |
| Riduzione rumore | **88 / 92** |
| Nitidezza | **0,9 / 0,9** |

Il risultato tipico è un JPEG da **0,6–1,3 MB** con dettaglio utilizzabile anche
a forte ingrandimento. Chi ha bisogno di file ancora più piccoli può scegliere
1920–2048 px; per la stampa restano disponibili Originale e TIFF.

---

## Denoise ibrido: pulito nelle zone piatte, dettagliato sul soggetto

Il denoise non usa più un solo filtro. Ora lavora in due fasi:

1. **Guided filter + coring** su luminanza e crominanza. La grana fine viene spenta,
   mentre i bordi e le texture reali vengono conservati.
2. **Non-local means solo nelle zone piatte** (cieli, pareti, ombre). È qui che
   restava il rumore più visibile dopo la nitidezza.

La crominanza viene elaborata a metà risoluzione: più veloce e senza aloni.
La forza si adatta automaticamente all'ISO del RAW.

> Il denoise non-locale è volutamente limitato alle aree uniformi. Visi, capelli,
> tessuti e particolari architettonici non vengono “lisciati” come con un filtro
> globale.

---

## Nitidezza protetta dal rumore

La nitidezza classica tende a far riemergere la grana nelle zone piatte. In questa
versione la maschera di nitidezza ha una **soglia stimata sul rumore**:

- i dettagli veri vengono accentuati;
- le differenze minime, tipiche della grana, restano spente;
- non si crea l'effetto “plastica” dopo il denoise.

L'ordine della pipeline è stato corretto: **curva → denoise → nitidezza**.
L'esposizione automatica viene applicata prima del denoise, così il rumore
introdotto dalla schiaritura viene pulito.

---

## PIÙ LUMINOSA più controllata

**PIÙ LUMINOSA** è stata resa più conservativa:

- limite sulla schiaritura delle ombre profonde: un notturno non diventa giorno;
- vividezza ridotta rispetto alla 2.54.0;
- rimosso il micro-contrasto finale che faceva riemergere la grana;
- esposizione applicata alla sola luminanza, senza spostare i colori.

Nelle foto molto scure il risultato resta più naturale e pulito. Per i notturni
spinti è comunque consigliato usare Esposizione e Ombre manuali.

---

## RIMUOVI GRANA subito sotto PIÙ LUMINOSA

Il pulsante **RIMUOVI GRANA (AUTO ISO)** è stato spostato direttamente sotto
**PIÙ LUMINOSA**, sia nel tab **Batch** sia nel tab **Sviluppo RAW**.

- è **attivo di default**;
- quando è attivo diventa verde e mostra **GRANA RIMOSSA (AUTO ISO)**;
- un secondo clic ripristina i valori manuali precedenti.

Il pulsante imposta **88 / 92** e nitidezza **0,9 / 0,9**.

---

## Preset aggiornati

Tutti i preset usano il nuovo motore, il denoise automatico e una nitidezza
controllata:

| Preset | Output | Nitidezza |
|---|---|---|
| Web / Social | 2048 px, JPEG 90 | 0,8 / 0,8 |
| Stampa Fine Art | Originale, TIFF 100 | 0,7 / 1,0 |
| Archivio JPEG | Originale, JPEG 95 | 0,6 / 1,0 |
| Ritratto | 3000 px, JPEG 92 | 0,8 / 0,9 |
| Paesaggio | 3000 px, JPEG 92 | 1,0 / 1,0 |
| Bianco e Nero | 3000 px, JPEG 92 | 0,9 / 0,9 |

La grana sintetica non è più attiva per impostazione predefinita.

---

## Tethering multi-marca

La scheda **Tethering & Cloud** ora spiega come lavorare con:

- **Canon** — EOS Utility / tethering Canon;
- **Nikon** — NX Tether o SnapBridge;
- **Fujifilm** — X Acquire / tethering Fujifilm;
- **Panasonic** — Lumix Tether;
- **OM System / Olympus** — OM Capture;
- **Leica** — Leica Tethered / Image Shuttle.

Per queste marche si usa il software del produttore e si monitora la sua cartella
di destinazione: ogni scatto viene sviluppato automaticamente. **Sony** conserva
anche il controllo Wi-Fi diretto con Smart Remote Control.

---

## Prestazioni misurate

Test su 4 RAW Sony A7S da 24 MP, profilo predefinito 3000 px con denoise attivo:

| Test | Tempo | Output |
|---|---:|---|
| Batch di 4 file, 3000 px | **12,8 s** | 743 / 639 / 609 / 915 KB |
| Singola foto, 3000 px | **8–9 s** | circa 0,6–1,3 MB |
| Stampa Fine Art, originale, TIFF | **circa 40-45 s/foto** | TIFF senza perdita |
| Archivio JPEG, originale | **circa 40-45 s/foto** | JPEG qualità 95 |

I preset a risoluzione originale sono più lenti perché il denoise non-locale
lavora anche sui 24 MP. È un costo voluto per la qualità di stampa.

---

## Compatibilità e note

- **Windows 10/11 x64**, nessuna installazione obbligatoria.
- I file originali non vengono mai modificati.
- L'EXIF viene preservato nei JPEG.
- La 2.55.0 legge le configurazioni JSON salvate con le versioni precedenti.
- Il profilo predefinito cambia rispetto alla 2.54.0: se preferisci il vecchio
  flusso leggero, imposta 1920 px e disattiva **RIMUOVI GRANA**.

---

## Download

- **Portable**: [FranchettiRawConverterPro.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe)
- **Installer**: [Franchetti_Raw_Converter_Setup_v2.55.0.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/Franchetti_Raw_Converter_Setup_v2.55.0.exe)
- **Release**: [v2.55.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.55.0)

Per assistenza, salva il **Log** e descrivi il passaggio che ha causato il problema.
