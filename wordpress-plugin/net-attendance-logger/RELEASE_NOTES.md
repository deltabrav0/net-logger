# Net & Meeting Attendance Plugin Release Notes

These notes are specific to the WordPress plugin packaged from `wordpress-plugin/net-attendance-logger`.

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
