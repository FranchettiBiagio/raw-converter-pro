#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera icon.ico multi-misura per Franchetti Raw Converter Pro.

Sorgente: icona.png (512x512, mockup del logo con sfondo chiaro e didascalia).
Il tile viene ritagliato, reso quadrato, mascherato con angoli arrotondati e
privato dello sfondo; sotto i 48 px si usa un disegno semplificato (tile scuro,
anello blu, freccia bianca) perche' il logo completo diventa illeggibile.

Uso:
    python tools/make_icon.py

Scrive icon.ico nella radice del progetto. Le misure sono 10: 16, 20, 24, 32,
40, 48, 64, 96, 128 e 256 px; la 256 e' compressa in PNG, le altre in BMP.
"""

from PIL import Image, ImageDraw
import io
import os
import struct

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(PROJECT_DIR, "icona.png")
OUTPUT = os.path.join(PROJECT_DIR, "icon.ico")

# ritaglio del tile dentro il mockup 512x512 (misurato sull'immagine)
TILE_CENTER = (256, 265)
TILE_SIDE = 346
CORNER_RATIO = 0.225
PADDING_RATIO = 0.04

SIMPLIFIED_SIZES = (16, 20, 24, 32, 40)
DETAILED_SIZES = (48, 64, 96, 128, 256)

TILE_TOP = (60, 82, 100)
TILE_BOTTOM = (14, 24, 38)
RING_COLOR = (74, 159, 224)
ARROW_COLOR = (245, 247, 250)


def load_tile():
    """Ritaglia il tile dal mockup e lo rende quadrato."""
    img = Image.open(SOURCE).convert("RGB")
    half = TILE_SIDE // 2
    box = (
        TILE_CENTER[0] - half,
        TILE_CENTER[1] - half,
        TILE_CENTER[0] + half,
        TILE_CENTER[1] + half,
    )
    return img.crop(box)


def rounded_mask(size, radius_ratio=CORNER_RATIO, supersample=4):
    """Maschera con angoli arrotondati, antialiasata per supersampling."""
    s = size * supersample
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=int(s * radius_ratio), fill=255
    )
    return mask.resize((size, size), Image.LANCZOS)


def detailed(size, tile):
    """Logo completo, ridimensionato dal tile ad alta risoluzione."""
    inner = max(1, int(round(size * (1 - 2 * PADDING_RATIO))))
    art = tile.resize((inner, inner), Image.LANCZOS)
    art.putalpha(rounded_mask(inner))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = (size - inner) // 2
    out.paste(art, (offset, offset), art)
    return out


def simplified(size):
    """Disegno dedicato alle misure piccole: tile, anello, freccia."""
    s = size * 8
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    gradient = Image.new("RGB", (1, s))
    pixels = gradient.load()
    for y in range(s):
        t = y / (s - 1)
        pixels[0, y] = tuple(
            int(TILE_TOP[i] + (TILE_BOTTOM[i] - TILE_TOP[i]) * t) for i in range(3)
        )
    gradient = gradient.resize((s, s))

    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=int(s * CORNER_RATIO), fill=255
    )
    img.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(img)
    center = s // 2
    radius = int(s * 0.395)
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        outline=RING_COLOR + (255,),
        width=max(2, int(s * 0.030)),
    )

    arrow_w, arrow_h = int(s * 0.44), int(s * 0.22)
    x0 = center - arrow_w // 2
    y0 = center - arrow_h // 2
    body = int(arrow_w * 0.55)
    draw.polygon(
        [
            (x0, y0 + arrow_h // 3),
            (x0 + body, y0 + arrow_h // 3),
            (x0 + body, y0),
            (x0 + arrow_w, center),
            (x0 + body, y0 + arrow_h),
            (x0 + body, y0 + 2 * arrow_h // 3),
            (x0, y0 + 2 * arrow_h // 3),
        ],
        fill=ARROW_COLOR + (255,),
    )

    art = img.resize((size, size), Image.LANCZOS)
    inner = max(1, int(round(size * (1 - 2 * PADDING_RATIO))))
    art = art.resize((inner, inner), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = (size - inner) // 2
    out.paste(art, (offset, offset), art)
    return out


def bmp_entry(image):
    """Payload BMP (BITMAPINFOHEADER + pixel BGRA + maschera AND)."""
    w, h = image.size
    px = image.load()

    rows = []
    for y in range(h - 1, -1, -1):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[x, y]
            row += bytes((b, g, r, a))
        rows.append(bytes(row))
    pixels = b"".join(rows)

    stride = ((w + 31) // 32) * 4
    mask = bytearray()
    for y in range(h - 1, -1, -1):
        bits = bytearray(stride)
        for x in range(w):
            if px[x, y][3] < 128:
                bits[x // 8] |= 0x80 >> (x % 8)
        mask += bits

    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    return header + pixels + bytes(mask)


def png_entry(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def write_ico(frames, path):
    entries, blobs = [], []
    offset = 6 + 16 * len(frames)
    for size, image in frames:
        blob = png_entry(image) if size >= 256 else bmp_entry(image)
        entries.append(
            struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(blob), offset)
        )
        offset += len(blob)
        blobs.append(blob)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<HHH", 0, 1, len(frames)) + b"".join(entries) + b"".join(blobs))


def main():
    tile = load_tile()
    frames = []
    for size in SIMPLIFIED_SIZES:
        frames.append((size, simplified(size)))
    for size in DETAILED_SIZES:
        frames.append((size, detailed(size, tile)))

    write_ico(frames, OUTPUT)
    print(f"[OK] {OUTPUT} - {os.path.getsize(OUTPUT)} byte")
    print("     misure:", ", ".join(str(s) for s, _ in frames))


if __name__ == "__main__":
    main()
