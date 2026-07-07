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
    public const NET_CONTROL_ROLE_SLUG = 'net_control';
    public const DETARC_MEMBER_ROLE_SLUG = 'detarc_member';
    private static bool $role_defaults_reconciled = false;

    public static function can_import(): bool
    {
        self::reconcile_role_defaults_once();
        return current_user_can('manage_options') || current_user_can(self::IMPORT);
    }

    public static function can_view_reports(): bool
    {
        self::reconcile_role_defaults_once();
        return current_user_can('manage_options') || current_user_can(self::VIEW_REPORTS);
    }

    public static function can_take_attendance(): bool
    {
        self::reconcile_role_defaults_once();
        return current_user_can('manage_options') || current_user_can(self::TAKE_ATTENDANCE);
    }

    public static function can_view_events(): bool
    {
        self::reconcile_role_defaults_once();
        return current_user_can('manage_options') || current_user_can(self::VIEW_EVENTS);
    }

    private static function reconcile_role_defaults_once(): void
    {
        if (self::$role_defaults_reconciled) {
            return;
        }

        self::$role_defaults_reconciled = true;
        self::grant_net_control_defaults();
        self::grant_detarc_member_defaults();
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

        self::grant_net_control_defaults();
        self::grant_detarc_member_defaults();
    }

    public static function grant_net_control_defaults(): void
    {
        $net_control = get_role(self::NET_CONTROL_ROLE_SLUG);
        if ($net_control) {
            $net_control->add_cap(self::IMPORT);
            $net_control->add_cap(self::TAKE_ATTENDANCE);
            $net_control->add_cap(self::VIEW_EVENTS);
            $net_control->add_cap(self::VIEW_REPORTS);
        }
    }

    public static function grant_detarc_member_defaults(): void
    {
        $detarc_member = get_role(self::DETARC_MEMBER_ROLE_SLUG);
        if ($detarc_member) {
            $detarc_member->add_cap(self::VIEW_EVENTS);
            $detarc_member->add_cap(self::VIEW_REPORTS);
            $detarc_member->remove_cap(self::IMPORT);
            $detarc_member->remove_cap(self::TAKE_ATTENDANCE);
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
        $role_slugs = array_values(array_intersect(array_map('sanitize_key', $role_slugs), [self::NET_CONTROL_ROLE_SLUG]));

        foreach ($editable_roles as $role_slug) {
            $role = get_role($role_slug);
            if (!$role) {
                continue;
            }

            if ($role_slug === 'administrator' || $role_slug === self::NET_CONTROL_ROLE_SLUG) {
                $role->add_cap(self::IMPORT);
            } else {
                $role->remove_cap(self::IMPORT);
            }
        }

        update_option('net_attendance_logger_import_role_slugs', $role_slugs, false);
    }
}
