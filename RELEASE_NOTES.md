# Release Notes v2.56.0

**Franchetti Raw Converter Pro** — Release v2.56.0  
**Data**: 1 Novembre 2026  
**Build**: 2.56.0.0

---

## Il ponte RAW diventa più fedele

La 2.56.0 interviene sul punto di partenza di tutta la pipeline: la lettura del
file RAW. Il nuovo ponte usa **rawpy/LibRaw** per leggere il sensore e applicare
la calibrazione della fotocamera prima di passare l'immagine alla pipeline
fotografica.

L'obiettivo è una resa più equilibrata e vicina a quella del software del
produttore, senza tabelle manuali per marca.

### Cosa cambia

- **WB camera**: il bilanciamento del bianco viene letto dai metadati del RAW.
- **Matrice colore camera**: LibRaw applica il profilo colore della fotocamera
  e converte in sRGB.
- **AHD per i sensori Bayer** (qualità 3): Sony, Canon, Nikon, Panasonic,
  OM System, Leica e gli altri marchi supportati.
- **AAHD 12 per Fujifilm X-Trans**: il percorso ottimizzato per i sensori
  X-Trans viene selezionato automaticamente sui file `.raf`.
- **Uscita BGR**: l'array decodificato è pronto per OpenCV; la pipeline interna
  lo riallinea a RGB per PIL/scikit-image senza invertire i canali.
- **Rilevamento Fujifilm** anche per DNG/TIFF tramite intestazione `FUJIFILM`.

---

## Test con RAW reali

| Fotocamera / file | Demosaic | Risultato |
|---|---|---|
| Sony ARW (4 file) | AHD (3) | 4/4 OK, colori e canali corretti |
| Fujifilm X-T30 III `DSCF0133.RAF` | AAHD (12) | 6264×4176, decoding ~2,8 s |
| Canon EOS R5 `.CR3` | AHD (3) | 8191×5463, decoding ~1,65 s |
| Nikon Z6 `.NEF` | AHD (3) | 4548×3030, decoding ~0,73 s |

Batch misto **4 Sony + 1 Fujifilm** a 1200 px: **5/5 OK** in circa **15,3 s**.

Output a 3000 px:
- Sony: 3000×2001, JPEG ~0,7 MB, ~8,5 s per foto.
- Fujifilm: 3000×2000, JPEG ~1,6 MB, ~9,2 s per foto.

Test del pacchetto finale:
- EXE portable, conversione Fujifilm a risoluzione originale: **OK**.
- EXE portable, batch Sony + Fujifilm: **2/2 OK**, nessun errore, report corretto.

---

## Nota tecnica: `use_camera_matrix`

Il codice tenta esplicitamente `use_camera_matrix=True`. La versione installata
di **rawpy 0.27.1 non espone questo parametro Python**; in quel caso LibRaw usa
il profilo camera predefinito, che con **WB camera attivo** è la matrice della
fotocamera. Il Log indica quando viene usato questo fallback.

Non è un errore di conversione: il risultato viene comunque calibrato con il
profilo della fotocamera. Se in futuro rawpy esporrà il flag, il codice lo userà
automaticamente.

---

## Compatibilità

- **Windows 10/11 x64**, portable o installer.
- I file originali non vengono mai modificati.
- L'EXIF viene preservato nei formati supportati.
- Le configurazioni e il flusso di lavoro delle versioni precedenti restano validi.
- Il profilo predefinito resta **3000 px, JPEG 90, denoise automatico**.

---

## Download

- **Portable**: [FranchettiRawConverterPro.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/FranchettiRawConverterPro.exe)
- **Installer**: [Franchetti_Raw_Converter_Setup_v2.56.0.exe](https://github.com/FranchettiBiagio/raw-converter-pro/releases/latest/download/Franchetti_Raw_Converter_Setup_v2.56.0.exe)
- **Release**: [v2.56.0](https://github.com/FranchettiBiagio/raw-converter-pro/releases/tag/v2.56.0)

## Integrità

```text
7B914EDE660293E364D15ACD0923A3B3A65EFDDCD7FF89D3660B42CF69EDA39C  FranchettiRawConverterPro.exe
AB45E001AB738006E2D9D02F306388DC97375E6187619B5D2716A91C17D60A52  Franchetti_Raw_Converter_Setup_v2.56.0.exe
```

Il file `SHA256SUMS.txt` nel repository contiene anche gli hash delle guide.

Per assistenza, salva il **Log** e descrivi il passaggio che ha causato il problema.
