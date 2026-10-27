# -*- coding: utf-8 -*-
"""
================================================================================
          FRANCHETTI RAW CONVERTER PRO v2.54.0 - MONOLITHIC CORE
================================================================================
Licenza: MIT
Descrizione: Suite Enterprise Open-Source per lo sviluppo RAW lineare a livello
             sensore (LibRaw con fallback AMaZE/AHD/PPG/LINEAR), ottimizzazione
             in spazio Y/Cb/Cr, denoise ISO, correzioni colore complete, ridimensionamento,
             watermarking, tethering Wi-Fi automatico (Hot-Folder), Cloud
             (Telegram/Dropbox) ed elaborazione batch su tutti i core.
================================================================================
"""

import os
import sys
import json
import math
import time
import queue
import logging
import threading
import traceback
import multiprocessing
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from tkinter import filedialog, messagebox

try:
    import numpy as np
    import rawpy
    import piexif
    import customtkinter as ctk
    from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageFont
    from skimage import color, filters
    from scipy.ndimage import uniform_filter
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import requests
except ImportError as e:  # pragma: no cover
    print(f"[ERRORE DI DIPENDENZA] Manca una libreria fondamentale: {e}")
    print("Esegui: pip install numpy rawpy piexif customtkinter Pillow scikit-image requests watchdog")
    sys.exit(1)


APP_VERSION = "2.54.0"
APP_TITLE = f"Franchetti Raw Converter Pro v{APP_VERSION} - Enterprise Suite"


def _scala_dpi_sistema():
    """Restituisce il fattore DPI di Windows (1.0 = 100%, 1.25 = 125%)."""
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        dc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, dc)
        if dpi and dpi > 0:
            return dpi / 96.0
    except Exception:
        pass
    return 1.0


SCALA_DPI = _scala_dpi_sistema()

# Impostiamo lo scaling PRIMA di creare la finestra: così tutti i widget
# nascono con fattore effettivo 1.0 ed evitiamo il doppio scaling (125% x 125%)
# che nell'exe PyInstaller tagliava la parte destra e inferiore dell'interfaccia.
if SCALA_DPI > 1.01:
    try:
        ctk.set_widget_scaling(1.0 / SCALA_DPI)
        ctk.set_window_scaling(1.0 / SCALA_DPI)
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Log su file: serve per diagnosticare i problemi segnalati dagli utenti.
try:
    _file_log = os.path.join(os.path.expanduser("~"), "Desktop", "franchetti_log.txt")
    _handler_file = logging.FileHandler(_file_log, encoding="utf-8")
    _handler_file.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(_handler_file)
except Exception:
    pass

RAW_ESTENSIONI = (
    ".arw", ".cr2", ".cr3", ".nef", ".nrw", ".raf", ".dng", ".orf", ".rw2",
    ".pef", ".srw", ".x3f", ".3fr", ".fff", ".raw", ".rwl", ".dcr", ".k25",
    ".kdc", ".mos", ".mrw", ".erf", ".mef", ".iiq", ".cap", ".braw", ".gpr",
)
IMMAGINI_ESTENSIONI = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp")
ESTENSIONI_ACCETTATE = RAW_ESTENSIONI + IMMAGINI_ESTENSIONI

FORMATI_OUTPUT = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "TIFF": ".tif",
    "WEBP": ".webp",
}


# ================================================================================
# 1. PARAMETRI DI DEFAULT
# ================================================================================
def parametri_default():
    return {
        # --- Sviluppo / tono ---
        "esposizione": 0.0,
        "temperatura": 0.0,
        "tinta": 0.0,
        "luci": 0.0,
        "ombre": 0.0,
        "bianchi": 0.0,
        "neri": 0.0,
        "contrasto": 0.35,
        "vivacita": 0.35,
        "saturazione": 1.0,
        "chiarezza": 0.0,
        "dehaze": 0.0,
        "nr_luminanza": 0.0,
        "nr_colore": 0.0,
        "rimuovi_grana_auto": False,
        "nitidezza_raggio": 1.5,
        "nitidezza_quantita": 1.0,
        "vignettatura": 0.0,
        "grana": 0.0,
        "curva_tonale": "Lineare",
        "hsl_rosso": 0.0,
        "hsl_verde": 0.0,
        "hsl_blu": 0.0,
        "colore_ombre": "#2b4c7e",
        "intensita_ombre": 0.0,
        "colore_luci": "#e0b070",
        "intensita_luci": 0.0,
        # --- Sviluppo RAW ---
        "use_camera_wb": True,
        "profilo_colore": "sRGB",
        # --- Output ---
        "max_dim": 1920,
        "qualita_jpeg": 90,
        "formato": "JPEG",
        "preserva_exif": True,
        # --- Miglioramento automatico (BETA) ---
        "auto_luminosita": False,
        # --- Prestazioni ---
        "usa_multicore": True,
        "mantieni_nomi": True,
        "prefisso": "",
        "suffisso": "",
        "sovrascrittura": "Rinomina",
        "ricorsivo": True,
        # --- Watermark ---
        "watermark_attivo": True,
        "watermark_text": "\u00a9 Franchetti 2025",
        "font_size": 14,
        "watermark_posizione": "Basso a destra",
        "watermark_opacita": 0.85,
        "logo_path": "",
        "logo_opacita": 0.55,
        # --- Tethering / Cloud ---
        "wifi_dir": "",
        "output_dir": "",
        "tg_token": "",
        "tg_chat_id": "",
        "gdrive_key": "",
        "meta_token": "",
        "meta_id": "",
        "dropbox_token": "",
        "swisstransfer_email": "",
        "cloud_telegram": False,
        "cloud_gdrive": False,
        "cloud_meta": False,
        "cloud_dropbox": False,
        "cloud_swiss": False,
        "tethering_attivo": False,
    }


LIMITI_NUMERICI = {
    "esposizione": (-3.0, 3.0),
    "temperatura": (-100.0, 100.0),
    "tinta": (-100.0, 100.0),
    "luci": (-100.0, 100.0),
    "ombre": (-100.0, 100.0),
    "bianchi": (-100.0, 100.0),
    "neri": (-100.0, 100.0),
    "contrasto": (0.0, 1.0),
    "vivacita": (0.0, 1.0),
    "saturazione": (0.0, 2.0),
    "chiarezza": (0.0, 1.0),
    "dehaze": (0.0, 1.0),
    "nr_luminanza": (0.0, 100.0),
    "nr_colore": (0.0, 100.0),
    "nitidezza_raggio": (0.5, 4.0),
    "nitidezza_quantita": (0.0, 5.0),
    "vignettatura": (-100.0, 100.0),
    "grana": (0.0, 100.0),
    "hsl_rosso": (-100.0, 100.0),
    "hsl_verde": (-100.0, 100.0),
    "hsl_blu": (-100.0, 100.0),
    "intensita_ombre": (0.0, 100.0),
    "intensita_luci": (0.0, 100.0),
    "max_dim": (0.0, 20000.0),
    "qualita_jpeg": (1.0, 100.0),
    "font_size": (8.0, 600.0),
    "watermark_opacita": (0.0, 1.0),
    "logo_opacita": (0.0, 1.0),
}


def pulisci_nome_file(valore):
    """Rimuove i caratteri non validi nei nomi file di Windows."""
    testo = str(valore or "")
    for carattere in '<>:"/\\|?*':
        testo = testo.replace(carattere, "_")
    return testo.strip().rstrip(".")


def normalizza_parametri(parametri):
    """Ripulisce i parametri (anche da un file di configurazione) prima dell'uso.

    Evita che un valore mancante o scritto male blocchi l'intera conversione.
    """
    base = parametri_default()
    p = dict(base)
    if parametri:
        p.update(parametri)

    for chiave, (minimo, massimo) in LIMITI_NUMERICI.items():
        try:
            valore = float(p.get(chiave, base[chiave]))
        except (TypeError, ValueError):
            valore = float(base[chiave])
        if not math.isfinite(valore):
            valore = float(base[chiave])
        p[chiave] = max(minimo, min(massimo, valore))

    for chiave in ("max_dim", "qualita_jpeg", "font_size"):
        p[chiave] = int(round(p[chiave]))

    formato = str(p.get("formato", "JPEG") or "JPEG").strip().upper()
    if formato == "JPG":
        formato = "JPEG"
    if formato == "TIF":
        formato = "TIFF"
    if formato not in FORMATI_OUTPUT:
        formato = "JPEG"
    p["formato"] = formato
    p["profilo_colore"] = "sRGB"

    politica = str(p.get("sovrascrittura", "Rinomina") or "Rinomina").strip()
    if politica not in ("Rinomina", "Sovrascrivi", "Salta"):
        politica = "Rinomina"
    p["sovrascrittura"] = politica

    for chiave in (
        "usa_multicore", "auto_luminosita", "rimuovi_grana_auto", "preserva_exif", "mantieni_nomi",
        "ricorsivo", "watermark_attivo", "use_camera_wb", "cloud_telegram",
        "cloud_gdrive", "cloud_meta", "cloud_dropbox", "cloud_swiss",
    ):
        p[chiave] = bool(p.get(chiave))

    p["prefisso"] = pulisci_nome_file(p.get("prefisso", ""))
    p["suffisso"] = pulisci_nome_file(p.get("suffisso", ""))
    p["watermark_text"] = str(p.get("watermark_text", "") or "")
    return p


# ================================================================================
# 1b. ELABORAZIONE PARALLELA: TUTTI I CORE DEL PROCESSORE
# ================================================================================
def memoria_disponibile_mb():
    """Memoria fisica libera in MB (Windows); 4 GB come stima prudente."""
    try:
        import ctypes

        class _MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stato = _MemoryStatusEx()
        stato.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stato)):
            return int(stato.ullAvailPhys / (1024 * 1024))
    except Exception:
        pass
    return 4096


def numero_processi_ottimale(numero_file, per_processo_mb=1200):
    """Quanti processi usare: tutti i core, limitati dalla RAM disponibile."""
    cpu = os.cpu_count() or 1
    # Picco stimato per processo: 1,2 GB a dimensione web; molto di piu' su
    # originali 24-60 MP, soprattutto con la riduzione grana attiva.
    per_ram = max(1, int((memoria_disponibile_mb() * 0.85) / max(256, per_processo_mb)))
    return max(1, min(int(cpu), per_ram, max(1, int(numero_file))))


_THREAD_ENV_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


def _limita_thread_per_processi():
    """Un solo thread BLAS/OpenMP per worker: evita oversubscription.

    Con 12-20 processi paralleli ogni worker non deve aprire a sua volta
    12-20 thread: si perderebbero decine di secondi in contesa di CPU.
    """
    vecchi = {}
    for nome in _THREAD_ENV_VARS:
        vecchi[nome] = os.environ.get(nome)
        os.environ[nome] = "1"
    return vecchi


def _ripristina_thread(vecchi):
    for nome, valore in (vecchi or {}).items():
        if valore is None:
            os.environ.pop(nome, None)
        else:
            os.environ[nome] = valore


def percorso_unico(percorso):
    """Restituisce un percorso libero, aggiungendo _1, _2, ... se necessario."""
    if not os.path.exists(percorso):
        return percorso
    radice, estensione = os.path.splitext(percorso)
    contatore = 1
    while True:
        candidato = f"{radice}_{contatore}{estensione}"
        if not os.path.exists(candidato):
            return candidato
        contatore += 1


def raccogli_file_sorgente(sorgente, ricorsivo=True, escludi=None):
    """Elenca i file convertibili. Evita duplicati e la cartella di output."""
    sorgente = str(sorgente or "").strip()
    escluso = None
    if escludi and os.path.isdir(sorgente):
        try:
            sorgente_norm = os.path.normcase(os.path.abspath(sorgente))
            escluso_norm = os.path.normcase(os.path.abspath(escludi))
            # Esclude l'output solo se e' dentro la sorgente. Se la destinazione
            # e' una cartella superiore, i file della sorgente devono restare.
            if escluso_norm == sorgente_norm or escluso_norm.startswith(
                sorgente_norm + os.sep
            ):
                escluso = escluso_norm
        except Exception:
            escluso = None

    def valido(percorso):
        if escluso:
            percorso_norm = os.path.normcase(os.path.abspath(percorso))
            if percorso_norm == escluso or percorso_norm.startswith(escluso + os.sep):
                return False
        return percorso.lower().endswith(ESTENSIONI_ACCETTATE)

    if ";" in sorgente:
        elenco = []
        for voce in sorgente.split(";"):
            voce = voce.strip()
            if voce and os.path.isfile(voce) and valido(voce):
                elenco.append(voce)
        return list(dict.fromkeys(elenco))
    if os.path.isfile(sorgente):
        return [sorgente] if valido(sorgente) else []
    if not os.path.isdir(sorgente):
        return []

    files = []
    if ricorsivo:
        for root, cartelle, nomi in os.walk(sorgente):
            if escluso:
                cartelle[:] = [
                    c for c in cartelle
                    if os.path.normcase(os.path.abspath(os.path.join(root, c))) != escluso
                ]
            for nome in nomi:
                percorso = os.path.join(root, nome)
                if valido(percorso):
                    files.append(percorso)
    else:
        for nome in os.listdir(sorgente):
            percorso = os.path.join(sorgente, nome)
            if os.path.isfile(percorso) and valido(percorso):
                files.append(percorso)
    return sorted(files)


def _converti_file_worker(compito):
    """Converte un singolo file. Funzione di modulo: necessaria al multiprocessing.

    Scrive su un file temporaneo e sostituisce l'output solo a conversione
    completata: un annullamento non lascia file corrotti.
    """
    percorso, output, parametri = compito
    temporaneo = ""
    try:
        if os.path.normcase(os.path.abspath(percorso)) == os.path.normcase(
            os.path.abspath(output)
        ):
            return {
                "percorso": percorso,
                "output": output,
                "ok": False,
                "errore": "Sorgente e destinazione coincidono: file non sovrascritto",
            }
        cartella = os.path.dirname(output)
        if cartella:
            os.makedirs(cartella, exist_ok=True)
        radice, estensione = os.path.splitext(output)
        temporaneo = f"{radice}.tmp{estensione}"
        ImageEngine.sviluppa_e_ottimizza(percorso, temporaneo, parametri)
        os.replace(temporaneo, output)
        return {"percorso": percorso, "output": output, "ok": True, "errore": ""}
    except Exception as errore:
        return {
            "percorso": percorso,
            "output": output,
            "ok": False,
            "errore": f"{type(errore).__name__}: {errore}",
            "traceback": traceback.format_exc(),
        }
    finally:
        if temporaneo:
            try:
                if os.path.exists(temporaneo):
                    os.remove(temporaneo)
            except Exception:
                pass


_ESECUTORI_ATTIVI = set()
_LOCK_ESECUTORI = threading.Lock()


def _termina_esecutore(esecutore):
    """Interrompe subito i processi figli (usato dall'annullamento)."""
    for processo in list(getattr(esecutore, "_processes", {}).values()):
        try:
            if processo.is_alive():
                processo.terminate()
        except Exception:
            pass


def termina_tutti_gli_esecutori():
    """Chiude subito ogni elaborazione parallela in corso (chiusura app)."""
    with _LOCK_ESECUTORI:
        esecutori = list(_ESECUTORI_ATTIVI)
    for esecutore in esecutori:
        _termina_esecutore(esecutore)
        try:
            esecutore.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass


def _pulisci_temporanei(compiti):
    """Rimuove i file .tmp rimasti se un processo viene terminato a meta' lavoro."""
    for _, _, output, _ in compiti:
        radice, estensione = os.path.splitext(output)
        temporaneo = f"{radice}.tmp{estensione}"
        for tentativo in range(3):
            try:
                if os.path.exists(temporaneo):
                    os.remove(temporaneo)
                break
            except OSError as errore:
                if tentativo == 2:
                    logging.warning("Impossibile rimuovere %s: %s", temporaneo, errore)
                else:
                    time.sleep(0.2)


def esegui_batch(files, params, destinazione, log=None, progresso=None, cancel_event=None):
    """Converte tutti i file, in parallelo su tutti i core quando possibile.

    log(messaggio), progresso(indice, totale, ok, errori, saltati).
    """
    def nota(messaggio):
        if log:
            try:
                log(messaggio)
            except Exception:
                pass

    def avanza(indice, totale, ok, errori, saltati):
        if progresso:
            try:
                progresso(indice, totale, ok, errori, saltati)
            except Exception:
                pass

    def cloud(output):
        canali = ("cloud_telegram", "cloud_gdrive", "cloud_meta", "cloud_dropbox", "cloud_swiss")
        if not any(params.get(c) for c in canali):
            return
        try:
            esiti = CloudDispatcher.dispatch(output, params)
            for nome_canale, esito in esiti:
                nota(f"Cloud {nome_canale}: {'inviato' if esito else 'saltato'}")
        except Exception as errore:
            nota(f"Cloud: errore di invio ({errore})")

    totale = len(files)
    params = normalizza_parametri(params)
    formato = str(params.get("formato", "JPEG")).upper()
    if formato == "JPG":
        formato = "JPEG"
    if formato == "TIF":
        formato = "TIFF"
    estensione = FORMATI_OUTPUT.get(formato, ".jpg")
    prefisso = str(params.get("prefisso", "") or "")
    suffisso = str(params.get("suffisso", "") or "")
    politica = str(params.get("sovrascrittura", "Rinomina") or "Rinomina")
    ok = errori = saltati = 0
    compiti = []
    nomi_prenotati = set()

    for indice, percorso in enumerate(files, start=1):
        if cancel_event is not None and cancel_event.is_set():
            break
        base = os.path.splitext(os.path.basename(percorso))[0]
        if params.get("mantieni_nomi", True):
            radice_nome = f"{prefisso}{base}{suffisso}"
        else:
            radice_nome = f"{prefisso}IMG_{indice:04d}{suffisso}"
        nome = f"{radice_nome}{estensione}"
        output = os.path.join(destinazione, nome)
        chiave = os.path.normcase(os.path.abspath(output))

        if politica == "Salta" and (os.path.exists(output) or chiave in nomi_prenotati):
            saltati += 1
            nota(f"Saltato (esiste): {nome}")
            avanza(indice, totale, ok, errori, saltati)
            continue

        # Nomi uguali (anche da sottocartelle diverse) non devono mai
        # scrivere sullo stesso file nello stesso momento. Con "Sovrascrivi"
        # un file gia' presente viene sostituito, ma non due file del batch.
        da_rinominare = chiave in nomi_prenotati or (
            politica == "Rinomina" and os.path.exists(output)
        )
        if da_rinominare:
            contatore = 1
            while True:
                nome = f"{radice_nome}_{contatore}{estensione}"
                output = os.path.join(destinazione, nome)
                chiave = os.path.normcase(os.path.abspath(output))
                libero = chiave not in nomi_prenotati
                if politica == "Rinomina":
                    libero = libero and not os.path.exists(output)
                if libero:
                    break
                contatore += 1

        nomi_prenotati.add(chiave)
        compiti.append((indice, percorso, output, nome))

    if compiti and (cancel_event is None or not cancel_event.is_set()):
        processi = 1
        if params.get("usa_multicore", True) and len(compiti) > 1:
            denoise = (
                float(params.get("nr_luminanza", 0.0)) > 0.0
                or float(params.get("nr_colore", 0.0)) > 0.0
            )
            max_dim = int(params.get("max_dim", 0) or 0)
            per_processo = 1200
            if max_dim == 0:
                per_processo = 2400 if denoise else 1800
            processi = numero_processi_ottimale(len(compiti), per_processo)
        if processi > 1:
            nota(f"Elaborazione parallela: {processi} processi su {os.cpu_count() or 1} core CPU.")
        else:
            nota("Elaborazione sequenziale.")

        if processi <= 1:
            for indice, percorso, output, nome in compiti:
                if cancel_event is not None and cancel_event.is_set():
                    break
                esito = _converti_file_worker((percorso, output, params))
                if esito["ok"]:
                    ok += 1
                    nota(f"OK: {nome}")
                    cloud(output)
                else:
                    errori += 1
                    logging.error("Errore su %s: %s", percorso, esito["errore"])
                    nota(f"ERRORE su {os.path.basename(percorso)}: {esito['errore']}")
                avanza(indice, totale, ok, errori, saltati)
        else:
            vecchi_thread = _limita_thread_per_processi()
            try:
                esecutore = ProcessPoolExecutor(max_workers=processi)
            except Exception:
                _ripristina_thread(vecchi_thread)
                raise
            with _LOCK_ESECUTORI:
                _ESECUTORI_ATTIVI.add(esecutore)
            futuro_mappa = {}
            annullato_durante = False
            try:
                for indice, percorso, output, nome in compiti:
                    if cancel_event is not None and cancel_event.is_set():
                        annullato_durante = True
                        break
                    futuro = esecutore.submit(_converti_file_worker, (percorso, output, params))
                    futuro_mappa[futuro] = (indice, percorso, output, nome)

                pendenti = set(futuro_mappa)
                while pendenti:
                    # Attesa breve: l'annullamento deve reagire subito, non
                    # aspettare che finisca la prima conversione in corso.
                    if cancel_event is not None and cancel_event.is_set():
                        annullato_durante = True
                        for altro in pendenti:
                            altro.cancel()
                        _termina_esecutore(esecutore)
                        break
                    completati, pendenti = wait(
                        pendenti, timeout=0.2, return_when=FIRST_COMPLETED
                    )
                    for futuro in completati:
                        if cancel_event is not None and cancel_event.is_set():
                            annullato_durante = True
                            for altro in pendenti:
                                altro.cancel()
                            _termina_esecutore(esecutore)
                            break
                        indice, percorso, output, nome = futuro_mappa[futuro]
                        try:
                            esito = futuro.result()
                        except Exception as errore:
                            esito = {
                                "ok": False,
                                "errore": f"{type(errore).__name__}: {errore}",
                            }
                            logging.error("Errore sul processo per %s: %s", percorso, errore)
                        if esito.get("ok"):
                            ok += 1
                            nota(f"OK: {nome}")
                            cloud(output)
                        else:
                            errori += 1
                            logging.error(
                                "Errore su %s: %s", percorso, esito.get("errore", "sconosciuto")
                            )
                            nota(
                                f"ERRORE su {os.path.basename(percorso)}: "
                                f"{esito.get('errore', 'sconosciuto')}"
                            )
                        avanza(indice, totale, ok, errori, saltati)
                    if annullato_durante:
                        break
            finally:
                if annullato_durante:
                    _termina_esecutore(esecutore)
                    try:
                        esecutore.shutdown(wait=False, cancel_futures=True)
                    except Exception:
                        pass
                    # I processi terminati non eseguono il loro finally: elimina
                    # gli eventuali .tmp prima di restituire il controllo alla GUI.
                    time.sleep(0.2)
                    _pulisci_temporanei(compiti)
                else:
                    esecutore.shutdown(wait=True)
                with _LOCK_ESECUTORI:
                    _ESECUTORI_ATTIVI.discard(esecutore)
                _ripristina_thread(vecchi_thread)

    annullato = bool(cancel_event is not None and cancel_event.is_set())
    if annullato:
        nota("Batch annullato dall'utente.")
    return {
        "ok": ok,
        "errori": errori,
        "saltati": saltati,
        "totale": totale,
        "annullato": annullato,
    }


# ================================================================================
# 2. CORE PIPELINE: MOTORE DI ELABORAZIONE IMMAGINI IN SPAZIO Y/Cb/Cr
# ================================================================================
class ImageEngine:
    """Pipeline completa RAW -> JPEG/TIFF/PNG/WEBP con correzioni fotografiche."""

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _luma(img):
        return (
            0.2126 * img[:, :, 0]
            + 0.7152 * img[:, :, 1]
            + 0.0722 * img[:, :, 2]
        )

    @staticmethod
    def _smoothstep(edge0, edge1, x):
        t = np.clip((x - edge0) / max(edge1 - edge0, 1e-6), 0.0, 1.0)
        return t * t * (3.0 - 2.0 * t)

    @classmethod
    def _applica_luminanza(cls, img, nuova_lum):
        """Cambia la luminanza preservando la crominanza originale."""
        lum = np.clip(cls._luma(img), 1e-5, 1.0)
        fattore = np.clip(nuova_lum, 0.0, 1.0) / lum
        return np.clip(img * fattore[:, :, None], 0.0, 1.0)

    @staticmethod
    def _hex_to_rgb(valore):
        valore = (valore or "#808080").lstrip("#")
        if len(valore) == 3:
            valore = "".join(c * 2 for c in valore)
        try:
            return np.array([int(valore[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
        except Exception:
            return np.array([0.5, 0.5, 0.5])

    @staticmethod
    def _curva_lut(tipo):
        x = np.linspace(0.0, 1.0, 256)
        if tipo == "Schiarisci":
            y = x ** 0.85
        elif tipo == "Scurisci":
            y = x ** 1.18
        elif tipo == "Media":
            y = x * 0.85 + (x * x * (3.0 - 2.0 * x)) * 0.15
        elif tipo == "Forte":
            y = x * 0.55 + (x * x * (3.0 - 2.0 * x)) * 0.45
        elif tipo == "Contrasto Alto":
            y = x * 0.35 + (x * x * (3.0 - 2.0 * x)) * 0.65
        else:
            y = x
        return np.clip(y, 0.0, 1.0) * 100.0

    # ------------------------------------------------------------ fase 1: tono
    @classmethod
    def _fase_tono(cls, img, p):
        ev = float(p.get("esposizione", 0.0))
        if abs(ev) > 1e-4:
            img = img * (2.0 ** ev)

        temp = float(p.get("temperatura", 0.0)) / 100.0
        tinta = float(p.get("tinta", 0.0)) / 100.0
        if abs(temp) > 1e-4 or abs(tinta) > 1e-4:
            img[:, :, 0] *= 1.0 + 0.30 * temp + 0.06 * tinta
            img[:, :, 1] *= 1.0 - 0.15 * tinta
            img[:, :, 2] *= 1.0 - 0.30 * temp + 0.06 * tinta
        img = np.clip(img, 0.0, 1.0)

        lum = np.clip(cls._luma(img), 0.0, 1.0)
        m_luci = cls._smoothstep(0.45, 1.0, lum)
        m_ombre = 1.0 - cls._smoothstep(0.0, 0.55, lum)
        m_bianchi = lum ** 3
        m_neri = (1.0 - lum) ** 3

        delta = (
            float(p.get("luci", 0.0)) / 100.0 * 0.45 * m_luci
            + float(p.get("ombre", 0.0)) / 100.0 * 0.45 * m_ombre
            + float(p.get("bianchi", 0.0)) / 100.0 * 0.30 * m_bianchi
            + float(p.get("neri", 0.0)) / 100.0 * 0.30 * m_neri
        )
        if np.any(np.abs(delta) > 1e-5):
            img = cls._applica_luminanza(img, np.clip(lum + delta, 0.0, 1.0))

        forza = float(p.get("contrasto", 0.0))
        if forza > 1e-4:
            lum = np.clip(cls._luma(img), 0.0, 1.0)
            curva = lum * lum * (3.0 - 2.0 * lum)
            nuova = lum * (1.0 - forza) + curva * forza
            nuova = np.clip(0.5 + (nuova - 0.5) * (1.0 + forza * 0.35), 0.0, 1.0)
            img = cls._applica_luminanza(img, nuova)

        return img

    # ------------------------------------------------------ fase 2: colore
    @staticmethod
    def _fase_colore(img, p):
        # Vivacità selettiva
        viv = float(p.get("vivacita", 0.0))
        if viv > 1e-4:
            maxv = img.max(axis=2)
            lcs = maxv - img.min(axis=2)
            out = img.copy()
            for i in range(3):
                out[:, :, i] = img[:, :, i] + (maxv - img[:, :, i]) * lcs * viv * 2.0
            img = np.clip(out, 0.0, 1.0)

        # Saturazione globale
        sat = float(p.get("saturazione", 1.0))
        if abs(sat - 1.0) > 1e-4:
            lum = ImageEngine._luma(img)[:, :, None]
            img = np.clip(lum + (img - lum) * sat, 0.0, 1.0)

        # HSL selettivo (rosso / verde / blu)
        hr = float(p.get("hsl_rosso", 0.0)) / 100.0
        hg = float(p.get("hsl_verde", 0.0)) / 100.0
        hb = float(p.get("hsl_blu", 0.0)) / 100.0
        if abs(hr) + abs(hg) + abs(hb) > 1e-4:
            hsv = color.rgb2hsv(np.clip(img, 0.0, 1.0))
            h = hsv[:, :, 0]
            m_r = ((h < 0.055) | (h > 0.945)).astype(np.float32)
            m_g = ((h >= 0.20) & (h <= 0.45)).astype(np.float32)
            m_b = ((h >= 0.50) & (h <= 0.75)).astype(np.float32)
            fattore = 1.0 + hr * m_r + hg * m_g + hb * m_b
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * fattore, 0.0, 1.0)
            img = np.clip(color.hsv2rgb(hsv), 0.0, 1.0)

        return img

    # --------------------------------------------------- fase 3: micro-contrasto
    @classmethod
    def _fase_dettaglio(cls, img, p):
        # Chiarezza (local contrast)
        chiarezza = float(p.get("chiarezza", 0.0))
        if chiarezza > 1e-4:
            lum = cls._luma(img)
            sigma = max(2.0, min(img.shape[0], img.shape[1]) / 220.0)
            sfocata = filters.gaussian(lum, sigma=sigma, preserve_range=True)
            nuova = np.clip(lum + (lum - sfocata) * chiarezza * 1.6, 0.0, 1.0)
            img = cls._applica_luminanza(img, nuova)

        # Dehaze semplificato (rimozione velo atmosferico)
        deh = float(p.get("dehaze", 0.0))
        if deh > 1e-4:
            velo = 0.06 * deh
            img = np.clip((img - velo) / max(1.0 - velo, 1e-3), 0.0, 1.0)
            img = np.clip(0.5 + (img - 0.5) * (1.0 + 0.35 * deh), 0.0, 1.0)

        return img

    # ------------------------------------- fase 4: grana, curva e nitidezza
    @staticmethod
    def _box_mean(array, raggio):
        """Media locale veloce (filtro a finestra separabile)."""
        raggio = max(0, int(raggio))
        if raggio <= 0:
            return array
        return uniform_filter(array, size=2 * raggio + 1, mode="reflect")

    @classmethod
    def _guided_auto(cls, y, raggio, epsilon):
        """Guided filter auto-guidato: leviga il rumore senza tagliare i bordi."""
        media = cls._box_mean(y, raggio)
        varianza = np.maximum(cls._box_mean(y * y, raggio) - media * media, 0.0)
        a = varianza / (varianza + epsilon)
        b = media * (1.0 - a)
        return cls._box_mean(a, raggio) * y + cls._box_mean(b, raggio)

    @classmethod
    def _guided(cls, guida, sorgente, raggio, epsilon):
        """Guided filter: usa la luminanza come guida per crominanza e colore."""
        media_g = cls._box_mean(guida, raggio)
        media_s = cls._box_mean(sorgente, raggio)
        var_g = np.maximum(cls._box_mean(guida * guida, raggio) - media_g * media_g, 0.0)
        cov = cls._box_mean(guida * sorgente, raggio) - media_g * media_s
        a = cov / (var_g + epsilon)
        b = media_s - a * media_g
        return cls._box_mean(a, raggio) * guida + cls._box_mean(b, raggio)

    @staticmethod
    def _down2(array):
        """Riduce di 2x con media: la crominanza non perde dettaglio utile."""
        h, w = array.shape
        h2, w2 = h // 2, w // 2
        if h2 < 2 or w2 < 2:
            return array
        return array[: h2 * 2, : w2 * 2].reshape(h2, 2, w2, 2).mean(axis=(1, 3))

    @staticmethod
    def _up2(array, larghezza, altezza):
        """Riporta a dimensione piena un canale float con interpolazione lineare."""
        if array.shape == (altezza, larghezza):
            return array
        canale = Image.fromarray(array.astype(np.float32), mode="F")
        return np.asarray(
            canale.resize((larghezza, altezza), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )

    @classmethod
    def _riduci_grana(cls, img, p, nrl, nrc):
        """Riduzione grana ISO con preservazione di bordi, contrasto e dettaglio.

        Lavora in Y/Cb/Cr: il canale di luminanza usa un guided filter
        auto-guidato, la crominanza un guided filter guidato dalla luminanza.
        Il rumore viene tolto nelle zone piatte, mentre i bordi e i dettagli
        fini restano intatti. La forza si adatta all'ISO del RAW.
        """
        iso = float(p.get("_iso", 0) or 0)
        fattore = 1.0
        if p.get("rimuovi_grana_auto") and iso > 0:
            if iso <= 400:
                fattore = 0.60
            elif iso <= 800:
                fattore = 0.78
            elif iso <= 1600:
                fattore = 0.92
            elif iso <= 3200:
                fattore = 1.08
            elif iso <= 6400:
                fattore = 1.22
            else:
                fattore = 1.35
        nrl = max(0.0, min(1.0, nrl * fattore))
        nrc = max(0.0, min(1.0, nrc * fattore))
        if nrl <= 1e-4 and nrc <= 1e-4:
            return img

        r = img[:, :, 0]
        g = img[:, :, 1]
        b = img[:, :, 2]
        y = 0.299 * r + 0.587 * g + 0.114 * b
        cb = b - y
        cr = r - y

        if nrl > 1e-4:
            raggio = max(1, int(round(1.0 + nrl * 4.0)))
            epsilon = 0.00015 + (nrl * nrl) * 0.0012
            y_pulita = cls._guided_auto(y, raggio, epsilon)
            # Il guided filter preserva i bordi; lasciamo un 2% del residuo
            # per non rendere la pelle "di plastica".
            y = y_pulita + (y - y_pulita) * 0.02

        if nrc > 1e-4:
            raggio = max(3, int(round(3.0 + nrc * 11.0)))
            epsilon = 0.0003 + (nrc * nrc) * 0.004
            # La crominanza e' a bassa frequenza: denoise a meta' risoluzione,
            # poi ricostruzione lineare. 4x piu' veloce, stesso risultato visivo.
            y_small = cls._down2(y)
            cb_small = cls._down2(cb)
            cr_small = cls._down2(cr)
            if cb_small is not cb:
                raggio_small = max(2, raggio // 2)
                cb_pulito = cls._guided(y_small, cb_small, raggio_small, epsilon)
                cr_pulito = cls._guided(y_small, cr_small, raggio_small, epsilon)
                cb_pulito = cls._up2(cb_pulito, cb.shape[1], cb.shape[0])
                cr_pulito = cls._up2(cr_pulito, cr.shape[1], cr.shape[0])
            else:
                cb_pulito = cls._guided(y, cb, raggio, epsilon)
                cr_pulito = cls._guided(y, cr, raggio, epsilon)
            beta = min(0.98, 0.70 + nrc * 0.28)
            cb = cb * (1.0 - beta) + cb_pulito * beta
            cr = cr * (1.0 - beta) + cr_pulito * beta

        r2 = y + cr
        b2 = y + cb
        g2 = (y - 0.299 * r2 - 0.114 * b2) / 0.587
        return np.clip(np.stack((r2, g2, b2), axis=-1), 0.0, 1.0)

    @classmethod
    def _fase_lab(cls, img, p):
        """Grana, curva tonale e nitidezza senza conversioni Lab pesanti."""
        nrl = float(p.get("nr_luminanza", 0.0)) / 100.0
        nrc = float(p.get("nr_colore", 0.0)) / 100.0
        if nrl > 1e-4 or nrc > 1e-4:
            img = cls._riduci_grana(img, p, nrl, nrc)

        curva = p.get("curva_tonale", "Lineare")
        if curva and curva != "Lineare":
            lum = np.clip(cls._luma(img), 0.0, 1.0)
            lut = cls._curva_lut(curva) / 100.0
            indici = np.clip((lum * 255.0).astype(np.int32), 0, 255)
            img = cls._applica_luminanza(img, lut[indici])

        q = float(p.get("nitidezza_quantita", 0.0))
        if q > 1e-4:
            raggio = float(p.get("nitidezza_raggio", 1.5))
            lum = np.clip(cls._luma(img), 0.0, 1.0)
            lum = filters.unsharp_mask(lum, radius=raggio, amount=q, preserve_range=True)
            img = cls._applica_luminanza(img, np.clip(lum, 0.0, 1.0))

        return np.clip(img, 0.0, 1.0)

    # ---------------------------------------------------- fase 5: effetti finali
    @classmethod
    def _fase_effetti(cls, img, p):
        # Split toning
        int_om = float(p.get("intensita_ombre", 0.0)) / 100.0
        int_lu = float(p.get("intensita_luci", 0.0)) / 100.0
        if int_om > 1e-4 or int_lu > 1e-4:
            lum = cls._luma(img)
            if int_om > 1e-4:
                col = cls._hex_to_rgb(p.get("colore_ombre", "#2b4c7e"))
                m = ((1.0 - lum) ** 2 * int_om * 0.45)[:, :, None]
                img = img + (col[None, None, :] - img) * m
            if int_lu > 1e-4:
                col = cls._hex_to_rgb(p.get("colore_luci", "#e0b070"))
                m = ((lum ** 2) * int_lu * 0.45)[:, :, None]
                img = img + (col[None, None, :] - img) * m
            img = np.clip(img, 0.0, 1.0)

        # Vignettatura / correzione vignettatura
        vig = float(p.get("vignettatura", 0.0))
        if abs(vig) > 1e-4:
            h, w = img.shape[:2]
            yy, xx = np.mgrid[0:h, 0:w]
            cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
            r = np.sqrt(((xx - cx) / max(cx, 1e-3)) ** 2 + ((yy - cy) / max(cy, 1e-3)) ** 2) / math.sqrt(2.0)
            r = np.clip(r, 0.0, 1.0) ** 2
            if vig < 0:
                maschera = 1.0 - (abs(vig) / 100.0) * 0.75 * r
            else:
                maschera = 1.0 + (vig / 100.0) * 0.60 * r
            img = np.clip(img * maschera[:, :, None], 0.0, 1.0)

        # Grana fotografica
        gr = float(p.get("grana", 0.0)) / 100.0
        if gr > 1e-4:
            rng = np.random.default_rng(42)
            rumore = rng.normal(0.0, 0.018 * gr, img.shape).astype(np.float32)
            img = np.clip(img + rumore, 0.0, 1.0)

        return img

    # ------------------------------------------------------------ watermark
    @staticmethod
    def _carica_font(dimensione):
        dimensione = max(8, int(dimensione))
        for nome in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(nome, dimensione)
            except Exception:
                continue
        try:
            return ImageFont.load_default(size=dimensione)
        except Exception:
            return ImageFont.load_default()

    @classmethod
    def applica_watermark_testo(cls, pil_img, testo, font_size, posizione, opacita):
        if not testo:
            return pil_img
        base = pil_img.convert("RGBA")
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = cls._carica_font(font_size)

        try:
            box = draw.textbbox((0, 0), testo, font=font)
            tw, th = box[2] - box[0], box[3] - box[1]
        except Exception:
            tw, th = len(testo) * font_size * 0.6, font_size

        margine = max(12, int(base.size[0] * 0.015))
        if posizione == "Basso a sinistra":
            x, y = margine, base.size[1] - th - margine
        elif posizione == "Alto a destra":
            x, y = base.size[0] - tw - margine, margine
        elif posizione == "Alto a sinistra":
            x, y = margine, margine
        elif posizione == "Centro":
            x, y = (base.size[0] - tw) // 2, (base.size[1] - th) // 2
        else:  # Basso a destra
            x, y = base.size[0] - tw - margine, base.size[1] - th - margine

        alfa = int(max(0, min(1, opacita)) * 255)
        # ombra per leggibilità su fondi chiari
        draw.text((x + 2, y + 2), testo, font=font, fill=(0, 0, 0, int(alfa * 0.65)))
        draw.text((x, y), testo, font=font, fill=(255, 255, 255, alfa))

        return Image.alpha_composite(base, overlay).convert("RGB")

    @staticmethod
    def applica_logo(base_image, logo_path, opacita=0.5, posizione="Basso a destra"):
        if not logo_path or not os.path.exists(logo_path):
            return base_image
        try:
            logo = Image.open(logo_path).convert("RGBA")
        except Exception as errore:
            logging.warning("Logo non leggibile (%s): %s", logo_path, errore)
            return base_image
        base_w, base_h = base_image.size
        if base_w <= 0 or logo.size[0] <= 0:
            return base_image

        larghezza = max(24, int(base_w * 0.15))
        altezza = max(1, int(logo.size[1] * (larghezza / float(logo.size[0]))))
        logo = logo.resize((larghezza, altezza), Image.Resampling.LANCZOS)

        alpha = logo.split()[3].point(lambda v: int(v * max(0.0, min(1.0, opacita))))
        logo.putalpha(alpha)

        layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        margine = max(12, int(base_w * 0.015))
        if posizione == "Basso a sinistra":
            pos = (margine, base_h - altezza - margine)
        elif posizione == "Alto a destra":
            pos = (base_w - larghezza - margine, margine)
        elif posizione == "Alto a sinistra":
            pos = (margine, margine)
        elif posizione == "Centro":
            pos = ((base_w - larghezza) // 2, (base_h - altezza) // 2)
        else:
            pos = (base_w - larghezza - margine, base_h - altezza - margine)
        layer.paste(logo, pos)

        return Image.alpha_composite(base_image.convert("RGBA"), layer).convert("RGB")

    # ------------------------------------------------------------ EXIF
    @classmethod
    def preserva_exif(cls, percorso_sorgente, percorso_output, attivo=True):
        if not attivo or not percorso_output.lower().endswith((".jpg", ".jpeg")):
            return
        try:
            exif_dict = piexif.load(percorso_sorgente)
            if piexif.ImageIFD.Orientation in exif_dict.get("0th", {}):
                exif_dict["0th"][piexif.ImageIFD.Orientation] = 1
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, percorso_output)
        except Exception as e:
            logging.debug("EXIF non preservabile per %s: %s", percorso_sorgente, e)

    # ------------------------------------------------------------ output
    @staticmethod
    def _salva(pil_img, percorso_output, p):
        formato = str(p.get("formato", "JPEG") or "JPEG").strip().upper()
        if formato == "JPG":
            formato = "JPEG"
        if formato == "TIF":
            formato = "TIFF"
        if formato not in ("JPEG", "PNG", "TIFF", "WEBP"):
            formato = "JPEG"
        try:
            qualita = int(p.get("qualita_jpeg", 90))
        except (TypeError, ValueError):
            qualita = 90
        qualita = max(1, min(100, qualita))
        kwargs = {}
        icc = None
        try:
            from PIL import ImageCms
            icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        except Exception:
            icc = None

        if formato == "JPEG":
            if pil_img.mode not in ("RGB", "L"):
                pil_img = pil_img.convert("RGB")
            kwargs = dict(quality=qualita, subsampling=0, optimize=False)
            if icc:
                kwargs["icc_profile"] = icc
        elif formato == "PNG":
            kwargs = dict(compress_level=6)
            if icc:
                kwargs["icc_profile"] = icc
        elif formato == "TIFF":
            kwargs = dict(compression="tiff_lzw")
            if icc:
                kwargs["icc_profile"] = icc
        elif formato == "WEBP":
            if pil_img.mode not in ("RGB", "RGBA"):
                pil_img = pil_img.convert("RGB")
            kwargs = dict(quality=qualita, method=4)
            if icc:
                kwargs["icc_profile"] = icc

        try:
            pil_img.save(percorso_output, format=formato, **kwargs)
        except OSError:
            # Alcuni JPEG fanno fallire l'ottimizzazione di libjpeg
            # ("broken data stream"): si riprova senza optimize.
            if formato == "JPEG" and kwargs.get("optimize"):
                kwargs.pop("optimize", None)
                pil_img.save(percorso_output, format=formato, **kwargs)
            else:
                raise

    # ------------------------------------------------------------ pipeline
    @staticmethod
    def correggi_luminosita_auto(pil_img):
        """Bilanciamento automatico dell'esposizione (funzione BETA "Piu' luminosa").

        Analizza l'istogramma: schiarisce le foto scure, riduce le alte luci
        delle foto troppo esposte, lascia invariate le foto gia' corrette.
        Usa una LUT a 256 livelli: veloce anche su immagini grandi.
        """
        arr = np.asarray(pil_img.convert("RGB"), dtype=np.uint8)
        base = arr.astype(np.float32) / 255.0
        lum = (
            0.2126 * base[..., 0] + 0.7152 * base[..., 1] + 0.0722 * base[..., 2]
        )
        mediana = float(np.median(lum))
        luci = float(np.percentile(lum, 97))

        # Bianco/nero assoluti: nulla da recuperare.
        if mediana <= 0.005 or mediana >= 0.995:
            return pil_img
        saturazione_max = float(
            (base.max(axis=2) - base.min(axis=2)).max()
        )

        gamma = 1.0
        if 0.01 < mediana < 0.40:
            # Foto scura: schiarisce fino a portare la mediana verso il centro
            obiettivo = 0.48 if mediana < 0.26 else 0.44
            gamma = math.log(obiettivo) / math.log(max(mediana, 0.01))
            gamma = max(0.32, min(1.0, gamma))
        elif luci > 0.985 and mediana < 0.995:
            # Solo alte luci realmente clipped: schiaritura contenuta, senza
            # scurire drasticamente una parete chiara ma correttamente esposta.
            obiettivo = max(0.66, min(0.80, mediana * 0.94))
            gamma = math.log(obiettivo) / math.log(max(mediana, 0.01))
            gamma = max(1.0, min(1.8, gamma))

        x = np.linspace(0.0, 1.0, 256, dtype=np.float32)
        y = np.power(x, gamma)
        # Ginocchio morbido sulle alte luci: evita di bruciare i bianchi
        ginocchio = 0.88
        sopra = y > ginocchio
        if np.any(sopra):
            y[sopra] = ginocchio + (1.0 - ginocchio) * np.tanh(
                (y[sopra] - ginocchio) / (1.0 - ginocchio)
            )
        y = np.clip(y / max(float(y[-1]), 1e-6), 0.0, 1.0)
        # Contrasto delicato: compensa l'appiattimento tipico dello schiarimento
        y = np.clip(0.5 + (y - 0.5) * 1.035, 0.0, 1.0)
        lut = (y * 255.0 + 0.5).astype(np.uint8)

        # Applica la curva alla sola luminanza: la saturazione non esplode.
        indici = np.clip((lum * 255.0).astype(np.int32), 0, 255)
        lum_nuova = lut[indici].astype(np.float32) / 255.0
        rapporto = lum_nuova / np.maximum(lum, 1e-4)
        base = np.clip(base * rapporto[..., None], 0.0, 1.0)

        # Vividezza misurata: piu' colore nelle zone spente, senza saturare
        # gli accenti ne' amplificare il rumore cromatico.
        lum2 = (
            0.2126 * base[..., 0] + 0.7152 * base[..., 1] + 0.0722 * base[..., 2]
        )
        grigio = lum2[..., None]
        saturazione = base.max(axis=2) - base.min(axis=2)
        spinta = 0.10 + 0.06 * (1.0 - np.clip(saturazione, 0.0, 1.0))
        base = grigio + (base - grigio) * (1.0 + spinta[..., None])
        base = np.clip(base, 0.0, 1.0)
        if abs(gamma - 1.0) < 1e-6 and saturazione_max < 0.002 and luci <= 0.985:
            return pil_img
        risultato = Image.fromarray((base * 255.0 + 0.5).astype(np.uint8), "RGB")

        # Micro-contrasto finale molto leggero: nessun effetto plastica.
        if min(risultato.size) > 4:
            risultato = risultato.filter(
                ImageFilter.UnsharpMask(radius=0.8, percent=20, threshold=5)
            )
        return risultato

    _demosaic_ok = None

    @classmethod
    def _decodifica_raw(cls, raw, p, nota=None):
        """Decodifica il RAW usando un algoritmo supportato dalla libraw inclusa.

        La build distribuita di rawpy/libraw non include sempre il pacchetto
        GPL3: in quel caso AMAZE non e' disponibile e si ripiega su AHD/PPG.
        """
        algoritmi = [
            rawpy.DemosaicAlgorithm.AMAZE,
            rawpy.DemosaicAlgorithm.AHD,
            rawpy.DemosaicAlgorithm.PPG,
            rawpy.DemosaicAlgorithm.LINEAR,
        ]
        if cls._demosaic_ok is not None:
            algoritmi = [cls._demosaic_ok] + [a for a in algoritmi if a != cls._demosaic_ok]
        ultimo_errore = None
        for algoritmo in algoritmi:
            try:
                rgb = raw.postprocess(
                    demosaic_algorithm=algoritmo,
                    use_camera_wb=bool(p.get("use_camera_wb", True)),
                    no_auto_bright=False,
                    output_color=rawpy.ColorSpace.sRGB,
                    output_bps=8,
                )
            except Exception as errore:
                ultimo_errore = errore
                continue
            if algoritmo != cls._demosaic_ok:
                cls._demosaic_ok = algoritmo
                if nota:
                    nota(f"Demosaic: {str(algoritmo).split('.')[-1]}")
            return rgb
        if ultimo_errore is not None:
            raise ultimo_errore
        raise RuntimeError("decodifica RAW non riuscita")

    @classmethod
    def sviluppa_e_ottimizza(cls, percorso_raw, percorso_output, parametri, callback=None):
        p = normalizza_parametri(parametri)

        def nota(msg):
            logging.info(msg)
            if callback:
                try:
                    callback(msg)
                except Exception:
                    pass

        nota(f"Avvio sviluppo: {os.path.basename(percorso_raw)}")

        # 1. Decodifica RAW (o immagine standard)
        iso = 0.0
        if percorso_raw.lower().endswith(RAW_ESTENSIONI):
            with rawpy.imread(percorso_raw) as raw:
                rgb = cls._decodifica_raw(raw, p, nota)
                try:
                    iso = float(raw.other.iso_speed or 0.0)
                except Exception:
                    iso = 0.0
        else:
            with Image.open(percorso_raw) as im:
                try:
                    iso = float(im.getexif().get(34855, 0) or 0.0)
                except Exception:
                    iso = 0.0
                im = ImageOps.exif_transpose(im).convert("RGB")
                rgb = np.array(im)
        p["_iso"] = iso

        # 1b. Ridimensiona subito al lato lungo richiesto: tutta la pipeline
        # lavora sulla risoluzione finale, non su 24-60 MP inutili.
        max_dim = int(p.get("max_dim", 0) or 0)
        if max_dim > 0 and max(rgb.shape[0], rgb.shape[1]) > max_dim:
            pil_raw = Image.fromarray(rgb, "RGB")
            fattore = max_dim / float(max(pil_raw.size))
            nuova = (
                max(1, int(pil_raw.size[0] * fattore)),
                max(1, int(pil_raw.size[1] * fattore)),
            )
            rgb = np.asarray(pil_raw.resize(nuova, Image.Resampling.LANCZOS))
            nota(f"Ridimensionato a {nuova[0]}x{nuova[1]} px")

        img = rgb.astype(np.float32) / 255.0

        # 2. Pipeline fotografica (sulla risoluzione finale)
        img = cls._fase_tono(img, p)
        img = cls._fase_colore(img, p)
        img = cls._fase_dettaglio(img, p)
        img = cls._fase_lab(img, p)
        img = cls._fase_effetti(img, p)

        img_finale = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
        pil_img = Image.fromarray(img_finale, "RGB")

        # 2b. Miglioramento automatico dell'esposizione (BETA "Piu' luminosa")
        if p.get("auto_luminosita"):
            pil_img = cls.correggi_luminosita_auto(pil_img)
            nota("Bilanciamento automatico della luminosita' e vividezza applicati")

        # 4. Watermark: logo + testo
        posizione = p.get("watermark_posizione", "Basso a destra")
        if p.get("logo_path"):
            pil_img = cls.applica_logo(
                pil_img, p.get("logo_path"), float(p.get("logo_opacita", 0.55)), posizione
            )
        if p.get("watermark_attivo", True) and p.get("watermark_text"):
            pil_img = cls.applica_watermark_testo(
                pil_img,
                str(p.get("watermark_text")),
                int(p.get("font_size", 14)),
                posizione,
                float(p.get("watermark_opacita", 0.85)),
            )

        # 5. Salvataggio + EXIF
        cls._salva(pil_img, percorso_output, p)
        cls.preserva_exif(percorso_raw, percorso_output, bool(p.get("preserva_exif", True)))
        nota(f"Salvato: {os.path.basename(percorso_output)}")
        return percorso_output


# ================================================================================
# 3. CLOUD DISPATCHER MULTI-CANALE
# ================================================================================
class CloudDispatcher:
    @staticmethod
    def invia_telegram(file_path, token, chat_id, didascalia="Nuovo scatto elaborato"):
        if not token or not chat_id:
            return False
        try:
            with open(file_path, "rb") as f:
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendPhoto",
                    data={"chat_id": chat_id, "caption": didascalia},
                    files={"photo": f},
                    timeout=30,
                )
            if r.status_code == 200:
                logging.info("Telegram: invio completato.")
                return True
            logging.error("Telegram errore %s: %s", r.status_code, r.text[:200])
        except Exception as e:
            logging.error("Telegram eccezione: %s", e)
        return False

    @staticmethod
    def invia_dropbox(file_path, token):
        if not token:
            return False
        try:
            nome = "/" + os.path.basename(file_path)
            with open(file_path, "rb") as f:
                r = requests.post(
                    "https://content.dropboxapi.com/2/files/upload",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Dropbox-API-Arg": json.dumps({"path": nome, "mode": "add", "autorename": True}),
                        "Content-Type": "application/octet-stream",
                    },
                    data=f,
                    timeout=60,
                )
            if r.status_code == 200:
                logging.info("Dropbox: invio completato.")
                return True
            logging.error("Dropbox errore %s", r.status_code)
        except Exception as e:
            logging.error("Dropbox eccezione: %s", e)
        return False

    @staticmethod
    def invia_google_drive(file_path, credenziali):
        if not credenziali:
            return False
        logging.warning("Google Drive: canale non attivo in questa versione (%s).", file_path)
        return False

    @staticmethod
    def invia_meta_social(file_path, access_token, account_id, platform="instagram"):
        if not access_token or not account_id:
            return False
        logging.warning("Meta Graph API: canale non attivo in questa versione (%s).", platform)
        return False

    @staticmethod
    def invia_swisstransfer(file_path, email):
        if not email:
            return False
        logging.warning("SwissTransfer: canale non attivo in questa versione (%s).", file_path)
        return False

    @classmethod
    def dispatch(cls, file_path, p, callback=None):
        esiti = []
        if p.get("cloud_telegram"):
            ok = cls.invia_telegram(file_path, p.get("tg_token", ""), p.get("tg_chat_id", ""))
            esiti.append(("Telegram", ok))
        if p.get("cloud_dropbox"):
            ok = cls.invia_dropbox(file_path, p.get("dropbox_token", ""))
            esiti.append(("Dropbox", ok))
        if p.get("cloud_gdrive"):
            ok = cls.invia_google_drive(file_path, p.get("gdrive_key", ""))
            esiti.append(("Google Drive", ok))
        if p.get("cloud_meta"):
            ok = cls.invia_meta_social(file_path, p.get("meta_token", ""), p.get("meta_id", ""))
            esiti.append(("Meta", ok))
        if p.get("cloud_swiss"):
            ok = cls.invia_swisstransfer(file_path, p.get("swisstransfer_email", ""))
            esiti.append(("SwissTransfer", ok))

        if callback and esiti:
            callback("Cloud: " + ", ".join(f"{n}={'OK' if o else 'saltato'}" for n, o in esiti))
        return esiti


# ================================================================================
# 4. TETHERING WI-FI (WATCHDOG HOT-FOLDER)
# ================================================================================
class RawHotFolderHandler(FileSystemEventHandler):
    def __init__(self, parametri, callback_interfaccia, snapshot=None):
        self.parametri = normalizza_parametri(parametri)
        self.callback = callback_interfaccia
        self.estensioni = ESTENSIONI_ACCETTATE
        self._in_corso = set()
        self._lock = threading.Lock()

    def _notifica(self, msg):
        if self.callback:
            try:
                self.callback(msg)
            except Exception:
                pass

    def _accoda(self, percorso):
        if not percorso or not percorso.lower().endswith(self.estensioni):
            return
        # Non riprocessare i file prodotti dal programma stesso.
        if os.path.splitext(os.path.basename(percorso))[0].upper().endswith("_PRO"):
            return
        cartella_output = self.parametri.get("output_dir") or ""
        if cartella_output:
            try:
                if os.path.normcase(os.path.dirname(os.path.abspath(percorso))) == os.path.normcase(
                    os.path.abspath(cartella_output)
                ):
                    return
            except Exception:
                pass
        with self._lock:
            if percorso in self._in_corso:
                return
            self._in_corso.add(percorso)
        threading.Thread(target=self._elabora, args=(percorso,), daemon=True).start()

    def on_created(self, event):
        if not event.is_directory:
            self._accoda(event.src_path)

    def on_moved(self, event):
        # Alcune fotocamere scrivono un file temporaneo e poi lo rinominano.
        if not event.is_directory:
            self._accoda(event.dest_path)

    @staticmethod
    def _attendi_file(percorso, timeout=25.0):
        """Attende che il file abbia smesso di crescere (scrittura completata)."""
        inizio = time.time()
        ultima_dimensione = -1
        stabile = 0
        while time.time() - inizio < timeout:
            try:
                dimensione = os.path.getsize(percorso)
            except OSError:
                dimensione = -1
            if dimensione > 0 and dimensione == ultima_dimensione:
                stabile += 1
                if stabile >= 3:
                    return True
            else:
                stabile = 0
                ultima_dimensione = dimensione
            time.sleep(0.5)
        try:
            return os.path.getsize(percorso) > 0
        except OSError:
            return False

    def _elabora(self, percorso):
        try:
            self._notifica(f"Wi-Fi: rilevato {os.path.basename(percorso)}")
            self._attendi_file(percorso)

            p = normalizza_parametri(self.parametri)
            cartella_output = p.get("output_dir") or os.path.join(os.path.dirname(percorso), "Output_Ottimizzati")
            os.makedirs(cartella_output, exist_ok=True)

            est = FORMATI_OUTPUT.get(str(p.get("formato", "JPEG")).upper(), ".jpg")
            nome = os.path.splitext(os.path.basename(percorso))[0] + "_PRO" + est
            output = percorso_unico(os.path.join(cartella_output, nome))

            esito = _converti_file_worker((percorso, output, p))
            if not esito.get("ok"):
                raise RuntimeError(esito.get("errore", "conversione non riuscita"))
            CloudDispatcher.dispatch(output, p, callback=self._notifica)
            self._notifica(f"Wi-Fi: pronto {os.path.basename(output)}")
        except Exception as e:
            logging.error("Errore tethering: %s\n%s", e, traceback.format_exc())
            self._notifica(f"Errore tethering: {e}")
        finally:
            with self._lock:
                self._in_corso.discard(percorso)


# ================================================================================
# 5. SONY WI-FI (CAMERA REMOTE API)
# ================================================================================
class SonyWifiClient:
    """Client per la Sony Camera Remote API via Wi-Fi (app Smart Remote Control).

    La fotocamera crea una rete Wi-Fi (DIRECT-xxxx:ILCE-7S); il PC vi si collega
    e parla con l'API JSON su http://<ip>:10000/sony.
    """

    def __init__(self, callback=None):
        self.callback = callback
        self.base = None
        self.apis = []

    @staticmethod
    def indirizzi_locali():
        import socket

        trovati = []
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                ip = info[4][0]
                if ip and ip not in trovati and not ip.startswith("127."):
                    trovati.append(ip)
        except Exception:
            pass
        return trovati

    @staticmethod
    def tcp_aperto(host, porta=10000, timeout=2.0):
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, porta))
            return True
        except OSError:
            return False
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _log(self, messaggio):
        if self.callback:
            try:
                self.callback(messaggio)
            except Exception:
                pass

    def _api(self, servizio, metodo, parametri=None, versione="1.0"):
        import urllib.request

        if not self.base:
            raise RuntimeError("fotocamera non connessa")
        corpo = json.dumps(
            {
                "method": metodo,
                "params": parametri or [],
                "id": 1,
                "version": versione,
            }
        ).encode("utf-8")
        richiesta = urllib.request.Request(
            f"{self.base}/{servizio}",
            data=corpo,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(richiesta, timeout=8) as risposta:
            dati = json.loads(risposta.read().decode("utf-8", "ignore"))
        if "error" in dati:
            raise RuntimeError(f"{metodo}: {dati['error']}")
        return dati.get("result", [])

    def _base_da_descrizione(self, locazione):
        """Legge il file di descrizione SSDP e ricava l'URL reale dell'API.

        Modelli diversi usano porte diverse (10000, 8080, ...): non va mai
        dato per scontato il numero di porta.
        """
        import re
        import urllib.request

        try:
            with urllib.request.urlopen(locazione, timeout=8) as risposta:
                xml = risposta.read().decode("utf-8", "ignore")
        except Exception as errore:
            self._log(f"Sony: descrizione non leggibile ({errore})")
            return None
        trovato = re.search(
            r"<av:X_ScalarWebAPI_ActionList_URL>\s*([^<]+?)\s*</av:X_ScalarWebAPI_ActionList_URL>",
            xml,
        )
        if trovato:
            base = trovato.group(1).strip().rstrip("/")
            self._log(f"Sony: API dichiarata su {base}")
            return base
        return None

    def scopri(self, timeout=4.0):
        import socket
        import re

        messaggio = (
            "M-SEARCH * HTTP/1.1\r\n"
            "HOST: 239.255.255.250:1900\r\n"
            'MAN: "ssdp:discover"\r\n'
            "MX: 2\r\n"
            "ST: urn:schemas-sony-com:service:ScalarWebAPI:1\r\n"
            "\r\n"
        ).encode("ascii")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.8)
        try:
            sock.sendto(messaggio, ("239.255.255.250", 1900))
        except OSError as errore:
            self._log(f"Sony: invio SSDP fallito ({errore})")
            sock.close()
            return None
        scadenza = time.time() + timeout
        locazioni = []
        while time.time() < scadenza:
            try:
                dati, _ = sock.recvfrom(65507)
            except socket.timeout:
                continue
            testo = dati.decode("utf-8", "ignore")
            posizione = re.search(r"LOCATION:\s*(\S+)", testo, re.IGNORECASE)
            if posizione and posizione.group(1).strip() not in locazioni:
                locazioni.append(posizione.group(1).strip())
        sock.close()
        for locazione in locazioni:
            host = re.sub(r"^https?://([^/:]+).*$", r"\1", locazione)
            self._log(f"Sony: fotocamera trovata sull'IP {host}")
            base = self._base_da_descrizione(locazione)
            if base:
                self.base = base
                return base
            # Ripiego: stesso IP, porte note dell'API Sony
            for porta in (8080, 10000):
                candidato = f"http://{host}:{porta}/sony"
                if self.tcp_aperto(host, porta):
                    self.base = candidato
                    return candidato
        return None

    def _chiama(self, metodo, parametri=None, versione="1.0"):
        """Chiama un metodo provando i servizi disponibili (system, poi camera)."""
        ultimo_errore = None
        for servizio in ("system", "camera"):
            try:
                return self._api(servizio, metodo, parametri, versione)
            except Exception as errore:
                ultimo_errore = errore
        raise ultimo_errore

    def _estrai_url(self, dato):
        import re

        trovati = []

        def cammina(valore):
            if isinstance(valore, dict):
                for sotto in valore.values():
                    cammina(sotto)
            elif isinstance(valore, list):
                for sotto in valore:
                    cammina(sotto)
            elif isinstance(valore, str):
                if valore.startswith("http") and re.search(
                    r"\.(jpe?g|arw|png|tiff?)(\?|$)", valore, re.IGNORECASE
                ):
                    trovati.append(valore)

        cammina(dato)
        return trovati

    def connetti(self):
        base = None
        try:
            base = self.scopri()
        except Exception as errore:
            self._log(f"Sony: ricerca SSDP non riuscita ({errore})")
        if not base:
            # Ripiego: indirizzo tipico della fotocamera in modalita' Smart Remote
            for porta in (8080, 10000):
                if self.tcp_aperto("192.168.122.1", porta):
                    self.base = f"http://192.168.122.1:{porta}/sony"
                    base = self.base
                    self._log(f"Sony: uso l'indirizzo {base}")
                    break
        if not base:
            raise RuntimeError(
                "fotocamera non raggiungibile. Il PC non sembra collegato al Wi-Fi "
                "della fotocamera (IP atteso 192.168.122.x). Apri 'Smart Remote Control' "
                "sulla A7S e collegati alla rete DIRECT-xxxx:ILCE-7S."
            )

        elenco = self._chiama("getAvailableApiList")
        self.apis = elenco[0] if elenco and isinstance(elenco[0], list) else []
        if not self.apis:
            self.apis = []
        try:
            info = self._chiama("getApplicationInfo")
            self._log(f"Sony: connesso ({info[0] if info else 'ok'})")
        except Exception as errore:
            self._log(f"Sony: info non disponibile ({errore})")

        if self.assicura_scatto():
            self._log("Sony: fotocamera pronta (scatto disponibile)")
        else:
            self._log(
                "Sony: connessa, ma la fotocamera non e' in modalita' remota. "
                "Apri Smart Remote Control sulla A7S e premi di nuovo CONNETTI."
            )
        return self.apis

    def _prova_modalita_remota(self, secondi):
        """Avvia la modalita' remota e attende che lo scatto sia disponibile."""
        try:
            self._chiama("startRecMode")
        except Exception as errore:
            self._log(f"Sony: startRecMode non riuscito ({errore})")
        for indice in range(secondi):
            time.sleep(1.0)
            try:
                elenco = self._chiama("getAvailableApiList")
            except Exception:
                continue
            self.apis = elenco[0] if elenco and isinstance(elenco[0], list) else []
            if "actTakePicture" in self.apis:
                return True
            if indice == 4:
                self._log("Sony: la fotocamera sta attivando la modalita' remota...")
        return False

    def assicura_scatto(self, tentativi=15):
        """Rende la fotocamera pronta per lo scatto remoto.

        Alcune Sony (A7S compresa) restano in uno stato intermedio in cui
        l'API risponde ma lo scatto non e' disponibile: in quel caso serve
        un ciclo stopRecMode/startRecMode.
        """
        if "actTakePicture" in self.apis:
            return True
        if self._prova_modalita_remota(tentativi):
            return True
        self._log("Sony: reset della modalita' remota...")
        try:
            self._chiama("stopRecMode")
        except Exception as errore:
            self._log(f"Sony: stopRecMode non riuscito ({errore})")
        time.sleep(3)
        return self._prova_modalita_remota(20)

    def _scarica(self, indirizzo, cartella):
        import urllib.request

        nome = os.path.basename(indirizzo.split("?")[0]) or f"sony_{int(time.time())}.jpg"
        destinazione = percorso_unico(os.path.join(cartella, nome))
        with urllib.request.urlopen(indirizzo, timeout=60) as risposta, open(destinazione, "wb") as uscita:
            uscita.write(risposta.read())
        self._log(f"Sony: scaricato {nome}")
        return destinazione

    def scatta_e_scarica(self, cartella):
        os.makedirs(cartella, exist_ok=True)
        if not self.assicura_scatto():
            raise RuntimeError(
                "la fotocamera non e' in modalita' remota. Apri 'Smart Remote Control' "
                "sulla A7S e riprova."
            )
        risultato = self._api("camera", "actTakePicture")
        url = self._estrai_url(risultato)
        if not url:
            # Alcuni modelli restituiscono lo scatto tramite getEvent
            for _ in range(10):
                time.sleep(1.0)
                eventi = self._api("camera", "getEvent", [True])
                url = self._estrai_url(eventi)
                if url:
                    break
        if not url:
            raise RuntimeError("la fotocamera non ha restituito alcuna immagine")
        return [self._scarica(indirizzo, cartella) for indirizzo in url if isinstance(indirizzo, str)]


# ================================================================================
# 6. INTERFACCIA GRAFICA (CUSTOMTKINTER)
# ================================================================================
class FranchettiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.geometry("1000x700+16+16")
        self.minsize(880, 560)

        self.parametri = parametri_default()
        self.observer = None
        self._sony = None
        self._cancel_event = threading.Event()
        self._batch_files = []
        self._batch_attivo = False
        self._slider_widgets = {}
        self._grana_precedente = (0.0, 0.0, 1.0, 1.5)
        self._ultima_cartella = os.path.expanduser("~")
        self._coda = queue.Queue()

        self._crea_interfaccia()
        self.protocol("WM_DELETE_WINDOW", self._chiudi_app)
        # Dopo il mapping della finestra normalizza lo scaling DPI: nell'exe
        # PyInstaller il fattore 125% può essere applicato due volte e tagliare
        # la parte destra dell'interfaccia.
        self.after(300, self._sincronizza_scaling)
        # Se il PC e' gia' collegato al Wi-Fi della Sony, prova a connettersi
        # da solo: l'utente trova la fotocamera gia' pronta.
        self.after(2000, self._auto_connetti_sony)

    def _auto_connetti_sony(self):
        try:
            if any(ip.startswith("192.168.122.") for ip in SonyWifiClient.indirizzi_locali()):
                self.connetti_sony()
        except Exception:
            pass

    def _sincronizza_scaling(self):
        self._applica_geometria()
        # CTk ripristina la geometria dopo il cambio di scaling: riapplichiamo
        # la dimensione corretta per sicurezza.
        self.after(1200, self._applica_geometria)
        self.after(2500, self._applica_geometria)

    def _applica_geometria(self):
        """Adatta la finestra all'area di lavoro di Windows (senza taskbar)."""
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = ctypes.windll.user32.FindWindowW(None, self.title())
            if not hwnd:
                return
            area = wintypes.RECT()
            # SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(
                0x0030, 0, ctypes.byref(area), 0
            ):
                x = area.left + 4
                y = area.top + 4
                larghezza = (area.right - area.left) - 8
                altezza = (area.bottom - area.top) - 8
            else:
                larghezza = max(900, self.winfo_screenwidth() - 40)
                altezza = max(600, self.winfo_screenheight() - 80)
                x, y = 6, 6
            # SWP_NOZORDER = 0x0004 | SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                hwnd, 0, x, y, larghezza, altezza, 0x0014
            )
        except Exception:
            pass

    # ---------------------------------------------------------------- layout
    def _crea_interfaccia(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # HEADER
        header = ctk.CTkFrame(self, corner_radius=0, height=58)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(
            header,
            text="FRANCHETTI RAW CONVERTER PRO",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=(20, 6), pady=10, sticky="w")
        ctk.CTkLabel(
            header,
            text="Ogni recensione positiva aiuta lo sviluppo del programma - grazie!",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
        ).grid(row=0, column=1, padx=(0, 14), pady=(22, 4), sticky="w")
        ctk.CTkLabel(
            header,
            text=f"v{APP_VERSION}  |  LibRaw  |  Multi-core  |  Tethering & Cloud",
            font=ctk.CTkFont(size=10),
            text_color="#8ab4f8",
        ).grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=12, pady=(6, 4), sticky="nsew")
        for nome in ("Batch", "Sviluppo RAW", "Tethering & Cloud", "Log"):
            self.tabview.add(nome)

        self._costruisci_tab_batch(self.tabview.tab("Batch"))
        self._costruisci_tab_sviluppo(self.tabview.tab("Sviluppo RAW"))
        self._costruisci_tab_tethering(self.tabview.tab("Tethering & Cloud"))
        self._costruisci_tab_log(self.tabview.tab("Log"))

        # STATUS BAR
        status = ctk.CTkFrame(self, corner_radius=0, height=30)
        status.grid(row=2, column=0, sticky="ew")
        status.grid_columnconfigure(1, weight=1)
        self.lbl_stato = ctk.CTkLabel(status, text="Pronto", font=ctk.CTkFont(size=11))
        self.lbl_stato.grid(row=0, column=0, padx=15, pady=4, sticky="w")
        self.lbl_path_stato = ctk.CTkLabel(status, text="", font=ctk.CTkFont(size=11), text_color="#9aa0a6")
        self.lbl_path_stato.grid(row=0, column=1, padx=15, pady=4, sticky="e")

        self.scrivi_log("Sistema pronto. Seleziona i file RAW e configura le opzioni di conversione.")
        self.after(120, self._processa_coda)

    def _processa_coda(self):
        """Svuota la coda di messaggi provenienti dai thread di lavoro (thread-safe)."""
        try:
            while True:
                messaggio = self._coda.get_nowait()
                tipo = messaggio[0]
                if tipo == "log":
                    self.scrivi_log(messaggio[1])
                elif tipo == "progress":
                    self._aggiorna_progresso(*messaggio[1:])
                elif tipo == "done":
                    self._fine_batch(*messaggio[1:])
        except queue.Empty:
            pass
        except Exception:
            pass
        try:
            self.after(120, self._processa_coda)
        except Exception:
            pass

    # ------------------------------------------------------------ tab BATCH
    def _costruisci_tab_batch(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(False)

        # Due colonne affiancate: tutte le impostazioni restano visibili senza
        # scorrimento anche su schermi 1366x768 e con scaling di Windows.
        contenuto = ctk.CTkFrame(tab, fg_color="transparent")
        contenuto.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        contenuto.grid_columnconfigure(0, weight=1, uniform="batch")
        contenuto.grid_columnconfigure(1, weight=1, uniform="batch")
        contenuto.grid_rowconfigure(0, weight=1)

        # ================= BLOCCO SORGENTE / DESTINAZIONE / DIMENSIONI =================
        sx = ctk.CTkFrame(contenuto, fg_color="transparent")
        sx.grid(row=0, column=0, padx=(4, 8), pady=2, sticky="nsew")
        sx.grid_columnconfigure(1, weight=1)

        r = 0
        ctk.CTkLabel(sx, text="SORGENTE", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=3, padx=6, pady=(3, 1), sticky="w"
        ); r += 1

        ctk.CTkLabel(sx, text="File / Cartella:").grid(row=r, column=0, padx=6, pady=3, sticky="w")
        self.entry_sorgente = ctk.CTkEntry(sx, placeholder_text="Cartella oppure file RAW multipli...")
        self.entry_sorgente.grid(row=r, column=1, columnspan=2, padx=6, pady=3, sticky="ew")
        r += 1

        btn_row = ctk.CTkFrame(sx, fg_color="transparent")
        btn_row.grid(row=r, column=0, columnspan=3, padx=6, pady=2, sticky="ew")
        ctk.CTkButton(btn_row, text="Seleziona cartella", width=140,
                      command=self.seleziona_cartella_sorgente).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Seleziona file RAW", width=140,
                      command=self.seleziona_file_sorgente).pack(side="left", padx=(0, 6))
        self.chk_ricorsivo = ctk.CTkCheckBox(btn_row, text="Sottocartelle")
        self.chk_ricorsivo.select()
        self.chk_ricorsivo.pack(side="left", padx=4)
        r += 1

        ctk.CTkLabel(sx, text="DESTINAZIONE", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=3, padx=6, pady=(3, 1), sticky="w"
        ); r += 1

        ctk.CTkLabel(sx, text="Cartella output:").grid(row=r, column=0, padx=6, pady=3, sticky="w")
        self.entry_destinazione = ctk.CTkEntry(sx, placeholder_text="Cartella di destinazione...")
        self.entry_destinazione.grid(row=r, column=1, padx=6, pady=3, sticky="ew")
        ctk.CTkButton(sx, text="Sfoglia", width=90,
                      command=self.seleziona_cartella_destinazione).grid(row=r, column=2, padx=6, pady=3)
        r += 1

        ctk.CTkLabel(sx, text="DIMENSIONI E FORMATO", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=3, padx=6, pady=(3, 1), sticky="w"
        ); r += 1

        dim = ctk.CTkFrame(sx)
        dim.grid(row=r, column=0, columnspan=3, padx=6, pady=2, sticky="ew")
        dim.grid_columnconfigure(1, weight=1)
        dim.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(dim, text="Lato max (px)").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.entry_max_dim = ctk.CTkEntry(dim, width=90)
        self.entry_max_dim.insert(0, "1920")
        self.entry_max_dim.grid(row=0, column=1, padx=6, pady=2, sticky="w")
        self.entry_max_dim.bind("<KeyRelease>", self._aggiorna_evidenzia_da_campo)
        ctk.CTkLabel(dim, text="misura pronta o valore (0 = originale)",
                     font=ctk.CTkFont(size=10), text_color="#9aa0a6").grid(
            row=0, column=2, columnspan=2, padx=6, sticky="w"
        )

        # Misure pronte in ordine crescente: un clic imposta il lato lungo.
        self._misure_pronte = [640, 800, 1024, 1200, 1600, 1920, 2048, 2560, 3000, 4000, 6000, 0]
        self.frame_misure = ctk.CTkFrame(dim, fg_color="transparent")
        self.frame_misure.grid(row=1, column=0, columnspan=4, padx=6, pady=(0, 2), sticky="w")
        self._bottoni_misure = []
        for indice, valore in enumerate(self._misure_pronte):
            testo = "Originale" if valore == 0 else f"{valore}"
            bottone = ctk.CTkButton(
                self.frame_misure,
                text=testo,
                width=74,
                height=26,
                font=ctk.CTkFont(size=11),
                fg_color="#3a3f45",
                hover_color="#4a5158",
                command=lambda v=valore: self._imposta_max_dim(v),
            )
            # Sei misure per riga: restano dentro la colonna anche a 1024 px.
            bottone.grid(row=indice // 6, column=indice % 6, padx=2, pady=2)
            self._bottoni_misure.append((valore, bottone))
        self._evidenzia_max_dim(1920)

        ctk.CTkLabel(dim, text="Qualità").grid(row=2, column=0, padx=6, pady=4, sticky="w")
        self.entry_qualita = ctk.CTkEntry(dim, width=80)
        self.entry_qualita.insert(0, "90")
        self.entry_qualita.grid(row=2, column=1, padx=6, pady=2, sticky="w")

        ctk.CTkLabel(dim, text="Formato").grid(row=2, column=2, padx=6, pady=4, sticky="e")
        self.combo_formato = ctk.CTkComboBox(
            dim, values=list(FORMATI_OUTPUT.keys()), width=110,
            command=lambda v: self.parametri.__setitem__("formato", v),
        )
        self.combo_formato.set("JPEG")
        self.combo_formato.grid(row=2, column=3, padx=6, pady=2, sticky="w")

        ctk.CTkLabel(dim, text="Spazio colore").grid(row=3, column=0, padx=6, pady=4, sticky="w")
        self.combo_spazio = ctk.CTkComboBox(
            dim, values=["sRGB"], width=140,
            command=lambda v: self.parametri.__setitem__("profilo_colore", v),
        )
        self.combo_spazio.set("sRGB")
        # Disabilitato dopo il set: cosi' il valore resta sempre leggibile.
        self.combo_spazio.configure(state="disabled")
        self.combo_spazio.grid(row=3, column=1, padx=6, pady=2, sticky="w")

        self.chk_wb_camera = ctk.CTkCheckBox(dim, text="WB fotocamera")
        self.chk_wb_camera.select()
        self.chk_wb_camera.grid(row=3, column=2, columnspan=2, padx=6, pady=2, sticky="w")

        self.chk_exif = ctk.CTkCheckBox(dim, text="Preserva EXIF")
        self.chk_exif.select()
        self.chk_exif.grid(row=4, column=0, columnspan=2, padx=6, pady=2, sticky="w")

        # Miglioramento automatico dell'esposizione (BETA)
        self.sw_auto_luminosita = ctk.CTkSwitch(
            dim,
            text="PIÙ LUMINOSA (BETA)",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._toggle_auto_luminosita(self.sw_auto_luminosita.get()),
        )
        self.sw_auto_luminosita.grid(row=5, column=0, columnspan=2, padx=6, pady=(4, 1), sticky="w")

        # Elaborazione su tutti i core del processore
        self.chk_multicore = ctk.CTkCheckBox(
            dim,
            text=f"USA TUTTI I CORE ({os.cpu_count() or 1} processi)",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.chk_multicore.select()
        self.chk_multicore.grid(row=6, column=0, columnspan=2, padx=6, pady=(4, 1), sticky="w")

        # ================= BLOCCO NOMI / WATERMARK / PRESET =================
        dx = ctk.CTkFrame(contenuto, fg_color="transparent")
        dx.grid(row=0, column=1, padx=(8, 4), pady=2, sticky="nsew")
        dx.grid_columnconfigure(1, weight=1)

        r = 0
        ctk.CTkLabel(dx, text="NOMI FILE E SOVRASCRITTURA",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=6, pady=(3, 1), sticky="w"
        ); r += 1

        self.chk_mantieni_nomi = ctk.CTkCheckBox(dx, text="Mantieni nome originale")
        self.chk_mantieni_nomi.select()
        self.chk_mantieni_nomi.grid(row=r, column=0, columnspan=2, padx=6, pady=3, sticky="w")
        r += 1

        nomi = ctk.CTkFrame(dx)
        nomi.grid(row=r, column=0, columnspan=2, padx=6, pady=2, sticky="ew")
        nomi.grid_columnconfigure(1, weight=1)
        nomi.grid_columnconfigure(3, weight=1)
        r += 1

        ctk.CTkLabel(nomi, text="Prefisso:").grid(row=0, column=0, padx=(6, 2), pady=3, sticky="w")
        self.entry_prefisso = ctk.CTkEntry(nomi, width=90, placeholder_text="FRC_")
        self.entry_prefisso.grid(row=0, column=1, padx=(0, 6), pady=3, sticky="ew")

        ctk.CTkLabel(nomi, text="Suffisso:").grid(row=0, column=2, padx=(6, 2), pady=3, sticky="w")
        self.entry_suffisso = ctk.CTkEntry(nomi, width=90, placeholder_text="_web")
        self.entry_suffisso.grid(row=0, column=3, padx=(0, 6), pady=3, sticky="ew")

        ctk.CTkLabel(nomi, text="Se esiste:").grid(row=1, column=0, padx=(6, 2), pady=3, sticky="w")
        self.combo_sovrascrittura = ctk.CTkComboBox(
            nomi, values=["Rinomina", "Sovrascrivi", "Salta"], width=150,
            command=lambda v: self.parametri.__setitem__("sovrascrittura", v),
        )
        self.combo_sovrascrittura.set("Rinomina")
        self.combo_sovrascrittura.grid(row=1, column=1, columnspan=3, padx=(0, 6), pady=3, sticky="w")

        ctk.CTkLabel(dx, text="WATERMARK", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=6, pady=(3, 1), sticky="w"
        ); r += 1

        self.chk_watermark = ctk.CTkCheckBox(dx, text="Applica testo")
        self.chk_watermark.select()
        self.chk_watermark.grid(row=r, column=0, columnspan=2, padx=6, pady=3, sticky="w")
        r += 1

        self.entry_watermark = ctk.CTkEntry(dx, placeholder_text="Testo watermark")
        self.entry_watermark.insert(0, self.parametri["watermark_text"])
        self.entry_watermark.grid(row=r, column=0, columnspan=2, padx=6, pady=3, sticky="ew")
        r += 1

        wm = ctk.CTkFrame(dx)
        wm.grid(row=r, column=0, columnspan=2, padx=6, pady=2, sticky="ew")
        wm.grid_columnconfigure(1, weight=1)
        wm.grid_columnconfigure(3, weight=1)
        r += 1

        ctk.CTkLabel(wm, text="Font (px):").grid(row=0, column=0, padx=(6, 2), pady=3, sticky="w")
        self.entry_font_size = ctk.CTkEntry(wm, width=70)
        self.entry_font_size.insert(0, "14")
        self.entry_font_size.grid(row=0, column=1, padx=(0, 6), pady=3, sticky="w")

        ctk.CTkLabel(wm, text="Posizione:").grid(row=0, column=2, padx=(10, 4), pady=3, sticky="w")
        self.combo_posizione = ctk.CTkComboBox(
            wm,
            values=["Basso a destra", "Basso a sinistra", "Alto a destra", "Alto a sinistra", "Centro"],
            width=150,
            command=lambda v: self.parametri.__setitem__("watermark_posizione", v),
        )
        self.combo_posizione.set("Basso a destra")
        self.combo_posizione.grid(row=0, column=3, padx=(0, 6), pady=3, sticky="w")

        ctk.CTkLabel(wm, text="Logo PNG:").grid(row=1, column=0, padx=(6, 2), pady=3, sticky="w")
        self.lbl_logo = ctk.CTkLabel(wm, text="Nessun logo", anchor="w", text_color="#9aa0a6")
        self.lbl_logo.grid(row=1, column=1, padx=(0, 6), pady=3, sticky="ew")
        ctk.CTkButton(wm, text="Carica", width=90, command=self.seleziona_logo).grid(
            row=1, column=2, columnspan=2, padx=(0, 6), pady=3, sticky="w"
        )

        ctk.CTkLabel(dx, text="PRESET E CONFIGURAZIONE",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=6, pady=(3, 1), sticky="w"
        ); r += 1

        self.combo_preset = ctk.CTkComboBox(
            dx,
            values=["Personalizzato", "Web / Social", "Stampa Fine Art", "Archivio JPEG",
                    "Ritratto", "Paesaggio", "Bianco e Nero"],
            width=190,
            command=self.applica_preset,
        )
        self.combo_preset.set("Personalizzato")
        self.combo_preset.grid(row=r, column=0, padx=6, pady=3, sticky="w")
        r += 1

        cfg = ctk.CTkFrame(dx, fg_color="transparent")
        cfg.grid(row=r, column=0, columnspan=2, padx=6, pady=2, sticky="ew")
        ctk.CTkButton(cfg, text="Salva config", width=130,
                      command=self.salva_configurazione).pack(side="left", padx=(0, 6))
        ctk.CTkButton(cfg, text="Carica config", width=130,
                      command=self.carica_configurazione).pack(side="left")

        # ---- azioni (sempre visibili in basso)
        azioni = ctk.CTkFrame(tab, fg_color="transparent")
        azioni.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 8))
        azioni.grid_columnconfigure(2, weight=1)

        self.btn_avvia = ctk.CTkButton(
            azioni, text="AVVIA CONVERSIONE BATCH", height=42, width=240,
            fg_color="#1f7a3d", hover_color="#258c47",
            font=ctk.CTkFont(size=14, weight="bold"), command=self.avvia_batch,
        )
        self.btn_avvia.grid(row=0, column=0, padx=(4, 8), pady=6)

        self.btn_annulla = ctk.CTkButton(
            azioni, text="ANNULLA", height=42, width=130, fg_color="#a32a2a", hover_color="#bf3333",
            state="disabled", command=self.annulla_batch,
        )
        self.btn_annulla.grid(row=0, column=1, padx=4, pady=6)

        self.btn_rimuovi_grana = ctk.CTkButton(
            azioni,
            text="RIMUOVI GRANA (AUTO ISO)",
            height=42,
            width=210,
            fg_color="#6a4c93",
            hover_color="#7e5aa8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_rimuovi_grana,
        )
        self.btn_rimuovi_grana.grid(row=0, column=2, padx=(10, 4), pady=6, sticky="w")

        self.progress = ctk.CTkProgressBar(azioni)
        self.progress.grid(row=1, column=0, columnspan=3, padx=4, pady=(2, 4), sticky="ew")
        self.progress.set(0)

        self.lbl_progresso = ctk.CTkLabel(azioni, text="In attesa", font=ctk.CTkFont(size=12))
        self.lbl_progresso.grid(row=2, column=0, columnspan=2, padx=4, pady=(0, 4), sticky="w")

        ctk.CTkButton(azioni, text="Apri cartella output", width=170, command=self.apri_cartella_output).grid(
            row=2, column=2, padx=4, pady=(0, 4), sticky="e"
        )

    # -------------------------------------------------------- tab SVILUPPO
    def _costruisci_tab_sviluppo(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(False)

        scroll = ctk.CTkScrollableFrame(tab, label_text="Correzioni colore e sviluppo", height=320)
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(0, weight=1)

        card_auto = ctk.CTkFrame(scroll)
        card_auto.pack(fill="x", padx=6, pady=(6, 2))
        self.sw_auto_sviluppo = ctk.CTkSwitch(
            card_auto,
            text="PIÙ LUMINOSA (BETA) - sistema automaticamente foto scure e troppo esposte",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._toggle_auto_luminosita(self.sw_auto_sviluppo.get()),
        )
        self.sw_auto_sviluppo.pack(padx=10, pady=10, anchor="w")

        sezioni = [
            ("ESPOSIZIONE E BILANCIAMENTO", [
                ("esposizione", "Esposizione (EV)", -3.0, 3.0, 0.0, "{:+.2f}"),
                ("temperatura", "Temperatura", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("tinta", "Tinta (verde/magenta)", -100.0, 100.0, 0.0, "{:+.0f}"),
            ]),
            ("TONI", [
                ("luci", "Luci", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("ombre", "Ombre", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("bianchi", "Bianchi", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("neri", "Neri", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("contrasto", "Contrasto (curva sigmoide)", 0.0, 1.0, 0.35, "{:.2f}"),
            ]),
            ("COLORE", [
                ("vivacita", "Vivacità selettiva", 0.0, 1.0, 0.35, "{:.2f}"),
                ("saturazione", "Saturazione", 0.0, 2.0, 1.0, "{:.2f}"),
                ("hsl_rosso", "Saturazione rossi", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("hsl_verde", "Saturazione verdi", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("hsl_blu", "Saturazione blu", -100.0, 100.0, 0.0, "{:+.0f}"),
            ]),
            ("DETTAGLIO E NITIDEZZA", [
                ("chiarezza", "Chiarezza (micro-contrasto)", 0.0, 1.0, 0.0, "{:.2f}"),
                ("dehaze", "Dehaze (rimozione velo)", 0.0, 1.0, 0.0, "{:.2f}"),
                ("nitidezza_quantita", "Nitidezza (quantità)", 0.0, 5.0, 1.0, "{:.2f}"),
                ("nitidezza_raggio", "Nitidezza (raggio)", 0.5, 4.0, 1.5, "{:.1f}"),
                ("nr_luminanza", "Riduzione rumore luminanza", 0.0, 100.0, 0.0, "{:.0f}"),
                ("nr_colore", "Riduzione rumore colore", 0.0, 100.0, 0.0, "{:.0f}"),
            ]),
            ("EFFETTI", [
                ("vignettatura", "Vignettatura (- scura / + schiarisci)", -100.0, 100.0, 0.0, "{:+.0f}"),
                ("grana", "Grana", 0.0, 100.0, 0.0, "{:.0f}"),
            ]),
        ]

        for titolo, sliders in sezioni:
            card = ctk.CTkFrame(scroll)
            card.pack(fill="x", padx=6, pady=6)
            card.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(card, text=titolo, font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=0, column=0, columnspan=3, padx=10, pady=(8, 4), sticky="w"
            )
            for idx, (chiave, etichetta, minimo, massimo, default, fmt) in enumerate(sliders, start=1):
                self._crea_slider(card, idx, chiave, etichetta, minimo, massimo, default, fmt)
            if titolo == "DETTAGLIO E NITIDEZZA":
                self.btn_rimuovi_grana_sviluppo = ctk.CTkButton(
                    card,
                    text="RIMUOVI GRANA (AUTO ISO)",
                    height=30,
                    fg_color="#6a4c93",
                    hover_color="#7e5aa8",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    command=self.toggle_rimuovi_grana,
                )
                self.btn_rimuovi_grana_sviluppo.grid(
                    row=len(sliders) + 1, column=0, columnspan=3,
                    padx=10, pady=(8, 10), sticky="ew",
                )

        # curva tonale + split toning
        card2 = ctk.CTkFrame(scroll)
        card2.pack(fill="x", padx=6, pady=6)
        card2.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card2, text="CURVA TONALE E SPLIT TONING", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=10, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(card2, text="Curva tonale:").grid(row=1, column=0, padx=10, pady=4, sticky="w")
        self.combo_curva = ctk.CTkComboBox(
            card2, values=["Lineare", "Media", "Forte", "Contrasto Alto", "Schiarisci", "Scurisci"],
            width=170, command=lambda v: self.parametri.__setitem__("curva_tonale", v),
        )
        self.combo_curva.set("Lineare")
        self.combo_curva.grid(row=1, column=1, padx=10, pady=4, sticky="w")

        self._crea_slider(card2, 2, "intensita_ombre", "Split toning ombre (intensità)", 0.0, 100.0, 0.0, "{:.0f}")
        self.entry_colore_ombre = self._crea_entry_colore(card2, 3, "Colore ombre", "#2b4c7e", "colore_ombre")
        self._crea_slider(card2, 4, "intensita_luci", "Split toning luci (intensità)", 0.0, 100.0, 0.0, "{:.0f}")
        self.entry_colore_luci = self._crea_entry_colore(card2, 5, "Colore luci", "#e0b070", "colore_luci")

        reset = ctk.CTkButton(scroll, text="Ripristina tutti i parametri di sviluppo", command=self.ripristina_sviluppo)
        reset.pack(pady=12)

    def _crea_slider(self, parent, riga, chiave, etichetta, minimo, massimo, default, fmt):
        ctk.CTkLabel(parent, text=etichetta).grid(row=riga, column=0, padx=10, pady=2, sticky="w")
        slider = ctk.CTkSlider(parent, from_=minimo, to=massimo,
                               command=lambda v, k=chiave: self._on_slider(k, v))
        slider.set(default)
        slider.grid(row=riga, column=1, padx=10, pady=2, sticky="ew")
        valore = ctk.CTkLabel(parent, text=fmt.format(default), width=60)
        valore.grid(row=riga, column=2, padx=10, pady=2, sticky="e")
        self._slider_widgets[chiave] = (slider, valore, fmt)
        self.parametri[chiave] = default
        return slider

    def _crea_entry_colore(self, parent, riga, etichetta, default, chiave):
        ctk.CTkLabel(parent, text=etichetta).grid(row=riga, column=0, padx=10, pady=2, sticky="w")
        entry = ctk.CTkEntry(parent, width=110)
        entry.insert(0, default)
        entry.grid(row=riga, column=1, padx=10, pady=2, sticky="w")
        entry.bind("<KeyRelease>", lambda e, k=chiave, w=entry: self.parametri.__setitem__(k, w.get().strip()))
        self.parametri[chiave] = default
        return entry

    def _on_slider(self, chiave, valore):
        self.parametri[chiave] = float(valore)
        if chiave in self._slider_widgets:
            _, label, fmt = self._slider_widgets[chiave]
            label.configure(text=fmt.format(float(valore)))
        if chiave in ("nr_luminanza", "nr_colore"):
            if (
                self.parametri.get("rimuovi_grana_auto")
                and float(self.parametri.get("nr_luminanza", 0.0)) <= 0.0
                and float(self.parametri.get("nr_colore", 0.0)) <= 0.0
            ):
                self.parametri["rimuovi_grana_auto"] = False
            self._aggiorna_stato_grana()

    def _imposta_parametro_slider(self, chiave, valore):
        """Aggiorna slider, etichetta e parametro in un solo passaggio."""
        valore = float(valore)
        self.parametri[chiave] = valore
        if chiave in self._slider_widgets:
            slider, label, fmt = self._slider_widgets[chiave]
            slider.set(valore)
            label.configure(text=fmt.format(valore))

    def toggle_rimuovi_grana(self):
        """Preset intelligente: denoise ISO con dettaglio, contrasto e nitidezza."""
        attivo = bool(self.parametri.get("rimuovi_grana_auto", False))
        if attivo:
            nrl, nrc, nit, raggio = self._grana_precedente
            self._imposta_parametro_slider("nr_luminanza", nrl)
            self._imposta_parametro_slider("nr_colore", nrc)
            self._imposta_parametro_slider("nitidezza_quantita", nit)
            self._imposta_parametro_slider("nitidezza_raggio", raggio)
            self.parametri["rimuovi_grana_auto"] = False
        else:
            self._grana_precedente = (
                float(self.parametri.get("nr_luminanza", 0.0)),
                float(self.parametri.get("nr_colore", 0.0)),
                float(self.parametri.get("nitidezza_quantita", 1.0)),
                float(self.parametri.get("nitidezza_raggio", 1.5)),
            )
            self._imposta_parametro_slider("nr_luminanza", 60.0)
            self._imposta_parametro_slider("nr_colore", 70.0)
            self._imposta_parametro_slider(
                "nitidezza_quantita",
                max(float(self.parametri.get("nitidezza_quantita", 1.0)), 1.25),
            )
            self._imposta_parametro_slider("nitidezza_raggio", 1.2)
            self.parametri["rimuovi_grana_auto"] = True
        self._aggiorna_stato_grana()

    def _aggiorna_stato_grana(self):
        attivo = bool(self.parametri.get("rimuovi_grana_auto", False))
        testo = "GRANA RIMOSSA (AUTO ISO) ✓" if attivo else "RIMUOVI GRANA (AUTO ISO)"
        colore = "#1f7a3d" if attivo else "#6a4c93"
        hover = "#258c47" if attivo else "#7e5aa8"
        for nome in ("btn_rimuovi_grana", "btn_rimuovi_grana_sviluppo"):
            bottone = getattr(self, nome, None)
            if bottone is None:
                continue
            try:
                bottone.configure(text=testo, fg_color=colore, hover_color=hover)
            except Exception:
                pass

    def ripristina_sviluppo(self):
        for chiave, (slider, label, fmt) in self._slider_widgets.items():
            default = parametri_default()[chiave]
            slider.set(default)
            label.configure(text=fmt.format(default))
            self.parametri[chiave] = default
        self.parametri["rimuovi_grana_auto"] = False
        self._grana_precedente = (0.0, 0.0, 1.0, 1.5)
        self._aggiorna_stato_grana()
        self.combo_curva.set("Lineare")
        self.parametri["curva_tonale"] = "Lineare"
        self.scrivi_log("Parametri di sviluppo ripristinati ai valori di default.")

    # ------------------------------------------------------ tab TETHERING
    def _costruisci_tab_tethering(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(False)

        scroll = ctk.CTkScrollableFrame(tab, label_text="Tethering Wi-Fi e distribuzione Cloud", height=320)
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(scroll, text="SONY WI-FI - SMART REMOTE CONTROL", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=8, pady=(8, 2), sticky="w"
        )
        ctk.CTkLabel(
            scroll,
            text=(
                "1) Sulla A7S apri l'app 'Smart Remote Control' (PlayMemories Camera Apps).\n"
                "2) Collega il PC alla rete Wi-Fi della fotocamera (DIRECT-xxxx:ILCE-7S).\n"
                "3) Premi CONNETTI FOTOCAMERA, poi SCATTA E SCARICA.\n"
                "La fotocamera non invia da sola le foto al PC: e' il programma a comandarla."
            ),
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#9aa0a6",
        ).grid(row=1, column=0, columnspan=3, padx=8, pady=(0, 4), sticky="w")

        self.lbl_sony = ctk.CTkLabel(scroll, text="Fotocamera non connessa", text_color="#ffb74d")
        self.lbl_sony.grid(row=2, column=0, columnspan=3, padx=8, pady=2, sticky="w")

        riga_sony = ctk.CTkFrame(scroll, fg_color="transparent")
        riga_sony.grid(row=3, column=0, columnspan=3, padx=8, pady=(2, 10), sticky="ew")
        riga_sony.grid_columnconfigure(0, weight=1)
        riga_sony.grid_columnconfigure(1, weight=1)
        riga_sony.grid_columnconfigure(2, weight=1)
        self.btn_sony_connetti = ctk.CTkButton(
            riga_sony, text="CONNETTI FOTOCAMERA", height=36, command=self.connetti_sony
        )
        self.btn_sony_connetti.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.btn_sony_diagnosi = ctk.CTkButton(
            riga_sony,
            text="DIAGNOSI",
            height=36,
            width=130,
            fg_color="#5a5a5a",
            hover_color="#6e6e6e",
            command=self.diagnosi_sony,
        )
        self.btn_sony_diagnosi.grid(row=0, column=1, padx=5, sticky="ew")
        self.btn_sony_scatta = ctk.CTkButton(
            riga_sony,
            text="SCATTA E SCARICA",
            height=36,
            fg_color="#1f7a3d",
            hover_color="#258c47",
            command=self.scatta_sony,
        )
        self.btn_sony_scatta.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        ctk.CTkLabel(scroll, text="HOT-FOLDER (CARTELLA MONITORATA)", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=6, column=0, columnspan=3, padx=8, pady=(14, 2), sticky="w"
        )
        ctk.CTkLabel(
            scroll,
            text=(
                "Utile con USB + Imaging Edge Desktop, con cartelle sincronizzate "
                "(Google Drive/Dropbox) o con fotocamere che salvano su cartella di rete."
            ),
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#9aa0a6",
            wraplength=900,
        ).grid(row=7, column=0, columnspan=3, padx=8, pady=(0, 4), sticky="w")

        ctk.CTkLabel(scroll, text="Cartella fotocamera:").grid(row=8, column=0, padx=8, pady=4, sticky="w")
        self.entry_wifi_dir = ctk.CTkEntry(scroll, placeholder_text="Cartella da monitorare (es. cartella sincronizzata)")
        self.entry_wifi_dir.grid(row=8, column=1, padx=8, pady=4, sticky="ew")
        ctk.CTkButton(scroll, text="Sfoglia", width=100, command=self.seleziona_cartella_wifi).grid(
            row=8, column=2, padx=8, pady=4
        )

        ctk.CTkLabel(scroll, text="Cartella output:").grid(row=9, column=0, padx=8, pady=4, sticky="w")
        self.entry_wifi_output = ctk.CTkEntry(scroll, placeholder_text="Cartella output tethering")
        self.entry_wifi_output.grid(row=9, column=1, padx=8, pady=4, sticky="ew")
        ctk.CTkButton(scroll, text="Sfoglia", width=100, command=self.seleziona_output_wifi).grid(
            row=9, column=2, padx=8, pady=4
        )

        self.btn_tethering = ctk.CTkButton(
            scroll, text="AVVIA MONITORAGGIO CARTELLA", height=40, fg_color="#1f7a3d", hover_color="#258c47",
            command=self.toggle_tethering,
        )
        self.btn_tethering.grid(row=10, column=0, columnspan=3, padx=8, pady=10, sticky="ew")

        ctk.CTkLabel(scroll, text="CREDENZIALI CLOUD", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=11, column=0, columnspan=3, padx=8, pady=(14, 2), sticky="w"
        )

        credenziali = [
            ("Telegram Bot Token", "entry_tg_token", False, "cloud_telegram"),
            ("Telegram Chat ID", "entry_tg_chat", False, "cloud_telegram"),
            ("Google Drive API Key / Folder ID (non attivo)", "entry_gdrive", False, "cloud_gdrive"),
            ("Meta Access Token (FB/IG) (non attivo)", "entry_meta", False, "cloud_meta"),
            ("Meta Account ID (non attivo)", "entry_meta_id", False, "cloud_meta"),
            ("Dropbox Access Token", "entry_dropbox", False, "cloud_dropbox"),
            ("SwissTransfer Email (non attivo)", "entry_swiss", False, "cloud_swiss"),
        ]
        riga = 12
        for etichetta, attr, _, chiave_flag in credenziali:
            ctk.CTkLabel(scroll, text=etichetta + ":").grid(row=riga, column=0, padx=8, pady=3, sticky="w")
            entry = ctk.CTkEntry(scroll)
            entry.grid(row=riga, column=1, padx=8, pady=3, sticky="ew")
            setattr(self, attr, entry)
            setattr(self, attr + "_flag", chiave_flag)
            riga += 1

        # checkboxes canali
        canali = ctk.CTkFrame(scroll)
        canali.grid(row=riga, column=0, columnspan=3, padx=8, pady=8, sticky="ew")
        self.chk_cloud_telegram = ctk.CTkCheckBox(canali, text="Telegram")
        self.chk_cloud_telegram.grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.chk_cloud_gdrive = ctk.CTkCheckBox(canali, text="Google Drive (non attivo)")
        self.chk_cloud_gdrive.grid(row=0, column=1, padx=10, pady=6, sticky="w")
        self.chk_cloud_meta = ctk.CTkCheckBox(canali, text="Meta FB/IG (non attivo)")
        self.chk_cloud_meta.grid(row=0, column=2, padx=10, pady=6, sticky="w")
        self.chk_cloud_dropbox = ctk.CTkCheckBox(canali, text="Dropbox")
        self.chk_cloud_dropbox.grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.chk_cloud_swiss = ctk.CTkCheckBox(canali, text="SwissTransfer (non attivo)")
        self.chk_cloud_swiss.grid(row=1, column=1, padx=10, pady=6, sticky="w")

        ctk.CTkLabel(
            scroll,
            text=(
                "Telegram e Dropbox sono operativi. Google Drive, Meta e SwissTransfer "
                "sono predisposti ma non ancora attivi: l'invio viene saltato senza errori."
            ),
            font=ctk.CTkFont(size=11), text_color="#9aa0a6", wraplength=900, justify="left",
        ).grid(row=riga + 1, column=0, columnspan=3, padx=8, pady=(0, 10), sticky="w")

    # ------------------------------------------------------------- tab LOG
    def _costruisci_tab_log(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(False)
        self.txt_log = ctk.CTkTextbox(tab, corner_radius=6, font=ctk.CTkFont(size=12, family="Consolas"))
        self.txt_log.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.txt_log.configure(state="disabled")

        barra = ctk.CTkFrame(tab, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        ctk.CTkButton(barra, text="Svuota log", width=120, command=self.svuota_log).pack(side="left")
        ctk.CTkButton(barra, text="Salva log su file", width=150, command=self.salva_log).pack(side="left", padx=8)

    # ============================================================ EVENTI UI
    def scrivi_log(self, messaggio):
        riga = f"[{time.strftime('%H:%M:%S')}] {messaggio}\n"
        try:
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", riga)
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")
        except Exception:
            pass
        logging.info(messaggio)

    def _log_threadsafe(self, messaggio):
        """Accoda un messaggio di log: può essere chiamato da qualsiasi thread."""
        try:
            self._coda.put(("log", messaggio))
        except Exception:
            pass

    def svuota_log(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def salva_log(self):
        percorso = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Testo", "*.txt")])
        if not percorso:
            return
        try:
            with open(percorso, "w", encoding="utf-8") as f:
                f.write(self.txt_log.get("1.0", "end"))
            self.scrivi_log(f"Log salvato in {percorso}")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare il log:\n{e}")

    def seleziona_cartella_sorgente(self):
        cartella = filedialog.askdirectory(initialdir=self._ultima_cartella)
        if cartella:
            self._ultima_cartella = cartella
            self.entry_sorgente.delete(0, "end")
            self.entry_sorgente.insert(0, cartella)
            self.scrivi_log(f"Sorgente: {cartella}")

    def seleziona_file_sorgente(self):
        files = filedialog.askopenfilenames(
            initialdir=self._ultima_cartella,
            title="Seleziona file RAW",
            filetypes=[
                ("File RAW", " ".join("*" + e for e in RAW_ESTENSIONI)),
                ("Immagini", " ".join("*" + e for e in IMMAGINI_ESTENSIONI)),
                ("Tutti i file", "*.*"),
            ],
        )
        if files:
            self._ultima_cartella = os.path.dirname(files[0])
            self.entry_sorgente.delete(0, "end")
            self.entry_sorgente.insert(0, "; ".join(files))
            self.scrivi_log(f"Selezionati {len(files)} file.")

    def seleziona_cartella_destinazione(self):
        cartella = filedialog.askdirectory(initialdir=self._ultima_cartella)
        if cartella:
            self.entry_destinazione.delete(0, "end")
            self.entry_destinazione.insert(0, cartella)
            self.lbl_path_stato.configure(text=cartella)
            self.scrivi_log(f"Destinazione: {cartella}")

    def seleziona_logo(self):
        percorso = filedialog.askopenfilename(
            title="Seleziona logo PNG", filetypes=[("Immagini PNG", "*.png"), ("Tutti i file", "*.*")]
        )
        if percorso:
            self.parametri["logo_path"] = percorso
            self.lbl_logo.configure(text=os.path.basename(percorso))
            self.scrivi_log(f"Logo caricato: {percorso}")

    def seleziona_cartella_wifi(self):
        cartella = filedialog.askdirectory(initialdir=self._ultima_cartella)
        if cartella:
            self.entry_wifi_dir.delete(0, "end")
            self.entry_wifi_dir.insert(0, cartella)
            if not self.entry_wifi_output.get().strip():
                self.entry_wifi_output.insert(0, os.path.join(cartella, "Output_Ottimizzati"))
            self.scrivi_log(f"Hot-folder Wi-Fi: {cartella}")

    def seleziona_output_wifi(self):
        cartella = filedialog.askdirectory(initialdir=self._ultima_cartella)
        if cartella:
            self.entry_wifi_output.delete(0, "end")
            self.entry_wifi_output.insert(0, cartella)

    def apri_cartella_output(self):
        cartella = self.entry_destinazione.get().strip()
        if not cartella or not os.path.isdir(cartella):
            messagebox.showwarning("Attenzione", "Seleziona prima una cartella di destinazione valida.")
            return
        try:
            os.startfile(cartella)  # Windows
        except Exception:
            messagebox.showinfo("Cartella output", cartella)

    # ============================================================ PRESET
    def applica_preset(self, nome):
        preset = {
            "Web / Social": {
                "max_dim": 2048, "qualita_jpeg": 85, "formato": "JPEG",
                "contrasto": 0.35, "vivacita": 0.40, "nitidezza_quantita": 1.2,
                "chiarezza": 0.15, "dehaze": 0.05,
            },
            "Stampa Fine Art": {
                "max_dim": 0, "qualita_jpeg": 100, "formato": "TIFF",
                "contrasto": 0.25, "vivacita": 0.25, "nitidezza_quantita": 1.6,
                "nitidezza_raggio": 1.8, "chiarezza": 0.10,
            },
            "Archivio JPEG": {
                "max_dim": 0, "qualita_jpeg": 95, "formato": "JPEG",
                "contrasto": 0.20, "vivacita": 0.20, "nitidezza_quantita": 0.8,
                "preserva_exif": True,
            },
            "Ritratto": {
                "max_dim": 3000, "qualita_jpeg": 92, "formato": "JPEG",
                "contrasto": 0.22, "vivacita": 0.20, "saturazione": 0.95,
                "chiarezza": 0.05, "ombre": 12, "luci": -8,
                "nitidezza_quantita": 0.9, "nr_luminanza": 15, "nr_colore": 20,
            },
            "Paesaggio": {
                "max_dim": 3840, "qualita_jpeg": 92, "formato": "JPEG",
                "contrasto": 0.42, "vivacita": 0.45, "chiarezza": 0.30,
                "dehaze": 0.20, "nitidezza_quantita": 1.8, "nitidezza_raggio": 1.6,
                "hsl_verde": 12, "hsl_blu": 10,
            },
            "Bianco e Nero": {
                "max_dim": 3000, "qualita_jpeg": 92, "formato": "JPEG",
                "saturazione": 0.0, "contrasto": 0.45, "chiarezza": 0.25,
                "nitidezza_quantita": 1.5, "grana": 12,
            },
        }.get(nome)

        if not preset:
            return

        for chiave, valore in preset.items():
            self.parametri[chiave] = valore
            if chiave in self._slider_widgets:
                slider, label, fmt = self._slider_widgets[chiave]
                slider.set(valore)
                label.configure(text=fmt.format(float(valore)))

        if "max_dim" in preset:
            self.entry_max_dim.delete(0, "end")
            self.entry_max_dim.insert(0, str(preset["max_dim"]))
            self._evidenzia_max_dim(int(preset["max_dim"]))
        if "qualita_jpeg" in preset:
            self.entry_qualita.delete(0, "end")
            self.entry_qualita.insert(0, str(preset["qualita_jpeg"]))
        if "formato" in preset:
            self.combo_formato.set(preset["formato"])
        if "preserva_exif" in preset:
            if preset["preserva_exif"]:
                self.chk_exif.select()
            else:
                self.chk_exif.deselect()

        self.parametri["rimuovi_grana_auto"] = bool(preset.get("rimuovi_grana_auto", False))
        self._aggiorna_stato_grana()
        self.scrivi_log(f"Preset applicato: {nome}")

    # ============================================================ CONFIG
    def salva_configurazione(self):
        percorso = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Configurazione JSON", "*.json")],
            initialfile="franchetti_config.json",
        )
        if not percorso:
            return
        try:
            self._raccogli_campi()
            with open(percorso, "w", encoding="utf-8") as f:
                json.dump(self.parametri, f, indent=2, ensure_ascii=False)
            self.scrivi_log(f"Configurazione salvata: {percorso}")
        except Exception as e:
            messagebox.showerror("Errore", f"Salvataggio non riuscito:\n{e}")

    def carica_configurazione(self):
        percorso = filedialog.askopenfilename(filetypes=[("Configurazione JSON", "*.json"), ("Tutti i file", "*.*")])
        if not percorso:
            return
        try:
            with open(percorso, "r", encoding="utf-8") as f:
                dati = json.load(f)
            if not isinstance(dati, dict):
                raise ValueError("il file non contiene una configurazione valida")
            self.parametri = normalizza_parametri(dati)
            self._applica_config_alla_ui()
            self.scrivi_log(f"Configurazione caricata: {percorso}")
        except Exception as e:
            messagebox.showerror("Errore", f"Caricamento non riuscito:\n{e}")

    def _applica_config_alla_ui(self):
        for chiave, valore in self.parametri.items():
            if chiave in self._slider_widgets:
                try:
                    slider, label, fmt = self._slider_widgets[chiave]
                    numero = float(valore)
                    slider.set(numero)
                    label.configure(text=fmt.format(numero))
                except Exception:
                    pass

        def imposta_check(widget, chiave, default=False):
            try:
                if bool(self.parametri.get(chiave, default)):
                    widget.select()
                else:
                    widget.deselect()
            except Exception:
                pass

        def imposta_entry(widget, chiave, default=""):
            try:
                widget.delete(0, "end")
                widget.insert(0, str(self.parametri.get(chiave, default) or ""))
            except Exception:
                pass

        self.entry_max_dim.delete(0, "end")
        self.entry_max_dim.insert(0, str(self.parametri.get("max_dim", 1920)))
        try:
            self._evidenzia_max_dim(int(self.parametri.get("max_dim", 1920)))
        except (TypeError, ValueError):
            pass
        self.entry_qualita.delete(0, "end")
        self.entry_qualita.insert(0, str(self.parametri.get("qualita_jpeg", 90)))
        self.combo_formato.set(self.parametri.get("formato", "JPEG"))
        self.combo_spazio.set(self.parametri.get("profilo_colore", "sRGB"))
        self.entry_watermark.delete(0, "end")
        self.entry_watermark.insert(0, self.parametri.get("watermark_text", ""))
        self.entry_font_size.delete(0, "end")
        self.entry_font_size.insert(0, str(self.parametri.get("font_size", 14)))
        self.combo_posizione.set(self.parametri.get("watermark_posizione", "Basso a destra"))
        self.entry_prefisso.delete(0, "end")
        self.entry_prefisso.insert(0, self.parametri.get("prefisso", ""))
        self.entry_suffisso.delete(0, "end")
        self.entry_suffisso.insert(0, self.parametri.get("suffisso", ""))
        self.combo_sovrascrittura.set(self.parametri.get("sovrascrittura", "Rinomina"))
        self.combo_curva.set(self.parametri.get("curva_tonale", "Lineare"))
        self.entry_colore_ombre.delete(0, "end")
        self.entry_colore_ombre.insert(0, self.parametri.get("colore_ombre", "#2b4c7e"))
        self.entry_colore_luci.delete(0, "end")
        self.entry_colore_luci.insert(0, self.parametri.get("colore_luci", "#e0b070"))

        imposta_check(self.chk_wb_camera, "use_camera_wb", True)
        imposta_check(self.chk_exif, "preserva_exif", True)
        imposta_check(self.chk_ricorsivo, "ricorsivo", True)
        imposta_check(self.chk_mantieni_nomi, "mantieni_nomi", True)
        imposta_check(self.chk_watermark, "watermark_attivo", True)
        imposta_check(self.chk_multicore, "usa_multicore", True)
        imposta_check(self.chk_cloud_telegram, "cloud_telegram")
        imposta_check(self.chk_cloud_gdrive, "cloud_gdrive")
        imposta_check(self.chk_cloud_meta, "cloud_meta")
        imposta_check(self.chk_cloud_dropbox, "cloud_dropbox")
        imposta_check(self.chk_cloud_swiss, "cloud_swiss")

        imposta_entry(self.entry_wifi_dir, "wifi_dir")
        imposta_entry(self.entry_wifi_output, "output_dir")
        imposta_entry(self.entry_tg_token, "tg_token")
        imposta_entry(self.entry_tg_chat, "tg_chat_id")
        imposta_entry(self.entry_gdrive, "gdrive_key")
        imposta_entry(self.entry_meta, "meta_token")
        imposta_entry(self.entry_meta_id, "meta_id")
        imposta_entry(self.entry_dropbox, "dropbox_token")
        imposta_entry(self.entry_swiss, "swisstransfer_email")

        logo = str(self.parametri.get("logo_path", "") or "")
        try:
            self.lbl_logo.configure(text=os.path.basename(logo) if logo else "Nessun logo")
        except Exception:
            pass

        self._toggle_auto_luminosita(bool(self.parametri.get("auto_luminosita", False)))
        self._aggiorna_stato_grana()

    # ============================================================ CAMPI
    def _toggle_auto_luminosita(self, attivo):
        """Attiva il miglioramento automatico e tiene allineati i due interruttori."""
        attivo = bool(attivo)
        self.parametri["auto_luminosita"] = attivo
        for nome in ("sw_auto_luminosita", "sw_auto_sviluppo"):
            widget = getattr(self, nome, None)
            if widget is None:
                continue
            try:
                if attivo and not widget.get():
                    widget.select()
                elif not attivo and widget.get():
                    widget.deselect()
            except Exception:
                pass

    def _imposta_max_dim(self, valore):
        """Imposta il lato lungo da una misura pronta."""
        self.entry_max_dim.delete(0, "end")
        self.entry_max_dim.insert(0, str(valore))
        self.parametri["max_dim"] = valore
        self._evidenzia_max_dim(valore)

    def _evidenzia_max_dim(self, valore):
        for preset, bottone in getattr(self, "_bottoni_misure", []):
            if preset == valore:
                bottone.configure(fg_color="#1f7a3d", hover_color="#258c47", text_color="#ffffff")
            else:
                bottone.configure(fg_color="#3a3f45", hover_color="#4a5158", text_color="#dce1e6")

    def _aggiorna_evidenzia_da_campo(self, _evento=None):
        try:
            valore = int(self.entry_max_dim.get() or 0)
        except ValueError:
            return
        self._evidenzia_max_dim(valore)

    def _raccogli_campi(self):
        """Sincronizza tutti i campi UI nel dizionario parametri."""
        try:
            self.parametri["max_dim"] = int(self.entry_max_dim.get() or 0)
        except ValueError:
            self.parametri["max_dim"] = 1920
        try:
            self._evidenzia_max_dim(int(self.parametri["max_dim"]))
        except (TypeError, ValueError):
            pass
        try:
            self.parametri["qualita_jpeg"] = max(1, min(100, int(self.entry_qualita.get() or 90)))
        except ValueError:
            self.parametri["qualita_jpeg"] = 90
        try:
            self.parametri["font_size"] = max(8, int(self.entry_font_size.get() or 14))
        except ValueError:
            self.parametri["font_size"] = 14

        self.parametri["formato"] = self.combo_formato.get()
        self.parametri["profilo_colore"] = self.combo_spazio.get()
        self.parametri["use_camera_wb"] = bool(self.chk_wb_camera.get())
        self.parametri["preserva_exif"] = bool(self.chk_exif.get())
        self.parametri["ricorsivo"] = bool(self.chk_ricorsivo.get())
        self.parametri["mantieni_nomi"] = bool(self.chk_mantieni_nomi.get())
        self.parametri["auto_luminosita"] = bool(self.sw_auto_luminosita.get())
        self.parametri["usa_multicore"] = bool(self.chk_multicore.get())
        self.parametri["prefisso"] = self.entry_prefisso.get().strip()
        self.parametri["suffisso"] = self.entry_suffisso.get().strip()
        self.parametri["sovrascrittura"] = self.combo_sovrascrittura.get()
        self.parametri["watermark_attivo"] = bool(self.chk_watermark.get())
        self.parametri["watermark_text"] = self.entry_watermark.get().strip()
        self.parametri["watermark_posizione"] = self.combo_posizione.get()
        self.parametri["curva_tonale"] = self.combo_curva.get()
        self.parametri["colore_ombre"] = self.entry_colore_ombre.get().strip() or "#2b4c7e"
        self.parametri["colore_luci"] = self.entry_colore_luci.get().strip() or "#e0b070"

        # Tethering / Cloud
        self.parametri["wifi_dir"] = self.entry_wifi_dir.get().strip()
        self.parametri["output_dir"] = self.entry_wifi_output.get().strip()
        self.parametri["tg_token"] = self.entry_tg_token.get().strip()
        self.parametri["tg_chat_id"] = self.entry_tg_chat.get().strip()
        self.parametri["gdrive_key"] = self.entry_gdrive.get().strip()
        self.parametri["meta_token"] = self.entry_meta.get().strip()
        self.parametri["meta_id"] = self.entry_meta_id.get().strip()
        self.parametri["dropbox_token"] = self.entry_dropbox.get().strip()
        self.parametri["swisstransfer_email"] = self.entry_swiss.get().strip()
        self.parametri["cloud_telegram"] = bool(self.chk_cloud_telegram.get())
        self.parametri["cloud_gdrive"] = bool(self.chk_cloud_gdrive.get())
        self.parametri["cloud_meta"] = bool(self.chk_cloud_meta.get())
        self.parametri["cloud_dropbox"] = bool(self.chk_cloud_dropbox.get())
        self.parametri["cloud_swiss"] = bool(self.chk_cloud_swiss.get())
        return self.parametri

    # ============================================================ BATCH
    def _raccogli_file_sorgente(self, sorgente, ricorsivo, escludi=None):
        return raccogli_file_sorgente(sorgente, ricorsivo, escludi)

    def avvia_batch(self):
        if self._batch_attivo:
            messagebox.showinfo("Batch", "Una conversione è già in corso.")
            return

        sorgente = self.entry_sorgente.get().strip()
        destinazione = self.entry_destinazione.get().strip()

        if not sorgente:
            messagebox.showwarning("Sorgente mancante", "Seleziona una cartella o dei file RAW.")
            return
        if not destinazione:
            messagebox.showwarning("Destinazione mancante", "Seleziona la cartella di destinazione.")
            return

        try:
            os.makedirs(destinazione, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile creare la cartella di destinazione:\n{e}")
            return

        self._raccogli_campi()
        files = self._raccogli_file_sorgente(
            sorgente, self.parametri.get("ricorsivo", True), escludi=destinazione
        )
        if not files:
            messagebox.showwarning("Nessun file", "Nessun file RAW o immagine trovato nella sorgente selezionata.")
            return

        self._batch_files = files
        self._cancel_event.clear()
        self._batch_attivo = True

        self.btn_avvia.configure(state="disabled")
        self.btn_annulla.configure(state="normal")
        self.progress.set(0)
        self.lbl_progresso.configure(text=f"0 / {len(files)}")
        self.lbl_stato.configure(text="Conversione in corso...")
        self.scrivi_log(f"Batch avviato: {len(files)} file -> {destinazione}")

        params = normalizza_parametri(self.parametri)
        thread = threading.Thread(
            target=self._batch_worker, args=(list(files), params, destinazione), daemon=True
        )
        thread.start()

    def _batch_worker(self, files, params, destinazione):
        def log(messaggio):
            self._log_threadsafe(messaggio)

        def progresso(indice, totale, ok, errori, saltati):
            self._coda.put(("progress", indice, totale, ok, errori, saltati))

        esito = esegui_batch(
            files, params, destinazione,
            log=log, progresso=progresso, cancel_event=self._cancel_event,
        )
        self._coda.put((
            "done", esito["ok"], esito["errori"], esito["saltati"], esito["annullato"]
        ))

    def _aggiorna_progresso(self, indice, totale, ok, errori, saltati=0):
        self.progress.set(min(1.0, indice / max(totale, 1)))
        testo = f"{indice} / {totale}  -  OK: {ok}  Errori: {errori}"
        if saltati:
            testo += f"  Saltati: {saltati}"
        self.lbl_progresso.configure(text=testo)

    def _fine_batch(self, ok, errori, saltati=0, annullato=False):
        self._batch_attivo = False
        self.btn_avvia.configure(state="normal")
        self.btn_annulla.configure(state="disabled")
        if annullato:
            testo = f"Annullato - OK: {ok}, Errori: {errori}"
        else:
            testo = f"Completato - OK: {ok}, Errori: {errori}"
        if saltati:
            testo += f", Saltati: {saltati}"
        self.lbl_stato.configure(text=testo)
        self.lbl_progresso.configure(text=testo)
        self.scrivi_log(f"Batch terminato: OK {ok}, errori {errori}, saltati {saltati}.")

    def annulla_batch(self):
        if not self._batch_attivo:
            return
        self._cancel_event.set()
        self.lbl_stato.configure(text="Annullamento in corso...")
        self.scrivi_log("Richiesto annullamento del batch...")

    # ============================================================ TETHERING
    def toggle_tethering(self):
        if self.observer and self.observer.is_alive():
            try:
                self.observer.stop()
                self.observer.join(timeout=3)
            except Exception:
                pass
            self.observer = None
            self.parametri["tethering_attivo"] = False
            self.btn_tethering.configure(text="AVVIA MONITORAGGIO CARTELLA", fg_color="#1f7a3d", hover_color="#258c47")
            self.lbl_stato.configure(text="Monitoraggio disattivato")
            self.scrivi_log("Monitoraggio cartella disattivato.")
            return

        self._raccogli_campi()
        cartella = self.parametri.get("wifi_dir", "")
        if not cartella or not os.path.isdir(cartella):
            messagebox.showwarning("Hot-folder", "Seleziona una cartella Wi-Fi valida da monitorare.")
            return

        output = self.parametri.get("output_dir") or os.path.join(cartella, "Output_Ottimizzati")
        os.makedirs(output, exist_ok=True)
        self.parametri["output_dir"] = output

        handler = RawHotFolderHandler(self.parametri, self._log_threadsafe)
        self.observer = Observer()
        self.observer.schedule(handler, path=cartella, recursive=False)
        self.observer.start()

        self.parametri["tethering_attivo"] = True
        self.btn_tethering.configure(text="DISATTIVA MONITORAGGIO", fg_color="#a32a2a", hover_color="#bf3333")
        self.lbl_stato.configure(text=f"Monitoraggio attivo: {cartella}")
        self.scrivi_log(f"Monitoraggio cartella attivo su {cartella}. Output: {output}")

    # ============================================================ SONY WI-FI
    def _stato_sony(self, testo, colore):
        """Aggiorna l'etichetta Sony dal thread principale (Tkinter non e' thread-safe)."""
        try:
            self.after(0, lambda: self.lbl_sony.configure(text=testo, text_color=colore))
        except Exception:
            pass

    def connetti_sony(self):
        def lavoro():
            try:
                self._log_threadsafe("Sony: ricerca della fotocamera in corso...")
                client = SonyWifiClient(self._log_threadsafe)
                api = client.connetti()
                self._sony = client
                if "actTakePicture" in api:
                    self._stato_sony(
                        f"Fotocamera pronta ({len(api)} funzioni disponibili)", "#66bb6a"
                    )
                    self._log_threadsafe("Sony: connessione riuscita. Usa SCATTA E SCARICA.")
                else:
                    self._stato_sony(
                        "Connessa ma non pronta: apri Smart Remote Control e riprova", "#ffb74d"
                    )
                    self._log_threadsafe(
                        "Sony: la fotocamera e' raggiungibile ma non e' in modalita' remota. "
                        "Sulla A7S apri Smart Remote Control e premi di nuovo CONNETTI."
                    )
            except Exception as errore:
                self._sony = None
                self._stato_sony("Fotocamera non connessa", "#ffb74d")
                self._log_threadsafe(f"Sony: connessione fallita - {errore}")
                self._log_threadsafe(
                    "Sony: controlla di essere collegato al Wi-Fi DIRECT-xxxx:ILCE-7S "
                    "e che l'app Smart Remote Control sia aperta sulla fotocamera."
                )
                self.diagnosi_sony()

        threading.Thread(target=lavoro, daemon=True).start()

    def diagnosi_sony(self):
        def lavoro():
            righe = []

            def annota(messaggio):
                righe.append(messaggio)
                self._log_threadsafe(messaggio)

            annota("=== DIAGNOSI SONY WI-FI ===")
            indirizzi = SonyWifiClient.indirizzi_locali()
            annota("IP del PC: " + (", ".join(indirizzi) if indirizzi else "nessuno"))
            in_rete = any(ip.startswith("192.168.122.") for ip in indirizzi)
            annota("Rete fotocamera 192.168.122.x: " + ("SI" if in_rete else "NO"))
            if not in_rete:
                annota(
                    "Il PC non e' collegato al Wi-Fi della fotocamera. "
                    "Collega la rete DIRECT-xxxx:ILCE-7S e riprova."
                )
            client = SonyWifiClient(self._log_threadsafe)
            base = None
            try:
                base = client.scopri(timeout=3.0)
            except Exception as errore:
                annota(f"Ricerca SSDP non riuscita: {errore}")
            if base:
                annota(f"Indirizzo API dichiarato dalla fotocamera: {base}")
                try:
                    info = client._chiama("getApplicationInfo")
                    annota("Fotocamera: " + json.dumps(info)[:400])
                    elenco = client._chiama("getAvailableApiList")
                    funzioni = elenco[0] if elenco and isinstance(elenco[0], list) else []
                    annota(f"Funzioni disponibili: {len(funzioni)}")
                    if "startRecMode" in funzioni:
                        client._chiama("startRecMode")
                        for _ in range(15):
                            time.sleep(1.0)
                            elenco = client._chiama("getAvailableApiList")
                            funzioni = elenco[0] if elenco and isinstance(elenco[0], list) else []
                            if "actTakePicture" in funzioni:
                                break
                    annota(
                        "Scatto remoto: "
                        + ("DISPONIBILE" if "actTakePicture" in funzioni else "NON disponibile")
                    )
                except Exception as errore:
                    annota(f"Errore chiamata API: {errore}")
            else:
                annota(
                    "Nessuna risposta dalla fotocamera. Apri 'Smart Remote Control' "
                    "sulla A7S e attendi che il Wi-Fi sia attivo."
                )
            percorso = os.path.join(os.path.expanduser("~"), "Desktop", "sony_diagnosi.txt")
            try:
                with open(percorso, "w", encoding="utf-8") as file_diag:
                    file_diag.write("\n".join(righe))
                annota(f"Diagnosi salvata in {percorso}")
            except Exception:
                pass

        threading.Thread(target=lavoro, daemon=True).start()

    def scatta_sony(self):
        client = getattr(self, "_sony", None)
        if client is None:
            messagebox.showwarning(
                "Sony Wi-Fi",
                "Prima premi CONNETTI FOTOCAMERA e attendi la conferma di connessione.",
            )
            return
        cartella = self.entry_wifi_dir.get().strip()
        if not cartella or not os.path.isdir(cartella):
            cartella = os.path.join(os.path.expanduser("~"), "Pictures", "SonyTether")
            os.makedirs(cartella, exist_ok=True)
            self.entry_wifi_dir.delete(0, "end")
            self.entry_wifi_dir.insert(0, cartella)

        def lavoro():
            try:
                self._log_threadsafe("Sony: scatto in corso...")
                file_ottenuti = client.scatta_e_scarica(cartella)
                self._log_threadsafe(
                    f"Sony: {len(file_ottenuti)} file ricevuti in {cartella}"
                )
                self._stato_sony(
                    f"Fotocamera pronta ({len(client.apis)} funzioni disponibili)", "#66bb6a"
                )
            except Exception as errore:
                self._log_threadsafe(f"Sony: scatto non riuscito - {errore}")
                self._stato_sony("Scatto non riuscito: vedi il tab Log", "#ffb74d")

        threading.Thread(target=lavoro, daemon=True).start()

    # ============================================================ CHIUSURA
    def _chiudi_app(self):
        try:
            self._cancel_event.set()
            if self.observer and self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=2)
            termina_tutti_gli_esecutori()
        except Exception:
            pass
        self.destroy()


# ================================================================================
# 6. ENTRY POINT
# ================================================================================
if __name__ == "__main__":
    # Necessario su Windows per l'elaborazione multi-processo (PyInstaller).
    multiprocessing.freeze_support()

    # Modalita' di test da riga di comando:
    #   FranchettiRawConverterPro.exe --converti-test <sorgente> <uscita>
    #   FranchettiRawConverterPro.exe --batch-test <sorgente> <cartella output>
    # Servono a verificare la conversione senza aprire la finestra.
    if "--converti-test" in sys.argv:
        indice = sys.argv.index("--converti-test")
        if len(sys.argv) < indice + 3:
            sys.exit(2)
        sorgente = sys.argv[indice + 1]
        uscita = sys.argv[indice + 2]
        try:
            parametri = parametri_default()
            parametri["watermark_attivo"] = False
            parametri["max_dim"] = 0
            ImageEngine.sviluppa_e_ottimizza(sorgente, uscita, parametri)
            sys.exit(0 if os.path.exists(uscita) else 3)
        except Exception as errore:
            logging.error("Test conversione fallito: %s", errore)
            sys.exit(1)

    if "--batch-test" in sys.argv:
        indice = sys.argv.index("--batch-test")
        if len(sys.argv) < indice + 3:
            sys.exit(2)
        sorgente = sys.argv[indice + 1]
        destinazione = sys.argv[indice + 2]
        os.makedirs(destinazione, exist_ok=True)
        parametri = parametri_default()
        parametri["watermark_attivo"] = False
        parametri["max_dim"] = 0
        elenco = raccogli_file_sorgente(sorgente, True, escludi=destinazione)
        inizio = time.time()
        esito = esegui_batch(
            elenco, parametri, destinazione,
            log=lambda messaggio: logging.info("[batch-test] %s", messaggio),
        )
        durata = time.time() - inizio
        rapporto = (
            f"File trovati: {len(elenco)}\n"
            f"OK: {esito['ok']}\n"
            f"Errori: {esito['errori']}\n"
            f"Saltati: {esito['saltati']}\n"
            f"Processi: {numero_processi_ottimale(len(elenco))} su {os.cpu_count() or 1} core\n"
            f"Durata: {durata:.1f} s\n"
        )
        try:
            with open(os.path.join(destinazione, "_report.txt"), "w", encoding="utf-8") as f:
                f.write(rapporto)
        except Exception:
            pass
        sys.exit(0 if esito["errori"] == 0 else 1)

    app = FranchettiApp()
    app.mainloop()
