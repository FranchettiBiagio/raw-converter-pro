# Deploy del sito — Franchetti Raw Converter Pro

## Stato: pubblicato (16/11/2026) — revisione grafica 2.58.1

| | |
|---|---|
| Repository | `github.com/FranchettiBiagio/franchetti-raw-converter-site` (pubblico) |
| Sito online | https://franchettibiagio.github.io/franchetti-raw-converter-site/ |
| Verifica | HTTP 200, 0 errori in console, 0 richieste esterne, 14 immagini caricate |
| Sorgente locale | `C:\FranchettiRawConverterPro\_publish` (repo git separato dal progetto) |
| Backup distribuibile | `dist\franchetti-site.zip` (8,9 MB, 26 file) |

Il repository contiene **solo** il sito: `store_assets`, i documenti di
certificazione e il codice dell'applicazione restano nel repository privato del
progetto.

## Struttura della pagina

| Sezione | Contenuto |
|---|---|
| `hero` | promessa, versione, tre azioni, micro-dati (27 RAW / 73 parametri / 4 uscite) |
| `trust` | originali in sola lettura, offline, scrittura atomica, prestazioni adattive |
| `#confronti` | tre confronti prima/dopo con maniglia trascinabile (RAW notturno, paesaggio, bianco e nero) + ritagli 100% |
| `#motore` | pipeline in 10 fasi, grafico misurato della protezione luci, statistiche |
| `#come` | quattro passaggi del flusso di lavoro |
| `#funzioni` | otto schede: formati, batch, Smart Batch, preset, LUT, firma, tethering, output |
| `#novita` | preset `.frcpreset`, XMP beta, LUT 3D, pacchetti con checksum, tempi Veloce |
| `#tethering` | FTP 2121 / hot folder / Sony Wi-Fi → sviluppo → firma → galleria |
| `#galleria` | tre schermate reali dell'applicazione |
| `band` | impegno sugli originali |
| `#lut` | griglia reale di 16 rese, 12 famiglie, download LUT + pack preset |
| `#compatibilita` | formati di ingresso/uscita, sistema, limiti dichiarati |
| `#faq` | nove domande, incluse LUT/preset separati e avviso SmartScreen |
| `#scarica` | installer, byte esatti, SHA-256, comando `certutil` |

## Aggiornare il sito

Nella cartella `_publish`:

```powershell
git add -A
git commit -m "Aggiornamento contenuti sito"
git push
```

GitHub Pages ricostruisce in 30–60 secondi. Non serve toccare il DNS.

Pacchetto pronto: `dist\franchetti-site.zip` (8,9 MB, 26 file, nessuna cartella
di primo livello: il contenuto va estratto nella radice del sito).

## Contenuto

```
index.html               pagina unica, italiana
styles.css               foglio di stile completo (responsive, print, reduced-motion)
app.js                   barra allo scroll, confronti trascinabili, schede accessibili,
                         comparsa progressiva
favicon.png              64×64
assets/
  hero.jpg               2400×1600  (Unsplash, licenza Unsplash)
  band.jpg               2400×1600  (Unsplash, licenza Unsplash)
  og-image.jpg           1200×630   (immagine di condivisione: logo, titolo, etichette)
  logo.png               256×256    (icona dell'app)
  ui-batch.jpg          1600×900    (schermata reale dell'app)
  ui-anteprima.jpg      1600×900    (schermata reale dell'app)
  ui-preset.jpg         1600×900    (schermata reale dell'app)
  ba-raw-before.jpg     1500×1000   (output reale: decodifica neutra)
  ba-raw-after.jpg      1500×1000   (output reale: preset + Smart Batch)
  ba-paesaggio-*.jpg    1500×1000   (output reale: preset Paesaggio freddo)
  ba-bianconero-*.jpg   1500×1000   (output reale: preset Bianco e Nero)
  noise-before.jpg       760×500    (ritaglio 100% prima)
  noise-after.jpg        760×500    (ritaglio 100% dopo, denoise reale)
  curva-luci.png        1100×620    (grafico misurato con la funzione del motore)
  luts-grid.jpg         1600×1200   (griglia LUT calcolata con interpolazione trilineare)
  card-paesaggio.jpg     960×540    (Unsplash, riserva)
  card-macro.jpg         960×640    (Unsplash, riserva)
  card-architettura.jpg  960×640    (Unsplash, riserva)
downloads/
  Franchetti_Arts_LUTs.zip      108 .cube + README + licenza, 4.535.997 byte
  Franchetti_Preset_Pack.zip    3 preset + manifest + README, 3.349 byte
```

Gli asset `ba-*` e `curva-luci.png` sono prodotti dal motore dell'applicazione,
non ritoccati: il sorgente RAW è uno scatto di prova Sony da 33 MP a ISO 2000.

## Anteprima di condivisione

In `<head>` sono presenti `og:image` e `twitter:image` con indirizzo **assoluto**
verso `assets/og-image.jpg` (1200×630, 126 KB): è l'immagine che WhatsApp,
Telegram, Facebook e LinkedIn mostrano quando si incolla il link. I campi
`og:url` e `og:image` contengono l'host di pubblicazione: **vanno aggiornati in
blocco** se il sito passa a un dominio proprio (`raw.franchettitv.it`).

Le anteprime vengono messe in cache dai social: dopo una modifica può servire
un nuovo link con parametro (`?v=2`) per forzare la rilettura. Per ripristinare
la cache di WhatsApp si condivide il link con una parte diversa dopo la barra
(`/` → `/?v=2`).

## Pubblicazione

1. Estrai lo ZIP in una cartella vuota.
2. Carica **tutto il contenuto** nella radice del sito (non la cartella che lo
   contiene), sovrascrivendo la versione precedente.
3. Apri l'indirizzo pubblico e verifica:
   - la home si apre senza errori in console;
   - il pulsante «Scarica l'installer» porta a
     `https://www.franchettitv.it/downloads/Franchetti_Raw_Converter_Setup_v2.58.1.exe`;
   - l'hash mostrato nella sezione Download corrisponde al file servito;
   - le tre schede dei confronti cambiano immagine e la maniglia si trascina;
   - i due ZIP in `downloads/` rispondono 200 e hanno le dimensioni dichiarate
     (4,3 MB LUT, 3,3 KB preset);
   - su telefono (375 px e 320 px) non compare scorrimento orizzontale.
4. In Partner Center, nel campo **Sito web** della scheda dello Store, usa questo
   indirizzo. È lo stesso dominio da cui viene servito l'installer.

## Download separati

| File | Contenuto | Byte | SHA-256 |
|---|---|---|---|
| `Franchetti_Arts_LUTs.zip` | 108 `.cube` + `README.txt` + `LICENZA.txt` | 4.535.997 | `56AB9A8E77CA87494387CC40AA2BB1289BC7C686BD15DC00F653E783A7E3D604` |
| `Franchetti_Preset_Pack.zip` | 3 `.frcpreset` + `manifest.json` + `README.md` | 3.349 | `D4DA327B8FA8948EC3C4E2BA2AE2CAC6DE8059F979BC756CC31FDB352F49D3A8` |

Il pack preset va rigenerato solo se cambia uno dei `.frcpreset`: gli hash in
`manifest.json` devono corrispondere ai file al momento della compressione.

## Contenuti: regole rispettate

- **Nessun riferimento a GitHub nel testo visibile**, né link alla piattaforma:
  gli unici link esterni sono il download sul dominio dell'autore e la posta.
  I meta `og:url` / `og:image` usano l'indirizzo assoluto di pubblicazione perché
  i social lo richiedono (senza, l'anteprima non compare).
- **Nessun logo o marchio di terzi**: le uniche immagini sono fotografie Unsplash
  (licenza Unsplash) e schermate reali del programma.
- **Nessuna promessa non verificata**: niente «certificato», niente «firmato»,
  niente tempi di conversione inventati; i numeri del profilo Veloce sono quelli
  misurati in `RELEASE_NOTES.md`.
- **Crediti fotografici** nel footer: licenza Unsplash per le foto di scena,
  uso non pubblicitario di marchi.

## Manutenzione a ogni nuova versione

Aggiorna in `index.html`:

| Punto | Cosa cambiare |
|---|---|
| `<title>` e `og:title` | numero di versione |
| hero, eyebrow | `Versione X.Y.Z` |
| link di download (2 punti) | nome del file `.exe` |
| sezione Download | byte esatti e hash SHA-256 |
| sezione Novità | data e contenuto tratto da `RELEASE_NOTES.md` |

Verifica l'hash con:

```powershell
(Get-FileHash .\Franchetti_Raw_Converter_Setup_X.Y.Z.exe -Algorithm SHA256).Hash
```

## Dominio proprio (consigliato per la scheda Store)

L'indirizzo `franchettibiagio.github.io/...` funziona, ma il nome dell'host
compare nella barra degli indirizzi. La pagina non lo cita mai; se si vuole un
indirizzo coerente con il marchio, si può puntare un sottodominio di
`franchettitv.it` a GitHub Pages, senza toccare il sito esistente su `www`.

1. Nel pannello DNS di `franchettitv.it` creare un record:

   | Tipo | Nome | Valore | TTL |
   |---|---|---|---|
   | CNAME | `raw` | `franchettibiagio.github.io` | automatico |

2. Solo dopo che il record risulta attivo, aggiungere al repository un file
   `CNAME` con una riga:

   ```
   raw.franchettitv.it
   ```

3. In **Settings → Pages** impostare *Custom domain* = `raw.franchettitv.it` e
   attendere il certificato (pochi minuti); poi attivare *Enforce HTTPS*.

4. Nel campo **Sito web** di Partner Center usare `https://raw.franchettitv.it/`.

Non aggiungere il file `CNAME` prima del record DNS: Pages inizierebbe a
reindirizzare anche l'indirizzo `github.io` verso un dominio non ancora
risolvibile, e il sito risulterebbe irraggiungibile.

## Nota sul server (facoltativo)

Il file viene servito con `Content-Type: application/x-msdos-program`. Funziona,
ma per uniformità si può forzare il tipo generico nella configurazione di nginx:

```nginx
location /downloads/ {
    default_type application/octet-stream;
}
```

Il download è già raggiungibile in HTTP Range (`Accept-Ranges: bytes`), quindi
riprende e non richiede configurazioni aggiuntive.
