# Net Logger Installation for Dummies

This guide is for a club officer, net-control operator, or WordPress administrator who wants a plain step-by-step checklist. It avoids developer language as much as possible.

## What you are installing

There are two separate pieces:

1. **Net Logger** — the program the net-control operator opens in a web browser during a net.
2. **Net & Meeting Attendance WordPress plugin** — the optional WordPress add-on that receives saved nets from Net Logger and displays attendance reports on the website.

You can use Net Logger by itself. Install the WordPress plugin only if you want saved nets to appear in WordPress.

For most users, **Part 1** and **Part 2** are the only parts needed to run a net. **Parts 3 through 6 are WordPress administrator setup tasks** for enabling the WordPress website to receive Net Logger attendance reports. **Part 7 is also usually a WordPress administrator or website manager task** because it creates or changes a public/member website page.

## Before you start

You need:

- A Windows, macOS, or Linux computer with Python 3.11 or newer installed.
- A web browser such as Chrome, Edge, Firefox, or Safari.
- On Windows: PowerShell.
- If using WordPress export: administrator access to the WordPress site.
- If using WordPress export: the plugin ZIP file named `net-attendance-logger.zip`.

You do **not** need Git for the normal instructions below. Git is only needed if you choose the developer-style `git clone` workflow in the fuller installation guide.

Important password note:

- Do not use your normal WordPress password inside Net Logger.
- WordPress will create a special **Application Password** for Net Logger.
- WordPress shows that Application Password only once. Copy it when it is created and keep it private.

## Part 1 — Install Net Logger on the operator computer

### Step 1 — Open a command window

On Windows:

1. Open the Start menu.
2. Type `PowerShell`.
3. Open Windows PowerShell.

On macOS:

1. Open Applications.
2. Open Utilities.
3. Open Terminal.

### Step 2 — Install Net Logger

These commands install Net Logger from GitHub's ZIP archive, so Git is not required.

On Windows PowerShell, copy and paste these commands one at a time:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
py -m pipx install --force https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
```

Then close PowerShell and open a new PowerShell window. This lets Windows reload the updated PATH.

On macOS or Linux Terminal, copy and paste these commands one at a time:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
python3 -m pipx install --force https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
```

Then close Terminal and open a new Terminal window.

Where Windows puts it:

- The Net Logger command is normally exposed from `%USERPROFILE%\.local\bin\net-logger.exe`.
- The isolated Python app files are normally under `%USERPROFILE%\.local\pipx\venvs\net-logger`.
- Net Logger's database and config are stored separately under `%APPDATA%\Net Logger`.

This is the normal per-user Python command-line app layout. It does not install into `Program Files` unless we later build a native Windows installer/MSI.

Wait until each command finishes before running the next one.

### Step 3 — Start Net Logger

Copy and paste this command, then press Enter:

```bash
net-logger serve
```

If Windows says it cannot find `net-logger`, run it by its full path:

```powershell
& "$env:USERPROFILE\.local\bin\net-logger.exe" serve
```

If that works, the installation is good and Windows has not reloaded PATH yet. Close PowerShell, open a new PowerShell window, and try `net-logger serve` again.

Leave this command window open while you use Net Logger. Closing it stops Net Logger.

### Step 4 — Open Net Logger in your browser

Open your browser and go to:

```text
http://127.0.0.1:8088
```

You should see the Net Logger page.

## Part 2 — Use Net Logger for a net

1. Type the net name.
2. Type the frequency.
3. Type the Net Control callsign.
4. Click **Start Net**.
5. Check in stations as they call in.
6. Add traffic or notes if needed.
7. Click **Stop Net** when the net is finished.
8. Open **Saved Nets / Metrics** to review, export CSV, or send the net to WordPress.

## Part 3 — Install the WordPress plugin

**WordPress administrator only.** Skip this part if you do not want WordPress reports. A normal net-control operator does not need to do this unless they also administer the WordPress site.

### Step 1 — Log in to WordPress

Open your WordPress admin page. For the DETARC development site:

```text
https://dev.detarc.net/wp-admin/
```

Log in as a WordPress administrator.

### Step 2 — Upload the plugin ZIP

1. In the left WordPress menu, go to **Plugins**.
2. Click **Add New Plugin**.
3. Click **Upload Plugin**.
4. Choose the file named:

   ```text
   net-attendance-logger.zip
   ```

5. Click **Install Now**.
6. If WordPress asks whether to replace the existing plugin, choose the replace/update option.
7. Click **Activate Plugin** if it is not already active.

### Step 3 — Confirm the plugin is installed

In the WordPress left menu, look for:

```text
Net Attendance
```

If you see that menu, the plugin is installed.

## Part 4 — Allow the right WordPress users to receive Net Logger imports

**WordPress administrator only.** This step lets a non-administrator WordPress user send saved nets from Net Logger after the administrator grants the proper import permission.

1. In WordPress, go to **Net Attendance → Settings**.
2. Find **API Import Permissions**.
3. Check the role that should be allowed to send saved nets, such as **DETARC Member**.
4. Click **Save Changes**.

Administrators can always import. This step is mainly for allowing trusted non-administrator operators.

## Part 5 — Create a WordPress Application Password

**WordPress administrator setup, or a user working under administrator direction.** Do this for the WordPress user that Net Logger will use. The Application Password belongs to a specific WordPress user account; it is not the user's normal login password.

There are two common ways to create it.

### Option A — Administrator creates it for a user

1. In WordPress, go to **Users**.
2. Open the user account that Net Logger should use.
3. Scroll to **Application Passwords**.
4. Enter a name such as:

   ```text
   Net Logger
   ```

5. Click **Add New Application Password**.
6. Copy the password WordPress shows you.

### Option B — User creates their own Application Password

If the WordPress administrator has already given the user permission to import Net Logger reports, the user can usually create their own Application Password this way:

1. Log in to WordPress.
2. In the top-right corner, click the user's name, or go to **Users → Profile**.
3. Scroll down to **Application Passwords**.
4. Enter a name such as:

   ```text
   Net Logger
   ```

5. Click **Add New Application Password**.
6. Copy the password WordPress shows you.
7. Give the password only to the person configuring Net Logger, or paste it directly into Net Logger yourself.

Important: WordPress shows this password only once. If you lose it, delete it and create a new one. Do not email or post this password publicly.

## Part 6 — Connect Net Logger to WordPress

**WordPress administrator setup, or a trusted operator working with administrator-provided settings.** This connects the operator's Net Logger installation to the WordPress REST endpoint so saved nets can be sent to WordPress.

1. Start Net Logger if it is not already running:

   ```bash
   net-logger serve
   ```

2. Open Net Logger in your browser:

   ```text
   http://127.0.0.1:8088
   ```

3. Open **Saved Nets / Metrics**.
4. Find a saved net.
5. Click **Send to WordPress**.
6. If Net Logger is not configured yet, it will open a setup form.
7. Enter the WordPress endpoint. For a normal site, it looks like this:

   ```text
   https://example.org/wp-json/net-attendance/v1/net-logger/sessions
   ```

   For DETARC development, use:

   ```text
   https://dev.detarc.net/wp-json/net-attendance/v1/net-logger/sessions
   ```

8. Enter the WordPress username.
9. Paste the WordPress Application Password.
10. Click **Test Only** first.
11. If the test succeeds, click **Test and Save**.
12. Click **Send to WordPress** again if needed.

## Part 7 — Create the WordPress reports page

**Usually a WordPress administrator or website manager task.** This part creates or changes a WordPress page on the website. A normal net-control operator usually does not need to do this.

1. In WordPress, go to **Pages → Add New Page**.
2. Name the page something like:

   ```text
   Net Attendance Reports
   ```

3. Add a Shortcode block or Paragraph block.
4. Paste this shortcode:

   ```text
   [net_attendance_reports]
   ```

5. Publish the page.
6. If desired, add it to the site menu.
7. If your site uses member-only page restrictions, restrict this page to members.

The plugin also checks permissions itself, so the report data remains protected even if the page is visible in a menu.

## Part 8 — Test the full flow

Use this checklist after installation:

1. Start Net Logger.
2. Open `http://127.0.0.1:8088`.
3. Start a short test net.
4. Check in one or two test stations.
5. Stop the net.
6. Open **Saved Nets / Metrics**.
7. Click **Send to WordPress**.
8. In WordPress, open **Net Attendance → Events** and confirm the event appears.
9. Open **Net Attendance → Reports & Charts** and confirm the report counts make sense.
10. Open the public/member reports page and confirm it displays correctly.

## Common problems

### Net Logger page does not open

Make sure the command window running Net Logger is still open. Then try again:

```text
http://127.0.0.1:8088
```

### `net-logger` command is not found

On Windows, first try the full pipx command path:

```powershell
& "$env:USERPROFILE\.local\bin\net-logger.exe" serve
```

If that starts Net Logger, close PowerShell, open a new PowerShell window, and try the shorter command again:

```powershell
net-logger serve
```

If the full path does not exist, reinstall with:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
py -m pipx install --force https://github.com/deltabrav0/net-logger/archive/refs/heads/main.zip
```

Older instructions used `python -m pip install git+https://...`, which requires Git and can place `net-logger.exe` under a Python-specific `Scripts` folder such as `AppData\Local\Python\pythoncore-...\Scripts`. The current beginner instructions avoid that route.

### WordPress says the import is not authorized

Check these items:

1. The WordPress username is correct.
2. You used an Application Password, not the normal login password.
3. The user is an administrator, or the user's role is checked under **Net Attendance → Settings → API Import Permissions**.
4. The Application Password was copied correctly.

### WordPress export endpoint is wrong

The endpoint must end with:

```text
/wp-json/net-attendance/v1/net-logger/sessions
```

For example:

```text
https://dev.detarc.net/wp-json/net-attendance/v1/net-logger/sessions
```

### A saved net was already sent

Net Logger remembers successful sends and disables the send button for that saved net. The WordPress importer is also designed to avoid duplicate records if a request is retried.

## Part 9 — Uninstall Net Logger

Use this section only if you want to remove Net Logger from a computer or remove the optional WordPress reporting setup.

### Stop Net Logger first

If Net Logger is running, go to the command window where `net-logger serve` is running and press:

```text
Ctrl+C
```

Then close that command window.

### Uninstall Net Logger from the operator computer

If you installed Net Logger with the recommended `pipx` commands, uninstall it with:

On Windows PowerShell:

```powershell
py -m pipx uninstall net-logger
```

On macOS or Linux Terminal:

```bash
python3 -m pipx uninstall net-logger
```

This removes the Net Logger program, but it does **not** automatically delete your saved nets, configuration file, or WordPress connection settings. That is intentional so you do not lose records by accident.

### Optional: delete saved Net Logger data and settings

Only do this if you are sure you no longer need the saved nets, station list, WordPress settings, custom logo setting, or FCC lookup settings on that computer.

Default data and settings locations:

- Windows: `%APPDATA%\Net Logger`
- macOS: `~/Library/Application Support/Net Logger`
- Linux: `~/.local/share/net-logger`

On Windows PowerShell, you can open the folder first to inspect or back it up:

```powershell
explorer "$env:APPDATA\Net Logger"
```

To delete it from Windows PowerShell after you have backed up anything you need:

```powershell
Remove-Item -Recurse -Force "$env:APPDATA\Net Logger"
```

On macOS Terminal, delete it with:

```bash
rm -rf "$HOME/Library/Application Support/Net Logger"
```

On Linux Terminal, delete it with:

```bash
rm -rf "$HOME/.local/share/net-logger"
```

### If you installed Net Logger with direct pip instead of pipx

Most users should have used `pipx`. If older instructions were used with direct `pip`, uninstall with:

On Windows PowerShell:

```powershell
py -m pip uninstall net-logger
```

On macOS or Linux Terminal:

```bash
python3 -m pip uninstall net-logger
```

### Optional: remove the WordPress plugin and reports page

**WordPress administrator only.** Do this only if the website should stop receiving and displaying Net Logger attendance reports.

1. In WordPress, go to **Plugins → Installed Plugins**.
2. Find **Net & Meeting Attendance**.
3. Click **Deactivate**.
4. If you also want to remove the plugin files, click **Delete** after it is deactivated.
5. If you created a reports page, go to **Pages**, find that page, and move it to the Trash.
6. If you created a WordPress Application Password only for Net Logger, open that user's profile and revoke/delete that Application Password.

Deleting the plugin from WordPress removes the plugin files. It may not remove previously imported attendance records from the WordPress database, depending on the plugin's current uninstall behavior. Back up WordPress before deleting site data.

## Daily use after everything is installed

For normal use, the operator only needs this:

1. Open a command window.
2. Run:

   ```bash
   net-logger serve
   ```

3. Open:

   ```text
   http://127.0.0.1:8088
   ```

4. Run the net.
5. Stop the net.
6. Send it to WordPress from **Saved Nets / Metrics** if desired.
