"""Costruisce il pacchetto MSIX per il Microsoft Store.

Il pacchetto contiene l'EXE onefile gia' compilato, gli asset grafici
(tile e logo generati da icon_512.png) e il manifest compilato dal template
in msix\\AppxManifest.xml.template.

Uso:
    python tools\\build_msix.py
    python tools\\build_msix.py --publisher "CN=FranchettiAcademy" --identity "FranchettiAcademy.FranchettiRawConverterPro"
    python tools\\build_msix.py --version 2.58.2.0

Per la pubblicazione i valori di --publisher e --identity devono essere quelli
mostrati in Partner Center (Product identity) del prodotto MSIX.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "msix", "AppxManifest.xml.template")
ICON = os.path.join(ROOT, "icon_512.png")
DEFAULT_EXE = os.path.join(ROOT, "dist", "FranchettiRawConverterPro.exe")
DEFAULT_LAYOUT = os.path.join(ROOT, "build", "msix", "layout")
DEFAULT_OUT = os.path.join(ROOT, "Output", "FranchettiRawConverterPro_2.58.1.0_x64.msix")

APP_FILE = "FranchettiRawConverterPro.exe"


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


def fit_logo(canvas_w, canvas_h, logo, fraction=0.8):
    size = int(round(min(canvas_w, canvas_h) * fraction))
    logo = logo.resize((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    canvas.alpha_composite(logo, ((canvas_w - size) // 2, (canvas_h - size) // 2))
    return canvas


def write_assets(assets_dir, icon):
    os.makedirs(assets_dir, exist_ok=True)
    targets = {
        "StoreLogo.png": (50, 50, 0.98),
        "Square44x44Logo.png": (44, 44, 0.98),
        "Square150x150Logo.png": (150, 150, 0.86),
        "Square310x310Logo.png": (310, 310, 0.76),
        "Wide310x150Logo.png": (310, 150, 0.78),
        "SplashScreen.png": (620, 300, 0.55),
    }
    for name, (w, h, fraction) in targets.items():
        img = fit_logo(w, h, icon, fraction)
        path = os.path.join(assets_dir, name)
        img.save(path, "PNG", optimize=True)
        print(f"  asset {name} {w}x{h}")


def find_makeappx():
    local = glob.glob(os.path.join(ROOT, "tools", "sdkbuildtools", "bin", "*", "x64", "makeappx.exe"))
    if local:
        local.sort(key=lambda p: [int(x) for x in os.path.basename(os.path.dirname(os.path.dirname(p))).split(".")])
        return local[-1]
    kits = glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe")
    if kits:
        kits.sort()
        return kits[-1]
    raise SystemExit(
        "makeappx.exe non trovato. Scarica 'Windows SDK Build Tools' oppure installa "
        "il Windows SDK con i componenti di packaging."
    )


def render_manifest(values):
    with open(TEMPLATE, encoding="utf-8") as fh:
        text = fh.read()
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    missing = [k for k in ("IDENTITY_NAME", "PUBLISHER", "VERSION", "DISPLAY_NAME",
                           "PUBLISHER_DISPLAY_NAME", "DESCRIPTION") if "{{" + k + "}}" in text]
    if missing:
        raise SystemExit("Segnaposto non sostituiti: " + ", ".join(missing))
    return text


def main():
    parser = argparse.ArgumentParser(description="Crea il pacchetto MSIX")
    parser.add_argument("--exe", default=DEFAULT_EXE)
    parser.add_argument("--layout", default=DEFAULT_LAYOUT)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--publisher", default="CN=FranchettiAcademy")
    parser.add_argument("--identity", default="FranchettiAcademy.FranchettiRawConverterPro")
    parser.add_argument("--version", default="2.58.1.0")
    parser.add_argument("--display-name", default="Franchetti Raw Converter Pro")
    parser.add_argument("--publisher-display", default="Franchetti Academy")
    parser.add_argument("--description", default="Da RAW a JPEG con preset, batch e tethering.")
    args = parser.parse_args()

    if not os.path.isfile(args.exe):
        raise SystemExit(f"EXE non trovato: {args.exe}")

    version = args.version.count(".") == 3 and args.version or args.version + ".0"

    print("Preparazione layout MSIX...")
    if os.path.isdir(args.layout):
        shutil.rmtree(args.layout)
    os.makedirs(args.layout, exist_ok=True)

    shutil.copy2(args.exe, os.path.join(args.layout, APP_FILE))
    write_assets(os.path.join(args.layout, "Assets"), load_icon())

    manifest = render_manifest({
        "IDENTITY_NAME": args.identity,
        "PUBLISHER": args.publisher,
        "VERSION": version,
        "DISPLAY_NAME": args.display_name,
        "PUBLISHER_DISPLAY_NAME": args.publisher_display,
        "DESCRIPTION": args.description,
    })
    with open(os.path.join(args.layout, "AppxManifest.xml"), "w", encoding="utf-8") as fh:
        fh.write(manifest)
    print("  AppxManifest.xml")
    print(f"  identity:  {args.identity}")
    print(f"  publisher: {args.publisher}")
    print(f"  version:   {version}")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    if os.path.exists(args.out):
        os.remove(args.out)

    makeappx = find_makeappx()
    print(f"Pacchetto con {makeappx}")
    result = subprocess.run(
        [makeappx, "pack", "/d", args.layout, "/p", args.out, "/o"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"makeappx fallito (exit {result.returncode})")

    size = os.path.getsize(args.out)
    print(f"\nCreato: {args.out}  ({size / (1024 * 1024):.1f} MB)")
    print("Prossimo passo: firmare il pacchetto con tools\\sign_msix_dev.ps1")
    print("(per lo Store la firma puo' essere self-signed: Microsoft ri-firma l'MSIX)")


if __name__ == "__main__":
    main()
