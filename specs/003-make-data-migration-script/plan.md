# Implementation Plan: Make-Data Migration Script

**Branch**: `003-make-data-migration-script` | **Date**: 2026-04-21 | **Spec**: [spec.md](./spec.md)

## Summary

Replace the example processing block in `scripts/make_data.py` with a thin migration entry
point that: reads `migration.source_env` and `migration.destination_env` from `config.yml`,
bootstraps a root logger with file handler writing to `data/logs/clone_content_YYMMDDHHMM.log`,
calls `migrate_content()` from the `arcgis_cloning` package, logs the result summary, and exits
with code `0` on success or `1` on pre-flight failure. Also adds the `migration` section to
`config.yml` under `environments.default`.

## Technical Context

**Language/Version**: Python 3.x (ArcGIS Pro conda environment)
**Primary Dependencies**: `arcgis_cloning.migrate_content`, `arcgis_cloning.config.load_config`, `arcgis_cloning.utils.get_logger` — all already in the package; no new dependencies
**Storage**: `data/logs/clone_content_YYMMDDHHMM.log` — plain text log file
**Testing**: Smoke test (execute script, assert log file created); existing unit tests for `migrate_content()` cover all migration logic
**Target Platform**: ArcGIS Pro conda environment; same as existing `make_data.py`
**Project Type**: CLI entry point (script)
**Performance Goals**: N/A — script is I/O-bound by portal API; no local processing
**Constraints**: Script MUST be a thin entry point (Constitution Principle I); zero business logic in script body

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Source-First Architecture | ✅ PASS | Script only bootstraps logger, reads config, calls `migrate_content()`, reports — no logic |
| II. Configuration-Driven Behavior | ✅ PASS | `source_env` / `destination_env` from `config.yml`; log path derived from `Path` + timestamp |
| III. Structured Observability | ✅ PASS | Root logger with file handler (`DEBUG`) + stream handler (`cfg.logging.level`); `get_logger` pattern |
| IV. Testing Discipline | ✅ PASS | Script entry point — smoke test covers integration; unit tests for migration logic already exist in Feature 002 |
| V. Coding Standards | ✅ PASS | `pathlib.Path`, no `print()`, existing module-level Google docstring preserved |

**Post-design re-check**: No violations. `config.yml` migration key added under `environments.default` per Principle II. Broken `LOG_LEVEL`, `INPUT_DATA`, `OUTPUT_DATA` imports removed.

## Project Structure

### Documentation (this feature)

```text
specs/003-make-data-migration-script/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── make_data.md     ← Phase 1 output
└── tasks.md             ← Phase 2 output (speckit.tasks)
```

### Source Code Changes

```text
scripts/
└── make_data.py         ← replace example block; fix broken imports; add migration call

config/
└── config.yml           ← add migration section under environments.default
```

**Structure Decision**: Modify two existing files only. No new modules needed.

## Implementation Design

### `config.yml` changes

Add under `environments.default`:

```yaml
migration:
  source_env: "source"
  destination_env: "destination"
```

### `make_data.py` rewrite

The `if __name__ == '__main__':` block is replaced as follows:

```python
if __name__ == '__main__':
    import sys
    from arcgis_cloning.config import load_config
    from arcgis_cloning import migrate_content

    # --- Logging setup ---
    date_string = datetime.now().strftime("%y%m%d%H%M")   # YYMMDDHHMM
    log_dir = DIR_PRJ / 'data' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f'clone_content_{date_string}.log'

    cfg = load_config()
    console_level = cfg.logging.level if hasattr(cfg, 'logging') else 'DEBUG'

    logger = get_logger(
        level='DEBUG',                  # root logger at DEBUG — all records pass through
        add_stream_handler=True,        # console at console_level (set on handler below)
        logfile_path=log_file,
    )
    # Tune the stream handler to the config-driven level
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(console_level)

    # --- Read migration config ---
    migration_cfg = getattr(cfg, 'migration', None)
    source_env = getattr(migration_cfg, 'source_env', 'source') if migration_cfg else 'source'
    destination_env = getattr(migration_cfg, 'destination_env', 'destination') if migration_cfg else 'destination'

    logger.info(f'Starting migration | source_env={source_env!r} | destination_env={destination_env!r}')
    logger.info(f'Log file: {log_file}')

    # --- Run migration ---
    try:
        result = migrate_content(source_env=source_env, destination_env=destination_env)
        logger.info(
            f'Migration complete: migrated={result.migrated}, '
            f'skipped={result.skipped}, failed={result.failed}'
        )
    except Exception as e:
        msg = f'Migration failed (pre-flight error): {e}'
        logger.critical(msg)
        sys.exit(1)
```

### Key design decisions

1. **`get_logger` without `logger_name`** → uses root logger → child loggers in
   `arcgis_cloning` module propagate to it automatically (all their records appear in the
   log file).
2. **Stream handler level adjusted post-creation** → `get_logger` does not expose per-handler
   level configuration; iterating over `logger.handlers` after creation is the correct
   approach to tune the console without touching the file handler.
3. **`load_config()` without `environment=`** → uses the `ENVIRONMENT` singleton (defaults
   to `"source"`); the `migration.*` keys are under `environments.default` and therefore
   available in all environments.
4. **`sys.exit(1)` only in `except`** → `migrate_content()` never raises on per-item failure
   (Feature 002 FR-006); `except` only catches pre-flight failures.
5. **`log_dir.mkdir(parents=True, exist_ok=True)`** → idempotent; replaces the `if not
   log_dir.exists(): log_dir.mkdir(parents=True)` pattern in the original script.

## Testing Strategy

| Test | Coverage |
|---|---|
| Smoke test: `python scripts/make_data.py` with mocked portals | SC-001, SC-002 |
| Verify `data/logs/clone_content_*.log` exists post-run | FR-002, FR-003 |
| Edit `migration.source_env` in config, re-run, check log for updated URL | FR-004, FR-005, SC-003 |
| Break credentials, run script, assert exit code 1 and log contains CRITICAL | SC-004 |

No new unit tests are added to `testing/` — all migration logic is covered by Feature 002
tests. The script itself is an entry point and is validated by integration/smoke testing.

