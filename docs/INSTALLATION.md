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

Not required for normal installs:

- Git. The recommended commands below install from GitHub's ZIP archive and do not need `git.exe` on PATH.

Optional:

- Git, only for developer checkout workflows such as `git clone` or `pip install git+https://...`. On Windows, choose the Git installer option that adds Git to PATH if you use those workflows.
- `pipx` for isolated command-line app installation
- `uv` for developer workflows
- Docker Desktop or Docker Engine for containerized use
- Local FCC flat-file data for offline callsign lookup
- WordPress administrator access if you want WordPress attendance imports and reports
- The Members plugin by MemberPress on WordPress if you want the club-specific Net Control role and DETARC Member roles for WordPress imports/reports

The default local address is:

```text
http://127.0.0.1:8088
```

## Recommended Windows installation: native installer

For ordinary Windows operators, the preferred installation is the native Windows installer from the GitHub Releases page:

```text
NetLoggerSetup-0.1.1.exe
```

This installer is intended for users who are used to double-clicking a setup program instead of using PowerShell. It installs the Net Logger desktop launcher, creates Start Menu shortcuts, and can optionally create a Desktop shortcut. The launcher starts the local Net Logger server and opens the browser automatically, so the operator does not need to type `net-logger serve`.

Typical Windows steps:

1. Download `NetLoggerSetup-0.1.1.exe` from the Net Logger release.
2. Double-click the downloaded installer.
3. Follow the installer prompts.
4. Start Net Logger from the Start Menu.
5. If the browser does not open automatically, use the launcher window's **Open Net Logger** button.

The installer stores the application under the normal Windows app location selected by the installer, commonly `Program Files` for all-user installs or the user's local programs folder for per-user installs. Runtime data remains outside the application folder:

```text
%APPDATA%\Net Logger
```

That data folder contains the SQLite database and `config.ini`. Uninstalling the application should not delete saved net data unless you deliberately remove this data folder.

### Windows security warning / SmartScreen

Until Net Logger has a code-signing certificate and enough download reputation, Windows may show a warning such as:

```text
Windows protected your PC
Microsoft Defender SmartScreen prevented an unrecognized app from starting.
```

If you downloaded the installer from the official GitHub Releases page for `deltabrav0/net-logger` and the filename is the expected `NetLoggerSetup-0.1.1.exe`, this warning means Windows does not yet recognize the publisher. To continue:

1. Click **More info**.
2. Confirm the app name is Net Logger or NetLoggerSetup.
3. Click **Run anyway**.

Do not click **Run anyway** for a copy received from an unknown email, chat attachment, file-sharing site, or unofficial download page. When in doubt, delete the file and download it again from the official GitHub release.

## Recommended Python command-line installation

For macOS, Linux, advanced Windows users, or troubleshooting, install with `pipx` from GitHub's ZIP archive. This avoids a Git requirement and keeps Net Logger in an isolated per-user Python app environment instead of a Python-version-specific `Scripts` folder.

Windows PowerShell:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
py -m pipx install --force https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
net-logger serve
```

If PowerShell says `net-logger` is not recognized immediately after install, close PowerShell, open a new PowerShell window, and try again. You can also run the installed command by full path:

```powershell
& "$env:USERPROFILE\.local\bin\net-logger.exe" serve
```

macOS/Linux:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
python3 -m pipx install --force https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
net-logger serve
```

On Windows, the pipx command shim normally lives at `%USERPROFILE%\.local\bin\net-logger.exe`, the isolated app environment normally lives under `%USERPROFILE%\.local\pipx\venvs\net-logger`, and runtime data/config live under `%APPDATA%\Net Logger`. This is a normal per-user Python CLI layout. Installing under `Program Files` would require a separate native Windows installer/MSI.

Then open:

```text
http://127.0.0.1:8088
```

Leave the terminal or PowerShell window open while using Net Logger. Closing it stops the server.

## Alternative: direct pip install

If you do not want pipx, `pip` can also install Net Logger from the same GitHub ZIP archive without requiring Git. This may put the `net-logger.exe` launcher in a Python-version-specific `Scripts` directory on Windows, so pipx is preferred for normal operators.

```bash
python -m pip install --user --upgrade https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
python -m net_logger.cli serve
```

On Windows, if `python` is not recognized, use:

```powershell
py -m pip install --user --upgrade https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
py -m net_logger.cli serve
```

The `py -m net_logger.cli serve` fallback bypasses PATH entirely, which is useful if Windows cannot find `net-logger.exe`.

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

The installer defaults to `pipx` and installs from GitHub's ZIP archive, so Git is not required:

```bash
python install.py --source github --method pipx
```

Useful options:

```bash
python install.py --source local --method pipx
python install.py --source github --method pip
python install.py --source github --method uv
python install.py --package-url https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
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

WordPress export requires three pieces:

1. The **Members plugin by MemberPress** installed on the WordPress site so the **Net Control** and **DETARC Member** roles can be created.
2. The **Net & Meeting Attendance** WordPress plugin installed on the WordPress site.
3. Net Logger configured with the WordPress endpoint, username, and Application Password for a user with the **Net Control** role.

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

Administrators are allowed automatically. Non-administrator API users must have the **Net Control** role created through the Members plugin by MemberPress:

1. Confirm the **Net Control** role exists with the slug `net_control`.
2. Assign the WordPress API user to the **Net Control** role.
3. Go to **Net Attendance → Settings** and confirm **API Import Permissions** shows Net Control as allowed.
4. Create the WordPress Application Password for that Net Control user.

DETARC Member users are view-only for Events and Reports & Charts; they cannot push Net Logger sessions through the API.

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
6. Click **Save Settings** to verify and write the settings to `config.ini`.
7. Send the saved net again if needed.

If Net Logger reports that the WordPress connection, authentication, or authorization failed, confirm the endpoint, username, Application Password, and that the WordPress user has the **Net Control** role.

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
python -m pip install dist/net_logger-0.1.1-py3-none-any.whl
net-logger serve
```

Install from a source archive:

```bash
python -m pip install dist/net_logger-0.1.1.tar.gz
net-logger serve
```

For the native Windows installer, build on Windows.

Manual Windows build:

```powershell
python -m pip install --upgrade pip
python -m pip install . pyinstaller
choco install innosetup -y
pyinstaller packaging/windows/net-logger.spec --noconfirm --clean
iscc packaging\windows\net-logger.iss
```

The PyInstaller spec builds the windowed desktop launcher from `packaging/windows/net_logger_launcher.py`. The Inno Setup script writes the installer to:

```text
dist/installer/NetLoggerSetup-0.1.1.exe
```

Cross-building Windows executables from macOS/Linux is generally not supported; build the Windows executable and installer on Windows. A future GitHub Actions workflow can automate this after the repository token used for pushes has permission to create or update workflow files.

## Running tests

```bash
uv run --extra dev pytest -q
```

## Uninstalling Net Logger

If using the Windows native installer, first quit the Net Logger launcher window. Then open Windows **Settings → Apps → Installed apps**, choose **Net Logger**, and select **Uninstall**. You can also use the Start Menu's normal uninstall entry if Windows shows one.

If using the Python command-line installation, stop the running server first with `Ctrl+C` in the terminal or PowerShell window where `net-logger serve` is running.

If installed with pipx, remove the application environment:

```bash
pipx uninstall net-logger
```

On Windows, this may also be run as:

```powershell
py -m pipx uninstall net-logger
```

If installed with direct pip instead of pipx, use:

```bash
python -m pip uninstall net-logger
```

Uninstalling the Python package does not delete saved nets or settings. Remove these directories only after backing up any data you need:

- Windows: `%APPDATA%\Net Logger`
- macOS: `~/Library/Application Support/Net Logger`
- Linux: `~/.local/share/net-logger`, or `$XDG_DATA_HOME/net-logger` when XDG is configured

For the optional WordPress integration, a WordPress administrator can deactivate and delete **Net & Meeting Attendance** under **Plugins → Installed Plugins**, remove the reports page under **Pages**, and revoke any Application Password created only for Net Logger. Deleting the plugin files may not remove previously imported attendance records from the WordPress database; back up WordPress before deleting site data.
