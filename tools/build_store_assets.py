"""Genera gli asset grafici per il Microsoft Store di Franchetti Raw Converter Pro.

Sorgenti: screenshot reali catturati con PrintWindow dalla GUI 2.58.1.
Output: store_assets/screenshots/*.png (1920x1080), hero, loghi.

Uso:  python tools/build_store_assets.py
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = r"C:\Users\Administrator\AppData\Local\Temp\opencode\store_shots\final_raw"
OUT = os.path.join(ROOT, "store_assets")
SHOTS = os.path.join(OUT, "screenshots")
HERO = os.path.join(OUT, "hero")
LOGOS = os.path.join(OUT, "logos")

FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_SEMI = r"C:\Windows\Fonts\segoeuisl.ttf"
ICON = os.path.join(ROOT, "icon_512.png")

W, H = 1920, 1080

BG_TOP = (10, 13, 18)
BG_BOTTOM = (17, 23, 31)
BLUE = (59, 130, 246)
CYAN = (34, 211, 238)
GREEN = (52, 211, 153)
TEXT = (244, 248, 252)
MUTED = (146, 164, 184)
BORDER = (44, 58, 74)
CARD = (15, 20, 27)


def font(path, size):
    return ImageFont.truetype(path, size)


def load_icon():
    """Ritaglia il disco del logo e ricostruisce un canale alpha pulito.

    Il PNG sorgente ha un alpha inaffidabile: il disco viene isolato dal
    contenuto RGB e mascherato con un cerchio antialias.
    """
    im = Image.open(ICON).convert("RGB").crop((32, 32, 481, 481))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, im.size[0] - 1, im.size[1] - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.5))
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def vertical_gradient(w, h, top, bottom):
    t = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    arr = np.array(top, dtype=np.float32)[None, None, :] * (1 - t) + np.array(
        bottom, dtype=np.float32
    )[None, None, :] * t
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def add_glow(img, cx, cy, radius, color, strength):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(np.float32)
    alpha = np.exp(-(dist / float(radius)) ** 2) * strength
    alpha = np.clip(alpha, 0, 1)[..., None]
    base = np.asarray(img, dtype=np.float32)
    tint = np.array(color, dtype=np.float32)[None, None, :]
    out = base[..., :3] * (1 - alpha) + tint * alpha
    rgb = np.clip(out, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB").convert("RGBA")


def tracked_text(draw, xy, text, fnt, fill, tracking=0, anchor_left=True):
    x, y = xy
    if not anchor_left:
        width = sum(draw.textlength(c, font=fnt) + tracking for c in text) - tracking
        x -= width
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    return mask


def paste_card(base, shot, box, radius=16, border=BORDER):
    """Inserisce lo screenshot in una card arrotondata con ombra morbida."""
    x, y, w, h = box
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.rounded_rectangle([x - 6, y + 14, x + w + 6, y + h + 22], radius + 6, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    base.alpha_composite(shadow)

    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    card.paste(CARD + (255,), (0, 0, w, h))
    base.alpha_composite(card, (x, y))

    resized = shot.convert("RGB").resize((w, h), Image.LANCZOS).convert("RGBA")
    resized.putalpha(rounded_mask((w, h), radius))
    base.alpha_composite(resized, (x, y))

    frame = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(
        [x, y, x + w - 1, y + h - 1], radius, outline=border + (255,), width=2
    )
    base.alpha_composite(frame)


def fit(box_w, box_h, src_w, src_h):
    scale = min(box_w / src_w, box_h / src_h)
    w = int(round(src_w * scale))
    h = int(round(src_h * scale))
    x = (W - w) // 2
    y = AREA_Y + (box_h - h) // 2
    return x, y, w, h


AREA_Y = 246
AREA_H = 792


def base_canvas():
    img = vertical_gradient(W, H, BG_TOP, BG_BOTTOM)
    img = add_glow(img, 260, 120, 520, (22, 44, 82), 0.55)
    img = add_glow(img, W - 180, H - 80, 620, (10, 52, 46), 0.45)
    # barra accento superiore
    bar = Image.new("RGBA", (W, 6), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    for x in range(W):
        t = x / (W - 1)
        if t < 0.5:
            k = t / 0.5
            col = tuple(int(BLUE[i] * (1 - k) + CYAN[i] * k) for i in range(3))
        else:
            k = (t - 0.5) / 0.5
            col = tuple(int(CYAN[i] * (1 - k) + GREEN[i] * k) for i in range(3))
        bd.line([(x, 0), (x, 6)], fill=col + (255,))
    img.alpha_composite(bar, (0, 0))
    return img


def brand_row(img, draw):
    icon = load_icon().resize((40, 40), Image.LANCZOS)
    img.alpha_composite(icon, (72, 44))
    tracked_text(
        draw, (124, 52), "FRANCHETTI RAW CONVERTER PRO", font(FONT_BOLD, 19),
        (188, 203, 219), tracking=3.2,
    )
    # pill versione
    f = font(FONT_REG, 16)
    label = "v2.58.1"
    tw = draw.textlength(label, font=f)
    box = [W - 72 - (tw + 34), 48, W - 72, 84]
    draw.rounded_rectangle(box, 18, fill=(23, 32, 43, 255), outline=(48, 64, 82, 255), width=1)
    draw.text((box[0] + 17, 55), label, font=f, fill=(150, 178, 205))


def headline(draw, title, subtitle):
    draw.text((72, 104), title, font=font(FONT_BOLD, 50), fill=TEXT)
    draw.text((72, 170), subtitle, font=font(FONT_REG, 25), fill=MUTED)


def build_shot(src, dest, title, subtitle):
    img = base_canvas()
    draw = ImageDraw.Draw(img)
    brand_row(img, draw)
    headline(draw, title, subtitle)
    shot = Image.open(src)
    box = fit(W - 144, AREA_H, shot.width, shot.height)
    paste_card(img, shot, box)
    img.convert("RGB").save(dest, "PNG", optimize=True)
    print("screenshot", dest, img.size)


def build_hero():
    hw, hh = 2340, 1200
    img = vertical_gradient(hw, hh, (9, 12, 17), (15, 21, 29))
    img = add_glow(img, 380, 220, 700, (20, 42, 80), 0.6)
    img = add_glow(img, hw - 260, hh - 140, 780, (10, 48, 42), 0.5)
    draw = ImageDraw.Draw(img)

    # barra accento
    bar = Image.new("RGBA", (hw, 8), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    for x in range(hw):
        t = x / (hw - 1)
        if t < 0.5:
            k = t / 0.5
            col = tuple(int(BLUE[i] * (1 - k) + CYAN[i] * k) for i in range(3))
        else:
            k = (t - 0.5) / 0.5
            col = tuple(int(CYAN[i] * (1 - k) + GREEN[i] * k) for i in range(3))
        bd.line([(x, 0), (x, 8)], fill=col + (255,))
    img.alpha_composite(bar, (0, 0))

    icon = load_icon().resize((64, 64), Image.LANCZOS)
    img.alpha_composite(icon, (110, 92))
    tracked_text(draw, (194, 106), "FRANCHETTI RAW CONVERTER PRO", font(FONT_BOLD, 25),
                 (190, 206, 222), tracking=4.0)

    draw.text((110, 236), "Da RAW a JPEG,", font=font(FONT_BOLD, 92), fill=TEXT)
    draw.text((110, 344), "pronti da consegnare.", font=font(FONT_BOLD, 92), fill=TEXT)
    draw.text(
        (112, 486),
        "25+ formati RAW, pipeline Y/Cb/Cr, preset portabili .frcpreset,",
        font=font(FONT_REG, 31), fill=MUTED,
    )
    draw.text(
        (112, 530),
        "tethering multi-marca e Cloud. Originali mai modificati.",
        font=font(FONT_REG, 31), fill=MUTED,
    )

    chips = ["25+ formati RAW", "Preset .frcpreset", "Zero telemetria"]
    x = 112
    f = font(FONT_SEMI, 24)
    for text in chips:
        tw = draw.textlength(text, font=f)
        box = [x, 630, x + tw + 44, 684]
        draw.rounded_rectangle(box, 22, fill=(22, 32, 44, 255), outline=(46, 62, 80, 255), width=1)
        draw.text((x + 22, 645), text, font=f, fill=(160, 186, 210))
        x = box[2] + 18

    shot = Image.open(os.path.join(RAW, "01_batch.png"))
    target_w = 1180
    target_h = int(round(target_w * shot.height / shot.width))
    x = hw - target_w - 96
    y = (hh - target_h) // 2 + 10
    # ombra
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x - 8, y + 18, x + target_w + 8, y + target_h + 28], 24, fill=(0, 0, 0, 180)
    )
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(34)))
    resized = shot.convert("RGB").resize((target_w, target_h), Image.LANCZOS).convert("RGBA")
    resized.putalpha(rounded_mask((target_w, target_h), 18))
    img.alpha_composite(resized, (x, y))
    frame = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(
        [x, y, x + target_w - 1, y + target_h - 1], 18, outline=(52, 68, 88, 255), width=2
    )
    img.alpha_composite(frame)

    dest = os.path.join(HERO, "hero_2340x1200.png")
    img.convert("RGB").save(dest, "PNG", optimize=True)
    print("hero", dest, img.size)


def build_logos():
    base = load_icon()
    for size in (300, 1080, 2160):
        im = base.resize((size, size), Image.LANCZOS)
        if size >= 1080:
            k = size / 1080.0
            r, g, b, a = im.split()
            rgb = Image.merge("RGB", (r, g, b)).filter(ImageFilter.GaussianBlur(0.55 * k))
            a = a.filter(ImageFilter.GaussianBlur(1.1 * k))
            r, g, b = rgb.split()
            im = Image.merge("RGBA", (r, g, b, a))
        dest = os.path.join(LOGOS, f"logo_{size}x{size}.png")
        im.save(dest, "PNG", optimize=True)
        print("logo", dest, im.size)


def main():
    for d in (OUT, SHOTS, HERO, LOGOS):
        os.makedirs(d, exist_ok=True)

    shots = [
        ("01_batch.png", "01_batch_1920x1080.png",
         "Batch RAW → JPEG con anteprima Prima/Dopo",
         "25+ formati, pipeline Y/Cb/Cr, originali sempre in sola lettura."),
        ("09_anteprima_grande.png", "02_anteprima_1920x1080.png",
         "Anteprima Prima/Dopo a schermo intero",
         "Colore, bianco e nero e dettaglio sotto controllo in tempo reale."),
        ("02_avanzate_top.png", "03_avanzate_1920x1080.png",
         "Controllo completo su esposizione, toni e colore",
         "Slider in tempo reale, curve tonali, split toning e LUT 3D .cube."),
        ("03_avanzate_preset.png", "04_preset_1920x1080.png",
         "Preset portabili, watermark e nomi file",
         "File .frcpreset leggibili, copyright EXIF/IPTC e logo PNG trasparente."),
        ("05_analisi.png", "05_smartbatch_1920x1080.png",
         "Smart Batch: analisi e correzioni per ogni foto",
         "Esposizione, clipping, contrasto, colore e rumore misurati sul RAW."),
        ("04_prestazioni.png", "06_prestazioni_1920x1080.png",
         "Prestazioni adattive al tuo PC",
         "Profili Veloce, Bilanciato e Massima qualità con benchmark reale."),
        ("06_tethering.png", "07_tethering_1920x1080.png",
         "Tethering multi-marca e Cloud Dispatch",
         "Hot-folder, Sony Wi-Fi diretto, invio Telegram e Dropbox."),
        ("07_ftp.png", "08_wifi_ftp_1920x1080.png",
         "Wi-Fi FTP: scatta e ricevi l'anteprima",
         "La fotocamera invia, il PC sviluppa e pubblica la galleria cliente."),
        ("08_log.png", "09_log_1920x1080.png",
         "Log operazioni e diagnostica",
         "Ogni passaggio è tracciato ed esportabile su file."),
    ]
    for src, dest, title, sub in shots:
        build_shot(os.path.join(RAW, src), os.path.join(SHOTS, dest), title, sub)

    build_hero()
    build_logos()
    print("Tutto generato in", OUT)


if __name__ == "__main__":
    main()
