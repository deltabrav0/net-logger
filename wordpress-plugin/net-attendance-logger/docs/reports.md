# Net Attendance Reports, Charts, and Member Access

## Admin reports page

![Net Attendance Reports & Charts page](images/reports-charts.png)

Administrators can view the internal reports page at:

```text
/wp-admin/admin.php?page=net-attendance-logger-reports
```

The page supports:

- Participation Snapshot cards for event count, total check-ins, distinct participants, and average attendance;
- Top Participants recognition using participant-level check-in counts;
- New Participants so recent first-time check-ins can be welcomed;
- Participation Awards for Bronze, Silver, Gold, Century Club, Rookie, Net Control service, and Current Streak recognition;
- attendance totals by net name;
- attendance-over-time charts;
- grouping by day, week, month, or year;
- filtering by imported net/event name.

The charts use each record's `checked_in_at` timestamp as the primary bucket date, falling back to the event `started_at` when an imported record has no check-in timestamp.

## Embedding reports in a WordPress page

Create a normal WordPress page, for example `Net Attendance Reports`, and place this shortcode in the page content:

```text
[net_attendance_reports]
```

Optional shortcode attributes:

```text
[net_attendance_reports period="week"]
[net_attendance_reports period="month" event_name="Weekly Net"]
[net_attendance_reports period="year" show_filters="no"]
[net_attendance_reports show_leaderboard="no"]
[net_attendance_reports show_new_participants="no"]
[net_attendance_reports show_milestones="no"]
[net_attendance_reports sections="snapshot,leaderboard"]
[net_attendance_reports sections="trends"]
[net_attendance_reports sections="new_participants,milestones"]
```

Participation sections default to visible. Use these attributes when a page should emphasize trends over public recognition:

- `sections="snapshot,leaderboard"` displays only the selected report sections. Supported section values are `snapshot, leaderboard, new_participants, milestones, totals, trends`. Use `sections="all"` or omit the attribute for the full report.
- `sections="trends"` is useful for a dedicated attendance trend page.
- `sections="new_participants,milestones"` is useful for a participation-recognition page that avoids the full leaderboard.
- `show_leaderboard="yes|no"` controls the Top Participants section when `leaderboard` is included in `sections`.
- `show_new_participants="yes|no"` controls the New Participants section.
- `show_milestones="yes|no"` controls the Participation Awards section.

Supported `period` values:

- `day`
- `week`
- `month`
- `year`

When filters are shown, the frontend form submits `period` and `event_name` query parameters to the same page.


## Participation Awards

The awards section is intentionally lightweight gamification. It recognizes participation and service without adding a separate points table. Award definitions are centralized in code and can be customized by developers with the `net_attendance_logger_participation_awards` WordPress filter.

Current awards:

- Bronze — 10 lifetime check-ins.
- Silver — 25 lifetime check-ins.
- Gold — 50 lifetime check-ins.
- Century Club — 100 lifetime check-ins.
- Rookie — first recorded check-in, useful for welcoming new participants.
- Net Control — service as net control, counted when the attendance role is `net_control` or the participant callsign matches the event net-control callsign.
- Current Streak — consecutive ISO weeks with at least one check-in.

Current Streak is calculated across the selected report scope. If `event_name` is supplied, the streak is net-specific; otherwise it is based on participation in any imported net/event during each ISO week.


## Standalone participation-awards page

Create a page for awards only by adding this shortcode:

```text
[net_attendance_awards]
```

Useful variations:

```text
[net_attendance_awards event_name="Weekly Net"]
[net_attendance_awards show_filters="no"]
[net_attendance_awards limit="20"]
```

Use this when you want a participation-awards page without the snapshot, leaderboard, new-participants, totals, or trend charts.

## Linking from a WordPress menu

Recommended approach:

1. Create a WordPress page containing `[net_attendance_reports]`.
2. Publish the page.
3. Go to Appearance → Menus, or Appearance → Editor → Navigation depending on the active theme.
4. Add the page to the appropriate site menu.
5. Restrict the page to DETARC members using the Members plugin by MemberPress.

The shortcode also enforces its own access check, so the reports are protected even if the page is accidentally linked from a public menu.

## DETARC Member access dependency

This plugin expects the Members plugin by MemberPress to manage the DETARC Member role.

Report access is allowed for users who meet at least one of these conditions:

- the user has WordPress `manage_options` capability, for site administrators;
- the user has the custom capability `view_net_attendance_reports`;
- the user has a DETARC Member role slug recognized by the plugin.

By default, the plugin recognizes these role slugs:

```text
detarc_member
detarc-member
```

If the actual Members role slug differs, add a small site-specific filter in a snippets plugin or theme/plugin customization:

```php
add_filter('net_attendance_logger_report_role_slugs', function (array $roles): array {
    $roles[] = 'your_actual_detarc_member_role_slug';
    return $roles;
});
```

Alternatively, use Members by MemberPress to grant the DETARC Member role this custom capability:

```text
view_net_attendance_reports
```

That capability is checked directly and avoids depending on a specific role slug.

## Unauthorized viewers

- Logged-out visitors see a prompt to log in with a DETARC Member account.
- Logged-in users without permission see a not-authorized message.
- Direct wp-admin reports access is denied unless the user passes the same report access check.
