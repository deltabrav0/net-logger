# Net Logger Installation for Dummies

This guide is for a club officer, net-control operator, or WordPress administrator who wants a plain step-by-step checklist. It avoids developer language as much as possible.

## What you are installing

There are two separate pieces:

1. **Net Logger** — the program the net-control operator opens in a web browser during a net.
2. **Net & Meeting Attendance WordPress plugin** — the optional WordPress add-on that receives saved nets from Net Logger and displays attendance reports on the website.

You can use Net Logger by itself. Install the WordPress plugin only if you want saved nets to appear in WordPress.

## Before you start

You need:

- A computer with Python 3.11 or newer installed.
- A web browser such as Chrome, Edge, Firefox, or Safari.
- If using WordPress export: administrator access to the WordPress site.
- If using WordPress export: the plugin ZIP file named `net-attendance-logger.zip`.

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

Copy and paste this command, then press Enter:

```bash
python -m pip install "git+https://github.com/deltabrav0/net-logger.git"
```

On some Windows computers, use this instead:

```powershell
py -m pip install "git+https://github.com/deltabrav0/net-logger.git"
```

Wait until the command finishes.

### Step 3 — Start Net Logger

Copy and paste this command, then press Enter:

```bash
net-logger serve
```

If Windows says it cannot find `net-logger`, try closing PowerShell, opening it again, and running the command one more time.

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

Skip this part if you do not want WordPress reports.

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

This step lets a non-administrator WordPress user send saved nets from Net Logger.

1. In WordPress, go to **Net Attendance → Settings**.
2. Find **API Import Permissions**.
3. Check the role that should be allowed to send saved nets, such as **DETARC Member**.
4. Click **Save Changes**.

Administrators can always import. This step is mainly for allowing trusted non-administrator operators.

## Part 5 — Create a WordPress Application Password

Do this for the WordPress user that Net Logger will use.

1. In WordPress, go to **Users**.
2. Open the user account that Net Logger should use.
3. Scroll to **Application Passwords**.
4. Enter a name such as:

   ```text
   Net Logger
   ```

5. Click **Add New Application Password**.
6. Copy the password WordPress shows you.

Important: WordPress shows this password only once. If you lose it, delete it and create a new one.

## Part 6 — Connect Net Logger to WordPress

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

Close and reopen the command window. If that does not work, reinstall with:

```bash
python -m pip install --upgrade "git+https://github.com/deltabrav0/net-logger.git"
```

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
