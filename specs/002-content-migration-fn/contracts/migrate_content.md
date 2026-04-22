# Contract: `migrate_content()`

**Module**: `arcgis_cloning._main`
**Exported via**: `arcgis_cloning.__init__`
**Feature**: `002-content-migration-fn` | **Date**: 2026-04-21

## Signature

```python
from arcgis.gis import GIS
from arcgis_cloning import migrate_content, MigrationResult

def migrate_content(
    source_gis: GIS | None = None,
    destination_gis: GIS | None = None,
    source_env: str = "source",
    destination_env: str = "destination",
    resume: bool = False,
    query: str | None = None,
    max_items: int | None = None,
) -> MigrationResult:
    ...
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `source_gis` | `GIS \| None` | `None` | Connected source portal. If `None`, connected via `secrets.yml` using `source_env`. |
| `destination_gis` | `GIS \| None` | `None` | Connected destination portal. If `None`, connected via `secrets.yml` using `destination_env`. |
| `source_env` | `str` | `"source"` | Environment name key in `secrets.yml` used when `source_gis` is `None`. |
| `destination_env` | `str` | `"destination"` | Environment name key in `secrets.yml` used when `destination_gis` is `None`. |
| `resume` | `bool` | `False` | If `True`, skip items whose `(title, type)` already exist in the destination. |
| `query` | `str \| None` | `None` | ArcGIS search query string to filter source items. `None` returns all accessible items. |
| `max_items` | `int \| None` | `None` | Maximum number of source items to process. `None` means no limit. |

## Return Value

`MigrationResult` dataclass:

```python
@dataclass
class MigrationResult:
    migrated: int          # items successfully cloned
    skipped: int           # items skipped (resume mode)
    failed: int            # items that raised during cloning
    failures: list[dict]   # per-failure: {item_id, title, type, error}
```

## Raises

| Exception | When |
|---|---|
| `ValueError` | Source and destination portal URLs are identical |
| `RuntimeError` | Connection to source or destination portal failed (pre-flight) |

**Note**: Per-item clone failures are **never** re-raised. They are recorded in
`MigrationResult.failures` and the function continues processing remaining items.

## Guarantees

- Always returns `MigrationResult` on completion (never raises due to per-item failure counts).
- Mirrors source folder structure in destination; creates missing folders before cloning.
- Paginates source search automatically; `max_items` caps total items processed (not page size).
- Resume comparison uses `(title, type)` as identity key — title+type uniqueness is assumed.

## Usage Examples

```python
from arcgis.gis import GIS
from arcgis_cloning import migrate_content

# Option A: provide pre-built GIS objects
source = GIS("https://source.example.com/arcgis", "admin", "password")
dest   = GIS(profile="my_dest_profile")
result = migrate_content(source_gis=source, destination_gis=dest)

# Option B: rely on secrets.yml defaults
result = migrate_content()

# Resume a partial migration
result = migrate_content(resume=True)

# Migrate only web maps, cap at 50
result = migrate_content(query="type:Web Map", max_items=50)

print(f"Migrated: {result.migrated}, Skipped: {result.skipped}, Failed: {result.failed}")
for f in result.failures:
    print(f"  FAIL {f[\"title\"]} ({f[\"type\"]}): {f[\"error\"]}")
```
