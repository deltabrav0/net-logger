$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installer = Join-Path $ScriptDir "install.py"
$ScriptArgs = $args
$VersionCheck = "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
$VersionPrint = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

function Invoke-NetLoggerInstaller {
    param([string]$PythonCommand)

    & $PythonCommand -c $VersionCheck | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & $PythonCommand $Installer @ScriptArgs
        exit $LASTEXITCODE
    }

    $FoundVersion = (& $PythonCommand -c $VersionPrint 2>$null)
    if (-not $FoundVersion) { $FoundVersion = "unknown" }
    $Resolved = (Get-Command $PythonCommand -ErrorAction SilentlyContinue).Source
    if (-not $Resolved) { $Resolved = $PythonCommand }
    Write-Error "Found Python $FoundVersion at $Resolved, but it is too old; Python 3.11 or newer is required to install Net Logger."
    exit 1
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    Invoke-NetLoggerInstaller "py"
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    Invoke-NetLoggerInstaller "python"
}

Write-Error "Python 3.11 or newer is required to install Net Logger."
exit 1
