# -*- coding: utf-8 -*-
"""
================================================================================
          FRANCHETTI RAW CONVERTER PRO v2.58.0 - MONOLITHIC CORE
================================================================================
Licenza: MIT
Descrizione: Suite Enterprise Open-Source per lo sviluppo RAW lineare a livello
             sensore (rawpy/LibRaw con WB e matrice camera, AHD/AAHD), ottimizzazione
             in spazio Y/Cb/Cr, denoise ISO, correzioni colore complete, ridimensionamento,
             watermarking, tethering automatico multi-marca (Hot-Folder) e Sony Wi-Fi, Cloud
             (Telegram/Dropbox) ed elaborazione batch su tutti i core.
================================================================================
"""

import os
import sys
import io
import gc
import json
import math
import time
import queue
import shutil
import socket
import logging
import tempfile
import threading
import traceback
import functools
import multiprocessing
from datetime import datetime
from concurrent.futures import (
    FIRST_COMPLETED,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
    wait,
)
from tkinter import filedialog, messagebox

try:
    import numpy as np
    import rawpy
    import piexif
    import customtkinter as ctk
    from PIL import Image, ImageFilter, ImageOps, ImageDraw, ImageFont
    from skimage import color, filters
    from skimage.restoration import denoise_nl_means
    from scipy.ndimage import gaussian_filter, uniform_filter
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import requests
except ImportError as e:  # pragma: no cover
    dettaglio = str(e)
    print("[ERRORE DI AVVIO] Impossibile caricare una libreria fondamentale.")
    print(f"Dettaglio: {dettaglio}")
    if "partially initialized" in dettaglio or "_pocketfft" in dettaglio:
        # Tipico del bundle PyInstaller quando il processo viene interrotto
        # durante l'import: non significa che numpy manchi davvero.
        print(
            "Questo non indica una libreria mancante: l'import di NumPy e' stato "
            "interrotto mentre il programma si avviava."
        )
        print(
            "Riavvia l'applicazione da sola. Se usi il pacchetto --onefile, "
            "evita di avviare due copie contemporaneamente e verifica lo spazio "
            "libero in /tmp."
        )
    else:
        print("Installa le dipendenze con: pip install -r requirements.txt")
        if os.name != "nt":
            print("Su Linux Mint, se manca tkinter: sudo apt install python3-tk")
    sys.exit(1)

# Dipendenze opzionali per la ricezione FTP dalle fotocamere e per il testo
# sovrapposto. Se mancano, il programma resta avviabile e avvisa l'utente.
try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
except Exception:  # pragma: no cover
    DummyAuthorizer = FTPHandler = FTPServer = None


APP_VERSION = "2.58.0"
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


def _pattern_dialogo(estensioni):
    """Pattern per filedialog, con le varianti maiuscole su Linux/macOS.

    Su Windows il dialogo ignora il caso, su Linux e macOS no: un file
    DSCF5306.RAF non comparirebbe con il solo pattern "*.raf".
    """
    pattern = []
    for estensione in estensioni:
        for variante in (estensione, estensione.upper()):
            valore = "*" + variante
            if valore not in pattern:
                pattern.append(valore)
    return " ".join(pattern)

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
        # Protezione luci: comprime la spalla delle alte luci senza
        # schiacciare il bianco. Attivabile dai pulsanti rapidi.
        "proteggi_luci": False,
        "vivacita": 0.35,
        "saturazione": 1.0,
        "chiarezza": 0.0,
        "dehaze": 0.0,
        # Profilo qualita' predefinito: denoise ISO attivo e nitidezza
        # controllata. Il rumore viene tolto nelle zone piatte senza
        # cancellare i dettagli, quindi i file restano leggeri ma puliti.
        "nr_luminanza": 88.0,
        "nr_colore": 92.0,
        "rimuovi_grana_auto": True,
        "nitidezza_raggio": 0.9,
        "nitidezza_quantita": 0.9,
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
        # 3000 px e' il miglior compromesso per ingrandimenti nitidi e
        # file JPEG da circa 1 MB con qualita' 90.
        "max_dim": 3000,
        "qualita_jpeg": 90,
        "formato": "JPEG",
        "preserva_exif": True,
        # --- Miglioramento automatico (BETA) ---
        "auto_luminosita": False,
        # --- Prestazioni ---
        "usa_multicore": True,
        # Profilo adattivo scelto nel pannello PRESTAZIONI. Non e' un
        # interruttore finto: cambia davvero numero di processi e intensita'
        # del denoise, lasciando intatti gli originali.
        "profilo_prestazioni": "Bilanciato",
        "processi_auto": True,
        "processi_manuali": 0,
        "mantieni_nomi": True,
        "prefisso": "",
        "suffisso": "",
        "sovrascrittura": "Rinomina",
        "ricorsivo": True,
        # --- Watermark ---
        "watermark_attivo": True,
        "watermark_text": "\u00a9 Franchetti " + str(datetime.now().year),
        "font_size": 14,
        "watermark_posizione": "Basso a destra",
        "watermark_opacita": 0.85,
        "logo_path": "",
        "logo_opacita": 0.55,
        # --- Copyright e metadati ---
        # Il testo visibile resta watermark_text; qui si decide se lo stesso
        # copyright viene scritto anche in EXIF/IPTC (Artist, Copyright,
        # ImageDescription). Vale sia per il batch sia per le anteprime FTP.
        "copyright_autore": "Franchetti",
        "copyright_metadati": True,
        # --- Tethering / Cloud ---
        "ftp_copyright": True,
        "ftp_galleria": True,
        "ftp_cloud_auto": False,
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
    "processi_manuali": (0.0, 64.0),
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

    for chiave in ("max_dim", "qualita_jpeg", "font_size", "processi_manuali"):
        p[chiave] = int(round(p[chiave]))

    profilo = str(p.get("profilo_prestazioni", "Bilanciato") or "Bilanciato").strip()
    if profilo not in PROFILI_PRESTAZIONI:
        profilo = "Bilanciato"
    p["profilo_prestazioni"] = profilo

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
        "ricorsivo", "watermark_attivo", "use_camera_wb", "proteggi_luci", "cloud_telegram",
        "cloud_gdrive", "cloud_meta", "cloud_dropbox", "cloud_swiss",
        "processi_auto", "copyright_metadati", "ftp_galleria", "ftp_cloud_auto",
    ):
        p[chiave] = bool(p.get(chiave))

    p["prefisso"] = pulisci_nome_file(p.get("prefisso", ""))
    p["suffisso"] = pulisci_nome_file(p.get("suffisso", ""))
    p["watermark_text"] = str(p.get("watermark_text", "") or "")
    p["copyright_autore"] = str(p.get("copyright_autore", "") or "").strip() or "Franchetti"
    p["ftp_copyright"] = bool(p.get("ftp_copyright", True))
    return p


# ================================================================================
# 1b. ELABORAZIONE PARALLELA: TUTTI I CORE DEL PROCESSORE
# ================================================================================
def memoria_disponibile_mb():
    """Memoria fisica disponibile in MB; 4 GB come stima prudente.

    Su Linux legge MemAvailable da /proc/meminfo: senza questo dato i profili
    "Bilanciato" e "Qualita'" restano ancorati a una stima Windows e possono
    avviare troppi processi su macchine piccole o virtuali.
    """
    if os.name != "nt":
        try:
            with open("/proc/meminfo", encoding="ascii", errors="ignore") as info:
                for riga in info:
                    if riga.startswith("MemAvailable:"):
                        return int(riga.split()[1]) // 1024
        except Exception:
            pass
        return 4096

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


def libera_memoria():
    """Restituisce al sistema la memoria gia' liberata da Python.

    Su Linux glibc tende a tenere per se' la memoria liberata: dopo un batch
    di RAW la RAM risulta ancora occupata e la macchina va in swap. malloc_trim
    restituisce quelle pagine al kernel; su Windows serve solo gc.collect().
    """
    try:
        gc.collect()
    except Exception:
        pass
    if os.name == "nt":
        return
    try:
        import ctypes

        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


@functools.lru_cache(maxsize=1)
def nuclei_fisici():
    """Nuclei fisici reali (Windows e Linux), senza aggiungere psutil.

    I core logici (hyperthreading) vanno bene per il profilo Veloce, ma per
    elaborare RAW il collo di bottiglia e' la memoria: sui core fisici si
    ottiene quasi lo stesso throughput con meno contesa e meno RAM.
    """
    if os.name != "nt":
        # Su Linux il fallback "logici // 2" della versione precedente
        # restituiva 1 su una VM da 2 vCPU: i batch restavano a un solo
        # processo anche con piu' file. /proc/cpuinfo espone la topologia.
        try:
            coppie = set()
            physical = core = None
            with open("/proc/cpuinfo", encoding="ascii", errors="ignore") as info:
                for riga in info:
                    if riga.startswith("physical id"):
                        physical = riga.split(":", 1)[1].strip()
                    elif riga.startswith("core id"):
                        core = riga.split(":", 1)[1].strip()
                    elif not riga.strip():
                        if physical is not None and core is not None:
                            coppie.add((physical, core))
                        physical = core = None
                if physical is not None and core is not None:
                    coppie.add((physical, core))
            if coppie:
                return len(coppie)
        except Exception:
            pass
        # Topologia non disponibile (VM particolari, macOS): usa i logici.
        return max(1, os.cpu_count() or 1)

    try:
        import ctypes
        from ctypes import wintypes

        class _DatiProcessore(ctypes.Union):
            _fields_ = [
                ("ProcessorCore", ctypes.c_ubyte),
                ("NumaNode", wintypes.DWORD),
                ("Cache", ctypes.c_byte * 16),
            ]

        class _InfoProcessore(ctypes.Structure):
            _fields_ = [
                ("ProcessorMask", ctypes.c_size_t),
                ("Relationship", wintypes.DWORD),
                ("Dati", _DatiProcessore),
            ]

        kernel32 = ctypes.windll.kernel32
        lunghezza = wintypes.DWORD(0)
        kernel32.GetLogicalProcessorInformation(None, ctypes.byref(lunghezza))
        if lunghezza.value > 0:
            buffer = (ctypes.c_byte * lunghezza.value)()
            if kernel32.GetLogicalProcessorInformation(
                buffer, ctypes.byref(lunghezza)
            ):
                dimensione = ctypes.sizeof(_InfoProcessore)
                conteggio = 0
                for indice in range(lunghezza.value // dimensione):
                    info = _InfoProcessore.from_buffer(buffer, indice * dimensione)
                    # RelationProcessorCore = 0
                    if int(info.Relationship) == 0:
                        conteggio += 1
                if conteggio > 0:
                    return conteggio
    except Exception:
        pass
    logici = os.cpu_count() or 1
    return max(1, logici // 2) if logici > 1 else 1


def nuclei_logici():
    return max(1, os.cpu_count() or 1)


# I profili non sono cosmetici: cambiano il numero di processi e l'intensita'
# del denoise. Il dettaglio fine resta regolabile in AVANZATE e Smart Batch
# puo' comunque correggere ogni singolo file.
PROFILI_PRESTAZIONI = {
    "Veloce": {
        "descrizione": (
            "Tutti i core logici e denoise leggero: il batch finisce prima, "
            "con file leggermente meno rifiniti."
        ),
        "core": "logici",
        "parametri": {
            "nr_luminanza": 70.0,
            "nr_colore": 80.0,
            "nitidezza_quantita": 0.70,
        },
    },
    "Bilanciato": {
        "descrizione": (
            "Core fisici, denoise e nitidezza predefiniti: il miglior "
            "compromesso tra tempo e qualita'."
        ),
        "core": "fisici",
        "parametri": {
            "nr_luminanza": 88.0,
            "nr_colore": 92.0,
            "nitidezza_quantita": 0.90,
        },
    },
    "Massima qualità": {
        "descrizione": (
            "Core fisici, denoise e nitidezza piu' curati: piu' lento, "
            "pensato per stampe e consegne finali."
        ),
        "core": "fisici",
        "parametri": {
            "nr_luminanza": 95.0,
            "nr_colore": 96.0,
            "nitidezza_quantita": 1.10,
        },
    },
}


def per_processo_mb(parametri):
    """Picco RAM stimato per worker (MB), in base a output e denoise."""
    denoise = (
        float(parametri.get("nr_luminanza", 0.0) or 0.0) > 0.0
        or float(parametri.get("nr_colore", 0.0) or 0.0) > 0.0
    )
    max_dim = int(parametri.get("max_dim", 0) or 0)
    if max_dim <= 0:
        # Originale a piena risoluzione: 24-60 MP con denoise sono il caso
        # peggiore per la memoria.
        return 2400 if denoise else 1800
    return 1200


def numero_processi_ottimale(
    numero_file, per_processo_mb_valore=1200, profilo="Bilanciato", override=0
):
    """Quanti processi usare: profilo, core disponibili e RAM libera.

    override > 0 forza un numero scelto dall'utente (sempre entro i limiti).
    """
    if override and int(override) > 0:
        return max(1, min(int(override), 64, max(1, int(numero_file))))

    profilo = profilo if profilo in PROFILI_PRESTAZIONI else "Bilanciato"
    cpu = (
        nuclei_fisici()
        if PROFILI_PRESTAZIONI[profilo]["core"] == "fisici"
        else nuclei_logici()
    )
    # 85% della RAM libera: lascia respiro al sistema e alla GUI.
    per_ram = max(
        1,
        int((memoria_disponibile_mb() * 0.85) / max(256, per_processo_mb_valore)),
    )
    return max(1, min(int(cpu), per_ram, max(1, int(numero_file))))


def stima_peso_file(percorso, parametri):
    """Peso relativo di un file, usato per decidere se vale la pena il pool."""
    try:
        mb = max(0.1, os.path.getsize(percorso) / (1024.0 * 1024.0))
    except OSError:
        mb = 12.0
    max_dim = int(parametri.get("max_dim", 0) or 0)
    if max_dim <= 0:
        peso_dim = 30.0
    else:
        peso_dim = (max_dim / 3000.0) ** 2 * 8.0
    return mb + peso_dim


def conviene_elaborazione_parallela(percorsi, parametri, processi):
    """Evita di pagare l'avvio del pool per pochi file piccoli.

    Con 2 JPEG da 2 MB il pool costerebbe piu' del lavoro risparmiato.
    Con 2 RAW da 40 MB, o con un batch pesante e abbastanza numerico,
    conviene.
    """
    if not parametri.get("usa_multicore", True):
        return False
    if processi <= 1 or len(percorsi) < 2:
        return False
    # Se l'utente sceglie a mano il numero di processi, la scelta vince
    # sull'euristica pensata per i batch piccoli.
    if not parametri.get("processi_auto", True):
        try:
            if int(parametri.get("processi_manuali", 0) or 0) > 1:
                return True
        except (TypeError, ValueError):
            pass
    peso = sum(stima_peso_file(percorso, parametri) for percorso in percorsi)
    # Il peso da solo non basta: 5 JPEG minuscoli non giustificano 5 worker.
    return peso >= 25.0 or (len(percorsi) >= 8 and peso >= 12.0)


def processi_per_batch(percorsi, parametri):
    """Numero di processi effettivo per un elenco di file."""
    if len(percorsi) < 2:
        return 1
    profilo = parametri.get("profilo_prestazioni", "Bilanciato")
    override = 0
    if not parametri.get("processi_auto", True):
        try:
            override = int(parametri.get("processi_manuali", 0) or 0)
        except (TypeError, ValueError):
            override = 0
    processi = numero_processi_ottimale(
        len(percorsi), per_processo_mb(parametri), profilo, override
    )
    if not conviene_elaborazione_parallela(percorsi, parametri, processi):
        return 1
    return processi


def stima_tempo_batch(secondi_medio, numero_file, processi):
    """Stima prudente del tempo totale, con efficienza del parallelismo."""
    secondi_medio = max(0.05, float(secondi_medio))
    numero_file = max(1, int(numero_file))
    processi = max(1, int(processi))
    fisici = nuclei_fisici()
    if processi <= fisici:
        efficienza = 0.90
    else:
        efficienza = max(0.62, 0.90 * fisici / float(processi))
    avvio = 0.8 if processi > 1 else 0.0
    return (secondi_medio * numero_file) / (processi * efficienza) + avvio


def formatta_durata(secondi):
    """0:00 / 12:34 / 1:02:03, leggibile nella barra di stato."""
    try:
        secondi = max(0, int(round(float(secondi))))
    except (TypeError, ValueError):
        secondi = 0
    ore, resto = divmod(secondi, 3600)
    minuti, sec = divmod(resto, 60)
    if ore:
        return f"{ore}:{minuti:02d}:{sec:02d}"
    return f"{minuti}:{sec:02d}"


def benchmark_conversione(files, parametri, massimo_file=2, log=None):
    """Prova reale su 1-2 file, in una cartella temporanea.

    Gli originali vengono solo letti. Serve a sostituire le stime inventate
    con un tempo misurato sul PC e sui file dell'utente.
    """
    if not files:
        raise ValueError("Nessun file disponibile per il benchmark.")

    raw = [f for f in files if f.lower().endswith(RAW_ESTENSIONI)]
    scelti = (raw or list(files))[: max(1, int(massimo_file))]
    p = normalizza_parametri(parametri)
    for canale in (
        "cloud_telegram", "cloud_gdrive", "cloud_meta", "cloud_dropbox", "cloud_swiss",
    ):
        p[canale] = False

    cartella = tempfile.mkdtemp(prefix="frc_benchmark_")
    tempi = []
    nomi = []
    try:
        for indice, percorso in enumerate(scelti):
            uscita = os.path.join(cartella, f"bench_{indice}.jpg")
            inizio = time.perf_counter()
            ImageEngine.sviluppa_e_ottimizza(percorso, uscita, p)
            durata = max(0.001, time.perf_counter() - inizio)
            tempi.append(durata)
            nomi.append(os.path.basename(percorso))
            if log:
                try:
                    log(
                        f"Benchmark: {nomi[-1]} elaborato in {durata:.1f}s "
                        f"({p.get('max_dim') or 'originale'} px)"
                    )
                except Exception:
                    pass
            try:
                os.remove(uscita)
            except OSError:
                pass
    finally:
        shutil.rmtree(cartella, ignore_errors=True)

    media = sum(tempi) / len(tempi)
    return {
        "file": len(tempi),
        "nomi": nomi,
        "secondi": tempi,
        "secondi_medio": media,
    }


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


# ================================================================================
# 1c. SMART BATCH: ANALISI PER FILE
# ================================================================================
def _ridimensiona_per_analisi(rgb, lato=1200):
    """Riduce l'immagine per misurare istogramma e rumore in pochi ms."""
    array = np.asarray(rgb)
    if array.dtype != np.uint8:
        array = np.clip(array, 0, 255).astype(np.uint8)
    if array.ndim == 2:
        array = np.stack((array, array, array), axis=-1)
    if array.shape[2] > 3:
        array = array[:, :, :3]
    pil = Image.fromarray(array, "RGB")
    if max(pil.size) > lato:
        pil.thumbnail((lato, lato), Image.Resampling.BILINEAR)
    return np.asarray(pil, dtype=np.uint8)


def _metriche_immagine(rgb, iso=0.0, clip_raw_alto=0.0, clip_raw_basso=0.0, origine=""):
    """Misura i dati oggettivi che servono alle correzioni Smart Batch."""
    arr = _ridimensiona_per_analisi(rgb)
    base = arr.astype(np.float32) / 255.0
    lum = (
        0.2126 * base[:, :, 0]
        + 0.7152 * base[:, :, 1]
        + 0.0722 * base[:, :, 2]
    )
    p1, p5, p50, p95, p99 = (
        float(valore) for valore in np.percentile(lum, [1, 5, 50, 95, 99])
    )
    clip_alto = max(float(np.mean(lum >= 0.985)), float(clip_raw_alto or 0.0))
    clip_basso = max(float(np.mean(lum <= 0.015)), float(clip_raw_basso or 0.0))
    saturazione = float(np.mean(base.max(axis=2) - base.min(axis=2)))

    dettaglio = lum - filters.gaussian(lum, sigma=1.0, preserve_range=True)
    mediana_dettaglio = float(np.median(dettaglio))
    rumore = float(
        1.4826 * np.median(np.abs(dettaglio - mediana_dettaglio))
    )

    try:
        hsv = color.rgb2hsv(np.clip(base, 0.0, 1.0))
        incarnati = float(
            np.mean(
                (hsv[:, :, 0] <= 0.12)
                & (hsv[:, :, 1] >= 0.12)
                & (hsv[:, :, 2] >= 0.20)
            )
        )
    except Exception:
        incarnati = 0.0

    return {
        "p1": round(p1, 4),
        "p5": round(p5, 4),
        "mediana": round(p50, 4),
        "p95": round(p95, 4),
        "p99": round(p99, 4),
        "contrasto": round(p95 - p5, 4),
        "clip_alto": round(clip_alto, 5),
        "clip_basso": round(clip_basso, 5),
        "saturazione": round(saturazione, 4),
        "rumore": round(rumore, 5),
        "incarnati": round(incarnati, 4),
        "iso": int(round(float(iso or 0.0))),
        "origine": origine,
    }


def _suggerimenti_da_metriche(metriche):
    """Regole conservative: correggono solo quello che l'istogramma giustifica."""
    p5 = float(metriche.get("p5", 0.0))
    p50 = float(metriche.get("mediana", 0.45))
    p95 = float(metriche.get("p95", 0.8))
    p99 = float(metriche.get("p99", 0.95))
    clip_alto = float(metriche.get("clip_alto", 0.0))
    clip_basso = float(metriche.get("clip_basso", 0.0))
    contrasto = float(metriche.get("contrasto", p95 - p5))
    saturazione = float(metriche.get("saturazione", 0.2))
    rumore = float(metriche.get("rumore", 0.0))
    iso = float(metriche.get("iso", 0.0))
    incarnati = float(metriche.get("incarnati", 0.0))

    suggerimenti = {}
    motivi = []
    ev = 0.0

    # Esposizione: la mediana e' l'indicatore piu' stabile, ma le alte luci
    # hanno sempre la precedenza per non bruciare il cielo o il vestito bianco.
    if p50 < 0.30:
        ev = min(0.65, max(0.20, math.log2(0.45 / max(p50, 0.05)) * 0.55))
        if clip_alto > 0.006 or p99 > 0.975:
            ev = min(ev, 0.15)
        suggerimenti["esposizione"] = round(ev, 2)
        suggerimenti["ombre"] = int(min(35, max(8, (0.32 - p50) * 110)))
        motivi.append("sottoesposta")
    elif p50 > 0.56:
        ev = -min(0.65, max(0.15, math.log2(max(p50, 0.05) / 0.45) * 0.55))
        suggerimenti["esposizione"] = round(ev, 2)
        suggerimenti["luci"] = -12
        motivi.append("sovraesposta")

    # Spalla delle alte luci: qui il recupero e' reale, non un semplice
    # abbassamento globale dell'esposizione.
    if p99 >= 0.975 or clip_alto >= 0.003:
        suggerimenti["luci"] = min(int(suggerimenti.get("luci", 0)), -18)
        suggerimenti["bianchi"] = min(int(suggerimenti.get("bianchi", 0)), -10)
        suggerimenti["proteggi_luci"] = True
        if ev > 0.15:
            suggerimenti["esposizione"] = 0.15
        motivi.append("luci da proteggere")

    # Ombre chiuse: alziamo le ombre, non l'esposizione globale.
    if p5 <= 0.025 or clip_basso >= 0.02:
        suggerimenti["ombre"] = max(int(suggerimenti.get("ombre", 0)), 18)
        suggerimenti["neri"] = max(int(suggerimenti.get("neri", 0)), 5)
        motivi.append("ombre chiuse")

    # Contrasto misurato sull'ampiezza reale dell'istogramma.
    if contrasto < 0.34:
        suggerimenti["contrasto"] = 0.46
        suggerimenti["chiarezza"] = max(float(suggerimenti.get("chiarezza", 0.0)), 0.07)
        motivi.append("contrasto basso")
    elif contrasto > 0.86:
        suggerimenti["contrasto"] = 0.28
        motivi.append("contrasto alto")

    # Colore spento: vivacita' selettiva, saturazione contenuta. Sui ritratti
    # con molti incarnati la saturazione globale resta piu' prudente.
    if saturazione < 0.14:
        suggerimenti["vivacita"] = max(float(suggerimenti.get("vivacita", 0.0)), 0.48)
        suggerimenti["saturazione"] = max(float(suggerimenti.get("saturazione", 1.0)), 1.05)
        motivi.append("colore spento")
    elif saturazione < 0.20 and incarnati < 0.08:
        suggerimenti["vivacita"] = max(float(suggerimenti.get("vivacita", 0.0)), 0.42)
        suggerimenti["saturazione"] = max(float(suggerimenti.get("saturazione", 1.0)), 1.03)
        motivi.append("colore migliorabile")

    # Rumore: il denoise automatico esiste gia'; qui alziamo solo il minimo
    # necessario per file molto rumorosi.
    if iso >= 1600 or rumore >= 0.020:
        nrl = 88.0 + min(10.0, max(0.0, (iso - 800.0) / 800.0) * 2.0)
        suggerimenti["nr_luminanza"] = round(min(98.0, max(88.0, nrl)), 0)
        suggerimenti["nr_colore"] = 94.0
        if iso >= 3200:
            suggerimenti["nitidezza_quantita"] = 0.80
        motivi.append("rumore alto")

    if not suggerimenti:
        return {}, "OK", "Già bilanciata"

    critico = (
        clip_alto >= 0.02
        or clip_basso >= 0.05
        or abs(ev) >= 0.45
        or p50 < 0.18
        or p50 > 0.72
    )
    stato = "CRITICO" if critico else "CORREGGI"
    return suggerimenti, stato, ", ".join(dict.fromkeys(motivi))


def analizza_file(percorso):
    """Analizza un singolo RAW/JPEG senza modificarlo.

    Usa una decodifica RAW a mezza risoluzione (veloce ma rappresentativa)
    e legge il clipping direttamente dal sensore quando disponibile.
    """
    nome = os.path.basename(percorso)
    iso = 0.0
    clip_alto = 0.0
    clip_basso = 0.0
    origine = "RAW" if percorso.lower().endswith(RAW_ESTENSIONI) else "IMMAGINE"
    try:
        if origine == "RAW":
            with rawpy.imread(percorso) as raw:
                try:
                    iso = float(raw.other.iso_speed or 0.0)
                except Exception:
                    iso = 0.0

                try:
                    sensore = raw.raw_image_visible[::4, ::4]
                    livelli_bianchi = raw.camera_white_level_per_channel
                    if not livelli_bianchi:
                        livelli_bianchi = [raw.white_level] * 4
                    bianco = max(float(v) for v in livelli_bianchi if v)
                    clip_alto = float(np.mean(sensore >= bianco * 0.985))
                    livelli_neri = raw.black_level_per_channel or [0, 0, 0, 0]
                    nero = max(float(v) for v in livelli_neri)
                    clip_basso = float(np.mean(sensore <= nero + 32.0))
                except Exception:
                    clip_alto = 0.0
                    clip_basso = 0.0

                try:
                    # Stessa resa del batch: rawpy applica il suo auto-bright
                    # anche in conversione, quindi l'analisi deve vederla.
                    rgb = raw.postprocess(
                        half_size=True,
                        use_camera_wb=True,
                        no_auto_bright=False,
                        output_bps=8,
                        output_color=rawpy.ColorSpace.sRGB,
                    )
                except Exception:
                    thumb = raw.extract_thumb()
                    if thumb.format == rawpy.ThumbFormat.JPEG:
                        with Image.open(io.BytesIO(thumb.data)) as im:
                            rgb = np.asarray(
                                ImageOps.exif_transpose(im).convert("RGB")
                            )
                    else:
                        rgb = np.asarray(thumb.data)
        else:
            with Image.open(percorso) as im:
                try:
                    iso = float(im.getexif().get(34855, 0) or 0.0)
                except Exception:
                    iso = 0.0
                rgb = np.asarray(ImageOps.exif_transpose(im).convert("RGB"))

        metriche = _metriche_immagine(
            rgb, iso=iso, clip_raw_alto=clip_alto, clip_raw_basso=clip_basso,
            origine=origine,
        )
        suggerimenti, stato, motivo = _suggerimenti_da_metriche(metriche)
        return {
            "percorso": percorso,
            "nome": nome,
            "ok": True,
            "errore": "",
            "metriche": metriche,
            "suggerimenti": suggerimenti,
            "stato": stato,
            "motivo": motivo,
        }
    except Exception as errore:
        return {
            "percorso": percorso,
            "nome": nome,
            "ok": False,
            "errore": f"{type(errore).__name__}: {errore}",
            "metriche": {},
            "suggerimenti": {},
            "stato": "ERRORE",
            "motivo": "Analisi non disponibile",
        }


def analizza_batch(files, log=None, progresso=None, cancel_event=None, max_workers=None):
    """Analizza tutti i file in parallelo e restituisce un piano per percorso."""
    totale = len(files)
    risultati = {}
    if totale == 0:
        return risultati

    def nota(messaggio):
        if log:
            try:
                log(messaggio)
            except Exception:
                pass

    if max_workers is None:
        max_workers = max(1, min(6, os.cpu_count() or 1, totale))

    ok = errori = 0
    esecutore = ThreadPoolExecutor(max_workers=max_workers)
    futuri = {esecutore.submit(analizza_file, percorso): percorso for percorso in files}
    try:
        for indice, futuro in enumerate(as_completed(futuri), start=1):
            if cancel_event is not None and cancel_event.is_set():
                for altro in futuri:
                    altro.cancel()
                break
            percorso = futuri[futuro]
            try:
                risultato = futuro.result()
            except Exception as errore:
                risultato = {
                    "percorso": percorso,
                    "nome": os.path.basename(percorso),
                    "ok": False,
                    "errore": f"{type(errore).__name__}: {errore}",
                    "metriche": {},
                    "suggerimenti": {},
                    "stato": "ERRORE",
                    "motivo": "Analisi non disponibile",
                }
            if risultato.get("ok"):
                ok += 1
            else:
                errori += 1
                nota(f"Analisi non riuscita su {os.path.basename(percorso)}: {risultato.get('errore', '')}")
            risultati[percorso] = risultato
            if progresso:
                try:
                    progresso(indice, totale, ok, errori)
                except Exception:
                    pass
    finally:
        # Attende i pochi file gia' in corso: evita che l'analisi continui
        # in background mentre parte la conversione batch.
        esecutore.shutdown(wait=True, cancel_futures=True)
    return risultati


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
            # wait=True: il thread di gestione chiude code e semafori. Con
            # wait=False restano i "leaked semaphore objects" all'uscita.
            esecutore.shutdown(wait=True, cancel_futures=True)
        except Exception:
            pass
        with _LOCK_ESECUTORI:
            _ESECUTORI_ATTIVI.discard(esecutore)


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


def esegui_batch(
    files, params, destinazione, log=None, progresso=None, cancel_event=None,
    analisi=None,
):
    """Converte tutti i file, in parallelo su tutti i core quando possibile.

    analisi: dizionario percorso -> risultato di analizza_file(). Se presente,
    ogni file usa il proprio piano di correzione Smart Batch.
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
    analisi_per_percorso = {}
    for percorso_analisi, risultato in (analisi or {}).items():
        try:
            chiave_analisi = os.path.normcase(os.path.abspath(percorso_analisi))
            analisi_per_percorso[chiave_analisi] = risultato
        except Exception:
            continue
    parametri_per_file = {}
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

        params_file = params
        try:
            chiave_file = os.path.normcase(os.path.abspath(percorso))
            risultato_analisi = analisi_per_percorso.get(chiave_file)
        except Exception:
            risultato_analisi = None
        if isinstance(risultato_analisi, dict) and risultato_analisi.get("ok"):
            suggerimenti = risultato_analisi.get("suggerimenti") or {}
            if suggerimenti:
                params_file = dict(params)
                params_file.update(suggerimenti)
                params_file["_analisi_applicata"] = True
        parametri_per_file[percorso] = params_file

        nomi_prenotati.add(chiave)
        compiti.append((indice, percorso, output, nome))

    if analisi_per_percorso:
        quanti = sum(
            1 for percorso in parametri_per_file
            if parametri_per_file[percorso] is not params
        )
        if quanti:
            nota(f"Smart Batch: correzioni per-file applicate a {quanti} file.")

    if compiti and (cancel_event is None or not cancel_event.is_set()):
        percorsi = [compito[1] for compito in compiti]
        processi = processi_per_batch(percorsi, params)
        profilo = str(params.get("profilo_prestazioni", "Bilanciato"))
        if processi > 1:
            nota(
                f"Elaborazione parallela: {processi} processi "
                f"(profilo {profilo}, {nuclei_fisici()} core fisici / "
                f"{nuclei_logici()} logici)."
            )
        else:
            if params.get("usa_multicore", True) and len(compiti) > 1:
                nota(
                    "Elaborazione sequenziale: batch piccolo, il pool "
                    "multi-processo costerebbe piu' del lavoro risparmiato."
                )
            else:
                nota("Elaborazione sequenziale.")

        if processi <= 1:
            for indice, percorso, output, nome in compiti:
                if cancel_event is not None and cancel_event.is_set():
                    break
                esito = _converti_file_worker(
                    (percorso, output, parametri_per_file.get(percorso, params))
                )
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
                    futuro = esecutore.submit(
                        _converti_file_worker,
                        (percorso, output, parametri_per_file.get(percorso, params)),
                    )
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
                        # wait=True chiude anche le code interne: evita i
                        # semafori rimasti appesi dopo un annullamento.
                        esecutore.shutdown(wait=True, cancel_futures=True)
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
    # Il batch puo' aver lasciato molta memoria libera ma non restituita al
    # sistema: su Linux la restituiamo esplicitamente prima di aggiornare la GUI.
    libera_memoria()
    return {
        "ok": ok,
        "errori": errori,
        "saltati": saltati,
        "totale": totale,
        "annullato": annullato,
    }


# ================================================================================
# 1d. COPYRIGHT NEI METADATI: EXIF + IPTC (senza dipendenze aggiuntive)
# ================================================================================
def _iptc_dataset(record, dataset, valore):
    """Un dataset IPTC IIM: 0x1C, record, dataset, lunghezza, testo UTF-8."""
    dati = valore if isinstance(valore, bytes) else str(valore).encode("utf-8")
    return b"\x1c" + bytes((int(record), int(dataset))) + len(dati).to_bytes(2, "big") + dati


def _app13_iptc(campi):
    """Costruisce un segmento APP13/Photoshop 3.0 con i dataset IPTC.

    Scriverlo a mano evita di aggiungere iptcinfo3 al pacchetto e mantiene
    il copyright leggibile da Photoshop, Lightroom, Bridge ed ExifTool.
    """
    dataset = [_iptc_dataset(1, 90, b"\x1b%G")]  # CodedCharacterSet = UTF-8
    for record, numero, testo in campi:
        if testo:
            dataset.append(_iptc_dataset(record, numero, testo))
    dati = b"".join(dataset)
    # Photoshop Image Resource Block (8BIM), resource 0x0404 = IPTC-NAA.
    risorsa = (
        b"8BIM"
        + (0x0404).to_bytes(2, "big")
        + b"\x00\x00"  # nome Pascal vuoto, allineato a 2 byte
        + len(dati).to_bytes(4, "big")
        + dati
    )
    if len(dati) % 2:
        risorsa += b"\x00"
    payload = b"Photoshop 3.0\x00" + risorsa
    return b"\xff\xed" + (len(payload) + 2).to_bytes(2, "big") + payload


def inserisci_iptc(percorso, campi):
    """Inserisce/sostituisce il blocco IPTC in un JPEG, senza perdere l'EXIF."""
    try:
        with open(percorso, "rb") as file_immagine:
            dati = file_immagine.read()
        if not dati.startswith(b"\xff\xd8"):
            return False

        nuovo = _app13_iptc(campi)
        uscita = bytearray(b"\xff\xd8")
        indice = 2
        inserito = False
        while indice + 4 <= len(dati):
            if dati[indice] != 0xFF:
                break
            marker = dati[indice + 1]
            if marker == 0xDA:  # Start Of Scan: da qui iniziano i dati compressi
                if not inserito:
                    uscita += nuovo
                    inserito = True
                uscita += dati[indice:]
                break
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                uscita += dati[indice : indice + 2]
                indice += 2
                continue
            lunghezza = int.from_bytes(dati[indice + 2 : indice + 4], "big")
            if lunghezza < 2:
                break
            segmento = dati[indice : indice + 2 + lunghezza]
            if marker == 0xED and segmento[4:18] == b"Photoshop 3.0\x00":
                indice += 2 + lunghezza  # rimuove il vecchio IPTC
                continue
            # APP13 sta dopo JFIF/EXIF/XMP: cosi' i lettori lo trovano subito.
            if not inserito and marker not in (0xE0, 0xE1, 0xE2):
                uscita += nuovo
                inserito = True
            uscita += segmento
            indice += 2 + lunghezza
        if not inserito:
            uscita += nuovo

        with open(percorso, "wb") as file_immagine:
            file_immagine.write(uscita)
        return True
    except Exception as errore:
        logging.debug("IPTC non inserito in %s: %s", percorso, errore)
        return False


def scrivi_metadati_copyright(percorso, testo, autore="", descrizione=""):
    """Scrive Artist, Copyright e ImageDescription in EXIF e IPTC.

    Restituisce True se almeno l'EXIF e' stato aggiornato. Il file deve essere
    un JPEG: per gli altri formati la funzione non fa nulla.
    """
    percorso = str(percorso or "")
    if not percorso.lower().endswith((".jpg", ".jpeg")):
        return False
    testo = str(testo or "").strip()
    if not testo:
        return False
    autore = str(autore or "").strip() or "Franchetti"
    descrizione = str(descrizione or "").strip() or (
        f"Elaborata con Franchetti Raw Converter Pro - {testo}"
    )

    esito_exif = False
    try:
        try:
            exif = piexif.load(percorso)
        except Exception:
            exif = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        exif.setdefault("0th", {})
        exif["0th"][piexif.ImageIFD.Artist] = autore.encode("utf-8")
        exif["0th"][piexif.ImageIFD.Copyright] = testo.encode("utf-8")
        exif["0th"][piexif.ImageIFD.ImageDescription] = descrizione.encode("utf-8")
        piexif.insert(piexif.dump(exif), percorso)
        esito_exif = True
    except Exception as errore:
        logging.debug("EXIF copyright non scritto in %s: %s", percorso, errore)

    inserisci_iptc(
        percorso,
        [
            (2, 5, os.path.basename(percorso)),  # Object Name
            (2, 80, autore),  # By-line
            (2, 116, testo),  # Copyright Notice
            (2, 120, descrizione),  # Caption-Abstract
        ],
    )
    return esito_exif


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

    @classmethod
    def _proteggi_luci(cls, img, soglia=0.68, pendenza_finale=1.40):
        """Comprime la spalla delle alte luci senza perdere il punto bianco.

        Sotto la soglia l'immagine resta identica. Sopra, una curva di
        Hermite cubica mantiene continuita' di valore e di pendenza nel punto
        di innesto (niente scalino visibile), comprime i toni alti e conserva
        il bianco pieno. La pendenza finale maggiore di 1 mantiene la
        separazione tra i toni quasi bianchi invece di schiacciarli.
        """
        lum = np.clip(cls._luma(img), 0.0, 1.0)
        ampiezza = 1.0 - soglia
        u = np.clip((lum - soglia) / ampiezza, 0.0, 1.0)
        relativo = u + (1.0 - pendenza_finale) * (u * u - u * u * u)
        nuova = np.where(lum > soglia, soglia + ampiezza * relativo, lum)
        return cls._applica_luminanza(img, np.clip(nuova, 0.0, 1.0))

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

        if p.get("proteggi_luci"):
            img = cls._proteggi_luci(img)

        return img

    # ------------------------------------------------------ fase 2: colore
    @staticmethod
    def _fase_colore(img, p):
        # Vivacità selettiva: aumenta la crominanza soprattutto sui toni
        # spenti, lasciando quasi intatti i colori già saturi. La luminanza
        # resta invariata, quindi la pelle non si schiarisce né si scurisce.
        viv = float(p.get("vivacita", 0.0))
        if viv > 1e-4:
            lum = ImageEngine._luma(img)[:, :, None]
            crominanza = img.max(axis=2) - img.min(axis=2)
            obiettivo = crominanza + viv * 0.5 * crominanza * (1.0 - crominanza)
            fattore = np.where(
                crominanza > 1e-6,
                obiettivo / np.maximum(crominanza, 1e-6),
                1.0,
            )
            img = np.clip(
                lum + (img - lum) * fattore[:, :, None], 0.0, 1.0
            )

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

    @staticmethod
    def _stima_rumore(y):
        """Stima robusta del rumore fine (scala 0-1) tramite MAD.

        La mediana assoluta delle deviazioni e' poco influenzata dai bordi
        veri: e' quindi adatta a distinguere grana e dettaglio strutturato.
        """
        dettaglio = y - filters.gaussian(y, sigma=1.0, preserve_range=True)
        mediana = float(np.median(dettaglio))
        return float(1.4826 * np.median(np.abs(dettaglio - mediana)))

    @classmethod
    def _riduci_grana(cls, img, p, nrl, nrc):
        """Denoise ISO progressivo in Y/Cb/Cr con recupero del dettaglio.

        Il filtro guided crea una base priva di rumore mantenendo i bordi.
        La differenza tra originale e base viene poi "coringata": le
        variazioni molto piccole (grana) vengono spente, mentre i dettagli
        con ampiezza reale vengono conservati. In questo modo non si ottiene
        l'effetto plastica e la grana non torna visibile dopo la nitidezza.
        """
        iso = float(p.get("_iso", 0) or 0)
        fattore = 1.0
        if p.get("rimuovi_grana_auto") and iso > 0:
            if iso <= 200:
                fattore = 0.45
            elif iso <= 400:
                fattore = 0.60
            elif iso <= 800:
                fattore = 0.76
            elif iso <= 1600:
                fattore = 0.90
            elif iso <= 2000:
                fattore = 0.97
            elif iso <= 3200:
                fattore = 1.08
            elif iso <= 6400:
                fattore = 1.20
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
            raggio = max(1, int(round(1.0 + nrl * 3.0)))
            epsilon = max(0.00015, (nrl * nrl) * 0.003)
            base = cls._guided_auto(y, raggio, epsilon)
            dettaglio = y - base

            # Il rumore dipende dall'ISO ma anche dalla risoluzione finale:
            # a 3000 px la grana e' piu' fine e va trattata con una soglia
            # leggermente piu' alta rispetto a un output da 2048 px.
            massimo = max(y.shape)
            rumore_misurato = cls._stima_rumore(y)
            rumore_iso = max(0.0025, iso * 5e-6 * (massimo / 2048.0) ** 0.75) if iso > 0 else 0.003
            sigma = max(0.0025, min(0.05, max(rumore_misurato, rumore_iso)))

            # gain=1 sui dettagli forti, gain~0 sulla grana a bassa ampiezza.
            k = 2.0 + 18.0 * nrl * nrl
            gain = (dettaglio * dettaglio) / (
                dettaglio * dettaglio + k * sigma * sigma + 1e-12
            )
            y_pulita = base + dettaglio * gain

            # Secondo passaggio non-locale SOLO nelle zone piatte: elimina la
            # grana residua di pareti, cieli e ombre senza toccare i dettagli
            # (visi, capelli, tessuti), che restano affidati al coring.
            if nrl > 0.20 and min(y.shape) >= 8:
                try:
                    h_nlm = max(0.008, min(0.055, sigma * 1.55))
                    y_nlm = denoise_nl_means(
                        y,
                        patch_size=5,
                        patch_distance=6,
                        h=h_nlm,
                        fast_mode=True,
                        sigma=0.0,
                        preserve_range=True,
                    )
                    attivita = gaussian_filter(
                        np.abs(y - gaussian_filter(y, sigma=2.0, mode="reflect")),
                        sigma=3.0,
                        mode="reflect",
                    )
                    bordo = np.clip(
                        (attivita - 0.9 * sigma) / (1.8 * sigma + 1e-12), 0.0, 1.0
                    )
                    bordo = bordo * bordo * (3.0 - 2.0 * bordo)
                    piatto = 1.0 - bordo
                    y_pulita = y_pulita * (1.0 - piatto) + y_nlm * piatto
                except Exception as errore:
                    logging.debug("Denoise non-locale non applicato: %s", errore)
            y = y_pulita

        if nrc > 1e-4:
            raggio = max(3, int(round(3.0 + nrc * 9.0)))
            epsilon = max(0.0003, (nrc * nrc) * 0.004)
            # La crominanza e' a bassa frequenza: denoise a meta' risoluzione,
            # poi ricostruzione lineare. 4x piu' veloce, stesso risultato visivo.
            y_small = cls._down2(y)
            cb_small = cls._down2(cb)
            cr_small = cls._down2(cr)
            raggio_small = max(2, raggio // 2)
            cb_pulito = cls._guided(y_small, cb_small, raggio_small, epsilon)
            cr_pulito = cls._guided(y_small, cr_small, raggio_small, epsilon)
            cb_pulito = cls._up2(cb_pulito, cb.shape[1], cb.shape[0])
            cr_pulito = cls._up2(cr_pulito, cr.shape[1], cr.shape[0])
            beta = min(0.995, 0.78 + nrc * 0.215)
            cb = cb * (1.0 - beta) + cb_pulito * beta
            cr = cr * (1.0 - beta) + cr_pulito * beta

        r2 = y + cr
        b2 = y + cb
        g2 = (y - 0.299 * r2 - 0.114 * b2) / 0.587
        return np.clip(np.stack((r2, g2, b2), axis=-1), 0.0, 1.0)

    @classmethod
    def _nitidezza_controllata(cls, img, quantita, raggio):
        """Nitidezza con soglia sul rumore: niente grana amplificata.

        Il classico unsharp mask agisce anche sulle differenze minime e fa
        riemergere la grana. Qui la maschera interviene solo sui dettagli
        realmente sopra la soglia di rumore; le zone piatte restano pulite.
        """
        quantita = float(quantita)
        if quantita <= 1e-4:
            return img
        y = np.clip(cls._luma(img), 0.0, 1.0)
        scala = max(1.0, (max(img.shape[:2]) / 2048.0) ** 0.35)
        raggio = max(0.5, min(4.0, float(raggio) * scala))
        dettaglio = y - gaussian_filter(y, sigma=raggio, mode="reflect")
        sigma = cls._stima_rumore(y)
        soglia = max(0.0035, min(0.018, sigma * 1.15))
        maschera = np.clip(
            (np.abs(dettaglio) - soglia) / (2.0 * soglia + 1e-12), 0.0, 1.0
        )
        maschera = maschera * maschera * (3.0 - 2.0 * maschera)
        y = np.clip(y + dettaglio * quantita * maschera, 0.0, 1.0)
        return cls._applica_luminanza(img, y)

    @classmethod
    def _fase_lab(cls, img, p):
        """Curva tonale, denoise ISO e nitidezza controllata.

        La curva viene applicata prima del denoise: se aumenta il contrasto,
        la grana viene poi rimossa dal filtro invece di essere amplificata.
        """
        curva = p.get("curva_tonale", "Lineare")
        if curva and curva != "Lineare":
            lum = np.clip(cls._luma(img), 0.0, 1.0)
            lut = cls._curva_lut(curva) / 100.0
            indici = np.clip((lum * 255.0).astype(np.int32), 0, 255)
            img = cls._applica_luminanza(img, lut[indici])

        nrl = float(p.get("nr_luminanza", 0.0)) / 100.0
        nrc = float(p.get("nr_colore", 0.0)) / 100.0
        if nrl > 1e-4 or nrc > 1e-4:
            img = cls._riduci_grana(img, p, nrl, nrc)

        q = float(p.get("nitidezza_quantita", 0.0))
        if q > 1e-4:
            img = cls._nitidezza_controllata(
                img, q, float(p.get("nitidezza_raggio", 0.9))
            )

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

    @staticmethod
    def _tronca_testo(draw, testo, font, larghezza_max):
        """Accorcia un testo con ellissi senza uscire dall'immagine."""
        testo = str(testo or "")
        if not testo or larghezza_max <= 0:
            return testo
        try:
            if draw.textlength(testo, font=font) <= larghezza_max:
                return testo
        except Exception:
            pass

        def larghezza(candidato):
            try:
                return draw.textlength(candidato, font=font)
            except Exception:
                return len(candidato) * max(6, int(getattr(font, "size", 12)))

        ellissi = "\u2026"
        migliore = ""
        sinistra, destra = 0, len(testo)
        while sinistra <= destra:
            medio = (sinistra + destra) // 2
            candidato = testo[:medio].rstrip() + ellissi
            if larghezza(candidato) <= larghezza_max:
                migliore = candidato
                sinistra = medio + 1
            else:
                destra = medio - 1
        return migliore or ellissi

    @classmethod
    def applica_watermark_testo(cls, pil_img, testo, font_size, posizione, opacita):
        if not testo:
            return pil_img
        base = pil_img.convert("RGBA")
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = cls._carica_font(font_size)
        margine = max(12, int(base.size[0] * 0.015))
        testo = cls._tronca_testo(
            draw, testo, font, max(20, base.size[0] - 2 * margine)
        )

        try:
            box = draw.textbbox((0, 0), testo, font=font)
            tw, th = box[2] - box[0], box[3] - box[1]
        except Exception:
            tw, th = len(testo) * font_size * 0.6, font_size

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
            # Foto scura: schiarisce senza trasformare la notte in giorno.
            # Il limite 0.48 evita di amplificare a dismisura il rumore nelle
            # ombre profonde (es. notturne), mantenendo un risultato pulito.
            obiettivo = 0.48 if mediana < 0.26 else 0.44
            gamma = math.log(obiettivo) / math.log(max(mediana, 0.01))
            gamma = max(0.48, min(1.0, gamma))
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
        spinta = 0.08 + 0.05 * (1.0 - np.clip(saturazione, 0.0, 1.0))
        base = grigio + (base - grigio) * (1.0 + spinta[..., None])
        base = np.clip(base, 0.0, 1.0)
        if abs(gamma - 1.0) < 1e-6 and saturazione_max < 0.002 and luci <= 0.985:
            return pil_img
        # La nitidezza viene applicata dopo il denoise, con soglia sul rumore:
        # qui non serve un altro unsharp che farebbe riemergere la grana.
        return Image.fromarray((base * 255.0 + 0.5).astype(np.uint8), "RGB")

    _camera_matrix_supportato = None

    @staticmethod
    def _rileva_fujifilm(percorso_raw):
        """Riconosce i RAW Fujifilm anche quando rawpy non espone il Make.

        L'estensione .raf e' il caso normale; per i DNG/TIFF Fujifilm
        controlliamo l'intestazione EXIF, dove compare la stringa FUJIFILM.
        """
        if not percorso_raw:
            return False
        try:
            estensione = os.path.splitext(percorso_raw)[1].lower()
            if estensione == ".raf":
                return True
            # Fujifilm puo' produrre DNG/TIFF: cerchiamo il Make nei primi
            # blocchi del file, senza leggere inutilmente gli altri RAW.
            if estensione not in (".dng", ".tif", ".tiff"):
                return False
            with open(percorso_raw, "rb") as file_raw:
                testa = file_raw.read(1024 * 1024)
            return b"FUJIFILM" in testa.upper()
        except OSError:
            return False

    @staticmethod
    def _converti_rgb_in_bgr(rgb):
        """Converte l'output RGB di rawpy in BGR, formato atteso da OpenCV."""
        return np.ascontiguousarray(rgb[..., ::-1])

    @classmethod
    def _decodifica_raw(cls, raw, p, nota=None, percorso_raw=None):
        """Ponte RAW -> matrice BGR tramite rawpy/LibRaw.

        LibRaw legge WB e profilo colore dalla fotocamera: in questo modo
        Sony, Nikon, Canon, Fujifilm, Panasonic, OM System e Leica vengono
        calibrati automaticamente senza tabelle manuali per marca.

        Fujifilm usa AAHD (qualita' 12, adatto ai sensori X-Trans); gli altri
        marchi usano AHD (qualita' 3). Se il flag use_camera_matrix non e'
        esposto dalla versione di rawpy installata, si usa il profilo camera
        predefinito di LibRaw. L'array restituito e' BGR, pronto per OpenCV.
        """
        fujifilm = cls._rileva_fujifilm(percorso_raw)
        algoritmo_aahd = getattr(rawpy.DemosaicAlgorithm, "AAHD", None)
        algoritmo_preferito = (
            algoritmo_aahd
            if fujifilm and algoritmo_aahd is not None
            else rawpy.DemosaicAlgorithm.AHD
        )

        # Proviamo prima la combinazione richiesta; i fallback coprono
        # build di LibRaw senza AAHD e versioni di rawpy che non accettano
        # use_camera_matrix come parametro Python.
        varianti = [(algoritmo_preferito, True)]
        if fujifilm and algoritmo_preferito != rawpy.DemosaicAlgorithm.AHD:
            varianti.append((rawpy.DemosaicAlgorithm.AHD, True))
        varianti.extend([
            (algoritmo_preferito, False),
            (rawpy.DemosaicAlgorithm.AHD, False),
            (rawpy.DemosaicAlgorithm.LINEAR, False),
        ])
        if cls._camera_matrix_supportato is False:
            varianti = [(algoritmo, False) for algoritmo, _ in varianti]
        varianti_uniche = []
        for variante in varianti:
            if variante not in varianti_uniche:
                varianti_uniche.append(variante)

        ultimo_errore = None
        for algoritmo, usa_matrice_camera in varianti_uniche:
            parametri = {
                "demosaic_algorithm": algoritmo,
                # Default True: il WB camera e' la base della resa bilanciata.
                "use_camera_wb": bool(p.get("use_camera_wb", True)),
                "no_auto_bright": False,
                "output_color": rawpy.ColorSpace.sRGB,
                "output_bps": 8,
            }
            if usa_matrice_camera:
                parametri["use_camera_matrix"] = True
            try:
                rgb = raw.postprocess(**parametri)
            except Exception as errore:
                if "use_camera_matrix" in str(errore):
                    cls._camera_matrix_supportato = False
                ultimo_errore = errore
                continue

            if usa_matrice_camera:
                cls._camera_matrix_supportato = True
            if nota:
                nome = str(algoritmo).split(".")[-1]
                dettaglio = f"Demosaic: {nome} ({int(algoritmo.value)})"
                if fujifilm and algoritmo_aahd is not None and algoritmo == algoritmo_aahd:
                    dettaglio += " - sensore X-Trans"
                elif fujifilm:
                    dettaglio += " - Fujifilm fallback"
                if not usa_matrice_camera:
                    dettaglio += " - matrice camera LibRaw predefinita"
                nota(dettaglio)
            return cls._converti_rgb_in_bgr(rgb)

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
                bgr = cls._decodifica_raw(raw, p, nota, percorso_raw=percorso_raw)
                # La pipeline fotografica lavora in RGB: il ponte RAW produce
                # BGR per OpenCV, quindi riallineiamo i canali senza copiare
                # i dati (la vista negativa viene poi convertita da NumPy/PIL).
                rgb = bgr[..., ::-1]
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

        # 2b. Miglioramento automatico dell'esposizione (BETA "Piu' luminosa").
        # Va applicato PRIMA del denoise: schiarire le ombre fa emergere il
        # rumore, che deve poi essere ripulito insieme al resto dell'immagine.
        if p.get("auto_luminosita"):
            pil_auto = Image.fromarray(
                (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), "RGB"
            )
            pil_auto = cls.correggi_luminosita_auto(pil_auto)
            img = np.asarray(pil_auto, dtype=np.float32) / 255.0
            nota("Bilanciamento automatico della luminosita' e vividezza applicati")

        img = cls._fase_lab(img, p)
        img = cls._fase_effetti(img, p)

        img_finale = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
        pil_img = Image.fromarray(img_finale, "RGB")

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

        # 5. Salvataggio + EXIF + copyright nei metadati
        cls._salva(pil_img, percorso_output, p)
        cls.preserva_exif(percorso_raw, percorso_output, bool(p.get("preserva_exif", True)))
        if bool(p.get("copyright_metadati", True)):
            testo_copyright = str(p.get("watermark_text", "") or "").strip() or (
                f"\u00a9 Franchetti {datetime.now().year}"
            )
            scrivi_metadati_copyright(
                percorso_output,
                testo_copyright,
                p.get("copyright_autore", "Franchetti"),
                f"{testo_copyright} - {os.path.basename(percorso_raw)}",
            )
        nota(f"Salvato: {os.path.basename(percorso_output)}")
        # Libera subito i buffer grandi della pipeline: nei worker del pool la
        # memoria resta altrimenti occupata fino alla chiusura del processo.
        del pil_img, img, img_finale
        libera_memoria()
        return percorso_output


# ================================================================================
# 2b. ANTEPRIMA PRIMA / DOPO
# ================================================================================
def carica_anteprima(percorso, lato=900, use_camera_wb=True):
    """Decodifica una versione ridotta del file per l'anteprima interattiva.

    I RAW vengono letti a metà risoluzione (molto più veloce) e poi ridotti:
    il risultato serve solo a mostrare l'effetto delle correzioni, non a
    produrre il file finale. Gli originali non vengono mai modificati.
    """
    estensione = os.path.splitext(percorso)[1].lower()
    if estensione in RAW_ESTENSIONI:
        with rawpy.imread(percorso) as raw:
            rgb = raw.postprocess(
                half_size=True,
                use_camera_wb=bool(use_camera_wb),
                no_auto_bright=False,
                output_color=rawpy.ColorSpace.sRGB,
                output_bps=8,
            )
        immagine = Image.fromarray(rgb, "RGB")
    else:
        with Image.open(percorso) as im:
            immagine = ImageOps.exif_transpose(im).convert("RGB")
    immagine.thumbnail((int(lato), int(lato)), Image.Resampling.LANCZOS)
    return immagine.copy()


def sviluppa_anteprima(base, parametri):
    """Applica la stessa pipeline fotografica del batch a un'immagine ridotta.

    La grana viene disattivata (cambierebbe a ogni anteprima) e il denoise
    lavora alla risoluzione ridotta: l'aspetto di toni e colori resta fedele
    senza rallentare l'interfaccia.
    """
    p = normalizza_parametri(parametri)
    p["max_dim"] = 0
    p["_iso"] = 0.0
    p["grana"] = 0.0

    rgb = np.asarray(base.convert("RGB"), dtype=np.float32) / 255.0
    img = ImageEngine._fase_tono(rgb, p)
    img = ImageEngine._fase_colore(img, p)
    img = ImageEngine._fase_dettaglio(img, p)
    if p.get("auto_luminosita"):
        pil_auto = Image.fromarray(
            (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), "RGB"
        )
        pil_auto = ImageEngine.correggi_luminosita_auto(pil_auto)
        img = np.asarray(pil_auto, dtype=np.float32) / 255.0
    img = ImageEngine._fase_lab(img, p)
    img = ImageEngine._fase_effetti(img, p)
    return Image.fromarray(
        (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), "RGB"
    )


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
# 3b. RICEZIONE FTP DIRETTA DALLA FOTOCAMERA
# ================================================================================
def cartella_tethering_predefinita():
    """Cartella stabile e facile da trovare per originali e anteprime."""
    immagini = os.path.join(os.path.expanduser("~"), "Pictures")
    if not os.path.isdir(immagini):
        immagini = os.path.join(os.path.expanduser("~"), "Immagini")
    if not os.path.isdir(immagini):
        immagini = os.path.expanduser("~")
    return os.path.join(immagini, "FranchettiRawConverterPro", "Tethering")


def ip_locale_per_ftp():
    """IP LAN del PC, ricavato dal socket (non 127.0.0.1)."""
    try:
        sonda = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sonda.connect(("8.8.8.8", 80))
        except OSError:
            sonda.connect(("1.1.1.1", 80))
        indirizzo = sonda.getsockname()[0]
        sonda.close()
        if indirizzo and not indirizzo.startswith("127."):
            return indirizzo
    except Exception:
        pass
    try:
        indirizzo = socket.gethostbyname(socket.gethostname())
        return indirizzo or "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def genera_galleria_cliente(
    cartella_anteprime,
    percorso_html=None,
    titolo="Selezione cliente",
    sottotitolo="",
):
    """Crea una galleria HTML autonoma con caselle di selezione.

    Il cliente apre un solo file (index.html), guarda le anteprime e copia
    l'elenco dei nomi selezionati. Nessun server, nessuna dipendenza esterna:
    funziona anche da chiavetta USB o da una cartella condivisa.
    """
    import html as html_lib
    from urllib.parse import quote

    cartella_anteprime = os.path.abspath(str(cartella_anteprime))
    if percorso_html is None:
        percorso_html = os.path.join(
            os.path.dirname(cartella_anteprime), "Galleria_Cliente", "index.html"
        )
    percorso_html = os.path.abspath(str(percorso_html))
    os.makedirs(os.path.dirname(percorso_html), exist_ok=True)

    try:
        nomi = sorted(
            nome
            for nome in os.listdir(cartella_anteprime)
            if nome.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        )
    except OSError:
        nomi = []

    cartella_html = os.path.dirname(percorso_html)
    try:
        relativa = os.path.relpath(cartella_anteprime, cartella_html).replace(os.sep, "/")
    except ValueError:
        relativa = "."
    if relativa == ".":
        relativa = ""

    schede = []
    for nome in nomi:
        nome_html = html_lib.escape(nome)
        src = quote((relativa + "/" + nome) if relativa else nome)
        schede.append(
            '<label class="foto">'
            f'<input type="checkbox" data-nome="{nome_html}">'
            f'<img src="{src}" loading="lazy" alt="{nome_html}">'
            f'<span class="nome">{nome_html}</span>'
            "</label>"
        )
    if not schede:
        schede.append(
            '<p class="vuoto">Le anteprime compariranno qui appena la '
            "fotocamera invia i primi scatti.</p>"
        )

    titolo_html = html_lib.escape(str(titolo or "Selezione cliente"))
    sottotitolo_html = html_lib.escape(str(sottotitolo or ""))
    modello = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITOLO__</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #14181c; color: #e8edf2; }
  header { position: sticky; top: 0; z-index: 5; background: rgba(20,24,28,.96);
           border-bottom: 1px solid #2b333b; padding: 16px 22px 12px; backdrop-filter: blur(6px); }
  h1 { margin: 0 0 4px; font-size: 22px; }
  .sotto { color: #9aa0a6; font-size: 13px; margin-bottom: 10px; }
  .barra { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  button { background: #2f6f9f; color: #fff; border: 0; border-radius: 7px;
           padding: 9px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
  button:hover { background: #3b83b8; }
  button.secondario { background: #3a3f45; }
  button.secondario:hover { background: #4a5158; }
  #contatore { margin-left: auto; font-size: 13px; color: #8ab4f8; font-weight: 600; }
  #esito { min-height: 18px; color: #66bb6a; font-size: 12px; margin-top: 6px; }
  main { padding: 18px 22px 40px; }
  .griglia { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
  .foto { position: relative; display: block; background: #1b2026; border: 2px solid #2b333b;
          border-radius: 10px; padding: 8px; cursor: pointer; transition: border-color .15s, transform .15s; }
  .foto:hover { border-color: #3b83b8; transform: translateY(-1px); }
  .foto:has(input:checked) { border-color: #1f9d55; box-shadow: 0 0 0 2px rgba(31,157,85,.25); }
  .foto input { position: absolute; top: 12px; left: 12px; width: 26px; height: 26px;
                accent-color: #1f9d55; cursor: pointer; }
  .foto img { width: 100%; height: 190px; object-fit: contain; background: #0e1114; border-radius: 6px; }
  .nome { display: block; margin-top: 7px; font-size: 12px; color: #cbd3db;
          overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .vuoto { color: #9aa0a6; font-size: 14px; }
  @media (max-width: 520px) { main { padding: 12px; } .foto img { height: 150px; } }
</style>
</head>
<body>
<header>
  <h1>__TITOLO__</h1>
  <div class="sotto">__SOTTOTITOLO__</div>
  <div class="barra">
    <button onclick="tutte(true)">Seleziona tutte</button>
    <button class="secondario" onclick="tutte(false)">Deseleziona</button>
    <button onclick="copiaSelezione()">Copia selezione</button>
    <button class="secondario" onclick="scaricaElenco()">Scarica elenco .txt</button>
    <span id="contatore">0 selezionate</span>
  </div>
  <div id="esito"></div>
</header>
<main>
  <div class="griglia">
    __SCHEDE__
  </div>
</main>
<script>
const caselle = Array.from(document.querySelectorAll('.foto input[type=checkbox]'));
const contatore = document.getElementById('contatore');
const esito = document.getElementById('esito');
function aggiorna() {
  const n = caselle.filter(function (c) { return c.checked; }).length;
  contatore.textContent = n + ' selezionate';
}
function tutte(valore) {
  caselle.forEach(function (c) { c.checked = valore; });
  aggiorna();
}
function nomiSelezionati() {
  return caselle.filter(function (c) { return c.checked; }).map(function (c) { return c.dataset.nome; });
}
function copiaVecchio(testo, fatto) {
  const area = document.createElement('textarea');
  area.value = testo;
  area.style.position = 'fixed';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  try { document.execCommand('copy'); fatto(); }
  catch (e) { alert('Copia non riuscita. Elenco:\\n\\n' + testo); }
  document.body.removeChild(area);
}
function copiaSelezione() {
  const nomi = nomiSelezionati();
  if (!nomi.length) { alert('Nessuna foto selezionata.'); return; }
  const testo = nomi.join('\\n');
  function fatto() { esito.textContent = nomi.length + ' nomi copiati negli appunti.'; }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(testo).then(fatto).catch(function () { copiaVecchio(testo, fatto); });
  } else {
    copiaVecchio(testo, fatto);
  }
}
function scaricaElenco() {
  const nomi = nomiSelezionati();
  if (!nomi.length) { alert('Nessuna foto selezionata.'); return; }
  const blob = new Blob([nomi.join('\\n')], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'selezione_foto.txt';
  a.click();
  URL.revokeObjectURL(a.href);
}
caselle.forEach(function (c) { c.addEventListener('change', aggiorna); });
aggiorna();
</script>
</body>
</html>
"""
    documento = (
        modello.replace("__TITOLO__", titolo_html)
        .replace("__SOTTOTITOLO__", sottotitolo_html)
        .replace("__SCHEDE__", "\n    ".join(schede))
    )
    temporaneo = percorso_html + ".tmp"
    with open(temporaneo, "w", encoding="utf-8") as file_galleria:
        file_galleria.write(documento)
    os.replace(temporaneo, percorso_html)
    return percorso_html


class RicevitoreFTP:
    """Server FTP minimale che riceve gli scatti e crea le anteprime cliente.

    La fotocamera (o un client FTP) invia i file nella cartella Originali.
    Appena un file e' completo viene accodato a un worker che sviluppa il RAW,
    riduce il lato lungo a 2000 px, sovrappone nome file e copyright e salva
    un JPEG leggero in Anteprime_Cliente. Gli originali non vengono toccati.
    """

    UTENTE = "camera"
    PASSWORD = "1234"
    PORTA = 2121
    LATO_MASSIMO = 2000
    QUALITA_JPEG = 85

    def __init__(
        self,
        cartella_originali=None,
        cartella_anteprime=None,
        log=None,
        notifica=None,
        parametri_getter=None,
    ):
        base = cartella_tethering_predefinita()
        # Ogni accensione crea una sessione: la fotocamera vede sempre la sua
        # "home" FTP, mentre sul PC originali, anteprime e galleria restano
        # ordinati per data senza mescolare clienti diversi.
        self.sessione = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.cartella_originali = cartella_originali or os.path.join(
            base, "Originali", self.sessione
        )
        self.cartella_anteprime = cartella_anteprime or os.path.join(
            base, "Anteprime_Cliente", self.sessione
        )
        self.cartella_galleria = os.path.join(
            base, "Galleria_Cliente", self.sessione
        )
        self.percorso_galleria = os.path.join(self.cartella_galleria, "index.html")
        self._log = log
        self._notifica_esterna = notifica
        self._parametri_getter = parametri_getter
        self._server = None
        self._thread_server = None
        self._thread_worker = None
        self._stop_event = threading.Event()
        self._coda = queue.Queue()
        self._ip = ""
        self._attivo = False
        self._lock = threading.Lock()

    # ---------------------------------------------------------------- stato
    def info(self):
        return {
            "ip": self._ip or ip_locale_per_ftp(),
            "porta": self.PORTA,
            "utente": self.UTENTE,
            "password": self.PASSWORD,
            "originali": self.cartella_originali,
            "anteprime": self.cartella_anteprime,
            "galleria": self.cartella_galleria,
            "galleria_html": self.percorso_galleria,
            "sessione": self.sessione,
            "attivo": self._attivo,
        }

    def _notifica(self, messaggio):
        # Se la GUI riceve il messaggio, e' lei a scriverlo nel tab Log e a
        # inoltrarlo al logger: un logging.info anche qui produrrebbe doppioni.
        inviato = False
        if self._log:
            try:
                self._log(messaggio)
                inviato = True
            except Exception:
                inviato = False
        if not inviato:
            logging.info(messaggio)
        if self._notifica_esterna and self._notifica_esterna is not self._log:
            try:
                self._notifica_esterna(messaggio)
            except Exception:
                pass

    # ---------------------------------------------------------------- avvio
    def start(self):
        with self._lock:
            if self._attivo:
                return self.info()
            if FTPServer is None or DummyAuthorizer is None or FTPHandler is None:
                raise RuntimeError(
                    "La libreria pyftpdlib non e' installata. Esegui: "
                    "pip install pyftpdlib"
                )
            os.makedirs(self.cartella_originali, exist_ok=True)
            os.makedirs(self.cartella_anteprime, exist_ok=True)
            os.makedirs(self.cartella_galleria, exist_ok=True)
            # pyftpdlib logga ogni connessione e ogni comando: i nostri
            # messaggi sono gia' chiari e i doppioni riempiono il tab Log.
            try:
                logging.getLogger("pyftpdlib").setLevel(logging.WARNING)
            except Exception:
                pass

            autorizzatore = DummyAuthorizer()
            autorizzatore.add_user(
                self.UTENTE,
                self.PASSWORD,
                self.cartella_originali,
                perm="elradfmwMT",
            )
            ricevitore = self

            class GestoreFTP(FTPHandler):
                def on_file_received(self, file):
                    ricevitore._file_ricevuto(file)

                def on_incomplete_file_received(self, file):
                    ricevitore._notifica(
                        "Trasferimento incompleto: " + os.path.basename(str(file))
                    )

            GestoreFTP.authorizer = autorizzatore
            GestoreFTP.banner = "Franchetti Raw Converter Pro - FTP pronto"
            # Porte passive esplicite: piu' facile da aprire nel firewall.
            GestoreFTP.passive_ports = range(50000, 50100)

            self._server = FTPServer(("0.0.0.0", self.PORTA), GestoreFTP)
            self._server.max_cons = 30
            self._server.max_cons_per_ip = 8
            self._ip = ip_locale_per_ftp()
            self._stop_event.clear()
            self._attivo = True

            self._thread_worker = threading.Thread(
                target=self._ciclo_elaborazione, daemon=True
            )
            self._thread_worker.start()
            self._thread_server = threading.Thread(
                target=self._ciclo_server, daemon=True
            )
            self._thread_server.start()

        self._notifica(
            f"Server FTP attivo su {self._ip}:{self.PORTA} - "
            f"cartella originale: {self.cartella_originali}"
        )
        return self.info()

    def _ciclo_server(self):
        server = self._server
        try:
            if server is not None:
                server.serve_forever(timeout=0.5, blocking=True, handle_exit=False)
        except Exception as errore:
            if not self._stop_event.is_set():
                self._notifica(f"Server FTP interrotto: {errore}")

    def stop(self):
        with self._lock:
            if not self._attivo and self._server is None:
                return
            self._attivo = False
            self._stop_event.set()
            server = self._server
            self._server = None
        if server is not None:
            try:
                server.close_all()
            except Exception:
                pass
        for thread in (self._thread_server, self._thread_worker):
            if thread is not None:
                try:
                    thread.join(timeout=3.0)
                except Exception:
                    pass
        self._thread_server = None
        self._thread_worker = None
        self._notifica("Server FTP fermato.")

    # ------------------------------------------------------------ ricezione
    def _file_ricevuto(self, percorso):
        percorso = os.path.abspath(str(percorso))
        if not percorso.lower().endswith(ESTENSIONI_ACCETTATE):
            self._notifica(
                "File ignorato (formato non supportato): "
                + os.path.basename(percorso)
            )
            return
        self._notifica(f"File ricevuto: {os.path.basename(percorso)}")
        self._coda.put(percorso)

    def _ciclo_elaborazione(self):
        while not self._stop_event.is_set():
            try:
                percorso = self._coda.get(timeout=0.4)
            except queue.Empty:
                continue
            try:
                self._elabora(percorso)
            except Exception as errore:
                logging.exception("Errore anteprima FTP per %s", percorso)
                self._notifica(
                    f"Anteprima non riuscita per {os.path.basename(percorso)}: "
                    f"{type(errore).__name__}: {errore}"
                )
            finally:
                try:
                    self._coda.task_done()
                except Exception:
                    pass

    def _parametri_correnti(self):
        if not self._parametri_getter:
            return {}
        try:
            dati = self._parametri_getter()
            return dati if isinstance(dati, dict) else {}
        except Exception:
            return {}

    def _testo_copyright(self, parametri=None):
        parametri = (
            parametri if isinstance(parametri, dict) else self._parametri_correnti()
        )
        if not bool(parametri.get("ftp_copyright", True)):
            return ""
        testo = str(parametri.get("watermark_text", "") or "").strip()
        return testo or f"\u00a9 Franchetti {datetime.now().year}"

    def _aggiorna_galleria(self, parametri=None):
        if not bool((parametri or {}).get("ftp_galleria", True)):
            return
        try:
            genera_galleria_cliente(
                self.cartella_anteprime,
                self.percorso_galleria,
                titolo="Selezione cliente",
                sottotitolo=(
                    "Spunta le foto che vuoi e premi «Copia selezione». "
                    f"Sessione {self.sessione}."
                ),
            )
        except Exception as errore:
            logging.debug("Galleria cliente non aggiornata: %s", errore)

    def _carica_rgb(self, percorso):
        estensione = os.path.splitext(percorso)[1].lower()
        if estensione in RAW_ESTENSIONI:
            fujifilm = ImageEngine._rileva_fujifilm(percorso)
            algoritmo = (
                getattr(rawpy.DemosaicAlgorithm, "AAHD", rawpy.DemosaicAlgorithm.AHD)
                if fujifilm
                else rawpy.DemosaicAlgorithm.AHD
            )
            with rawpy.imread(percorso) as raw:
                opzioni = {
                    "demosaic_algorithm": algoritmo,
                    "use_camera_wb": True,
                    "no_auto_bright": False,
                    "output_color": rawpy.ColorSpace.sRGB,
                    "output_bps": 8,
                }
                try:
                    rgb = raw.postprocess(use_camera_matrix=True, **opzioni)
                except Exception as errore:
                    if "use_camera_matrix" not in str(errore):
                        raise
                    rgb = raw.postprocess(**opzioni)
            return rgb
        with Image.open(percorso) as immagine:
            immagine = ImageOps.exif_transpose(immagine).convert("RGB")
            return np.array(immagine)

    def _ridimensiona_bgr(self, bgr):
        altezza, larghezza = bgr.shape[:2]
        lato = max(altezza, larghezza)
        if lato <= self.LATO_MASSIMO:
            return bgr
        fattore = self.LATO_MASSIMO / float(lato)
        nuova = (
            max(1, int(round(larghezza * fattore))),
            max(1, int(round(altezza * fattore))),
        )
        if cv2 is not None:
            return cv2.resize(bgr, nuova, interpolation=cv2.INTER_LANCZOS4)
        immagine = Image.fromarray(bgr[:, :, ::-1], "RGB").resize(
            nuova, Image.Resampling.LANCZOS
        )
        return np.array(immagine)[:, :, ::-1]

    def _sovrapponi_cv(self, bgr, nome_file, copyright_testo):
        altezza, larghezza = bgr.shape[:2]
        scala = max(0.45, min(1.55, larghezza / 2600.0))
        spessore = max(1, int(round(1.6 * scala)))
        margine = max(14, int(round(larghezza * 0.012)))
        font = cv2.FONT_HERSHEY_DUPLEX

        def scrivi(testo, x, y):
            # Bordo nero piu' spesso sotto il testo bianco: leggibile su
            # sfondi chiari e scuri senza bisogno di una barra piena.
            cv2.putText(
                bgr, testo, (int(x), int(y)), font, scala,
                (0, 0, 0), spessore + 3, cv2.LINE_AA,
            )
            cv2.putText(
                bgr, testo, (int(x), int(y)), font, scala,
                (255, 255, 255), spessore, cv2.LINE_AA,
            )

        scrivi(f"File: {nome_file}", margine, altezza - margine)
        if copyright_testo:
            (larghezza_testo, _), _ = cv2.getTextSize(
                copyright_testo, font, scala, spessore + 3
            )
            x = max(margine, larghezza - margine - larghezza_testo)
            scrivi(copyright_testo, x, altezza - margine)
        return bgr

    def _sovrapponi_pil(self, immagine, nome_file, copyright_testo):
        disegno = ImageDraw.Draw(immagine)
        larghezza, altezza = immagine.size
        dimensione = max(14, int(round(larghezza / 58.0)))
        font = ImageEngine._carica_font(dimensione)
        margine = max(12, int(round(larghezza * 0.012)))

        def scrivi(testo, posizione, ancoraggio):
            x, y = posizione
            for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                disegno.text(
                    (x + dx, y + dy), testo, font=font,
                    fill=(0, 0, 0), anchor=ancoraggio,
                )
            disegno.text(
                (x, y), testo, font=font, fill=(255, 255, 255), anchor=ancoraggio
            )

        larghezza_max = max(40, int(larghezza * 0.46))
        nome_file = ImageEngine._tronca_testo(
            disegno, f"File: {nome_file}", font, larghezza_max
        )
        scrivi(nome_file, (margine, altezza - margine), "ls")
        if copyright_testo:
            copyright_testo = ImageEngine._tronca_testo(
                disegno, copyright_testo, font, larghezza_max
            )
            scrivi(
                copyright_testo, (larghezza - margine, altezza - margine), "rs"
            )
        return immagine

    def _salva_jpeg(self, immagine, percorso):
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        if cv2 is not None and isinstance(immagine, np.ndarray):
            esito, buffer = cv2.imencode(
                ".jpg",
                immagine,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(self.QUALITA_JPEG)],
            )
            if not esito:
                raise RuntimeError("codifica JPEG non riuscita")
            buffer.tofile(percorso)
            return
        if isinstance(immagine, np.ndarray):
            immagine = Image.fromarray(immagine[:, :, ::-1], "RGB")
        immagine.save(
            percorso, "JPEG", quality=self.QUALITA_JPEG, optimize=False
        )

    def _invia_cloud_anteprima(self, percorso, parametri):
        canali = (
            "cloud_telegram", "cloud_gdrive", "cloud_meta",
            "cloud_dropbox", "cloud_swiss",
        )
        if not any(bool(parametri.get(canale)) for canale in canali):
            return
        try:
            esiti = CloudDispatcher.dispatch(percorso, parametri, callback=self._notifica)
            for nome_canale, esito in esiti:
                self._notifica(
                    f"Cloud {nome_canale}: {'inviato' if esito else 'saltato'}"
                )
        except Exception as errore:
            self._notifica(f"Cloud: errore di invio ({errore})")

    def _elabora(self, percorso):
        inizio = time.time()
        nome_originale = os.path.basename(percorso)
        parametri = self._parametri_correnti()
        rgb = self._carica_rgb(percorso)

        # Overlay sempre con Pillow: cv2.putText non conosce ©, accenti o
        # caratteri Unicode e li trasformerebbe in punti interrogativi.
        immagine = Image.fromarray(rgb, "RGB")
        immagine.thumbnail(
            (self.LATO_MASSIMO, self.LATO_MASSIMO),
            Image.Resampling.LANCZOS,
        )
        copyright_testo = self._testo_copyright(parametri)
        immagine = self._sovrapponi_pil(
            immagine, nome_originale, copyright_testo
        )
        larghezza, altezza = immagine.size

        radice, _ = os.path.splitext(nome_originale)
        nome_anteprima = f"{radice}_anteprima.jpg"
        uscita = percorso_unico(
            os.path.join(self.cartella_anteprime, nome_anteprima)
        )
        self._salva_jpeg(immagine, uscita)

        if bool(parametri.get("copyright_metadati", True)):
            testo_metadati = copyright_testo or (
                f"\u00a9 Franchetti {datetime.now().year}"
            )
            scrivi_metadati_copyright(
                uscita,
                testo_metadati,
                parametri.get("copyright_autore", "Franchetti"),
                f"{testo_metadati} - {nome_originale}",
            )

        self._aggiorna_galleria(parametri)
        if bool(parametri.get("ftp_cloud_auto", False)):
            threading.Thread(
                target=self._invia_cloud_anteprima,
                args=(uscita, dict(parametri)),
                daemon=True,
            ).start()

        durata = time.time() - inizio
        self._notifica(
            f"Anteprima pronta: {os.path.basename(uscita)} "
            f"({larghezza}x{altezza}, {durata:.1f}s)"
        )


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
        self._snapshot_rapido = {}
        self._snapshot_luci = None
        self._analisi = {}
        self._analisi_files = []
        self._analisi_in_corso = False
        self._finestra_analisi = None
        self._grana_precedente = (0.0, 0.0, 0.9, 0.9)
        self._ultima_cartella = os.path.expanduser("~")
        self._coda = queue.Queue()

        # Anteprima Prima/Dopo: una sola decodifica per file, poi la pipeline
        # viene rieseguita solo sull'immagine ridotta gia' in memoria.
        self._anteprima_file = None
        self._anteprima_prima = None
        self._anteprima_dopo = None
        self._anteprima_generazione = 0
        self._anteprima_after_id = None
        self._anteprima_in_corso = False
        self._anteprima_richiesta = False
        self._anteprima_lato = 900
        self._dim_anteprima = (180, 112)
        self._dim_av_anteprima = (300, 170)
        self._dim_grande_anteprima = (520, 330)
        self._finestra_avanzate = None
        self._finestra_anteprima = None
        self._resize_prev_job = None
        self._resize_av_job = None
        self._resize_grande_job = None

        # Ricezione Wi-Fi FTP dalla fotocamera. Il server gira in un thread
        # separato; qui teniamo solo il riferimento e lo stato mostrato in UI.
        self._ftp_server = None
        self._ftp_attivo = False
        self._ftp_in_avvio = False

        # Prestazioni adattive: benchmark reale e stima del tempo.
        self._benchmark_secondi_medio = None
        self._benchmark_in_corso = False
        self._finestra_prestazioni = None
        self._perf_stato_label = None
        self._batch_inizio = None
        self._batch_totale = 0

        self._crea_interfaccia()
        self._aggiorna_stato_grana()
        self.protocol("WM_DELETE_WINDOW", self._chiudi_app)
        # Dopo il mapping della finestra normalizza lo scaling DPI: nell'exe
        # PyInstaller il fattore 125% può essere applicato due volte e tagliare
        # la parte destra dell'interfaccia.
        self.after(300, self._sincronizza_scaling)
        # Mostra subito il segnaposto dell'anteprima; se la sorgente e' gia'
        # compilata carica il primo file appena la finestra e' pronta.
        self.after(900, self._aggiorna_file_anteprima)
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
            text=f"v{APP_VERSION}  |  LibRaw  |  Multi-core  |  Wi-Fi FTP e tethering",
            font=ctk.CTkFont(size=10),
            text_color="#8ab4f8",
        ).grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=12, pady=(6, 4), sticky="nsew")
        for nome in ("Batch", "Wi-Fi FTP", "Tethering & Cloud", "Log"):
            self.tabview.add(nome)

        self._costruisci_tab_batch(self.tabview.tab("Batch"))
        self._costruisci_tab_ftp(self.tabview.tab("Wi-Fi FTP"))
        self._costruisci_tab_tethering(self.tabview.tab("Tethering & Cloud"))
        self._costruisci_tab_log(self.tabview.tab("Log"))
        # La finestra avanzata viene costruita subito (ma resta nascosta):
        # cosi' tutti i campi esistono anche se l'utente salva una configurazione
        # senza aver mai aperto gli slider.
        self._crea_finestra_avanzate()

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
                elif tipo == "analisi_progress":
                    self._aggiorna_progresso_analisi(*messaggio[1:])
                elif tipo == "analisi_done":
                    self._fine_analisi(*messaggio[1:])
                elif tipo == "anteprima_done":
                    self._fine_anteprima(*messaggio[1:])
                elif tipo == "anteprima_error":
                    self._errore_anteprima(*messaggio[1:])
                elif tipo == "ftp_evento":
                    self._ftp_evento(messaggio[1])
                elif tipo == "ftp_stato":
                    self._ftp_stato_ui(*messaggio[1:])
                elif tipo == "bench_done":
                    self._fine_benchmark(messaggio[1])
                elif tipo == "bench_error":
                    self._errore_benchmark(messaggio[1])
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
        self.entry_sorgente.bind("<Return>", lambda e: self._aggiorna_file_anteprima())
        self.entry_sorgente.bind("<FocusOut>", lambda e: self._aggiorna_file_anteprima())
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
        self.entry_max_dim.insert(0, "3000")
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
        self._evidenzia_max_dim(3000)

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

        # Denoise ISO: subito sotto PIU' LUMINOSA, nello stesso blocco.
        self.btn_rimuovi_grana = ctk.CTkButton(
            dim,
            text="RIMUOVI GRANA (AUTO ISO)",
            height=30,
            width=210,
            fg_color="#6a4c93",
            hover_color="#7e5aa8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.toggle_rimuovi_grana,
        )
        self.btn_rimuovi_grana.grid(
            row=6, column=0, columnspan=2, padx=6, pady=(2, 1), sticky="w"
        )

        # Elaborazione su tutti i core del processore
        self.chk_multicore = ctk.CTkCheckBox(
            dim,
            text=(
                f"USA TUTTI I CORE ({nuclei_fisici()} fisici / "
                f"{nuclei_logici()} logici)"
            ),
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.chk_multicore.select()
        self.chk_multicore.grid(row=7, column=0, columnspan=2, padx=6, pady=(4, 1), sticky="w")

        # Pannello prestazioni: profilo, processi e benchmark reale.
        self.btn_prestazioni = ctk.CTkButton(
            dim,
            text="PRESTAZIONI: Bilanciato - automatico",
            height=30,
            fg_color="#3a3f45",
            hover_color="#4a5158",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._apri_prestazioni,
        )
        self.btn_prestazioni.grid(
            row=8, column=0, columnspan=2, padx=(3, 2), pady=(3, 2), sticky="ew"
        )
        self._aggiorna_etichetta_prestazioni()

        # ================= ANTEPRIMA PRIMA / DOPO =================
        dx = ctk.CTkFrame(contenuto, fg_color="transparent")
        dx.grid(row=0, column=1, padx=(8, 4), pady=2, sticky="nsew")
        dx.grid_columnconfigure(0, weight=1)

        card_prev = ctk.CTkFrame(dx)
        card_prev.grid(row=0, column=0, sticky="ew")
        card_prev.grid_columnconfigure(0, weight=1, uniform="prev")
        card_prev.grid_columnconfigure(1, weight=1, uniform="prev")
        card_prev.bind("<Configure>", self._on_prev_resize)
        larghezza_ant, altezza_ant = self._dim_anteprima

        ctk.CTkLabel(
            card_prev,
            text="ANTEPRIMA PRIMA / DOPO",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 1), sticky="w")
        self.lbl_anteprima_info = ctk.CTkLabel(
            card_prev,
            text="Seleziona una sorgente per vedere l'anteprima.",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=400,
        )
        self.lbl_anteprima_info.grid(
            row=1, column=0, columnspan=2, padx=10, pady=(0, 4), sticky="w"
        )

        self.lbl_anteprima_prima = ctk.CTkLabel(
            card_prev,
            text="PRIMA",
            width=larghezza_ant,
            height=altezza_ant,
            fg_color="#1b1f24",
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9aa0a6",
        )
        self.lbl_anteprima_prima.grid(row=2, column=0, padx=(10, 4), pady=2, sticky="ew")
        self.lbl_anteprima_dopo = ctk.CTkLabel(
            card_prev,
            text="DOPO",
            width=180,
            height=112,
            fg_color="#1b1f24",
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9aa0a6",
        )
        self.lbl_anteprima_dopo.grid(row=2, column=1, padx=(4, 10), pady=2, sticky="ew")
        ctk.CTkLabel(
            card_prev, text="PRIMA", font=ctk.CTkFont(size=9), text_color="#9aa0a6"
        ).grid(row=3, column=0, pady=(0, 2))
        ctk.CTkLabel(
            card_prev, text="DOPO", font=ctk.CTkFont(size=9), text_color="#9aa0a6"
        ).grid(row=3, column=1, pady=(0, 2))

        ctk.CTkButton(
            card_prev,
            text="APRI ANTEPRIMA GRANDE",
            height=28,
            fg_color="#3a3f45",
            hover_color="#4a5158",
            font=ctk.CTkFont(size=11),
            command=self._apri_anteprima_grande,
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=(2, 8), sticky="ew")

        # ---- Correzioni rapide: restano nella finestra di conversione.
        self._costruisci_correzioni_rapide(dx, riga=1)

        ctk.CTkButton(
            dx,
            text="AVANZATE  ▸  slider completi, nomi, watermark, preset",
            height=36,
            fg_color="#2f6f9f",
            hover_color="#3b83b8",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._apri_avanzate,
        ).grid(row=2, column=0, sticky="ew", pady=(6, 0))

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

        self.btn_analizza = ctk.CTkButton(
            azioni, text="ANALIZZA FILE", height=42, width=170,
            fg_color="#2f6f9f", hover_color="#3b83b8",
            font=ctk.CTkFont(size=13, weight="bold"), command=self.avvia_analisi,
        )
        self.btn_analizza.grid(row=0, column=2, padx=4, pady=6)

        self.chk_usa_analisi = ctk.CTkCheckBox(
            azioni, text="Usa correzioni per file",
            font=ctk.CTkFont(size=11),
        )
        self.chk_usa_analisi.grid(row=0, column=3, padx=(4, 8), pady=6, sticky="w")

        self.progress = ctk.CTkProgressBar(azioni)
        self.progress.grid(row=1, column=0, columnspan=4, padx=4, pady=(2, 4), sticky="ew")
        self.progress.set(0)

        self.lbl_progresso = ctk.CTkLabel(azioni, text="In attesa", font=ctk.CTkFont(size=12))
        self.lbl_progresso.grid(row=2, column=0, columnspan=3, padx=4, pady=(0, 4), sticky="w")

        ctk.CTkButton(azioni, text="Apri cartella output", width=170, command=self.apri_cartella_output).grid(
            row=2, column=3, padx=4, pady=(0, 4), sticky="e"
        )

    # ------------------------------------------------ correzioni rapide (UI)
    def _costruisci_correzioni_rapide(self, parent, riga=0):
        """Pulsanti Smart Batch condivisi dalla finestra di conversione."""
        card_rapide = ctk.CTkFrame(parent)
        card_rapide.grid(row=riga, column=0, sticky="ew", pady=(6, 0))
        card_rapide.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_rapide,
            text="CORREZIONI RAPIDE",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
        ctk.CTkLabel(
            card_rapide,
            text="Cumulative e reversibili: l'anteprima si aggiorna subito.",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
        ).grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

        griglia_rapide = ctk.CTkFrame(card_rapide, fg_color="transparent")
        griglia_rapide.grid(row=2, column=0, padx=6, pady=(0, 4), sticky="ew")
        for colonna in range(3):
            griglia_rapide.grid_columnconfigure(colonna, weight=1, uniform="rapide")

        pulsanti_rapidi = [
            ("CONTRASTO NATURALE", "contrasto", "#2f6f9f", "#3b83b8"),
            ("SALVA LUCI", "luci", "#8a5a1f", "#a56d26"),
            ("COLORE PIÙ RICCO", "colore", "#7b3f8f", "#9250a8"),
            ("SOVRAESPOSTA", "sovra", "#8a3f2f", "#a54d39"),
            ("SOTTOESPOSTA", "sotto", "#2f6f5f", "#3b8a75"),
            ("ANNULLA CORREZIONI", "annulla", "#4a5158", "#5d666e"),
        ]
        self._bottoni_rapidi = {}
        for indice, (testo, chiave, colore, hover) in enumerate(pulsanti_rapidi):
            bottone = ctk.CTkButton(
                griglia_rapide,
                text=testo,
                height=32,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=colore,
                hover_color=hover,
                command=lambda k=chiave: self._correzione_rapida(k),
            )
            bottone.grid(
                row=indice // 3,
                column=indice % 3,
                padx=4,
                pady=3,
                sticky="ew",
            )
            self._bottoni_rapidi[chiave] = bottone

        self.sw_proteggi_luci = ctk.CTkSwitch(
            card_rapide,
            text="Proteggi luci attivo",
            font=ctk.CTkFont(size=11),
            command=lambda: self._toggle_proteggi_luci(self.sw_proteggi_luci.get()),
        )
        self.sw_proteggi_luci.grid(row=3, column=0, padx=10, pady=(2, 8), sticky="w")
        return card_rapide

    # -------------------------------------------------- finestra AVANZATE
    def _crea_finestra_avanzate(self):
        """Costruisce (nascosta) la finestra con slider e opzioni di output."""
        finestra = ctk.CTkToplevel(self)
        self._finestra_avanzate = finestra
        finestra.title("Regolazioni avanzate - Franchetti Raw Converter Pro")
        finestra.geometry("900x760")
        finestra.minsize(760, 560)
        finestra.transient(self)
        finestra.withdraw()
        finestra.protocol("WM_DELETE_WINDOW", self._chiudi_avanzate)
        finestra.grid_columnconfigure(0, weight=1)
        finestra.grid_rowconfigure(1, weight=1)

        testata = ctk.CTkFrame(finestra, fg_color="transparent")
        testata.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
        testata.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            testata,
            text="REGOLAZIONI AVANZATE",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            testata,
            text="Sviluppo, nomi file, watermark e preset. Le modifiche si vedono nell'anteprima.",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkButton(
            testata, text="Chiudi", width=100, command=self._chiudi_avanzate
        ).grid(row=0, column=1, rowspan=2, padx=(8, 0), sticky="e")

        scroll = ctk.CTkScrollableFrame(
            finestra, label_text="Sviluppo, nomi, watermark e preset"
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        scroll.grid_columnconfigure(0, weight=1)

        # Anteprima compatta anche qui: gli slider restano sotto controllo.
        card_prev = ctk.CTkFrame(scroll)
        card_prev.pack(fill="x", padx=6, pady=(6, 2))
        card_prev.grid_columnconfigure(0, weight=1, uniform="avprev")
        card_prev.grid_columnconfigure(1, weight=1, uniform="avprev")
        card_prev.bind("<Configure>", self._on_av_prev_resize)
        larghezza_av, altezza_av = self._dim_av_anteprima
        ctk.CTkLabel(
            card_prev,
            text="ANTEPRIMA PRIMA / DOPO",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(8, 1), sticky="w")
        self.lbl_av_info = ctk.CTkLabel(
            card_prev,
            text="Seleziona una sorgente per vedere l'anteprima.",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
        )
        self.lbl_av_info.grid(
            row=1, column=0, columnspan=2, padx=10, pady=(0, 4), sticky="w"
        )
        self.lbl_av_prima = ctk.CTkLabel(
            card_prev,
            text="PRIMA",
            width=larghezza_av,
            height=altezza_av,
            fg_color="#1b1f24",
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9aa0a6",
        )
        self.lbl_av_prima.grid(row=2, column=0, padx=(10, 4), pady=(2, 8), sticky="ew")
        self.lbl_av_dopo = ctk.CTkLabel(
            card_prev,
            text="DOPO",
            width=larghezza_av,
            height=altezza_av,
            fg_color="#1b1f24",
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9aa0a6",
        )
        self.lbl_av_dopo.grid(row=2, column=1, padx=(4, 10), pady=(2, 8), sticky="ew")

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
                ("nitidezza_quantita", "Nitidezza (quantità)", 0.0, 5.0, 0.9, "{:.2f}"),
                ("nitidezza_raggio", "Nitidezza (raggio)", 0.5, 4.0, 0.9, "{:.1f}"),
                ("nr_luminanza", "Riduzione rumore luminanza", 0.0, 100.0, 88.0, "{:.0f}"),
                ("nr_colore", "Riduzione rumore colore", 0.0, 100.0, 92.0, "{:.0f}"),
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
            width=170, command=self._on_curva_tonale,
        )
        self.combo_curva.set(self.parametri.get("curva_tonale", "Lineare"))
        self.combo_curva.grid(row=1, column=1, padx=10, pady=4, sticky="w")

        self._crea_slider(card2, 2, "intensita_ombre", "Split toning ombre (intensità)", 0.0, 100.0, 0.0, "{:.0f}")
        self.entry_colore_ombre = self._crea_entry_colore(card2, 3, "Colore ombre", "#2b4c7e", "colore_ombre")
        self._crea_slider(card2, 4, "intensita_luci", "Split toning luci (intensità)", 0.0, 100.0, 0.0, "{:.0f}")
        self.entry_colore_luci = self._crea_entry_colore(card2, 5, "Colore luci", "#e0b070", "colore_luci")

        # ---- Nomi file, watermark, preset (prima nel tab Batch)
        card3 = ctk.CTkFrame(scroll)
        card3.pack(fill="x", padx=6, pady=6)
        card3.grid_columnconfigure(1, weight=1)
        r = 0
        ctk.CTkLabel(card3, text="NOMI FILE E SOVRASCRITTURA",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=10, pady=(8, 2), sticky="w"
        ); r += 1

        self.chk_mantieni_nomi = ctk.CTkCheckBox(card3, text="Mantieni nome originale")
        self.chk_mantieni_nomi.select()
        self.chk_mantieni_nomi.grid(row=r, column=0, columnspan=2, padx=10, pady=3, sticky="w")
        r += 1

        nomi = ctk.CTkFrame(card3, fg_color="transparent")
        nomi.grid(row=r, column=0, columnspan=2, padx=10, pady=2, sticky="ew")
        nomi.grid_columnconfigure(1, weight=1)
        nomi.grid_columnconfigure(3, weight=1)
        r += 1

        ctk.CTkLabel(nomi, text="Prefisso:").grid(row=0, column=0, padx=(0, 2), pady=3, sticky="w")
        self.entry_prefisso = ctk.CTkEntry(nomi, width=120, placeholder_text="FRC_")
        self.entry_prefisso.grid(row=0, column=1, padx=(0, 8), pady=3, sticky="ew")

        ctk.CTkLabel(nomi, text="Suffisso:").grid(row=0, column=2, padx=(0, 2), pady=3, sticky="w")
        self.entry_suffisso = ctk.CTkEntry(nomi, width=120, placeholder_text="_web")
        self.entry_suffisso.grid(row=0, column=3, padx=(0, 0), pady=3, sticky="ew")

        ctk.CTkLabel(nomi, text="Se esiste:").grid(row=1, column=0, padx=(0, 2), pady=3, sticky="w")
        self.combo_sovrascrittura = ctk.CTkComboBox(
            nomi, values=["Rinomina", "Sovrascrivi", "Salta"], width=150,
            command=lambda v: self.parametri.__setitem__("sovrascrittura", v),
        )
        self.combo_sovrascrittura.set(self.parametri.get("sovrascrittura", "Rinomina"))
        self.combo_sovrascrittura.grid(row=1, column=1, columnspan=3, padx=(0, 0), pady=3, sticky="w")

        ctk.CTkLabel(card3, text="WATERMARK", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=10, pady=(8, 2), sticky="w"
        ); r += 1

        self.chk_watermark = ctk.CTkCheckBox(card3, text="Applica testo")
        self.chk_watermark.select()
        self.chk_watermark.grid(row=r, column=0, columnspan=2, padx=10, pady=3, sticky="w")
        r += 1

        self.entry_watermark = ctk.CTkEntry(card3, placeholder_text="Testo watermark")
        self.entry_watermark.insert(0, self.parametri["watermark_text"])
        self.entry_watermark.grid(row=r, column=0, columnspan=2, padx=10, pady=3, sticky="ew")
        r += 1

        wm = ctk.CTkFrame(card3, fg_color="transparent")
        wm.grid(row=r, column=0, columnspan=2, padx=10, pady=2, sticky="ew")
        wm.grid_columnconfigure(1, weight=1)
        wm.grid_columnconfigure(3, weight=1)
        r += 1

        ctk.CTkLabel(wm, text="Font (px):").grid(row=0, column=0, padx=(0, 2), pady=3, sticky="w")
        self.entry_font_size = ctk.CTkEntry(wm, width=70)
        self.entry_font_size.insert(0, "14")
        self.entry_font_size.grid(row=0, column=1, padx=(0, 8), pady=3, sticky="w")

        ctk.CTkLabel(wm, text="Posizione:").grid(row=0, column=2, padx=(0, 4), pady=3, sticky="w")
        self.combo_posizione = ctk.CTkComboBox(
            wm,
            values=["Basso a destra", "Basso a sinistra", "Alto a destra", "Alto a sinistra", "Centro"],
            width=150,
            command=lambda v: self.parametri.__setitem__("watermark_posizione", v),
        )
        self.combo_posizione.set(self.parametri.get("watermark_posizione", "Basso a destra"))
        self.combo_posizione.grid(row=0, column=3, padx=(0, 0), pady=3, sticky="w")

        ctk.CTkLabel(wm, text="Logo PNG:").grid(row=1, column=0, padx=(0, 2), pady=3, sticky="w")
        self.lbl_logo = ctk.CTkLabel(wm, text="Nessun logo", anchor="w", text_color="#9aa0a6")
        self.lbl_logo.grid(row=1, column=1, padx=(0, 8), pady=3, sticky="ew")
        ctk.CTkButton(wm, text="Carica", width=90, command=self.seleziona_logo).grid(
            row=1, column=2, columnspan=2, padx=(0, 0), pady=3, sticky="w"
        )

        ctk.CTkLabel(wm, text="Autore (EXIF):").grid(
            row=2, column=0, padx=(0, 2), pady=3, sticky="w"
        )
        self.entry_copyright_autore = ctk.CTkEntry(
            wm, placeholder_text="Franchetti"
        )
        self.entry_copyright_autore.insert(
            0, self.parametri.get("copyright_autore", "Franchetti")
        )
        self.entry_copyright_autore.grid(
            row=2, column=1, columnspan=3, padx=(0, 0), pady=3, sticky="ew"
        )

        ctk.CTkLabel(card3, text="PRESET E CONFIGURAZIONE",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=10, pady=(8, 2), sticky="w"
        ); r += 1

        self.combo_preset = ctk.CTkComboBox(
            card3,
            values=["Personalizzato", "Web / Social", "Stampa Fine Art", "Archivio JPEG",
                    "Ritratto", "Paesaggio", "Bianco e Nero"],
            width=190,
            command=self.applica_preset,
        )
        self.combo_preset.set("Personalizzato")
        self.combo_preset.grid(row=r, column=0, padx=10, pady=3, sticky="w")
        r += 1

        cfg = ctk.CTkFrame(card3, fg_color="transparent")
        cfg.grid(row=r, column=0, columnspan=2, padx=10, pady=(2, 8), sticky="ew")
        ctk.CTkButton(cfg, text="Salva config", width=130,
                      command=self.salva_configurazione).pack(side="left", padx=(0, 6))
        ctk.CTkButton(cfg, text="Carica config", width=130,
                      command=self.carica_configurazione).pack(side="left")

        ctk.CTkButton(
            scroll, text="Ripristina tutti i parametri di sviluppo",
            command=self.ripristina_sviluppo,
        ).pack(pady=12)

    def _apri_avanzate(self):
        finestra = self._finestra_avanzate
        if finestra is None or not finestra.winfo_exists():
            self._crea_finestra_avanzate()
            finestra = self._finestra_avanzate
        try:
            larghezza = 900
            altezza = min(760, max(560, self.winfo_screenheight() - 90))
            x = max(10, self.winfo_screenwidth() - larghezza - 20)
            y = max(10, (self.winfo_screenheight() - altezza) // 2)
            finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")
        except Exception:
            pass
        finestra.deiconify()
        try:
            finestra.lift()
            finestra.after(80, finestra.focus_force)
        except Exception:
            pass

    def _chiudi_avanzate(self):
        try:
            self._raccogli_campi()
        except Exception:
            pass
        self._programma_anteprima()
        try:
            if self._finestra_avanzate is not None:
                self._finestra_avanzate.withdraw()
        except Exception:
            pass

    # -------------------------------------------------- anteprima Prima/Dopo
    def _file_anteprima_corrente(self):
        try:
            sorgente = self.entry_sorgente.get().strip()
        except Exception:
            return None
        if not sorgente:
            return None
        try:
            destinazione = self.entry_destinazione.get().strip() or None
        except Exception:
            destinazione = None
        try:
            files = raccogli_file_sorgente(
                sorgente, bool(self.parametri.get("ricorsivo", True)), escludi=destinazione
            )
        except Exception:
            return None
        return files[0] if files else None

    def _imposta_info_anteprima(self, testo):
        for nome in ("lbl_anteprima_info", "lbl_av_info"):
            etichetta = getattr(self, nome, None)
            if etichetta is None:
                continue
            try:
                etichetta.configure(text=testo)
            except Exception:
                pass

    def _mostra_segnaposto_anteprima(self, messaggio):
        self._imposta_info_anteprima(messaggio)
        for nome, testo in (
            ("lbl_anteprima_prima", "PRIMA"),
            ("lbl_anteprima_dopo", "DOPO"),
            ("lbl_av_prima", "PRIMA"),
            ("lbl_av_dopo", "DOPO"),
        ):
            etichetta = getattr(self, nome, None)
            if etichetta is None:
                continue
            try:
                etichetta.configure(image="", text=testo)
            except Exception:
                pass

    def _aggiorna_file_anteprima(self, forza=False):
        """Sceglie il primo file della sorgente e prepara la base ridotta."""
        percorso = self._file_anteprima_corrente()
        if not forza and percorso == self._anteprima_file:
            return
        self._anteprima_file = percorso
        self._anteprima_prima = None
        self._anteprima_dopo = None
        self._anteprima_generazione += 1
        if not percorso:
            self._mostra_segnaposto_anteprima(
                "Seleziona una cartella o un file: l'anteprima mostra il primo file."
            )
            return
        self._imposta_info_anteprima(
            f"File: {os.path.basename(percorso)} - caricamento anteprima..."
        )
        self._programma_anteprima(immediato=True)

    def _programma_anteprima(self, immediato=False):
        """Aggiorna l'anteprima con un piccolo debounce durante gli slider."""
        if getattr(self, "lbl_anteprima_prima", None) is None:
            return
        precedente = self._anteprima_after_id
        if precedente:
            try:
                self.after_cancel(precedente)
            except Exception:
                pass
            self._anteprima_after_id = None
        try:
            self._anteprima_after_id = self.after(
                0 if immediato else 320, self._avvia_anteprima
            )
        except Exception:
            self._anteprima_after_id = None

    def _avvia_anteprima(self):
        self._anteprima_after_id = None
        if not self._anteprima_file:
            self._aggiorna_file_anteprima()
            if not self._anteprima_file:
                return
        if self._anteprima_in_corso:
            self._anteprima_richiesta = True
            return
        self._anteprima_generazione += 1
        generazione = self._anteprima_generazione
        self._anteprima_richiesta = False
        self._anteprima_in_corso = True
        base = self._anteprima_prima
        percorso = self._anteprima_file
        parametri = normalizza_parametri(self.parametri)
        usa_wb = bool(self.parametri.get("use_camera_wb", True))
        threading.Thread(
            target=self._anteprima_worker,
            args=(generazione, percorso, base, parametri, usa_wb),
            daemon=True,
        ).start()

    def _anteprima_worker(self, generazione, percorso, base, parametri, usa_wb):
        try:
            if base is None:
                base = carica_anteprima(
                    percorso, lato=self._anteprima_lato, use_camera_wb=usa_wb
                )
            dopo = sviluppa_anteprima(base, parametri)
            self._coda.put(("anteprima_done", generazione, percorso, base, dopo))
        except Exception as errore:
            logging.debug("Anteprima non disponibile per %s: %s", percorso, errore)
            self._coda.put(
                (
                    "anteprima_error",
                    generazione,
                    percorso,
                    f"{type(errore).__name__}: {errore}",
                )
            )

    def _fine_anteprima(self, generazione, percorso, base, dopo):
        self._anteprima_in_corso = False
        if percorso == self._anteprima_file:
            self._anteprima_prima = base
            if generazione == self._anteprima_generazione:
                self._anteprima_dopo = dopo
                self._mostra_anteprima(base, dopo)
        if self._anteprima_richiesta:
            self._anteprima_richiesta = False
            self._programma_anteprima(immediato=True)

    def _errore_anteprima(self, generazione, percorso, errore):
        self._anteprima_in_corso = False
        if percorso == self._anteprima_file:
            self._imposta_info_anteprima(f"Anteprima non disponibile: {errore}")
        if self._anteprima_richiesta:
            self._anteprima_richiesta = False
            self._programma_anteprima(immediato=True)

    def _aggiorna_immagine_label(self, etichetta, immagine, dimensione, segnaposto):
        if etichetta is None:
            return
        if immagine is None:
            try:
                etichetta.configure(image="", text=segnaposto)
            except Exception:
                pass
            return
        try:
            # "contain" mostra tutta la foto: con "fit" i ritratti verticali
            # perdevano testa e piedi. Il fondo scuro riempie i bordi senza
            # deformare l'immagine.
            originale = immagine.convert("RGB")
            contenuta = ImageOps.contain(
                originale, dimensione, Image.Resampling.LANCZOS
            )
            miniatura = Image.new("RGB", dimensione, (27, 31, 36))
            miniatura.paste(
                contenuta,
                (
                    max(0, (dimensione[0] - contenuta.size[0]) // 2),
                    max(0, (dimensione[1] - contenuta.size[1]) // 2),
                ),
            )
            ctk_immagine = ctk.CTkImage(
                light_image=miniatura, dark_image=miniatura, size=dimensione
            )
            # Il riferimento deve restare agganciato alla label: se lo
            # tenessimo solo in una lista, ogni ridisegno ne aggiungerebbe
            # uno nuovo finche' la finestra non viene chiusa.
            try:
                etichetta._immagine_ctk = ctk_immagine
            except Exception:
                pass
            etichetta.configure(image=ctk_immagine, text="")
        except Exception:
            try:
                etichetta.configure(image="", text=segnaposto)
            except Exception:
                pass

    def _mostra_anteprima(self, prima, dopo):
        self._aggiorna_immagine_label(
            getattr(self, "lbl_anteprima_prima", None), prima, self._dim_anteprima, "PRIMA"
        )
        self._aggiorna_immagine_label(
            getattr(self, "lbl_anteprima_dopo", None), dopo, self._dim_anteprima, "DOPO"
        )
        self._aggiorna_immagine_label(
            getattr(self, "lbl_av_prima", None), prima, self._dim_av_anteprima, "PRIMA"
        )
        self._aggiorna_immagine_label(
            getattr(self, "lbl_av_dopo", None), dopo, self._dim_av_anteprima, "DOPO"
        )
        self._aggiorna_immagine_label(
            getattr(self, "lbl_grande_prima", None), prima, self._dim_grande_anteprima, "PRIMA"
        )
        self._aggiorna_immagine_label(
            getattr(self, "lbl_grande_dopo", None), dopo, self._dim_grande_anteprima, "DOPO"
        )
        if self._anteprima_file:
            self._imposta_info_anteprima(
                f"{os.path.basename(self._anteprima_file)} - anteprima rapida "
                f"{prima.size[0]}x{prima.size[1]} px (l'originale non viene modificato)."
            )

    # ------------------------------------------------ ridimensionamento live
    def _on_prev_resize(self, evento=None):
        if self._resize_prev_job:
            try:
                self.after_cancel(self._resize_prev_job)
            except Exception:
                pass
        self._resize_prev_job = self.after(220, self._applica_resize_prev)

    def _applica_resize_prev(self):
        self._resize_prev_job = None
        etichetta = getattr(self, "lbl_anteprima_prima", None)
        if etichetta is None:
            return
        try:
            larghezza = max(140, (etichetta.master.winfo_width() - 40) // 2)
        except Exception:
            return
        altezza = max(90, int(round(larghezza * 0.62)))
        if (
            abs(larghezza - self._dim_anteprima[0]) < 8
            and abs(altezza - self._dim_anteprima[1]) < 8
        ):
            return
        self._dim_anteprima = (larghezza, altezza)
        for nome in ("lbl_anteprima_prima", "lbl_anteprima_dopo"):
            widget = getattr(self, nome, None)
            if widget is not None:
                try:
                    widget.configure(width=larghezza, height=altezza)
                except Exception:
                    pass
        if self._anteprima_prima is not None and self._anteprima_dopo is not None:
            self._aggiorna_immagine_label(
                getattr(self, "lbl_anteprima_prima", None),
                self._anteprima_prima,
                self._dim_anteprima,
                "PRIMA",
            )
            self._aggiorna_immagine_label(
                getattr(self, "lbl_anteprima_dopo", None),
                self._anteprima_dopo,
                self._dim_anteprima,
                "DOPO",
            )

    def _on_av_prev_resize(self, evento=None):
        if self._resize_av_job:
            try:
                self.after_cancel(self._resize_av_job)
            except Exception:
                pass
        self._resize_av_job = self.after(220, self._applica_resize_av)

    def _applica_resize_av(self):
        self._resize_av_job = None
        etichetta = getattr(self, "lbl_av_prima", None)
        if etichetta is None:
            return
        try:
            larghezza = max(200, (etichetta.master.winfo_width() - 40) // 2)
        except Exception:
            return
        altezza = max(130, int(round(larghezza * 0.58)))
        if (
            abs(larghezza - self._dim_av_anteprima[0]) < 8
            and abs(altezza - self._dim_av_anteprima[1]) < 8
        ):
            return
        self._dim_av_anteprima = (larghezza, altezza)
        for nome in ("lbl_av_prima", "lbl_av_dopo"):
            widget = getattr(self, nome, None)
            if widget is not None:
                try:
                    widget.configure(width=larghezza, height=altezza)
                except Exception:
                    pass
        if self._anteprima_prima is not None and self._anteprima_dopo is not None:
            self._aggiorna_immagine_label(
                getattr(self, "lbl_av_prima", None),
                self._anteprima_prima,
                self._dim_av_anteprima,
                "PRIMA",
            )
            self._aggiorna_immagine_label(
                getattr(self, "lbl_av_dopo", None),
                self._anteprima_dopo,
                self._dim_av_anteprima,
                "DOPO",
            )

    def _on_grande_resize(self, evento=None):
        if self._resize_grande_job:
            try:
                self.after_cancel(self._resize_grande_job)
            except Exception:
                pass
        self._resize_grande_job = self.after(220, self._applica_resize_grande)

    def _applica_resize_grande(self):
        self._resize_grande_job = None
        finestra = self._finestra_anteprima
        if finestra is None:
            return
        try:
            larghezza = max(240, (finestra.winfo_width() - 42) // 2)
            altezza = max(160, finestra.winfo_height() - 78)
        except Exception:
            return
        if (
            abs(larghezza - self._dim_grande_anteprima[0]) < 8
            and abs(altezza - self._dim_grande_anteprima[1]) < 8
        ):
            return
        self._dim_grande_anteprima = (larghezza, altezza)
        if self._anteprima_prima is not None and self._anteprima_dopo is not None:
            self._aggiorna_immagine_label(
                getattr(self, "lbl_grande_prima", None),
                self._anteprima_prima,
                self._dim_grande_anteprima,
                "PRIMA",
            )
            self._aggiorna_immagine_label(
                getattr(self, "lbl_grande_dopo", None),
                self._anteprima_dopo,
                self._dim_grande_anteprima,
                "DOPO",
            )

    def _apri_anteprima_grande(self):
        if self._anteprima_prima is None or self._anteprima_dopo is None:
            messagebox.showinfo(
                "Anteprima",
                "Seleziona prima una sorgente con almeno un file RAW o un'immagine.",
            )
            return
        finestra = self._finestra_anteprima
        if finestra is not None and finestra.winfo_exists():
            finestra.deiconify()
            finestra.lift()
            self._mostra_anteprima(self._anteprima_prima, self._anteprima_dopo)
            return

        finestra = ctk.CTkToplevel(self)
        self._finestra_anteprima = finestra
        finestra.title("Anteprima Prima / Dopo - Franchetti Raw Converter Pro")
        finestra.geometry("1120x470")
        finestra.minsize(820, 360)
        finestra.transient(self)
        finestra.grid_columnconfigure(0, weight=1, uniform="grande")
        finestra.grid_columnconfigure(1, weight=1, uniform="grande")
        finestra.grid_rowconfigure(1, weight=1)
        finestra.bind("<Configure>", self._on_grande_resize)

        ctk.CTkLabel(
            finestra,
            text="PRIMA",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(10, 2))
        ctk.CTkLabel(
            finestra,
            text="DOPO",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#66bb6a",
        ).grid(row=0, column=1, padx=12, pady=(10, 2))
        self.lbl_grande_prima = ctk.CTkLabel(
            finestra, text="PRIMA", fg_color="#1b1f24", corner_radius=8,
            text_color="#9aa0a6",
        )
        self.lbl_grande_prima.grid(row=1, column=0, padx=(12, 6), pady=(0, 10), sticky="nsew")
        self.lbl_grande_dopo = ctk.CTkLabel(
            finestra, text="DOPO", fg_color="#1b1f24", corner_radius=8,
            text_color="#9aa0a6",
        )
        self.lbl_grande_dopo.grid(row=1, column=1, padx=(6, 12), pady=(0, 10), sticky="nsew")

        def chiudi():
            self._finestra_anteprima = None
            self.lbl_grande_prima = None
            self.lbl_grande_dopo = None
            try:
                finestra.destroy()
            except Exception:
                pass

        finestra.protocol("WM_DELETE_WINDOW", chiudi)
        try:
            finestra.after(120, finestra.lift)
            finestra.after(160, finestra.focus_force)
        except Exception:
            pass
        self._mostra_anteprima(self._anteprima_prima, self._anteprima_dopo)


    def _crea_slider(self, parent, riga, chiave, etichetta, minimo, massimo, default, fmt):
        ctk.CTkLabel(parent, text=etichetta).grid(row=riga, column=0, padx=10, pady=2, sticky="w")
        slider = ctk.CTkSlider(parent, from_=minimo, to=massimo,
                               command=lambda v, k=chiave: self._on_slider(k, v))
        # La finestra avanzata viene costruita dopo i preset/config: parte
        # sempre dal valore corrente, non dai default.
        valore_iniziale = float(self.parametri.get(chiave, default))
        slider.set(valore_iniziale)
        slider.grid(row=riga, column=1, padx=10, pady=2, sticky="ew")
        valore = ctk.CTkLabel(parent, text=fmt.format(valore_iniziale), width=60)
        valore.grid(row=riga, column=2, padx=10, pady=2, sticky="e")
        self._slider_widgets[chiave] = (slider, valore, fmt)
        self.parametri.setdefault(chiave, valore_iniziale)
        return slider

    def _crea_entry_colore(self, parent, riga, etichetta, default, chiave):
        ctk.CTkLabel(parent, text=etichetta).grid(row=riga, column=0, padx=10, pady=2, sticky="w")
        entry = ctk.CTkEntry(parent, width=110)
        valore_iniziale = str(self.parametri.get(chiave, default) or default)
        entry.insert(0, valore_iniziale)
        entry.grid(row=riga, column=1, padx=10, pady=2, sticky="w")
        entry.bind("<KeyRelease>", lambda e, k=chiave, w=entry: self._on_entry_colore(k, w))
        self.parametri.setdefault(chiave, valore_iniziale)
        return entry

    def _on_entry_colore(self, chiave, widget):
        self.parametri[chiave] = widget.get().strip()
        self._programma_anteprima()

    def _on_curva_tonale(self, valore):
        self.parametri["curva_tonale"] = valore
        self._programma_anteprima()

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
        self._programma_anteprima()

    def _imposta_parametro_slider(self, chiave, valore):
        """Aggiorna slider, etichetta e parametro in un solo passaggio."""
        valore = float(valore)
        self.parametri[chiave] = valore
        if chiave in self._slider_widgets:
            slider, label, fmt = self._slider_widgets[chiave]
            slider.set(valore)
            label.configure(text=fmt.format(valore))
        self._programma_anteprima()

    # ------------------------------------------------- correzioni rapide
    _CHIAVI_RAPIDE = (
        "esposizione", "luci", "ombre", "bianchi", "neri", "contrasto",
        "chiarezza", "dehaze", "vivacita", "saturazione", "hsl_rosso",
        "hsl_verde", "hsl_blu", "nr_luminanza", "nr_colore",
        "nitidezza_quantita", "nitidezza_raggio", "proteggi_luci",
    )

    def _salva_snapshot_rapido(self):
        if self._snapshot_rapido:
            return
        self._snapshot_rapido = {
            chiave: self.parametri.get(chiave) for chiave in self._CHIAVI_RAPIDE
        }

    def _ripristina_snapshot_rapido(self):
        if not self._snapshot_rapido:
            return False
        for chiave, valore in self._snapshot_rapido.items():
            if chiave == "proteggi_luci":
                self.parametri[chiave] = bool(valore)
            elif chiave in self._slider_widgets:
                self._imposta_parametro_slider(chiave, float(valore))
            else:
                self.parametri[chiave] = valore
        self._snapshot_rapido = {}
        self._snapshot_luci = None
        self._aggiorna_stato_proteggi_luci()
        self._programma_anteprima()
        return True

    def _correzione_rapida(self, nome):
        """Applica una correzione fotografica rapida agli slider esistenti."""
        if nome == "annulla":
            if self._ripristina_snapshot_rapido():
                self.scrivi_log("Correzioni rapide annullate: parametri ripristinati.")
            else:
                self.scrivi_log("Nessuna correzione rapida da annullare.")
            return

        self._salva_snapshot_rapido()

        if nome == "contrasto":
            self._imposta_parametro_slider(
                "contrasto", min(0.95, float(self.parametri.get("contrasto", 0.35)) + 0.14)
            )
            self._imposta_parametro_slider(
                "chiarezza", min(0.60, float(self.parametri.get("chiarezza", 0.0)) + 0.06)
            )
            self._imposta_parametro_slider(
                "neri", max(-100.0, float(self.parametri.get("neri", 0.0)) - 5.0)
            )
            self._imposta_parametro_slider(
                "bianchi", min(100.0, float(self.parametri.get("bianchi", 0.0)) + 4.0)
            )
            messaggio = "Contrasto naturale applicato."

        elif nome == "colore":
            self._imposta_parametro_slider(
                "vivacita", min(0.90, float(self.parametri.get("vivacita", 0.35)) + 0.14)
            )
            self._imposta_parametro_slider(
                "saturazione", min(1.30, float(self.parametri.get("saturazione", 1.0)) + 0.06)
            )
            for chiave in ("hsl_rosso", "hsl_verde", "hsl_blu"):
                self._imposta_parametro_slider(
                    chiave, min(25.0, float(self.parametri.get(chiave, 0.0)) + 2.0)
                )
            messaggio = "Colore più ricco applicato."

        elif nome == "sovra":
            if self._snapshot_luci is None:
                self._snapshot_luci = (
                    float(self.parametri.get("luci", 0.0)),
                    float(self.parametri.get("bianchi", 0.0)),
                )
            self._imposta_parametro_slider(
                "esposizione", max(-3.0, float(self.parametri.get("esposizione", 0.0)) - 0.35)
            )
            self._imposta_parametro_slider(
                "luci", max(-100.0, float(self.parametri.get("luci", 0.0)) - 18.0)
            )
            self._imposta_parametro_slider(
                "bianchi", max(-100.0, float(self.parametri.get("bianchi", 0.0)) - 12.0)
            )
            self.parametri["proteggi_luci"] = True
            self._aggiorna_stato_proteggi_luci()
            messaggio = "Correzione per foto sovraesposta applicata."

        elif nome == "sotto":
            self._imposta_parametro_slider(
                "esposizione", min(3.0, float(self.parametri.get("esposizione", 0.0)) + 0.35)
            )
            self._imposta_parametro_slider(
                "ombre", min(100.0, float(self.parametri.get("ombre", 0.0)) + 18.0)
            )
            self._imposta_parametro_slider(
                "neri", min(100.0, float(self.parametri.get("neri", 0.0)) + 5.0)
            )
            messaggio = "Correzione per foto sottoesposta applicata."

        elif nome == "luci":
            attivo = not bool(self.parametri.get("proteggi_luci", False))
            if attivo:
                self._snapshot_luci = (
                    float(self.parametri.get("luci", 0.0)),
                    float(self.parametri.get("bianchi", 0.0)),
                )
                self._imposta_parametro_slider(
                    "luci", min(float(self.parametri.get("luci", 0.0)), -12.0)
                )
                self._imposta_parametro_slider(
                    "bianchi", min(float(self.parametri.get("bianchi", 0.0)), -6.0)
                )
            elif self._snapshot_luci is not None:
                luci, bianchi = self._snapshot_luci
                self._imposta_parametro_slider("luci", luci)
                self._imposta_parametro_slider("bianchi", bianchi)
                self._snapshot_luci = None
            self.parametri["proteggi_luci"] = attivo
            self._aggiorna_stato_proteggi_luci()
            messaggio = (
                "Protezione luci attivata: le alte luci vengono compresse."
                if attivo
                else "Protezione luci disattivata."
            )
        else:
            return

        self.scrivi_log(messaggio)
        self._programma_anteprima()

    def _toggle_proteggi_luci(self, attivo):
        """Allinea interruttore e parametro di protezione luci."""
        attivo = bool(attivo)
        self.parametri["proteggi_luci"] = attivo
        self._aggiorna_stato_proteggi_luci()
        self.scrivi_log(
            "Protezione luci attiva." if attivo else "Protezione luci disattivata."
        )
        self._programma_anteprima()

    def _aggiorna_stato_proteggi_luci(self):
        attivo = bool(self.parametri.get("proteggi_luci", False))
        switch = getattr(self, "sw_proteggi_luci", None)
        if switch is not None:
            try:
                if attivo and not switch.get():
                    switch.select()
                elif not attivo and switch.get():
                    switch.deselect()
            except Exception:
                pass
        bottone = getattr(self, "_bottoni_rapidi", {}).get("luci")
        if bottone is not None:
            try:
                bottone.configure(
                    text="LUCI PROTETTE ✓" if attivo else "SALVA LUCI",
                    fg_color="#1f7a3d" if attivo else "#8a5a1f",
                    hover_color="#258c47" if attivo else "#a56d26",
                )
            except Exception:
                pass

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
            self._imposta_parametro_slider("nr_luminanza", 88.0)
            self._imposta_parametro_slider("nr_colore", 92.0)
            self._imposta_parametro_slider("nitidezza_quantita", 0.9)
            self._imposta_parametro_slider("nitidezza_raggio", 0.9)
            self.parametri["rimuovi_grana_auto"] = True
        self._aggiorna_stato_grana()
        self._programma_anteprima()

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
        self.parametri["rimuovi_grana_auto"] = True
        self.parametri["proteggi_luci"] = False
        self._snapshot_rapido = {}
        self._snapshot_luci = None
        self._grana_precedente = (0.0, 0.0, 0.9, 0.9)
        self._aggiorna_stato_grana()
        self._aggiorna_stato_proteggi_luci()
        self.combo_curva.set("Lineare")
        self.parametri["curva_tonale"] = "Lineare"
        self.scrivi_log("Parametri di sviluppo ripristinati ai valori di default.")
        self._programma_anteprima()

    # ------------------------------------------------------ tab TETHERING
    # ------------------------------------------------------- tab WI-FI FTP
    def _costruisci_tab_ftp(self, tab):
        """Ricezione diretta: la fotocamera invia, il PC prepara l'anteprima."""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(False)

        base = cartella_tethering_predefinita()
        self._ftp_cartella_originali = os.path.join(base, "Originali")
        self._ftp_cartella_anteprime = os.path.join(base, "Anteprime_Cliente")
        self._ftp_cartella_galleria = os.path.join(base, "Galleria_Cliente")
        self._ftp_info_corrente = {}
        self._ftp_galleria_html = ""

        scroll = ctk.CTkScrollableFrame(
            tab, label_text="Scatta, invia via Wi-Fi, ricevi l'anteprima pronta"
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(0, weight=1)

        # ---- Accensione
        card = ctk.CTkFrame(scroll)
        card.pack(fill="x", padx=6, pady=(8, 6))
        card.grid_columnconfigure(0, weight=1)

        self.sw_ftp = ctk.CTkSwitch(
            card,
            text="RICEZIONE WI-FI FTP",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._toggle_ftp_switch,
        )
        self.sw_ftp.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")

        self.lbl_ftp_stato = ctk.CTkLabel(
            card,
            text="Spento. Accendi l'interruttore per ricevere le foto.",
            font=ctk.CTkFont(size=11),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
        )
        self.lbl_ftp_stato.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="w")

        self.btn_ftp = ctk.CTkButton(
            card,
            text="ACCENDI WI-FI FTP",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1f7a3d",
            hover_color="#258c47",
            command=lambda: self._toggle_ftp(not self._ftp_attivo),
        )
        self.btn_ftp.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="ew")

        # ---- Dati da inserire nella fotocamera
        card_dati = ctk.CTkFrame(scroll)
        card_dati.pack(fill="x", padx=6, pady=6)
        card_dati.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_dati,
            text="DATI PER LA FOTOCAMERA",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")

        self.lbl_ftp_avviso = ctk.CTkLabel(
            card_dati,
            text="Inserisci questi dati nel menu FTP della fotocamera.",
            font=ctk.CTkFont(size=11),
            text_color="#9aa0a6",
            anchor="w",
        )
        self.lbl_ftp_avviso.grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")

        ip_iniziale = ip_locale_per_ftp()
        self.lbl_ftp_ip = ctk.CTkLabel(
            card_dati,
            text=f"IP: {ip_iniziale}    Porta: {RicevitoreFTP.PORTA}",
            font=ctk.CTkFont(size=14, family="Consolas"),
            anchor="w",
        )
        self.lbl_ftp_ip.grid(row=2, column=0, padx=14, pady=2, sticky="w")
        self.lbl_ftp_credenziali = ctk.CTkLabel(
            card_dati,
            text=f"Utente: {RicevitoreFTP.UTENTE}    Password: {RicevitoreFTP.PASSWORD}",
            font=ctk.CTkFont(size=14, family="Consolas"),
            anchor="w",
        )
        self.lbl_ftp_credenziali.grid(row=3, column=0, padx=14, pady=2, sticky="w")

        azioni_dati = ctk.CTkFrame(card_dati, fg_color="transparent")
        azioni_dati.grid(row=4, column=0, padx=10, pady=(6, 12), sticky="ew")
        for colonna in range(3):
            azioni_dati.grid_columnconfigure(colonna, weight=1)
        ctk.CTkButton(
            azioni_dati,
            text="COPIA DATI",
            height=32,
            command=self._copia_dati_ftp,
        ).grid(row=0, column=0, padx=(4, 4), sticky="ew")
        ctk.CTkButton(
            azioni_dati,
            text="APRI ANTEPRIME",
            height=32,
            fg_color="#3a3f45",
            hover_color="#4a5158",
            command=lambda: self._apri_cartella_tethering(
                self._ftp_cartella_anteprime
            ),
        ).grid(row=0, column=1, padx=(4, 4), sticky="ew")
        ctk.CTkButton(
            azioni_dati,
            text="APRI GALLERIA",
            height=32,
            fg_color="#2f6f9f",
            hover_color="#3b83b8",
            command=self._apri_galleria_cliente,
        ).grid(row=0, column=2, padx=(4, 4), sticky="ew")

        # ---- Copyright e cartelle
        card_opt = ctk.CTkFrame(scroll)
        card_opt.pack(fill="x", padx=6, pady=6)
        card_opt.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_opt,
            text="COSA SCRIVE SOPRA LE FOTO",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")
        self.sw_ftp_copyright = ctk.CTkSwitch(
            card_opt,
            text="Aggiungi copyright/watermark (in basso a destra)",
            command=self._toggle_ftp_copyright,
        )
        self.sw_ftp_copyright.select()
        self.parametri["ftp_copyright"] = True
        self.sw_ftp_copyright.grid(row=1, column=0, padx=14, pady=(0, 4), sticky="w")

        self.sw_ftp_metadati = ctk.CTkSwitch(
            card_opt,
            text="Scrivi copyright nei metadati EXIF/IPTC (anche nel batch)",
            command=lambda: self._toggle_ftp_metadati(
                bool(self.sw_ftp_metadati.get())
            ),
        )
        self.sw_ftp_metadati.select()
        self.parametri["copyright_metadati"] = True
        self.sw_ftp_metadati.grid(
            row=2, column=0, padx=14, pady=(0, 4), sticky="w"
        )

        self.sw_ftp_galleria = ctk.CTkSwitch(
            card_opt,
            text="Crea la galleria cliente con le caselle di selezione",
            command=lambda: self._toggle_ftp_galleria(
                bool(self.sw_ftp_galleria.get())
            ),
        )
        self.sw_ftp_galleria.select()
        self.parametri["ftp_galleria"] = True
        self.sw_ftp_galleria.grid(
            row=3, column=0, padx=14, pady=(0, 4), sticky="w"
        )

        self.sw_ftp_cloud_auto = ctk.CTkSwitch(
            card_opt,
            text="Invia automaticamente le anteprime ai cloud attivi (Telegram/Dropbox)",
            command=lambda: self._toggle_ftp_cloud_auto(
                bool(self.sw_ftp_cloud_auto.get())
            ),
        )
        self.sw_ftp_cloud_auto.deselect()
        self.parametri["ftp_cloud_auto"] = False
        self.sw_ftp_cloud_auto.grid(
            row=4, column=0, padx=14, pady=(0, 4), sticky="w"
        )

        ctk.CTkLabel(
            card_opt,
            text=(
                "Il nome del file originale viene sempre scritto in basso a "
                "sinistra. Il testo del copyright si imposta in AVANZATE; se "
                "e' vuoto viene usato \u00a9 Franchetti <anno>. La galleria "
                "salva un file index.html che il cliente apre con doppio clic."
            ),
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=860,
        ).grid(row=5, column=0, padx=14, pady=(0, 8), sticky="w")

        cartelle = ctk.CTkFrame(card_opt, fg_color="transparent")
        cartelle.grid(row=6, column=0, padx=10, pady=(0, 12), sticky="ew")
        for colonna in range(3):
            cartelle.grid_columnconfigure(colonna, weight=1)
        ctk.CTkButton(
            cartelle,
            text="CARTELLA ORIGINALI",
            height=32,
            fg_color="#3a3f45",
            hover_color="#4a5158",
            command=lambda: self._apri_cartella_tethering(
                self._ftp_cartella_originali
            ),
        ).grid(row=0, column=0, padx=(4, 4), sticky="ew")
        ctk.CTkButton(
            cartelle,
            text="CARTELLA ANTEPRIME",
            height=32,
            fg_color="#3a3f45",
            hover_color="#4a5158",
            command=lambda: self._apri_cartella_tethering(
                self._ftp_cartella_anteprime
            ),
        ).grid(row=0, column=1, padx=(4, 4), sticky="ew")
        ctk.CTkButton(
            cartelle,
            text="CARTELLA GALLERIA",
            height=32,
            fg_color="#3a3f45",
            hover_color="#4a5158",
            command=lambda: self._apri_cartella_tethering(
                self._ftp_cartella_galleria
            ),
        ).grid(row=0, column=2, padx=(4, 4), sticky="ew")

        # ---- Come si usa, senza promesse impossibili
        card_aiuto = ctk.CTkFrame(scroll)
        card_aiuto.pack(fill="x", padx=6, pady=(6, 12))
        card_aiuto.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card_aiuto,
            text="COME FUNZIONA (IN 3 PASSI)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")
        ctk.CTkLabel(
            card_aiuto,
            text=(
                "1) Accendi il Wi-Fi FTP: il PC resta in ascolto sulla rete locale.\n"
                "2) Nella fotocamera apri il trasferimento FTP e inserisci IP, "
                "porta, utente e password qui sopra.\n"
                "3) Scatta e invia: appena il file arriva, il programma sviluppa "
                "il RAW, riduce il lato lungo a 2000 px e salva il JPEG pronto "
                "per il cliente in Anteprime_Cliente. L'originale non viene toccato."
            ),
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=860,
        ).grid(row=1, column=0, padx=14, pady=(0, 6), sticky="w")
        ctk.CTkLabel(
            card_aiuto,
            text=(
                "Compatibilita': Nikon, Canon, Fujifilm e molti modelli Sony con "
                "trasferimento FTP integrato possono inviare direttamente. I modelli "
                "senza client FTP nella fotocamera non possono farlo da soli: in quel "
                "caso usa l'app del produttore o la scheda, oppure la cartella "
                "monitorata in 'Tethering & Cloud'. Il Bluetooth non trasferisce RAW "
                "di alta qualita' in modo universale: non lo simuliamo."
            ),
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=860,
        ).grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

        self._aggiorna_dati_ftp({})

    # ------------------------------------------------------ controllo FTP
    def _toggle_ftp_switch(self):
        self._toggle_ftp(bool(self.sw_ftp.get()))

    def _toggle_ftp(self, attivo):
        if attivo:
            self._avvia_ftp()
        else:
            self._ferma_ftp()

    def _ftp_parametri(self):
        """Dati letti dal thread di elaborazione: nessun accesso ai widget."""
        chiavi = (
            "ftp_copyright", "watermark_text", "copyright_metadati",
            "copyright_autore", "ftp_galleria", "ftp_cloud_auto",
            "cloud_telegram", "cloud_gdrive", "cloud_meta",
            "cloud_dropbox", "cloud_swiss",
            "tg_token", "tg_chat_id", "gdrive_key", "meta_token", "meta_id",
            "dropbox_token", "swisstransfer_email",
        )
        # Copia superficiale: il worker non tocca mai i widget Tk.
        return {chiave: self.parametri.get(chiave) for chiave in chiavi}

    def _toggle_ftp_copyright(self):
        attivo = bool(self.sw_ftp_copyright.get())
        self.parametri["ftp_copyright"] = attivo
        self.scrivi_log(
            "Wi-Fi FTP: copyright attivo." if attivo else "Wi-Fi FTP: copyright disattivato."
        )

    def _toggle_ftp_metadati(self, attivo):
        self.parametri["copyright_metadati"] = bool(attivo)
        self.scrivi_log(
            "Copyright nei metadati EXIF/IPTC attivo."
            if attivo
            else "Copyright nei metadati EXIF/IPTC disattivato."
        )

    def _toggle_ftp_galleria(self, attivo):
        self.parametri["ftp_galleria"] = bool(attivo)
        self.scrivi_log(
            "Galleria cliente attiva." if attivo else "Galleria cliente disattivata."
        )

    def _toggle_ftp_cloud_auto(self, attivo):
        self.parametri["ftp_cloud_auto"] = bool(attivo)
        self.scrivi_log(
            "Invio automatico ai cloud attivo."
            if attivo
            else "Invio automatico ai cloud disattivato."
        )

    def _avvia_ftp(self):
        if self._ftp_in_avvio:
            return
        if self._ftp_server is not None and self._ftp_attivo:
            return
        self._ftp_in_avvio = True
        try:
            self._raccogli_campi()
        except Exception:
            pass
        try:
            self.sw_ftp.select()
            self.btn_ftp.configure(state="disabled", text="AVVIO IN CORSO...")
        except Exception:
            pass
        self._imposta_stato_ftp("Avvio del server Wi-Fi...", "#ffb74d")
        threading.Thread(target=self._ftp_avvia_worker, daemon=True).start()

    def _ftp_avvia_worker(self):
        try:
            ricevitore = RicevitoreFTP(
                log=lambda messaggio: self._coda.put(("ftp_evento", messaggio)),
                parametri_getter=self._ftp_parametri,
            )
            info = ricevitore.start()
            self._ftp_server = ricevitore
            self._ftp_attivo = True
            self._coda.put(("ftp_stato", True, info, ""))
        except Exception as errore:
            self._ftp_server = None
            self._ftp_attivo = False
            logging.exception("Avvio Wi-Fi FTP non riuscito")
            self._coda.put(
                (
                    "ftp_stato",
                    False,
                    {},
                    f"{type(errore).__name__}: {errore}",
                )
            )

    def _ferma_ftp(self):
        server = self._ftp_server
        self._ftp_server = None
        self._ftp_attivo = False
        self._ftp_in_avvio = False
        try:
            self.sw_ftp.deselect()
            self.btn_ftp.configure(state="disabled", text="ARRESTO IN CORSO...")
        except Exception:
            pass
        self._imposta_stato_ftp("Spegnimento del server Wi-Fi...", "#ffb74d")
        if server is None:
            self._ftp_stato_ui(False, {}, "")
            return
        threading.Thread(
            target=self._ftp_ferma_worker, args=(server,), daemon=True
        ).start()

    def _ftp_ferma_worker(self, server):
        try:
            server.stop()
        except Exception:
            logging.exception("Arresto Wi-Fi FTP non riuscito")
        self._coda.put(("ftp_stato", False, server.info(), ""))

    def _imposta_stato_ftp(self, testo, colore="#9aa0a6"):
        try:
            self.lbl_ftp_stato.configure(text=testo, text_color=colore)
        except Exception:
            pass

    def _aggiorna_dati_ftp(self, info):
        info = info or {}
        ip = info.get("ip") or ip_locale_per_ftp()
        porta = info.get("porta") or RicevitoreFTP.PORTA
        utente = info.get("utente") or RicevitoreFTP.UTENTE
        password = info.get("password") or RicevitoreFTP.PASSWORD
        self._ftp_info_corrente = {
            "ip": ip,
            "porta": porta,
            "utente": utente,
            "password": password,
        }
        if info.get("originali"):
            self._ftp_cartella_originali = info["originali"]
        if info.get("anteprime"):
            self._ftp_cartella_anteprime = info["anteprime"]
        if info.get("galleria"):
            self._ftp_cartella_galleria = info["galleria"]
        if info.get("galleria_html"):
            self._ftp_galleria_html = info["galleria_html"]
        try:
            self.lbl_ftp_ip.configure(text=f"IP: {ip}    Porta: {porta}")
            self.lbl_ftp_credenziali.configure(
                text=f"Utente: {utente}    Password: {password}"
            )
        except Exception:
            pass

    def _copia_dati_ftp(self):
        dati = self._ftp_info_corrente or {}
        ip = dati.get("ip") or ip_locale_per_ftp()
        porta = dati.get("porta") or RicevitoreFTP.PORTA
        utente = dati.get("utente") or RicevitoreFTP.UTENTE
        password = dati.get("password") or RicevitoreFTP.PASSWORD
        testo = f"IP: {ip}\nPorta: {porta}\nUtente: {utente}\nPassword: {password}"
        try:
            self.clipboard_clear()
            self.clipboard_append(testo)
            self.scrivi_log("Dati Wi-Fi FTP copiati negli appunti.")
        except Exception:
            pass

    def _apri_cartella_tethering(self, percorso):
        try:
            os.makedirs(percorso, exist_ok=True)
            os.startfile(percorso)
        except Exception as errore:
            messagebox.showinfo("Cartella", f"Non riesco ad aprire:\n{percorso}\n\n{errore}")

    def _apri_galleria_cliente(self):
        anteprime = self._ftp_cartella_anteprime
        html = self._ftp_galleria_html or os.path.join(
            self._ftp_cartella_galleria, "index.html"
        )
        try:
            os.makedirs(self._ftp_cartella_galleria, exist_ok=True)
            genera_galleria_cliente(
                anteprime,
                html,
                titolo="Selezione cliente",
                sottotitolo=(
                    "Spunta le foto che vuoi e premi «Copia selezione». "
                    "Il fotografo ricevera' l'elenco dei nomi."
                ),
            )
        except Exception as errore:
            messagebox.showinfo(
                "Galleria",
                f"Non riesco a creare la galleria:\n{html}\n\n{errore}",
            )
            return
        try:
            os.startfile(html)
        except Exception as errore:
            messagebox.showinfo(
                "Galleria", f"Galleria creata in:\n{html}\n\n{errore}"
            )

    def _ftp_evento(self, messaggio):
        self.scrivi_log(messaggio)
        if "Anteprima pronta" in messaggio:
            self._imposta_stato_ftp(messaggio, "#66bb6a")
        elif "non riuscita" in messaggio or "incompleto" in messaggio:
            self._imposta_stato_ftp(messaggio, "#ef5350")

    def _ftp_stato_ui(self, attivo, info, errore):
        self._ftp_in_avvio = False
        try:
            self.btn_ftp.configure(state="normal")
        except Exception:
            pass

        if errore:
            self._ftp_attivo = False
            self._ftp_server = None
            try:
                self.sw_ftp.deselect()
                self.btn_ftp.configure(
                    text="ACCENDI WI-FI FTP",
                    fg_color="#1f7a3d",
                    hover_color="#258c47",
                )
            except Exception:
                pass
            self._imposta_stato_ftp(f"Wi-Fi non attivo: {errore}", "#ef5350")
            self.scrivi_log(f"Wi-Fi FTP non avviato: {errore}")
            return

        if attivo:
            self._ftp_attivo = True
            self._aggiorna_dati_ftp(info)
            try:
                self.sw_ftp.select()
                self.btn_ftp.configure(
                    text="SPEGNI WI-FI FTP",
                    fg_color="#a33a3a",
                    hover_color="#b54545",
                )
            except Exception:
                pass
            self._imposta_stato_ftp(
                "Wi-Fi attivo! Invia le foto dalla fotocamera.", "#66bb6a"
            )
            return

        self._ftp_attivo = False
        self._aggiorna_dati_ftp(info)
        try:
            self.sw_ftp.deselect()
            self.btn_ftp.configure(
                text="ACCENDI WI-FI FTP",
                fg_color="#1f7a3d",
                hover_color="#258c47",
            )
        except Exception:
            pass
        self._imposta_stato_ftp("Spento. La porta 2121 e' libera.", "#9aa0a6")

    def _costruisci_tab_tethering(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(False)

        scroll = ctk.CTkScrollableFrame(tab, label_text="Tethering multi-marca e distribuzione Cloud", height=320)
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(scroll, text="TETHERAGGIO MULTI-MARCA - SONY WI-FI DIRETTO", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=8, pady=(8, 2), sticky="w"
        )
        ctk.CTkLabel(
            scroll,
            text=(
                "SONY (A7S e modelli compatibili con Smart Remote Control):\n"
                "1) Apri l'app 'Smart Remote Control' sulla fotocamera.\n"
                "2) Collega il PC alla rete Wi-Fi della fotocamera (DIRECT-xxxx).\n"
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

        ctk.CTkLabel(
            scroll,
            text="ALTRI MARCHI: CANON, NIKON, FUJIFILM, PANASONIC, OM SYSTEM, LEICA",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=4, column=0, columnspan=3, padx=8, pady=(12, 2), sticky="w")
        ctk.CTkLabel(
            scroll,
            text=(
                "Collega la fotocamera via USB e usa il software di tethering del produttore: "
                "Canon EOS Utility, Nikon NX Tether/Transfer 2, Fujifilm X Acquire, "
                "Panasonic Lumix Tether, OM Capture, Leica Tethered. Imposta come destinazione "
                "la cartella monitorata qui sotto: la conversione parte da sola a ogni scatto. "
                "Funziona anche con qualsiasi altra marca che salvi su cartella locale, scheda o rete."
            ),
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#9aa0a6",
            wraplength=900,
        ).grid(row=5, column=0, columnspan=3, padx=8, pady=(0, 4), sticky="w")

        ctk.CTkLabel(scroll, text="HOT-FOLDER MULTI-MARCA (CARTELLA MONITORATA)", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=6, column=0, columnspan=3, padx=8, pady=(14, 2), sticky="w"
        )
        ctk.CTkLabel(
            scroll,
            text=(
                "Scegli la cartella in cui Canon EOS Utility, Nikon Transfer 2, Fujifilm X Acquire, "
                "Panasonic Lumix Tether, Sony Imaging Edge Desktop o un'altra app salvano gli scatti. "
                "Va bene anche una cartella sincronizzata (Google Drive/Dropbox) o di rete."
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

    def _invalida_analisi(self):
        """Evita di riusare un piano per-file dopo un cambio di sorgente."""
        if self._analisi_in_corso:
            return
        self._analisi = {}
        self._analisi_files = []
        try:
            self.chk_usa_analisi.deselect()
        except Exception:
            pass

    def seleziona_cartella_sorgente(self):
        cartella = filedialog.askdirectory(initialdir=self._ultima_cartella)
        if cartella:
            self._ultima_cartella = cartella
            self.entry_sorgente.delete(0, "end")
            self.entry_sorgente.insert(0, cartella)
            self._invalida_analisi()
            self._aggiorna_file_anteprima()
            self.scrivi_log(f"Sorgente: {cartella}")

    def seleziona_file_sorgente(self):
        files = filedialog.askopenfilenames(
            initialdir=self._ultima_cartella,
            title="Seleziona file RAW",
            filetypes=[
                ("File RAW", _pattern_dialogo(RAW_ESTENSIONI)),
                ("Immagini", _pattern_dialogo(IMMAGINI_ESTENSIONI)),
                ("Tutti i file", "*.*"),
            ],
        )
        if files:
            self._ultima_cartella = os.path.dirname(files[0])
            self.entry_sorgente.delete(0, "end")
            self.entry_sorgente.insert(0, "; ".join(files))
            self._invalida_analisi()
            self._aggiorna_file_anteprima()
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
                "max_dim": 2048, "qualita_jpeg": 90, "formato": "JPEG",
                "contrasto": 0.30, "vivacita": 0.35, "nitidezza_quantita": 0.8,
                "nitidezza_raggio": 0.8, "chiarezza": 0.08, "dehaze": 0.02,
                "nr_luminanza": 88, "nr_colore": 92, "rimuovi_grana_auto": True,
            },
            "Stampa Fine Art": {
                "max_dim": 0, "qualita_jpeg": 100, "formato": "TIFF",
                "contrasto": 0.22, "vivacita": 0.25, "nitidezza_quantita": 0.7,
                "nitidezza_raggio": 1.0, "chiarezza": 0.06,
                "nr_luminanza": 88, "nr_colore": 92, "rimuovi_grana_auto": True,
            },
            "Archivio JPEG": {
                "max_dim": 0, "qualita_jpeg": 95, "formato": "JPEG",
                "contrasto": 0.18, "vivacita": 0.20, "nitidezza_quantita": 0.6,
                "nitidezza_raggio": 1.0, "preserva_exif": True,
                "nr_luminanza": 88, "nr_colore": 92, "rimuovi_grana_auto": True,
            },
            "Ritratto": {
                "max_dim": 3000, "qualita_jpeg": 92, "formato": "JPEG",
                "contrasto": 0.22, "vivacita": 0.20, "saturazione": 0.97,
                "chiarezza": 0.02, "ombre": 6, "luci": -4,
                "nitidezza_quantita": 0.8, "nitidezza_raggio": 0.9,
                "nr_luminanza": 88, "nr_colore": 92, "rimuovi_grana_auto": True,
            },
            "Paesaggio": {
                "max_dim": 3000, "qualita_jpeg": 92, "formato": "JPEG",
                "contrasto": 0.35, "vivacita": 0.35, "chiarezza": 0.15,
                "dehaze": 0.08, "nitidezza_quantita": 1.0, "nitidezza_raggio": 1.0,
                "hsl_verde": 8, "hsl_blu": 6,
                "nr_luminanza": 88, "nr_colore": 92, "rimuovi_grana_auto": True,
            },
            "Bianco e Nero": {
                "max_dim": 3000, "qualita_jpeg": 92, "formato": "JPEG",
                "saturazione": 0.0, "contrasto": 0.38, "chiarezza": 0.15,
                "nitidezza_quantita": 0.9, "nitidezza_raggio": 0.9, "grana": 0,
                "nr_luminanza": 88, "nr_colore": 92, "rimuovi_grana_auto": True,
            },
        }.get(nome)

        if not preset:
            return

        self._snapshot_rapido = {}
        self._snapshot_luci = None
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
        self._aggiorna_stato_proteggi_luci()
        self.scrivi_log(f"Preset applicato: {nome}")
        self._programma_anteprima()

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
        self.entry_max_dim.insert(0, str(self.parametri.get("max_dim", 3000)))
        try:
            self._evidenzia_max_dim(int(self.parametri.get("max_dim", 3000)))
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
        if hasattr(self, "entry_copyright_autore"):
            self.entry_copyright_autore.delete(0, "end")
            self.entry_copyright_autore.insert(
                0, self.parametri.get("copyright_autore", "Franchetti")
            )
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
        if hasattr(self, "sw_ftp_copyright"):
            imposta_check(self.sw_ftp_copyright, "ftp_copyright", True)
        if hasattr(self, "sw_ftp_metadati"):
            imposta_check(self.sw_ftp_metadati, "copyright_metadati", True)
        if hasattr(self, "sw_ftp_galleria"):
            imposta_check(self.sw_ftp_galleria, "ftp_galleria", True)
        if hasattr(self, "sw_ftp_cloud_auto"):
            imposta_check(self.sw_ftp_cloud_auto, "ftp_cloud_auto", False)
        self._aggiorna_etichetta_prestazioni()
        self._aggiorna_widget_prestazioni()

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

        self._snapshot_rapido = {}
        self._snapshot_luci = None
        self._toggle_auto_luminosita(bool(self.parametri.get("auto_luminosita", False)))
        self._aggiorna_stato_grana()
        self._aggiorna_stato_proteggi_luci()
        self._programma_anteprima()

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
        self._programma_anteprima()

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
            self.parametri["max_dim"] = 3000
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
        self.parametri["proteggi_luci"] = bool(self.sw_proteggi_luci.get())
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
        if hasattr(self, "sw_ftp_copyright"):
            self.parametri["ftp_copyright"] = bool(self.sw_ftp_copyright.get())
        if hasattr(self, "sw_ftp_metadati"):
            self.parametri["copyright_metadati"] = bool(self.sw_ftp_metadati.get())
        if hasattr(self, "sw_ftp_galleria"):
            self.parametri["ftp_galleria"] = bool(self.sw_ftp_galleria.get())
        if hasattr(self, "sw_ftp_cloud_auto"):
            self.parametri["ftp_cloud_auto"] = bool(self.sw_ftp_cloud_auto.get())
        if hasattr(self, "entry_copyright_autore"):
            self.parametri["copyright_autore"] = (
                self.entry_copyright_autore.get().strip() or "Franchetti"
            )
        self._aggiorna_etichetta_prestazioni()
        return self.parametri

    # ============================================================ PRESTAZIONI
    def _processi_ui(self, numero_file=999):
        """Processi mostrati nella UI: automatici o scelti a mano."""
        profilo = self.parametri.get("profilo_prestazioni", "Bilanciato")
        if self.parametri.get("processi_auto", True):
            return numero_processi_ottimale(
                numero_file, per_processo_mb(self.parametri), profilo
            )
        try:
            scelto = int(self.parametri.get("processi_manuali", 0) or 0)
        except (TypeError, ValueError):
            scelto = 0
        return max(1, min(scelto or 1, nuclei_logici()))

    def _aggiorna_etichetta_prestazioni(self):
        try:
            profilo = self.parametri.get("profilo_prestazioni", "Bilanciato")
            if self.parametri.get("processi_auto", True):
                processi = self._processi_ui()
                testo = f"PRESTAZIONI: {profilo} - automatico (max {processi})"
            else:
                processi = self._processi_ui()
                testo = f"PRESTAZIONI: {profilo} - {processi} processi"
            if hasattr(self, "btn_prestazioni"):
                self.btn_prestazioni.configure(text=testo)
        except Exception:
            pass

    def _aggiorna_slider_parametro(self, chiave, valore):
        try:
            slider, label, fmt = self._slider_widgets[chiave]
        except Exception:
            return
        try:
            slider.set(float(valore))
            label.configure(text=fmt.format(float(valore)))
        except Exception:
            pass

    def _apri_prestazioni(self):
        finestra = self._finestra_prestazioni
        if finestra is not None:
            try:
                if finestra.winfo_exists():
                    finestra.deiconify()
                    finestra.lift()
                    finestra.focus_force()
                    self._aggiorna_widget_prestazioni()
                    return
            except Exception:
                pass

        finestra = ctk.CTkToplevel(self)
        self._finestra_prestazioni = finestra
        finestra.title("Prestazioni - Franchetti Raw Converter Pro")
        finestra.geometry("620x520")
        finestra.minsize(520, 420)
        finestra.transient(self)
        finestra.grid_columnconfigure(0, weight=1)

        def chiudi():
            self._finestra_prestazioni = None
            self._perf_stato_label = None
            try:
                finestra.destroy()
            except Exception:
                pass

        finestra.protocol("WM_DELETE_WINDOW", chiudi)

        ctk.CTkLabel(
            finestra,
            text="PRESTAZIONI ADATTIVE",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(
            finestra,
            text=(
                "Il programma misura i core, la RAM e (con il benchmark) i tuoi "
                "file reali. Gli originali non vengono mai modificati."
            ),
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=580,
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        self._perf_info = ctk.CTkLabel(
            finestra,
            text="",
            font=ctk.CTkFont(size=12, family="Consolas"),
            anchor="w",
        )
        self._perf_info.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="w")

        profilo_card = ctk.CTkFrame(finestra)
        profilo_card.grid(row=3, column=0, padx=16, pady=4, sticky="ew")
        profilo_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(profilo_card, text="Profilo").grid(
            row=0, column=0, padx=(12, 8), pady=(10, 4), sticky="w"
        )
        self._perf_profilo = ctk.CTkComboBox(
            profilo_card,
            values=list(PROFILI_PRESTAZIONI.keys()),
            width=190,
            command=self._cambia_profilo_prestazioni,
        )
        self._perf_profilo.set(self.parametri.get("profilo_prestazioni", "Bilanciato"))
        self._perf_profilo.grid(row=0, column=1, padx=(0, 12), pady=(10, 4), sticky="w")
        self._perf_desc = ctk.CTkLabel(
            profilo_card,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=540,
        )
        self._perf_desc.grid(
            row=1, column=0, columnspan=2, padx=12, pady=(0, 10), sticky="w"
        )

        processi_card = ctk.CTkFrame(finestra)
        processi_card.grid(row=4, column=0, padx=16, pady=4, sticky="ew")
        processi_card.grid_columnconfigure(1, weight=1)
        self._perf_auto = ctk.CTkSwitch(
            processi_card,
            text="Numero processi automatico",
            command=self._toggle_processi_auto,
        )
        self._perf_auto.grid(
            row=0, column=0, columnspan=3, padx=12, pady=(10, 4), sticky="w"
        )
        ctk.CTkLabel(processi_card, text="Processi").grid(
            row=1, column=0, padx=(12, 8), pady=4, sticky="w"
        )
        self._perf_slider = ctk.CTkSlider(
            processi_card,
            from_=1,
            to=nuclei_logici(),
            number_of_steps=max(1, nuclei_logici() - 1),
            command=self._on_processi_slider,
        )
        self._perf_slider.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self._perf_valore = ctk.CTkLabel(
            processi_card, text="", font=ctk.CTkFont(size=11, weight="bold")
        )
        self._perf_valore.grid(row=1, column=2, padx=(8, 12), pady=4, sticky="e")
        ctk.CTkLabel(
            processi_card,
            text=(
                "Automatico rispetta RAM libera e core fisici/logici. "
                "Oltre i core fisici il guadagno e' minimo e la RAM sale."
            ),
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=540,
        ).grid(row=2, column=0, columnspan=3, padx=12, pady=(0, 10), sticky="w")

        bench_card = ctk.CTkFrame(finestra)
        bench_card.grid(row=5, column=0, padx=16, pady=4, sticky="ew")
        bench_card.grid_columnconfigure(0, weight=1)
        self._perf_bench_btn = ctk.CTkButton(
            bench_card,
            text="BENCHMARK SUI MIEI FILE",
            height=34,
            fg_color="#2f6f9f",
            hover_color="#3b83b8",
            command=self._avvia_benchmark,
        )
        self._perf_bench_btn.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="ew")
        self._perf_bench_label = ctk.CTkLabel(
            bench_card,
            text="Mai eseguito: la stima usa valori prudenti.",
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
            anchor="w",
            justify="left",
            wraplength=540,
        )
        self._perf_bench_label.grid(
            row=1, column=0, padx=12, pady=(0, 4), sticky="w"
        )
        self._perf_stima = ctk.CTkLabel(
            bench_card,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="w",
            justify="left",
            wraplength=540,
        )
        self._perf_stima.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="w")
        self._perf_stato_label = ctk.CTkLabel(
            bench_card,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#8ab4f8",
            anchor="w",
        )
        self._perf_stato_label.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="w")

        ctk.CTkButton(
            finestra, text="Chiudi", width=120, command=chiudi
        ).grid(row=6, column=0, padx=16, pady=(8, 14), sticky="e")

        self._aggiorna_widget_prestazioni()
        try:
            finestra.after(120, finestra.lift)
            finestra.after(160, finestra.focus_force)
        except Exception:
            pass

    def _cambia_profilo_prestazioni(self, nome):
        profilo = PROFILI_PRESTAZIONI.get(nome)
        if not profilo:
            return
        self.parametri["profilo_prestazioni"] = nome
        for chiave, valore in profilo["parametri"].items():
            self.parametri[chiave] = valore
            self._aggiorna_slider_parametro(chiave, valore)
        self._aggiorna_stato_grana()
        self._aggiorna_etichetta_prestazioni()
        self._aggiorna_widget_prestazioni()
        self.scrivi_log(
            f"Profilo prestazioni: {nome}. Denoise e nitidezza aggiornati; "
            "il numero di processi resta adattivo."
        )
        self._programma_anteprima()

    def _toggle_processi_auto(self):
        auto = bool(self._perf_auto.get())
        self.parametri["processi_auto"] = auto
        if auto:
            self.parametri["processi_manuali"] = 0
            try:
                self._perf_slider.configure(state="disabled")
            except Exception:
                pass
        else:
            try:
                self.parametri["processi_manuali"] = max(1, int(round(self._perf_slider.get())))
                self._perf_slider.configure(state="normal")
            except Exception:
                pass
        self._aggiorna_valore_processi()
        self._aggiorna_etichetta_prestazioni()
        self.scrivi_log(
            "Processi: automatici (RAM e core)."
            if auto
            else f"Processi: {self.parametri.get('processi_manuali', 1)} scelti a mano."
        )

    def _on_processi_slider(self, valore):
        if not self.parametri.get("processi_auto", True):
            self.parametri["processi_manuali"] = max(1, int(round(float(valore))))
        self._aggiorna_valore_processi()
        self._aggiorna_etichetta_prestazioni()

    def _aggiorna_valore_processi(self):
        try:
            processi = self._processi_ui()
            suffisso = (
                " max (auto)" if self.parametri.get("processi_auto", True) else ""
            )
            self._perf_valore.configure(text=f"{processi}{suffisso}")
        except Exception:
            pass

    def _aggiorna_widget_prestazioni(self):
        finestra = self._finestra_prestazioni
        if finestra is None:
            return
        try:
            if not finestra.winfo_exists():
                return
        except Exception:
            return

        auto = bool(self.parametri.get("processi_auto", True))
        try:
            self._perf_info.configure(
                text=(
                    f"CPU: {nuclei_fisici()} fisici / {nuclei_logici()} logici"
                    f"    RAM libera: {memoria_disponibile_mb() / 1024.0:.1f} GB"
                )
            )
            profilo = self.parametri.get("profilo_prestazioni", "Bilanciato")
            self._perf_profilo.set(profilo)
            self._perf_desc.configure(
                text=PROFILI_PRESTAZIONI.get(profilo, {}).get("descrizione", "")
            )
            if auto and not self._perf_auto.get():
                self._perf_auto.select()
            elif not auto and self._perf_auto.get():
                self._perf_auto.deselect()
            self._perf_slider.configure(state="disabled" if auto else "normal")
            if auto:
                self._perf_slider.set(self._processi_ui())
            else:
                self._perf_slider.set(
                    max(1, min(nuclei_logici(), int(self.parametri.get("processi_manuali", 1) or 1)))
                )
            self._aggiorna_valore_processi()
            self._aggiorna_stima_prestazioni()
        except Exception:
            pass

    def _aggiorna_stima_prestazioni(self):
        try:
            if self._benchmark_secondi_medio is None:
                self._perf_stima.configure(
                    text=(
                        "Stima: esegui il benchmark per misurare il tempo reale "
                        "sui tuoi file e sul tuo PC."
                    )
                )
                return
            files = []
            try:
                sorgente = self.entry_sorgente.get().strip()
                if sorgente:
                    files = raccogli_file_sorgente(
                        sorgente,
                        bool(self.parametri.get("ricorsivo", True)),
                        self.entry_destinazione.get().strip() or None,
                    )
            except Exception:
                files = []
            numero_file = len(files) or 1
            # Stessa decisione usata dal batch: niente stime parallele
            # ottimistiche per 3 JPEG che verranno elaborati in sequenza.
            processi = processi_per_batch(files, self.parametri) if files else 1
            secondi = stima_tempo_batch(
                self._benchmark_secondi_medio, numero_file, processi
            )
            velocita = numero_file / max(0.1, secondi) * 60.0
            dettaglio_processi = (
                f"{processi} processi"
                if processi > 1
                else "1 processo (batch piccolo)"
            )
            self._perf_stima.configure(
                text=(
                    f"Stima per {numero_file} file: ~{formatta_durata(secondi)} "
                    f"({velocita:.1f} file/min, {dettaglio_processi})."
                )
            )
        except Exception:
            pass

    def _avvia_benchmark(self):
        if self._benchmark_in_corso:
            return
        sorgente = self.entry_sorgente.get().strip()
        if not sorgente:
            messagebox.showwarning(
                "Benchmark", "Seleziona prima una cartella o dei file RAW."
            )
            return
        files = raccogli_file_sorgente(
            sorgente,
            bool(self.parametri.get("ricorsivo", True)),
            self.entry_destinazione.get().strip() or None,
        )
        if not files:
            messagebox.showwarning(
                "Benchmark", "Nessun file RAW o immagine trovato nella sorgente."
            )
            return

        self._raccogli_campi()
        parametri = normalizza_parametri(self.parametri)
        self._benchmark_in_corso = True
        try:
            self._perf_bench_btn.configure(state="disabled", text="BENCHMARK IN CORSO...")
            self._perf_bench_label.configure(
                text="Sto elaborando 1-2 file reali in una cartella temporanea..."
            )
        except Exception:
            pass
        threading.Thread(
            target=self._benchmark_worker, args=(list(files), parametri), daemon=True
        ).start()

    def _benchmark_worker(self, files, parametri):
        try:
            risultato = benchmark_conversione(
                files, parametri, massimo_file=2, log=self._log_threadsafe
            )
        except Exception as errore:
            self._coda.put(("bench_error", f"{type(errore).__name__}: {errore}"))
            return
        self._coda.put(("bench_done", risultato))

    def _fine_benchmark(self, risultato):
        self._benchmark_in_corso = False
        media = float(risultato.get("secondi_medio", 0.0) or 0.0)
        self._benchmark_secondi_medio = media if media > 0 else None
        try:
            self._perf_bench_btn.configure(
                state="normal", text="RIPETI BENCHMARK"
            )
        except Exception:
            pass
        if self._benchmark_secondi_medio is None:
            return
        processi = self._processi_ui()
        testo = (
            f"Misurato: {media:.1f}s per file ({len(risultato.get('secondi', []))} "
            f"file di prova, 1 processo), ~{60.0 / media:.1f} file/min."
        )
        try:
            self._perf_bench_label.configure(text=testo)
        except Exception:
            pass
        self.scrivi_log("Benchmark completato. " + testo)
        self._aggiorna_stima_prestazioni()

    def _errore_benchmark(self, errore):
        self._benchmark_in_corso = False
        try:
            self._perf_bench_btn.configure(
                state="normal", text="BENCHMARK SUI MIEI FILE"
            )
            self._perf_bench_label.configure(text=f"Benchmark non riuscito: {errore}")
        except Exception:
            pass
        self.scrivi_log(f"Benchmark non riuscito: {errore}")

    def _stima_batch_corrente(self, files, parametri):
        if self._benchmark_secondi_medio is None:
            return ""
        try:
            processi = processi_per_batch(list(files), parametri)
            secondi = stima_tempo_batch(
                self._benchmark_secondi_medio, len(files), processi
            )
            return (
                f"Stima: ~{formatta_durata(secondi)} per {len(files)} file "
                f"({processi} processi, misurato {self._benchmark_secondi_medio:.1f}s/file)."
            )
        except Exception:
            return ""

    # ============================================================ BATCH
    def _raccogli_file_sorgente(self, sorgente, ricorsivo, escludi=None):
        return raccogli_file_sorgente(sorgente, ricorsivo, escludi)

    # ---------------------------------------------------- Smart Batch: analisi
    def avvia_analisi(self):
        """Analizza tutti i file e prepara un piano di correzione per ciascuno."""
        if self._batch_attivo:
            messagebox.showinfo("Analisi", "Attendi la fine della conversione in corso.")
            return
        if self._analisi_in_corso:
            messagebox.showinfo("Analisi", "L'analisi dei file è già in corso.")
            return

        sorgente = self.entry_sorgente.get().strip()
        if not sorgente:
            messagebox.showwarning(
                "Sorgente mancante", "Seleziona una cartella o dei file RAW da analizzare."
            )
            return

        self._raccogli_campi()
        destinazione = self.entry_destinazione.get().strip()
        files = self._raccogli_file_sorgente(
            sorgente, self.parametri.get("ricorsivo", True), escludi=destinazione or None
        )
        if not files:
            messagebox.showwarning(
                "Nessun file", "Nessun file RAW o immagine trovato nella sorgente selezionata."
            )
            return

        self._analisi = {}
        self._analisi_files = list(files)
        self._analisi_in_corso = True
        self._cancel_event.clear()
        self.btn_analizza.configure(state="disabled")
        self.btn_avvia.configure(state="disabled")
        self.btn_annulla.configure(state="normal")
        self.chk_usa_analisi.deselect()
        self.progress.set(0)
        self.lbl_progresso.configure(text=f"Analisi 0 / {len(files)}")
        self.lbl_stato.configure(text="Analisi file in corso...")
        self.scrivi_log(
            f"Analisi Smart Batch avviata: {len(files)} file. Nessun file verrà modificato."
        )

        threading.Thread(
            target=self._analisi_worker, args=(list(files),), daemon=True
        ).start()

    def _analisi_worker(self, files):
        def log(messaggio):
            self._log_threadsafe(messaggio)

        def progresso(indice, totale, ok, errori):
            self._coda.put(("analisi_progress", indice, totale, ok, errori))

        try:
            risultati = analizza_batch(
                files, log=log, progresso=progresso, cancel_event=self._cancel_event
            )
        except Exception as errore:
            log(f"Analisi Smart Batch non riuscita: {errore}")
            risultati = {}
        finally:
            self._coda.put(("analisi_done", risultati, list(files)))

    def _aggiorna_progresso_analisi(self, indice, totale, ok, errori):
        self.progress.set(min(1.0, indice / max(totale, 1)))
        self.lbl_progresso.configure(
            text=f"Analisi {indice} / {totale}  -  OK: {ok}  Errori: {errori}"
        )

    def _fine_analisi(self, risultati, files):
        annullato = self._cancel_event.is_set()
        self._cancel_event.clear()
        self._analisi_in_corso = False
        self._analisi = risultati or {}
        self._analisi_files = list(files or [])

        self.btn_analizza.configure(state="normal")
        self.btn_avvia.configure(state="normal")
        self.btn_annulla.configure(state="disabled")

        risultati = self._analisi
        ok = sum(1 for r in risultati.values() if r.get("ok"))
        errori = sum(1 for r in risultati.values() if not r.get("ok"))
        da_correggere = sum(
            1 for r in risultati.values()
            if r.get("ok") and r.get("stato") in ("CORREGGI", "CRITICO")
        )
        critici = sum(
            1 for r in risultati.values()
            if r.get("ok") and r.get("stato") == "CRITICO"
        )
        puliti = sum(
            1 for r in risultati.values()
            if r.get("ok") and r.get("stato") == "OK"
        )

        if da_correggere:
            self.chk_usa_analisi.select()
        else:
            self.chk_usa_analisi.deselect()

        if annullato:
            testo = f"Analisi annullata - file letti: {ok}, errori: {errori}"
            self.lbl_stato.configure(text=testo)
            self.scrivi_log(testo)
        else:
            self.progress.set(1.0)
            testo = (
                f"Analisi completata: {ok} file, {da_correggere} da correggere, "
                f"{puliti} già corrette, {critici} critici"
            )
            if errori:
                testo += f", {errori} errori"
            self.lbl_stato.configure(text=testo)
            self.lbl_progresso.configure(text=testo)
            self.scrivi_log(testo)
            if critici:
                self.scrivi_log(
                    "Attenzione: le alte luci già completamente bruciate non "
                    "contengono dettaglio e non possono essere recuperate."
                )

        if risultati:
            self._mostra_finestra_analisi(risultati, files)
        else:
            messagebox.showinfo(
                "Analisi",
                "Nessun file analizzato. Controlla la sorgente e riprova.",
            )

    def _mostra_finestra_analisi(self, risultati, files):
        """Mostra il piano per file in una tabella leggibile e compatta."""
        if self._finestra_analisi is not None:
            try:
                self._finestra_analisi.destroy()
            except Exception:
                pass
            self._finestra_analisi = None

        finestra = ctk.CTkToplevel(self)
        finestra.title("Analisi file - Smart Batch")
        finestra.geometry("1000x620")
        finestra.minsize(820, 420)
        finestra.transient(self)
        finestra.grid_columnconfigure(0, weight=1)
        finestra.grid_rowconfigure(2, weight=1)
        self._finestra_analisi = finestra

        def chiudi():
            self._finestra_analisi = None
            try:
                finestra.destroy()
            except Exception:
                pass

        finestra.protocol("WM_DELETE_WINDOW", chiudi)

        da_correggere = sum(
            1 for r in risultati.values()
            if r.get("ok") and r.get("stato") in ("CORREGGI", "CRITICO")
        )
        ctk.CTkLabel(
            finestra,
            text=(
                f"Piano Smart Batch: {len(risultati)} file analizzati, "
                f"{da_correggere} con correzioni suggerite"
            ),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")
        ctk.CTkLabel(
            finestra,
            text=(
                "Le correzioni sono conservative e per-file. I dettagli già "
                "completamente bruciati non sono recuperabili. Deseleziona "
                "«Usa correzioni per file» nel tab Batch per ignorarle."
            ),
            font=ctk.CTkFont(size=10),
            text_color="#9aa0a6",
        ).grid(row=1, column=0, padx=12, pady=(0, 4), sticky="w")

        contenitore = ctk.CTkScrollableFrame(finestra)
        contenitore.grid(row=2, column=0, padx=10, pady=4, sticky="nsew")
        colonne = (
            ("File", 220), ("Stato", 78), ("Motivo", 250), ("EV", 58),
            ("Luci", 52), ("Ombre", 58), ("Contr.", 58), ("Colore", 62),
            ("Rumore", 62),
        )
        for indice, (titolo, larghezza) in enumerate(colonne):
            contenitore.grid_columnconfigure(indice, weight=1 if indice in (0, 2) else 0)
            ctk.CTkLabel(
                contenitore, text=titolo, width=larghezza,
                font=ctk.CTkFont(size=10, weight="bold"), anchor="w",
            ).grid(row=0, column=indice, padx=3, pady=(2, 4), sticky="w")

        def valore(suggerimenti, chiave, formato="{:.0f}", default=""):
            if chiave not in suggerimenti:
                return "-"
            try:
                return formato.format(float(suggerimenti[chiave]))
            except (TypeError, ValueError):
                return str(suggerimenti[chiave])

        riga = 1
        for percorso in files:
            risultato = risultati.get(percorso)
            if not risultato:
                continue
            stato = str(risultato.get("stato", "ERRORE"))
            colori = {
                "OK": "#66bb6a",
                "CORREGGI": "#ffb74d",
                "CRITICO": "#ff7043",
                "ERRORE": "#ef5350",
            }
            suggerimenti = risultato.get("suggerimenti") or {}
            valori = (
                risultato.get("nome", os.path.basename(percorso)),
                stato,
                risultato.get("motivo", ""),
                valore(suggerimenti, "esposizione", "{:+.2f}"),
                valore(suggerimenti, "luci"),
                valore(suggerimenti, "ombre", "{:+.0f}"),
                valore(suggerimenti, "contrasto", "{:.2f}"),
                valore(suggerimenti, "vivacita", "{:.2f}"),
                valore(suggerimenti, "nr_luminanza", "{:.0f}"),
            )
            for indice, testo in enumerate(valori):
                ctk.CTkLabel(
                    contenitore,
                    text=str(testo),
                    width=colonne[indice][1],
                    anchor="w",
                    justify="left",
                    wraplength=colonne[indice][1] if indice in (0, 2) else 0,
                    font=ctk.CTkFont(size=10),
                    text_color=colori.get(stato, "#dce1e6") if indice == 1 else "#dce1e6",
                ).grid(row=riga, column=indice, padx=3, pady=2, sticky="w")
            riga += 1

        ctk.CTkButton(finestra, text="Chiudi", width=140, command=chiudi).grid(
            row=3, column=0, padx=12, pady=(4, 10), sticky="e"
        )
        try:
            finestra.after(120, finestra.lift)
            finestra.after(160, finestra.focus_force)
        except Exception:
            pass

    def avvia_batch(self):
        if self._batch_attivo:
            messagebox.showinfo("Batch", "Una conversione è già in corso.")
            return
        if self._analisi_in_corso:
            messagebox.showinfo("Batch", "Attendi la fine dell'analisi dei file.")
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
        self._batch_inizio = time.time()
        self._batch_totale = len(files)

        self.btn_avvia.configure(state="disabled")
        self.btn_analizza.configure(state="disabled")
        self.btn_annulla.configure(state="normal")
        self.progress.set(0)
        self.lbl_progresso.configure(text=f"0 / {len(files)}")
        self.lbl_stato.configure(text="Conversione in corso...")
        self.scrivi_log(f"Batch avviato: {len(files)} file -> {destinazione}")

        params = normalizza_parametri(self.parametri)
        stima = self._stima_batch_corrente(files, params)
        if stima:
            self.scrivi_log(stima)
        analisi = None
        if self.chk_usa_analisi.get():
            analisi = {
                percorso: self._analisi[percorso]
                for percorso in files
                if percorso in self._analisi
            }
            if analisi:
                self.scrivi_log(
                    f"Smart Batch: uso il piano per-file su {len(analisi)} file."
                )
            else:
                self.scrivi_log(
                    "Smart Batch: nessuna analisi valida per i file selezionati; "
                    "uso le impostazioni globali."
                )
                analisi = None
        thread = threading.Thread(
            target=self._batch_worker,
            args=(list(files), params, destinazione, analisi),
            daemon=True,
        )
        thread.start()

    def _batch_worker(self, files, params, destinazione, analisi=None):
        def log(messaggio):
            self._log_threadsafe(messaggio)

        def progresso(indice, totale, ok, errori, saltati):
            self._coda.put(("progress", indice, totale, ok, errori, saltati))

        esito = esegui_batch(
            files, params, destinazione,
            log=log, progresso=progresso, cancel_event=self._cancel_event,
            analisi=analisi,
        )
        self._coda.put((
            "done", esito["ok"], esito["errori"], esito["saltati"], esito["annullato"]
        ))

    def _aggiorna_progresso(self, indice, totale, ok, errori, saltati=0):
        self.progress.set(min(1.0, indice / max(totale, 1)))
        testo = f"{indice} / {totale}  -  OK: {ok}  Errori: {errori}"
        if saltati:
            testo += f"  Saltati: {saltati}"
        if self._batch_inizio is not None and indice > 0:
            trascorso = max(0.1, time.time() - self._batch_inizio)
            media = trascorso / indice
            rimanenti = max(0, totale - indice)
            eta = media * rimanenti
            velocita = 60.0 / max(0.1, media)
            testo += f"  -  {velocita:.1f} file/min"
            if rimanenti:
                testo += f"  -  ETA {formatta_durata(eta)}"
        self.lbl_progresso.configure(text=testo)
        if self._perf_stato_label is not None:
            try:
                self._perf_stato_label.configure(text=testo)
            except Exception:
                pass

    def _fine_batch(self, ok, errori, saltati=0, annullato=False):
        self._batch_attivo = False
        self.btn_avvia.configure(state="normal")
        self.btn_analizza.configure(state="normal")
        self.btn_annulla.configure(state="disabled")
        durata = ""
        if self._batch_inizio is not None:
            secondi = max(0.1, time.time() - self._batch_inizio)
            durata = f", {formatta_durata(secondi)}"
            if secondi >= 0.1:
                durata += f" ({max(0, ok + errori + saltati) / secondi * 60.0:.1f} file/min)"
        if annullato:
            testo = f"Annullato - OK: {ok}, Errori: {errori}{durata}"
        else:
            testo = f"Completato - OK: {ok}, Errori: {errori}{durata}"
        if saltati:
            testo += f", Saltati: {saltati}"
        self.lbl_stato.configure(text=testo)
        self.lbl_progresso.configure(text=testo)
        self.scrivi_log(f"Batch terminato: OK {ok}, errori {errori}, saltati {saltati}{durata}.")
        if self._perf_stato_label is not None:
            try:
                self._perf_stato_label.configure(text=testo)
            except Exception:
                pass
        self._batch_inizio = None

    def annulla_batch(self):
        if self._analisi_in_corso:
            self._cancel_event.set()
            self.lbl_stato.configure(text="Annullamento analisi in corso...")
            self.scrivi_log("Richiesto annullamento dell'analisi...")
            return
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
            if self._ftp_server is not None:
                try:
                    self._ftp_server.stop()
                except Exception:
                    pass
                self._ftp_server = None
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
