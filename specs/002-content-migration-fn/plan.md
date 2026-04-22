# Implementation Plan: Content Migration Function

**Branch**: `002-content-migration-fn` | **Date**: 2026-04-21 | **Spec**: [spec.md](./spec.md)

## Summary

Implement `migrate_content()` in `src/arcgis_cloning/_main.py` — a function that clones ArcGIS
portal content from a source `GIS` instance to a destination `GIS` instance. The function
supports optional resume (skip already-present items by title+type comparison), auto-pagination,
folder structure mirroring, per-item error isolation, and returns a `MigrationResult` dataclass.
Connection to portals is either via caller-supplied `GIS` objects or via `secrets.yml`
environment credentials (profile or username/password).

## Technical Context

**Language/Version**: Python 3.x (ArcGIS Pro conda environment)
**Primary Dependencies**: `arcgis` (ArcGIS API for Python — GIS, Item, ContentManager), `dataclasses` (stdlib), `arcgis_cloning.utils.get_logger`, `arcgis_cloning.config.load_secrets`
**Storage**: N/A — no local file I/O; all state managed via portal REST API
**Testing**: pytest with `unittest.mock` / `pytest-mock` to mock `GIS` connections and `Item.clone_items`
**Target Platform**: ArcGIS Pro conda environment; also importable from notebooks and toolboxes
**Project Type**: library (function in `src/arcgis_cloning/`)
**Performance Goals**: Handles 100+ items without OOM; individual item timeout handled via per-item try/except
**Constraints**: `arcgis` is not listed in `pyproject.toml` (provided by ArcGIS Pro env); no ArcPy usage in this function

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Source-First Architecture | ✅ PASS | Function lives in `src/arcgis_cloning/_main.py`; exported from `__init__.py`; no logic in scripts |
| II. Configuration-Driven Behavior | ✅ PASS | Credentials from `secrets.yml` via `load_secrets()`; no hardcoded URLs or profile names |
| III. Structured Observability | ✅ PASS | `get_logger(__name__, ...)` at module level; FR-004 mandates all five log levels with specific messages |
| IV. Testing Discipline | ✅ PASS | Tests required in `testing/test_arcgis_cloning.py`; GIS connections mocked via `unittest.mock` |
| V. Coding Standards | ✅ PASS | Type hints, Google docstrings, PEP 8, `pathlib.Path` not needed (no filesystem ops) |

**Post-design re-check**: No violations identified after Phase 1 design. `arcgis` is not added to `pyproject.toml` per Spatial & ArcGIS Constraints.

## Project Structure

### Documentation (this feature)

```text
specs/002-content-migration-fn/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── migrate_content.md   ← Phase 1 output
└── tasks.md             ← Phase 2 output (speckit.tasks)
```

### Source Code

```text
src/arcgis_cloning/
├── _main.py             ← MigrationResult dataclass + migrate_content() + private helpers
└── __init__.py          ← export migrate_content, MigrationResult

testing/
└── test_arcgis_cloning.py   ← add tests for all US1/US2/US3 scenarios
```

**Structure Decision**: Single-file addition to existing `_main.py`. No new modules needed.
All helpers are private (`_`-prefixed) within `_main.py` to avoid polluting the public API.

## Implementation Design

### `MigrationResult` dataclass

```python
@dataclass
class MigrationResult:
    migrated: int = 0
    skipped: int = 0
    failed: int = 0
    failures: list[dict] = field(default_factory=list)
```

Each `failures` entry: `{"item_id": str, "title": str, "type": str, "error": str}`

### `migrate_content()` signature

```python
def migrate_content(
    source_gis: GIS | None = None,
    destination_gis: GIS | None = None,
    source_env: str = "source",
    destination_env: str = "destination",
    resume: bool = False,
    query: str | None = None,
    max_items: int | None = None,
) -> MigrationResult:
```

### Private helpers

| Helper | Purpose |
|---|---|
| `_connect_gis(env_name, gis_obj)` | Returns provided GIS or connects via secrets.yml; supports profile and username/password |
| `_get_all_items(gis, query, max_items)` | Calls `gis.content.search(query, max_items=-1)` with optional cap; returns list of Items |
| `_build_dest_index(dest_gis)` | Returns `set[tuple[str, str]]` of `(title, type)` for all items in destination |
| `_resolve_folder_name(src_item, src_gis)` | Looks up folder name from `src_item["ownerFolder"]` using `src_gis.users.me.folders`; returns `None` for root items |
| `_ensure_folder(dest_gis, folder_name)` | Checks `dest_gis.users.me.folders` for existing folder; creates via `dest_gis.content.folders.create(folder=folder_name)` only if absent |

### Execution flow

```
1. Pre-flight:
   a. Connect source_gis and destination_gis (_connect_gis)
   b. Validate source URL != destination URL → raise ValueError if equal (CRITICAL log + re-raise)

2. Discover:
   a. Fetch all source items (_get_all_items)
   b. Log INFO: migration start banner
   c. If zero items → log WARNING and return MigrationResult(0, 0, 0, [])

3. Resume index (only when resume=True):
   a. Build (title, type) set from destination (_build_dest_index)
   b. Log DEBUG: N items already in destination

4. Per-item loop:
   For each item (with 1-based counter N of M):
     a. If resume=True and (title, type) in dest_index:
        → Log INFO: "Skipping already-present item: <title> (<type>)"
        → result.skipped += 1; continue
     b. Resolve folder name (_resolve_folder_name)
     c. Ensure folder exists in destination (_ensure_folder)
     d. Log INFO: "Migrating item N of M: <title> (<type>)"
     e. t0 = time.perf_counter()
     f. Try: destination_gis.content.clone_items([item], folder=folder_name)
     g. Log DEBUG: clone duration
     h. On exception:
        → Build msg = f"Failed to clone '{title}' ({type}, {item_id}): {e}"
        → logger.error(msg)
        → result.failed += 1; result.failures.append({...})
     i. On success: result.migrated += 1

5. Complete:
   Log INFO: migration complete banner (migrated/skipped/failed counts)
   return result
```

### ArcGIS API patterns confirmed (research.md)

- `destination_gis.content.clone_items(items=[item], folder=folder_name)` — clone single item per call for per-item isolation
- `gis.content.search(query or "", max_items=-1)` — returns all matching items
- `item["ownerFolder"]` — folder ID string or `None` for root
- `gis.users.me.folders` — list of `{"id": ..., "title": ..., "username": ...}` dicts
- `gis.content.folders.create(folder="name")` — does NOT deduplicate; must pre-check

## Testing Strategy

All tests mock `arcgis.gis.GIS` and `ContentManager`. No live portal connections in unit tests.

| Test | Story | What it validates |
|---|---|---|
| `test_migrate_content_returns_migration_result` | US1/US3 | Return type is `MigrationResult` |
| `test_migrate_content_migrates_all_items` | US1 | `result.migrated == len(source_items)` |
| `test_migrate_content_resume_skips_existing` | US2 | Items in dest index are skipped |
| `test_migrate_content_resume_empty_dest_migrates_all` | US2 edge | `resume=True` with empty dest = full migration |
| `test_migrate_content_failed_item_does_not_raise` | US3/FR-006 | Per-item exception recorded, not raised |
| `test_migrate_content_all_fail_returns_result` | FR-006 | All-fail still returns `MigrationResult`, not raise |
| `test_migrate_content_same_url_raises` | FR-007 | `ValueError` on identical source/dest URL |
| `test_migrate_content_zero_items_returns_empty_result` | edge | Zero-item source returns early |
| `test_migrate_content_max_items_caps_search` | FR-009 | `max_items=2` limits items processed |
| `test_migrate_content_uses_env_credentials_when_no_gis` | FR-003 | `_connect_gis` called when `source_gis=None` |
