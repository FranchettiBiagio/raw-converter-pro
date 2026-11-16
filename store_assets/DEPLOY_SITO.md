# Deploy del sito — Franchetti Raw Converter Pro

## Stato: pubblicato (16/11/2026)

| | |
|---|---|
| Repository | `github.com/FranchettiBiagio/franchetti-raw-converter-site` (pubblico) |
| Sito online | https://franchettibiagio.github.io/franchetti-raw-converter-site/ |
| Verifica | HTTP 200, 22.212 byte, 0 errori in console, 0 richieste esterne, immagini tutte caricate |
| Sorgente locale | `C:\FranchettiRawConverterPro\_publish` (repo git separato dal progetto) |
| Backup distribuibile | `dist\franchetti-site.zip` (2,03 MB, 13 file) |

Il repository contiene **solo** il sito: `store_assets`, i documenti di
certificazione e il codice dell'applicazione restano nel repository privato del
progetto.

## Aggiornare il sito

Nella cartella `_publish`:

```powershell
git add -A
git commit -m "Aggiornamento contenuti sito"
git push
```

GitHub Pages ricostruisce in 30–60 secondi. Non serve toccare il DNS.

Pacchetto pronto: `dist\franchetti-site.zip` (2,03 MB, 13 file, nessuna cartella
di primo livello: il contenuto va estratto nella radice del sito).

## Contenuto

```
index.html               pagina unica, italiana
styles.css               foglio di stile completo (responsive, print, reduced-motion)
app.js                   ombra della barra allo scroll + comparsa progressiva
favicon.png              64×64
assets/
  hero.jpg               2400×1600  (CC0)
  band.jpg               2400×1600  (CC0)
  card-paesaggio.jpg      960×540   (CC0)
  card-macro.jpg          960×640   (CC0)
  card-architettura.jpg   960×640   (CC0)
  logo.png               256×256    (icona dell'app)
  ui-batch.jpg          1600×900    (schermata reale dell'app)
  ui-anteprima.jpg      1600×900    (schermata reale dell'app)
  ui-preset.jpg         1600×900    (schermata reale dell'app)
```

## Pubblicazione

1. Estrai lo ZIP in una cartella vuota.
2. Carica **tutto il contenuto** nella radice del sito (non la cartella che lo
   contiene), sovrascrivendo la versione precedente.
3. Apri l'indirizzo pubblico e verifica:
   - la home si apre senza errori in console;
   - il pulsante «Scarica l'installer» porta a
     `https://www.franchettitv.it/downloads/Franchetti_Raw_Converter_Setup_v2.58.1.exe`;
   - l'hash mostrato nella sezione Download corrisponde al file servito;
   - su telefono (375 px) non compare scorrimento orizzontale.
4. In Partner Center, nel campo **Sito web** della scheda dello Store, usa questo
   indirizzo. È lo stesso dominio da cui viene servito l'installer.

## Contenuti: regole rispettate

- **Nessun riferimento a GitHub**, né nel testo né nei link: l'unico link esterno
  è il download sul dominio dell'autore e l'indirizzo di posta.
- **Nessun logo o marchio di terzi**: le uniche immagini sono fotografie CC0 e
  schermate reali del programma.
- **Nessuna promessa non verificata**: niente «certificato», niente «firmato»,
  niente tempi di conversione inventati; i numeri del profilo Veloce sono quelli
  misurati in `RELEASE_NOTES.md`.
- **Crediti fotografici** nel footer: CC0 / pubblico dominio, uso non
  pubblicitario di marchi.

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
