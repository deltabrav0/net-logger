# Net & Meeting Attendance Installation

## Development environment

Current DETARC WordPress development site:

```text
https://dev.detarc.net
```

Use this environment for plugin upload, activation, shortcode/page testing, and REST/API development before moving changes to production.

## Build the development ZIP

From the plugin project root:

```bash
cd /Users/dbutler/Local/Development/net-attendance-wordpress-plugin
python3 -m unittest discover -s tests -v
find net-attendance-logger -name '*.php' -print0 | xargs -0 -n1 php -l
rm -f net-attendance-logger-mvp-dev.zip
zip -r net-attendance-logger-mvp-dev.zip net-attendance-logger -x '*/__pycache__/*' '*.DS_Store'
```

Expected ZIP path:

```text
/Users/dbutler/Local/Development/net-attendance-wordpress-plugin/net-attendance-logger-mvp-dev.zip
```

Package the plugin directory itself (`net-attendance-logger/`), not the containing repository.

## Install or update through wp-admin

1. Log in to the development WordPress admin area:

   ```text
   https://dev.detarc.net/wp-admin/
   ```

2. Go to Plugins → Add New Plugin → Upload Plugin.
3. Upload:

   ```text
   net-attendance-logger-mvp-dev.zip
   ```

4. If WordPress says the destination folder already exists, choose the option to replace/update the existing plugin.
5. Activate the plugin if it is not already active.
6. Confirm the admin menu contains `Net Attendance`.

## Verify after installation

In wp-admin, verify these pages load:

```text
/wp-admin/admin.php?page=net-attendance-logger
/wp-admin/admin.php?page=net-attendance-logger-take-attendance
/wp-admin/admin.php?page=net-attendance-logger-import
/wp-admin/admin.php?page=net-attendance-logger-reports
```

The reports page can also be tested with filters:

```text
/wp-admin/admin.php?page=net-attendance-logger-reports&period=week&event_name=Weekly+Net
```

## Import sample attendance data

Use the admin import page:

```text
/wp-admin/admin.php?page=net-attendance-logger-import
```

The local reusable sample payload is:

```text
/Users/dbutler/Local/Development/net-attendance-wordpress-plugin/docs/sample-data/weekly-net-june-2026.json
```

Recommended workflow:

1. Upload or paste the JSON.
2. Click `Validate Only` first.
3. Confirm the expected event/participant/record counts.
4. Run the actual import.
5. Check the Events and Reports admin pages.

## Access-control dependency

Frontend reports are intended for DETARC members.

REST imports use a separate custom capability so a non-administrator API user can push saved Net Logger sessions without receiving full site administration privileges:

```text
import_net_attendance
```

Preferred REST API setup:

1. Go to `Net Attendance → Settings`.
2. In `API Import Permissions`, check the role that should be allowed to push data, such as `DETARC Member` on dev.detarc.net.
3. Save settings.
4. Create the WordPress Application Password for a user in that role.

Administrators are always allowed. The plugin grants the import capability to administrators on activation and stores selected import roles in `net_attendance_logger_import_role_slugs`. This avoids hard-coding DETARC-specific role names into the REST API, while still letting each WordPress instance choose its own API role.

Frontend report access is separate. The plugin allows report access for users who have one of these:

- WordPress `manage_options` capability;
- custom capability `view_net_attendance_reports`;
- recognized DETARC Member role slug.

Preferred setup with Members by MemberPress:

1. Ensure the DETARC Member role exists.
2. Grant that role this custom capability:

   ```text
   view_net_attendance_reports
   ```

The plugin also recognizes these role slugs by default:

```text
detarc_member
detarc-member
```

If the actual site role slug is different, add a filter in a site-specific snippets plugin or customization plugin rather than editing plugin core:

```php
add_filter('net_attendance_logger_report_role_slugs', function (array $roles): array {
    $roles[] = 'your_actual_detarc_member_role_slug';
    return $roles;
});
```

## Notes for credentials

Do not store wp-admin passwords, application passwords, SSH credentials, or REST nonces in this plugin's docs, repository, commits, or issue text.
