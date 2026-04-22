# Feature Specification: Environment as Portal Configuration

**Feature Branch**: `001-environment-as-portal-config`  
**Created**: 2026-04-21  
**Status**: Draft  
**Input**: Refactor the configuration system so that named environments represent connectable ArcGIS Enterprise instances (e.g. `source`, `destination`) rather than deployment stages (`dev`, `test`, `prod`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load Portal Config by Name (Priority: P1)

A developer writing a clone script needs to load connection settings for both the
source and destination portals independently. They call `load_config("source")` and
`load_config("destination")` to obtain two separate configuration objects, each
carrying the correct logging level, data paths, and any portal-specific overrides.
Credentials are loaded in parallel via `load_secrets("source")` and
`load_secrets("destination")`, giving them `url`, `username`, and `password` for each portal.

**Why this priority**: This is the entire point of the refactor — without the ability to
load a named portal configuration, no clone operation can be written correctly.

**Independent Test**: Can be fully tested by calling `load_config("source")` and
`load_config("destination")` against the updated `config.yml` and verifying the
returned objects carry distinct, correct values for each portal.

**Acceptance Scenarios**:

1. **Given** `config.yml` has `source` and `destination` blocks under `environments`,
   **When** a script calls `load_config("source")`,
   **Then** a `ConfigNode` is returned whose values reflect the `source` block merged
   over `default`.
2. **Given** `secrets.yml` has `source` and `destination` blocks each with `url`,
   `username`, and `password`,
   **When** a script calls `load_secrets("source")`,
   **Then** a `ConfigNode` is returned with `secrets.source.url`, `secrets.source.username`,
   and `secrets.source.password` populated correctly.
3. **Given** both `load_config` and `load_secrets` return correctly,
   **When** a clone script wires them together for a read-from-source /
   write-to-destination operation,
   **Then** the script can access `source_cfg.logging.level`,
   `source_sec.source.url`, `dest_cfg.data.output`, and `dest_sec.destination.url`
   without errors.

---

### User Story 2 - Default Environment Points to Source (Priority: P2)

A developer who imports `arcgis_cloning.config` without specifying an environment
expects the module-level `config` singleton to correspond to a meaningful default —
the source portal — rather than a non-existent `"dev"` environment that would raise
a `ValueError` on import.

**Why this priority**: The current default `"dev"` no longer exists in `config.yml`,
so the module-level singleton breaks at import time. Fixing the default is a blocker
for all consumers of the module.

**Independent Test**: Can be fully tested by importing `arcgis_cloning.config` without
setting `PROJECT_ENV` and confirming that `config.logging.level` is accessible and
no `ValueError` is raised.

**Acceptance Scenarios**:

1. **Given** `PROJECT_ENV` is not set,
   **When** `arcgis_cloning.config` is imported,
   **Then** `ENVIRONMENT` equals `"source"` and `config` is a valid `ConfigNode`
   reflecting the `source` environment.
2. **Given** `PROJECT_ENV=destination` is set in the shell,
   **When** `arcgis_cloning.config` is imported,
   **Then** `ENVIRONMENT` equals `"destination"` and `config` reflects that portal's
   settings.

---

### User Story 3 - Discover Available Portals (Priority: P3)

A toolbox tool or script wants to enumerate the portals defined in `config.yml` to
present a drop-down or validate user input before attempting a connection.

**Why this priority**: Useful for toolbox UI and validation, but the clone operation
works without it as long as `load_config` and `load_secrets` work.

**Independent Test**: Can be fully tested by calling `get_available_environments()` and
asserting the returned list equals `["destination", "source"]` (or whatever portals are
defined).

**Acceptance Scenarios**:

1. **Given** `config.yml` defines `source` and `destination` under `environments`,
   **When** `get_available_environments()` is called,
   **Then** it returns `["destination", "source"]` (sorted alphabetically, `default`
   excluded).
2. **Given** a third portal entry (e.g. `staging`) is added to `config.yml`,
   **When** `get_available_environments()` is called,
   **Then** `"staging"` appears in the returned list without any code changes.

---

### Edge Cases

- **Missing `source` or `destination` block**: `load_config("source")` raises a
  `ValueError` with a message listing the available environments when the requested
  key is absent from `config.yml`.
- **Empty environment block**: A named block that is present but has no keys (e.g.
  `source:` with no children) inherits all values from `default` without error.
- **`secrets.yml` absent**: The module-level `secrets` singleton is set to an empty
  `ConfigNode` and a warning is emitted; callers that attempt `load_secrets("source")`
  explicitly receive a `FileNotFoundError`.
- **`PROJECT_ENV` set to an unknown portal name**: `load_config()` (no args) raises
  a `ValueError` naming the invalid environment.
- **Additional portals**: Adding a third entry (e.g. `staging`) to `config.yml` and
  `secrets.yml` requires no Python changes; `load_config("staging")` works immediately.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `config.yml` MUST define `source` and `destination` environment blocks
  under the `environments` key, each providing portal-specific overrides merged on top
  of `environments.default`.
- **FR-002**: `environments.default` in `config.yml` MUST contain shared fallback keys
  (`logging.level`, `data.input`, `data.output`) so that every named portal inherits
  sensible defaults without repetition.
- **FR-003**: `config.yml` MUST NOT contain references to `dev`, `test`, or `prod`
  environment names.
- **FR-004**: `secrets.yml` and `secrets_template.yml` MUST each contain a `source`
  block and a `destination` block, both having `url`, `username`, and `password` keys.
- **FR-005**: `load_secrets(environment="source")` and
  `load_secrets(environment="destination")` MUST return a `ConfigNode` whose top-level
  key matches the environment name, giving callers access to
  `secrets_node.<env>.url`, `secrets_node.<env>.username`, and
  `secrets_node.<env>.password`.
- **FR-006**: The `ENVIRONMENT` constant in `config.py` MUST default to `"source"` when
  the `PROJECT_ENV` environment variable is not set.
- **FR-007**: `load_config(environment=<name>)` MUST continue to work for any portal
  name defined in `config.yml`, with no code changes required when portals are added or
  removed.
- **FR-008**: `get_available_environments()` MUST return a sorted list of all
  environment keys from `config.yml` excluding `"default"`.
- **FR-009**: The module-level `config` and `secrets` singletons loaded at import time
  MUST remain available and unchanged in their public interface; existing callers that
  use `config.logging.level` or `secrets.esri.*` MUST NOT break (excluding the `esri`
  key which is replaced by per-portal keys).
- **FR-010**: `config.py` docstring and inline comments MUST be updated to reflect the
  portal-based environment model and the recommended per-call usage pattern:

  ```python
  source_cfg = load_config("source")
  source_sec = load_secrets("source")
  dest_cfg   = load_config("destination")
  dest_sec   = load_secrets("destination")
  ```

### Key Entities

- **Portal Environment**: A named entry under `environments` in `config.yml` that
  represents a single connectable ArcGIS Enterprise instance. Attributes: `logging.level`,
  `data.input`, `data.output`, and any portal-specific overrides.
- **Portal Secrets**: A named entry in `secrets.yml` matching a portal environment name.
  Attributes: `url` (portal URL), `username`, `password`.
- **`ConfigNode`**: Existing immutable attribute-accessible wrapper returned by both
  `load_config` and `load_secrets`. No changes to this class are required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can write a complete clone script — loading config and secrets
  for both source and destination — in under 10 lines of setup code using the documented
  pattern.
- **SC-002**: Importing `arcgis_cloning.config` without setting `PROJECT_ENV` raises no
  exceptions and produces a valid `config` object on 100% of attempts.
- **SC-003**: All existing tests in `testing/` continue to pass without modification
  after the `ENVIRONMENT` default is changed from `"dev"` to `"source"`.
- **SC-004**: `get_available_environments()` returns a list that always reflects the
  current state of `config.yml` — adding a new portal to the YAML is immediately
  discoverable without any code changes.
- **SC-005**: No credentials, URLs, or portal-specific strings appear in `config.yml`
  or anywhere in source-controlled files; all sensitive values live exclusively in
  `secrets.yml`.

## Assumptions

- The existing `ConfigNode` class, `load_config`, `load_secrets`, and
  `get_available_environments` function signatures are retained unchanged; only the
  default value of `ENVIRONMENT` and the contents of `config.yml` change.
- `load_secrets` does not currently accept an `environment` parameter — the per-portal
  pattern works by relying on the existing structure of `secrets.yml` where each
  top-level key matches a portal name. The caller accesses
  `secrets_node.<env>.url` after loading the full secrets file. No new parameter is
  added to `load_secrets` unless explicitly requested in implementation.
- The `secrets.esri` key referenced in the current `config.py` docstring is treated as
  legacy; it will be removed from examples and replaced with the portal-keyed pattern
  (`secrets.source.url`, `secrets.destination.url`).
- Only `source` and `destination` portals are in scope for this refactor. A `staging`
  entry is called out as a forward-compatible example but is not required to be added
  to the YAML files in this feature.
- ArcGIS Pro and `arcpy` are not involved in the configuration layer itself; this
  refactor is pure Python and YAML changes with no geoprocessing side effects.
- The `config/secrets.yml` already contains `source` and `destination` blocks with
  placeholder credentials; no structural changes to `secrets.yml` are required, only
  documentation of the pattern.
- The `make test` suite does not currently test for the `"dev"` environment name; if
  it does, those tests will need to be updated as part of this feature.
