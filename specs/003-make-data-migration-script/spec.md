# Feature Specification: Make-Data Migration Script

**Feature Branch**: `003-make-data-migration-script`
**Created**: 2026-04-21
**Status**: Draft
**Input**: User description: "modify the make_data.py script to run the migration and put the logged output in a file named clone_content_yymmddhhmm.log in ./data/logs. Source and destination should be read from the config."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Run Content Migration from the Command Line (Priority: P1)

An operator runs `make_data.py` to execute a full portal content migration from source to
destination. The script bootstraps logging, reads the portal environment names from
`config.yml`, delegates all migration work to the package's migration function, and writes a
complete audit trail to a timestamped log file in `data/logs/`.

**Why this priority**: This is the core deliverable — the script is the primary entry point
operators use to trigger migrations. Without it the `migrate_content()` function has no
runnable shell.

**Independent Test**: Can be tested by executing `python scripts/make_data.py`, confirming
the process completes without error, and verifying that a file named
`clone_content_YYMMDDHHMM.log` exists in `data/logs/` with migration log lines inside.

**Acceptance Scenarios**:

1. **Given** valid portal credentials in `secrets.yml` and reachable source and destination
   portals, **When** the script is executed, **Then** the migration runs end-to-end and a
   timestamped log file is created in `data/logs/`.
2. **Given** the `data/logs/` directory does not exist, **When** the script is executed,
   **Then** the directory is created automatically before the log file is written.
3. **Given** a migration that encounters per-item clone failures, **When** the script
   completes, **Then** the log file records each failure and the script exits without raising
   an unhandled exception (per-item failures are non-fatal).

---

### User Story 2 — Configure Source and Destination Without Touching the Script (Priority: P2)

An operator changes which portals are used as source and destination by editing `config.yml`
only, with no modification to `scripts/make_data.py`.

**Why this priority**: Hardcoding environment names in the script breaks the configuration-
driven contract of the project. Operators must be able to re-point the migration to different
portals by changing a single config value.

**Independent Test**: Can be tested by editing `config.yml` to set different environment
names under `migration.source_env` and `migration.destination_env`, re-running the script,
and confirming the log file records the updated portal URLs.

**Acceptance Scenarios**:

1. **Given** `migration.source_env` is set to a custom environment name in `config.yml`,
   **When** the script is run, **Then** the migration reads credentials for that environment
   name from `secrets.yml` rather than using a hardcoded default.
2. **Given** `migration.source_env` and `migration.destination_env` are absent from
   `config.yml`, **When** the script is run, **Then** the script falls back to the built-in
   defaults (`"source"` and `"destination"`) without error.

---

### Edge Cases

- What happens if `data/logs/` does not exist?
  Response: The directory is created automatically before the log file is written.
- What happens if the migration pre-flight fails (e.g., bad credentials)?
  Response: The error is logged to the log file before the script exits with a non-zero
  status; the log file still captures the failure detail.
- What if `migration.source_env` is present in config but has no matching entry in
  `secrets.yml`?
  Response: The migration function raises `KeyError`; the script logs the error and exits
  with a non-zero status.
- What happens if a prior log file exists with the same timestamp?
  Response: Not possible in practice — the timestamp includes minute-level precision and the
  script runs once per invocation. No deduplication logic is required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `scripts/make_data.py` MUST invoke `migrate_content()` from the
  `arcgis_cloning` package when executed, passing no business logic of its own — the script
  is a thin entry point only.
- **FR-002**: The script MUST write all log output to a file at
  `data/logs/clone_content_YYMMDDHHMM.log`, where `YY` is the two-digit year, `MM` the
  two-digit month, `DD` the two-digit day, `HH` the two-digit hour, and `MM` the two-digit
  minute of script execution. The file MUST be created fresh on every run.
- **FR-003**: The `data/logs/` directory MUST be created by the script if it does not already
  exist, before any log output is written.
- **FR-004**: The source portal environment name and destination portal environment name MUST
  be read from `config.yml` under a `migration` key (`migration.source_env` and
  `migration.destination_env`). When these keys are absent, the script MUST fall back to the
  built-in defaults (`"source"` and `"destination"`).
- **FR-005**: `config.yml` MUST be updated to include a `migration` section under
  `environments.default` with `source_env: "source"` and `destination_env: "destination"` as
  the default values, so the keys are discoverable without requiring operators to read source
  code.
- **FR-006**: The script MUST log at `INFO` level both when it starts (including the resolved
  source and destination environment names) and when it finishes (including the final
  `MigrationResult` counts: migrated, skipped, failed). On a pre-flight failure, the script
  MUST log only the CRITICAL error message; no `MigrationResult` summary is produced or
  logged because no result exists at that point.
- **FR-007**: The log file MUST capture all log levels produced by `migrate_content()` (DEBUG
  through CRITICAL), providing a complete audit trail of the migration in the file even if
  only INFO-level messages are shown in the console.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Executing `python scripts/make_data.py` produces a file at
  `data/logs/clone_content_YYMMDDHHMM.log` with content on every run.
- **SC-002**: The log file contains a start banner, per-item progress lines, and a completion
  summary with migrated/skipped/failed counts — sufficient to audit the migration without
  additional tooling.
- **SC-003**: Changing `migration.source_env` in `config.yml` and re-running the script
  connects to the newly specified portal with no code changes.
- **SC-004**: The script produces exit code `0` on successful migration (even if individual
  items fail) and a non-zero exit code on pre-flight failure.

## Assumptions

- `migrate_content()` is already implemented and exported from the `arcgis_cloning` package
  (Feature 002). This script only wires it to the command-line entry point.
- The ArcGIS Pro conda environment (or equivalent) is active when the script is run; all
  portal connectivity dependencies are satisfied by the environment.
- Both portal credentials (`secrets.yml`) are configured before the script is run;
  credential management is out of scope for this feature.
- The `migration` config section is added under `environments.default`, meaning it applies
  universally unless overridden at the environment level.
- The existing sample/example code block in `make_data.py` (ArcPy / GeoAccessor processing)
  is replaced entirely by the migration invocation.
- Log level for the file handler is `DEBUG` (captures everything); log level for the console
  handler follows `config.logging.level` from the active environment.

- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]

## Assumptions

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right assumptions based on reasonable defaults
  chosen when the feature description did not specify certain details.
-->

- [Assumption about target users, e.g., "Users have stable internet connectivity"]
- [Assumption about scope boundaries, e.g., "Mobile support is out of scope for v1"]
- [Assumption about data/environment, e.g., "Existing authentication system will be reused"]
- [Dependency on existing system/service, e.g., "Requires access to the existing user profile API"]
