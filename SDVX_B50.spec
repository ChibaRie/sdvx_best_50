# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['gen_b50.py'],
    pathex=[],
    binaries=[],
    datas=[('msyh.ttc', '.')],
    hiddenimports=['PIL', 'PIL._imagingtk', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'pytest', 'email', 'http',
        'xml', 'pydoc', 'doctest',
        'distutils', 'setuptools', 'pkg_resources', 'pip',
        'multiprocessing', 'concurrent', 'asyncio',
        'sqlite3', 'bz2', 'lzma', 'tarfile',
        'socket', 'ssl', 'selectors',
        'PIL._tkinter_finder', 'PIL.ImageQt', 'PIL.ImageTk',
    ],
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
    name='SDVX_B50',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
