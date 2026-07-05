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
        self.assertIn("Version: 0.1.2", text)
        self.assertIn("define('NAL_VERSION', '0.1.2')", text)

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
            "list_event_names",
            "report_attendance_series",
            "report_attendance_totals_by_event_name",
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
            "can_take_attendance",
            "grant_detarc_member_defaults",
            "detarc_member",
            "DETARC Member",
            "take_net_attendance",
            "Capabilities::can_take_attendance()",
            "Capabilities::can_import()",
        ]:
            self.assertIn(token, admin)

    def test_reports_shortcode_avoids_admin_only_frontend_helpers(self):
        admin = (PLUGIN / "includes" / "class-admin-controller.php").read_text()
        self.assertIn("function render_reports_shortcode($atts = [])", admin)
        self.assertIn("is_array($atts) ? $atts : []", admin)
        self.assertIn("nal-report-filter-submit", admin)
        self.assertNotIn("submit_button(__('Apply Filters'", admin)

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
        ]:
            self.assertIn(token, readme_text)


if __name__ == "__main__":
    unittest.main()
