# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Budget Analyser.

This spec file provides cross-platform build configuration for creating
standalone executables for Windows (.exe) and macOS (.app).

Usage:
    pyinstaller budget_analyser.spec

The spec file automatically detects the platform and applies appropriate
settings for icons and data paths.
"""

import sys
from pathlib import Path

# Detect platform
is_windows = sys.platform == 'win32'
is_macos = sys.platform == 'darwin'

# Project paths (spec file is in scripts/ directory)
project_root = Path(SPECPATH).parent
src_path = project_root / 'src' / 'budget_analyser'
assets_path = project_root / 'assets'
data_path = src_path / 'data'

# Icon selection based on platform
if is_windows:
    icon_file = str(assets_path / 'icon.ico')
    # Windows uses semicolon as path separator in --add-data
    data_separator = ';'
elif is_macos:
    icon_file = str(assets_path / 'icon.icns')
    # macOS/Linux uses colon as path separator in --add-data
    data_separator = ':'
else:
    icon_file = None
    data_separator = ':'

# Data files to include
datas = [
    (str(data_path), f'budget_analyser/data'),
    (str(project_root / 'pyproject.toml'), '.'),
    (str(project_root / 'VERSION'), '.'),
]

# Hidden imports for PySide6
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtCharts',
]

block_cipher = None

a = Analysis(
    [str(src_path / '__main__.py')],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Budget Analyser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS app bundle configuration
if is_macos:
    app = BUNDLE(
        exe,
        name='Budget Analyser.app',
        icon=icon_file,
        bundle_identifier='com.budgetanalyser.app',
        info_plist={
            'CFBundleName': 'Budget Analyser',
            'CFBundleDisplayName': 'Budget Analyser',
            'CFBundleGetInfoString': 'Personal finance tracking and analysis tool',
            'CFBundleIdentifier': 'com.budgetanalyser.app',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # Support dark mode
            'LSMinimumSystemVersion': '10.13',
        },
    )
