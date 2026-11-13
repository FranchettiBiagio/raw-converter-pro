# Codici di uscita dell'installer — Franchetti Raw Converter Pro

Documentazione dei valori restituiti da `Franchetti_Raw_Converter_Setup_*.exe`
(installer Inno Setup 7). Gli stessi valori sono dichiarati in Partner Center
alla voce **Installer handling**.

## Codici restituiti dal setup

| Codice | Significato |
|---|---|
| `0` | Installazione completata con successo |
| `1` | Setup non riuscito ad inizializzarsi |
| `2` | Installazione annullata dall'utente prima dell'inizio |
| `3` | Errore fatale durante la preparazione dell'installazione |
| `4` | Errore fatale durante l'installazione |
| `5` | Installazione annullata dall'utente durante la copia dei file |
| `6` | Processo terminato dal debugger (non avviene in produzione) |
| `7` | La fase di preparazione ha stabilito che non è possibile procedere |
| `8` | Come `7`, ma serve un riavvio del sistema per correggere il problema |

Fonte: documentazione ufficiale Inno Setup, sezione *Setup Exit Codes* —
<https://jrsoftware.org/ishelp/topic_setupexitcodes.htm>

## Come si comporta questo installer

L'installer è **silenzioso** e non richiede alcuna interazione:

```
Franchetti_Raw_Converter_Setup_2.58.1.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
```

- non mostra interfaccia;
- non richiede privilegi di amministratore (installazione per-utente);
- non richiede riavvio;
- non scarica nulla: è un installer offline completo.

In condizioni normali restituisce **`0`**. Restituisce **`2`** solo se
l'utente annulla, cosa che con i parametri silenziosi non avviene.

## Mappatura dichiarata in Partner Center

| Scenario | Codice |
|---|---|
| Installazione annullata dall'utente | `1` |
| L'applicazione esiste già | `183` |
| Installazione già in corso | `215` |
| Fallimento della rete | `1231` |
| Pacchetto rifiutato durante l'installazione | `5` |
| Installazione riuscita | `0` |
| Altri guasti | `2` |

> Nota: i valori non standard (183, 215, 1231) sono quelli già accettati nella
> sottomissione precedente e vengono mantenuti per coerenza. L'unico codice che
> l'installer restituisce realmente è `0`, più `2`/`5` in caso di annullamento.
