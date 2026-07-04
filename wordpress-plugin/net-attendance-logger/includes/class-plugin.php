<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

require_once NAL_PLUGIN_DIR . 'includes/class-capabilities.php';
require_once NAL_PLUGIN_DIR . 'includes/class-repository.php';
require_once NAL_PLUGIN_DIR . 'includes/class-importer.php';
require_once NAL_PLUGIN_DIR . 'includes/class-rest-controller.php';
require_once NAL_PLUGIN_DIR . 'includes/class-admin-controller.php';

final class Plugin
{
    private static bool $initialized = false;

    public static function init(): void
    {
        if (self::$initialized) {
            return;
        }

        self::$initialized = true;

        add_action('wp_enqueue_scripts', [self::class, 'register_public_assets']);
        add_shortcode('net_attendance_reports', [Admin_Controller::class, 'render_reports_shortcode']);
        Rest_Controller::register();
        Admin_Controller::register();
    }

    public static function register_public_assets(): void
    {
        wp_register_style(
            'net-attendance-logger',
            NAL_PLUGIN_URL . 'public/css/net-attendance.css',
            [],
            NAL_VERSION
        );
    }
}
