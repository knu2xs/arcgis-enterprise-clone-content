# Tasks: Content Migration Function

**Feature**: `002-content-migration-fn`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Exact file paths are included in every task description

---

## Phase 1: Setup

- [X] T001 Add imports to `src/arcgis_cloning/_main.py`: `import time`, `from __future__ import annotations`, `from dataclasses import dataclass, field`, `from typing import TYPE_CHECKING`; add conditional `if TYPE_CHECKING: from arcgis.gis import GIS` import block to avoid hard runtime dependency

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the `MigrationResult` dataclass and all private helper functions.
These are shared by all three user stories and must exist before any story implementation.

**CRITICAL**: US1 (`migrate_content` body), US2 (resume logic), and US3 (result inspection)
all depend on `MigrationResult`, `_connect_gis`, `_get_all_items`, `_build_dest_index`,
`_resolve_folder_name`, and `_ensure_folder` being in place first.

- [X] T002 Add `MigrationResult` dataclass to `src/arcgis_cloning/_main.py` with fields `migrated: int = 0`, `skipped: int = 0`, `failed: int = 0`, `failures: list[dict] = field(default_factory=list)`
- [X] T003 [P] Add `_connect_gis(env_name: str, gis_obj: GIS | None) -> GIS` to `src/arcgis_cloning/_main.py`: if `gis_obj` is not `None` return it; otherwise call `load_secrets()`, read the `profile` or `url/username/password` from the env block, connect via `GIS(profile=...)` or `GIS(url, username, password)`, log CRITICAL + re-raise on failure
- [X] T004 [P] Add `_get_all_items(gis: GIS, query: str | None, max_items: int | None) -> list` to `src/arcgis_cloning/_main.py`: call `gis.content.search(query or "", max_items=-1)`; if `max_items` is not `None` slice result to `[:max_items]`; log DEBUG with item count; return list
- [X] T005 [P] Add `_build_dest_index(dest_gis: GIS) -> set[tuple[str, str]]` to `src/arcgis_cloning/_main.py`: call `dest_gis.content.search("", max_items=-1)`, return `{(item.title, item.type) for item in items}`; log DEBUG with index size
- [X] T006 [P] Add `_resolve_folder_name(src_item: object, src_gis: GIS) -> str | None` to `src/arcgis_cloning/_main.py`: read `src_item["ownerFolder"]`; if `None` return `None`; build `{f["id"]: f["title"] for f in src_gis.users.me.folders}` and return `folder_id_to_name.get(folder_id)`; log DEBUG with resolved name
- [X] T007 [P] Add `_ensure_folder(dest_gis: GIS, folder_name: str | None) -> None` to `src/arcgis_cloning/_main.py`: if `folder_name` is `None` return immediately; check `{f["title"] for f in dest_gis.users.me.folders}`; only call `dest_gis.content.folders.create(folder=folder_name)` when folder is absent; log DEBUG with action taken

**Checkpoint**: All private helpers implemented and importable; `MigrationResult` constructable with default values.

---

## Phase 3: User Story 1 � Migrate Content from Source to Destination (Priority: P1) MVP

**Goal**: `migrate_content()` connects to both portals, discovers all source items, clones
each one to the mirrored destination folder, returns a `MigrationResult`, and logs at all
required levels.

**Independent Test**: Call `migrate_content(source_gis=mock_src, destination_gis=mock_dest)`
with mocked GIS objects; assert return type is `MigrationResult` and `result.migrated == N`.

### Implementation for User Story 1

- [X] T008 [US1] Implement `migrate_content()` function body in `src/arcgis_cloning/_main.py` with the full execution flow: pre-flight (connect + URL equality check), discover items, INFO start banner, per-item loop (resolve folder ? ensure folder ? clone ? count), INFO complete banner; return `MigrationResult`; full logging at DEBUG/INFO/WARNING/ERROR/CRITICAL per FR-004
- [X] T009 [US1] Export `migrate_content` and `MigrationResult` from `src/arcgis_cloning/__init__.py`: add `from ._main import migrate_content, MigrationResult` and include both in `__all__`

### Tests for User Story 1

- [X] T010 [P] [US1] Add `test_migrate_content_returns_migration_result` to `testing/test_arcgis_cloning.py`: mock source GIS returning 1 item, mock `clone_items` success; assert return is `MigrationResult` instance
- [X] T011 [P] [US1] Add `test_migrate_content_migrates_all_items` to `testing/test_arcgis_cloning.py`: mock source with 3 items, mock `clone_items` success all 3; assert `result.migrated == 3`, `result.skipped == 0`, `result.failed == 0`
- [X] T012 [P] [US1] Add `test_migrate_content_zero_items_returns_empty_result` to `testing/test_arcgis_cloning.py`: mock `content.search` returning `[]`; assert `result.migrated == 0`, `result.skipped == 0`, `result.failed == 0`
- [X] T013 [P] [US1] Add `test_migrate_content_same_url_raises` to `testing/test_arcgis_cloning.py`: pass `source_gis` and `destination_gis` mocks both with `url == "https://same.example.com"`; assert `ValueError` is raised

**Checkpoint**: `migrate_content()` callable end-to-end with mocked GIS; US1 acceptance
scenarios 1 and 3 covered; package exports working.

---

## Phase 4: User Story 2 � Resume an Interrupted Migration (Priority: P2)

**Goal**: When `resume=True` the function compares source items against a destination index
built from `_build_dest_index` and skips items whose `(title, type)` already exists.
Result counts reflect skips correctly.

**Independent Test**: Mock destination index containing item A; mock source with items A and
B; call with `resume=True`; assert `result.skipped == 1`, `result.migrated == 1`.

### Implementation for User Story 2

- [X] T014 [US2] Update `migrate_content()` in `src/arcgis_cloning/_main.py`: add resume branch � when `resume=True`, call `_build_dest_index(dest_gis)` after discovering source items; in the per-item loop check `(item.title, item.type) in dest_index` before cloning; log INFO skip message and increment `result.skipped`; log DEBUG with destination index size

### Tests for User Story 2

- [X] T015 [P] [US2] Add `test_migrate_content_resume_skips_existing` to `testing/test_arcgis_cloning.py`: mock dest index with `{("Map A", "Web Map")}`, source has "Map A" and "Map B"; call `resume=True`; assert `result.skipped == 1`, `result.migrated == 1`
- [X] T016 [P] [US2] Add `test_migrate_content_resume_all_present_returns_zero_migrated` to `testing/test_arcgis_cloning.py`: dest index contains all source items; assert `result.migrated == 0`, `result.skipped == len(source_items)`
- [X] T017 [P] [US2] Add `test_migrate_content_resume_empty_dest_migrates_all` to `testing/test_arcgis_cloning.py`: `resume=True` with empty destination; assert `result.migrated == len(source_items)`, `result.skipped == 0`
- [X] T018 [P] [US2] Add `test_migrate_content_resume_title_type_both_must_match` to `testing/test_arcgis_cloning.py`: dest index has `{("Map A", "Web Map")}`; source has item titled "Map A" with type "Dashboard"; assert item is NOT skipped (`result.migrated == 1`, `result.skipped == 0`)

**Checkpoint**: Resume skip logic verified; US2 acceptance scenarios 1, 2, and 3 covered.

---

## Phase 5: User Story 3 � Structured Migration Report (Priority: P3)

**Goal**: `MigrationResult` contains accurate failure records when `clone_items` raises.
The function never raises on per-item failure; it always returns the result object.

**Independent Test**: Mock one item to raise `RuntimeError`; assert function returns
`MigrationResult` (no raise), `result.failed == 1`, `result.failures[0]` contains
`item_id`, `title`, `type`, `error` keys.

### Tests for User Story 3

- [X] T019 [US3] Add `test_migrate_content_failed_item_does_not_raise` to `testing/test_arcgis_cloning.py`: mock `clone_items` to raise `RuntimeError("clone error")`; assert function returns `MigrationResult`, not raises; `result.failed == 1`
- [X] T020 [P] [US3] Add `test_migrate_content_failure_record_contains_expected_keys` to `testing/test_arcgis_cloning.py`: mock 1-item failure; assert `result.failures[0]` has keys `item_id`, `title`, `type`, `error` with correct values
- [X] T021 [P] [US3] Add `test_migrate_content_all_fail_returns_result_not_raises` to `testing/test_arcgis_cloning.py`: mock 3 items all raising; assert `result.failed == 3`, `len(result.failures) == 3`, function does not raise
- [X] T022 [P] [US3] Add `test_migrate_content_max_items_caps_processing` to `testing/test_arcgis_cloning.py`: mock source with 5 items; call with `max_items=2`; assert `result.migrated + result.failed + result.skipped == 2`

**Checkpoint**: US3 acceptance scenarios 1 and 2 covered; failure isolation contract verified.

---

## Phase 3 (continued): Additional Tests for User Story 1

- [X] T026 [P] [US1] Add `test_migrate_content_fresh_run_does_not_skip_existing` to `testing/test_arcgis_cloning.py`: mock destination with one item already present (same title and type as a source item); call `migrate_content()` WITHOUT `resume=True`; assert `result.migrated == 1` and `result.skipped == 0` (fresh run clones regardless of destination state)
- [X] T027 [P] [US1] Add `test_migrate_content_connection_failure_raises_runtime_error` to `testing/test_arcgis_cloning.py`: mock `_connect_gis` to raise `RuntimeError("Connection failed")`; assert the function raises `RuntimeError` before returning any result; assert `result` is not returned

## Phase 2 (continued): Folder-Mirroring Tests

- [X] T028 [P] [US1] Add `test_migrate_content_creates_folder_in_destination` to `testing/test_arcgis_cloning.py`: mock source item with `ownerFolder` set to a known folder ID/name; mock `dest_gis.users.me.folders` returning empty list; assert `dest_gis.content.folders.create` is called once with the expected folder name
- [X] T029 [P] [US1] Add `test_migrate_content_root_item_skips_folder_creation` to `testing/test_arcgis_cloning.py`: mock source item with `ownerFolder=None`; mock `dest_gis.content.folders.create`; assert `create` is NOT called

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Add Google-style docstring to `migrate_content()` in `src/arcgis_cloning/_main.py` with `Args:`, `Returns:`, `Raises:` sections and `!!! note` admonition documenting the resume comparison key assumption per project coding standards
- [X] T024 [P] Add Google-style docstrings to all five private helpers (`_connect_gis`, `_get_all_items`, `_build_dest_index`, `_resolve_folder_name`, `_ensure_folder`) in `src/arcgis_cloning/_main.py`
- [X] T025 Add `# TODO (post-clone WARNING): compare cloned item properties against source` comment at the clone site inside `migrate_content()` in `src/arcgis_cloning/_main.py` (deferred per FR-004 WARNING deferral note)
- [X] T030 [P] Run full test suite (`python -m pytest testing/ -v`) and confirm all tests (existing + new) pass with zero failures

---

## Dependencies & Execution Order

```
Phase 1 (Setup: T001)
  +-? Phase 2 (Foundational: T002�T007)  ? ALL Phase 3/4/5 tasks blocked until complete
        +-? Phase 3 (US1: T008�T013)     ? T008 impl first; T009 export; T010�T013 tests [P]
        +-? Phase 4 (US2: T014�T018)     ? T014 impl first; T015�T018 tests [P]
        +-? Phase 5 (US3: T019�T022)     ? no new impl needed; tests [P] after Phase 3 impl
              +-? Phase 6 (Polish: T023�T025)
```

### Parallel execution within phases

- **Phase 2**: T003, T004, T005, T006, T007 can all be written in parallel (different functions, no cross-dependencies); T002 (`MigrationResult`) must exist first
- **Phase 3**: T010�T013, T026, T027 tests are all independent and can be written simultaneously after T008+T009
- **Phase 2 (continued)**: T028, T029 folder-mirroring tests are independent after T007
- **Phase 4**: T015�T018 tests are all independent after T014
- **Phase 5**: T019�T022 are all independent after Phase 3 impl (T008) is done
- **Phase 6**: T023, T024, T025 are independent of each other

### Implementation strategy (MVP first)

**MVP = Phases 1�3 (T001�T013, T026�T029)**: Delivers US1 � fresh-run migration end-to-end with
correct result, logging, folder mirroring, and package exports. Independently demonstrable.

**Increment 2 = Phase 4 (T014�T018)**: Adds resume support (US2).

**Increment 3 = Phase 5 (T019�T022)**: Adds structured failure reporting tests (US3
behaviour is already implemented in T008 via the try/except; these tasks add test coverage).

**Final = Phase 6 (T023�T025, T030)**: Docstrings, TODO comment, full test run.
