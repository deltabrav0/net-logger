# Optional WordPress Plugin

Net Logger includes the optional WordPress plugin under:

`wordpress-plugin/net-attendance-logger`

The plugin is named **Net & Meeting Attendance**. It is not required for normal Net Logger use. Install it only when you want Net Logger to send saved net sessions into WordPress for public attendance pages, reports, or manual attendance workflows.

For DETARC-style role separation, the WordPress site also needs the **Members plugin by MemberPress**. Net & Meeting Attendance relies on that plugin-created role structure so **Net Control** users can send/take attendance while **DETARC Member** users remain view-only for Events and Reports.

## What the plugin provides

- A WordPress custom-table attendance store for events, participants, and attendance records.
- REST endpoints for authenticated imports from Net Logger.
- A Net Logger-native endpoint:

  `POST /wp-json/net-attendance/v1/net-logger/sessions`

- WordPress admin pages for import, reporting, rapid summary entry, manual attendance-taking, and event metadata editing.
- Public shortcode/reporting support documented in the plugin's own docs, including participation snapshot cards, top participants, new participants, milestones, and attendance trend charts.

## How this relates to Net Logger configuration

In Net Logger, configure WordPress export with the reports-page setup form or in `config.ini`:

```ini
[wordpress]
endpoint = https://example.org/wp-json/net-attendance/v1/net-logger/sessions
username = your-wordpress-username
application_password = paste-your-wordpress-application-password-here
timeout = 20
```

Use a WordPress Application Password for a trusted operator/admin user. Do not commit real credentials to git or paste them into documentation.

## Plugin documentation

The imported plugin documentation is kept with the plugin:

- `wordpress-plugin/net-attendance-logger/docs/installation.md` — plugin upload, permissions, Application Passwords, Net Logger connection, and verification
- `wordpress-plugin/net-attendance-logger/docs/usage.md` — admin pages, manual attendance, and shortcodes
- `wordpress-plugin/net-attendance-logger/docs/api.md` — REST endpoints and payloads
- `wordpress-plugin/net-attendance-logger/docs/reports.md` — report behavior and shortcode access
- `wordpress-plugin/net-attendance-logger/RELEASE_NOTES.md` — plugin-specific release notes
- `wordpress-plugin/net-attendance-logger/readme.txt` — WordPress plugin readme

For a non-technical end-to-end checklist covering both Net Logger and WordPress, see [Installation for Dummies](INSTALLATION_FOR_DUMMIES.md).

## Packaging note

To install the plugin on a WordPress site, upload the prepared ZIP at:

```text
wordpress-plugin/net-attendance-logger.zip
```

To rebuild that ZIP from the repository root:

```bash
cd wordpress-plugin
rm -f net-attendance-logger.zip
zip -r net-attendance-logger.zip net-attendance-logger \
  -x '*/__pycache__/*' '*.pyc' '.pytest_cache/*' '*.DS_Store'
```

Package the `net-attendance-logger` directory itself, not the whole Net Logger repository.
