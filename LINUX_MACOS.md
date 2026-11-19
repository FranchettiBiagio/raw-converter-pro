# Linux e macOS (sperimentale)

Franchetti Raw Converter Pro è lo stesso programma su Windows, Linux e macOS.
Su Windows esiste un pacchetto pronto; su Linux e macOS **non c'è un file da
scaricare e avviare**: si parte dal codice sorgente e servono cinque minuti.

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
- Su macOS il risultato è **`dist/FranchettiRawConverterPro`**, un singolo
  eseguibile: non viene creato un bundle `.app` con icona. Per distribuirlo
  servirebbe firma e notarizzazione Apple (vedi sotto).

Variabili utili:

| Variabile | Effetto |
| --- | --- |
| `FRC_ONEFILE=1` | torna al pacchetto singolo (sconsigliato: si ri-estrae in `/tmp`) |
| `FRC_THREADS=1` | forza il batch con i thread invece dei processi |

Icona, versione del file e manifest sono opzioni Windows: su Linux e macOS la
build le salta e lo scrive.

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
- icona e proprietà del file non impostate;
- Sony Wi-Fi, server FTP e tethering non sono stati provati su Linux o macOS;
- nessun aggiornamento automatico.

Sul sito la pagina di download resta quella Windows: è l'unica versione che si
scarica e si avvia subito.

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
