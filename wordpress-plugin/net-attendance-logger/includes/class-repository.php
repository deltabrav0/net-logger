<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class Repository
{
    public function upsert_event(array $event): int
    {
        global $wpdb;
        $table = DB::events_table();
        $now = current_time('mysql');
        $source = $this->text($event['source'] ?? 'manual', 64) ?: 'manual';
        $external_id = $this->nullable_text($event['external_id'] ?? null, 191);
        $existing_id = null;

        if ($external_id !== null && $external_id !== '') {
            $existing_id = $wpdb->get_var($wpdb->prepare(
                "SELECT id FROM {$table} WHERE source = %s AND external_id = %s LIMIT 1",
                $source,
                $external_id
            ));
        }

        $data = [
            'external_id' => $external_id,
            'source' => $source,
            'event_type' => $this->nullable_text($event['event_type'] ?? null, 100),
            'name' => $this->text($event['name'] ?? '', 191),
            'status' => $this->text($event['status'] ?? 'closed', 32) ?: 'closed',
            'started_at' => $this->nullable_datetime($event['started_at'] ?? null),
            'ended_at' => $this->nullable_datetime($event['ended_at'] ?? null),
            'frequency' => $this->nullable_text($event['frequency'] ?? null, 100),
            'band' => $this->nullable_text($event['band'] ?? null, 64),
            'mode' => $this->nullable_text($event['mode'] ?? null, 64),
            'repeater' => $this->nullable_text($event['repeater'] ?? null, 191),
            'net_control' => $this->normalize_callsign($event['net_control'] ?? null),
            'location' => $this->nullable_text($event['location'] ?? null, 191),
            'notes' => $this->nullable_longtext($event['notes'] ?? null),
            'metadata' => $this->encode_metadata($event['metadata'] ?? null),
            'updated_at' => $now,
        ];

        if ($existing_id) {
            $wpdb->update($table, $data, ['id' => (int) $existing_id]);
            return (int) $existing_id;
        }

        $data['created_at'] = $now;
        $wpdb->insert($table, $data);
        return (int) $wpdb->insert_id;
    }

    public function upsert_participant(array $participant): int
    {
        global $wpdb;
        $table = DB::participants_table();
        $now = current_time('mysql');
        $source = $this->text($participant['source'] ?? 'manual', 64) ?: 'manual';
        $external_id = $this->nullable_text($participant['external_id'] ?? null, 191);
        $callsign = $this->normalize_callsign($participant['callsign'] ?? null);
        $existing_id = null;

        if ($callsign !== null && $callsign !== '') {
            $existing_id = $wpdb->get_var($wpdb->prepare(
                "SELECT id FROM {$table} WHERE callsign = %s LIMIT 1",
                $callsign
            ));
        }

        if (!$existing_id && $external_id !== null && $external_id !== '') {
            $existing_id = $wpdb->get_var($wpdb->prepare(
                "SELECT id FROM {$table} WHERE source = %s AND external_id = %s LIMIT 1",
                $source,
                $external_id
            ));
        }

        $data = [
            'external_id' => $external_id,
            'source' => $source,
            'callsign' => $callsign,
            'name' => $this->nullable_text($participant['name'] ?? null, 191),
            'first_name' => $this->nullable_text($participant['first_name'] ?? null, 100),
            'last_name' => $this->nullable_text($participant['last_name'] ?? null, 100),
            'city' => $this->nullable_text($participant['city'] ?? null, 100),
            'state' => $this->nullable_text(isset($participant['state']) ? strtoupper((string) $participant['state']) : null, 32),
            'grid' => $this->nullable_text(isset($participant['grid']) ? strtoupper((string) $participant['grid']) : null, 16),
            'lat' => $this->nullable_float($participant['lat'] ?? null),
            'lon' => $this->nullable_float($participant['lon'] ?? null),
            'organization' => $this->nullable_text($participant['organization'] ?? null, 191),
            'member_number' => $this->nullable_text($participant['member_number'] ?? null, 100),
            'notes' => $this->nullable_longtext($participant['notes'] ?? null),
            'metadata' => $this->encode_metadata($participant['metadata'] ?? null),
            'updated_at' => $now,
        ];

        if ($existing_id) {
            $wpdb->update($table, $data, ['id' => (int) $existing_id]);
            return (int) $existing_id;
        }

        $data['created_at'] = $now;
        $wpdb->insert($table, $data);
        return (int) $wpdb->insert_id;
    }

    public function upsert_attendance_record(int $event_id, int $participant_id, array $record): int
    {
        global $wpdb;
        $table = DB::records_table();
        $now = current_time('mysql');
        $existing_id = $wpdb->get_var($wpdb->prepare(
            "SELECT id FROM {$table} WHERE event_id = %d AND participant_id = %d LIMIT 1",
            $event_id,
            $participant_id
        ));

        $data = [
            'event_id' => $event_id,
            'participant_id' => $participant_id,
            'sequence' => isset($record['sequence']) ? absint($record['sequence']) : null,
            'checked_in_at' => $this->nullable_datetime($record['checked_in_at'] ?? null),
            'status' => $this->text($record['status'] ?? 'present', 32) ?: 'present',
            'role' => $this->nullable_text($record['role'] ?? null, 64),
            'traffic' => !empty($record['traffic']) ? 1 : 0,
            'traffic_details' => $this->nullable_longtext($record['traffic_details'] ?? null),
            'notes' => $this->nullable_longtext($record['notes'] ?? null),
            'metadata' => $this->encode_metadata($record['metadata'] ?? null),
            'updated_at' => $now,
        ];

        if ($existing_id) {
            $wpdb->update($table, $data, ['id' => (int) $existing_id]);
            return (int) $existing_id;
        }

        $data['created_at'] = $now;
        $wpdb->insert($table, $data);
        return (int) $wpdb->insert_id;
    }

    public function get_event(int $event_id): ?array
    {
        global $wpdb;
        $row = $wpdb->get_row($wpdb->prepare(
            'SELECT * FROM ' . DB::events_table() . ' WHERE id = %d',
            $event_id
        ), ARRAY_A);
        return $row ?: null;
    }

    public function get_event_attendance(int $event_id): array
    {
        global $wpdb;
        $records = DB::records_table();
        $participants = DB::participants_table();
        return $wpdb->get_results($wpdb->prepare(
            "SELECT r.*, p.callsign, p.name, p.city, p.state, p.grid
             FROM {$records} r
             JOIN {$participants} p ON p.id = r.participant_id
             WHERE r.event_id = %d
             ORDER BY COALESCE(r.sequence, 999999), p.callsign, p.name",
            $event_id
        ), ARRAY_A) ?: [];
    }

    public function list_events(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        return $wpdb->get_results(
            "SELECT e.*, COUNT(r.id) AS attendance_count,
                    COALESCE(SUM(CASE WHEN r.traffic = 1 THEN 1 ELSE 0 END), 0) AS traffic_count
             FROM {$events} e
             LEFT JOIN {$records} r ON r.event_id = e.id
             GROUP BY e.id
             ORDER BY e.started_at DESC, e.id DESC",
            ARRAY_A
        ) ?: [];
    }

    public function report_attendance_over_time(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        return $wpdb->get_results(
            "SELECT DATE(e.started_at) AS event_date, COUNT(r.id) AS attendance_count
             FROM {$events} e
             LEFT JOIN {$records} r ON r.event_id = e.id
             GROUP BY DATE(e.started_at)
             ORDER BY event_date ASC",
            ARRAY_A
        ) ?: [];
    }

    public function report_top_participants(array $args = []): array
    {
        global $wpdb;
        $records = DB::records_table();
        $participants = DB::participants_table();
        return $wpdb->get_results(
            "SELECT p.id, p.callsign, p.name, COUNT(r.id) AS attendance_count
             FROM {$participants} p
             JOIN {$records} r ON r.participant_id = p.id
             GROUP BY p.id
             ORDER BY attendance_count DESC, p.callsign, p.name
             LIMIT 25",
            ARRAY_A
        ) ?: [];
    }

    public function list_event_names(): array
    {
        global $wpdb;
        $events = DB::events_table();
        $rows = $wpdb->get_col("SELECT DISTINCT name FROM {$events} WHERE name <> '' ORDER BY name ASC");
        return array_values(array_filter(array_map('strval', $rows ?: [])));
    }

    public function report_attendance_series(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $period = $this->report_period($args['period'] ?? 'month');
        $event_name = $this->nullable_text($args['event_name'] ?? null, 191);
        $date_value = "COALESCE(r.checked_in_at, e.started_at)";
        $bucket_exprs = [
            'day' => "DATE({$date_value})",
            'week' => "DATE_FORMAT({$date_value}, '%x-W%v')",
            'month' => "DATE_FORMAT({$date_value}, '%Y-%m')",
            'year' => "DATE_FORMAT({$date_value}, '%Y')",
        ];
        $bucket_expr = $bucket_exprs[$period];
        $where = "WHERE {$date_value} IS NOT NULL";
        $params = [];
        if ($event_name !== null && $event_name !== '') {
            $where .= ' AND e.name = %s';
            $params[] = $event_name;
        }

        $sql = "SELECT e.name AS event_name,
                       {$bucket_expr} AS bucket,
                       COUNT(r.id) AS attendance_count,
                       COALESCE(SUM(CASE WHEN r.traffic = 1 THEN 1 ELSE 0 END), 0) AS traffic_count
                FROM {$records} r
                JOIN {$events} e ON e.id = r.event_id
                {$where}
                GROUP BY e.name, bucket
                ORDER BY e.name ASC, bucket ASC";
        if ($params) {
            $sql = $wpdb->prepare($sql, ...$params);
        }
        return $wpdb->get_results($sql, ARRAY_A) ?: [];
    }

    public function report_attendance_totals_by_event_name(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $event_name = $this->nullable_text($args['event_name'] ?? null, 191);
        $where = '';
        $params = [];
        if ($event_name !== null && $event_name !== '') {
            $where = 'WHERE e.name = %s';
            $params[] = $event_name;
        }

        $sql = "SELECT e.name AS event_name,
                       COUNT(r.id) AS attendance_count,
                       COALESCE(SUM(CASE WHEN r.traffic = 1 THEN 1 ELSE 0 END), 0) AS traffic_count
                FROM {$events} e
                LEFT JOIN {$records} r ON r.event_id = e.id
                {$where}
                GROUP BY e.name
                ORDER BY attendance_count DESC, e.name ASC";
        if ($params) {
            $sql = $wpdb->prepare($sql, ...$params);
        }
        return $wpdb->get_results($sql, ARRAY_A) ?: [];
    }

    public function close_event(int $event_id): bool
    {
        global $wpdb;
        $updated = $wpdb->update(
            DB::events_table(),
            [
                'status' => 'closed',
                'ended_at' => current_time('mysql'),
                'updated_at' => current_time('mysql'),
            ],
            ['id' => $event_id]
        );
        return $updated !== false;
    }

    public function reopen_event(int $event_id): bool
    {
        global $wpdb;
        $updated = $wpdb->update(
            DB::events_table(),
            [
                'status' => 'open',
                'ended_at' => null,
                'updated_at' => current_time('mysql'),
            ],
            ['id' => $event_id]
        );
        return $updated !== false;
    }

    public function delete_event(int $event_id): bool
    {
        global $wpdb;
        $wpdb->delete(DB::records_table(), ['event_id' => $event_id]);
        $deleted = $wpdb->delete(DB::events_table(), ['id' => $event_id]);
        return $deleted !== false && $deleted > 0;
    }

    public function list_participants(array $args = []): array
    {
        global $wpdb;
        $participants = DB::participants_table();
        $q = $this->nullable_text($args['q'] ?? null, 100);
        $limit = isset($args['limit']) ? max(1, min(200, absint($args['limit']))) : 50;
        $where = '';
        $params = [];
        if ($q !== null && $q !== '') {
            $like = '%' . $wpdb->esc_like($q) . '%';
            $where = 'WHERE callsign LIKE %s OR name LIKE %s';
            $params[] = $like;
            $params[] = $like;
        }
        $sql = "SELECT * FROM {$participants} {$where} ORDER BY callsign, name LIMIT %d";
        $params[] = $limit;
        return $wpdb->get_results($wpdb->prepare($sql, ...$params), ARRAY_A) ?: [];
    }

    public function next_attendance_sequence(int $event_id): int
    {
        global $wpdb;
        $records = DB::records_table();
        return (int) $wpdb->get_var($wpdb->prepare(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM {$records} WHERE event_id = %d",
            $event_id
        ));
    }

    public function update_attendance_record(int $record_id, array $record): bool
    {
        global $wpdb;
        $data = ['updated_at' => current_time('mysql')];
        if (array_key_exists('traffic', $record)) {
            $data['traffic'] = !empty($record['traffic']) ? 1 : 0;
        }
        if (array_key_exists('traffic_details', $record)) {
            $data['traffic_details'] = $this->nullable_longtext($record['traffic_details']);
        }
        if (array_key_exists('notes', $record)) {
            $data['notes'] = $this->nullable_longtext($record['notes']);
        }
        if (array_key_exists('role', $record)) {
            $data['role'] = $this->nullable_text($record['role'], 64);
        }
        $updated = $wpdb->update(DB::records_table(), $data, ['id' => $record_id]);
        return $updated !== false;
    }

    public function delete_attendance_record(int $record_id): bool
    {
        global $wpdb;
        $deleted = $wpdb->delete(DB::records_table(), ['id' => $record_id]);
        return $deleted !== false && $deleted > 0;
    }

    private function report_period(mixed $value): string
    {
        $period = strtolower(sanitize_key((string) ($value ?: 'month')));
        return in_array($period, ['day', 'week', 'month', 'year'], true) ? $period : 'month';
    }

    private function normalize_callsign(mixed $value): ?string
    {
        $text = strtoupper(preg_replace('/\s+/', '', (string) ($value ?? '')));
        return $text === '' ? null : substr($text, 0, 32);
    }

    private function text(mixed $value, int $max): string
    {
        return substr(sanitize_text_field((string) ($value ?? '')), 0, $max);
    }

    private function nullable_text(mixed $value, int $max): ?string
    {
        $text = $this->text($value, $max);
        return $text === '' ? null : $text;
    }

    private function nullable_longtext(mixed $value): ?string
    {
        if ($value === null) {
            return null;
        }
        $text = wp_kses_post((string) $value);
        return $text === '' ? null : $text;
    }

    private function nullable_datetime(mixed $value): ?string
    {
        if (!$value) {
            return null;
        }
        $timestamp = strtotime((string) $value);
        return $timestamp ? gmdate('Y-m-d H:i:s', $timestamp) : null;
    }

    private function nullable_float(mixed $value): ?float
    {
        return is_numeric($value) ? (float) $value : null;
    }

    private function encode_metadata(mixed $metadata): ?string
    {
        if ($metadata === null || $metadata === '') {
            return null;
        }
        return wp_json_encode($metadata);
    }
}
