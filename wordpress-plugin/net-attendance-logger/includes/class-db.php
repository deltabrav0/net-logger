<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class DB
{
    public const EVENTS = 'net_attendance_events';
    public const PARTICIPANTS = 'net_attendance_participants';
    public const RECORDS = 'net_attendance_records';

    public static function table_name(string $table): string
    {
        global $wpdb;
        return $wpdb->prefix . $table;
    }

    public static function events_table(): string
    {
        return self::table_name(self::EVENTS);
    }

    public static function participants_table(): string
    {
        return self::table_name(self::PARTICIPANTS);
    }

    public static function records_table(): string
    {
        return self::table_name(self::RECORDS);
    }

    /**
     * Return dbDelta-compatible CREATE TABLE statements for the plugin schema.
     *
     * @return string[]
     */
    public static function schema_sql(): array
    {
        global $wpdb;

        $charset_collate = $wpdb->get_charset_collate();
        $events = self::events_table();
        $participants = self::participants_table();
        $records = self::records_table();

        return [
            "CREATE TABLE {$events} (
                id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
                external_id varchar(191) NULL,
                source varchar(64) NOT NULL DEFAULT 'manual',
                event_type varchar(100) NULL,
                name varchar(191) NOT NULL,
                status varchar(32) NOT NULL DEFAULT 'closed',
                started_at datetime NULL,
                ended_at datetime NULL,
                frequency varchar(100) NULL,
                band varchar(64) NULL,
                mode varchar(64) NULL,
                repeater varchar(191) NULL,
                net_control varchar(32) NULL,
                location varchar(191) NULL,
                summary_only tinyint(1) NOT NULL DEFAULT 0,
                aggregate_attendance_count int(10) unsigned NULL,
                notes longtext NULL,
                metadata longtext NULL,
                created_at datetime NOT NULL,
                updated_at datetime NOT NULL,
                PRIMARY KEY  (id),
                KEY source_external_id (source, external_id),
                KEY started_at (started_at),
                KEY event_type (event_type),
                KEY net_control (net_control)
            ) {$charset_collate};",
            "CREATE TABLE {$participants} (
                id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
                external_id varchar(191) NULL,
                source varchar(64) NOT NULL DEFAULT 'manual',
                callsign varchar(32) NULL,
                name varchar(191) NULL,
                first_name varchar(100) NULL,
                last_name varchar(100) NULL,
                city varchar(100) NULL,
                state varchar(32) NULL,
                grid varchar(16) NULL,
                lat decimal(10,7) NULL,
                lon decimal(10,7) NULL,
                organization varchar(191) NULL,
                member_number varchar(100) NULL,
                notes longtext NULL,
                metadata longtext NULL,
                created_at datetime NOT NULL,
                updated_at datetime NOT NULL,
                PRIMARY KEY  (id),
                KEY callsign (callsign),
                KEY source_external_id (source, external_id),
                KEY name (name),
                KEY state (state)
            ) {$charset_collate};",
            "CREATE TABLE {$records} (
                id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
                event_id bigint(20) unsigned NOT NULL,
                participant_id bigint(20) unsigned NOT NULL,
                sequence int(10) unsigned NULL,
                checked_in_at datetime NULL,
                status varchar(32) NOT NULL DEFAULT 'present',
                role varchar(64) NULL,
                traffic tinyint(1) NOT NULL DEFAULT 0,
                traffic_details longtext NULL,
                notes longtext NULL,
                metadata longtext NULL,
                created_at datetime NOT NULL,
                updated_at datetime NOT NULL,
                PRIMARY KEY  (id),
                UNIQUE KEY event_participant (event_id, participant_id),
                KEY event_id (event_id),
                KEY participant_id (participant_id),
                KEY checked_in_at (checked_in_at),
                KEY status (status),
                KEY traffic (traffic)
            ) {$charset_collate};",
        ];
    }
}
