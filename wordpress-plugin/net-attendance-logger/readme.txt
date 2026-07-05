=== Net & Meeting Attendance ===
Contributors: deltabrav0
Tags: attendance, amateur radio, nets, meetings, reports
Requires at least: 6.0
Tested up to: 6.6
Requires PHP: 8.0
Stable tag: 0.1.1
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Store, import, report, and display attendance for radio nets and meetings.

== Description ==

Net & Meeting Attendance is a WordPress plugin for managing attendance events such as amateur-radio nets, in-person meetings, training sessions, and emergency communications exercises.

The MVP is designed around a net-agnostic attendance model and future integration with Net Logger.

Current MVP capabilities:

* custom tables for events, participants, and attendance records;
* wp-admin JSON import with validation/dry-run support;
* single-event and batch JSON payload support;
* wp-admin event detail and reports pages;
* attendance event deletion from wp-admin;
* rapid summary entry for paper logs or historical nets with only date/time, net name, frequency, and head count;
* simple manual attendance-taking page for use when Net Logger is unavailable;
* frontend report embedding with the [net_attendance_reports] shortcode.

Current development environment:

https://dev.detarc.net

== Installation ==

Build and upload the plugin ZIP:

1. From the Net Logger repository root, run the tests and PHP lint.
2. Build wordpress-plugin/net-attendance-logger.zip with the net-attendance-logger directory at the ZIP root.
3. In WordPress, go to Plugins -> Add New Plugin -> Upload Plugin.
4. Upload net-attendance-logger.zip.
5. If replacing an existing installation, choose the WordPress option to replace/update the existing plugin.
6. Activate the plugin.
7. Confirm the Net Attendance admin menu appears.
8. Go to Net Attendance -> Settings -> API Import Permissions and choose the role allowed to receive Net Logger imports.

Detailed installation and configuration instructions are in docs/installation.md.

== Usage ==

Admin pages:

* Net Attendance -> Events
* Net Attendance -> Take Attendance
* Net Attendance -> Rapid Entry
* Net Attendance -> Reports & Charts
* Net Attendance -> Import JSON

The Rapid Entry screen records summary-only events for historical paper logs, meeting rosters, or off-system nets where only the date/time, net/event name, frequency, and total head count are known. These summary-only events do not create participant records, but reports include their head count.

The Take Attendance screen is a deliberately simple manual attendance-entry workflow. Use the standalone Net Logger tool for normal net-control work; use the WordPress screen when Net Logger is unavailable. It can start an event, automatically check in net control, provide a Quick Check-in row for keyboard-first callsign entry, auto-uppercase callsigns, edit traffic/notes, remove mistaken check-ins, close the event, and require Reopen Event for Editing before changing a closed event. Event details show traffic text through a Yes - view expander.

Events can be deleted from the wp-admin Events list or event detail screen. Deleting an event deletes the attached attendance records but leaves participant/station records available for reuse.

Reports can be embedded in a WordPress page with:

[net_attendance_reports]

Optional shortcode examples:

[net_attendance_reports period="week"]
[net_attendance_reports period="month" event_name="Weekly Net"]
[net_attendance_reports period="year" show_filters="no"]

Supported period values:

* day
* week
* month
* year

Detailed usage and shortcode instructions are in docs/usage.md and docs/reports.md.

== Access Control ==

REST API imports use the custom capability import_net_attendance. Administrators are always allowed, and site admins can grant API import access to any existing role from Net Attendance → Settings → API Import Permissions. DETARC sites using the Members by MemberPress detarc_member role receive import_net_attendance, take_net_attendance, and view_net_attendance_events automatically, so DETARC Member users can access Net Attendance → Events, Take Attendance, Rapid Entry, and Import JSON from the wp-admin left menu without becoming administrators.

Frontend report visibility depends on the DETARC Member role managed by Members by MemberPress, or the custom capability view_net_attendance_reports.

Administrators with manage_options can view reports. For member report access, the preferred setup is to grant the DETARC Member role the custom capability:

view_net_attendance_reports

The plugin also recognizes detarc_member and detarc-member role slugs by default. See docs/reports.md for role-slug filter details.

== Privacy ==

Public attendance output is callsign-oriented by default. Participant names for no-callsign meeting attendees are not intended to be public unless a future admin setting explicitly enables them.

== Current Limitations ==

The MVP imports, reports, and provides a simple manual attendance-taking screen. It does not try to replace the standalone Net Logger interface.
