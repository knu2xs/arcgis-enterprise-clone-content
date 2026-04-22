# Quickstart: Content Migration Function

**Feature**: `002-content-migration-fn` | **Date**: 2026-04-21

## Prerequisites

1. `config/secrets.yml` populated with `source` and `destination` portal blocks:

```yaml
source:
  profile: "my_source_profile"   # OR use url/username/password below
  url: ""
  username: ""
  password: ""

destination:
  profile: ""
  url: "https://destination.example.com/arcgis"
  username: "admin"
  password: "s3cr3t"
```

2. Package installed (`pip install -e .` from project root or via `make env`).

## Basic Usage

### Migrate all content (fresh run)

```python
from arcgis_cloning import migrate_content

result = migrate_content()
print(f"Done: {result.migrated} migrated, {result.skipped} skipped, {result.failed} failed")
```

### Resume an interrupted migration

```python
result = migrate_content(resume=True)
# Items already present in destination are skipped automatically
```

### Migrate a filtered subset

```python
# Only Web Maps and Feature Services, capped at 100 items
result = migrate_content(
    query="type:Web Map OR type:Feature Service",
    max_items=100,
)
```

### Supply your own GIS connections

```python
from arcgis.gis import GIS
from arcgis_cloning import migrate_content

src  = GIS("https://source.example.com/arcgis", "user", "pass")
dest = GIS(profile="dest_profile")

result = migrate_content(source_gis=src, destination_gis=dest, resume=True)
```

### Inspect failures

```python
result = migrate_content(resume=True)
if result.failed:
    for f in result.failures:
        print(f"FAIL [{f['item_id']}] {f['title']} ({f['type']}): {f['error']}")
```

## Script Entry Point Pattern

Following the source-first architecture, scripts remain thin:

```python
# scripts/run_migration.py
import datetime
from pathlib import Path
from arcgis_cloning.utils import get_logger
from arcgis_cloning import migrate_content

script_pth = Path(__file__)
dir_logs = script_pth.parent.parent / "reports" / "logs"
dir_logs.mkdir(parents=True, exist_ok=True)
logfile = dir_logs / f"migration_{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}.log"

logger = get_logger(level="INFO", add_stream_handler=True, logfile_path=logfile)

result = migrate_content(resume=True)
logger.info(f"Migration complete: {result.migrated} migrated, {result.skipped} skipped, {result.failed} failed")
```
