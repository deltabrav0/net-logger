# Net Logger Release Notes

## v0.1.2

Release date: 2026-07-21

### Fixed

- Fixed Windows FCC database updates so downloaded FCC files are written under the current user's Net Logger data directory instead of a developer-specific `/Users/dbutler/...` path.

## v0.1.1

Release date: 2026-07-21

### Added

- Added Windows native-installer packaging scaffolding: a desktop launcher command, PyInstaller spec, Inno Setup script, and installer-first Windows documentation.
- Added FCC lookup preview text to the station lookup hint. When an entered callsign is not already in Known Stations, Net Logger now previews either `New station: ...` from the local FCC database or `Unknown station: ...` before the operator presses Enter or clicks Find / Check in.

### Changed

- Station lookup preview remains non-destructive: FCC preview lookups do not create station records. Records are still created only after the operator submits the lookup/check-in action.

## v0.1.0

Initial public application baseline.
