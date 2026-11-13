# Microsoft Store — Testo del listing v2.58.1

Testo pronto per il **Partner Center** (solo aggiornamento della scheda, nessun
nuovo pacchetto). Campi pensati per la pubblicazione **EXE/MSI**: nel Partner
Center la scheda descrive l'app, mentre il file caricato resta l'installer
Inno Setup `Franchetti_Raw_Converter_Setup_v2.58.1.exe`.

> Nota: i limiti di carattere indicati sono quelli tipici del Partner Center.
> I testi sono volutamente più corti, così non vengono troncati.

---

## Nome prodotto

```text
Franchetti Raw Converter Pro
```

---

## Descrizione breve (max 1.000 caratteri)

```text
Convertitore RAW professionale per Windows: 25+ formati, pipeline Y/Cb/Cr, profili di prestazione adattivi, tethering multi-marca, watermark, copyright EXIF/IPTC, galleria cliente HTML e invio Telegram/Dropbox. Preset portabili .frcpreset, import XMP (beta) e LUT 3D .cube. Gli originali non vengono mai modificati. Portable, open source (MIT), zero telemetria.
```

---

## Descrizione completa (max 10.000 caratteri)

```text
Franchetti Raw Converter Pro trasforma i file RAW in JPEG, TIFF e PNG ottimizzati con una pipeline matematica in spazio Y/Cb/Cr, pensata per fotografi professionisti, studi e chi consegna molte foto in poco tempo.

Tutto avviene in un'unica applicazione Windows, portable o installabile, open source con licenza MIT e senza telemetria. Gli originali vengono solo letti: nessuna foto viene mai sovrascritta o modificata.

FORMATI RAW SUPPORTATI (25+)
Sony ARW, SRF, SR2; Canon CR2, CR3, CRW; Nikon NEF, NRW; Fujifilm RAF; Olympus/OM System ORF; Panasonic RW2, RAW; DNG; e ancora PEF, SRW, X3F, 3FR, FFF, RWL, DCR, K25, KDC, MOS, MRW. Decodifica con rawpy/LibRaw, demosaicatura AHD per i sensori Bayer e AAHD 12 per Fujifilm X-Trans.

PIPELINE Y/Cb/Cr
La luminanza viene separata dalla crominanza: il contrasto sigmoidale protegge luci e ombre, la vivacità selettiva interviene solo sui toni spenti, il denoise ibrido lavora sulle zone piatte e la nitidezza controllata agisce solo su Y con una soglia sul rumore. Il risultato sono dettagli puliti, incarnati naturali e nessun alone colorato.

PRESTAZIONI ADATTIVE
Il pannello PRESTAZIONI legge i core fisici, i core logici e la RAM libera del PC. Scegli il profilo Veloce, Bilanciato o Massima qualità; il numero di processi è automatico, con slider per l'override manuale. Il pool multi-processo parte solo quando il numero e il peso dei file lo giustificano, così i batch piccoli restano immediati. Il benchmark sui tuoi file misura il tempo reale su 1-2 foto in una cartella temporanea e fornisce una stima del batch, con file/min ed ETA durante la conversione. Nella 2.58.1 il profilo Veloce è circa il 39% più rapido sul test da 24 MP a 3000 px.

PRESET PORTABILI .frcpreset
I preset sono file JSON leggibili, con nome, autore, descrizione, tag, una sezione look e un output facoltativo. Non contengono percorsi, cartelle, credenziali cloud, FTP o copyright e non vengono mai eseguiti. Puoi salvare il look corrente, importare, esportare, eliminare e applicare un preset con anteprima. I sei preset storici sono già inclusi: Web / Social, Stampa Fine Art, Archivio JPEG, Ritratto, Paesaggio e Bianco e Nero. I pacchetti scaricabili usano un manifest con checksum SHA-256 e l'importazione è sempre manuale: l'app non scarica nulla da sola.

IMPORT XMP (BETA) E LUT 3D
Importa i preset Lightroom .xmp con mappatura parziale di esposizione, toni, colore, denoise, nitidezza, vignettatura e split toning. Profili camera, curve puntuali, texture e film simulation restano fuori e l'app lo dichiara prima di applicare il preset. Le LUT 3D .cube si applicano con interpolazione trilineare, intensità regolabile e calcolo a blocchi per non consumare memoria sulle foto grandi.

SMART BATCH
ANALIZZA FILE decodifica i RAW a mezza risoluzione e misura esposizione, clipping, contrasto, colore, incarnati, rumore e ISO. Le correzioni suggerite sono conservative e diverse per ogni foto; puoi applicarle tutte oppure usare solo le impostazioni globali. Le correzioni rapide (CONTRASTO NATURALE, SALVA LUCI, COLORE PIÙ RICCO, SOVRAESPOSTA, SOTTOESPOSTA, ANNULLA CORREZIONI) aggiornano gli slider esistenti e sono reversibili.

TETHERING E CLOUD
Il tethering multi-marca monitora una cartella hot-folder con watchdog: appena il file arriva via Wi-Fi viene elaborato con pipeline completa, watermark ed EXIF. È disponibile anche il collegamento diretto alle Sony via Wi-Fi. Il Cloud Dispatch invia i risultati a Telegram e Dropbox; gli altri canali sono predisposti e vengono saltati senza errori se non attivi.

WATERMARK, EXIF E GALLERIA CLIENTE
Watermark proporzionale con logo PNG trasparente, alpha compositing e opacità configurabile. Preservazione dei blocchi EXIF, correzione dell'orientamento, GPS e timestamp; copyright EXIF Artist/Copyright/ImageDescription e IPTC By-line/Copyright Notice/Caption-Abstract/Object Name. La galleria cliente HTML è autonoma, con miniature, checkbox, copia selezione e download dell'elenco in .txt.

PRIVACY E SICUREZZA
Nessuna telemetria, nessun crash reporting, nessun aggiornamento automatico, nessuna scrittura nel registro di Windows e nessuna raccolta di dati personali. La rete viene usata solo se attivi Cloud Dispatch o Wi-Fi FTP. Gli originali sono sempre in sola lettura.

REQUISITI
Windows 10 versione 1809 o successiva, architettura x64, 2 GB di RAM minimi (8 GB consigliati), 100 MB di spazio libero. Per batch grandi si consiglia un SSD e una CPU multi-core.

LICENZA
MIT: gratuito per uso personale e commerciale. Attribuzione apprezzata: "Franchetti Raw Converter Pro by Franchetti".
```

---

## Novità della versione 2.58.1 (max 1.500 caratteri)

```text
Preset portabili .frcpreset: file JSON con look e output facoltativo, senza percorsi, cloud, FTP o copyright. Salva, importa, esporta, elimina e applica i preset con anteprima; i sei preset storici sono già migrati. Pacchetti scaricabili con manifest e checksum SHA-256, importazione sempre manuale. Import XMP (beta) con mappatura parziale dei preset Lightroom. LUT 3D .cube con interpolazione trilineare e intensità regolabile. Profilo Veloce più rapido: denoise non-locale a metà risoluzione e stima del rumore campionata, circa -39% sul test da 24 MP a 3000 px. Bilanciato e Massima qualità restano invariati. Correzioni Linux sperimentali: filtro .RAF maiuscolo, core fisici da /proc/cpuinfo, memoria da /proc/meminfo, semafori rilasciati correttamente e messaggio di dipendenza più chiaro.
```

---

## Caratteristiche principali (max 20 voci, 200 caratteri ciascuna)

```text
Supporto a 25+ formati RAW, inclusi ARW, CR3, NEF, RAF, ORF, RW2 e DNG
Pipeline Y/Cb/Cr con contrasto sigmoidale e vivacità selettiva
Denoise ibrido e nitidezza controllata solo sul canale di luminanza
Profili di prestazione Veloce, Bilanciato e Massima qualità
Numero di processi automatico da core fisici, core logici e RAM libera
Benchmark reale sui tuoi file con stima, file/min ed ETA
Preset portabili .frcpreset con import, export e anteprima
Pacchetti preset con manifest e checksum SHA-256
Import XMP (beta) con mappatura parziale dei preset Lightroom
LUT 3D .cube con interpolazione trilineare e intensità regolabile
Tethering multi-marca con hot-folder e supporto Sony Wi-Fi
Cloud Dispatch per Telegram e Dropbox
Watermark proporzionale con logo PNG trasparente
Copyright EXIF/IPTC e preservazione dei metadati originali
Galleria cliente HTML con selezione e download elenco
Batch ricorsivo con nomi personalizzati e anti-collisione
Interfaccia scura professionale in italiano
Gli originali non vengono mai modificati
Nessuna telemetria e nessuna raccolta dati
Portable, open source, licenza MIT
```

---

## Parole chiave (max 7, 30 caratteri ciascuna)

```text
convertitore RAW
RAW in JPEG
batch fotografico
preset fotografici
tethering Wi-Fi
watermark foto
conversione RAW
```

---

## Requisiti di sistema

| Campo | Valore |
|---|---|
| Sistema operativo | Windows 10 versione 1809 o successiva; Windows 11 |
| Architettura | x64 |
| RAM minima | 2 GB |
| RAM consigliata | 8 GB o più |
| Spazio su disco | 100 MB liberi (1 GB consigliato) |
| CPU | Qualsiasi x64; multi-core consigliata |
| DirectX | Non richiesto |
| Connessione Internet | Non richiesta, salvo Cloud Dispatch o Wi-Fi FTP |
| GPU | Non richiesta: elaborazione su CPU |

---

## Informazioni aggiuntive per il Partner Center

| Campo | Testo |
|---|---|
| Sviluppato da | Franchetti |
| Copyright | © 2026 Franchetti. Tutti i diritti riservati. |
| Licenza | MIT License |
| Categoria consigliata | Fotografia |
| Sottocategoria | Strumenti di conversione / Elaborazione immagini |
| Sito web | https://franchettibiagio.github.io/raw-converter-pro/ |
| Informativa sulla privacy | https://github.com/FranchettiBiagio/raw-converter-pro/blob/main/PRIVACY.md |
| Supporto | https://github.com/FranchettiBiagio/raw-converter-pro/issues |
| Note sulla versione | https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.58.1 |
| Lingua del listing | Italiano (principale); inglese facoltativo |
| Tipo di pacchetto | EXE/MSI — installer Inno Setup v2.58.1 |

---

## Materiale grafico pronto

La cartella `store_assets/` (e l'archivio `store_assets_v2.58.1.zip`) contiene:

- 9 screenshot reali 1920×1080 in ordine di caricamento (`store_assets/screenshots/`);
- immagine hero 2340×1200 (`store_assets/hero/`);
- logo Store 300×300, 1080×1080 e 2160×2160 (`store_assets/logos/`).

Istruzioni campo per campo e ordine degli screenshot:
`store_assets/README.md`.

---

## Controlli prima della pubblicazione

- [ ] Nome prodotto invariato rispetto alla scheda esistente
- [ ] Descrizione breve e completa incollate senza formattazione Markdown
- [ ] Caratteristiche principali: massimo 20 voci
- [ ] Parole chiave: massimo 7, ognuna entro 30 caratteri
- [ ] URL privacy e supporto raggiungibili
- [ ] Screenshot aggiornati alla 2.58.1 (minimo 4, 16:9)
- [ ] Immagine hero 2340×1200 aggiornata, se richiesta
- [ ] Installer EXE/MSI già caricato nella sottomissione esistente
- [ ] **Firma Authenticode non necessaria** per questo prodotto: l'installer
      v1.0.0 distribuito dallo Store è `NotSigned`. Vedi
      `store_assets/PUBLISH_EXE_FREE.md`
- [ ] **Package URL** versionato aggiornato all'installer v2.58.1
- [ ] **Installer parameters** `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`
- [ ] Codice di ritorno successo `0`, annullamento `2`
- [ ] Nessuna modifica al pacchetto: solo testo della scheda
