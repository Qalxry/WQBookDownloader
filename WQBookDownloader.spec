# -*- mode: python ; coding: utf-8 -*-

import PyInstaller.config
import os
import datetime
PyInstaller.config.CONF['distpath'] = os.path.join('dist', f'build-{datetime.datetime.now().strftime("%Y%m%d")}')

a = Analysis(
    ['wqdl/main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/*','assets')],
    hiddenimports=[
        "flet",
        "selenium",
    ],
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
    name='WQBookDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.png'],
)
