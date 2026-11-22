#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di build per Franchetti Raw Converter Pro.

Windows: crea dist\\FranchettiRawConverterPro.exe (build ufficiale).
Linux: crea la cartella dist/FranchettiRawConverterPro/ con l'eseguibile accanto
       alle librerie (build sperimentale).
macOS: crea l'app dist/FranchettiRawConverterPro.app (build sperimentale).
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
IS_LINUX = sys.platform.startswith("linux")
IS_MAC = sys.platform == "darwin"
OUTPUT_NAME = "FranchettiRawConverterPro"
OUTPUT_EXE = OUTPUT_NAME + (".exe" if IS_WINDOWS else "")
BUNDLE_NAME = OUTPUT_NAME + ".app"
BUNDLE_ID = "it.franchetti.rawconverterpro"
# Su Linux il bundle --onefile si ri-estrae in /tmp a ogni processo figlio:
# con il multiprocessing diventa un ciclo di copie fino a esaurire la RAM.
# --onedir tiene i file accanto all'eseguibile e il problema non si presenta.
# Su macOS vale lo stesso ragionamento: anche lì --onefile si scompatta in una
# cartella temporanea a ogni avvio, e il bundle .app funziona meglio con --onedir.
USARE_ONEDIR = (IS_LINUX or IS_MAC) and os.environ.get("FRC_ONEFILE", "") != "1"
ICON_FILE = PROJECT_DIR / "icon.ico"
ICNS_FILE = PROJECT_DIR / "icon.icns"
VERSION_FILE = PROJECT_DIR / "version_info.txt"
MANIFEST_FILE = PROJECT_DIR / "app.manifest"

# Metadati versione (single source of truth)
VERSION = "2.58.2"
VERSION_TUPLE = (2, 58, 2, 0)


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

    if IS_MAC:
        if ICNS_FILE.exists():
            extra_args.append(f"--icon={ICNS_FILE}")
            print(f"Icona trovata: {ICNS_FILE}")
        else:
            print("Icona .icns NON trovata: l'app usera' l'icona generica (opzionale).")
            print("Per crearla: vedi 'Icona macOS' in LINUX_MACOS.md")

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
        if IS_MAC:
            print("Build macOS: creo dist/FranchettiRawConverterPro.app (doppio clic).")
        elif USARE_ONEDIR:
            print("Build --onedir: i file restano accanto all'eseguibile (consigliato su Linux).")
        if sys.version_info >= (3, 14):
            print(
                "\nATTENZIONE: Python %s su Linux usa 'forkserver' per il multiprocessing.\n"
                "Con un programma impacchettato e' la combinazione che manda in crash\n"
                "l'applicazione a catena. Per la build consigliata usa Python 3.11 o 3.12\n"
                "(per esempio: conda create -n frc python=3.12)." % sys.version.split()[0]
            )

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        *(["--onedir"] if USARE_ONEDIR else ["--onefile"]),
        *(["--windowed"] if (IS_WINDOWS or IS_MAC) else []),
        *([f"--osx-bundle-identifier={BUNDLE_ID}"] if IS_MAC else []),
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
        # ImageTk carica _tkinter_finder a runtime: senza questo, su Linux le
        # anteprime non vengono disegnate (ModuleNotFoundError su PIL._tkinter_finder).
        "--hidden-import=PIL.ImageTk",
        "--hidden-import=PIL._tkinter_finder",
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

    if IS_MAC:
        exe_path = DIST_DIR / BUNDLE_NAME
    elif USARE_ONEDIR:
        exe_path = DIST_DIR / OUTPUT_NAME / OUTPUT_EXE
    else:
        exe_path = DIST_DIR / OUTPUT_EXE

    if exe_path.exists():
        if exe_path.is_dir():
            byte_totali = sum(p.stat().st_size for p in exe_path.rglob("*") if p.is_file())
        else:
            byte_totali = exe_path.stat().st_size
        size_mb = byte_totali / (1024 * 1024)
        print(f"\n[OK] BUILD COMPLETATO!")
        print(f"Eseguibile: {exe_path}")
        print(f"Dimensione: {size_mb:.1f} MB")
        print(f"Versione: {VERSION}")
        if IS_WINDOWS:
            print(f"\nPer testare: {exe_path}")
        elif IS_MAC:
            print(f"\nPer testare: open '{exe_path}'")
            print(
                "Primo avvio senza firma Apple: clic destro sull'app, poi Apri (oppure\n"
                "Impostazioni di Sistema > Privacy e Sicurezza > Apri comunque)."
            )
            print(
                "\nPer distribuirla, comprimi il bundle preservando permessi e link:\n"
                f"  ditto -c -k --sequesterRsrc --keepParent '{exe_path}' "
                f"{OUTPUT_NAME}-macOS.zip"
            )
            print(
                "Non usare il compressore del Finder ne' 'zip -r': rompono i link\n"
                "interni della .app e l'app non parte piu'."
            )
        else:
            print(f"\nPer testare: chmod +x '{exe_path}' && '{exe_path}'")
            if USARE_ONEDIR:
                print(
                    "La cartella dist/" + OUTPUT_NAME + "/ va tenuta insieme: "
                    "l'eseguibile da solo non parte."
                )
        if not IS_WINDOWS:
            print(
                "Nota: build sperimentale su Linux/macOS. Se il binario ha problemi, "
                "avvia dalla sorgente con: python3 main.py"
            )
    else:
        print(f"\n[ERRORE] Eseguibile non trovato in {exe_path}")
        if IS_MAC:
            print(
                "Controlla l'output di PyInstaller: su macOS deve comparire "
                f"dist/{BUNDLE_NAME}."
            )
        elif not IS_WINDOWS:
            print(
                "Controlla l'output di PyInstaller: su Linux il nome non ha "
                "estensione e deve comparire in dist/."
            )
        sys.exit(1)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
