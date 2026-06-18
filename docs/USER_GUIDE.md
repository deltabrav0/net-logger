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
8. Use CSV export or Metrics as needed.

## Starting a net

At the top of the page, enter:

- Net name
- Frequency
- Net Control callsign

The **Net name** and **Frequency** fields are editable suggestion boxes. After you have saved nets, Net Logger suggests previous net names and previous frequencies. Choosing a previous net name, such as **Weekly Net**, automatically fills the frequency with that net's most recently used frequency. You can still type a new net name or frequency at any time.

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

- Enter a callsign.
- Net Logger searches known stations first.
- If a matching known callsign is found and a net is open, the station is checked in.
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

Press **Update FCC Database** to download the current FCC amateur-license file, extract the local lookup files, and rebuild the callsign index. The update requires internet access and can take a few minutes.

## Last Heard timestamps

Known station cards display Last Heard information when available. This helps Net Control quickly see which stations have checked in recently and which stations have not been heard in a while.

## Stopping or canceling a net

Press **Stop Net** when the net is finished. The session and check-ins are saved in the SQLite database.

Press **Cancel Net** when the net was started by mistake or should be discarded. Canceling deletes that net session and its check-ins so it does not appear in Saved Nets, exports, or Metrics. Known station records remain available.

## CSV export

Use CSV export to download saved net records for spreadsheet review, archival records, or external reporting.

## Metrics

The Metrics view summarizes check-in activity by net and by time period. Supported grouping periods include:

- Week
- Month
- Year

Use **Net name** to filter metrics to one saved net name, or leave it on **All nets** to compare every saved net.

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
