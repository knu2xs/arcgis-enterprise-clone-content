# Feature Specification: CSV URL Mapping Output for Migrated Content

**Feature Branch**: `005-csv-url-output`
**Created**: 2026-04-22
**Status**: Draft
**Input**: User description: "Add an optional parameter to output a file of original url and updated url for migrated content in a csv file. This output will be in the same location with the same naming convention as the log file."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Generate a URL Mapping CSV During Migration (Priority: P1)

An operator or developer runs a content migration and opts into CSV output by providing a
file path for the mapping file. After the migration completes, a CSV file exists at the
specified path containing one row per successfully migrated item with the original source URL
and the updated destination URL.

**Why this priority**: This is the entire deliverable — the URL mapping file is the only
artifact this feature introduces, and it has no value without at least one recorded URL pair.

**Independent Test**: Can be tested by running the migration function with the optional CSV
path parameter set to a known writable path, confirming the CSV is created, and verifying
that each row contains the original item URL from the source portal and the corresponding
cloned item URL from the destination portal.

**Acceptance Scenarios**:

1. **Given** valid source and destination connections and at least one item to migrate,
   **When** the migration function is called with the CSV path parameter set,
   **Then** a CSV file is written at the specified path with one row per successfully
   migrated item containing the original URL and the updated URL.
2. **Given** the migration function is called without the CSV path parameter (default),
   **When** the migration completes,
   **Then** no CSV file is created and the function behaves identically to its current
   behaviour.
3. **Given** a migration where some items fail to clone,
   **When** the CSV is written,
   **Then** only successfully migrated items appear in the CSV; skipped and failed items
   are excluded.
4. **Given** a migration where all items are skipped (resume mode, destination already
   complete),
   **When** the migration completes with the CSV path parameter set,
   **Then** an empty CSV (header row only) is written at the specified path.

---

### User Story 2 — Script Automatically Co-locates CSV with Log File (Priority: P2)

An operator running `make_data.py` passes an optional flag to enable CSV output. The script
derives the CSV file path from the same timestamp and directory used for the log file
(`data/logs/clone_content_YYMMDDHHMM.csv`), so both artefacts are co-located and share a
common timestamp for easy correlation.

**Why this priority**: The feature description explicitly requires the CSV to follow the same
location and naming convention as the log file. This user story realises that requirement at
the script level without coupling the migration function to any path convention.

**Independent Test**: Can be tested by running `make_data.py` with the CSV flag enabled,
then confirming both `clone_content_YYMMDDHHMM.log` and `clone_content_YYMMDDHHMM.csv`
exist in `data/logs/` with the same timestamp prefix.

**Acceptance Scenarios**:

1. **Given** the script is invoked with the CSV output flag enabled,
   **When** the migration completes,
   **Then** a CSV file named `clone_content_YYMMDDHHMM.csv` is present in `data/logs/`
   with the same timestamp as the corresponding log file.
2. **Given** the script is invoked without the CSV output flag (default),
   **When** the migration completes,
   **Then** no CSV file is written; only the log file is produced.
3. **Given** the `data/logs/` directory does not exist at the time of invocation,
   **When** the script runs with CSV output enabled,
   **Then** the directory is created before both the CSV and log files are written.

---

### Edge Cases

- What happens when an item is migrated but neither the source nor destination has a URL
  (e.g., a non-service content item such as a PDF or image)?
  Response: Both `original_url` and `updated_url` columns are written as empty strings for
  that row; the row is still included for full auditability.
- What happens when the specified CSV path points to a directory that does not exist?
  Response: The migration function raises a descriptive error before beginning the migration
  loop, so no partial CSV is written.
- What happens when the CSV path is provided but the migration finds no items?
  Response: An empty CSV (header row only) is written and the function returns normally.
- What happens when two source items have the same URL?
  Response: Both rows are written; the CSV records the actual state of each item rather
  than deduplicating.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `migrate_content()` function MUST accept a new optional parameter that
  accepts a file path value or is absent/`None` by default.
- **FR-002**: When the CSV path parameter is provided, the function MUST write a CSV file at
  that path upon migration completion containing one row per successfully migrated item.
- **FR-003**: Each CSV row MUST contain the item name, item type, original item URL (source
  portal), and updated item URL (destination portal after cloning).
- **FR-004**: The CSV file MUST include a header row naming each column.
- **FR-005**: When the CSV path parameter is `None` (default), the function MUST NOT create
  any CSV file and MUST NOT alter any existing behaviour.
- **FR-006**: Skipped items (resume mode) and failed items MUST NOT appear in the CSV; only
  successfully cloned items are recorded.
- **FR-007**: If the parent directory of the provided CSV path does not exist, the function
  MUST raise a descriptive error before the migration begins.
- **FR-008**: The `make_data.py` script MUST support an optional flag that, when set, derives
  the CSV path from the same timestamp and directory as the log file
  (`data/logs/clone_content_YYMMDDHHMM.csv`) and passes it to `migrate_content()`.
- **FR-009**: The CSV output feature MUST be additive — no existing parameter, return value,
  or behaviour of `migrate_content()` may change when the parameter is not used.

### Key Entities

- **URL Mapping Record**: Represents a single successfully migrated item. Key attributes:
  item name, item type, original URL (source portal item URL before migration), and updated
  URL (destination portal item URL after cloning).
- **CSV Output File**: A delimited text file written at the caller-supplied path containing
  all URL mapping records for the run. When produced via `make_data.py`, it shares its
  timestamp and directory with the run's log file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When the CSV flag is enabled, a CSV file is present on disk at the expected
  path within the same elapsed time as the migration itself (no separate post-processing
  step required).
- **SC-002**: Every successfully migrated item has exactly one corresponding row in the CSV;
  no items are double-counted or omitted.
- **SC-003**: The CSV and log file produced by a single `make_data.py` run share an identical
  timestamp prefix, allowing them to be correlated without manual filename matching.
- **SC-004**: Disabling the feature (omitting the parameter or flag) produces a result
  indistinguishable from a run without the feature installed — same return value, same log
  output, no additional files on disk.
- **SC-005**: The CSV is written as part of the migration invocation without requiring a
  separate function call from the caller.

## Assumptions

- The ArcGIS `Item` object returned by `clone_items()` exposes the cloned item's URL in a
  consistent, accessible field; no additional API calls beyond what `clone_items()` already
  performs are needed to retrieve it.
- The source item's URL is accessible from the source `Item` object prior to cloning.
- Items with no URL (non-service types such as documents, images, or notebooks) have an
  empty or `None` URL field rather than raising an error when accessed.
- The CSV flag in `make_data.py` defaults to disabled; no change is required to existing
  invocations or scheduled runs.
- The `make_data.py` script is the only entry point where the log-file co-location naming
  convention needs to be enforced; direct callers of `migrate_content()` are responsible
  for supplying their own CSV path if they need CSV output.
- CSV output is written in full after the migration loop completes, not streamed
  incrementally during the loop.
