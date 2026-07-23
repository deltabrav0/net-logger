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
            'summary_only' => !empty($event['summary_only']) ? 1 : 0,
            'aggregate_attendance_count' => isset($event['aggregate_attendance_count']) ? absint($event['aggregate_attendance_count']) : null,
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
            "SELECT e.*, COALESCE(e.aggregate_attendance_count, COUNT(r.id)) AS attendance_count,
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
            "SELECT DATE(e.started_at) AS event_date,
                    SUM(CASE WHEN e.summary_only = 1 THEN COALESCE(e.aggregate_attendance_count, 0) WHEN r.id IS NULL THEN 0 ELSE 1 END) AS attendance_count
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
        $events = DB::events_table();
        $records = DB::records_table();
        $participants = DB::participants_table();
        [$where, $params] = $this->event_filter_where($args, 'e');
        $limit = isset($args['limit']) ? max(1, min(100, absint($args['limit']))) : 25;
        $sql = "SELECT p.id, p.callsign, p.name, COUNT(r.id) AS attendance_count,
                        MIN(r.checked_in_at) AS first_checkin_at,
                        MAX(r.checked_in_at) AS last_checkin_at
                 FROM {$participants} p
                 JOIN {$records} r ON r.participant_id = p.id
                 JOIN {$events} e ON e.id = r.event_id
                 {$where}
                 GROUP BY p.id
                 ORDER BY attendance_count DESC, last_checkin_at DESC, p.callsign, p.name
                 LIMIT %d";
        $params[] = $limit;
        return $wpdb->get_results($wpdb->prepare($sql, ...$params), ARRAY_A) ?: [];
    }

    public function report_participation_snapshot(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $participants = DB::participants_table();
        [$where, $params] = $this->event_filter_where($args, 'e');
        $sql = "SELECT COUNT(DISTINCT e.id) AS event_count,
                       SUM(CASE WHEN e.summary_only = 1 THEN COALESCE(e.aggregate_attendance_count, 0) WHEN r.id IS NULL THEN 0 ELSE 1 END) AS attendance_count,
                       COUNT(DISTINCT p.id) AS distinct_participants,
                       COALESCE(SUM(CASE WHEN r.traffic = 1 THEN 1 ELSE 0 END), 0) AS traffic_count
                FROM {$events} e
                LEFT JOIN {$records} r ON r.event_id = e.id
                LEFT JOIN {$participants} p ON p.id = r.participant_id
                {$where}";
        if ($params) {
            $sql = $wpdb->prepare($sql, ...$params);
        }
        $row = $wpdb->get_row($sql, ARRAY_A) ?: [];
        $event_count = max(0, (int) ($row['event_count'] ?? 0));
        $attendance_count = max(0, (int) ($row['attendance_count'] ?? 0));
        $row['average_attendance'] = $event_count > 0 ? round($attendance_count / $event_count, 1) : 0;
        return $row;
    }

    public function report_new_participants(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $participants = DB::participants_table();
        [$where, $params] = $this->event_filter_where($args, 'e');
        $limit = isset($args['limit']) ? max(1, min(100, absint($args['limit']))) : 10;
        $sql = "SELECT p.id, p.callsign, p.name, p.city, p.state,
                        MIN(r.checked_in_at) AS first_checkin_at,
                        MAX(r.checked_in_at) AS last_checkin_at,
                        COUNT(r.id) AS attendance_count
                 FROM {$participants} p
                 JOIN {$records} r ON r.participant_id = p.id
                 JOIN {$events} e ON e.id = r.event_id
                 {$where}
                 GROUP BY p.id
                 ORDER BY first_checkin_at DESC, p.callsign, p.name
                 LIMIT %d";
        $params[] = $limit;
        return $wpdb->get_results($wpdb->prepare($sql, ...$params), ARRAY_A) ?: [];
    }

    public function report_participation_milestones(array $args = []): array
    {
        return $this->report_participation_awards($args);
    }

    public function report_participation_awards(array $args = []): array
    {
        $limit = isset($args['limit']) ? max(1, min(100, absint($args['limit']))) : 25;
        $awards = [];

        foreach ($this->report_lifetime_awards($args + ['limit' => $limit]) as $row) {
            $awards[] = $row;
        }
        foreach ($this->report_new_participants($args + ['limit' => $limit]) as $row) {
            $awards[] = $this->award_row($row, 'rookie', 1, __('First recorded check-in', 'net-attendance-logger'));
        }
        foreach ($this->report_net_control_awards($args + ['limit' => $limit]) as $row) {
            $awards[] = $row;
        }
        foreach ($this->report_weekly_streaks($args + ['limit' => $limit]) as $row) {
            $awards[] = $row;
        }

        usort($awards, static function (array $a, array $b): int {
            $priority = ['century' => 10, 'gold' => 20, 'silver' => 30, 'bronze' => 40, 'streak' => 50, 'net_control' => 60, 'rookie' => 70];
            $a_priority = $priority[$a['award_slug'] ?? ''] ?? 99;
            $b_priority = $priority[$b['award_slug'] ?? ''] ?? 99;
            if ($a_priority !== $b_priority) {
                return $a_priority <=> $b_priority;
            }
            $metric = ((int) ($b['metric_value'] ?? 0)) <=> ((int) ($a['metric_value'] ?? 0));
            if ($metric !== 0) {
                return $metric;
            }
            return strcmp((string) ($a['callsign'] ?? ''), (string) ($b['callsign'] ?? ''));
        });

        return array_slice($awards, 0, $limit);
    }

    public function report_weekly_streaks(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $participants = DB::participants_table();
        [$where, $params] = $this->event_filter_where($args, 'e');
        $limit = isset($args['limit']) ? max(1, min(100, absint($args['limit']))) : 25;
        $definitions = self::participation_awards();
        $threshold = (int) ($definitions['streak']['threshold'] ?? 3);
        $sql = "SELECT p.id, p.callsign, p.name,
                        DATE_FORMAT(COALESCE(r.checked_in_at, e.started_at), '%x-W%v') AS iso_week,
                        MAX(COALESCE(r.checked_in_at, e.started_at)) AS last_checkin_at
                 FROM {$participants} p
                 JOIN {$records} r ON r.participant_id = p.id
                 JOIN {$events} e ON e.id = r.event_id
                 {$where}
                 GROUP BY p.id, iso_week
                 ORDER BY p.id ASC, iso_week DESC";
        if ($params) {
            $sql = $wpdb->prepare($sql, ...$params);
        }
        $rows = $wpdb->get_results($sql, ARRAY_A) ?: [];
        $by_participant = [];
        foreach ($rows as $row) {
            $id = (int) ($row['id'] ?? 0);
            if ($id > 0) {
                $by_participant[$id][] = $row;
            }
        }

        $awards = [];
        foreach ($by_participant as $participant_rows) {
            $streak = 0;
            $expected = null;
            foreach ($participant_rows as $row) {
                $week = (string) ($row['iso_week'] ?? '');
                if ($week === '') {
                    continue;
                }
                if ($expected !== null && $week !== $expected) {
                    break;
                }
                $streak++;
                $expected = $this->previous_iso_week($week);
            }
            if ($streak >= $threshold) {
                $awards[] = $this->award_row($participant_rows[0], 'streak', $streak, sprintf(_n('%d consecutive week', '%d consecutive weeks', $streak, 'net-attendance-logger'), $streak));
            }
        }

        usort($awards, static fn(array $a, array $b): int => ((int) ($b['metric_value'] ?? 0)) <=> ((int) ($a['metric_value'] ?? 0)));
        return array_slice($awards, 0, $limit);
    }

    public function report_net_control_awards(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $participants = DB::participants_table();
        [$where, $params] = $this->event_filter_where($args, 'e');
        $limit = isset($args['limit']) ? max(1, min(100, absint($args['limit']))) : 25;
        $sql = "SELECT p.id, p.callsign, p.name, COUNT(DISTINCT e.id) AS net_control_count,
                        MAX(COALESCE(r.checked_in_at, e.started_at)) AS last_checkin_at
                 FROM {$participants} p
                 JOIN {$records} r ON r.participant_id = p.id
                 JOIN {$events} e ON e.id = r.event_id
                 {$where}
                 " . ($where === '' ? 'WHERE' : 'AND') . " (LOWER(r.role) = 'net_control' OR LOWER(p.callsign) = LOWER(e.net_control))
                 GROUP BY p.id
                 HAVING net_control_count >= 1
                 ORDER BY net_control_count DESC, last_checkin_at DESC, p.callsign, p.name
                 LIMIT %d";
        $params[] = $limit;
        $rows = $wpdb->get_results($wpdb->prepare($sql, ...$params), ARRAY_A) ?: [];
        return array_map(fn(array $row): array => $this->award_row($row, 'net_control', (int) ($row['net_control_count'] ?? 0), sprintf(_n('%d session served', '%d sessions served', (int) ($row['net_control_count'] ?? 0), 'net-attendance-logger'), (int) ($row['net_control_count'] ?? 0))), $rows);
    }

    private function report_lifetime_awards(array $args = []): array
    {
        global $wpdb;
        $events = DB::events_table();
        $records = DB::records_table();
        $participants = DB::participants_table();
        [$where, $params] = $this->event_filter_where($args, 'e');
        $limit = isset($args['limit']) ? max(1, min(100, absint($args['limit']))) : 25;
        $sql = "SELECT p.id, p.callsign, p.name, COUNT(r.id) AS attendance_count,
                        MIN(r.checked_in_at) AS first_checkin_at,
                        MAX(r.checked_in_at) AS last_checkin_at
                 FROM {$participants} p
                 JOIN {$records} r ON r.participant_id = p.id
                 JOIN {$events} e ON e.id = r.event_id
                 {$where}
                 GROUP BY p.id
                 HAVING attendance_count >= 10
                 ORDER BY attendance_count DESC, last_checkin_at DESC, p.callsign, p.name
                 LIMIT %d";
        $params[] = $limit;
        $rows = $wpdb->get_results($wpdb->prepare($sql, ...$params), ARRAY_A) ?: [];
        $awards = [];
        foreach ($rows as $row) {
            $count = (int) ($row['attendance_count'] ?? 0);
            $slug = 'bronze';
            foreach (['century', 'gold', 'silver', 'bronze'] as $candidate) {
                $threshold = (int) (self::participation_awards()[$candidate]['threshold'] ?? 0);
                if ($count >= $threshold) {
                    $slug = $candidate;
                    break;
                }
            }
            $awards[] = $this->award_row($row, $slug, $count, sprintf(_n('%d lifetime check-in', '%d lifetime check-ins', $count, 'net-attendance-logger'), $count));
        }
        return $awards;
    }

    private static function participation_awards(): array
    {
        return apply_filters('net_attendance_logger_participation_awards', [
            'bronze' => ['award_slug' => 'bronze', 'award_label' => 'Bronze', 'emoji' => '🥉', 'type' => 'lifetime_checkins', 'threshold' => 10],
            'silver' => ['award_slug' => 'silver', 'award_label' => 'Silver', 'emoji' => '🥈', 'type' => 'lifetime_checkins', 'threshold' => 25],
            'gold' => ['award_slug' => 'gold', 'award_label' => 'Gold', 'emoji' => '🥇', 'type' => 'lifetime_checkins', 'threshold' => 50],
            'century' => ['award_slug' => 'century', 'award_label' => 'Century Club', 'emoji' => '💯', 'type' => 'lifetime_checkins', 'threshold' => 100],
            'rookie' => ['award_slug' => 'rookie', 'award_label' => 'Rookie', 'emoji' => '⭐', 'type' => 'first_checkin'],
            'net_control' => ['award_slug' => 'net_control', 'award_label' => 'Net Control', 'emoji' => '🎙️', 'type' => 'net_control_sessions', 'threshold' => 1],
            'streak' => ['award_slug' => 'streak', 'award_label' => 'Current Streak', 'emoji' => '🔥', 'type' => 'weekly_streak', 'threshold' => 3],
        ]);
    }

    private function award_row(array $row, string $slug, int $metric_value, string $metric_label): array
    {
        $definition = self::participation_awards()[$slug] ?? ['award_label' => ucfirst($slug), 'emoji' => ''];
        return [
            'id' => (int) ($row['id'] ?? 0),
            'callsign' => (string) ($row['callsign'] ?? ''),
            'name' => (string) ($row['name'] ?? ''),
            'award_slug' => $slug,
            'award_label' => (string) ($definition['award_label'] ?? ucfirst($slug)),
            'emoji' => (string) ($definition['emoji'] ?? ''),
            'metric_value' => $metric_value,
            'metric_label' => $metric_label,
            'attendance_count' => (int) ($row['attendance_count'] ?? $metric_value),
            'last_checkin_at' => (string) ($row['last_checkin_at'] ?? ''),
        ];
    }

    private function previous_iso_week(string $week): ?string
    {
        if (!preg_match('/^(\d{4})-W(\d{2})$/', $week, $matches)) {
            return null;
        }
        $date = new \DateTimeImmutable();
        $date = $date->setISODate((int) $matches[1], (int) $matches[2], 1)->modify('-1 week');
        return $date->format('o-\\WW');
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
                       SUM(CASE WHEN e.summary_only = 1 THEN COALESCE(e.aggregate_attendance_count, 0) WHEN r.id IS NULL THEN 0 ELSE 1 END) AS attendance_count,
                       COALESCE(SUM(CASE WHEN r.traffic = 1 THEN 1 ELSE 0 END), 0) AS traffic_count
                FROM {$events} e
                LEFT JOIN {$records} r ON r.event_id = e.id
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
                       SUM(CASE WHEN e.summary_only = 1 THEN COALESCE(e.aggregate_attendance_count, 0) WHEN r.id IS NULL THEN 0 ELSE 1 END) AS attendance_count,
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

    public function update_event(int $event_id, array $event): bool
    {
        global $wpdb;
        $data = ['updated_at' => current_time('mysql')];
        if (array_key_exists('name', $event)) {
            $name = $this->text($event['name'], 191);
            if ($name !== '') {
                $data['name'] = $name;
            }
        }
        if (array_key_exists('event_type', $event)) {
            $data['event_type'] = $this->nullable_text($event['event_type'], 100);
        }
        if (array_key_exists('started_at', $event)) {
            $data['started_at'] = $this->nullable_datetime($event['started_at']);
        }
        if (array_key_exists('ended_at', $event)) {
            $data['ended_at'] = $this->nullable_datetime($event['ended_at']);
        }
        if (array_key_exists('frequency', $event)) {
            $data['frequency'] = $this->nullable_text($event['frequency'], 100);
        }
        if (array_key_exists('net_control', $event)) {
            $data['net_control'] = $this->normalize_callsign($event['net_control']);
        }
        if (array_key_exists('notes', $event)) {
            $data['notes'] = $this->nullable_longtext($event['notes']);
        }
        $updated = $wpdb->update(DB::events_table(), $data, ['id' => $event_id]);
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

    public function create_summary_event(array $event): int
    {
        $count = isset($event['aggregate_attendance_count']) ? absint($event['aggregate_attendance_count']) : 0;
        return $this->upsert_event(array_merge($event, [
            'source' => $event['source'] ?? 'rapid_summary',
            'status' => 'closed',
            'summary_only' => true,
            'aggregate_attendance_count' => $count,
        ]));
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

    private function event_filter_where(array $args, string $event_alias = 'e'): array
    {
        $event_name = $this->nullable_text($args['event_name'] ?? null, 191);
        if ($event_name === null || $event_name === '') {
            return ['', []];
        }
        return ["WHERE {$event_alias}.name = %s", [$event_name]];
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
