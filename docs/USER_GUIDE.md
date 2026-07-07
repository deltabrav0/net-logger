# Net Logger User Guide

Net Logger is a small local web app for running an amateur-radio net. It keeps a list of known stations, lets you check stations into an active net, tracks traffic/notes, exports CSV, and shows check-in metrics.

For setup instructions, see the [installation guide](INSTALLATION.md).

## Opening Net Logger

Start the server, then open Net Logger in a browser. The default local address is:

```text
http://127.0.0.1:8088
```

If the server was started on all LAN interfaces, another device on the same network can open the app by using the host computer's LAN address and configured port.

## Basic use

1. Open Net Logger in your browser.
2. Enter a net name, frequency, and Net Control callsign.
3. Press **Start Net**.
4. Net Control is automatically added to **Checked In**.
5. Check in stations by clicking **Check in** or dragging known stations into **Checked In**.
6. Expand a checked-in card to edit traffic and notes.
7. Press **Stop Net** when the net is finished.
8. Open **Saved Nets / Metrics** for CSV export or metrics as needed.

## Starting a net

At the top of the page, enter:

- Net name
- Frequency
- Net Control callsign

After you have saved at least one net, Net Logger pre-fills **Net name** and **Frequency** with the most recent saved values. You can still type over either field at any time.

Press **Start Net**. If Net Control is not already in the station list, Net Logger attempts a local FCC lookup when FCC data is configured. Net Control is then automatically added to the **Checked In** column for the active session.

## Checking in stations

Net Logger uses two main board columns:

- **Known Stations**: stations saved in the database that are not currently checked in
- **Checked In**: stations checked into the active net session

To check in a known station:

- Click **Check in** on the station card, or
- Drag the station card from **Known Stations** to **Checked In**.

Checked-in stations remain attached to the active net session until the session is stopped or the check-in is removed.

## Editing traffic and notes

Expand a checked-in station card to edit:

- Traffic
- Notes

Use these fields during the net to record whether the station has traffic and any follow-up details you need to preserve.

## Adding and checking in stations

Use the single station lookup box labeled **Search or add station**.

- Enter a callsign or operator name.
- As you type, Net Logger shows reusable known-station suggestions with the saved name, location, and grid when those details are available.
- If the typed callsign exactly matches a known station, the helper text confirms the saved station details before you press Enter.
- Net Logger searches known stations first.
- If a matching known callsign is found and a net is open, the existing station record is reused and checked in.
- If no known station matches, Net Logger then searches the local FCC database.
- If FCC data is found, the station is saved with FCC details.
- If FCC data is not found, a callsign-only station is saved.

When a net is open, stations found or created from the lookup box are automatically checked into the active net. When no net is open, the box filters the known-station list as you type and can still be used to save a new station.

Known station cards include two maintenance actions:

- **Update details** — looks up the station's existing callsign in the local FCC database and updates the name, location, grid, latitude, and longitude if FCC data is now available.
- **Delete** — removes the station. Use this only for wrong or unwanted station records; deleting a station also removes saved check-ins for that station.

FCC lookup is local/off-grid. The app does not require internet lookup services such as QRZ. For FCC data setup, see the [installation guide](INSTALLATION.md#fcc-lookup-setup).

## FCC database age and updates

The toolbar shows the local FCC database age, for example `FCC database: 3 days old`. If local FCC data is missing, the indicator shows that the database is unavailable.

Press **Update FCC Database** to download the current FCC amateur-license file, extract the local lookup files, and rebuild the callsign index. The update requires internet access and can take a few minutes. While it is running, the toolbar shows `FCC database: updating…`. When it finishes successfully, the age should change to `updated today`.

To check the update from the command line on a Docker host:

```bash
curl http://127.0.0.1:8088/api/fcc/status
```

A healthy updated database reports `available: true`, `age_days: 0`, and `EN.dat` / `EN.idx` present under `files`. You can also check the files in the container:

```bash
docker compose exec net-logger ls -lh /fcc/data/EN.dat /fcc/data/EN.idx /fcc/data/HD.dat
```

During an update, `EN.dat` and `HD.dat` are downloaded/extracted first, then `EN.idx` is rebuilt. If the browser still says `updating…` for much longer than several minutes, check container logs:

```bash
docker compose logs --tail=100 net-logger
```

## Last Heard timestamps

Known station cards display Last Heard information when available. This helps Net Control quickly see which stations have checked in recently and which stations have not been heard in a while.

## Stopping or canceling a net

Press **Stop Net** when the net is finished. The session and check-ins are saved in the SQLite database.

Press **Cancel Net** when the net was started by mistake or should be discarded. Canceling deletes that net session and its check-ins so it does not appear in Saved Nets, exports, or Metrics. Known station records remain available.

## CSV export

Use CSV export to download saved net records for spreadsheet review, archival records, or external reporting. In the web app, open **Saved Nets / Metrics** from the main page header to reach saved sessions and export links.

## Metrics

Open **Saved Nets / Metrics** from the main page header to view metrics. The Metrics view summarizes check-in activity by net and by time period. Supported grouping periods include:

- Week
- Month
- Year

Use **Net name** to filter metrics to one saved net name, or leave it on **All nets** to compare every saved net.

## WordPress export

If the Net & Meeting Attendance WordPress plugin is configured, open **Saved Nets / Metrics** and press **Send to WordPress** on a saved net. Net Logger sends the saved session and check-ins to the configured WordPress REST endpoint using the configured WordPress username and Application Password.

On **Saved Nets / Metrics**, choose **View/edit WordPress settings** to review or update the endpoint, username, timeout, or Application Password. Leave the Application Password blank to keep the saved password. If required settings are missing, Net Logger opens this form automatically when you try to send a net. Choose **Test Only** to check the connection without saving, or **Save Settings** to test the connection and write the settings to `config.ini`. If the test fails, confirm the endpoint, WordPress username, Application Password, and that the WordPress user has the **Net Control** role.

The WordPress settings live in Net Logger's `config.ini` file under `[wordpress]`:

```ini
[wordpress]
endpoint = https://example.org/wp-json/net-attendance/v1/net-logger/sessions
username = your-wordpress-username
application_password = paste-your-wordpress-application-password-here
timeout = 20
```

A configuration file is just a small text file. Save the file after editing it, then restart Net Logger. See the installation guide for the exact `config.ini` location on Windows, macOS, and Linux.

Net Logger records a successful push locally and disables the button for that saved net afterward. The WordPress plugin also imports by stable `source + external_id` identity, so a retry should update the same event rather than create a duplicate.

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

Stop the server, then copy the SQLite database file. If using default installed paths, see the default database locations in the [installation guide](INSTALLATION.md#running-the-server).

Example on macOS:

```bash
cp "$HOME/Library/Application Support/Net Logger/net_logger.sqlite3" ./net_logger_backup.sqlite3
```
