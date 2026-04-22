---
title: Usage Reference
---
# Usage Reference

This page documents all `migrate_content()` parameters, the `MigrationResult` return
value, and common usage patterns. For a step-by-step first-run guide see the
[Quickstart](quickstart.md).

---

## migrate_content()

Clones items from a source ArcGIS portal to a destination portal. Returns a
`MigrationResult` summarising how many items were migrated, skipped, or failed.

```python
from arcgis_cloning import migrate_content

result = migrate_content()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_gis` | `GIS \| None` | `None` | Pre-built authenticated `GIS` object for the source portal. When provided, `source_env` and `secrets.yml` are ignored for the source connection. |
| `destination_gis` | `GIS \| None` | `None` | Pre-built authenticated `GIS` object for the destination portal. When provided, `destination_env` and `secrets.yml` are ignored for the destination connection. |
| `source_env` | `str` | `"source"` | Key in `config/secrets.yml` identifying the source portal credentials. Ignored when `source_gis` is provided. |
| `destination_env` | `str` | `"destination"` | Key in `config/secrets.yml` identifying the destination portal credentials. Ignored when `destination_gis` is provided. |
| `resume` | `bool` | `False` | When `True`, items already present in the destination (matched by **title and type**) are skipped rather than re-cloned. Defaults to `False` (fresh-run). |
| `query` | `str \| None` | `None` | ArcGIS content search query string passed to `gis.content.search()`. `None` returns all items accessible to the authenticated source user. |
| `max_items` | `int \| None` | `None` | Cap on the number of source items to process. `None` means no limit. Useful for safety checks and dry runs. |

!!! note
    `source_gis` and `destination_gis` are intended for testing or advanced scenarios
    where portal connections are managed externally. For normal use, set credentials in
    `config/secrets.yml` and let the function connect automatically.

---

## MigrationResult

`migrate_content()` returns a `MigrationResult` dataclass with four fields:

| Field | Type | Description |
|-------|------|-------------|
| `migrated` | `int` | Number of items successfully cloned to the destination portal. |
| `skipped` | `int` | Number of items skipped because they were already present in the destination (only non-zero in resume mode). |
| `failed` | `int` | Number of items that could not be cloned due to an error. |
| `failures` | `list[dict]` | Per-item failure records. Each entry has four keys: `item_id`, `title`, `type`, and `error`. |

```python
result = migrate_content()
print(f"Migrated: {result.migrated}")
print(f"Skipped:  {result.skipped}")
print(f"Failed:   {result.failed}")
```

!!! note
    `failed > 0` does **not** raise an exception. The migration always runs to
    completion; failures are collected and returned so callers can decide how to handle
    them. Only a pre-flight error (bad credentials, identical portals) raises an
    exception and exits the script with code `1`.

---

## Inspecting failures

Each record in `result.failures` is a plain `dict` with four keys:

| Key | Type | Contents |
|-----|------|----------|
| `item_id` | `str` | The ArcGIS item ID of the failed source item. |
| `title` | `str` | The title of the failed item. |
| `type` | `str` | The item type (e.g. `"Web Map"`, `"Dashboard"`). |
| `error` | `str` | The exception message from the failed clone attempt. |

```python
result = migrate_content()

if result.failed:
    print(f"{result.failed} item(s) failed:")
    for rec in result.failures:
        print(f"  [{rec['item_id']}] {rec['title']} ({rec['type']}): {rec['error']}")
```

---

## Log file

Every run produces a timestamped log file in `data/logs/`:

```
data/logs/clone_content_YYMMDDHHMM.log
```

The filename uses a **2-digit year** (`%y`), so a run at 14:30 on 21 April 2026
produces `clone_content_2604211430.log`.

| Log level | Written to file | Written to console |
|-----------|----------------|--------------------|
| `DEBUG` | ✓ (all records) | ✗ by default |
| `INFO` | ✓ | ✓ |
| `WARNING` | ✓ | ✓ |
| `ERROR` | ✓ | ✓ |
| `CRITICAL` | ✓ | ✓ |

The console level is controlled by `logging.level` in `config/config.yml`
(default: `DEBUG` — all records shown). The file always captures `DEBUG` and above,
providing a full audit trail regardless of the console setting.

---

## Resume mode

Use resume mode when a previous migration was interrupted and you want to continue
from where it left off — without re-cloning items that already arrived.

```python
# Fresh run (default) — clone everything regardless of destination state
result = migrate_content()

# Resume run — skip items already present in the destination
result = migrate_content(resume=True)
```

**How items are matched**: an item is considered *already present* when the destination
contains an item with the **same title and the same type**. If the title matches but the
type differs (e.g. a `"Web Map"` on the source vs. a `"Dashboard"` of the same name on
the destination), the item is treated as absent and will be cloned.

!!! tip
    Resume mode reads the full destination item index once at the start of the run, so
    it does not make additional API calls per item during the loop.

---

## Filtering items

### By content type or keyword — `query`

The `query` parameter is passed directly to `gis.content.search()`. Use ArcGIS query
syntax to filter the source items:

```python
# Migrate only Web Maps
result = migrate_content(query='type:"Web Map"')

# Migrate items owned by a specific user
result = migrate_content(query='owner:jsmith')

# Migrate items tagged "migration-ready"
result = migrate_content(query='tags:"migration-ready"')

# Combine conditions
result = migrate_content(query='type:"Dashboard" AND owner:jsmith')
```

### Limit item count — `max_items`

Use `max_items` to process only the first *N* source items. This is useful for
safety checks and dry runs before committing to a full migration:

```python
# Process only the first 10 items — useful for testing
result = migrate_content(max_items=10)
print(f"Test run: {result.migrated} migrated, {result.failed} failed")
```

!!! warning
    `max_items` truncates the source item list *after* the search query is applied.
    A value of `10` with `query='type:"Web Map"'` processes the first 10 Web Maps,
    not 10 items total.
