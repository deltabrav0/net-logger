<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class Admin_Controller
{
    public const MENU_SLUG = 'net-attendance-logger';
    public const IMPORT_SLUG = 'net-attendance-logger-import';
    public const REPORTS_SLUG = 'net-attendance-logger-reports';
    public const RAPID_ENTRY_SLUG = 'net-attendance-logger-rapid-entry';
    public const TAKE_SLUG = 'net-attendance-logger-take-attendance';
    public const SETTINGS_SLUG = 'net-attendance-logger-settings';

    public static function register(): void
    {
        if (!is_admin()) {
            return;
        }

        add_action('admin_menu', [self::class, 'register_menu']);
        // Keep the Members by MemberPress DETARC Member role (detarc_member) able to use operator screens.
        // Custom capability: take_net_attendance.
        add_action('admin_init', [Capabilities::class, 'grant_detarc_member_defaults']);
        add_action('admin_post_nal_import_json', [self::class, 'handle_import_json']);
        add_action('admin_post_nal_start_event', [self::class, 'handle_start_event']);
        add_action('admin_post_nal_rapid_entry', [self::class, 'handle_rapid_entry']);
        add_action('admin_post_nal_add_checkin', [self::class, 'handle_add_checkin']);
        add_action('admin_post_nal_update_checkin', [self::class, 'handle_update_checkin']);
        add_action('admin_post_nal_delete_checkin', [self::class, 'handle_delete_checkin']);
        add_action('admin_post_nal_close_event', [self::class, 'handle_close_event']);
        add_action('admin_post_nal_reopen_event', [self::class, 'handle_reopen_event']);
        add_action('admin_post_nal_delete_event', [self::class, 'handle_delete_event']);
        add_action('admin_post_nal_save_settings', [self::class, 'handle_save_settings']);
    }

    public static function register_menu(): void
    {
        add_menu_page(
            __('Net Attendance', 'net-attendance-logger'),
            __('Net Attendance', 'net-attendance-logger'),
            Capabilities::TAKE_ATTENDANCE,
            self::MENU_SLUG,
            [self::class, 'render_take_attendance_page'],
            'dashicons-groups',
            26
        );

        add_submenu_page(
            self::MENU_SLUG,
            __('Events', 'net-attendance-logger'),
            __('Events', 'net-attendance-logger'),
            'manage_options',
            self::MENU_SLUG,
            [self::class, 'render_events_page']
        );

        add_submenu_page(
            self::MENU_SLUG,
            __('Reports & Charts', 'net-attendance-logger'),
            __('Reports & Charts', 'net-attendance-logger'),
            'manage_options',
            self::REPORTS_SLUG,
            [self::class, 'render_reports_page']
        );

        add_submenu_page(
            self::MENU_SLUG,
            __('Take Attendance', 'net-attendance-logger'),
            __('Take Attendance', 'net-attendance-logger'),
            Capabilities::TAKE_ATTENDANCE,
            self::TAKE_SLUG,
            [self::class, 'render_take_attendance_page']
        );

        add_submenu_page(
            self::MENU_SLUG,
            __('Rapid Entry', 'net-attendance-logger'),
            __('Rapid Entry', 'net-attendance-logger'),
            Capabilities::TAKE_ATTENDANCE,
            self::RAPID_ENTRY_SLUG,
            [self::class, 'render_rapid_entry_page']
        );

        add_submenu_page(
            self::MENU_SLUG,
            __('Import JSON', 'net-attendance-logger'),
            __('Import JSON', 'net-attendance-logger'),
            Capabilities::IMPORT,
            self::IMPORT_SLUG,
            [self::class, 'render_import_page']
        );

        add_submenu_page(
            self::MENU_SLUG,
            __('Settings', 'net-attendance-logger'),
            __('Settings', 'net-attendance-logger'),
            'manage_options',
            self::SETTINGS_SLUG,
            [self::class, 'render_settings_page']
        );
    }

    public static function render_events_page(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('You do not have permission to access this page.', 'net-attendance-logger'));
        }

        $repository = new Repository();
        $event_id = isset($_GET['event_id']) ? absint($_GET['event_id']) : 0;

        echo '<div class="wrap">';
        echo '<h1>' . esc_html__('Net Attendance Events', 'net-attendance-logger') . '</h1>';

        self::render_admin_notice();

        if ($event_id > 0) {
            self::render_event_detail($repository, $event_id);
        } else {
            self::render_event_list($repository);
        }

        echo '</div>';
    }

    public static function render_import_page(): void
    {
        if (!Capabilities::can_import()) {
            wp_die(esc_html__('You do not have permission to access this page.', 'net-attendance-logger'));
        }

        $sample = wp_json_encode([
            'source' => 'manual',
            'external_id' => 'sample-2026-07-02',
            'event' => [
                'name' => 'Sample Training Net',
                'event_type' => 'Repeater Net',
                'started_at' => gmdate('Y-m-d H:i:s'),
                'frequency' => '146.520 MHz',
                'net_control' => 'N0CALL',
            ],
            'attendance' => [
                [
                    'sequence' => 1,
                    'checked_in_at' => gmdate('Y-m-d H:i:s'),
                    'participant' => [
                        'callsign' => 'N0CALL',
                        'name' => 'Net Control',
                    ],
                    'role' => 'net_control',
                    'traffic' => false,
                ],
            ],
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);

        echo '<div class="wrap">';
        echo '<h1>' . esc_html__('Import Net Attendance JSON', 'net-attendance-logger') . '</h1>';
        self::render_admin_notice();
        echo '<p>' . esc_html__('Upload a JSON file or paste a generic attendance payload, a batch payload with an events array, or supported Net Logger-shaped JSON. Use Validate Only for a dry run before writing records.', 'net-attendance-logger') . '</p>';
        echo '<form method="post" enctype="multipart/form-data" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('nal_import_json', 'nal_import_json_nonce');
        echo '<input type="hidden" name="action" value="nal_import_json" />';
        echo '<table class="form-table" role="presentation"><tbody>';
        echo '<tr><th scope="row"><label for="nal_import_file">' . esc_html__('JSON file', 'net-attendance-logger') . '</label></th><td><input type="file" id="nal_import_file" name="payload_file" accept="application/json,.json" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_import_payload">' . esc_html__('Or paste JSON', 'net-attendance-logger') . '</label></th><td><textarea id="nal_import_payload" name="payload" rows="24" class="large-text code" spellcheck="false" placeholder="' . esc_attr($sample ?: '') . '"></textarea></td></tr>';
        echo '</tbody></table>';
        echo '<p>';
        submit_button(__('Validate Only', 'net-attendance-logger'), 'secondary', 'validate_only', false);
        echo ' ';
        submit_button(__('Import Attendance', 'net-attendance-logger'), 'primary', 'import_attendance', false);
        echo '</p>';
        echo '</form>';
        echo '<h2>' . esc_html__('Example payload', 'net-attendance-logger') . '</h2>';
        echo '<pre style="max-width: 960px; overflow: auto; background: #fff; border: 1px solid #ccd0d4; padding: 12px;">' . esc_html($sample ?: '') . '</pre>';
        echo '</div>';
    }

    public static function render_rapid_entry_page(): void
    {
        if (!Capabilities::can_take_attendance()) {
            wp_die(esc_html__('You do not have permission to add rapid summary entries.', 'net-attendance-logger'));
        }

        echo '<div class="wrap">';
        echo '<h1>' . esc_html__('Rapid Summary Entry', 'net-attendance-logger') . '</h1>';
        self::render_admin_notice();
        echo '<p>' . esc_html__('Use this form for historical paper logs, meeting rosters, or off-system nets when you only know the date/time, net name, frequency, and total head count. Rapid entries are saved as summary-only events and do not create individual callsign records.', 'net-attendance-logger') . '</p>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="max-width: 760px; padding: 16px; background: #fff; border: 1px solid #ccd0d4;">';
        wp_nonce_field('nal_rapid_entry', 'nal_rapid_entry_nonce');
        echo '<input type="hidden" name="action" value="nal_rapid_entry" />';
        echo '<input type="hidden" name="summary_only" value="1" />';
        echo '<table class="form-table" role="presentation"><tbody>';
        echo '<tr><th scope="row"><label for="nal_rapid_started_at">' . esc_html__('Date/time', 'net-attendance-logger') . '</label></th><td><input required type="datetime-local" id="nal_rapid_started_at" name="started_at" class="regular-text" /><p class="description">' . esc_html__('Use the local date and time the net or meeting started.', 'net-attendance-logger') . '</p></td></tr>';
        echo '<tr><th scope="row"><label for="nal_rapid_event_name">' . esc_html__('Net/Event Name', 'net-attendance-logger') . '</label></th><td><input required id="nal_rapid_event_name" name="event_name" class="regular-text" value="Weekly Net" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_rapid_event_type">' . esc_html__('Event Type', 'net-attendance-logger') . '</label></th><td><input id="nal_rapid_event_type" name="event_type" class="regular-text" value="Repeater Net" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_rapid_frequency">' . esc_html__('Frequency', 'net-attendance-logger') . '</label></th><td><input id="nal_rapid_frequency" name="frequency" class="regular-text" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_rapid_head_count">' . esc_html__('Head Count', 'net-attendance-logger') . '</label></th><td><input required type="number" min="0" step="1" id="nal_rapid_head_count" name="head_count" class="small-text" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_rapid_notes">' . esc_html__('Notes', 'net-attendance-logger') . '</label></th><td><textarea id="nal_rapid_notes" name="notes" rows="4" class="large-text" placeholder="' . esc_attr__('Paper log, roster, or source notes', 'net-attendance-logger') . '"></textarea></td></tr>';
        echo '</tbody></table>';
        submit_button(__('Save Summary-only Event', 'net-attendance-logger'));
        echo '</form>';
        echo '</div>';
    }

    public static function render_settings_page(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('You do not have permission to manage Net Attendance settings.', 'net-attendance-logger'));
        }

        $roles = get_editable_roles();
        $selected = Capabilities::import_role_slugs();

        echo '<div class="wrap">';
        echo '<h1>' . esc_html__('Net Attendance Settings', 'net-attendance-logger') . '</h1>';
        self::render_admin_notice();
        echo '<h2>' . esc_html__('API Import Permissions', 'net-attendance-logger') . '</h2>';
        echo '<p>' . esc_html__('WordPress Application Passwords authenticate as a normal user. Grant the custom import capability to whichever role should be allowed to send Net Logger sessions to the REST API. Administrators are always allowed.', 'net-attendance-logger') . '</p>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('nal_save_settings', 'nal_save_settings_nonce');
        echo '<input type="hidden" name="action" value="nal_save_settings" />';
        echo '<table class="widefat striped" style="max-width: 760px;"><thead><tr><th>' . esc_html__('Role', 'net-attendance-logger') . '</th><th>' . esc_html__('Allow REST imports', 'net-attendance-logger') . '</th></tr></thead><tbody>';
        foreach ($roles as $slug => $role) {
            $slug = sanitize_key($slug);
            $role_name = isset($role['name']) ? translate_user_role((string) $role['name']) : $slug;
            $is_admin = $slug === 'administrator';
            $has_capability = !empty($role['capabilities'][Capabilities::IMPORT]);
            $checked = $is_admin || $has_capability || in_array($slug, $selected, true);
            echo '<tr><td><strong>' . esc_html($role_name) . '</strong><br><code>' . esc_html($slug) . '</code></td><td>';
            echo '<label><input type="checkbox" name="import_roles[]" value="' . esc_attr($slug) . '"' . checked($checked, true, false) . ($is_admin ? ' disabled' : '') . ' /> ' . esc_html($is_admin ? __('Always allowed', 'net-attendance-logger') : __('Can push Net Logger sessions through the REST API', 'net-attendance-logger')) . '</label>';
            echo '</td></tr>';
        }
        echo '</tbody></table>';
        submit_button(__('Save API Permissions', 'net-attendance-logger'));
        echo '</form>';
        echo '<p><strong>' . esc_html__('Required capability:', 'net-attendance-logger') . '</strong> <code>' . esc_html(Capabilities::IMPORT) . '</code></p>';
        echo '</div>';
    }

    public static function render_take_attendance_page(): void
    {
        if (!Capabilities::can_take_attendance()) {
            wp_die(esc_html__('You do not have permission to take attendance.', 'net-attendance-logger'));
        }

        $repository = new Repository();
        $event_id = isset($_GET['event_id']) ? absint($_GET['event_id']) : 0;
        $event = $event_id > 0 ? $repository->get_event($event_id) : null;
        $attendance = $event ? $repository->get_event_attendance($event_id) : [];

        echo '<div class="wrap">';
        echo '<h1>' . esc_html__('Take Attendance', 'net-attendance-logger') . '</h1>';
        self::render_admin_notice();
        self::render_attendance_scripts();
        echo '<div class="notice notice-warning inline"><p>' . esc_html__('Use the standalone Net Logger tool for normal net-control work. This WordPress screen provides simple manual attendance entry when Net Logger is unavailable.', 'net-attendance-logger') . '</p></div>';

        if (!$event) {
            self::render_start_event_form();
            echo '</div>';
            return;
        }

        echo '<p><a href="' . esc_url(admin_url('admin.php?page=' . self::TAKE_SLUG)) . '">&larr; ' . esc_html__('Start or select another event', 'net-attendance-logger') . '</a></p>';
        echo '<h2>' . esc_html($event['name'] ?? __('Untitled Event', 'net-attendance-logger')) . '</h2>';
        self::render_event_status_banner($event);

        if (self::event_is_open($event)) {
            self::render_quick_checkin_form($event_id);
            self::render_add_checkin_form($event_id);
            self::render_close_event_form($event_id);
        } else {
            echo '<div class="notice notice-info inline"><p>' . esc_html__('This event is closed. Check-ins cannot be edited unless you deliberately reopen the event.', 'net-attendance-logger') . '</p></div>';
            self::render_reopen_event_form($event_id);
        }

        self::render_manual_attendance_table($event_id, $attendance, self::event_is_open($event));
        echo '</div>';
    }

    public static function render_reports_page(): void
    {
        if (!self::current_user_can_view_reports()) {
            wp_die(esc_html__('You do not have permission to view net attendance reports.', 'net-attendance-logger'));
        }

        echo '<div class="wrap">';
        self::render_reports_content(true);
        echo '</div>';
    }

    public static function render_reports_shortcode($atts = []): string
    {
        $atts = is_array($atts) ? $atts : [];

        if (!self::current_user_can_view_reports()) {
            if (!is_user_logged_in()) {
                return '<p class="net-attendance-reports-login-required">' . esc_html__('Please log in with a DETARC Member account to view these reports.', 'net-attendance-logger') . '</p>';
            }
            return '<p class="net-attendance-reports-not-authorized">' . esc_html__('You do not have permission to view these net attendance reports.', 'net-attendance-logger') . '</p>';
        }

        $atts = shortcode_atts([
            'period' => '',
            'event_name' => '',
            'show_filters' => 'yes',
        ], $atts, 'net_attendance_reports');

        ob_start();
        echo '<div class="net-attendance-reports">';
        self::render_reports_content(false, $atts);
        echo '</div>';
        return (string) ob_get_clean();
    }

    private static function render_reports_content(bool $admin_context, array $atts = []): void
    {
        $repository = new Repository();
        $period_source = isset($_GET['period']) ? (string) wp_unslash($_GET['period']) : (string) ($atts['period'] ?? 'month');
        $event_name_source = isset($_GET['event_name']) ? (string) wp_unslash($_GET['event_name']) : (string) ($atts['event_name'] ?? '');
        $period = self::report_period($period_source ?: 'month');
        $event_name = sanitize_text_field($event_name_source);
        $show_filters = strtolower((string) ($atts['show_filters'] ?? 'yes')) !== 'no';
        $event_names = $repository->list_event_names();
        $series_rows = $repository->report_attendance_series([
            'period' => $period,
            'event_name' => $event_name,
        ]);
        $totals = $repository->report_attendance_totals_by_event_name([
            'event_name' => $event_name,
        ]);
        $series_by_event = self::group_series_by_event_name($series_rows);

        echo '<h1>' . esc_html__('Net Attendance Reports & Charts', 'net-attendance-logger') . '</h1>';
        if ($admin_context) {
            self::render_admin_notice();
        }
        echo '<p>' . esc_html__('View imported net attendance grouped by day, week, month, or year, with an optional net-name filter matching the Net Logger metrics view.', 'net-attendance-logger') . '</p>';
        if ($show_filters) {
            self::render_reports_filter_form($period, $event_name, $event_names, $admin_context);
        }
        self::render_reports_styles();

        echo '<h2>' . esc_html__('Attendance by Net', 'net-attendance-logger') . '</h2>';
        self::render_totals_chart($totals);

        echo '<h2>' . esc_html__('Attendance Over Time', 'net-attendance-logger') . '</h2>';
        self::render_series_charts($series_by_event, $period);
    }

    private static function current_user_can_view_reports(): bool
    {
        if (Capabilities::can_view_reports()) {
            return true;
        }

        $user = wp_get_current_user();
        if (!$user || empty($user->roles)) {
            return false;
        }

        $allowed_roles = apply_filters('net_attendance_logger_report_role_slugs', ['detarc_member', 'detarc-member']);
        return (bool) array_intersect(array_map('strval', $allowed_roles), array_map('strval', $user->roles));
    }

    private static function render_reports_filter_form(string $period, string $event_name, array $event_names, bool $admin_context): void
    {
        echo '<form method="get" style="margin: 16px 0 24px; padding: 12px; background: #fff; border: 1px solid #ccd0d4; display: flex; gap: 16px; align-items: end; flex-wrap: wrap;">';
        if ($admin_context) {
            echo '<input type="hidden" name="page" value="' . esc_attr(self::REPORTS_SLUG) . '" />';
        }
        echo '<label><span style="display:block; font-weight:600; margin-bottom:4px;">' . esc_html__('Group by', 'net-attendance-logger') . '</span>';
        echo '<select name="period">';
        foreach (['day' => __('Day', 'net-attendance-logger'), 'week' => __('Week', 'net-attendance-logger'), 'month' => __('Month', 'net-attendance-logger'), 'year' => __('Year', 'net-attendance-logger')] as $value => $label) {
            echo '<option value="' . esc_attr($value) . '"' . selected($period, $value, false) . '>' . esc_html($label) . '</option>';
        }
        echo '</select></label>';
        echo '<label><span style="display:block; font-weight:600; margin-bottom:4px;">' . esc_html__('Net name', 'net-attendance-logger') . '</span>';
        echo '<select name="event_name">';
        echo '<option value="">' . esc_html__('All nets', 'net-attendance-logger') . '</option>';
        foreach ($event_names as $name) {
            echo '<option value="' . esc_attr($name) . '"' . selected($event_name, $name, false) . '>' . esc_html($name) . '</option>';
        }
        echo '</select></label>';
        echo '<button type="submit" class="button button-primary nal-report-filter-submit">' . esc_html__('Apply Filters', 'net-attendance-logger') . '</button>';
        echo '</form>';
    }

    private static function render_totals_chart(array $totals): void
    {
        if (!$totals) {
            echo '<div class="notice notice-info inline"><p>' . esc_html__('No attendance data is available for the selected filters.', 'net-attendance-logger') . '</p></div>';
            return;
        }

        $max = max(1, ...array_map(static fn($row) => (int) ($row['attendance_count'] ?? 0), $totals));
        echo '<div class="nal-bar-chart">';
        foreach ($totals as $row) {
            $count = (int) ($row['attendance_count'] ?? 0);
            $width = max(3, (int) round(($count / $max) * 100));
            echo '<div class="nal-bar-row">';
            echo '<div class="nal-bar-label">' . esc_html($row['event_name'] ?? __('Untitled net', 'net-attendance-logger')) . '</div>';
            echo '<div class="nal-bar-track"><div class="nal-bar-fill" style="width:' . esc_attr((string) $width) . '%"></div></div>';
            echo '<div class="nal-bar-value">' . esc_html((string) $count) . '</div>';
            echo '</div>';
        }
        echo '</div>';
    }

    private static function render_series_charts(array $series_by_event, string $period): void
    {
        if (!$series_by_event) {
            echo '<div class="notice notice-info inline"><p>' . esc_html__('No attendance-over-time data is available for the selected filters.', 'net-attendance-logger') . '</p></div>';
            return;
        }

        foreach ($series_by_event as $event_name => $points) {
            $max = max(1, ...array_map(static fn($row) => (int) ($row['attendance_count'] ?? 0), $points));
            echo '<section class="nal-column-section">';
            echo '<h3>' . esc_html($event_name ?: __('Untitled net', 'net-attendance-logger')) . '</h3>';
            echo '<div class="nal-column-chart" role="img" aria-label="' . esc_attr(sprintf(__('Attendance grouped by %s for %s', 'net-attendance-logger'), $period, $event_name ?: __('Untitled net', 'net-attendance-logger'))) . '">';
            foreach ($points as $point) {
                $count = (int) ($point['attendance_count'] ?? 0);
                $height = max(10, (int) round(($count / $max) * 150));
                echo '<div class="nal-column-wrap">';
                echo '<div class="nal-column-value">' . esc_html((string) $count) . '</div>';
                echo '<div class="nal-column-bar" style="height:' . esc_attr((string) $height) . 'px" title="' . esc_attr(($point['bucket'] ?? '') . ': ' . $count) . '"></div>';
                echo '<div class="nal-column-label">' . esc_html($point['bucket'] ?? '') . '</div>';
                echo '</div>';
            }
            echo '</div>';
            echo '<table class="widefat striped nal-report-table"><thead><tr><th>' . esc_html__('Bucket', 'net-attendance-logger') . '</th><th>' . esc_html__('Attendance', 'net-attendance-logger') . '</th><th>' . esc_html__('Traffic', 'net-attendance-logger') . '</th></tr></thead><tbody>';
            foreach ($points as $point) {
                echo '<tr><td>' . esc_html($point['bucket'] ?? '') . '</td><td>' . esc_html((string) (int) ($point['attendance_count'] ?? 0)) . '</td><td>' . esc_html((string) (int) ($point['traffic_count'] ?? 0)) . '</td></tr>';
            }
            echo '</tbody></table>';
            echo '</section>';
        }
    }

    private static function group_series_by_event_name(array $rows): array
    {
        $grouped = [];
        foreach ($rows as $row) {
            $name = (string) ($row['event_name'] ?? __('Untitled net', 'net-attendance-logger'));
            if (!isset($grouped[$name])) {
                $grouped[$name] = [];
            }
            $grouped[$name][] = $row;
        }
        return $grouped;
    }

    private static function report_period(string $period): string
    {
        $period = strtolower(sanitize_key($period));
        return in_array($period, ['day', 'week', 'month', 'year'], true) ? $period : 'month';
    }

    private static function render_reports_styles(): void
    {
        echo '<style>
            .nal-bar-chart { max-width: 960px; margin: 12px 0 28px; }
            .nal-bar-row { display: grid; grid-template-columns: minmax(140px, 220px) 1fr 48px; gap: 10px; align-items: center; margin: 8px 0; }
            .nal-bar-label { font-weight: 600; overflow-wrap: anywhere; }
            .nal-bar-track { height: 18px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }
            .nal-bar-fill { height: 100%; background: #2271b1; border-radius: 999px; }
            .nal-bar-value { text-align: right; font-variant-numeric: tabular-nums; }
            .nal-column-section { max-width: 1100px; margin: 0 0 32px; padding: 16px; background: #fff; border: 1px solid #ccd0d4; }
            .nal-column-chart { min-height: 210px; display: flex; gap: 12px; align-items: flex-end; padding: 12px; overflow-x: auto; border: 1px solid #dcdcde; background: #f6f7f7; }
            .nal-column-wrap { min-width: 64px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 4px; }
            .nal-column-value { font-weight: 600; font-variant-numeric: tabular-nums; }
            .nal-column-bar { width: 34px; background: #2271b1; border-radius: 6px 6px 0 0; }
            .nal-column-label { max-width: 92px; font-size: 12px; text-align: center; white-space: nowrap; transform: rotate(-25deg); transform-origin: top center; margin-top: 8px; }
            .nal-report-table { margin-top: 18px; max-width: 640px; }
        </style>';
    }

    private static function render_attendance_scripts(): void
    {
        echo '<script>document.addEventListener("DOMContentLoaded",function(){var first=null;document.querySelectorAll(".nal-callsign-input").forEach(function(input){if(!first){first=input;}input.addEventListener("input",function(){var pos=input.selectionStart;input.value=input.value.toUpperCase().replace(/\s+/g,"");if(pos!==null){input.setSelectionRange(pos,pos);}});});if(first){first.focus();first.select();}});</script>';
    }

    private static function render_start_event_form(): void
    {
        echo '<h2>' . esc_html__('Start Attendance Event', 'net-attendance-logger') . '</h2>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="max-width: 760px; padding: 16px; background: #fff; border: 1px solid #ccd0d4;">';
        wp_nonce_field('nal_start_event', 'nal_start_event_nonce');
        echo '<input type="hidden" name="action" value="nal_start_event" />';
        echo '<table class="form-table" role="presentation"><tbody>';
        echo '<tr><th scope="row"><label for="nal_event_name">' . esc_html__('Net/Event Name', 'net-attendance-logger') . '</label></th><td><input required class="regular-text" id="nal_event_name" name="event_name" value="Weekly Net" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_event_type">' . esc_html__('Event Type', 'net-attendance-logger') . '</label></th><td><input class="regular-text" id="nal_event_type" name="event_type" value="Repeater Net" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_frequency">' . esc_html__('Frequency', 'net-attendance-logger') . '</label></th><td><input class="regular-text" id="nal_frequency" name="frequency" /></td></tr>';
        echo '<tr><th scope="row"><label for="nal_net_control">' . esc_html__('Net Control Callsign', 'net-attendance-logger') . '</label></th><td><input class="regular-text nal-callsign-input" id="nal_net_control" name="net_control" autocapitalize="characters" autocomplete="off" /><p class="description">' . esc_html__('If supplied, net control is checked in automatically.', 'net-attendance-logger') . '</p></td></tr>';
        echo '</tbody></table>';
        submit_button(__('Start Event', 'net-attendance-logger'));
        echo '</form>';
    }

    private static function render_quick_checkin_form(int $event_id): void
    {
        echo '<h2>' . esc_html__('Quick Check-in', 'net-attendance-logger') . '</h2>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '#nal-quick-checkin" id="nal-quick-checkin" style="max-width: 960px; padding: 14px 16px; background: #fff; border: 2px solid #2271b1; display:flex; gap: 10px; align-items:end; flex-wrap:wrap;">';
        wp_nonce_field('nal_add_checkin_' . $event_id, 'nal_add_checkin_nonce');
        echo '<input type="hidden" name="action" value="nal_add_checkin" />';
        echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
        echo '<label><span style="display:block;font-weight:600;">' . esc_html__('Callsign', 'net-attendance-logger') . '</span><input required id="nal_quick_callsign" name="callsign" class="regular-text nal-callsign-input" autocapitalize="characters" autocomplete="off" placeholder="' . esc_attr__('CALLSIGN', 'net-attendance-logger') . '" /></label>';
        submit_button(__('Check In', 'net-attendance-logger'), 'primary', 'submit', false);
        echo '<span class="description">' . esc_html__('Type a callsign and press Enter. The cursor returns here after each save.', 'net-attendance-logger') . '</span>';
        echo '</form>';
    }

    private static function render_add_checkin_form(int $event_id): void
    {
        echo '<details style="max-width:960px; margin:16px 0;"><summary style="cursor:pointer; font-weight:600;">' . esc_html__('Add details with check-in', 'net-attendance-logger') . '</summary>';
        echo '<h2>' . esc_html__('Detailed Check-in', 'net-attendance-logger') . '</h2>';
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="max-width: 960px; padding: 16px; background: #fff; border: 1px solid #ccd0d4;">';
        wp_nonce_field('nal_add_checkin_' . $event_id, 'nal_add_checkin_nonce');
        echo '<input type="hidden" name="action" value="nal_add_checkin" />';
        echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
        echo '<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items:end;">';
        echo '<label><span style="display:block;font-weight:600;">' . esc_html__('Callsign', 'net-attendance-logger') . '</span><input required name="callsign" class="regular-text nal-callsign-input" autocapitalize="characters" autocomplete="off" /></label>';
        echo '<label><span style="display:block;font-weight:600;">' . esc_html__('Name', 'net-attendance-logger') . '</span><input name="name" class="regular-text" /></label>';
        echo '<label><span style="display:block;font-weight:600;">' . esc_html__('City', 'net-attendance-logger') . '</span><input name="city" class="regular-text" /></label>';
        echo '<label><span style="display:block;font-weight:600;">' . esc_html__('State', 'net-attendance-logger') . '</span><input name="state" class="small-text" /></label>';
        echo '<label><input type="checkbox" name="traffic" value="1" /> ' . esc_html__('Traffic', 'net-attendance-logger') . '</label>';
        echo '</div>';
        echo '<p><label><span style="display:block;font-weight:600;">' . esc_html__('Traffic Details', 'net-attendance-logger') . '</span><input name="traffic_details" class="large-text" /></label></p>';
        echo '<p><label><span style="display:block;font-weight:600;">' . esc_html__('Notes', 'net-attendance-logger') . '</span><input name="notes" class="large-text" /></label></p>';
        submit_button(__('Add Check-in', 'net-attendance-logger'));
        echo '</form>';
        echo '</details>';
    }

    private static function render_close_event_form(int $event_id): void
    {
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="margin: 16px 0;">';
        wp_nonce_field('nal_close_event_' . $event_id, 'nal_close_event_nonce');
        echo '<input type="hidden" name="action" value="nal_close_event" />';
        echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
        submit_button(__('Close Event', 'net-attendance-logger'), 'secondary', 'submit', false);
        echo '</form>';
    }

    private static function render_reopen_event_form(int $event_id): void
    {
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="margin: 16px 0;" onsubmit="return confirm(\'' . esc_js(__('Reopen this event so attendance can be edited?', 'net-attendance-logger')) . '\');">';
        wp_nonce_field('nal_reopen_event_' . $event_id, 'nal_reopen_event_nonce');
        echo '<input type="hidden" name="action" value="nal_reopen_event" />';
        echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
        submit_button(__('Reopen Event for Editing', 'net-attendance-logger'), 'secondary', 'submit', false);
        echo '</form>';
    }

    private static function render_manual_attendance_table(int $event_id, array $attendance, bool $editable): void
    {
        echo '<h2>' . esc_html__('Current Check-ins', 'net-attendance-logger') . '</h2>';
        if (!$attendance) {
            echo '<div class="notice notice-info inline"><p>' . esc_html__('No check-ins have been recorded yet.', 'net-attendance-logger') . '</p></div>';
            return;
        }

        echo '<table class="widefat striped"><thead><tr>';
        foreach ([__('#', 'net-attendance-logger'), __('Callsign', 'net-attendance-logger'), __('Name', 'net-attendance-logger'), __('Time', 'net-attendance-logger'), __('Traffic / Notes', 'net-attendance-logger'), __('Actions', 'net-attendance-logger')] as $heading) {
            echo '<th>' . esc_html($heading) . '</th>';
        }
        echo '</tr></thead><tbody>';
        foreach ($attendance as $record) {
            $record_id = absint($record['id'] ?? 0);
            echo '<tr>';
            echo '<td>' . esc_html((string) ($record['sequence'] ?? '')) . '</td>';
            echo '<td><strong>' . esc_html($record['callsign'] ?? '') . '</strong></td>';
            echo '<td>' . esc_html($record['name'] ?? '') . '</td>';
            echo '<td>' . esc_html(self::format_datetime($record['checked_in_at'] ?? null)) . '</td>';
            echo '<td>';
            if ($editable) {
                echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
                wp_nonce_field('nal_update_checkin_' . $record_id, 'nal_update_checkin_nonce');
                echo '<input type="hidden" name="action" value="nal_update_checkin" />';
                echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
                echo '<input type="hidden" name="record_id" value="' . esc_attr((string) $record_id) . '" />';
                echo '<label><input type="checkbox" name="traffic" value="1"' . checked(!empty($record['traffic']), true, false) . ' /> ' . esc_html__('Traffic', 'net-attendance-logger') . '</label>';
                echo '<input name="traffic_details" class="regular-text" placeholder="' . esc_attr__('Traffic details', 'net-attendance-logger') . '" value="' . esc_attr($record['traffic_details'] ?? '') . '" /> ';
                echo '<input name="notes" class="regular-text" placeholder="' . esc_attr__('Notes', 'net-attendance-logger') . '" value="' . esc_attr($record['notes'] ?? '') . '" /> ';
                submit_button(__('Save', 'net-attendance-logger'), 'secondary small', 'submit', false);
                echo '</form>';
            } else {
                echo esc_html(!empty($record['traffic']) ? __('Traffic', 'net-attendance-logger') : __('No traffic', 'net-attendance-logger'));
                if (!empty($record['traffic_details'])) {
                    echo ': ' . esc_html($record['traffic_details']);
                }
                if (!empty($record['notes'])) {
                    echo '<br />' . esc_html($record['notes']);
                }
            }
            echo '</td>';
            echo '<td>';
            if ($editable) {
                echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" onsubmit="return confirm(\'' . esc_js(__('Remove this check-in?', 'net-attendance-logger')) . '\');">';
                wp_nonce_field('nal_delete_checkin_' . $record_id, 'nal_delete_checkin_nonce');
                echo '<input type="hidden" name="action" value="nal_delete_checkin" />';
                echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
                echo '<input type="hidden" name="record_id" value="' . esc_attr((string) $record_id) . '" />';
                submit_button(__('Remove', 'net-attendance-logger'), 'delete small', 'submit', false);
                echo '</form>';
            }
            echo '</td>';
            echo '</tr>';
        }
        echo '</tbody></table>';
    }

    public static function handle_start_event(): void
    {
        self::require_admin_capability(__('You do not have permission to start attendance events.', 'net-attendance-logger'));
        check_admin_referer('nal_start_event', 'nal_start_event_nonce');
        $repository = new Repository();
        $event_id = $repository->upsert_event([
            'source' => 'manual',
            'name' => sanitize_text_field(wp_unslash((string) ($_POST['event_name'] ?? ''))),
            'event_type' => sanitize_text_field(wp_unslash((string) ($_POST['event_type'] ?? 'Repeater Net'))),
            'status' => 'open',
            'started_at' => current_time('mysql'),
            'frequency' => sanitize_text_field(wp_unslash((string) ($_POST['frequency'] ?? ''))),
            'net_control' => sanitize_text_field(wp_unslash((string) ($_POST['net_control'] ?? ''))),
        ]);
        $net_control = sanitize_text_field(wp_unslash((string) ($_POST['net_control'] ?? '')));
        if ($net_control !== '') {
            $participant_id = $repository->upsert_participant([
                'source' => 'manual',
                'callsign' => $net_control,
                'name' => __('Net Control', 'net-attendance-logger'),
            ]);
            $repository->upsert_attendance_record($event_id, $participant_id, [
                'sequence' => $repository->next_attendance_sequence($event_id),
                'checked_in_at' => current_time('mysql'),
                'role' => 'net_control',
                'traffic' => false,
            ]);
        }
        self::redirect_with_notice(self::TAKE_SLUG, __('Attendance event started.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_rapid_entry(): void
    {
        self::require_admin_capability(__('You do not have permission to add rapid summary entries.', 'net-attendance-logger'));
        check_admin_referer('nal_rapid_entry', 'nal_rapid_entry_nonce');

        $event_name = sanitize_text_field(wp_unslash((string) ($_POST['event_name'] ?? '')));
        $head_count = absint($_POST['head_count'] ?? 0);
        $started_at = sanitize_text_field(wp_unslash((string) ($_POST['started_at'] ?? '')));
        if ($event_name === '' || $started_at === '') {
            self::redirect_with_notice(self::RAPID_ENTRY_SLUG, __('Date/time and net/event name are required.', 'net-attendance-logger'), 'error');
        }

        $repository = new Repository();
        $event_id = $repository->create_summary_event([
            'source' => 'rapid_summary',
            'name' => $event_name,
            'event_type' => sanitize_text_field(wp_unslash((string) ($_POST['event_type'] ?? 'Repeater Net'))),
            'started_at' => $started_at,
            'ended_at' => $started_at,
            'frequency' => sanitize_text_field(wp_unslash((string) ($_POST['frequency'] ?? ''))),
            'aggregate_attendance_count' => $head_count,
            'summary_only' => !empty($_POST['summary_only']),
            'notes' => wp_unslash((string) ($_POST['notes'] ?? '')),
            'metadata' => [
                'entry_method' => 'rapid_summary',
            ],
        ]);

        self::redirect_with_notice(self::MENU_SLUG, __('Summary-only event saved.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_add_checkin(): void
    {
        self::require_admin_capability(__('You do not have permission to add check-ins.', 'net-attendance-logger'));
        $event_id = absint($_POST['event_id'] ?? 0);
        check_admin_referer('nal_add_checkin_' . $event_id, 'nal_add_checkin_nonce');
        $callsign = strtoupper(preg_replace('/\s+/', '', sanitize_text_field(wp_unslash((string) ($_POST['callsign'] ?? '')))));
        if ($event_id <= 0 || $callsign === '') {
            self::redirect_with_notice(self::TAKE_SLUG, __('Event and callsign are required.', 'net-attendance-logger'), 'error', ['event_id' => $event_id]);
        }
        $repository = new Repository();
        if (!self::repository_event_is_open($repository, $event_id)) {
            self::redirect_with_notice(self::TAKE_SLUG, __('Closed events must be reopened before check-ins can be changed.', 'net-attendance-logger'), 'error', ['event_id' => $event_id]);
        }
        $participant_id = $repository->upsert_participant([
            'source' => 'manual',
            'callsign' => $callsign,
            'name' => sanitize_text_field(wp_unslash((string) ($_POST['name'] ?? ''))),
            'city' => sanitize_text_field(wp_unslash((string) ($_POST['city'] ?? ''))),
            'state' => sanitize_text_field(wp_unslash((string) ($_POST['state'] ?? ''))),
        ]);
        $repository->upsert_attendance_record($event_id, $participant_id, [
            'sequence' => $repository->next_attendance_sequence($event_id),
            'checked_in_at' => current_time('mysql'),
            'status' => 'present',
            'traffic' => !empty($_POST['traffic']),
            'traffic_details' => wp_unslash((string) ($_POST['traffic_details'] ?? '')),
            'notes' => wp_unslash((string) ($_POST['notes'] ?? '')),
        ]);
        self::redirect_with_notice(self::TAKE_SLUG, __('Check-in saved.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_update_checkin(): void
    {
        self::require_admin_capability(__('You do not have permission to update check-ins.', 'net-attendance-logger'));
        $event_id = absint($_POST['event_id'] ?? 0);
        $record_id = absint($_POST['record_id'] ?? 0);
        check_admin_referer('nal_update_checkin_' . $record_id, 'nal_update_checkin_nonce');
        $repository = new Repository();
        if (!self::repository_event_is_open($repository, $event_id)) {
            self::redirect_with_notice(self::TAKE_SLUG, __('Closed events must be reopened before check-ins can be changed.', 'net-attendance-logger'), 'error', ['event_id' => $event_id]);
        }
        $repository->update_attendance_record($record_id, [
            'traffic' => !empty($_POST['traffic']),
            'traffic_details' => wp_unslash((string) ($_POST['traffic_details'] ?? '')),
            'notes' => wp_unslash((string) ($_POST['notes'] ?? '')),
        ]);
        self::redirect_with_notice(self::TAKE_SLUG, __('Check-in updated.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_delete_checkin(): void
    {
        self::require_admin_capability(__('You do not have permission to remove check-ins.', 'net-attendance-logger'));
        $event_id = absint($_POST['event_id'] ?? 0);
        $record_id = absint($_POST['record_id'] ?? 0);
        check_admin_referer('nal_delete_checkin_' . $record_id, 'nal_delete_checkin_nonce');
        $repository = new Repository();
        if (!self::repository_event_is_open($repository, $event_id)) {
            self::redirect_with_notice(self::TAKE_SLUG, __('Closed events must be reopened before check-ins can be changed.', 'net-attendance-logger'), 'error', ['event_id' => $event_id]);
        }
        $repository->delete_attendance_record($record_id);
        self::redirect_with_notice(self::TAKE_SLUG, __('Check-in removed.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_close_event(): void
    {
        self::require_admin_capability(__('You do not have permission to close events.', 'net-attendance-logger'));
        $event_id = absint($_POST['event_id'] ?? 0);
        check_admin_referer('nal_close_event_' . $event_id, 'nal_close_event_nonce');
        $repository = new Repository();
        $repository->close_event($event_id);
        self::redirect_with_notice(self::TAKE_SLUG, __('Attendance event closed. Reopen it deliberately if further edits are needed.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_reopen_event(): void
    {
        self::require_admin_capability(__('You do not have permission to reopen events.', 'net-attendance-logger'));
        $event_id = absint($_POST['event_id'] ?? 0);
        check_admin_referer('nal_reopen_event_' . $event_id, 'nal_reopen_event_nonce');
        $repository = new Repository();
        $repository->reopen_event($event_id);
        self::redirect_with_notice(self::TAKE_SLUG, __('Attendance event reopened for editing.', 'net-attendance-logger'), 'success', ['event_id' => $event_id]);
    }

    public static function handle_delete_event(): void
    {
        self::require_admin_capability(__('You do not have permission to delete events.', 'net-attendance-logger'));
        $event_id = absint($_POST['event_id'] ?? 0);
        check_admin_referer('nal_delete_event_' . $event_id, 'nal_delete_event_nonce');
        $repository = new Repository();
        $deleted = $repository->delete_event($event_id);
        self::redirect_with_notice(self::MENU_SLUG, $deleted ? __('Attendance event deleted.', 'net-attendance-logger') : __('Attendance event could not be deleted.', 'net-attendance-logger'), $deleted ? 'success' : 'error');
    }

    public static function handle_import_json(): void
    {
        if (!Capabilities::can_import()) {
            wp_die(esc_html__('You do not have permission to import attendance.', 'net-attendance-logger'));
        }

        check_admin_referer('nal_import_json', 'nal_import_json_nonce');

        $payload = isset($_POST['payload']) ? trim(wp_unslash((string) $_POST['payload'])) : '';
        if (!empty($_FILES['payload_file']['tmp_name']) && is_uploaded_file($_FILES['payload_file']['tmp_name'])) {
            $uploaded = file_get_contents($_FILES['payload_file']['tmp_name']);
            if ($uploaded !== false && trim($uploaded) !== '') {
                $payload = $uploaded;
            }
        }
        $dry_run = isset($_POST['validate_only']);
        $importer = new Importer();
        $result = $dry_run ? $importer->validate($payload) : $importer->import($payload, false);

        $message = $result['ok']
            ? sprintf(
                '%s: %d event(s), %d participant(s), %d record(s).',
                $dry_run ? __('Validation succeeded', 'net-attendance-logger') : __('Import completed', 'net-attendance-logger'),
                (int) ($result['created']['events'] ?? 0),
                (int) ($result['created']['participants'] ?? 0),
                (int) ($result['created']['records'] ?? 0)
            )
            : sprintf(
                '%s: %s',
                __('Import failed', 'net-attendance-logger'),
                implode('; ', array_map('sanitize_text_field', $result['errors'] ?? []))
            );

        $args = [
            'page' => self::IMPORT_SLUG,
            'nal_notice' => $result['ok'] ? 'success' : 'error',
            'nal_message' => rawurlencode($message),
        ];

        if (!$dry_run && !empty($result['event_id'])) {
            $args['page'] = self::MENU_SLUG;
            $args['event_id'] = absint($result['event_id']);
        }

        wp_safe_redirect(add_query_arg($args, admin_url('admin.php')));
        exit;
    }

    public static function handle_save_settings(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('You do not have permission to manage Net Attendance settings.', 'net-attendance-logger'));
        }

        check_admin_referer('nal_save_settings', 'nal_save_settings_nonce');
        $roles = isset($_POST['import_roles']) && is_array($_POST['import_roles']) ? wp_unslash($_POST['import_roles']) : [];
        Capabilities::set_import_roles(array_map('sanitize_key', $roles));

        self::redirect_with_notice(self::SETTINGS_SLUG, __('API import role permissions saved.', 'net-attendance-logger'));
    }

    private static function render_event_list(Repository $repository): void
    {
        $events = $repository->list_events();
        echo '<p><a class="button button-primary" href="' . esc_url(admin_url('admin.php?page=' . self::TAKE_SLUG)) . '">' . esc_html__('Take Attendance', 'net-attendance-logger') . '</a> ';
        echo '<a class="button" href="' . esc_url(admin_url('admin.php?page=' . self::RAPID_ENTRY_SLUG)) . '">' . esc_html__('Rapid Entry', 'net-attendance-logger') . '</a> ';
        echo '<a class="button" href="' . esc_url(admin_url('admin.php?page=' . self::IMPORT_SLUG)) . '">' . esc_html__('Import JSON', 'net-attendance-logger') . '</a></p>';

        if (!$events) {
            echo '<div class="notice notice-info inline"><p>' . esc_html__('No attendance events have been imported yet.', 'net-attendance-logger') . '</p></div>';
            return;
        }

        echo '<table class="widefat striped">';
        echo '<thead><tr>';
        foreach ([__('Date', 'net-attendance-logger'), __('Name', 'net-attendance-logger'), __('Status', 'net-attendance-logger'), __('Type', 'net-attendance-logger'), __('Net Control', 'net-attendance-logger'), __('Frequency', 'net-attendance-logger'), __('Attendance', 'net-attendance-logger'), __('Traffic', 'net-attendance-logger'), __('Source', 'net-attendance-logger'), __('Actions', 'net-attendance-logger')] as $heading) {
            echo '<th>' . esc_html($heading) . '</th>';
        }
        echo '</tr></thead><tbody>';

        foreach ($events as $event) {
            $url = add_query_arg([
                'page' => self::MENU_SLUG,
                'event_id' => absint($event['id']),
            ], admin_url('admin.php'));
            echo '<tr>';
            echo '<td>' . esc_html(self::format_datetime($event['started_at'] ?? null)) . '</td>';
            echo '<td><a href="' . esc_url($url) . '"><strong>' . esc_html($event['name'] ?? __('Untitled Event', 'net-attendance-logger')) . '</strong></a></td>';
            echo '<td>' . esc_html(self::event_status_label($event)) . '</td>';
            echo '<td>' . esc_html($event['event_type'] ?? '') . '</td>';
            echo '<td>' . esc_html($event['net_control'] ?? '') . '</td>';
            echo '<td>' . esc_html($event['frequency'] ?? '') . '</td>';
            echo '<td>' . esc_html((string) (int) ($event['attendance_count'] ?? 0)) . '</td>';
            echo '<td>' . esc_html((string) (int) ($event['traffic_count'] ?? 0)) . '</td>';
            echo '<td>' . esc_html($event['source'] ?? '') . '</td>';
            echo '<td>';
            echo '<a class="button button-small" href="' . esc_url(add_query_arg(['page' => self::TAKE_SLUG, 'event_id' => absint($event['id'])], admin_url('admin.php'))) . '">' . esc_html__('Edit Attendance', 'net-attendance-logger') . '</a> ';
            self::render_delete_event_form(absint($event['id']), true);
            echo '</td>';
            echo '</tr>';
        }

        echo '</tbody></table>';
    }

    private static function render_event_detail(Repository $repository, int $event_id): void
    {
        $event = $repository->get_event($event_id);
        if (!$event) {
            echo '<div class="notice notice-error inline"><p>' . esc_html__('Event not found.', 'net-attendance-logger') . '</p></div>';
            echo '<p><a href="' . esc_url(admin_url('admin.php?page=' . self::MENU_SLUG)) . '">&larr; ' . esc_html__('Back to events', 'net-attendance-logger') . '</a></p>';
            return;
        }

        $attendance = $repository->get_event_attendance($event_id);
        echo '<p><a href="' . esc_url(admin_url('admin.php?page=' . self::MENU_SLUG)) . '">&larr; ' . esc_html__('Back to events', 'net-attendance-logger') . '</a></p>';
        echo '<h2>' . esc_html($event['name'] ?? __('Untitled Event', 'net-attendance-logger')) . '</h2>';
        self::render_delete_event_form($event_id, false);
        echo '<table class="form-table" role="presentation"><tbody>';
        self::render_detail_row(__('Date', 'net-attendance-logger'), self::format_datetime($event['started_at'] ?? null));
        self::render_detail_row(__('Type', 'net-attendance-logger'), $event['event_type'] ?? '');
        self::render_detail_row(__('Net Control', 'net-attendance-logger'), $event['net_control'] ?? '');
        self::render_detail_row(__('Frequency', 'net-attendance-logger'), $event['frequency'] ?? '');
        self::render_detail_row(__('Status', 'net-attendance-logger'), self::event_status_label($event));
        if (!empty($event['summary_only'])) {
            self::render_detail_row(__('Summary-only event', 'net-attendance-logger'), __('Yes', 'net-attendance-logger'));
            self::render_detail_row(__('Head Count', 'net-attendance-logger'), (string) (int) ($event['aggregate_attendance_count'] ?? 0));
        }
        self::render_detail_row(__('Source', 'net-attendance-logger'), $event['source'] ?? '');
        echo '</tbody></table>';

        echo '<h2>' . esc_html__('Attendance', 'net-attendance-logger') . '</h2>';
        if (!$attendance) {
            echo '<div class="notice notice-info inline"><p>' . esc_html__('No attendance records are attached to this event.', 'net-attendance-logger') . '</p></div>';
            return;
        }

        echo '<table class="widefat striped">';
        echo '<thead><tr>';
        foreach ([__('#', 'net-attendance-logger'), __('Time', 'net-attendance-logger'), __('Callsign', 'net-attendance-logger'), __('Name', 'net-attendance-logger'), __('Location', 'net-attendance-logger'), __('Grid', 'net-attendance-logger'), __('Role', 'net-attendance-logger'), __('Traffic', 'net-attendance-logger'), __('Notes', 'net-attendance-logger')] as $heading) {
            echo '<th>' . esc_html($heading) . '</th>';
        }
        echo '</tr></thead><tbody>';
        foreach ($attendance as $record) {
            $location = trim((string) ($record['city'] ?? '') . ', ' . (string) ($record['state'] ?? ''), ', ');
            echo '<tr>';
            echo '<td>' . esc_html((string) ($record['sequence'] ?? '')) . '</td>';
            echo '<td>' . esc_html(self::format_datetime($record['checked_in_at'] ?? null)) . '</td>';
            echo '<td><strong>' . esc_html($record['callsign'] ?? '') . '</strong></td>';
            echo '<td>' . esc_html($record['name'] ?? '') . '</td>';
            echo '<td>' . esc_html($location) . '</td>';
            echo '<td>' . esc_html($record['grid'] ?? '') . '</td>';
            echo '<td>' . esc_html($record['role'] ?? '') . '</td>';
            echo '<td>' . self::render_traffic_cell($record) . '</td>';
            echo '<td>' . esc_html($record['notes'] ?? '') . '</td>';
            echo '</tr>';
        }
        echo '</tbody></table>';
    }

    private static function render_delete_event_form(int $event_id, bool $compact): void
    {
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="display:inline-block; margin: 0 0 12px;" onsubmit="return confirm(\'' . esc_js(__('Delete this attendance event and all of its attendance records? This cannot be undone.', 'net-attendance-logger')) . '\');">';
        wp_nonce_field('nal_delete_event_' . $event_id, 'nal_delete_event_nonce');
        echo '<input type="hidden" name="action" value="nal_delete_event" />';
        echo '<input type="hidden" name="event_id" value="' . esc_attr((string) $event_id) . '" />';
        submit_button(__('Delete Event', 'net-attendance-logger'), $compact ? 'delete small' : 'delete', 'submit', false);
        echo '</form>';
    }

    private static function render_detail_row(string $label, mixed $value): void
    {
        echo '<tr><th scope="row">' . esc_html($label) . '</th><td>' . esc_html((string) $value) . '</td></tr>';
    }

    private static function render_event_status_banner(array $event): void
    {
        $open = self::event_is_open($event);
        $class = $open ? 'notice-success' : 'notice-warning';
        $label = self::event_status_label($event);
        echo '<div class="notice ' . esc_attr($class) . ' inline"><p><strong>' . esc_html($label) . '</strong> &nbsp; ';
        echo esc_html__('Started:', 'net-attendance-logger') . ' ' . esc_html(self::format_datetime($event['started_at'] ?? null));
        if (!$open && !empty($event['ended_at'])) {
            echo ' &nbsp; ' . esc_html__('Closed:', 'net-attendance-logger') . ' ' . esc_html(self::format_datetime($event['ended_at']));
        }
        echo '</p></div>';
    }

    private static function event_status_label(array $event): string
    {
        return self::event_is_open($event) ? __('Open for attendance entry', 'net-attendance-logger') : __('Closed - editing locked', 'net-attendance-logger');
    }

    private static function event_is_open(array $event): bool
    {
        return strtolower((string) ($event['status'] ?? '')) !== 'closed';
    }

    private static function repository_event_is_open(Repository $repository, int $event_id): bool
    {
        $event = $event_id > 0 ? $repository->get_event($event_id) : null;
        return is_array($event) && self::event_is_open($event);
    }

    private static function render_traffic_cell(array $record): string
    {
        if (empty($record['traffic'])) {
            return esc_html__('No', 'net-attendance-logger');
        }
        $details = trim(wp_strip_all_tags((string) ($record['traffic_details'] ?? '')));
        $notes = trim(wp_strip_all_tags((string) ($record['notes'] ?? '')));
        if ($details === '' && $notes === '') {
            return esc_html__('Yes', 'net-attendance-logger');
        }
        $body = $details;
        if ($notes !== '') {
            $body .= ($body !== '' ? "\n" : '') . sprintf(__('Notes: %s', 'net-attendance-logger'), $notes);
        }
        return '<details class="nal-traffic-details"><summary>' . esc_html__('Yes - view', 'net-attendance-logger') . '</summary><div style="min-width:220px; max-width:360px; white-space:pre-wrap; padding:8px; background:#fff; border:1px solid #ccd0d4;">' . esc_html($body) . '</div></details>';
    }

    private static function require_admin_capability(string $message): void
    {
        if (!Capabilities::can_take_attendance()) {
            wp_die(esc_html($message));
        }
    }

    private static function redirect_with_notice(string $page, string $message, string $type = 'success', array $extra_args = []): void
    {
        $args = array_merge([
            'page' => $page,
            'nal_notice' => $type === 'success' ? 'success' : 'error',
            'nal_message' => rawurlencode($message),
        ], $extra_args);
        wp_safe_redirect(add_query_arg($args, admin_url('admin.php')));
        exit;
    }

    private static function render_admin_notice(): void
    {
        if (empty($_GET['nal_notice']) || empty($_GET['nal_message'])) {
            return;
        }

        $class = $_GET['nal_notice'] === 'success' ? 'notice-success' : 'notice-error';
        $message = sanitize_text_field(wp_unslash((string) $_GET['nal_message']));
        echo '<div class="notice ' . esc_attr($class) . ' is-dismissible"><p>' . esc_html($message) . '</p></div>';
    }

    private static function format_datetime(mixed $value): string
    {
        if (!$value) {
            return '';
        }

        $timestamp = strtotime((string) $value);
        if (!$timestamp) {
            return (string) $value;
        }

        return date_i18n(get_option('date_format') . ' ' . get_option('time_format'), $timestamp);
    }
}
