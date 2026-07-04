<?php

namespace Net_Attendance_Logger;

use WP_REST_Request;
use WP_REST_Response;
use WP_REST_Server;

if (!defined('ABSPATH')) {
    exit;
}

final class Rest_Controller
{
    public static function register(): void
    {
        add_action('rest_api_init', [self::class, 'register_routes']);
    }

    public static function register_routes(): void
    {
        register_rest_route('net-attendance/v1', '/imports/validate', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [self::class, 'validate_import'],
            'permission_callback' => [self::class, 'can_import'],
        ]);

        register_rest_route('net-attendance/v1', '/imports', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [self::class, 'create_import'],
            'permission_callback' => [self::class, 'can_import'],
        ]);

        register_rest_route('net-attendance/v1', '/net-logger/sessions', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [self::class, 'create_net_logger_session'],
            'permission_callback' => [self::class, 'can_import'],
        ]);
    }

    public static function can_import(): bool
    {
        // WordPress Application Passwords authenticate the request as a user;
        // the custom capability below keeps imports limited to trusted operators
        // without hard-coding a site-specific role such as DETARC Member.
        return Capabilities::can_import();
    }

    public static function validate_import(WP_REST_Request $request): WP_REST_Response
    {
        $payload = $request->get_json_params();
        $importer = new Importer();
        $result = $importer->validate(is_array($payload) ? $payload : []);
        return new WP_REST_Response($result, $result['ok'] ? 200 : 400);
    }

    public static function create_import(WP_REST_Request $request): WP_REST_Response
    {
        $payload = $request->get_json_params();
        $importer = new Importer();
        $result = $importer->import(is_array($payload) ? $payload : [], false);
        return new WP_REST_Response($result, $result['ok'] ? 201 : 400);
    }

    public static function create_net_logger_session(WP_REST_Request $request): WP_REST_Response
    {
        $payload = $request->get_json_params();
        $importer = new Importer();
        $result = $importer->import(is_array($payload) ? $payload : [], false);
        $status = $result['ok'] ? (!empty($result['updated']['events']) ? 200 : 201) : 400;
        return new WP_REST_Response($result, $status);
    }
}
