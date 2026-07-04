<?php
/**
 * Plugin Name: Net & Meeting Attendance
 * Description: Store, import, report, and display attendance for radio nets and meetings.
 * Version: 0.1.1
 * Author: Danny Butler
 * Text Domain: net-attendance-logger
 * Requires at least: 6.0
 * Requires PHP: 8.0
 */

if (!defined('ABSPATH')) {
    exit;
}

define('NAL_VERSION', '0.1.1');
define('NAL_PLUGIN_FILE', __FILE__);
define('NAL_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('NAL_PLUGIN_URL', plugin_dir_url(__FILE__));

require_once NAL_PLUGIN_DIR . 'includes/class-plugin.php';
require_once NAL_PLUGIN_DIR . 'includes/class-db.php';
require_once NAL_PLUGIN_DIR . 'includes/class-activator.php';

register_activation_hook(NAL_PLUGIN_FILE, 'Net_Attendance_Logger\Activator::activate');

add_action('plugins_loaded', function () {
    Net_Attendance_Logger\Plugin::init();
});
