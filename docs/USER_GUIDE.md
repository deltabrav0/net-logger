# Net Logger User Guide

Net Logger is a small local web app for running an amateur-radio net. It keeps a list of known stations, lets you check stations into an active net, tracks traffic/notes, exports CSV, and shows check-in metrics.

## Requirements

- Python 3.11 or newer
- A modern web browser
- Optional: local FCC flat-file data for offline callsign lookup

The app runs locally by default at:

```text
http://127.0.0.1:8088
```

## Installation

### Recommended installation from GitHub on Windows, macOS, and Linux with pipx

`pipx` installs Python command-line apps into isolated environments.

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

### Install from GitHub with pip

```bash
python -m pip install "git+https://github.com/deltabrav0/net-logger.git"
net-logger serve
```

### Install from GitHub with uv tool

```bash
uv tool install git+https://github.com/deltabrav0/net-logger.git
net-logger serve
```

### Developer installation from a GitHub checkout

```bash
git clone https://github.com/deltabrav0/net-logger.git
cd net-logger
uv sync --extra dev
uv run net-logger serve
```

### Developer installation with uv from an existing local checkout

From the project directory:

```bash
uv sync --extra dev
uv run net-logger serve
```

Or run the Flask module directly during development:

```bash
uv run --with Flask python -m net_logger.app
```

### Developer installation with pip

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

Default installed database locations:

- Windows: `%APPDATA%\Net Logger\net_logger.sqlite3`
- macOS: `~/Library/Application Support/Net Logger/net_logger.sqlite3`
- Linux: `~/.local/share/net-logger/net_logger.sqlite3`, or `$XDG_DATA_HOME/net-logger/net_logger.sqlite3`

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

## Basic use

1. Open Net Logger in your browser.
2. Enter a net name, frequency, and Net Control callsign.
3. Press **Start Net**.
4. Net Control is automatically added to **Checked In**.
5. Check in stations by clicking **Check in** or dragging known stations into **Checked In**.
6. Expand a checked-in card to edit traffic and notes.
7. Press **Stop Net** when the net is finished.
8. Use CSV export or Metrics as needed.

## Adding stations

Use the add-station form for a callsign not already listed.

- Enter the callsign.
- Optional: enter a name manually.
- Press **FCC lookup** to populate details from local FCC data if available.
- Press **Add station**.

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

## Deleting all records

Use the administrative reset API when you want a clean database.

Preview what would be deleted:

```bash
curl -X DELETE "http://127.0.0.1:8088/api/records?dry_run=true"
```

Delete everything:

```bash
curl -X DELETE http://127.0.0.1:8088/api/records
```

Warning: this deletes stations, net sessions, and check-ins. Back up the SQLite database first if you may need the data later.

## Backing up data

Stop the server, then copy the SQLite database file. If using default installed paths, see the default database locations above.

Example:

```bash
cp "$HOME/Library/Application Support/Net Logger/net_logger.sqlite3" ./net_logger_backup.sqlite3
```

## Running tests

```bash
uv run --extra dev pytest -q
```
