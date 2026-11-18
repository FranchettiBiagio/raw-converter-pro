#!/usr/bin/env bash
# Diagnosi dell'avvio su Linux.
#
# Avvia l'applicazione, campiona ogni 3 secondi memoria, numero di copie
# del processo e processi piu' pesanti, poi chiude tutto e scrive un report.
#
# Uso:
#   bash tools/diagnosi_linux.sh
#   bash tools/diagnosi_linux.sh /percorso/FranchettiRawConverterPro 120
#
# Il report finisce in ~/diagnosi-frc.txt: allegalo a una segnalazione.

set -u

APP="${1:-dist/FranchettiRawConverterPro/FranchettiRawConverterPro}"
DURATA="${2:-180}"
REPORT="$HOME/diagnosi-frc.txt"
TEMP_LOG="$(mktemp -t frc-avvio-XXXXXX.log)"
NOME="$(basename "$APP")"
MASSIMO_COPIE=0

if [ ! -x "$APP" ]; then
    echo "Non trovo un eseguibile avviabile in: $APP"
    echo "Uso: bash tools/diagnosi_linux.sh [eseguibile] [secondi]"
    exit 1
fi

{
    echo "Diagnosi Franchetti Raw Converter Pro"
    echo "Data: $(date)"
    echo "Eseguibile: $APP"
    echo "Processori: $(nproc 2>/dev/null || echo '?')"
    echo "Memoria:"
    free -m
    echo "Python di sistema: $(python3 --version 2>&1 || echo 'assente')"
    echo "=================================================="
} >"$REPORT"

echo "Avvio dell'applicazione: non chiuderla, la diagnosi dura $DURATA secondi."
"$APP" >"$TEMP_LOG" 2>&1 &
PID=$!
sleep 3

for ((istante = 3; istante <= DURATA; istante += 3)); do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "[$istante s] il processo principale e' terminato" >>"$REPORT"
        break
    fi
    COPIE=$(pgrep -fc "$NOME" 2>/dev/null) || true
    COPIE=${COPIE:-0}
    if [ "$COPIE" -gt "$MASSIMO_COPIE" ]; then
        MASSIMO_COPIE=$COPIE
    fi
    {
        echo "--- $istante s ---"
        free -m | head -2
        echo "copie di '$NOME' in esecuzione: $COPIE"
        ps -eo pid,ppid,rss,pcpu,etime,comm --sort=-rss | head -8
    } >>"$REPORT"
    sleep 3
done

if kill -0 "$PID" 2>/dev/null; then
    pkill -P "$PID" 2>/dev/null
    kill "$PID" 2>/dev/null
    sleep 1
fi
pkill -f "$NOME" 2>/dev/null

{
    echo "=================================================="
    echo "Copie massime osservate: $MASSIMO_COPIE"
    echo
    echo "=== output a terminale ==="
    tail -n 60 "$TEMP_LOG"
    echo
    echo "=== log dell'applicazione ==="
    for file in \
        "$HOME/.local/share/FranchettiRawConverterPro/franchetti_log.txt" \
        "$HOME/franchetti_log.txt"; do
        if [ -f "$file" ]; then
            echo "--- $file"
            tail -n 60 "$file"
        fi
    done
} >>"$REPORT"

rm -f "$TEMP_LOG"

echo
echo "Report scritto in: $REPORT"
if [ "$MASSIMO_COPIE" -gt 3 ]; then
    echo "Sono comparse fino a $MASSIMO_COPIE copie dell'applicazione: e' il ciclo di processi."
else
    echo "Nessun ciclo di copie: la memoria cresce dentro un solo processo."
fi
