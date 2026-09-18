# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('datasets', 'datasets'),
        ('db', 'db'),
        ('screens', 'screens'),
        ('ui', 'ui'),
        ('core', 'core'),
        ('layout_config.json', '.')
    ],
    hiddenimports=[
        'pygame',
        'cv2',
        'numpy',
        'mediapipe',
        'sqlite3',
        'threading',
        'PIL',
        'PIL.Image',
        'urllib.request',
        'json',
        'math',
        'time',
        'random'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CognitiveMaze',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True for testing / viewing log outputs; set to False to hide black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CognitiveMaze',
)
