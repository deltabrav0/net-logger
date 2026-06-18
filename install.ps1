$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Installer = Join-Path $ScriptDir "install.py"

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py $Installer @args
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python $Installer @args
    exit $LASTEXITCODE
}

Write-Error "Python 3.11 or newer is required to install Net Logger."
exit 1
