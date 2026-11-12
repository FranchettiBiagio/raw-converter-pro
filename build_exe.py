#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di build per Franchetti Raw Converter Pro.

Windows: crea dist\\FranchettiRawConverterPro.exe (build ufficiale).
Linux/macOS: crea un eseguibile senza estensione (build sperimentale).
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
IS_WINDOWS = os.name == "nt"
OUTPUT_NAME = "FranchettiRawConverterPro"
OUTPUT_EXE = OUTPUT_NAME + (".exe" if IS_WINDOWS else "")
ICON_FILE = PROJECT_DIR / "icon.ico"
VERSION_FILE = PROJECT_DIR / "version_info.txt"
MANIFEST_FILE = PROJECT_DIR / "app.manifest"

# Metadati versione (single source of truth)
VERSION = "2.58.1"
VERSION_TUPLE = (2, 58, 1, 0)


def run_cmd(cmd, cwd=None):
    print(">>> " + (cmd if isinstance(cmd, str) else " ".join(str(parte) for parte in cmd)))
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
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
        import cv2
        import pyftpdlib
        print("Dipendenze OK")
    except ImportError:
        print("Installazione dipendenze...")
        run_cmd([
            sys.executable, "-m", "pip", "install",
            "-r", str(PROJECT_DIR / "requirements.txt"),
        ])

    try:
        import PyInstaller
    except ImportError:
        print("Installazione PyInstaller...")
        run_cmd([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Verifica icona e version info (opzioni solo Windows)
    extra_args = []
    if IS_WINDOWS and ICON_FILE.exists():
        extra_args.append(f"--icon={ICON_FILE}")
        print(f"Icona trovata: {ICON_FILE}")
    elif IS_WINDOWS:
        print("Icona NON trovata (opzionale)")

    if IS_WINDOWS and VERSION_FILE.exists():
        extra_args.append(f"--version-file={VERSION_FILE}")
        print(f"Version info trovata: {VERSION_FILE}")
    elif IS_WINDOWS:
        print("Version info NON trovata (opzionale)")

    if IS_WINDOWS and MANIFEST_FILE.exists():
        extra_args.append(f"--manifest={MANIFEST_FILE}")
        print(f"Manifest DPI trovato: {MANIFEST_FILE}")
    elif IS_WINDOWS:
        print("Manifest DPI NON trovato (opzionale)")

    if not IS_WINDOWS:
        print("Build sperimentale: opzioni icona, version-info e manifest saltate.")
        print("Il binario usera' il tema/icona di sistema e non avra' metadati EXE.")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        *(["--windowed"] if IS_WINDOWS else []),
        f"--name={OUTPUT_NAME}",
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
        "--collect-all=pyftpdlib",
        "--hidden-import=cv2",
        "--hidden-import=pyftpdlib",
        "--hidden-import=pyftpdlib.authorizers",
        "--hidden-import=pyftpdlib.handlers",
        "--hidden-import=pyftpdlib.servers",
        "--hidden-import=pyftpdlib.filesystems",
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
        "--hidden-import=skimage.restoration",
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
        "--hidden-import=multiprocessing",
        "--hidden-import=multiprocessing.spawn",
        *(["--hidden-import=multiprocessing.popen_spawn_win32"] if IS_WINDOWS else []),
        "--hidden-import=concurrent.futures",
        "--hidden-import=concurrent.futures.process",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.simpledialog",
        "--hidden-import=tkinter.scrolledtext",
        "--hidden-import=xml.etree.ElementTree",
        "--hidden-import=zipfile",
        "--hidden-import=hashlib",
        "--hidden-import=colorsys",
        *extra_args,
        str(MAIN_SCRIPT)
    ]

    print(f"\nEsecuzione PyInstaller...")
    run_cmd(" ".join(cmd))

    exe_path = DIST_DIR / OUTPUT_EXE
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n[OK] BUILD COMPLETATO!")
        print(f"Eseguibile: {exe_path}")
        print(f"Dimensione: {size_mb:.1f} MB")
        print(f"Versione: {VERSION}")
        if IS_WINDOWS:
            print(f"\nPer testare: {exe_path}")
        else:
            print(f"\nPer testare: chmod +x '{exe_path}' && '{exe_path}'")
            print(
                "Nota: build sperimentale su Linux/macOS. Se il bundle --onefile "
                "ha problemi, avvia dalla sorgente con: python3 main.py"
            )
    else:
        print(f"\n[ERRORE] Eseguibile non trovato in {exe_path}")
        if not IS_WINDOWS:
            print(
                "Controlla l'output di PyInstaller: su Linux il nome non ha "
                "estensione e deve comparire in dist/."
            )
        sys.exit(1)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
