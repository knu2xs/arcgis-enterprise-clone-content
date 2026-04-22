# Data Model: Content Migration Function

**Feature**: `002-content-migration-fn` | **Date**: 2026-04-21

## Entities

### `MigrationResult` (dataclass)

The structured return value of `migrate_content()`. Immutable summary of a single migration run.

| Field | Type | Description |
|---|---|---|
| `migrated` | `int` | Count of items successfully cloned to the destination |
| `skipped` | `int` | Count of items skipped because they were already present (resume mode only) |
| `failed` | `int` | Count of items that raised an exception during cloning |
| `failures` | `list[dict]` | One entry per failed item (see `ItemFailure` schema below) |

**Invariant**: `migrated + skipped + failed == total source items processed`

---

### `ItemFailure` (dict schema within `MigrationResult.failures`)

Each entry in `MigrationResult.failures` is a plain dict with these keys:

| Key | Type | Description |
|---|---|---|
| `item_id` | `str` | ArcGIS item ID of the failed source item |
| `title` | `str` | Display title of the failed source item |
| `type` | `str` | ArcGIS item type string (e.g., `"Feature Service"`, `"Web Map"`) |
| `error` | `str` | Exception message captured at the point of failure |

---

### `ContentItem` (ArcGIS API `Item` — external, not owned by this package)

An `arcgis.gis.Item` object retrieved from the source portal. Relevant attributes used:

| Attribute | Access pattern | Notes |
|---|---|---|
| Item ID | `item.id` | Unique portal identifier |
| Title | `item.title` | Used for INFO logging and resume comparison |
| Type | `item.type` | Used for INFO logging and resume comparison |
| Owner folder ID | `item["ownerFolder"]` | `None` for root; folder ID string otherwise |

---

## State Transitions

```
Source item
    │
    ├─ [resume=True, (title,type) in dest_index] ──► SKIPPED  (result.skipped += 1)
    │
    ├─ [clone_items() succeeds] ──────────────────► MIGRATED  (result.migrated += 1)
    │
    └─ [clone_items() raises] ────────────────────► FAILED    (result.failed += 1,
                                                               result.failures.append({...}))
```

---

## Folder Mapping (runtime, not persisted)

During execution the function builds an ephemeral mapping to resolve source folder IDs to
folder names and to ensure the folder exists in the destination before cloning:

```
src_gis.users.me.folders
  → {folder_id: folder_name}  (built once before the item loop)

dest_gis.users.me.folders
  → {folder_name: True}       (checked before creating; refreshed per unique folder name)
```

This mapping is not persisted between calls.
