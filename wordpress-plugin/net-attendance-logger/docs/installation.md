# Net & Meeting Attendance Installation

The **Net & Meeting Attendance** plugin is the optional WordPress side of Net Logger. Install it when you want saved Net Logger sessions to be sent into WordPress for attendance storage, reports, charts, and member-facing pages.

The standalone Net Logger app does not require this plugin for normal net-control operation.

## Development environment

Current DETARC WordPress development site:

```text
https://dev.detarc.net
```

Use this environment for plugin upload, activation, shortcode/page testing, and REST/API development before moving changes to production.

## Installation flow

1. Build or locate the plugin ZIP.
2. Upload and activate the ZIP in WordPress.
3. Confirm the **Net Attendance** admin menu appears.
4. Configure API import permissions under **Net Attendance → Settings**.
5. Create a WordPress Application Password for the Net Logger API user.
6. Configure Net Logger's WordPress export settings from **Saved Nets / Metrics → Send to WordPress**.
7. Create a WordPress reports page with `[net_attendance_reports]` if frontend reports are desired.
8. Test the full Net Logger → WordPress import flow.

## Build the plugin ZIP

From this repository root:

```bash
cd /Users/dbutler/Local/Development/net-logger
uv run --extra dev pytest -q
find wordpress-plugin/net-attendance-logger -name '*.php' -print0 | xargs -0 -n1 php -l
cd wordpress-plugin
rm -f net-attendance-logger.zip
zip -r net-attendance-logger.zip net-attendance-logger -x '*/__pycache__/*' '*.pyc' '.pytest_cache/*' '*.DS_Store'
```

Expected ZIP path:

```text
/Users/dbutler/Local/Development/net-logger/wordpress-plugin/net-attendance-logger.zip
```

Package the plugin directory itself (`net-attendance-logger/`), not the whole Net Logger repository.

## Install or update through wp-admin

1. Log in to the development WordPress admin area:

   ```text
   https://dev.detarc.net/wp-admin/
   ```

2. Go to **Plugins → Add New Plugin → Upload Plugin**.
3. Upload:

   ```text
   net-attendance-logger.zip
   ```

4. If WordPress says the destination folder already exists, choose the option to replace/update the existing plugin.
5. Activate the plugin if it is not already active.
6. Confirm the admin menu contains **Net Attendance**.

## Verify after installation

In wp-admin, verify these pages load:

```text
/wp-admin/admin.php?page=net-attendance-logger
/wp-admin/admin.php?page=net-attendance-logger-take-attendance
/wp-admin/admin.php?page=net-attendance-logger-import
/wp-admin/admin.php?page=net-attendance-logger-reports
/wp-admin/admin.php?page=net-attendance-logger-settings
```

The reports page can also be tested with filters:

```text
/wp-admin/admin.php?page=net-attendance-logger-reports&period=week&event_name=Weekly+Net
```

## Configure REST API import access

REST imports use a separate custom capability so a non-administrator API user can push saved Net Logger sessions without receiving full site administration privileges:

```text
import_net_attendance
```

Preferred REST API setup:

1. Go to **Net Attendance → Settings**.
2. In **API Import Permissions**, check the role that should be allowed to push data, such as **DETARC Member** on dev.detarc.net.
3. Save settings.
4. Create the WordPress Application Password for a user in that role.
5. Use that username and Application Password in Net Logger's WordPress export configuration.

Administrators are always allowed. The plugin grants the import capability to administrators on activation and stores selected import roles in `net_attendance_logger_import_role_slugs`. This avoids hard-coding DETARC-specific role names into the REST API, while still letting each WordPress instance choose its own API role.

## Create the WordPress Application Password

For the WordPress user that Net Logger will use:

1. Go to **Users** in wp-admin.
2. Open the user profile.
3. Scroll to **Application Passwords**.
4. Enter a label such as `Net Logger`.
5. Click **Add New Application Password**.
6. Copy the generated password immediately.

Do not use the user's normal login password. WordPress Application Passwords are purpose-specific credentials and can be revoked later without changing the user's normal password.

## Configure Net Logger export

In Net Logger:

1. Open **Saved Nets / Metrics**.
2. Click **Send to WordPress** on a saved net.
3. If WordPress export is not configured, Net Logger opens a setup form.
4. Enter the endpoint, WordPress username, and Application Password.
5. Click **Test Only** first.
6. If the test succeeds, click **Test and Save**.

Endpoint format:

```text
https://example.org/wp-json/net-attendance/v1/net-logger/sessions
```

DETARC development endpoint:

```text
https://dev.detarc.net/wp-json/net-attendance/v1/net-logger/sessions
```

Net Logger saves these settings in its local `config.ini` file under `[wordpress]`.

## Configure frontend report access

Frontend report access is separate from REST import access. The plugin allows report access for users who have one of these:

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

## Create the frontend reports page

1. Create a WordPress page named something like `Net Attendance Reports`.
2. Add a Shortcode block or Paragraph block containing:

   ```text
   [net_attendance_reports]
   ```

3. Publish the page.
4. Add the page to the site menu through **Appearance → Menus** or **Appearance → Editor → Navigation**, depending on the active theme.
5. Restrict the page to DETARC members if the site is using page-level restrictions.

The shortcode itself performs an access check, so report output is still protected even if the page is accidentally visible in a public menu.

## Import sample attendance data manually

Use the admin import page:

```text
/wp-admin/admin.php?page=net-attendance-logger-import
```

Recommended workflow:

1. Paste or upload JSON in the supported import format.
2. Click **Validate Only** first.
3. Confirm the expected event/participant/record counts.
4. Run the actual import.
5. Check the Events and Reports admin pages.

The native Net Logger endpoint is usually easier than manual JSON imports for real saved nets.

## End-to-end verification checklist

1. Run a short test net in Net Logger.
2. Stop the net so it becomes a saved net.
3. Open **Saved Nets / Metrics**.
4. Click **Send to WordPress**.
5. Confirm the request succeeds.
6. In WordPress, open **Net Attendance → Events** and confirm the event appears.
7. Open **Net Attendance → Reports & Charts** and confirm the event is counted.
8. Open the frontend reports page and confirm an authorized member/admin can view it.
9. Confirm a logged-out browser does not see protected report data.

## Notes for credentials

Do not store wp-admin passwords, application passwords, SSH credentials, REST nonces, or other secrets in this plugin's docs, repository, commits, screenshots, issue text, or support messages.
