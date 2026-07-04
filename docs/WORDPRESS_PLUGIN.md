# Optional WordPress Plugin

Net Logger includes the optional WordPress plugin under:

`wordpress-plugin/net-attendance-logger`

The plugin is named **Net & Meeting Attendance**. It is not required for normal Net Logger use. Install it only when you want Net Logger to send saved net sessions into WordPress for public attendance pages, reports, or manual attendance workflows.

## What the plugin provides

- A WordPress custom-table attendance store for events, participants, and attendance records.
- REST endpoints for authenticated imports from Net Logger.
- A Net Logger-native endpoint:

  `POST /wp-json/net-attendance/v1/net-logger/sessions`

- WordPress admin pages for import, reporting, and manual attendance-taking.
- Public shortcode/reporting support documented in the plugin's own docs.

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

- `wordpress-plugin/net-attendance-logger/docs/installation.md`
- `wordpress-plugin/net-attendance-logger/docs/usage.md`
- `wordpress-plugin/net-attendance-logger/docs/api.md`
- `wordpress-plugin/net-attendance-logger/docs/reports.md`
- `wordpress-plugin/net-attendance-logger/readme.txt`

## Packaging note

To install the plugin on a WordPress site, zip the `net-attendance-logger` directory itself, not the whole Net Logger repository.

Example from the repository root:

```bash
cd wordpress-plugin
zip -r net-attendance-logger.zip net-attendance-logger \
  -x '*/__pycache__/*' '*.pyc' '.pytest_cache/*'
```
