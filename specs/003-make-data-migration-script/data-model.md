# Data Model: Make-Data Migration Script

**Feature**: `003-make-data-migration-script`
**Date**: 2026-04-21

---

This feature is a script-level entry point — it introduces no new domain entities, database
tables, or persistent data structures. All portal content entities are owned by Feature 002.

## Configuration Schema (New Keys)

The following new keys are added to `config/config.yml` under `environments.default`:

```yaml
environments:
  default:
    migration:
      source_env: "source"       # env name key in secrets.yml for the source portal
      destination_env: "destination"  # env name key in secrets.yml for the destination portal
```

### Access Pattern

```python
from arcgis_cloning.config import load_config

cfg = load_config()
source_env = getattr(cfg.migration, "source_env", "source")         # → "source"
destination_env = getattr(cfg.migration, "destination_env", "destination")  # → "destination"
```

## Log File

The script produces one ephemeral file per invocation:

| Property | Value |
|---|---|
| Location | `{project_root}/data/logs/` |
| Filename pattern | `clone_content_YYMMDDHHMM.log` |
| Format example | `clone_content_2604211430.log` |
| Content | All log records from DEBUG through CRITICAL emitted during the run |
| Lifecycle | Created fresh on each invocation; never rotated or deleted by the script |

## Runtime State (not persisted)

| Name | Type | Description |
|---|---|---|
| `cfg` | `ConfigNode` | Loaded project configuration for the active environment |
| `source_env` | `str` | Portal environment name for the source; defaults to `"source"` |
| `destination_env` | `str` | Portal environment name for the destination; defaults to `"destination"` |
| `result` | `MigrationResult` | Return value from `migrate_content()`; logged then discarded |
| `log_file` | `pathlib.Path` | Full path to the log file for this run |
