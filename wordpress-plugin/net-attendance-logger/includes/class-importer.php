<?php

namespace Net_Attendance_Logger;

if (!defined('ABSPATH')) {
    exit;
}

final class Importer
{
    private Repository $repository;

    public function __construct(?Repository $repository = null)
    {
        $this->repository = $repository ?: new Repository();
    }

    public function validate(array|string $payload): array
    {
        $normalized = $this->normalize_payload($payload);
        if (!$normalized['ok']) {
            return $normalized;
        }

        return $this->process($normalized['payload'], true);
    }

    public function import(array|string $payload, bool $dry_run = false): array
    {
        $normalized = $this->normalize_payload($payload);
        if (!$normalized['ok']) {
            return $normalized;
        }

        return $this->process($normalized['payload'], $dry_run);
    }

    private function result(bool $dry_run): array
    {
        return [
            'ok' => true,
            'dry_run' => $dry_run,
            'event_id' => null,
            'event_ids' => [],
            'created' => ['events' => 0, 'participants' => 0, 'records' => 0],
            'updated' => ['events' => 0, 'participants' => 0, 'records' => 0],
            'errors' => [],
        ];
    }

    private function normalize_payload(array|string $payload): array
    {
        if (is_string($payload)) {
            $decoded = json_decode($payload, true);
            if (!is_array($decoded)) {
                return $this->error('malformed JSON payload');
            }
            $payload = $decoded;
        }

        if (isset($payload['events']) && is_array($payload['events'])) {
            $payload['events'] = array_map(function ($event_payload) {
                if (is_array($event_payload) && isset($event_payload['session']) && !isset($event_payload['event'])) {
                    return $this->from_net_logger_payload($event_payload);
                }
                return $event_payload;
            }, $payload['events']);
        }

        if (isset($payload['session']) && !isset($payload['event'])) {
            $payload = $this->from_net_logger_payload($payload);
        }

        return ['ok' => true, 'payload' => $payload, 'errors' => []];
    }

    private function process(array $payload, bool $dry_run): array
    {
        if (isset($payload['events']) && is_array($payload['events'])) {
            return $this->process_batch($payload['events'], $dry_run);
        }

        $errors = $this->validate_payload($payload);
        if ($errors) {
            return [
                'ok' => false,
                'dry_run' => $dry_run,
                'event_id' => null,
                'created' => ['events' => 0, 'participants' => 0, 'records' => 0],
                'updated' => ['events' => 0, 'participants' => 0, 'records' => 0],
                'errors' => $errors,
            ];
        }

        $attendance = $payload['attendance'] ?? [];
        $result = $this->result($dry_run);
        $result['created']['events'] = $dry_run ? 1 : 0;
        $result['created']['participants'] = $dry_run ? count($attendance) : 0;
        $result['created']['records'] = $dry_run ? count($attendance) : 0;

        if ($dry_run) {
            return $result;
        }

        $event = $this->build_event($payload);
        $event_id = $this->repository->upsert_event($event);
        $result['event_id'] = $event_id;
        $result['event_ids'][] = $event_id;
        $result['created']['events'] = 1;

        foreach ($attendance as $item) {
            $participant = $item['participant'] ?? [];
            $participant['source'] = $participant['source'] ?? ($payload['source'] ?? 'import');
            $participant_id = $this->repository->upsert_participant($participant);
            $record = $this->build_record($item);
            $this->repository->upsert_attendance_record($event_id, $participant_id, $record);
            $result['created']['participants']++;
            $result['created']['records']++;
        }

        return $result;
    }

    private function process_batch(array $events, bool $dry_run): array
    {
        $batch_result = $this->result($dry_run);

        if ($events === []) {
            $batch_result['ok'] = false;
            $batch_result['errors'][] = 'events array must include at least one event';
            return $batch_result;
        }

        foreach ($events as $index => $event_payload) {
            if (!is_array($event_payload)) {
                $batch_result['ok'] = false;
                $batch_result['errors'][] = "events row {$index} must be an object";
                continue;
            }

            $result = $this->process($event_payload, $dry_run);
            if (!$result['ok']) {
                $batch_result['ok'] = false;
                foreach ($result['errors'] as $error) {
                    $batch_result['errors'][] = "event {$index}: {$error}";
                }
                continue;
            }

            if (!empty($result['event_id'])) {
                $batch_result['event_id'] = $result['event_id'];
                $batch_result['event_ids'][] = $result['event_id'];
            }

            foreach (['events', 'participants', 'records'] as $key) {
                $batch_result['created'][$key] += (int) ($result['created'][$key] ?? 0);
                $batch_result['updated'][$key] += (int) ($result['updated'][$key] ?? 0);
            }
        }

        return $batch_result;
    }

    private function validate_payload(array $payload): array
    {
        $errors = [];
        $event = $payload['event'] ?? null;
        if (!is_array($event)) {
            $errors[] = 'event object is required';
            return $errors;
        }

        if (trim((string) ($event['name'] ?? '')) === '') {
            $errors[] = 'event name is required';
        }

        $attendance = $payload['attendance'] ?? [];
        if (!is_array($attendance)) {
            $errors[] = 'attendance must be an array';
            return $errors;
        }

        foreach ($attendance as $index => $item) {
            if (!is_array($item)) {
                $errors[] = "attendance row {$index} must be an object";
                continue;
            }
            $participant = $item['participant'] ?? null;
            if (!is_array($participant)) {
                $errors[] = "attendance row {$index} participant object is required";
                continue;
            }
            $has_identity = trim((string) ($participant['callsign'] ?? '')) !== ''
                || trim((string) ($participant['name'] ?? '')) !== ''
                || trim((string) ($participant['external_id'] ?? '')) !== '';
            if (!$has_identity) {
                $errors[] = "attendance row {$index} participant identity is required";
            }
        }

        return $errors;
    }

    private function build_event(array $payload): array
    {
        $event = $payload['event'];
        $event['source'] = $payload['source'] ?? ($event['source'] ?? 'import');
        $event['external_id'] = $payload['external_id'] ?? ($event['external_id'] ?? null);
        $event['metadata'] = $event['metadata'] ?? ['original_source' => $payload['source'] ?? 'import'];
        return $event;
    }

    private function build_record(array $item): array
    {
        return [
            'sequence' => $item['sequence'] ?? null,
            'checked_in_at' => $item['checked_in_at'] ?? null,
            'status' => $item['status'] ?? 'present',
            'role' => $item['role'] ?? null,
            'traffic' => $item['traffic'] ?? false,
            'traffic_details' => $item['traffic_details'] ?? null,
            'notes' => $item['notes'] ?? null,
            'metadata' => $item['metadata'] ?? null,
        ];
    }

    private function from_net_logger_payload(array $payload): array
    {
        $session = $payload['session'] ?? [];
        $checkins = $payload['checkins'] ?? [];
        $attendance = [];
        foreach ($checkins as $checkin) {
            $attendance[] = [
                'sequence' => $checkin['sequence'] ?? null,
                'checked_in_at' => $checkin['checked_in_at'] ?? null,
                'status' => 'present',
                'role' => (($checkin['station']['callsign'] ?? '') === ($session['net_control'] ?? '')) ? 'net_control' : null,
                'traffic' => $checkin['traffic'] ?? false,
                'traffic_details' => $checkin['traffic_details'] ?? '',
                'notes' => $checkin['notes'] ?? '',
                'participant' => $checkin['station'] ?? [],
                'metadata' => ['net_logger_checkin_id' => $checkin['id'] ?? null],
            ];
        }

        return [
            'source' => $payload['source'] ?? 'net_logger',
            'external_id' => (string) ($session['id'] ?? ''),
            'event' => [
                'name' => $session['name'] ?? 'Imported Net',
                'event_type' => 'Repeater Net',
                'frequency' => $session['frequency'] ?? null,
                'net_control' => $session['net_control'] ?? null,
                'status' => $session['status'] ?? 'closed',
                'started_at' => $session['started_at'] ?? null,
                'ended_at' => $session['closed_at'] ?? null,
                'metadata' => ['net_logger_session' => $session],
            ],
            'attendance' => $attendance,
        ];
    }

    private function error(string $message): array
    {
        return [
            'ok' => false,
            'dry_run' => false,
            'event_id' => null,
            'created' => ['events' => 0, 'participants' => 0, 'records' => 0],
            'updated' => ['events' => 0, 'participants' => 0, 'records' => 0],
            'errors' => [$message],
        ];
    }
}
