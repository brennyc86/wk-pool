# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — WK Pool 2026
# schema.json zit NIET in de exe; hij moet naast de exe staan.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'flask', 'werkzeug', 'werkzeug.serving', 'werkzeug.exceptions',
        'werkzeug.routing', 'werkzeug.wrappers', 'werkzeug.middleware',
        'click', 'jinja2', 'itsdangerous', 'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.ztos, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WK_Pool_2026',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # Geen zwart venster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
