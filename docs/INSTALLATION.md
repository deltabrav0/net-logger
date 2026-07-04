# Net Logger Installation Guide

Net Logger is an installable Python web app for Windows, macOS, and Linux. It provides a `net-logger` command that starts a local Flask server for the browser UI.

## Requirements

- Python 3.11 or newer
- A modern web browser
- Optional: `pipx` for isolated command-line app installation
- Optional: `uv` for developer workflows
- Optional: local FCC flat-file data for offline callsign lookup

The app runs locally by default at:

```text
http://127.0.0.1:8088
```

## Cross-platform installer script

The repository includes a standard-library Python installer that works on Windows, macOS, and Linux when Python 3.11+ is available.

From a downloaded or cloned checkout:

```bash
python install.py
```

On Windows, you can also use:

```powershell
py install.py
```

The installer defaults to `pipx` and installs from GitHub:

```bash
python install.py --source github --method pipx
```

Useful options:

```bash
python install.py --source local --method pipx
python install.py --source github --method pip
python install.py --source github --method uv
python install.py --upgrade
python install.py --dry-run
```

Small platform wrappers are also included:

macOS/Linux:

```bash
./install.sh
```

Windows PowerShell:

```powershell
.\install.ps1
```

The wrappers delegate to `install.py` so the installation logic stays the same across platforms.

## Docker installation

If Docker Desktop or Docker Engine is installed, Net Logger can run in a container with persistent SQLite data in a Docker volume.

From the repository root:

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8088
```

The default compose file stores data in the `net-logger-data` volume, optionally reads a custom logo from `./config/app-logo.png`, and optionally reads FCC lookup files from `./fcc-data`. See [Docker guide](DOCKER.md) for full details, backup notes, and security guidance.

## Recommended installation from GitHub with pipx

`pipx` installs Python command-line apps into isolated environments. This is the recommended installation method for normal use.

Install pipx if needed:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

Then install Net Logger directly from GitHub:

```bash
pipx install git+https://github.com/deltabrav0/net-logger.git
```

Run it:

```bash
net-logger serve
```

Open:

```text
http://127.0.0.1:8088
```

## Install from GitHub with pip

```bash
python -m pip install "git+https://github.com/deltabrav0/net-logger.git"
net-logger serve
```

## Install from GitHub with uv tool

```bash
uv tool install git+https://github.com/deltabrav0/net-logger.git
net-logger serve
```

## Developer installation from a GitHub checkout

```bash
git clone https://github.com/deltabrav0/net-logger.git
cd net-logger
uv sync --extra dev
uv run net-logger serve
```

## Developer installation from an existing local checkout with uv

From the project directory:

```bash
uv sync --extra dev
uv run net-logger serve
```

Or run the Flask module directly during development:

```bash
uv run --with Flask python -m net_logger.app
```

## Developer installation with pip

```bash
cd /path/to/net-logger
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install:

```bash
python -m pip install -e .
```

Run:

```bash
net-logger serve
```

## Running the server

Default:

```bash
net-logger serve
```

Bind only to localhost:

```bash
net-logger serve --host 127.0.0.1 --port 8088
```

Bind to all LAN interfaces:

```bash
net-logger serve --host 0.0.0.0 --port 8088
```

Use a custom database file:

```bash
net-logger serve --database /path/to/net_logger.sqlite3
```

Environment variables:

- `NET_LOGGER_HOST`: default host, e.g. `0.0.0.0`
- `NET_LOGGER_PORT`: default port, e.g. `8088`
- `NET_LOGGER_DATABASE`: explicit SQLite database path
- `NET_LOGGER_DATA_DIR`: directory used for the default database path
- `NET_LOGGER_DEBUG`: set to `true` for Flask debug mode
- `NET_LOGGER_FCC_LOOKUP_PATH`: local FCC flat-file lookup directory
- `NET_LOGGER_LOGO_PATH`: optional path to a custom PNG logo file
- `NET_LOGGER_WORDPRESS_ENDPOINT`: optional WordPress import endpoint, e.g. `https://example.org/wp-json/net-attendance/v1/net-logger/sessions`
- `NET_LOGGER_WORDPRESS_USERNAME`: WordPress username for Application Password authentication
- `NET_LOGGER_WORDPRESS_APPLICATION_PASSWORD`: WordPress Application Password value; keep this out of shell history, notes, and source control
- `NET_LOGGER_WORDPRESS_TIMEOUT`: optional WordPress request timeout in seconds, default `20`

Default installed database locations:

- Windows: `%APPDATA%\Net Logger\net_logger.sqlite3`
- macOS: `~/Library/Application Support/Net Logger/net_logger.sqlite3`
- Linux: `~/.local/share/net-logger/net_logger.sqlite3`, or `$XDG_DATA_HOME/net-logger/net_logger.sqlite3`

## Customizing the application logo

Net Logger ships with a default logo at:

```text
src/net_logger/static/app-logo.png
```

The default logo is a square PNG image sized `1024 x 1024` pixels. The browser displays it as a smaller header image, but keeping the source image square prevents distortion on high-resolution displays.

There are two supported customization approaches.

### Runtime logo override

For an installed app, save your replacement PNG anywhere readable by the user running Net Logger and set `NET_LOGGER_LOGO_PATH` before starting the server.

Windows PowerShell:

```powershell
$env:NET_LOGGER_LOGO_PATH="C:\path\to\app-logo.png"
net-logger serve
```

macOS/Linux:

```bash
export NET_LOGGER_LOGO_PATH="/path/to/app-logo.png"
net-logger serve
```

Use the same practical shape and format as the bundled logo: PNG, square, ideally `1024 x 1024` pixels. The file may be named anything when using `NET_LOGGER_LOGO_PATH`, but naming it `app-logo.png` keeps deployments consistent.

### Source/distribution logo replacement

If you are building your own branded copy from a Git checkout, replace the bundled file with your logo while keeping the same filename:

```text
src/net_logger/static/app-logo.png
```

Then reinstall or rebuild the package. For best results, use a square `1024 x 1024` PNG. The package configuration includes `static/*.png`, so the replacement logo is included in wheels, source distributions, and PyInstaller builds that collect package data.

## Packaging and distribution

### Build a wheel and source distribution

From the project directory:

```bash
uv build
```

The installable artifacts are written to:

```text
dist/
```

Install the wheel on Windows, macOS, or Linux:

```bash
python -m pip install dist/net_logger-0.1.0-py3-none-any.whl
net-logger serve
```

The wheel is pure Python and cross-platform. It includes the web UI static files.

### Install from a source archive

```bash
python -m pip install dist/net_logger-0.1.0.tar.gz
net-logger serve
```

### Optional single-file executable packaging

For a standalone executable, build on each target operating system with PyInstaller. Cross-building Windows executables from macOS/Linux is generally not supported; build each executable on the OS where it will run.

Install PyInstaller in a build environment:

```bash
python -m pip install pyinstaller
python -m pip install .
```

Build:

```bash
pyinstaller --name net-logger --onefile --collect-data net_logger -m net_logger.cli
```

Run the generated executable from `dist/`:

Windows:

```powershell
.\dist\net-logger.exe serve
```

macOS/Linux:

```bash
./dist/net-logger serve
```

## FCC lookup setup

FCC lookup is local/off-grid. The app does not require internet lookup services such as QRZ.

Set the FCC data path before starting the server:

Windows PowerShell:

```powershell
$env:NET_LOGGER_FCC_LOOKUP_PATH="C:\path\to\fcc_database_web_app"
net-logger serve
```

macOS/Linux:

```bash
export NET_LOGGER_FCC_LOOKUP_PATH="/path/to/fcc_database_web_app"
net-logger serve
```

Expected files under that directory:

```text
data/EN.dat
data/EN.idx
data/zipcodes.csv
maidenhead.py
```

If FCC files are missing, lookup returns `found: false` and the app still works.

Net Logger can also update the FCC files from the browser. The **Update FCC Database** button downloads the FCC amateur-license complete dump, extracts `EN.dat` and `HD.dat`, and rebuilds `data/EN.idx` in the configured FCC lookup directory. This requires internet access on the machine running Net Logger.

Other trusted local/LAN applications can use Net Logger's FCC lookup, status, and update endpoints as a small local FCC database service. See [Local FCC Database API](FCC_DATABASE_API.md).

## Running tests

```bash
uv run --extra dev pytest -q
```
