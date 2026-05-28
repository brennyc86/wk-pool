# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — WK Pool 2026 (compatibel met PyInstaller 6.x)
# schema.json zit NIET in de exe; hij moet naast de exe staan.

from PyInstaller.utils.hooks import collect_all

flask_datas, flask_bins, flask_hidden = collect_all('flask')
wz_datas, wz_bins, wz_hidden = collect_all('werkzeug')
jinja_datas, jinja_bins, jinja_hidden = collect_all('jinja2')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=flask_bins + wz_bins + jinja_bins,
    datas=flask_datas + wz_datas + jinja_datas,
    hiddenimports=flask_hidden + wz_hidden + jinja_hidden + [
        'flask', 'werkzeug', 'werkzeug.serving', 'werkzeug.exceptions',
        'werkzeug.routing', 'werkzeug.wrappers', 'werkzeug.middleware',
        'werkzeug.middleware.proxy_fix',
        'click', 'jinja2', 'itsdangerous', 'itsdangerous.url_safe',
        'tkinter', '_tkinter', 'tkinter.ttk', 'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
