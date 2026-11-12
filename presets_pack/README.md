# Pack preset ufficiale

Questa cartella contiene preset nel formato nativo `.frcpreset` e un
`manifest.json` con il checksum SHA-256 di ogni file.

- `Cinema caldo` — ombre fredde, luci dorate, contrasto deciso.
- `Paesaggio freddo` — bianco più freddo, verdi puliti, blu profondi.
- `Ritratto soft` — pelle morbida, toni bassi, contrasto contenuto.

## Installazione

I preset sono solo dati: non contengono codice e non vengono mai eseguiti.

1. Scarica il pacchetto o questa cartella.
2. In Franchetti Raw Converter Pro apri **AVANZATE → Importa**.
3. Seleziona `manifest.json` (o il file `.zip` del pacchetto).
4. L'app verifica il checksum SHA-256 e importa i preset.

I preset vengono salvati nella cartella dati dell'utente:

- Windows: `%APPDATA%\FranchettiRawConverterPro\presets`
- Linux: `~/.local/share/FranchettiRawConverterPro/presets`
- macOS: `~/Library/Application Support/FranchettiRawConverterPro/presets`

## Sicurezza

- Un preset contiene solo parametri di sviluppo e, facoltativamente, output.
- Non può contenere percorsi, cartelle, credenziali cloud, FTP o copyright.
- Se un checksum non corrisponde, il file viene rifiutato.
- Nessun download automatico: l'importazione è sempre manuale.

## Formato

```json
{
  "tipo": "franchetti-raw-preset",
  "versione": 1,
  "nome": "Cinema caldo",
  "autore": "Franchetti",
  "descrizione": "Look cinematografico caldo.",
  "tag": ["cinema", "colore"],
  "look": { "contrasto": 0.42 },
  "output": { "max_dim": 3000, "qualita_jpeg": 92, "formato": "JPEG" }
}
```
