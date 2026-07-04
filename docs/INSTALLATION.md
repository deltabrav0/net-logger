# Net Logger Installation Guide

Net Logger is an installable Python web app for Windows, macOS, and Linux. It provides a `net-logger` command that starts a small local web server for the browser UI.

If you want a click-by-click checklist for non-technical users, start with [Installation for Dummies](INSTALLATION_FOR_DUMMIES.md). This guide is the fuller reference.

## Installation flow at a glance

1. Install Net Logger on the operator computer.
2. Start Net Logger with `net-logger serve`.
3. Open the browser UI at `http://127.0.0.1:8088`.
4. Optionally configure local FCC lookup data.
5. Optionally install the WordPress plugin.
6. Optionally connect Net Logger to WordPress from **Saved Nets / Metrics → Send to WordPress**.

The WordPress plugin is optional. Net Logger works normally without WordPress.

## Requirements

Required:

- Python 3.11 or newer
- A modern web browser

Optional:

- `pipx` for isolated command-line app installation
- `uv` for developer workflows
- Docker Desktop or Docker Engine for containerized use
- Local FCC flat-file data for offline callsign lookup
- WordPress administrator access if you want WordPress attendance imports and reports

The default local address is:

```text
http://127.0.0.1:8088
```

## Recommended normal installation

For most users, install directly from GitHub with `pip`:

```bash
python -m pip install "git+https://github.com/deltabrav0/net-logger.git"
net-logger serve
```

On Windows, if `python` is not recognized, try:

```powershell
py -m pip install "git+https://github.com/deltabrav0/net-logger.git"
net-logger serve
```

Then open:

```text
http://127.0.0.1:8088
```

Leave the terminal or PowerShell window open while using Net Logger. Closing it stops the server.

## Alternative: install with pipx

`pipx` installs Python command-line apps into isolated environments. This is a good long-term installation method for operators who already have or are comfortable installing `pipx`.

Install pipx if needed:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

Install Net Logger:

```bash
pipx install git+https://github.com/deltabrav0/net-logger.git
net-logger serve
```

Upgrade later with:

```bash
pipx upgrade net-logger
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

If Docker is installed, Net Logger can run in a container with persistent SQLite data in a Docker volume.

From the repository root:

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8088
```

The default compose file stores data in the `net-logger-data` volume, optionally reads a custom logo from `./config/app-logo.png`, and optionally reads FCC lookup files from `./fcc-data`. See [Docker guide](DOCKER.md) for backup, custom logo, FCC data, and security notes.

## Running the server

Default local-only server:

```bash
net-logger serve
```

Explicit local-only address:

```bash
net-logger serve --host 127.0.0.1 --port 8088
```

Allow other devices on the same LAN to open Net Logger:

```bash
net-logger serve --host 0.0.0.0 --port 8088
```

Use a custom database file:

```bash
net-logger serve --database /path/to/net_logger.sqlite3
```

Default installed database locations:

- Windows: `%APPDATA%\Net Logger\net_logger.sqlite3`
- macOS: `~/Library/Application Support/Net Logger/net_logger.sqlite3`
- Linux: `~/.local/share/net-logger/net_logger.sqlite3`, or `$XDG_DATA_HOME/net-logger/net_logger.sqlite3`

## Configuration file

A configuration file is a small text file Net Logger reads when it starts. It lets you change settings without typing long commands or learning shell environment variables. Edit the values after the equals signs, save the file, and restart Net Logger.

Net Logger creates this file automatically the first time it starts:

- Windows: `%APPDATA%\Net Logger\config.ini`
- macOS: `~/Library/Application Support/Net Logger/config.ini`
- Linux: `~/.local/share/net-logger/config.ini`, or `$XDG_DATA_HOME/net-logger/config.ini` when XDG is configured

If you want to keep the file somewhere else, start Net Logger with:

```bash
net-logger --config /path/to/config.ini serve
```

Advanced users may also set `NET_LOGGER_CONFIG` to point to a different configuration file. Other `NET_LOGGER_...` environment variables still work and override the config file, but ordinary users should prefer editing `config.ini`.

Example `config.ini`:

```ini
[server]
# Use 127.0.0.1 for this computer only.
# Use 0.0.0.0 if other computers on your LAN should be able to open Net Logger.
host = 127.0.0.1
port = 8088
debug = false

[paths]
# Leave database blank to use the normal location.
database =
# Optional path to a custom square PNG logo image.
logo_path =
# Optional folder containing local FCC lookup files.
fcc_lookup_path =

[wordpress]
# These settings enable the Saved Nets / Metrics "Send to WordPress" button.
# The endpoint normally ends with /wp-json/net-attendance/v1/net-logger/sessions
endpoint = https://example.org/wp-json/net-attendance/v1/net-logger/sessions
username = your-wordpress-username
application_password = paste-your-wordpress-application-password-here
timeout = 20
```

## WordPress export setup

WordPress export requires two pieces:

1. The **Net & Meeting Attendance** WordPress plugin installed on the WordPress site.
2. Net Logger configured with the WordPress endpoint, username, and Application Password.

### 1. Install the WordPress plugin

The plugin lives in this repository under:

```text
wordpress-plugin/net-attendance-logger
```

The uploadable ZIP is:

```text
wordpress-plugin/net-attendance-logger.zip
```

In WordPress:

1. Log in as an administrator.
2. Go to **Plugins → Add New Plugin → Upload Plugin**.
3. Upload `net-attendance-logger.zip`.
4. If WordPress says the destination folder already exists, choose the option to replace/update the existing plugin.
5. Activate the plugin if it is not already active.
6. Confirm the admin menu contains **Net Attendance**.

Detailed plugin documentation is in [Optional WordPress Plugin](WORDPRESS_PLUGIN.md) and in the plugin's own docs under `wordpress-plugin/net-attendance-logger/docs/`.

### 2. Allow the proper WordPress role to import

REST imports use a custom WordPress capability:

```text
import_net_attendance
```

Administrators are allowed automatically. To allow a non-administrator operator role, such as DETARC Member:

1. Go to **Net Attendance → Settings**.
2. In **API Import Permissions**, check the role that should be allowed to push data.
3. Save settings.
4. Create the WordPress Application Password for a user in that role.

This capability-based setup is preferred over hard-coding a site-specific role name into the REST API.

### 3. Create a WordPress Application Password

Create an Application Password for the WordPress user Net Logger will use. This is not the user's normal WordPress login password. WordPress shows the generated Application Password only once.

Keep `application_password` private. Do not paste it into GitHub issues, screenshots, email, public documentation, or commits.

### 4. Configure Net Logger from the web interface

The easiest first-time setup is from Net Logger itself:

1. Open **Saved Nets / Metrics**.
2. Click **Send to WordPress** on a saved net.
3. If WordPress export is not configured, Net Logger opens a setup form.
4. Enter the endpoint, WordPress username, and Application Password.
5. Click **Test Only** to verify without saving.
6. Click **Test and Save** to verify and write the settings to `config.ini`.
7. Send the saved net again if needed.

The endpoint normally looks like:

```text
https://example.org/wp-json/net-attendance/v1/net-logger/sessions
```

For the DETARC development site:

```text
https://dev.detarc.net/wp-json/net-attendance/v1/net-logger/sessions
```

## WordPress report page setup

To show reports on a normal WordPress page:

1. Create or edit a WordPress page.
2. Add a Shortcode block or Paragraph block.
3. Paste:

   ```text
   [net_attendance_reports]
   ```

4. Publish the page.
5. Add it to the site menu if desired.
6. Restrict the page to members if the site uses page-level member restrictions.

The shortcode performs its own access check. Administrators, users with `view_net_attendance_reports`, and recognized DETARC Member roles can view reports.

## FCC lookup setup

FCC lookup is local/off-grid. The app does not require internet lookup services such as QRZ.

Set `fcc_lookup_path` in the `[paths]` section of `config.ini`:

```ini
[paths]
fcc_lookup_path = /path/to/fcc_database_web_app
```

On Windows, use the Windows folder path:

```ini
[paths]
fcc_lookup_path = C:\path\to\fcc_database_web_app
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

## Customizing the application logo

For an installed app, save your replacement PNG anywhere readable by the user running Net Logger. Then open `config.ini`, find the `[paths]` section, and set `logo_path` to the image file.

Example:

```ini
[paths]
logo_path = /path/to/app-logo.png
```

On Windows:

```ini
[paths]
logo_path = C:\path\to\app-logo.png
```

Use a square PNG, ideally `1024 x 1024` pixels.

If you are building your own branded copy from a Git checkout, replace the bundled source file instead:

```text
src/net_logger/static/app-logo.png
```

Then reinstall or rebuild the package.

## Developer installation

From a GitHub checkout:

```bash
git clone https://github.com/deltabrav0/net-logger.git
cd net-logger
uv sync --extra dev
uv run net-logger serve
```

From an existing local checkout:

```bash
uv sync --extra dev
uv run net-logger serve
```

Developer installation with pip:

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

Install and run:

```bash
python -m pip install -e .
net-logger serve
```

## Packaging and distribution

Build a wheel and source distribution:

```bash
uv build
```

The installable artifacts are written to `dist/`.

Install the wheel:

```bash
python -m pip install dist/net_logger-0.1.0-py3-none-any.whl
net-logger serve
```

Install from a source archive:

```bash
python -m pip install dist/net_logger-0.1.0.tar.gz
net-logger serve
```

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

Run the generated executable from `dist/`.

Windows:

```powershell
.\dist\net-logger.exe serve
```

macOS/Linux:

```bash
./dist/net-logger serve
```

## Running tests

```bash
uv run --extra dev pytest -q
```
