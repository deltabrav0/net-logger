# PyInstaller spec for the Windows Net Logger desktop launcher.
# Build from the repository root on Windows:
#   pyinstaller packaging/windows/net-logger.spec --noconfirm --clean

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

net_logger_datas = collect_data_files('net_logger')

a = Analysis(
    ['packaging/windows/net_logger_launcher.py'],
    pathex=[],
    binaries=[],
    datas=net_logger_datas,
    hiddenimports=[],
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
    name='Net Logger',
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
