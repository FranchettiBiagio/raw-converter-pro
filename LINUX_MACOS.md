# Linux e macOS (sperimentale)

Franchetti Raw Converter Pro è lo stesso programma su Windows, Linux e macOS.
Su Windows esiste un pacchetto pronto; su Linux e macOS si parte dal codice
sorgente. Sul sito c'è un archivio per Linux e uno per macOS con avvio
automatico: il programma è lo stesso, cambia il modo di avviarlo.

> **Stato reale:** la versione Linux è stata provata su Linux Mint 22.3 in
> macchina virtuale (2 vCPU, 8 GB di RAM). macOS non è mai stato provato.
> Considera entrambe **sperimentali**: nessuna garanzia che funzionino su ogni
> distribuzione o versione.

---

## Cosa serve

| Voce | Richiesta |
| --- | --- |
| Python | **3.11 o 3.12** (consigliate). Con 3.14 o superiore il batch può comportarsi male: l'app avvisa in build |
| Tk | la libreria grafica di Python (`python3-tk`) |
| Spazio su disco | circa 1 GB tra dipendenze e build |
| RAM | 2 GB minimo, 8 GB consigliati |
| Sistema | Linux x86_64; macOS Intel o Apple Silicon |

Gli originali non vengono mai modificati, come su Windows.

---

## Linux: avvio in cinque comandi

```bash
git clone https://github.com/FranchettiBiagio/raw-converter-pro.git
cd raw-converter-pro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Se manca Tk, il programma non parte e lo dice. Installalo così:

| Distribuzione | Comando |
| --- | --- |
| Debian, Ubuntu, Mint | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |
| Arch, Manjaro | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-tk` |

Per uscire dall'ambiente: `deactivate`.

---

## macOS: avvio in cinque comandi

Sul sito è disponibile anche un pacchetto con `Avvia Franchetti Raw
Converter.command`: doppio clic, prepara l'ambiente al primo avvio e apre il
programma. Se preferisci i comandi a mano, valgono quelli qui sotto.

Serve una Python con Tk. Va bene quella di [python.org](https://www.python.org/downloads/)
(include Tk); con Homebrew aggiungi il pacchetto Tk della stessa versione:

```bash
brew install python-tk@3.12
```

Poi, nel Terminale:

```bash
git clone https://github.com/FranchettiBiagio/raw-converter-pro.git
cd raw-converter-pro
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Se macOS blocca l'app compilata

Un programma compilato senza firma Apple viene fermato al primo avvio. Tre
modi, dal più semplice:

1. clic destro sul programma → **Apri** → **Apri**;
2. **Impostazioni di Sistema → Privacy e Sicurezza** → in fondo, **Apri comunque**;
3. da Terminale, sulla cartella che contiene il programma:
   `xattr -dr com.apple.quarantine "/percorso/della/cartella"`

L'avvio dalla sorgente (`python3 main.py`) non ha questo problema.

---

## Compilare l'eseguibile

```bash
python3 build_exe.py
```

- Su Linux il risultato è la cartella **`dist/FranchettiRawConverterPro/`**:
  va tenuta tutta, l'eseguibile da solo non parte. Non viene più estratto in
  `/tmp` a ogni avvio.
- Su macOS il risultato è l'app **`dist/FranchettiRawConverterPro.app`**: si
  apre con doppio clic. Anche lì la build è `--onedir`, dentro il bundle, così
  non viene scompattata in una cartella temporanea a ogni avvio.

Variabili utili:

| Variabile | Effetto |
| --- | --- |
| `FRC_ONEFILE=1` | torna al pacchetto singolo (sconsigliato: si ri-estrae in `/tmp`) |
| `FRC_THREADS=1` | forza il batch con i thread invece dei processi |

Versione del file e manifest restano opzioni Windows: su Linux e macOS la build
le salta e lo scrive.

### Distribuire la .app

```bash
ditto -c -k --sequesterRsrc --keepParent \
  "dist/FranchettiRawConverterPro.app" FranchettiRawConverterPro-macOS.zip
```

Non usare il compressore del Finder né `zip -r`: rompono i link interni del
bundle e l'app non parte più. Lo ZIP va caricato così com'è, senza rinominare
niente dentro.

### Icona macOS

PyInstaller su macOS vuole un file `.icns`. Partendo da un PNG quadrato da
512 o 1024 px (`icona.png` va bene):

```bash
mkdir -p icon.iconset
for s in 16 32 128 256 512; do
  sips -z $s $s icona.png --out icon.iconset/icon_${s}x${s}.png
  sips -z $((s*2)) $((s*2)) icona.png --out icon.iconset/icon_${s}x${s}@2x.png
done
iconutil -c icns icon.iconset -o icon.icns
rm -rf icon.iconset
```

Metti `icon.icns` nella cartella del progetto e rilancia la build: lo script lo
usa da solo.

### Firma e notarizzazione (facoltativa)

Senza firma Apple l'app funziona, ma al primo avvio va aperta con **clic destro →
Apri**. Per togliere l'avviso servono un account Apple Developer (99 $ l'anno) e
qualche comando in più:

```bash
codesign --deep --force --options runtime \
  --sign "Developer ID Application: Nome Cognome (TEAMID)" \
  "dist/FranchettiRawConverterPro.app"
xcrun notarytool submit FranchettiRawConverterPro-macOS.zip --wait \
  --apple-id ... --team-id ... --password ...
xcrun stapler staple "dist/FranchettiRawConverterPro.app"
```

Senza questi passaggi l'app resta perfettamente usabile: cambia solo il primo
avvio.

---

## Dove sono log e diagnosi

Il log non è sul Desktop: sta nella cartella dati dell'utente.

| Sistema | Percorso |
| --- | --- |
| Linux | `~/.local/share/FranchettiRawConverterPro/franchetti_log.txt` |
| macOS | `~/Library/Application Support/FranchettiRawConverterPro/franchetti_log.txt` |

Su Linux c'è anche uno script che misura memoria e processi durante l'avvio:

```bash
bash tools/diagnosi_linux.sh
```

Scrive un report in `~/diagnosi-frc.txt`.

---

## Cosa non c'è (e non va dato per scontato)

- nessun pacchetto `.deb`, `.rpm`, `.AppImage` o `.dmg`;
- nessuna firma o notarizzazione Apple: l'app compilata va aperta come sopra;
- icone del bundle solo se crei `icon.icns` prima della build;
- Sony Wi-Fi, server FTP e tethering non sono stati provati su Linux o macOS;
- nessun aggiornamento automatico.

Sul sito ci sono due archivi: quello per macOS con avvio assistito e quello per
Linux con il sorgente. Nessuno dei due è un binario compilato.

---

## Se qualcosa non funziona

Apri una segnalazione su
[GitHub Issues](https://github.com/FranchettiBiagio/raw-converter-pro/issues)
con:

1. distribuzione e versione (per esempio «Linux Mint 22.3» o «macOS 15.2, M2»);
2. `python3 --version`;
3. cosa hai fatto prima dell'errore;
4. il file `franchetti_log.txt` e, su Linux, `~/diagnosi-frc.txt`.

Con queste quattro cose il problema si riproduce quasi sempre.
