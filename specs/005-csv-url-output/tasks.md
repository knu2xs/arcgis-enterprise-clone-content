# Tasks: CSV URL Mapping Output for Migrated Content

**Feature**: `005-csv-url-output`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`)
- Exact file paths are included in every task description

---

## Phase 1: Core — `migrate_content()` CSV Parameter (User Story 1, Priority P1)

**Goal**: Add `url_csv_path` parameter to `migrate_content()`, validate the parent directory
exists pre-flight, collect a URL row per successfully migrated item, and write the CSV after
the migration loop.

- [X] T001 [US1] In `src/arcgis_cloning/_main.py`, add `url_csv_path: Path | str | None = None` as the last parameter of `migrate_content()`; update the function's `logger.debug` call at the top of the function to include `url_csv_path` in the log line; update the docstring `Args:` section with a description of the new parameter and add `ValueError` to the `Raises:` section
- [X] T002 [US1] In `src/arcgis_cloning/_main.py`, after the identical-URL pre-flight check and before `_get_all_items()`, add the `url_csv_path` parent-directory validation: if `url_csv_path is not None` convert to `Path`, check `csv_path.parent.exists()`, and raise `ValueError` with a descriptive message logging it at `logger.error` first
- [X] T003 [US1] In `src/arcgis_cloning/_main.py`, declare `url_rows: list[dict] = []` immediately before the `for n, item in enumerate(...)` migration loop
- [X] T004 [US1] In `src/arcgis_cloning/_main.py`, inside the `try` block of the migration loop where `dest_gis.content.clone_items()` is called, capture the return value: change the call to `cloned = dest_gis.content.clone_items(items=[item], folder=folder_name)`; derive `dest_url = cloned[0].url if cloned else None`; append `{"name": title, "type": item_type, "original_url": item.url or "", "updated_url": dest_url or ""}` to `url_rows`; keep `result.migrated += 1` immediately after
- [X] T005 [US1] In `src/arcgis_cloning/_main.py`, after the final `logger.info("Migration complete ...")` call, add the CSV write block: if `url_csv_path is not None`, resolve `csv_path = Path(url_csv_path)`, log `logger.debug` with path and row count, call `pd.DataFrame(url_rows, columns=["name", "type", "original_url", "updated_url"]).to_csv(csv_path, index=False)`, then log `logger.info(f"URL mapping CSV written: {csv_path}")`

**Checkpoint**: With `url_csv_path=None` (default), `migrate_content()` behaves identically
to the pre-feature version — no CSV is created, no new log lines appear.

---

## Phase 2: Script Integration — `make_data.py` CSV Flag (User Story 2, Priority P2)

**Goal**: `make_data.py` accepts an optional `--csv` CLI flag. When set, it derives the CSV
path from the same timestamp and `data/logs/` directory as the log file and passes it to
`migrate_content()`.

- [X] T006 [US2] In `scripts/make_data.py`, add `import argparse` after the existing `import logging` line; after the module-level imports (before `if __name__ == '__main__':`) is fine, but it MUST be inside the `__main__` block: add the `argparse.ArgumentParser` setup and `parser.add_argument("--csv", action="store_true", default=False, ...)` call as described in `plan.md`; call `args = parser.parse_args()` immediately after
- [X] T007 [US2] In `scripts/make_data.py`, after the `log_file` path is set, add `csv_file = log_dir / f'clone_content_{date_string}.csv' if args.csv else None`; add `if csv_file: logger.info(f'CSV output: {csv_file}')` after the start banner
- [X] T008 [US2] In `scripts/make_data.py`, update the `migrate_content(...)` call to pass `url_csv_path=csv_file`

**Checkpoint**: Running `python scripts/make_data.py --csv` (with portals mocked) produces
both `clone_content_*.log` and `clone_content_*.csv` in `data/logs/` with the same timestamp.
Running without `--csv` produces only the log file.

---

## Phase 3: Tests (Priority P1 & P2)

- [X] T009 [P] [US1] In `testing/test_arcgis_cloning.py`, add `test_migrate_content_writes_csv_for_migrated_items`: mock `_connect_gis` to return fake GIS objects, mock `_get_all_items` to return one fake item with `.url`, `.title`, `.type`, `.itemid`, `["ownerFolder"]`; mock `_resolve_folder_name` to return `None`; mock `_ensure_folder`; mock `dest_gis.content.clone_items` to return a list with one fake cloned item having a `.url`; call `migrate_content()` with `url_csv_path` set to a `tmp_path / "out.csv"`; assert the CSV exists, read with `pd.read_csv`, check columns `["name", "type", "original_url", "updated_url"]` are present and the row values match
- [X] T010 [P] [US1] In `testing/test_arcgis_cloning.py`, add `test_migrate_content_no_csv_when_path_none`: same mocks as T009; call `migrate_content()` without `url_csv_path`; assert no `*.csv` files exist in `tmp_path`
- [X] T011 [P] [US1] In `testing/test_arcgis_cloning.py`, add `test_migrate_content_csv_header_only_when_all_skipped`: mock resume mode where all items are already in destination index; call `migrate_content()` with `resume=True` and a `url_csv_path`; assert the CSV exists with only the header row (zero data rows)
- [X] T012 [P] [US1] In `testing/test_arcgis_cloning.py`, add `test_migrate_content_raises_on_missing_csv_directory`: call `migrate_content()` with `url_csv_path` pointing to a non-existent parent directory; assert `ValueError` is raised before any portal connection is attempted (mock `_connect_gis` to ensure it is not called, or verify exception is raised)
- [X] T013 [P] [US1] In `testing/test_arcgis_cloning.py`, add `test_migrate_content_csv_excludes_failed_items`: mock two items — one clones successfully, one raises an exception; call `migrate_content()` with `url_csv_path`; assert CSV has exactly one row (the successful item only)

---

## Phase 4: Polish

- [X] T014 [P] Run full test suite `python -m pytest testing/ -v` and confirm all existing tests plus the new tests pass with zero failures

---

## Dependencies & Execution Order

```
Phase 1 (T001→T002→T003→T004→T005)  ← sequential; each extends _main.py
  └─► Phase 2 (T006→T007→T008)       ← sequential; extends make_data.py; depends on Phase 1 signature
        └─► Phase 3 (T009–T013 [P])   ← parallel; depend on Phase 1 implementation
              └─► Phase 4 (T014)      ← runs after all code and tests are written
```

### Parallel execution within phases

- **Phase 3**: T009–T013 are fully independent tests and can be written simultaneously
- **Phase 4**: T014 is a single validation task
