# Windows Packaging

This directory contains the native Windows packaging files for Net Logger.

Build on Windows from the repository root:

```powershell
python -m pip install --upgrade pip
python -m pip install . pyinstaller
choco install innosetup -y
pyinstaller packaging/windows/net-logger.spec --noconfirm --clean
iscc packaging\windows\net-logger.iss
```

The PyInstaller step creates `dist\Net Logger.exe`. The Inno Setup step creates:

```text
dist\installer\NetLoggerSetup-0.1.1.exe
```

The workflow can be automated with GitHub Actions later once the pushing token has permission to create or update workflow files.
