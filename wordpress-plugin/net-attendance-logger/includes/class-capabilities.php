<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class Capabilities
{
    public const IMPORT = 'import_net_attendance';
    public const VIEW_REPORTS = 'view_net_attendance_reports';
    public const TAKE_ATTENDANCE = 'take_net_attendance';
    public const VIEW_EVENTS = 'view_net_attendance_events';

    public static function can_import(): bool
    {
        return current_user_can('manage_options') || current_user_can(self::IMPORT);
    }

    public static function can_view_reports(): bool
    {
        return current_user_can('manage_options') || current_user_can(self::VIEW_REPORTS);
    }

    public static function can_take_attendance(): bool
    {
        return current_user_can('manage_options') || current_user_can(self::TAKE_ATTENDANCE);
    }

    public static function can_view_events(): bool
    {
        return current_user_can('manage_options') || current_user_can(self::VIEW_EVENTS);
    }

    public static function grant_defaults(): void
    {
        $administrator = get_role('administrator');
        if ($administrator) {
            $administrator->add_cap(self::IMPORT);
            $administrator->add_cap(self::VIEW_REPORTS);
            $administrator->add_cap(self::TAKE_ATTENDANCE);
            $administrator->add_cap(self::VIEW_EVENTS);
        }

        self::grant_detarc_member_defaults();
    }

    public static function grant_detarc_member_defaults(): void
    {
        $detarc_member = get_role('detarc_member');
        if ($detarc_member) {
            $detarc_member->add_cap(self::IMPORT);
            $detarc_member->add_cap(self::TAKE_ATTENDANCE);
            $detarc_member->add_cap(self::VIEW_EVENTS);
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
