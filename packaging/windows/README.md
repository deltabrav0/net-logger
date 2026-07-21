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
dist\installer\NetLoggerSetup-0.1.2.exe
```

The GitHub Actions workflow at `.github/workflows/windows-installer.yml` builds this installer on Windows, uploads it as a workflow artifact, and attaches it to GitHub Releases when a release is published.
