# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['rawpy', 'rawpy._rawpy', 'numpy', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageOps', 'imageio', 'imageio.v3', 'skimage', 'skimage.color', 'skimage.filters', 'customtkinter', 'watchdog', 'watchdog.observers', 'watchdog.events', 'piexif', 'requests', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageOps', 'PIL.ImageCms', 'PIL.ImageFilter', 'PIL.ImageDraw', 'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.scrolledtext']
tmp_ret = collect_all('imageio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('skimage')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('watchdog')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('piexif')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('requests')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:/FranchettiRawConverterPro/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FranchettiRawConverterPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='C:/FranchettiRawConverterPro/version_info.txt',
    icon=['C:/FranchettiRawConverterPro/icon.ico'],
    manifest='C:/FranchettiRawConverterPro/app.manifest',
)
