#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera icona brand 'FRC' per Franchetti Raw Converter Pro
Output: icon.ico (multi-size 16-256) + icon_512.png (512x512 per store)
"""

from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = r"C:\FranchettiRawConverterPro"

def create_icon_base(size):
    """Crea immagine base quadrata con design FRC"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Sfondo circolare gradiente simulato (blu professionale)
    margin = size // 16
    for i in range(size // 2 - margin):
        alpha = int(255 * (1 - i / (size // 2)) * 0.95)
        r = 25 + i // 3
        g = 70 + i // 4
        b = 140 + i // 5
        draw.ellipse([margin + i, margin + i, size - margin - i, size - margin - i], 
                     outline=(r, g, b, alpha), width=2)
    
    # Testo "FRC"
    try:
        font_size = int(size * 0.35)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "FRC"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2 - int(size * 0.04)
    
    # Ombra
    shadow = max(1, size // 64)
    draw.text((x + shadow, y + shadow), text, font=font, fill=(0, 0, 0, 180))
    # Testo principale
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # Piccola fotocamera stilizzata in basso
    cam_size = int(size * 0.18)
    cam_x = (size - cam_size) // 2
    cam_y = y + th + int(size * 0.06)
    # Corpo
    draw.rounded_rectangle([cam_x, cam_y, cam_x + cam_size, cam_y + int(cam_size * 0.6)], 
                           radius=max(1, size // 64), outline=(255, 255, 255, 200), width=max(1, size // 64))
    # Obiettivo
    lens_r = int(cam_size * 0.22)
    draw.ellipse([cam_x + cam_size//2 - lens_r, cam_y + int(cam_size * 0.3) - lens_r,
                  cam_x + cam_size//2 + lens_r, cam_y + int(cam_size * 0.3) + lens_r],
                 outline=(255, 255, 255, 200), width=max(1, size // 64))
    
    return img

def main():
    print("Generazione icone Franchetti Raw Converter Pro...")
    
    # Dimensioni per .ico
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    ico_images = []
    
    for sz in ico_sizes:
        img = create_icon_base(sz)
        ico_images.append(img)
        print(f"  {sz}x{sz} OK")
    
    # Salva .ico multi-risoluzione
    ico_path = os.path.join(OUT_DIR, "icon.ico")
    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=[(im.width, im.height) for im in ico_images],
        append_images=ico_images[1:]
    )
    print(f"\n[OK] icon.ico salvato: {ico_path}")
    
    # Genera 512x512 PNG per store
    png_512 = create_icon_base(512)
    png_path = os.path.join(OUT_DIR, "icon_512.png")
    png_512.save(png_path, format='PNG')
    print(f"[OK] icon_512.png salvato: {png_path} ({png_512.width}x{png_512.height})")
    
    print("\nFatto! File pronti per uptodown.dev")

if __name__ == "__main__":
    main()