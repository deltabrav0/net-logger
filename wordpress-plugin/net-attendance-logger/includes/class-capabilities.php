<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class Capabilities
{
    public const IMPORT = 'import_net_attendance';
    public const VIEW_REPORTS = 'view_net_attendance_reports';

    public static function can_import(): bool
    {
        return current_user_can('manage_options') || current_user_can(self::IMPORT);
    }

    public static function can_view_reports(): bool
    {
        return current_user_can('manage_options') || current_user_can(self::VIEW_REPORTS);
    }

    public static function grant_defaults(): void
    {
        $administrator = get_role('administrator');
        if ($administrator) {
            $administrator->add_cap(self::IMPORT);
            $administrator->add_cap(self::VIEW_REPORTS);
        }
    }

    public static function import_role_slugs(): array
    {
        $slugs = get_option('net_attendance_logger_import_role_slugs', []);
        return is_array($slugs) ? array_values(array_filter(array_map('sanitize_key', $slugs))) : [];
    }

    public static function set_import_roles(array $role_slugs): void
    {
        $editable_roles = array_keys(get_editable_roles());
        $role_slugs = array_values(array_intersect(array_map('sanitize_key', $role_slugs), $editable_roles));

        foreach ($editable_roles as $role_slug) {
            $role = get_role($role_slug);
            if (!$role) {
                continue;
            }

            if ($role_slug === 'administrator' || in_array($role_slug, $role_slugs, true)) {
                $role->add_cap(self::IMPORT);
            } else {
                $role->remove_cap(self::IMPORT);
            }
        }

        update_option('net_attendance_logger_import_role_slugs', $role_slugs, false);
    }
}
