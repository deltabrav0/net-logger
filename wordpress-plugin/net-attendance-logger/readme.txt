=== Net & Meeting Attendance ===
Contributors: deltabrav0
Tags: attendance, amateur radio, nets, meetings, reports
Requires at least: 6.0
Tested up to: 6.6
Requires PHP: 8.0
Stable tag: 0.1.6
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
* attendance event metadata editing and event deletion from wp-admin;
* rapid summary entry for paper logs or historical nets with only date/time, net name, frequency, and head count;
* simple manual attendance-taking page for use when Net Logger is unavailable;
* frontend report embedding with the [net_attendance_reports] shortcode, including participation snapshot cards, top participants, new participants, Participation Awards (Bronze, Silver, Gold, Century Club, Rookie, Net Control, and Current Streak), and attendance trend charts.

Current development environment:

https://dev.detarc.net

== Installation ==

Build and upload the plugin ZIP:

Prerequisite: install and activate the Members plugin by MemberPress so the Net Control and DETARC Member roles can be created and assigned.

1. From the Net Logger repository root, run the tests and PHP lint.
2. Build wordpress-plugin/net-attendance-logger.zip with the net-attendance-logger directory at the ZIP root.
3. In WordPress, go to Plugins -> Add New Plugin -> Upload Plugin.
4. Upload net-attendance-logger.zip.
5. If replacing an existing installation, choose the WordPress option to replace/update the existing plugin.
6. Activate the plugin.
7. Confirm the Net Attendance admin menu appears.
8. Ensure Net Logger API users have the Net Control role. DETARC Member users receive view-only Events and Reports access.

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

Event detail pages include an Edit Event Details form for correcting event metadata such as net/event name, start time, frequency, net control, and notes. This does not reopen the event or alter attendance records.

Events can be deleted from the wp-admin Events list or event detail screen. Deleting an event deletes the attached attendance records but leaves participant/station records available for reuse.

Reports can be embedded in a WordPress page with:

[net_attendance_reports]

Optional shortcode examples:

[net_attendance_reports period="week"]
[net_attendance_reports period="month" event_name="Weekly Net"]
[net_attendance_reports period="year" show_filters="no"]
[net_attendance_reports show_leaderboard="no"]
[net_attendance_reports show_new_participants="no"]
[net_attendance_reports show_milestones="no"]
[net_attendance_reports sections="snapshot,leaderboard"]
[net_attendance_reports sections="trends"]
[net_attendance_reports sections="new_participants,milestones"]

Supported period values:

* day
* week
* month
* year

Supported section values for split report pages are: snapshot, leaderboard, new_participants, milestones, totals, trends. For example, use sections="snapshot,leaderboard" for a recognition page, sections="trends" for a chart-only trend page, or sections="new_participants,milestones" for a welcome-and-milestones page.

Plugin documentation is bundled with the ZIP: docs/installation.md, docs/usage.md, docs/reports.md, docs/api.md, and RELEASE_NOTES.md. Detailed usage and shortcode instructions are in docs/usage.md and docs/reports.md.

== Access Control ==

REST API imports use the custom capability import_net_attendance. Administrators are always allowed. The Net Attendance -> Settings -> API Import Permissions screen documents the import capability, but DETARC sites using the Members plugin by MemberPress should use the Net Control role (slug net_control) for operators who may take attendance, use Rapid Entry, import JSON, and push Net Logger sessions through the REST API. Net Control users receive import_net_attendance, take_net_attendance, view_net_attendance_events, and view_net_attendance_reports automatically.

DETARC Member users receive only view_net_attendance_events and view_net_attendance_reports automatically, so DETARC Members can view Net Attendance -> Events and Net Attendance -> Reports & Charts without being able to take attendance, use Rapid Entry, import JSON, or push Net Logger sessions through the API.

Frontend report visibility depends on the DETARC Member role managed by Members by MemberPress, or the custom capability view_net_attendance_reports.

Administrators with manage_options can view reports. For member report access, the preferred setup is to grant the DETARC Member role the custom capability:

view_net_attendance_reports

The plugin also recognizes detarc_member and detarc-member role slugs by default. See docs/reports.md for role-slug filter details.

== Privacy ==

Public attendance output is callsign-oriented by default. Participant names for no-callsign meeting attendees are not intended to be public unless a future admin setting explicitly enables them.

== Current Limitations ==

The MVP imports, reports, and provides a simple manual attendance-taking screen. It does not try to replace the standalone Net Logger interface.
