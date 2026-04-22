# Research: Make-Data Migration Script

**Feature**: `003-make-data-migration-script`
**Date**: 2026-04-21

---

## Decision Log

### D1 — Root Logger vs Named Logger

- **Decision**: Use root logger (omit `logger_name`) when calling `get_logger()` in the script
  entry point. Pass `logfile_path=` to attach the file handler.
- **Rationale**: The `_logging.py` docstring examples explicitly show the root-logger pattern for
  scripts (`logger = get_logger(level='INFO', add_stream_handler=True, logfile_path=...)`) — this
  propagates to all module-level child loggers automatically, capturing `migrate_content()` output
  in the same log file.
- **Alternatives considered**: Named logger per script — rejected because it would not capture
  log records from the `arcgis_cloning` module logger (`"arcgis_cloning"`) unless explicit
  propagation was configured.

### D2 — Log File Naming Format

- **Decision**: `clone_content_{datetime.now().strftime("%y%m%d%H%M")}.log`
  → produces e.g. `clone_content_2604211430.log`
- **Rationale**: `%y` = 2-digit year, `%m` = 2-digit month, `%d` = 2-digit day,
  `%H` = 24-hr hour, `%M` = minute — exactly matching the `YYMMDDHHMM` format in the spec.
  Minute-level resolution is sufficient; two runs within the same minute are not a concern for
  a single-invocation migration script.
- **Alternatives considered**: ISO 8601 (`%Y%m%dT%H%M%S`) — already used by the existing
  script for `make_data.py` log names; rejected here in favour of the spec-defined format.

### D3 — Broken Config Imports in Existing `make_data.py`

- **Decision**: Remove the existing `from arcgis_cloning.config import LOG_LEVEL, INPUT_DATA,
  OUTPUT_DATA` imports. Replace with `load_config()` and access `cfg.logging.level`,
  `cfg.migration.source_env`, `cfg.migration.destination_env`.
- **Rationale**: `LOG_LEVEL`, `INPUT_DATA`, and `OUTPUT_DATA` are not exported from
  `arcgis_cloning/config.py`. The existing script would fail at import time. The correct
  pattern is `load_config()` → `ConfigNode` access.
- **Alternatives considered**: Re-adding the constants to `config.py` — rejected as
  unnecessary complexity; `load_config()` already solves this cleanly.

### D4 — Config Key Path for Migration Settings

- **Decision**: Add `migration` block under `environments.default` in `config.yml`:
  ```yaml
  migration:
    source_env: "source"
    destination_env: "destination"
  ```
  Access in script: `cfg = load_config(); source_env = cfg.migration.source_env`.
- **Rationale**: `ConfigNode` supports nested attribute access. Placing under `environments.default`
  makes the values available to all environments and overridable per-environment (FR-005).
- **Alternatives considered**: Top-level YAML key (outside `environments`) — rejected because the
  deep-merge logic only processes the `environments` block; top-level keys are not environment-
  specific and cannot be overridden.

### D5 — Graceful Fallback When `migration` Key Is Absent

- **Decision**: Use `getattr(cfg, "migration", None)` then conditional attribute access; fall
  back to `"source"` and `"destination"` if the `migration` attribute is absent or its sub-keys
  are absent.
- **Rationale**: FR-004 requires fallback behaviour when keys are absent. `ConfigNode.get()`
  returns `None` for missing keys; a simple `or "source"` chain covers the fallback.
- **Alternatives considered**: Try/except `AttributeError` — more verbose; the `getattr` pattern
  is cleaner for optional config sections.

### D6 — Exit Code Contract

- **Decision**: Wrap the `migrate_content()` call in a `try/except Exception`; call
  `sys.exit(1)` in the `except` block after logging. Normal completion uses implicit `sys.exit(0)`.
- **Rationale**: SC-004 requires exit code `0` on success (including partial item failures) and
  non-zero on pre-flight failure. `migrate_content()` never raises on per-item failure
  (Feature 002 FR-006), so `except` only fires on pre-flight issues.
- **Alternatives considered**: `sys.exit(result.failed > 0)` — rejected because partial item
  failures should not block CI/CD pipelines; the spec explicitly allows them to be non-fatal.

### D7 — Console vs File Log Level

- **Decision**: Root logger at `DEBUG` level; stream handler at `cfg.logging.level`
  (reads from config, defaults to `"DEBUG"` per `config.yml`); file handler at `DEBUG`.
- **Rationale**: FR-007 requires the file to capture all levels. Console level respects operator
  preference via config. The root logger must be at `DEBUG` to allow all messages through to
  handlers.
- **Alternatives considered**: Hardcoding `"INFO"` for console — rejected as it would ignore the
  `config.logging.level` setting, violating Principle II.
