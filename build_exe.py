#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di build per creare FranchettiRawConverterPro.exe su Windows
Uso: python build_exe.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
MAIN_SCRIPT = PROJECT_DIR / "main.py"
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
OUTPUT_EXE = "FranchettiRawConverterPro.exe"
ICON_FILE = PROJECT_DIR / "icon.ico"
VERSION_FILE = PROJECT_DIR / "version_info.txt"
MANIFEST_FILE = PROJECT_DIR / "app.manifest"

# Metadati versione (single source of truth)
VERSION = "2.52.0"
VERSION_TUPLE = (2, 50, 1, 0)


def run_cmd(cmd, cwd=None):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Comando fallito: {cmd}")
    return result


def main():
    print("=" * 60)
    print(f"BUILD Franchetti Raw Converter Pro v{VERSION}")
    print("=" * 60)

    if not MAIN_SCRIPT.exists():
        print(f"ERRORE: {MAIN_SCRIPT} non trovato")
        sys.exit(1)

    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            print(f"Pulizia {d}...")
            shutil.rmtree(d, ignore_errors=True)

    print("\nVerifica dipendenze...")
    try:
        import rawpy
        import PIL
        import numpy
        print("Dipendenze OK")
    except ImportError:
        print("Installazione dipendenze...")
        run_cmd(f"{sys.executable} -m pip install -r {PROJECT_DIR / 'requirements.txt'}")

    try:
        import PyInstaller
    except ImportError:
        print("Installazione PyInstaller...")
        run_cmd(f"{sys.executable} -m pip install pyinstaller")

    # Verifica icona e version info
    extra_args = []
    if ICON_FILE.exists():
        extra_args.append(f"--icon={ICON_FILE}")
        print(f"Icona trovata: {ICON_FILE}")
    else:
        print("Icona NON trovata (opzionale)")

    if VERSION_FILE.exists():
        extra_args.append(f"--version-file={VERSION_FILE}")
        print(f"Version info trovata: {VERSION_FILE}")
    else:
        print("Version info NON trovata (opzionale)")

    if MANIFEST_FILE.exists():
        extra_args.append(f"--manifest={MANIFEST_FILE}")
        print(f"Manifest DPI trovato: {MANIFEST_FILE}")
    else:
        print("Manifest DPI NON trovato (opzionale)")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        f"--name={OUTPUT_EXE.replace('.exe', '')}",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={PROJECT_DIR}",
        "--clean",
        "--noconfirm",
        "--collect-all=imageio",
        "--collect-all=skimage",
        "--collect-all=customtkinter",
        "--collect-all=watchdog",
        "--collect-all=piexif",
        "--collect-all=requests",
        "--hidden-import=rawpy",
        "--hidden-import=rawpy._rawpy",
        "--hidden-import=numpy",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=PIL.ImageFont",
        "--hidden-import=PIL.ImageOps",
        "--hidden-import=imageio",
        "--hidden-import=imageio.v3",
        "--hidden-import=skimage",
        "--hidden-import=skimage.color",
        "--hidden-import=skimage.filters",
        "--hidden-import=customtkinter",
        "--hidden-import=watchdog",
        "--hidden-import=watchdog.observers",
        "--hidden-import=watchdog.events",
        "--hidden-import=piexif",
        "--hidden-import=requests",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=PIL.ImageFont",
        "--hidden-import=PIL.ImageOps",
        "--hidden-import=PIL.ImageCms",
        "--hidden-import=PIL.ImageFilter",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.scrolledtext",
        *extra_args,
        str(MAIN_SCRIPT)
    ]

    print(f"\nEsecuzione PyInstaller...")
    run_cmd(" ".join(cmd))

    exe_path = DIST_DIR / OUTPUT_EXE
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] BUILD COMPLETATO!")
        print(f"Executable: {exe_path}")
        print(f"Dimensione: {size_mb:.1f} MB")
        print(f"Versione: {VERSION}")
        print(f"\nPer testare: {exe_path}")
    else:
        print(f"\n[ERRORE] Executable non trovato in {exe_path}")
        sys.exit(1)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
