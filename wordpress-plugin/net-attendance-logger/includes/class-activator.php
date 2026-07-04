<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class Activator
{
    public static function activate(): void
    {
        self::create_tables();
        Capabilities::grant_defaults();
        update_option('net_attendance_logger_version', NAL_VERSION);
    }

    private static function create_tables(): void
    {
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';

        foreach (DB::schema_sql() as $sql) {
            dbDelta($sql);
        }
    }
}
