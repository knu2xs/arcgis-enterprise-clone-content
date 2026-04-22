# Tasks: Make-Data Migration Script

**Feature**: `003-make-data-migration-script`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`)
- Exact file paths are included in every task description

---

## Phase 1: Setup

- [X] T001 Add `migration` section to `config/config.yml` under `environments.default` with `source_env: "source"` and `destination_env: "destination"` keys

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure the existing `make_data.py` module-level header (imports, `DIR_PRJ`
definition, package-path bootstrap) is clean and correct before the main block is rewritten.
The broken `from arcgis_cloning.config import LOG_LEVEL, INPUT_DATA, OUTPUT_DATA` import
must be removed along with all other sample-code imports.

- [X] T002 Update module-level imports in `scripts/make_data.py`: remove `from arcgis_cloning.config import LOG_LEVEL, INPUT_DATA, OUTPUT_DATA`; add `import logging` and `import sys`; retain `from datetime import datetime`, `import importlib.util`, `import sys` (deduplicated), `from pathlib import Path`, `import arcgis_cloning`, `from arcgis_cloning.utils import get_logger`; add `from arcgis_cloning.config import load_config` and `from arcgis_cloning import migrate_content`

**Checkpoint**: `python -c "import scripts.make_data"` (or `python scripts/make_data.py --help`) does not raise an `ImportError`.

---

## Phase 3: User Story 1 — Run Content Migration from the Command Line (Priority: P1) MVP

**Goal**: When `python scripts/make_data.py` is executed, the script bootstraps a root logger
with a `DEBUG`-level file handler writing to `data/logs/clone_content_YYMMDDHHMM.log`,
creates the directory if absent, calls `migrate_content()`, logs INFO start and completion
banners, exits `0` on success and `1` on pre-flight failure.

**Independent Test**: Execute `python scripts/make_data.py` (with mocked or real portals);
assert `data/logs/clone_content_*.log` exists and contains the start banner and completion
summary.

### Implementation for User Story 1

- [X] T003 [US1] Replace the `if __name__ == '__main__':` block in `scripts/make_data.py` with the migration entry point: compute `date_string = datetime.now().strftime("%y%m%d%H%M")`; set `log_dir = DIR_PRJ / 'data' / 'logs'`; call `log_dir.mkdir(parents=True, exist_ok=True)`; set `log_file = log_dir / f'clone_content_{date_string}.log'`
- [X] T004 [US1] In `scripts/make_data.py` (continuing the `__main__` block after T003): call `cfg = load_config()`; derive `console_level = cfg.logging.level if hasattr(cfg, 'logging') else 'DEBUG'`; call `logger = get_logger(level='DEBUG', add_stream_handler=True, logfile_path=log_file)`; iterate `logger.handlers` and set stream handler level to `console_level` per the plan design
- [X] T005 [US1] In `scripts/make_data.py` (continuing after T004): read `migration_cfg = getattr(cfg, 'migration', None)`; derive `source_env` and `destination_env` with `'source'` / `'destination'` fallbacks; log INFO start banner including `source_env`, `destination_env`, and `log_file` path
- [X] T006 [US1] In `scripts/make_data.py` (continuing after T005): wrap `result = migrate_content(source_env=source_env, destination_env=destination_env)` in a `try/except Exception as e` block; on success log INFO completion banner (`result.migrated`, `result.skipped`, `result.failed`); on exception build `msg`, log `logger.critical(msg)`, call `sys.exit(1)`

**Checkpoint**: Running `python scripts/make_data.py` with mocked/stubbed portals (or with
`migrate_content` patched to return a `MigrationResult`) produces a log file at
`data/logs/clone_content_*.log` with start and completion lines; exit code is `0`.

---

## Phase 4: User Story 2 — Configure Source and Destination Without Touching the Script (Priority: P2)

**Goal**: `migration.source_env` and `migration.destination_env` in `config.yml` drive
which portal credentials are used. When the keys are absent the script falls back to
`"source"` / `"destination"` without error.

**Independent Test**: Change `migration.source_env` in `config.yml` to a different value;
re-run the script (with mocked portals); confirm the log banner shows the updated env name.
Separately, remove the `migration` block from config; confirm the script still runs using
defaults.

*No additional implementation tasks* — the fallback logic is already built into T005 via
`getattr(cfg, 'migration', None)` and `getattr(migration_cfg, 'source_env', 'source')`.
US2 acceptance is verified by the configuration already added in T001 and the fallback path
covered in T005.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T007 [P] Update the module-level docstring in `scripts/make_data.py` to describe the script's purpose as a content migration entry point (replace the generic "Example script to process spatial data" text with a description matching its new role)
- [X] T008 [P] Verify `config/config.yml` has the complete `migration` section added in T001 and that `load_config()` correctly returns `cfg.migration.source_env == "source"` by running `python -c "from arcgis_cloning.config import load_config; cfg = load_config(); print(cfg.migration.source_env)"` from project root
- [X] T009 [P] Run full test suite (`python -m pytest testing/ -v`) and confirm all existing tests (26 passing from Features 001 and 002) still pass with zero failures after the `make_data.py` and `config.yml` changes
- [X] T010 [P] [US2] Add `test_make_data_fallback_when_migration_key_absent` to `testing/test_arcgis_cloning.py`: patch `load_config()` to return a `ConfigNode({})` (no `migration` key); import and call the config-reading block logic (or extract it to a helper); assert `source_env == "source"` and `destination_env == "destination"` (FR-004 fallback)
- [X] T011 [P] [US1] Add `test_make_data_preflight_failure_exits_with_code_1` to `testing/test_arcgis_cloning.py`: patch `migrate_content` to raise `RuntimeError("pre-flight error")`; invoke the `__main__` block (or the try/except wrapper) via `subprocess` or `pytest.raises(SystemExit)`; assert `SystemExit.code == 1` (SC-004)

---

## Dependencies & Execution Order

```
Phase 1 (Setup: T001)  ← config.yml update; unblocks T004/T005/T008
  └─► Phase 2 (Foundational: T002)  ← fix broken imports; unblocks T003–T006
        └─► Phase 3 (US1: T003→T004→T005→T006)  ← sequential; each task builds on the prior
              └─► Phase 4 (US2)  ← no new tasks; covered by T001 + T005 fallback
                    └─► Phase 5 (Polish: T007, T008, T009, T010, T011 [P])
```

### Parallel execution within phases

- **Phase 1**: T001 is a single task; no parallelism
- **Phase 2**: T002 is a single task; no parallelism
- **Phase 3**: T003→T004→T005→T006 are sequential additions to the same `__main__` block;
  each depends on the prior task's output being in place
- **Phase 5**: T007, T008, T009, T010, T011 are fully independent and can be executed
  simultaneously

### Implementation strategy (MVP first)

**MVP = Phases 1–3 (T001–T006)**: Delivers US1 — fully functional migration entry point
with log file, `data/logs/` auto-creation, INFO banners, and correct exit codes.
Independently demonstrable.

**Increment 2 = Phase 4**: No new tasks — US2 is already satisfied by T001 (config key)
and T005 (fallback logic). Validated by editing `config.yml` and re-running.

**Final = Phase 5 (T007–T011)**: Docstring, config smoke test, fallback test, exit-code
test, full regression test run.
