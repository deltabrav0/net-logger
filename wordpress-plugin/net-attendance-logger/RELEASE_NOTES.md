# Net & Meeting Attendance Plugin Release Notes

These notes are specific to the WordPress plugin packaged from `wordpress-plugin/net-attendance-logger`.

## v0.1.6

- Added Participation Awards as a scalable award-definition layer using `net_attendance_logger_participation_awards`.
- Added lifetime check-in awards: Bronze, Silver, Gold, and Century Club.
- Added Rookie recognition for first recorded check-ins.
- Added Net Control service recognition from `role = net_control` records or matching event net-control callsigns.
- Added Current Streak recognition for consecutive ISO-week participation.
- Added visible Plugin Documentation links on the plugin Settings page and updated bundled docs/readme guidance.

## v0.1.5

- Added a `sections` shortcode attribute so the same reports renderer can power separate report pages without duplicating code.
- Supported section values are `snapshot, leaderboard, new_participants, milestones, totals, trends`.
- Example recognition page: `[net_attendance_reports sections="snapshot,leaderboard"]`.
- Example trends page: `[net_attendance_reports sections="trends"]`.
- Example welcome/milestones page: `[net_attendance_reports sections="new_participants,milestones"]`.
- Updated plugin documentation and WordPress readme examples for separate report pages.

## v0.1.4

- Added participation reporting for DETARC member engagement: Participation Snapshot, Top Participants, New Participants, and Participation Milestones.
- Added report shortcode controls for hiding leaderboard, new-participant, and milestone sections.
- Documented Members plugin by MemberPress access expectations for frontend reports.
