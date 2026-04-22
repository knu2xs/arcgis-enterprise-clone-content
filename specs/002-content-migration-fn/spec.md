# Feature Specification: Content Migration Function

**Feature Branch**: `002-content-migration-fn`
**Created**: 2026-04-21
**Status**: Draft
**Input**: User description: "Create function in main for content migration using arcgis and standard patterns in the documentation. Include ability to resume, using a content comparison between source and destination."

## User Scenarios & Testing *(mandatory)*

### User Story 1 � Migrate Content from Source to Destination (Priority: P1)

A developer or administrator calls a single function to copy ArcGIS content items from a
source portal to a destination portal. The function connects to both portals using the
credentials defined in `secrets.yml` (profile or username/password), discovers the content
to migrate, and clones each item to the destination.

**Why this priority**: This is the core deliverable � without it no other story has value.
A working migration from source to destination is the MVP.

**Independent Test**: Can be tested by running the function with a small set of known items
in the source portal and confirming those items appear in the destination portal afterward.

**Acceptance Scenarios**:

1. **Given** valid source and destination connections and at least one item in the source,
   **When** the migration function is called, **Then** each discovered item is cloned to the
   destination portal and the function returns a summary of migrated items.
2. **Given** a destination portal where the item already exists (same title and type),
   **When** the migration function is called without the resume flag, **Then** the item is
   cloned again (no deduplication assumed in fresh-run mode).
3. **Given** an unreachable destination portal, **When** the migration function is called,
   **Then** the function raises a descriptive error and logs the failure before exiting.

---

### User Story 2 � Resume an Interrupted Migration (Priority: P2)

A developer or administrator resumes a partially completed migration without re-cloning items
that already exist in the destination. The function compares content between source and
destination (by item title and type, or a stable identifier) and skips items already present,
cloning only the remainder.

**Why this priority**: Migrations over large content libraries or slow network links are
frequently interrupted. Without resume support, every failure requires starting over �
wasting time and creating duplicate content.

**Independent Test**: Can be tested by running a migration, interrupting it mid-way, then
re-running with `resume=True` and confirming only the remaining items are cloned (no
duplicates, total item count in destination equals source item count).

**Acceptance Scenarios**:

1. **Given** a destination that already contains a subset of source items, **When** the
   migration function is called with `resume=True`, **Then** already-present items are
   skipped and only the missing items are cloned.
2. **Given** all source items are already present in the destination, **When** the migration
   function is called with `resume=True`, **Then** zero items are cloned and the function
   returns a summary indicating the migration is complete.
3. **Given** `resume=True` and a destination that contains items with the same title but a
   different type, **When** the migration function compares content, **Then** those items
   are treated as absent (title + type must both match) and are cloned.

---

### User Story 3 � Receive a Structured Migration Report (Priority: P3)

After migration completes (or is interrupted), the caller receives a structured result
object summarising what was migrated, what was skipped, and what failed � without having to
parse log output.

**Why this priority**: Callers (scripts, toolboxes, notebooks) need a machine-readable
result to decide what to do next, display progress to an end-user, or persist a migration
audit trail. Logging alone is insufficient for programmatic consumption.

**Independent Test**: Can be tested by inspecting the return value of the migration function
after a run that includes at least one migrated item, one skipped item (resume mode), and one
intentionally failed item (unreachable or permission-denied item).

**Acceptance Scenarios**:

1. **Given** a completed migration, **When** the return value is inspected, **Then** it
   contains counts of migrated, skipped, and failed items plus a list of any failures with
   item identifiers and error messages.
2. **Given** a migration with one item that fails to clone, **When** the function returns,
   **Then** the failure is recorded in the result and the function does not raise an exception
   (partial failure is non-fatal; the remaining items continue to be processed).

---

### Edge Cases

- What happens when the source portal contains no items matching the query?
  Response: Function returns immediately with a zero-migration summary; no error is raised.
- What happens when the source and destination are the same portal URL?
  Response: Function raises a descriptive error before attempting any migration.
- What happens when a specific item fails to clone mid-run?
  Response: Failure is logged and recorded in the result; migration continues with remaining items.
- What happens when `resume=True` but the destination is empty?
  Response: Behaves identically to a fresh run � all source items are cloned.
- What happens when credentials are missing or invalid for either portal?
  Response: Connection attempt raises an error; function logs and re-raises before any migration begins.

## Clarifications

### Session 2026-04-21

- Q: How does the function receive GIS connections — pre-built GIS objects, environment name strings, or raw credentials? → A: Both: accept optional `GIS` objects; if not provided fall back to environment name strings with defaults `"source"` and `"destination"` loaded from `secrets.yml`.
- Q: How should destination folder structure be handled — mirror source, deposit at root, or accept an override? → A: Mirror source folder structure; create matching folders in the destination if they don't exist.
- Q: How should source item pagination be handled — caller-controlled limit, auto-paginate all, or auto-paginate with optional cap? → A: Paginate automatically to fetch all matching items; also expose an optional `max_items` cap parameter for safety and testing purposes.
- Q: What shape should the structured return value take — plain dict, dataclass, or DataFrame? → A: A `dataclass` instance with typed named fields (e.g., `migrated`, `skipped`, `failed`, `failures`).
- Q: Should the function raise if all items fail, or always return MigrationResult? → A: Always return `MigrationResult`; raise only on pre-flight failures (bad credentials, same source/destination URL), never based on per-item failure counts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The migration function MUST accept a `resume` parameter (default `False`) that
  controls whether already-present destination items are skipped.
- **FR-002**: When `resume=True`, the function MUST compare source and destination content by
  item title and item type to determine which items require cloning.
- **FR-003**: The function MUST accept optional `source_gis` and `destination_gis` parameters
  (pre-built `GIS` objects). When either is `None`, the function MUST connect by loading
  credentials from `secrets.yml` for the corresponding environment name string (defaulting to
  `"source"` and `"destination"` respectively), supporting both profile-based and
  username/password-based authentication as defined by the `profile` key in `secrets.yml`.
  If the `env_name` key is absent from `secrets.yml`, the function MUST raise `KeyError`
  with a descriptive message identifying the missing key, and log at CRITICAL before
  re-raising.
- **FR-004**: The function MUST use a module-level logger configured via `get_logger` and
  produce log output at all appropriate severity levels throughout its execution, following
  the logging conventions established in the project:
    - **DEBUG**: Entry into the function with all parameter values; connection details
      (portal URL, auth method); total item count discovered in source; each item's title,
      type, and ID before and after cloning; content comparison result per item (present /
      absent) when `resume=True`; duration of individual clone operations.
    - **INFO**: Migration start banner (source URL, destination URL, resume flag, query);
      running progress counter per item (`Migrating item N of M: <title> (<type>)`);
      skip notification per item when resume is active (`Skipping already-present item:
      <title> (<type>)`); migration complete banner with final migrated / skipped / failed
      counts.
    - **WARNING**: When the source returns zero items for the given query.

      !!! note
          Post-clone property comparison (e.g., verifying item type or count round-trips
          correctly) is deferred to a future version. The implementation MUST include a
          `# TODO (post-clone WARNING): compare cloned item properties against source`
          comment at the clone site so the gap is visible in code review.
    - **ERROR**: Per-item clone failure (item title, type, ID, and exception message),
      logged using the build-message → log → record pattern before continuing to the next
      item.
    - **CRITICAL**: Any unrecoverable pre-flight failure (identical source/destination
      URL, connection failure to either portal) logged before re-raising.
- **FR-005**: The function MUST return a `MigrationResult` dataclass instance with typed
  named fields: `migrated` (int), `skipped` (int), `failed` (int), and `failures` (list of
  records each containing the item identifier and error message).
- **FR-006**: Per-item clone failures MUST be caught, logged at `ERROR` level, and recorded
  in `MigrationResult.failures` without halting the migration of remaining items. The
  function MUST always return a `MigrationResult` — it MUST NOT raise based on the count
  of per-item failures, even if all items fail. Raises are reserved exclusively for
  pre-flight failures (FR-007, FR-003).
- **FR-007**: The function MUST raise a descriptive error if source and destination portal
  URLs are identical.
- **FR-008**: The function MUST live in `src/arcgis_cloning/_main.py` and be exported from
  the package `__init__.py`, consistent with the source-first architecture principle.
- **FR-009**: The function MUST accept an optional `query` parameter to filter which source
  items are included in the migration (defaults to all items accessible to the authenticated
  user). The function MUST paginate source results automatically to retrieve all matching
  items regardless of total count. An optional `max_items` parameter MUST be accepted to
  cap the number of items processed, defaulting to no limit; this cap is primarily intended
  for safety checks and testing.
- **FR-010**: The function MUST mirror the source folder structure in the destination,
  creating matching folders if they do not already exist, so each cloned item lands in the
  same relative folder path as its source counterpart.

### Key Entities

- **MigrationResult**: A `dataclass` returned by the migration function with typed fields:
  `migrated: int`, `skipped: int`, `failed: int`, and `failures: list[dict]` where each
  failure dict contains the item identifier and error message.
- **ContentItem**: An ArcGIS portal item � identified by title, type, and item ID; the unit
  of work for comparison and cloning.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A migration of 100 items completes without manual intervention from end to end.
- **SC-002**: A resumed migration skips 100% of items already present in the destination,
  confirmed by item count equality between source subset and destination.
- **SC-003**: A single item failure does not prevent the remaining items from being cloned �
  the function processes all items and records failures without stopping.
- **SC-004**: The return value can be inspected programmatically to determine migration
  completeness without parsing log output.
- **SC-005**: The function is callable from a notebook, a script, and an ArcGIS toolbox with
  no changes to its signature.

## Assumptions

- Both source and destination portals are reachable from the execution environment.
- The authenticated user on the source portal has read access to the items being migrated.
- The authenticated user on the destination portal has permission to create content.
- Content comparison for resume purposes uses item title + item type as the matching key;
  a more robust identifier (e.g., item ID mapping) is out of scope for this version.
- Cloning fidelity (service URL re-pointing, layer remapping) is delegated to the ArcGIS
  API for Python built-in clone mechanisms; no custom remapping logic is in scope.
- The function targets items owned by or shared with the authenticated source user; cloning
  items owned by other users is out of scope unless the query explicitly includes them.
- `pandas` is available in the environment for result tabulation if needed.
