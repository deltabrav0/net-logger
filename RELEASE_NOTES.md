# Net Logger Release Notes

## v0.1.1

Release date: 2026-07-21

### Added

- Added FCC lookup preview text to the station lookup hint. When an entered callsign is not already in Known Stations, Net Logger now previews either `New station: ...` from the local FCC database or `Unknown station: ...` before the operator presses Enter or clicks Find / Check in.

### Changed

- Station lookup preview remains non-destructive: FCC preview lookups do not create station records. Records are still created only after the operator submits the lookup/check-in action.

## v0.1.0

Initial public application baseline.
