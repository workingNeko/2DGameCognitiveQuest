# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect all dynamic libraries, C-extensions, and data files for core dependencies
mp_datas, mp_binaries, mp_hiddenimports = collect_all('mediapipe')
cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')
pygame_datas, pygame_binaries, pygame_hiddenimports = collect_all('pygame')

datas = [
    ('assets', 'assets'),
    ('screens', 'screens'),
    ('core', 'core'),
    ('ui', 'ui'),
    ('db', 'db'),
    ('datasets', 'datasets'),
    ('layout_config.json', '.'),
] + mp_datas + cv2_datas + pygame_datas

binaries = mp_binaries + cv2_binaries + pygame_binaries

hiddenimports = [
    'winreg',
    'core',
    'core.autostart_manager',
    'core.cursor_system',
    'core.audio_manager',
    'core.font_manager',
    'core.camera_system',
    'core.pathfinder_guide',
    'core.quiz_dialog',
    'core.sound_effects',
    'core.gba_dialogue',
    'core.hints',
    'core.npc_dialog_system',
    'core.npc_scripts',
    'core.pause_menu',
    'core.philippine_currency',
    'core.report_card',
    'core.vector_icons',
    'core.visual_effects',
    'ui',
    'ui.button',
    'db',
    'db.connect_db',
    'db.save_system',
    'screens',
    'screens.main_menu',
    'screens.stageselect',
    'screens.studentselect',
    'screens.tutorial',
    'screens.quarter1',
    'screens.quarter2',
    'screens.quarter3',
    'screens.quarter4',
    'screens.leaderboard',
    'screens.map_loader',
    'pygame',
    'pygame._sdl2',
    'pygame._sdl2.audio',
    'pygame._sdl2.mixer',
    'cv2',
    'numpy',
    'mediapipe',
    'sqlite3',
    'threading',
    'PIL',
    'PIL.Image',
    'urllib.request',
    'urllib.parse',
    'json',
    'math',
    'time',
    'random',
    'ctypes',
    'csv',
] + mp_hiddenimports + cv2_hiddenimports + pygame_hiddenimports

a = Analysis(
    ['main.py'],
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
    [],
    exclude_binaries=True,
    name='CognitiveMaze',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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
