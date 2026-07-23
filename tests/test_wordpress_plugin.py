import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "wordpress-plugin"
PLUGIN = PLUGIN_ROOT / "net-attendance-logger"


class PluginScaffoldTests(unittest.TestCase):
    def test_plugin_main_file_declares_expected_wordpress_metadata(self):
        main = PLUGIN / "net-attendance-logger.php"
        self.assertTrue(main.exists())
        text = main.read_text()
        self.assertIn("Plugin Name: Net & Meeting Attendance", text)
        self.assertIn("Text Domain: net-attendance-logger", text)
        self.assertIn("Net_Attendance_Logger\\Plugin::init", text)
        self.assertIn("NAL_PLUGIN_BASENAME", text)
        self.assertIn("Version: 0.1.8", text)
        self.assertIn("define('NAL_VERSION', '0.1.8')", text)

    def test_plugin_loader_and_public_css_exist(self):
        self.assertTrue((PLUGIN / "includes" / "class-plugin.php").exists())
        self.assertTrue((PLUGIN / "includes" / "class-capabilities.php").exists())
        self.assertTrue((PLUGIN / "public" / "css" / "net-attendance.css").exists())
        self.assertTrue((PLUGIN / "readme.txt").exists())

    def test_activation_schema_files_and_hook_are_present(self):
        main_text = (PLUGIN / "net-attendance-logger.php").read_text()
        self.assertIn("includes/class-activator.php", main_text)
        self.assertIn("register_activation_hook", main_text)
        self.assertIn("Net_Attendance_Logger\\Activator::activate", main_text)
        activator_text = (PLUGIN / "includes" / "class-activator.php").read_text()
        self.assertIn("function maybe_upgrade", activator_text)
        self.assertIn("net_attendance_logger_version", activator_text)
        self.assertIn("Activator::maybe_upgrade", (PLUGIN / "includes" / "class-plugin.php").read_text())
        self.assertTrue((PLUGIN / "includes" / "class-activator.php").exists())
        self.assertTrue((PLUGIN / "includes" / "class-db.php").exists())

    def test_activation_schema_defines_three_custom_tables(self):
        activator = (PLUGIN / "includes" / "class-activator.php").read_text()
        db_file = (PLUGIN / "includes" / "class-db.php").read_text()
        self.assertIn("dbDelta", activator)
        self.assertIn("net_attendance_events", db_file)
        self.assertIn("net_attendance_participants", db_file)
        self.assertIn("net_attendance_records", db_file)
        self.assertIn("UNIQUE KEY event_participant", db_file)
        for column in ["external_id", "event_type", "started_at", "frequency", "net_control", "summary_only", "aggregate_attendance_count", "callsign", "grid", "checked_in_at", "traffic_details", "metadata"]:
            self.assertIn(column, db_file)

    def test_repository_layer_declares_required_upsert_and_query_methods(self):
        plugin_text = (PLUGIN / "includes" / "class-plugin.php").read_text()
        self.assertIn("includes/class-repository.php", plugin_text)
        repo = (PLUGIN / "includes" / "class-repository.php").read_text()
        for method in [
            "upsert_event",
            "upsert_participant",
            "upsert_attendance_record",
            "get_event",
            "get_event_attendance",
            "list_events",
            "report_attendance_over_time",
            "report_top_participants",
            "report_participation_snapshot",
            "report_new_participants",
            "report_participation_milestones",
            "report_participation_awards",
            "report_weekly_streaks",
            "report_net_control_awards",
            "list_event_names",
            "report_attendance_series",
            "report_attendance_totals_by_event_name",
            "update_event",
            "close_event",
            "reopen_event",
            "delete_event",
            "next_attendance_sequence",
            "update_attendance_record",
            "delete_attendance_record",
            "create_summary_event",
        ]:
            self.assertIn(f"function {method}", repo)

    def test_repository_layer_implements_import_idempotency_rules(self):
        repo = (PLUGIN / "includes" / "class-repository.php").read_text()
        self.assertIn("source = %s AND external_id = %s", repo)
        self.assertIn("callsign = %s", repo)
        self.assertIn("event_id = %d AND participant_id = %d", repo)
        self.assertIn("normalize_callsign", repo)
        self.assertIn("wp_json_encode", repo)

    def test_importer_layer_accepts_generic_payloads_and_dry_run(self):
        plugin_text = (PLUGIN / "includes" / "class-plugin.php").read_text()
        self.assertIn("includes/class-importer.php", plugin_text)
        importer = (PLUGIN / "includes" / "class-importer.php").read_text()
        for token in [
            "function validate",
            "function import",
            "dry_run",
            "attendance",
            "events",
            "process_batch",
            "participant",
            "from_net_logger_payload",
            "net_logger_checkin_id",
            "net_logger_session",
            "upsert_event",
            "upsert_participant",
            "upsert_attendance_record",
            "event name is required",
            "participant identity is required",
        ]:
            self.assertIn(token, importer)

    def test_rest_controller_registers_authenticated_import_endpoints(self):
        plugin_text = (PLUGIN / "includes" / "class-plugin.php").read_text()
        self.assertIn("includes/class-rest-controller.php", plugin_text)
        self.assertIn("Rest_Controller::register", plugin_text)
        rest = (PLUGIN / "includes" / "class-rest-controller.php").read_text()
        for token in [
            "register_rest_route",
            "net-attendance/v1",
            "imports/validate",
            "imports",
            "net-logger/sessions",
            "create_net_logger_session",
            "Capabilities::can_import()",
            "without hard-coding a site-specific role",
            "Application Password",
            "WP_REST_Server::CREATABLE",
            "validate_import",
            "create_import",
        ]:
            self.assertIn(token, rest)
        capabilities = (PLUGIN / "includes" / "class-capabilities.php").read_text()
        for token in [
            "import_net_attendance",
            "view_net_attendance_reports",
            "view_net_attendance_events",
            "NET_CONTROL_ROLE_SLUG",
            "DETARC_MEMBER_ROLE_SLUG",
            "grant_net_control_defaults",
            "remove_cap(self::IMPORT)",
            "remove_cap(self::TAKE_ATTENDANCE)",
            "grant_defaults",
            "$administrator->add_cap(self::IMPORT)",
            "set_import_roles",
            "get_editable_roles",
            "net_attendance_logger_import_role_slugs",
        ]:
            self.assertIn(token, capabilities)

    def test_net_logger_sample_payload_is_seeded_and_documented(self):
        sample = PLUGIN_ROOT / "docs" / "sample-data" / "net-logger-session.json"
        self.assertTrue(sample.exists())
        text = sample.read_text()
        for token in [
            '"session"',
            '"checkins"',
            '"callsign"',
            '"traffic_details"',
        ]:
            self.assertIn(token, text)
        api = (PLUGIN / "docs" / "api.md").read_text()
        self.assertIn("/wp-json/net-attendance/v1/net-logger/sessions", api)
        self.assertIn("docs/sample-data/net-logger-session.json", api)
        self.assertIn("WordPress Application Password", api)
        self.assertIn("import_net_attendance", api)
        self.assertIn("Net Attendance → Settings → API Import Permissions", api)
        self.assertIn("Repeated pushes are idempotent", api)

    def test_admin_controller_registers_menu_and_import_page(self):
        plugin_text = (PLUGIN / "includes" / "class-plugin.php").read_text()
        self.assertIn("includes/class-admin-controller.php", plugin_text)
        self.assertIn("Admin_Controller::register", plugin_text)
        self.assertIn("add_shortcode('net_attendance_reports'", plugin_text)
        self.assertIn("add_shortcode('net_attendance_awards'", plugin_text)
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        for token in [
            "add_menu_page",
            "Net Attendance",
            "dashicons-groups",
            "add_submenu_page",
            "Import JSON",
            "enctype=\"multipart/form-data\"",
            "payload_file",
            "is_uploaded_file",
            "admin_post_nal_import_json",
            "handle_import_json",
            "render_events_page",
            "render_import_page",
            "render_reports_page",
            "render_reports_shortcode",
            "render_awards_shortcode",
            "render_awards_content",
            "render_take_attendance_page",
            "render_settings_page",
            "render_rapid_entry_page",
            "handle_save_settings",
            "handle_rapid_entry",
            "SETTINGS_SLUG",
            "RAPID_ENTRY_SLUG",
            "nal_rapid_entry",
            "summary_only",
            "aggregate_attendance_count",
            "Rapid Entry",
            "Head Count",
            "Summary-only event",
            "create_summary_event",
            "nal_save_settings",
            "API Import Permissions",
            "Capabilities::set_import_roles",
            "Capabilities::IMPORT",
            "$has_capability",
            "Save API Permissions",
            "Plugin Documentation",
            "Award Structure",
            "nal-award-structure",
            "Bronze — 10 lifetime check-ins",
            "Current Streak — 3 consecutive ISO weeks",
            "Net Control — one or more sessions served",
            "net_attendance_logger_participation_awards",
            "nal-plugin-documentation",
            "docs/usage.md",
            "docs/reports.md",
            "docs/api.md",
            "handle_start_event",
            "handle_add_checkin",
            "handle_update_checkin",
            "handle_delete_checkin",
            "handle_close_event",
            "handle_reopen_event",
            "handle_delete_event",
            "nal_delete_event_nonce",
            "Take Attendance",
            "Quick Check-in",
            "nal-callsign-input",
            "Reopen Event for Editing",
            "Closed events must be reopened before check-ins can be changed",
            "Yes - view",
            "Use the standalone Net Logger tool",
            "current_user_can_view_reports",
            "Capabilities::can_view_reports",
            "detarc_member",
            "net_attendance_logger_report_role_slugs",
            "Reports & Charts",
            "report_attendance_series",
            "list_events",
            "get_event_attendance",
            "checked_in_at",
            "manage_options",
            "TAKE_ATTENDANCE",
            "VIEW_EVENTS",
            "VIEW_REPORTS",
            "can_take_attendance",
            "can_view_events",
            "can_view_reports",
            "grant_detarc_member_defaults",
            "grant_net_control_defaults",
            "detarc_member",
            "net_control",
            "DETARC Member",
            "Net Control",
            "Capabilities::can_take_attendance()",
            "Capabilities::can_view_events()",
            "Capabilities::VIEW_REPORTS",
            "Capabilities::can_import()",
        ]:
            self.assertIn(token, admin)

    def test_detarc_members_can_only_view_while_net_control_can_operate(self):
        capabilities = (PLUGIN / "includes" / "class-capabilities.php").read_text()
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()

        for token in [
            "public const NET_CONTROL_ROLE_SLUG = 'net_control'",
            "public const DETARC_MEMBER_ROLE_SLUG = 'detarc_member'",
            "$net_control->add_cap(self::IMPORT)",
            "$net_control->add_cap(self::TAKE_ATTENDANCE)",
            "$detarc_member->add_cap(self::VIEW_EVENTS)",
            "$detarc_member->add_cap(self::VIEW_REPORTS)",
            "$detarc_member->remove_cap(self::IMPORT)",
            "$detarc_member->remove_cap(self::TAKE_ATTENDANCE)",
            "function grant_net_control_defaults",
            "function grant_detarc_member_defaults",
        ]:
            self.assertIn(token, capabilities)

        self.assertIn("Capabilities::VIEW_EVENTS", admin)
        self.assertIn("Capabilities::VIEW_REPORTS", admin)
        self.assertIn("Capabilities::TAKE_ATTENDANCE", admin)
        self.assertIn("Capabilities::can_take_attendance()", admin)
        self.assertIn("Capabilities::can_import()", admin)

    def test_reports_shortcode_avoids_admin_only_frontend_helpers(self):
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        self.assertIn("function render_reports_shortcode($atts = [])", admin)
        self.assertIn("is_array($atts) ? $atts : []", admin)
        self.assertIn("nal-report-filter-submit", admin)
        self.assertNotIn("submit_button(__('Apply Filters'", admin)

    def test_reports_include_participation_snapshot_leaderboard_newcomers_and_awards(self):
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        repo = (PLUGIN / "includes" / "class-repository.php").read_text()
        for token in [
            "Participation Snapshot",
            "Top Participants",
            "New Participants",
            "Participation Awards",
            "render_participation_snapshot",
            "render_top_participants_chart",
            "render_new_participants",
            "render_participation_milestones",
            "show_leaderboard",
            "show_new_participants",
            "show_milestones",
        ]:
            self.assertIn(token, admin)
        for token in [
            "function participation_awards",
            "net_attendance_logger_participation_awards",
            "'bronze'",
            "'silver'",
            "'gold'",
            "'century'",
            "'rookie'",
            "'net_control'",
            "'streak'",
            "COUNT(DISTINCT p.id) AS distinct_participants",
            "MIN(r.checked_in_at) AS first_checkin_at",
            "MAX(r.checked_in_at) AS last_checkin_at",
            "DATE_FORMAT(COALESCE(r.checked_in_at, e.started_at), '%x-W%v')",
            "LOWER(r.role) = 'net_control'",
            "LOWER(p.callsign) = LOWER(e.net_control)",
            "award_slug",
            "award_label",
            "metric_label",
        ]:
            self.assertIn(token, repo)


    def test_participation_awards_shortcode_renders_awards_only(self):
        plugin_text = (PLUGIN / "includes" / "class-plugin.php").read_text()
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        reports = (PLUGIN / "docs" / "reports.md").read_text()
        usage = (PLUGIN / "docs" / "usage.md").read_text()
        readme = (PLUGIN / "readme.txt").read_text()

        self.assertIn("add_shortcode('net_attendance_awards'", plugin_text)
        for token in [
            "function render_awards_shortcode($atts = [])",
            "shortcode_atts",
            "net_attendance_awards",
            "render_awards_content",
            "report_participation_awards",
            "show_filters",
            "limit",
            "Participation Awards",
            "net-attendance-awards",
        ]:
            self.assertIn(token, admin)

        for doc in [reports, usage, readme]:
            self.assertIn("[net_attendance_awards]", doc)
            self.assertIn("participation-awards page", doc)

    def test_reports_shortcode_supports_sections_attribute_for_separate_chart_pages(self):
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        reports = (PLUGIN / "docs" / "reports.md").read_text()
        readme = (PLUGIN / "readme.txt").read_text()

        for token in [
            "'sections' => 'all'",
            "report_sections",
            "section_enabled($sections, 'snapshot')",
            "section_enabled($sections, 'leaderboard')",
            "section_enabled($sections, 'new_participants')",
            "section_enabled($sections, 'milestones')",
            "section_enabled($sections, 'totals')",
            "section_enabled($sections, 'trends')",
        ]:
            self.assertIn(token, admin)

        for token in [
            'sections="snapshot,leaderboard"',
            'sections="trends"',
            'sections="new_participants,milestones"',
            "snapshot, leaderboard, new_participants, milestones, totals, trends",
        ]:
            self.assertIn(token, reports)
            self.assertIn(token, readme)

    def test_plugin_release_notes_document_current_plugin_version(self):
        notes = PLUGIN / "RELEASE_NOTES.md"
        self.assertTrue(notes.exists())
        text = notes.read_text()
        for token in [
            "## v0.1.8",
            "Award Structure",
            "Settings page",
            "Bronze",
            "Current Streak",
            "## v0.1.7",
            "[net_attendance_awards]",
            "participation-awards page",
            "## v0.1.6",
            "Participation Awards",
            "Bronze",
            "Current Streak",
            "Net Control",
            "## v0.1.5",
            "sections=\"snapshot,leaderboard\"",
            "separate report pages",
        ]:
            self.assertIn(token, text)

    def test_event_detail_supports_editing_event_metadata_without_reopening_attendance(self):
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        repo = (PLUGIN / "includes" / "class-repository.php").read_text()
        for token in [
            "admin_post_nal_update_event",
            "handle_update_event",
            "render_edit_event_form",
            "nal_update_event_nonce",
            "name=\"event_name\"",
            "name=\"started_at\"",
            "name=\"frequency\"",
            "Event details updated.",
            "Update Event Details",
        ]:
            self.assertIn(token, admin)
        self.assertIn("function update_event", repo)
        self.assertIn("'name' =>", repo)
        self.assertIn("'started_at' =>", repo)
        self.assertIn("'frequency' =>", repo)

    def test_reports_documentation_covers_shortcode_and_memberpress_dependency(self):
        reports = PLUGIN / "docs" / "reports.md"
        self.assertTrue(reports.exists())
        text = reports.read_text()
        for token in [
            "[net_attendance_reports]",
            "Members plugin by MemberPress",
            "DETARC Member",
            "view_net_attendance_reports",
            "net_attendance_logger_report_role_slugs",
            "Appearance → Menus",
            "Participation Snapshot",
            "Top Participants",
            "New Participants",
            "Participation Awards",
            "show_leaderboard=\"yes|no\"",
            "show_new_participants=\"yes|no\"",
            "show_milestones=\"yes|no\"",
            "Participation Awards",
            "Bronze",
            "Silver",
            "Gold",
            "Century Club",
            "Rookie",
            "Current Streak",
            "Net Control",
            "Award Structure",
            "Settings page",
        ]:
            self.assertIn(token, text)

    def test_installation_and_usage_documentation_cover_checkpoint_basics(self):
        installation = PLUGIN / "docs" / "installation.md"
        usage = PLUGIN / "docs" / "usage.md"
        readme = PLUGIN / "readme.txt"
        for path in [installation, usage, readme]:
            self.assertTrue(path.exists(), f"missing documentation file: {path}")

        installation_text = installation.read_text()
        for token in [
            "https://dev.detarc.net",
            "net-attendance-logger.zip",
            "Plugins → Add New Plugin → Upload Plugin",
            "Net Attendance → Settings",
            "import_net_attendance",
            "API Import Permissions",
            "net_attendance_logger_import_role_slugs",
            "view_net_attendance_reports",
            "Members by MemberPress",
            "Members plugin by MemberPress",
            "Net Control role",
        ]:
            self.assertIn(token, installation_text)

        usage_text = usage.read_text()
        for token in [
            "[net_attendance_reports]",
            "period=\"day|week|month|year\"",
            "show_filters=\"yes|no\"",
            "https://dev.detarc.net/net-attendance-reports/",
            "simple manual attendance-taking screen",
            "Quick Check-in",
            "Reopen Event for Editing",
            "Yes - view",
            "Use the standalone Net Logger tool",
            "delete an attendance event",
            "Rapid Summary Entry",
            "date/time",
            "head count",
            "summary-only events",
        ]:
            self.assertIn(token, usage_text)

        readme_text = readme.read_text()
        for token in [
            "https://dev.detarc.net",
            "docs/installation.md",
            "docs/usage.md",
            "[net_attendance_reports period=\"week\"]",
            "import_net_attendance",
            "API Import Permissions",
            "Members plugin by MemberPress",
            "Plugin documentation",
            "Award Structure",
            "Settings page",
            "docs/reports.md",
            "Participation Awards",
            "Current Streak",
        ]:
            self.assertIn(token, readme_text)


if __name__ == "__main__":
    unittest.main()
