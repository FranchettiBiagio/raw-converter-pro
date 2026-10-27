# Guida completa a Franchetti Raw Converter Pro

**Versione 2.54.0 — Windows 10/11 — Italiano**

Questa guida spiega, in modo semplice, **tutte le funzioni** del programma e indica le impostazioni consigliate per ottenere foto pulite, naturali e nitide. Non serve essere esperti: basta seguire i passaggi.

> **Regola d'oro:** il programma **non modifica mai i file originali**. Lavora sempre su una copia e scrive i risultati nella cartella di destinazione. Tieni comunque un backup delle foto importanti.

---

## Indice

1. [Primi passi in 2 minuti](#1-primi-passi-in-2-minuti)
2. [Come è fatta la finestra](#2-come-e-fatta-la-finestra)
3. [Scheda Batch: conversione di tante foto](#3-scheda-batch-conversione-di-tante-foto)
4. [Scheda Sviluppo RAW: regolazioni fotografiche](#4-scheda-sviluppo-raw-regolazioni-fotografiche)
5. [Scheda Tethering & Cloud](#5-scheda-tethering-cloud)
6. [Scheda Log: messaggi ed errori](#6-scheda-log-messaggi-ed-errori)
7. [Impostazioni consigliate per tipo di foto](#7-impostazioni-consigliate-per-tipo-di-foto)
8. [Flussi di lavoro pronti all'uso](#8-flussi-di-lavoro-pronti-alluso)
9. [Domande frequenti e soluzione problemi](#9-domande-frequenti-e-soluzione-problemi)
10. [Glossario semplice](#10-glossario-semplice)
11. [Scheda riassuntiva da stampare](#11-scheda-riassuntiva-da-stampare)

---

## 1. Primi passi in 2 minuti

1. **Apri il programma.**
2. Nella scheda **Batch**, premi **Seleziona cartella** e scegli la cartella che contiene i file RAW (oppure **Seleziona file RAW** per scegliere solo alcuni file).
3. Premi **Sfoglia** accanto a **Cartella output** e scegli una cartella **diversa** da quella delle foto originali.
4. Controlla **Lato max (px)**, **Qualità**, **Formato** e, se vuoi, attiva **PIÙ LUMINOSA** e **RIMUOVI GRANA (AUTO ISO)**.
5. Premi **AVVIA CONVERSIONE BATCH**. Attendi la fine e premi **Apri cartella output**.

Per una prova sicura: usa prima **5–10 foto** in una cartella di prova, guarda i risultati, poi lancia il gruppo completo.

---

## 2. Come è fatta la finestra

La finestra ha quattro schede:

| Scheda | A cosa serve |
|---|---|
| **Batch** | Converte una o centinaia di foto in JPEG, PNG, TIFF o WebP. È la scheda principale. |
| **Sviluppo RAW** | Imposta esposizione, colore, dettaglio, riduzione grana, nitidezza, vignettatura e split toning. |
| **Tethering & Cloud** | Collega una Sony via Wi-Fi, monitora una cartella e invia i risultati a Telegram o Dropbox. |
| **Log** | Mostra cosa sta facendo il programma e permette di salvare il registro. |

In basso c'è la **barra di stato**: a sinistra il messaggio corrente, a destra il percorso della cartella di output. In fondo alla scheda Batch ci sono i pulsanti di avvio, annullamento, rimozione grana, avanzamento e apertura della cartella.

> **Importante:** le regolazioni della scheda **Sviluppo RAW** non sono un'anteprima dal vivo. Vengono applicate quando avvii la conversione Batch. Per provarle, converti prima una sola foto.

---

## 3. Scheda Batch: conversione di tante foto

### 3.1 Sorgente

- **File / Cartella:** mostra cosa stai convertendo.
- **Seleziona cartella:** converte tutti i file supportati nella cartella scelta.
- **Seleziona file RAW:** converte solo i file che selezioni. Puoi selezionare più file con `Ctrl` o `Maiusc`.
- **Sottocartelle:** se è attivo, il programma entra anche nelle sottocartelle. La cartella di output viene esclusa automaticamente per evitare di rielaborare i risultati.
- Puoi anche scrivere più percorsi nel campo, separati da punto e virgola (`;`).

**Formati accettati:** RAW di Sony, Canon, Nikon, Fujifilm, Olympus/OM System, Panasonic, Pentax, Samsung, Sigma, Hasselblad, Phase One e altri (`.arw`, `.cr2`, `.cr3`, `.nef`, `.raf`, `.dng`, `.orf`, `.rw2`, ecc.) e immagini già pronte (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.bmp`, `.webp`).

**Consiglio:** se nella cartella ci sono anche vecchi JPEG, il programma li convertirà come immagini normali. Per un batch di soli RAW, seleziona i file RAW oppure usa una cartella dedicata.

### 3.2 Destinazione

- **Cartella output:** dove vengono salvate le foto finite.
- **Regola:** usa una cartella **diversa** dalla sorgente. È più sicuro e rende immediato capire quali file sono nuovi.
- **Apri cartella output:** apre Esplora file nella destinazione.

### 3.3 Dimensioni e formato

#### Lato max (px)

Il programma ridimensiona la foto **prima** di applicare contrasto, colore, nitidezza e riduzione grana. Così è molto più veloce e il risultato è ottimizzato per la dimensione finale.

| Pulsante | Uso tipico |
|---|---|
| **640** | Anteprime, miniature, siti molto leggeri |
| **800** | Blog, vecchi schermi, immagini piccole |
| **1024** | Web veloce, documenti, presentazioni |
| **1200** | Siti web, gallery leggere |
| **1600** | Web di qualità, social ad alta risoluzione |
| **1920** | **Impostazione predefinita consigliata** per web e social |
| **2048** | Social molto definiti, schermi 2K |
| **2560** | Monitor 2K/4K, stampe piccole |
| **3000** | Stampe 20×30 cm, ritratti |
| **4000** | Stampe grandi, archival leggero |
| **6000** | Massima qualità per stampe molto grandi |
| **Originale** | Nessun ridimensionamento: usa la risoluzione nativa del RAW |

Puoi anche scrivere un valore personalizzato nel campo. **0** significa **Originale**.

> Il programma **non ingrandisce** mai una foto oltre la sua risoluzione originale: se scrivi un valore più grande, l'immagine resta alla dimensione nativa.

#### Qualità

- Valore da **1 a 100**.
- **JPEG:** 85 è ottimo per il web; 90–95 per clienti e stampe; 100 è il massimo ma il file è molto più grande e non sempre si vede la differenza.
- **WebP:** usa gli stessi valori; 80–90 è di solito più che sufficiente.
- **PNG e TIFF:** la qualità non si applica; PNG è senza perdita (file grandi), TIFF usa compressione LZW senza perdita.

**Consiglio:** non usare qualità 100 per tutte le foto del web. Qualità **90** è il miglior compromesso tra dettaglio, peso e compatibilità.

#### Formato

| Formato | Quando usarlo | Attenzione |
|---|---|---|
| **JPEG** | Web, social, consegna al cliente, condivisione | Perdita leggera; non riaprire e risalvare molte volte |
| **PNG** | Grafica, schermate, immagini con testi | File molto grandi; non serve per normali foto RAW |
| **TIFF** | Archiviazione, stampa professionale, post-produzione | File molto grandi; compressione LZW senza perdita |
| **WEBP** | Siti web moderni, immagini leggere | Meno compatibile con programmi molto vecchi |

#### Spazio colore

È fissato a **sRGB**, lo standard più compatibile con web, social, Windows e laboratori di stampa. Non è un'impostazione da cambiare.

#### WB fotocamera

Se è attivo, usa il bilanciamento del bianco impostato nella fotocamera al momento dello scatto. È la scelta giusta nella maggior parte dei casi.

- **Attivo:** colori fedeli allo scatto originale.
- **Disattivo:** il programma usa un bilanciamento neutro; utile solo se vuoi ripartire da zero.

#### Preserva EXIF

Salva nel JPEG i dati di scatto: data, fotocamera, obiettivo, ISO, tempi, diaframma, GPS e orientamento. È consigliato **attivo**.

> L'EXIF viene inserito nei **JPEG**. PNG, TIFF e WebP non ricevono gli stessi metadati in questa versione.

#### PIÙ LUMINOSA (BETA)

È un intervento automatico e conservativo:

- schiarisce le foto scure;
- recupera le alte luci solo quando sono realmente bruciate;
- aggiunge **vividezza** ai colori spenti (circa +10–16%);
- applica un micro-contrasto leggerissimo;
- lascia invariati i bianchi e i neri assoluti e i grigi neutri già esposti correttamente.

**Quando attivarla:** foto scure, controluce, interni, giornate nuvolose, foto da smartphone o RAW sottoesposti.

**Quando evitarla:** foto già esposte bene, still life con colori delicati, foto bianco e nero, immagini in cui vuoi mantenere l'atmosfera scura.

> Non è un miracolo: se la foto è completamente nera o bruciata, non può recuperare ciò che non c'è. In quel caso usa le regolazioni manuali di **Esposizione**, **Ombre** e **Luci**.

#### USA TUTTI I CORE

Il programma usa tutti i processori disponibili e riduce automaticamente il numero di processi se la RAM libera non basta. È consigliato **attivo**.

Se il computer ha poca RAM o stai convertendo RAW da 50–60 MP, il programma può usare meno processi: è una protezione, non un errore. Con 16 GB di RAM e molti file, lascia attiva l'opzione e chiudi altri programmi pesanti.

### 3.4 Nomi file e sovrascrittura

- **Mantieni nome originale:** `FOTO (12).ARW` diventa `FOTO (12).jpg`.
- **Disattivato:** usa un nome progressivo, per esempio `IMG_0001.jpg`, `IMG_0002.jpg`.
- **Prefisso:** testo aggiunto prima del nome, per esempio `FRC_`.
- **Suffisso:** testo aggiunto dopo il nome, per esempio `_web`.
- **Se esiste:**
  - **Rinomina:** non sovrascrive; aggiunge `_1`, `_2`, ecc.
  - **Sovrascrivi:** sostituisce il file già presente.
  - **Salta:** non converte il file e lo conta tra i saltati.

**Consiglio:** per il web usa **Rinomina** o **Salta**; per rigenerare una consegna usa **Sovrascrivi**. Evita di sovrascrivere per sbaglio il lavoro di un'altra persona.

Se due file di sottocartelle diverse hanno lo stesso nome, il programma li rinomina automaticamente per non farli scontrare. Non ci saranno due processi che scrivono lo stesso file.

### 3.5 Watermark

- **Applica testo:** attiva o disattiva la scritta.
- **Testo watermark:** il testo da imprimere, per esempio `© Mario Rossi 2026`.
- **Font (px):** dimensione del testo. 12–18 per foto 1920 px; 24–40 per foto 3000–6000 px. Il valore è in pixel, non in punti.
- **Posizione:** basso a destra, basso a sinistra, alto a destra, alto a sinistra, centro.
- **Logo PNG:** carica un'immagine PNG con trasparenza. Il logo viene ridimensionato al 15% del lato lungo e posizionato nella stessa posizione del testo.
- **Carica:** sceglie il file PNG del logo.

**Consiglio:** il watermark deve essere discreto. Per il web usa testo 14–18 px e opacità visibile ma non invadente. Per il logo usa un PNG pulito, senza sfondo bianco. Se il logo ha già il testo, non aggiungere anche il testo del watermark.

### 3.6 Preset e configurazione

Il menu **Preset** imposta in un colpo solo dimensione, qualità, formato e regolazioni di sviluppo. Puoi comunque modificare i valori dopo.

| Preset | Cosa imposta |
|---|---|
| **Personalizzato** | Non cambia nulla: usi le tue impostazioni |
| **Web / Social** | 2048 px, JPEG 85, contrasto 0,35, vivacità 0,40, nitidezza 1,2, chiarezza 0,15, dehaze 0,05 |
| **Stampa Fine Art** | Originale, TIFF, qualità 100, contrasto 0,25, vivacità 0,25, nitidezza 1,6 raggio 1,8, chiarezza 0,10 |
| **Archivio JPEG** | Originale, JPEG 95, contrasto 0,20, vivacità 0,20, nitidezza 0,8, EXIF attivo |
| **Ritratto** | 3000 px, JPEG 92, contrasto 0,22, vivacità 0,20, saturazione 0,95, chiarezza 0,05, ombre +12, luci -8, nitidezza 0,9, riduzione rumore 15/20 |
| **Paesaggio** | 3840 px, JPEG 92, contrasto 0,42, vivacità 0,45, chiarezza 0,30, dehaze 0,20, nitidezza 1,8 raggio 1,6, verdi +12, blu +10 |
| **Bianco e Nero** | 3000 px, JPEG 92, saturazione 0, contrasto 0,45, chiarezza 0,25, nitidezza 1,5, grana 12 |

> I preset **non** sono vincolanti. Dopo averli applicati puoi spostare gli slider. Il preset **Ritratto** imposta una riduzione rumore manuale (15/20): è già attiva anche se il pulsante **RIMUOVI GRANA** non è evidenziato.

**Salva config** e **Carica config** salvano e rileggono tutti i parametri in un file JSON. Sono utili per conservare il tuo stile di sviluppo.

> **Privacy:** il file di configurazione può contenere anche token di Telegram/Dropbox e percorsi del computer. Conservalo in un posto sicuro e non condividerlo.

### 3.7 Barra delle azioni

- **AVVIA CONVERSIONE BATCH:** avvia il lavoro con le impostazioni correnti.
- **ANNULLA:** interrompe il batch e rimuove i file parziali. I file già completati restano.
- **RIMUOVI GRANA (AUTO ISO):** attiva o disattiva il preset intelligente di riduzione rumore. Quando è attivo diventa verde e mostra **GRANA RIMOSSA (AUTO ISO)**.
- **Barra di avanzamento:** mostra quanti file sono stati elaborati, quanti sono riusciti, quanti hanno avuto errori e quanti sono stati saltati.
- **Apri cartella output:** apre la destinazione.

Se un file è corrotto o non supportato, il programma lo segnala e **continua con gli altri**. Un errore non blocca l'intero batch.

---

## 4. Scheda Sviluppo RAW: regolazioni fotografiche

Queste regolazioni si applicano a tutte le foto del batch. Sono pensate per un risultato naturale: meglio poco e buono che troppo e artificiale.

### 4.1 PIÙ LUMINOSA (BETA)

Lo stesso interruttore della scheda Batch. È un'elaborazione automatica dell'esposizione e della vividezza. Attivalo qui o nella scheda Batch: è condiviso.

### 4.2 Esposizione e bilanciamento

| Controllo | Intervallo | Cosa fa | Consiglio |
|---|---|---|---|
| **Esposizione (EV)** | -3,00 … +3,00 | Schiarisce o scurisce l'intera foto | +0,3 per foto un po' scure; -0,3 per foto chiare |
| **Temperatura** | -100 … +100 | Rende la foto più blu (negativo) o più calda/arancione (positivo) | +5…+15 per interni caldi; -5…-15 per ombre blu |
| **Tinta (verde/magenta)** | -100 … +100 | Corregge le dominanti verdi o magenta | Piccoli valori, ±5…±10 |

> La temperatura non è in Kelvin: è un valore **relativo**. Serve a correggere l'atmosfera, non a impostare i gradi esatti.

### 4.3 Toni

| Controllo | Intervallo | Cosa fa | Consiglio |
|---|---|---|---|
| **Luci** | -100 … +100 | Recupera o schiarisce le zone chiare | -10…-25 per cieli e finestre |
| **Ombre** | -100 … +100 | Apre o chiude le zone scure | +10…+25 per dettagli nei neri |
| **Bianchi** | -100 … +100 | Agisce sul punto più chiaro | -5…-15 se il bianco è bruciato |
| **Neri** | -100 … +100 | Agisce sul punto più scuro | -5…-15 per neri più profondi |
| **Contrasto (curva sigmoide)** | 0,00 … 1,00 | Aumenta la separazione tra luci e ombre | 0,20–0,35 naturale; 0,45+ per effetto deciso |

**Attenzione:** il contrasto predefinito è **0,35**, già presente. Se aumenti anche luci/ombre, il risultato può diventare troppo duro. Guarda sempre la foto alla dimensione finale.

### 4.4 Colore

| Controllo | Intervallo | Cosa fa | Consiglio |
|---|---|---|---|
| **Vivacità selettiva** | 0,00 … 1,00 | Rende più vivi i colori spenti senza esagerare con quelli già saturi | 0,20–0,45 |
| **Saturazione** | 0,00 … 2,00 | Aumenta o riduce tutti i colori | 0,95–1,10; 0 per bianco e nero |
| **Saturazione rossi** | -100 … +100 | Corregge rossi, arancioni e incarnati | -10…+10; attenzione alla pelle |
| **Saturazione verdi** | -100 … +100 | Corregge prati, foglie, vegetazione | +5…+15 per paesaggi |
| **Saturazione blu** | -100 … +100 | Corregge cielo e acqua | +5…+15 per paesaggi; -10 se il cielo è troppo carico |

**Regola per i ritratti:** saturazione sotto 1,00 e vivacità moderata. La pelle non deve diventare arancione o “plastica”.

### 4.5 Dettaglio e nitidezza

| Controllo | Intervallo | Cosa fa | Consiglio |
|---|---|---|---|
| **Chiarezza (micro-contrasto)** | 0,00 … 1,00 | Aumenta il contrasto locale e la sensazione di dettaglio | 0,05–0,20 ritratti; 0,20–0,35 paesaggi |
| **Dehaze (rimozione velo)** | 0,00 … 1,00 | Toglie la foschia e aumenta la trasparenza | 0,05–0,20; oltre 0,30 può scurire troppo |
| **Nitidezza (quantità)** | 0,00 … 5,00 | Quanto forte è la nitidezza | 0,8–1,3 ritratti; 1,2–1,8 paesaggi; 1,5–2,0 stampa |
| **Nitidezza (raggio)** | 0,50 … 4,00 | Spessore del dettaglio | 1,0–1,5 ritratti; 1,2–1,8 paesaggi |
| **Riduzione rumore luminanza** | 0 … 100 | Toglie il rumore chiaro/scuro (grana) | 0 per ISO bassi; 40–70 per ISO alti |
| **Riduzione rumore colore** | 0 … 100 | Toglie le macchie colorate | 0 per ISO bassi; 50–80 per ISO alti |

**Come funziona la nitidezza:** viene applicata solo alla luminanza, quindi non crea bordi colorati. Per questo puoi usare valori più alti rispetto ad altri programmi, ma non esagerare.

**Come funziona la riduzione rumore:** lavora separatamente su luminanza e colore. Protegge i bordi e lascia un piccolo residuo di grana per non rendere la pelle “di plastica”. La crominanza viene pulita a metà risoluzione: è più veloce e il risultato visivo è lo stesso.

### 4.6 RIMUOVI GRANA (AUTO ISO)

Questo è il pulsante **un clic** per le foto rumorose.

**Quando lo premi, imposta:**

- riduzione rumore luminanza **60**;
- riduzione rumore colore **70**;
- nitidezza quantità almeno **1,25**;
- nitidezza raggio **1,20**.

La forza della riduzione si adatta automaticamente all'ISO del RAW:

| ISO | Fattore applicato |
|---|---|
| fino a 400 | 0,60 (delicato) |
| 401–800 | 0,78 |
| 801–1600 | 0,92 |
| 1601–3200 | 1,08 |
| 3201–6400 | 1,22 |
| oltre 6400 | 1,35 (più forte) |

**Quando usarlo:** ISO 800+, interni, sera, concerti, sport, foto con ombre sollevate.

**Quando non usarlo:** ISO 100–400 con luce buona, still life puliti, foto in cui vuoi conservare la grana.

**Come annullarlo:** premi di nuovo il pulsante. Il programma ripristina i valori che avevi prima (quantità e raggio di nitidezza compresi). Il pulsante torna viola e la scritta torna **RIMUOVI GRANA (AUTO ISO)**.

> Se preferisci, puoi regolare a mano **Riduzione rumore luminanza** e **Riduzione rumore colore**. Il pulsante è solo una scorciatoia: non blocca i valori manuali.

### 4.7 Curva tonale e split toning

**Curva tonale:**

| Voce | Effetto |
|---|---|
| **Lineare** | Nessuna curva: massimo controllo naturale |
| **Media** | Contrasto leggero |
| **Forte** | Contrasto deciso |
| **Contrasto Alto** | Contrasto molto marcato |
| **Schiarisci** | Immagine più luminosa e aperta |
| **Scurisci** | Immagine più scura e densa |

**Split toning:**

- **Split toning ombre (intensità):** 0–100; colora le zone scure.
- **Colore ombre:** colore in formato esadecimale, per esempio `#2b4c7e` (blu).
- **Split toning luci (intensità):** 0–100; colora le zone chiare.
- **Colore luci:** per esempio `#e0b070` (caldo).

**Consiglio:** split toning a **5–15** è elegante; oltre 30 diventa un effetto stilizzato. Per un look cinema: ombre blu e luci calde, entrambe a 10–15.

### 4.8 Effetti

| Controllo | Intervallo | Cosa fa | Consiglio |
|---|---|---|---|
| **Vignettatura** | -100 … +100 | Negativo scurisce gli angoli; positivo li schiarisce | -10…-25 per concentrare l'attenzione |
| **Grana** | 0 … 100 | Aggiunge grana fotografica | 8–15 per bianco e nero o look pellicola |

La grana viene generata in modo casuale ma **ripetibile**: la stessa foto produce sempre lo stesso risultato.

### 4.9 Ripristina tutti i parametri di sviluppo

Riporta gli slider, la curva e lo split toning ai valori predefiniti. **Non** cancella il watermark, la destinazione, i nomi file o le credenziali cloud. Se il pulsante **RIMUOVI GRANA** era attivo, viene disattivato.

---

## 5. Scheda Tethering & Cloud

### 5.1 Sony Wi-Fi — Smart Remote Control

Il programma può comandare una Sony A7S (o modello compatibile) via Wi-Fi. La fotocamera **non invia da sola** le foto: è il programma a comandarla.

**Preparazione:**

1. Sulla fotocamera apri l'app **Smart Remote Control** (PlayMemories Camera Apps).
2. Collega il PC alla rete Wi-Fi creata dalla fotocamera: il nome è simile a `DIRECT-xxxx:ILCE-7S`.
3. Attendi che il PC abbia un indirizzo di rete (di solito `192.168.122.x`).
4. Nel programma premi **CONNETTI FOTOCAMERA**.
5. Premi **SCATTA E SCARICA** per scattare e trasferire la foto.
6. **DIAGNOSI** mostra informazioni utili se la connessione non funziona.

**Consigli:**

- Disattiva temporaneamente il firewall di Windows solo per la rete della fotocamera, se la connessione viene bloccata.
- Non usare contemporaneamente VPN o reti aziendali restrittive.
- Se la fotocamera si spegne, riconnetti la rete Wi-Fi e premi di nuovo **CONNETTI FOTOCAMERA**.
- La distanza ideale è di pochi metri, senza muri spessi.

### 5.2 Hot-folder (cartella monitorata)

È il modo più semplice per automatizzare l'arrivo delle foto.

1. **Cartella fotocamera:** la cartella da controllare (per esempio una cartella sincronizzata da Dropbox, Google Drive, Imaging Edge o una cartella di rete).
2. **Cartella output:** dove salvare le foto sviluppate.
3. Premi **AVVIA MONITORAGGIO CARTELLA**. Il pulsante diventa **DISATTIVA MONITORAGGIO**.

Quando arriva un file supportato, il programma aspetta che la scrittura sia finita (dimensione stabile), poi lo converte con le impostazioni correnti della scheda Batch. Ignora la cartella di output e i file già prodotti, quindi non entra in un ciclo infinito.

**Consiglio:** usa una cartella di appoggio dedicata solo all'arrivo delle foto. Non puntare il monitoraggio sulla cartella che contiene l'intero archivio: sarebbe inutile e lento.

### 5.3 Credenziali Cloud

**Telegram (operativo):**

- **Telegram Bot Token:** lo ottieni da `@BotFather` su Telegram.
- **Telegram Chat ID:** l'ID della chat o del canale che deve ricevere le foto.
- Attiva la casella **Telegram**.
- Il programma invia una foto alla volta al termine dell'elaborazione. Non invia cartelle né file non immagine.

**Dropbox (operativo):**

- **Dropbox Access Token:** crea un token con i permessi di scrittura nel tuo account Dropbox.
- Attiva la casella **Dropbox**.
- Il file viene caricato nella radice dell'account (o nella cartella consentita dal token), con rinomina automatica se esiste già un file con lo stesso nome.

**Canali non attivi:**

- **Google Drive (non attivo)**
- **Meta FB/IG (non attivo)**
- **SwissTransfer (non attivo)**

Questi campi sono predisposti, ma l'invio viene saltato senza errori. Non perdere tempo a configurarli in questa versione.

**Privacy:** i token sono credenziali sensibili. Non condividerli, non metterli in screenshot e non salvarli in un file di configurazione che poi condividi.

---

## 6. Scheda Log: messaggi ed errori

La scheda **Log** mostra in tempo reale:

- file avviati, completati, saltati o falliti;
- algoritmo di demosaic usato (AMaZE, AHD, PPG o LINEAR);
- numero di processi attivati;
- messaggi di tethering, cloud ed eventuali errori.

- **Svuota log:** cancella il contenuto visualizzato.
- **Salva log su file:** salva un file di testo utile per assistenza o per capire un errore.

**Consiglio:** se un file non viene convertito, salva il log e controlla la riga con **Errore**. Spesso il problema è un file corrotto, un percorso non accessibile o un formato non supportato.

---

## 7. Impostazioni consigliate per tipo di foto

### 7.1 Tabella rapida

| Tipo di foto | Lato max | Qualità | Formato | PIÙ LUMINOSA | Rimuovi grana | Nitidezza | Watermark |
|---|---:|---:|---|---|---|---|---|
| Web / social | 1920 | 90 | JPEG | Solo se scura | ISO 800+ | 1,2 / 1,2 | Sì, piccolo |
| Social alta qualità | 2048 | 90 | JPEG | Solo se scura | ISO 800+ | 1,2 / 1,2 | Sì |
| Stampa fine art | Originale | 95–100 | TIFF | No | ISO 1600+ | 1,6 / 1,8 | No |
| Archivio | Originale | 95 | JPEG | No | No | 0,8 / 1,5 | No |
| Ritratto | 3000 | 92 | JPEG | Sì, se scuro | ISO 800+ | 0,9 / 1,2 | Solo se richiesto |
| Paesaggio | 3000–3840 | 92 | JPEG | Solo se scuro | ISO 800+ | 1,5–1,8 / 1,6 | No |
| Notte / concerto | 1920–3000 | 92 | JPEG | No | Sì | 1,0 / 1,2 | No |
| Bianco e nero | 3000 | 92 | JPEG | No | ISO 1600+ | 1,5 / 1,5 | Facoltativo |
| Prova rapida | 1200 | 85 | JPEG | No | No | 1,0 / 1,5 | No |

### 7.2 Consigli per ISO

| ISO | Riduzione rumore | Note |
|---|---|---|
| 100–400 | 0 / 0 | Lascia il dettaglio naturale |
| 400–800 | 15–25 / 20–30 | Solo se vedi rumore nelle ombre |
| 800–1600 | 30–45 / 40–55 | Il pulsante AUTO è già adatto |
| 1600–3200 | 45–60 / 55–70 | AUTO consigliato |
| 3200–6400 | 60–70 / 70–80 | AUTO; controlla la pelle |
| Oltre 6400 | 70–80 / 80–90 | AUTO; valuta un formato più piccolo |

**Regola:** meglio un po' di grana che una pelle “liscia come plastica”. Se il risultato è troppo morbido, abbassa la riduzione luminanza di 10–15 punti.

### 7.3 Consigli per ritratti

- **Esposizione:** +0,2…+0,4 se la pelle è scura.
- **Luci:** -10…-15 per non bruciare il viso.
- **Ombre:** +10…+20 per aprire gli occhi.
- **Contrasto:** 0,20–0,30.
- **Vivacità:** 0,15–0,25.
- **Saturazione:** 0,95–1,00.
- **Chiarezza:** 0,05–0,10.
- **Nitidezza:** 0,8–1,0, raggio 1,2.
- **Riduzione rumore:** solo se serve; il preset **Ritratto** è un buon punto di partenza.

### 7.4 Consigli per paesaggi

- **Contrasto:** 0,30–0,45.
- **Vivacità:** 0,30–0,45.
- **Chiarezza:** 0,20–0,30.
- **Dehaze:** 0,10–0,20.
- **Verdi:** +8…+15.
- **Blu:** +5…+10, ma non esagerare con il cielo.
- **Nitidezza:** 1,5–1,8, raggio 1,6.

### 7.5 Consigli per notte e concerti

- Non alzare troppo l'esposizione: il rumore aumenta.
- Usa **RIMUOVI GRANA (AUTO ISO)**.
- Riduci il contrasto a 0,20–0,30 per non perdere dettaglio nelle ombre.
- Nitidezza 0,9–1,2, raggio 1,2.
- Se i colori sono troppo sporchi, alza la riduzione rumore colore a 75–85.
- Converti a 1920–3000 px: il rumore è meno visibile e il file è più gestibile.

---

## 8. Flussi di lavoro pronti all'uso

### 8.1 Web e social in 4 passi

1. Seleziona la cartella RAW.
2. Scegli **1920** px, **JPEG**, qualità **90**.
3. Attiva **PIÙ LUMINOSA** solo se le foto sono scure.
4. Avvia. Per le foto a ISO alto, attiva **RIMUOVI GRANA**.

### 8.2 Consegna al cliente

1. **3000** px, **JPEG**, qualità **95**.
2. **PIÙ LUMINOSA** attiva solo sulle foto sottoesposte.
3. **RIMUOVI GRANA** per ISO 800+.
4. Watermark solo se previsto dal contratto.
5. Controlla 5 foto campione prima di consegnare tutto.

### 8.3 Stampa fine art

1. **Originale**, **TIFF**, qualità **100**.
2. **PIÙ LUMINOSA** spenta.
3. Nitidezza **1,6**, raggio **1,8**.
4. **RIMUOVI GRANA** solo se necessario.
5. Nessun watermark.
6. Verifica la stampa con il laboratorio: il TIFF è senza perdita.

### 8.4 Archivio

1. **Originale**, **JPEG**, qualità **95**.
2. EXIF attivo.
3. Nessun watermark.
4. Nessuna riduzione rumore, salvo RAW molto rumorosi.
5. Conserva anche i RAW originali su un disco separato.

### 8.5 Bianco e nero

1. Preset **Bianco e Nero**.
2. Saturazione **0**.
3. Contrasto **0,40–0,50**.
4. Chiarezza **0,20–0,30**.
5. Grana **8–15**.
6. Nitidezza **1,3–1,6**.

### 8.6 Tethering in studio

1. Collega la Sony via Wi-Fi.
2. Apri **Tethering & Cloud**.
3. Scegli la cartella di arrivo e la cartella output.
4. Avvia il monitoraggio.
5. Scatta: il programma converte automaticamente.
6. Se necessario, attiva **Telegram** o **Dropbox** per l'invio immediato.

---

## 9. Domande frequenti e soluzione problemi

### Il programma è lento. Perché?

- La prima conversione è più lenta: il programma carica le librerie.
- **Originale** e **denoise** richiedono più tempo e RAM.
- Con RAW da 50–60 MP il numero di processi viene ridotto per non esaurire la memoria.
- Chiudi browser, giochi e altri programmi pesanti.
- Per il web usa **1920 px**: è molto più veloce e spesso sufficiente.
- Non convertire due volte la stessa cartella nella stessa destinazione.

### Un file dà errore. Cosa faccio?

1. Apri il **Log** e cerca la riga con **Errore**.
2. Verifica che il file si apra con un altro programma.
3. Prova a convertirlo da solo.
4. Se è corrotto, escludilo: il batch continuerà con gli altri.
5. Salva il log e segnala il problema con il nome del file e il messaggio.

### Perché alcuni file vengono saltati?

La politica **Se esiste** è impostata su **Salta** oppure il file non è un formato supportato. Controlla anche che la cartella di output non sia la stessa della sorgente.

### Perché il watermark è troppo grande o troppo piccolo?

La dimensione è in **pixel**. Per una foto 1920 px usa 14–18; per 3000 px usa 24–32; per 6000 px usa 40–60. Il logo viene ridimensionato al 15% del lato lungo.

### La foto è troppo chiara o troppo scura.

- Se **PIÙ LUMINOSA** è attiva, disattivala e regola manualmente **Esposizione**.
- Controlla **Luci** e **Ombre**.
- Premi **Ripristina tutti i parametri di sviluppo** e riparti.
- Se la foto è bruciata o nera, non c'è recupero: il RAW non contiene più informazione.

### La pelle è diventata “di plastica”.

Hai usato troppa riduzione rumore o troppa nitidezza. Abbassa **Riduzione rumore luminanza** di 10–20 punti e **Nitidezza** a 0,8–1,0. Per i ritratti meglio un po' di grana naturale.

### Il cielo è troppo saturo.

Abbassa **Saturazione blu** e **Vivacità**. Se il cielo è bruciato, usa **Luci** negativo e **Bianchi** negativo.

### La Sony non si connette.

- La fotocamera deve essere in **Smart Remote Control**.
- Il PC deve essere collegato alla rete Wi-Fi `DIRECT-xxxx:ILCE-7S`.
- L'indirizzo del PC deve essere `192.168.122.x`.
- Prova **DIAGNOSI**.
- Disattiva VPN e firewall per quella rete.
- Riavvia la fotocamera e riconnetti.

### Telegram non invia.

- Controlla **Bot Token** e **Chat ID**.
- Apri il bot su Telegram e premi **Start** almeno una volta.
- La casella **Telegram** deve essere attiva.
- Verifica la connessione Internet e che il token non sia scaduto.

### Dropbox non carica.

- Il token deve avere i permessi di scrittura.
- La casella **Dropbox** deve essere attiva.
- Token scaduti o revocati vanno rigenerati.

### Posso usare il programma su Mac?

No: è un'applicazione Windows 10/11.

### Il programma invia i miei dati?

No. Non c'è telemetria. L'unica connessione è quella che attivi tu: Sony Wi-Fi, Telegram o Dropbox. I token restano sul tuo computer.

### Dove sono i file convertiti?

Nella **Cartella output** scelta. Il percorso è mostrato anche nella barra di stato in basso. Il pulsante **Apri cartella output** la apre subito.

### Posso annullare un batch lungo?

Sì. Premi **ANNULLA**. I file già completati restano; quelli in corso vengono interrotti e i file parziali vengono rimossi.

### Perché il file JPEG è più pesante del solito?

Qualità 95–100 e subsampling 4:4:4 producono file grandi. Per il web usa qualità 85–90. Per la stampa è normale che il file sia grande.

---

## 10. Glossario semplice

| Termine | Significato |
|---|---|
| **RAW** | File grezzo della fotocamera: contiene molti più dati di un JPEG e permette correzioni migliori. |
| **JPEG** | Formato compresso, leggero e universale. Ottimo per web e condivisione. |
| **PNG** | Formato senza perdita, con supporto trasparenza. Utile per grafica, non per foto normali. |
| **TIFF** | Formato senza perdita, pesante, usato per stampa e archiviazione. |
| **WebP** | Formato moderno, leggero, per siti web. |
| **sRGB** | Spazio colore standard, compatibile con la maggior parte di schermi e servizi. |
| **EXIF** | Dati di scatto salvati nel file: data, fotocamera, ISO, tempi, GPS. |
| **ISO** | Sensibilità della fotocamera. ISO alto = più rumore. |
| **EV** | Unità di esposizione: +1 EV raddoppia la luce, -1 EV la dimezza. |
| **Bilanciamento del bianco** | Corregge la dominante di colore della luce. |
| **Luminanza** | Informazione di chiaro/scuro, separata dal colore. |
| **Crominanza** | Informazione di colore, separata dalla luminanza. |
| **Guided filter** | Filtro intelligente che toglie il rumore nelle zone piatte e protegge i bordi. |
| **Demosaic** | Ricostruzione del colore dai dati del sensore RAW. |
| **AMaZE / AHD / PPG** | Algoritmi di demosaic. AMaZE è il più avanzato; il programma ripiega automaticamente se non disponibile. |
| **Lanczos** | Metodo di ridimensionamento di alta qualità. |
| **Vignettatura** | Scurimento o schiarimento degli angoli. |
| **Split toning** | Colorazione separata di ombre e luci. |
| **Watermark** | Firma o logo sovrapposto alla foto. |
| **Hot-folder** | Cartella controllata automaticamente: quando arriva un file, viene convertito. |
| **Tethering** | Controllo della fotocamera dal computer. |

---

## 11. Scheda riassuntiva da stampare

### Web / social

- Lato max: **1920**
- Qualità: **90**
- Formato: **JPEG**
- PIÙ LUMINOSA: **solo se scura**
- Rimuovi grana: **ISO 800+**
- Nitidezza: **1,2 / 1,2**
- Watermark: **sì, 14–18 px**

### Consegna cliente

- Lato max: **3000**
- Qualità: **95**
- Formato: **JPEG**
- PIÙ LUMINOSA: **solo se scura**
- Rimuovi grana: **ISO 800+**
- Nitidezza: **1,2 / 1,3**
- Watermark: **secondo accordo**

### Stampa fine art

- Lato max: **Originale**
- Qualità: **100**
- Formato: **TIFF**
- PIÙ LUMINOSA: **no**
- Rimuovi grana: **solo se serve**
- Nitidezza: **1,6 / 1,8**
- Watermark: **no**

### Archivio

- Lato max: **Originale**
- Qualità: **95**
- Formato: **JPEG**
- PIÙ LUMINOSA: **no**
- Rimuovi grana: **no**
- Nitidezza: **0,8 / 1,5**
- EXIF: **sì**
- Watermark: **no**

### Notte / ISO alto

- Lato max: **1920–3000**
- Qualità: **92**
- Formato: **JPEG**
- PIÙ LUMINOSA: **no**
- Rimuovi grana: **sì**
- Nitidezza: **1,0 / 1,2**
- Watermark: **no**

---

**Franchetti Raw Converter Pro v2.54.0** — Guida completa.
Per assistenza, salva il **Log** e descrivi il passaggio che ha causato il problema.
