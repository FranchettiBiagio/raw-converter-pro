# -*- coding: utf-8 -*-
"""
================================================================================
          FRANCHETTI RAW CONVERTER PRO v2.50.1 - MONOLITHIC CORE
================================================================================
Licenza: MIT
Descrizione: Suite Enterprise Open-Source per lo sviluppo RAW lineare a livello
             sensore (LibRaw), ottimizzazione in spazio CIE L*a*b*, correzioni
             colore complete, ridimensionamento, watermarking, tethering Wi-Fi
             automatico (Hot-Folder) e distribuzione Cloud multi-canale.
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
from datetime import datetime
from tkinter import filedialog, messagebox

try:
    import numpy as np
    import rawpy
    import piexif
    import customtkinter as ctk
    from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter
    from skimage import color, filters
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import requests
except ImportError as e:  # pragma: no cover
    print(f"[ERRORE DI DIPENDENZA] Manca una libreria fondamentale: {e}")
    print("Esegui: pip install numpy rawpy piexif customtkinter Pillow scikit-image requests watchdog")
    sys.exit(1)


APP_VERSION = "2.51.4"
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


# ================================================================================
# 2. CORE PIPELINE: MOTORE DI ELABORAZIONE IMMAGINI IN SPAZIO CIE L*a*b*
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

    # ----------------------------------------------------- fase 4: Lab + curve
    @classmethod
    def _fase_lab(cls, img, p):
        lab = color.rgb2lab(np.clip(img, 0.0, 1.0))
        L = np.clip(lab[:, :, 0], 0.0, 100.0)

        # Curva tonale parametrica
        lut = cls._curva_lut(p.get("curva_tonale", "Lineare"))
        indici = np.clip((L / 100.0 * 255.0).astype(np.int32), 0, 255)
        lab[:, :, 0] = lut[indici]

        # Riduzione rumore cromatico
        nrc = float(p.get("nr_colore", 0.0)) / 100.0
        if nrc > 1e-4:
            sigma = 0.6 + nrc * 2.6
            lab[:, :, 1] = filters.gaussian(lab[:, :, 1], sigma=sigma, preserve_range=True)
            lab[:, :, 2] = filters.gaussian(lab[:, :, 2], sigma=sigma, preserve_range=True)

        # Riduzione rumore luminanza
        nrl = float(p.get("nr_luminanza", 0.0)) / 100.0
        if nrl > 1e-4:
            lab[:, :, 0] = filters.gaussian(
                lab[:, :, 0], sigma=0.35 + nrl * 1.8, preserve_range=True
            )

        # Nitidezza sul canale L (nessun alone cromatico)
        q = float(p.get("nitidezza_quantita", 0.0))
        if q > 1e-4:
            raggio = float(p.get("nitidezza_raggio", 1.5))
            lab[:, :, 0] = filters.unsharp_mask(
                lab[:, :, 0], radius=raggio, amount=q, preserve_range=True
            )

        return np.clip(color.lab2rgb(lab), 0.0, 1.0)

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
        logo = Image.open(logo_path).convert("RGBA")
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
        formato = str(p.get("formato", "JPEG")).upper()
        qualita = int(p.get("qualita_jpeg", 90))
        kwargs = {}
        icc = None
        try:
            from PIL import ImageCms
            icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        except Exception:
            icc = None

        if formato in ("JPEG", "JPG"):
            if pil_img.mode not in ("RGB", "L"):
                pil_img = pil_img.convert("RGB")
            kwargs = dict(quality=qualita, subsampling=0, optimize=True)
            if icc:
                kwargs["icc_profile"] = icc
        elif formato == "PNG":
            kwargs = dict(compress_level=6)
            if icc:
                kwargs["icc_profile"] = icc
        elif formato in ("TIFF", "TIF"):
            kwargs = dict(compression="tiff_lzw")
            if icc:
                kwargs["icc_profile"] = icc
        elif formato == "WEBP":
            if pil_img.mode not in ("RGB", "RGBA"):
                pil_img = pil_img.convert("RGB")
            kwargs = dict(quality=qualita, method=4)
            if icc:
                kwargs["icc_profile"] = icc
        else:
            kwargs = dict(quality=qualita)

        pil_img.save(percorso_output, format=None if formato == "JPG" else formato, **kwargs)

    # ------------------------------------------------------------ pipeline
    @classmethod
    def sviluppa_e_ottimizza(cls, percorso_raw, percorso_output, parametri, callback=None):
        p = parametri

        def nota(msg):
            logging.info(msg)
            if callback:
                try:
                    callback(msg)
                except Exception:
                    pass

        nota(f"Avvio sviluppo: {os.path.basename(percorso_raw)}")

        # 1. Decodifica RAW (o immagine standard)
        if percorso_raw.lower().endswith(RAW_ESTENSIONI):
            with rawpy.imread(percorso_raw) as raw:
                rgb = raw.postprocess(
                    demosaic_algorithm=rawpy.DemosaicAlgorithm.AMAZE,
                    use_camera_wb=bool(p.get("use_camera_wb", True)),
                    no_auto_bright=False,
                    output_color=rawpy.ColorSpace.sRGB,
                    output_bps=8,
                )
        else:
            with Image.open(percorso_raw) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                rgb = np.array(im)

        img = rgb.astype(np.float32) / 255.0

        # 2. Pipeline fotografica
        img = cls._fase_tono(img, p)
        img = cls._fase_colore(img, p)
        img = cls._fase_dettaglio(img, p)
        img = cls._fase_lab(img, p)
        img = cls._fase_effetti(img, p)

        img_finale = (np.clip(img, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
        pil_img = Image.fromarray(img_finale, "RGB")

        # 3. Ridimensionamento (lato lungo)
        max_dim = int(p.get("max_dim", 0) or 0)
        if max_dim > 0 and max(pil_img.size) > max_dim:
            fattore = max_dim / float(max(pil_img.size))
            nuova = (max(1, int(pil_img.size[0] * fattore)), max(1, int(pil_img.size[1] * fattore)))
            pil_img = pil_img.resize(nuova, Image.Resampling.LANCZOS)
            nota(f"Ridimensionato a {nuova[0]}x{nuova[1]} px")

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
        logging.info("Google Drive: credenziale presente, predisposizione upload per %s", file_path)
        return False

    @staticmethod
    def invia_meta_social(file_path, access_token, account_id, platform="instagram"):
        if not access_token or not account_id:
            return False
        logging.info("Meta Graph API: pubblicazione %s predisposta per %s", platform, file_path)
        return False

    @staticmethod
    def invia_swisstransfer(file_path, email):
        if not email:
            return False
        logging.info("SwissTransfer: trasferimento predisposto per %s (%s)", file_path, email)
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
        self.parametri = dict(parametri)
        self.callback = callback_interfaccia
        self.estensioni = RAW_ESTENSIONI
        self._in_corso = set()
        self._lock = threading.Lock()

    def _notifica(self, msg):
        if self.callback:
            try:
                self.callback(msg)
            except Exception:
                pass

    def on_created(self, event):
        if event.is_directory:
            return
        percorso = event.src_path
        if not percorso.lower().endswith(self.estensioni):
            return
        with self._lock:
            if percorso in self._in_corso:
                return
            self._in_corso.add(percorso)
        threading.Thread(target=self._elabora, args=(percorso,), daemon=True).start()

    def _elabora(self, percorso):
        try:
            self._notifica(f"Wi-Fi: rilevato {os.path.basename(percorso)}")
            time.sleep(1.5)

            p = dict(self.parametri)
            cartella_output = p.get("output_dir") or os.path.join(os.path.dirname(percorso), "Output_Ottimizzati")
            os.makedirs(cartella_output, exist_ok=True)

            est = FORMATI_OUTPUT.get(str(p.get("formato", "JPEG")).upper(), ".jpg")
            nome = os.path.splitext(os.path.basename(percorso))[0] + "_PRO" + est
            output = os.path.join(cartella_output, nome)

            ImageEngine.sviluppa_e_ottimizza(percorso, output, p, callback=self._notifica)
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
        destinazione = os.path.join(cartella, nome)
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
            text=f"v{APP_VERSION}  |  LibRaw AMaZE  |  CIE L*a*b*  |  Tethering & Cloud",
            font=ctk.CTkFont(size=12),
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
                    self._fine_batch(messaggio[1], messaggio[2])
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

        scroll = ctk.CTkScrollableFrame(tab, height=320)
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(0, weight=1)

        # ================= BLOCCO SORGENTE / DESTINAZIONE / DIMENSIONI =================
        sx = ctk.CTkFrame(scroll, fg_color="transparent")
        sx.grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        sx.grid_columnconfigure(1, weight=1)

        r = 0
        ctk.CTkLabel(sx, text="SORGENTE", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=3, padx=6, pady=(6, 2), sticky="w"
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
            row=r, column=0, columnspan=3, padx=6, pady=(6, 2), sticky="w"
        ); r += 1

        ctk.CTkLabel(sx, text="Cartella output:").grid(row=r, column=0, padx=6, pady=3, sticky="w")
        self.entry_destinazione = ctk.CTkEntry(sx, placeholder_text="Cartella di destinazione...")
        self.entry_destinazione.grid(row=r, column=1, padx=6, pady=3, sticky="ew")
        ctk.CTkButton(sx, text="Sfoglia", width=90,
                      command=self.seleziona_cartella_destinazione).grid(row=r, column=2, padx=6, pady=3)
        r += 1

        ctk.CTkLabel(sx, text="DIMENSIONI E FORMATO", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=3, padx=6, pady=(6, 2), sticky="w"
        ); r += 1

        dim = ctk.CTkFrame(sx)
        dim.grid(row=r, column=0, columnspan=3, padx=6, pady=2, sticky="ew")
        dim.grid_columnconfigure(1, weight=1)
        dim.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(dim, text="Lato lungo max (px)").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.entry_max_dim = ctk.CTkEntry(dim, width=90)
        self.entry_max_dim.insert(0, "1920")
        self.entry_max_dim.grid(row=0, column=1, padx=6, pady=4, sticky="w")
        self.entry_max_dim.bind("<KeyRelease>", self._aggiorna_evidenzia_da_campo)
        ctk.CTkLabel(dim, text="scegli una misura o scrivi un valore (0 = originale)",
                     font=ctk.CTkFont(size=10), text_color="#9aa0a6").grid(
            row=0, column=2, columnspan=2, padx=6, sticky="w"
        )

        # Misure pronte in ordine crescente: un clic imposta il lato lungo.
        self._misure_pronte = [640, 800, 1024, 1200, 1600, 1920, 2048, 2560, 3000, 4000, 6000, 0]
        self.frame_misure = ctk.CTkFrame(dim, fg_color="transparent")
        self.frame_misure.grid(row=1, column=0, columnspan=4, padx=6, pady=(0, 4), sticky="w")
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
            bottone.grid(row=0, column=indice, padx=2, pady=2)
            self._bottoni_misure.append((valore, bottone))
        self._evidenzia_max_dim(1920)

        ctk.CTkLabel(dim, text="Qualità").grid(row=2, column=0, padx=6, pady=4, sticky="w")
        self.entry_qualita = ctk.CTkEntry(dim, width=80)
        self.entry_qualita.insert(0, "90")
        self.entry_qualita.grid(row=2, column=1, padx=6, pady=4, sticky="w")

        ctk.CTkLabel(dim, text="Formato").grid(row=2, column=2, padx=6, pady=4, sticky="e")
        self.combo_formato = ctk.CTkComboBox(
            dim, values=list(FORMATI_OUTPUT.keys()), width=110,
            command=lambda v: self.parametri.__setitem__("formato", v),
        )
        self.combo_formato.set("JPEG")
        self.combo_formato.grid(row=2, column=3, padx=6, pady=4, sticky="w")

        ctk.CTkLabel(dim, text="Spazio colore").grid(row=3, column=0, padx=6, pady=4, sticky="w")
        self.combo_spazio = ctk.CTkComboBox(
            dim, values=["sRGB", "Adobe RGB", "ProPhoto RGB"], width=140,
            command=lambda v: self.parametri.__setitem__("profilo_colore", v),
        )
        self.combo_spazio.set("sRGB")
        self.combo_spazio.grid(row=3, column=1, padx=6, pady=4, sticky="w")

        self.chk_wb_camera = ctk.CTkCheckBox(dim, text="WB fotocamera")
        self.chk_wb_camera.select()
        self.chk_wb_camera.grid(row=3, column=2, columnspan=2, padx=6, pady=4, sticky="w")

        self.chk_exif = ctk.CTkCheckBox(dim, text="Preserva EXIF")
        self.chk_exif.select()
        self.chk_exif.grid(row=4, column=0, columnspan=2, padx=6, pady=4, sticky="w")

        # ================= BLOCCO NOMI / WATERMARK / PRESET =================
        dx = ctk.CTkFrame(scroll, fg_color="transparent")
        dx.grid(row=1, column=0, padx=4, pady=(8, 2), sticky="ew")
        dx.grid_columnconfigure(1, weight=1)

        r = 0
        ctk.CTkLabel(dx, text="NOMI FILE E SOVRASCRITTURA",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=r, column=0, columnspan=2, padx=6, pady=(6, 2), sticky="w"
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
            row=r, column=0, columnspan=2, padx=6, pady=(6, 2), sticky="w"
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
            row=r, column=0, columnspan=2, padx=6, pady=(6, 2), sticky="w"
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

    def ripristina_sviluppo(self):
        for chiave, (slider, label, fmt) in self._slider_widgets.items():
            default = parametri_default()[chiave]
            slider.set(default)
            label.configure(text=fmt.format(default))
            self.parametri[chiave] = default
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
            ("Google Drive API Key / Folder ID", "entry_gdrive", False, "cloud_gdrive"),
            ("Meta Access Token (FB/IG)", "entry_meta", False, "cloud_meta"),
            ("Meta Account ID", "entry_meta_id", False, "cloud_meta"),
            ("Dropbox Access Token", "entry_dropbox", False, "cloud_dropbox"),
            ("SwissTransfer Email", "entry_swiss", False, "cloud_swiss"),
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
        self.chk_cloud_gdrive = ctk.CTkCheckBox(canali, text="Google Drive")
        self.chk_cloud_gdrive.grid(row=0, column=1, padx=10, pady=6, sticky="w")
        self.chk_cloud_meta = ctk.CTkCheckBox(canali, text="Meta (FB/IG)")
        self.chk_cloud_meta.grid(row=0, column=2, padx=10, pady=6, sticky="w")
        self.chk_cloud_dropbox = ctk.CTkCheckBox(canali, text="Dropbox")
        self.chk_cloud_dropbox.grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.chk_cloud_swiss = ctk.CTkCheckBox(canali, text="SwissTransfer")
        self.chk_cloud_swiss.grid(row=1, column=1, padx=10, pady=6, sticky="w")

        ctk.CTkLabel(
            scroll,
            text="Nota: i canali senza credenziali valide vengono saltati automaticamente.",
            font=ctk.CTkFont(size=11), text_color="#9aa0a6",
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
            self.parametri.update(dati)
            self._applica_config_alla_ui()
            self.scrivi_log(f"Configurazione caricata: {percorso}")
        except Exception as e:
            messagebox.showerror("Errore", f"Caricamento non riuscito:\n{e}")

    def _applica_config_alla_ui(self):
        for chiave, valore in self.parametri.items():
            if chiave in self._slider_widgets:
                try:
                    slider, label, fmt = self._slider_widgets[chiave]
                    slider.set(float(valore))
                    label.configure(text=fmt.format(float(valore)))
                except Exception:
                    pass

        self.entry_max_dim.delete(0, "end")
        self.entry_max_dim.insert(0, str(self.parametri.get("max_dim", 1920)))
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

    # ============================================================ CAMPI
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
    def _raccogli_file_sorgente(self, sorgente, ricorsivo):
        if ";" in sorgente:
            return [f.strip() for f in sorgente.split(";") if f.strip() and os.path.isfile(f.strip())]
        if os.path.isfile(sorgente):
            return [sorgente]
        if not os.path.isdir(sorgente):
            return []

        files = []
        if ricorsivo:
            for root, _, nomi in os.walk(sorgente):
                for nome in nomi:
                    if nome.lower().endswith(ESTENSIONI_ACCETTATE):
                        files.append(os.path.join(root, nome))
        else:
            for nome in os.listdir(sorgente):
                percorso = os.path.join(sorgente, nome)
                if os.path.isfile(percorso) and nome.lower().endswith(ESTENSIONI_ACCETTATE):
                    files.append(percorso)
        return sorted(files)

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
        files = self._raccogli_file_sorgente(sorgente, self.parametri.get("ricorsivo", True))
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

        params = dict(self.parametri)
        thread = threading.Thread(
            target=self._batch_worker, args=(list(files), params, destinazione), daemon=True
        )
        thread.start()

    def _batch_worker(self, files, params, destinazione):
        ok = 0
        errori = 0
        totale = len(files)
        formato = str(params.get("formato", "JPEG")).upper()
        estensione = FORMATI_OUTPUT.get(formato, ".jpg")

        for indice, percorso in enumerate(files, start=1):
            if self._cancel_event.is_set():
                self._log_threadsafe("Batch annullato dall'utente.")
                break

            try:
                base = os.path.splitext(os.path.basename(percorso))[0]
                if params.get("mantieni_nomi", True):
                    nome = f"{params.get('prefisso', '')}{base}{params.get('suffisso', '')}{estensione}"
                else:
                    nome = f"{params.get('prefisso', '')}IMG_{indice:04d}{params.get('suffisso', '')}{estensione}"
                output = os.path.join(destinazione, nome)

                esistente = os.path.exists(output)
                politica = params.get("sovrascrittura", "Rinomina")
                if esistente and politica == "Salta":
                    self._log_threadsafe(f"Saltato (esiste): {nome}")
                    ok += 1
                    self._coda.put(("progress", indice, totale, ok, errori))
                    continue
                if esistente and politica == "Rinomina":
                    contatore = 1
                    while os.path.exists(output):
                        nome = f"{params.get('prefisso', '')}{base}{params.get('suffisso', '')}_{contatore}{estensione}"
                        output = os.path.join(destinazione, nome)
                        contatore += 1

                ImageEngine.sviluppa_e_ottimizza(
                    percorso, output, params, callback=self._log_threadsafe
                )

                if any(params.get(c) for c in ("cloud_telegram", "cloud_gdrive", "cloud_meta",
                                               "cloud_dropbox", "cloud_swiss")):
                    CloudDispatcher.dispatch(output, params, callback=self._log_threadsafe)

                ok += 1
            except Exception as e:
                errori += 1
                logging.error("Errore su %s: %s\n%s", percorso, e, traceback.format_exc())
                self._log_threadsafe(f"ERRORE su {os.path.basename(percorso)}: {e}")

            self._coda.put(("progress", indice, totale, ok, errori))

        self._coda.put(("done", ok, errori))

    def _aggiorna_progresso(self, indice, totale, ok, errori):
        self.progress.set(min(1.0, indice / max(totale, 1)))
        self.lbl_progresso.configure(text=f"{indice} / {totale}  -  OK: {ok}  Errori: {errori}")

    def _fine_batch(self, ok, errori):
        self._batch_attivo = False
        self.btn_avvia.configure(state="normal")
        self.btn_annulla.configure(state="disabled")
        self.lbl_stato.configure(text=f"Completato - OK: {ok}, Errori: {errori}")
        self.lbl_progresso.configure(text=f"Completato - OK: {ok}, Errori: {errori}")
        self.scrivi_log(f"Batch terminato: {ok} conversioni riuscite, {errori} errori.")

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
        except Exception:
            pass
        self.destroy()


# ================================================================================
# 6. ENTRY POINT
# ================================================================================
if __name__ == "__main__":
    app = FranchettiApp()
    app.mainloop()
