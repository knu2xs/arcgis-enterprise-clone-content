# Interface Contract: `scripts/make_data.py`

**Feature**: `003-make-data-migration-script`
**Date**: 2026-04-21
**Contract type**: CLI entry point (command-line invocation)

---

## Invocation

```bash
python scripts/make_data.py
```

No command-line arguments are accepted. All configuration is read from `config/config.yml`
and `config/secrets.yml`.

## Exit Codes

| Code | Condition |
|---|---|
| `0` | Migration completed (including runs with per-item failures) |
| `1` | Pre-flight failure: bad credentials, unreachable portal, same source/destination URL, missing secrets key |

## Side Effects

| Side Effect | Description |
|---|---|
| Log file created | `data/logs/clone_content_YYMMDDHHMM.log` written to project root–relative path |
| `data/logs/` created | Directory created if absent; no error if already present |
| Portal content cloned | `migrate_content()` clones items from source portal to destination portal |

## Inputs (read from config)

| Config key | Default | Description |
|---|---|---|
| `migration.source_env` | `"source"` | Key name in `secrets.yml` for source portal credentials |
| `migration.destination_env` | `"destination"` | Key name in `secrets.yml` for destination portal credentials |
| `logging.level` | `"DEBUG"` | Console log level; file handler always uses `DEBUG` |

## Outputs

| Output | Description |
|---|---|
| Log file | Full DEBUG-level audit trail of the migration at `data/logs/clone_content_YYMMDDHHMM.log` |
| Console | INFO-level progress lines and final summary |
| Exit code | `0` on success, `1` on pre-flight failure |

## Log File Format

The log file is plain text with standard Python logging format:

```
2026-04-21 14:30:01,234 - arcgis_cloning - INFO - Migration started | source=https://... | destination=https://... | resume=False | query=None | items_found=42
2026-04-21 14:30:01,500 - arcgis_cloning - INFO - Migrating item 1 of 42: My Map (Web Map)
...
2026-04-21 14:31:05,123 - make_data - INFO - Migration complete: migrated=41, skipped=0, failed=1
```

## Dependencies

- `arcgis_cloning.migrate_content` (Feature 002) — must be installed or on `sys.path`
- `arcgis_cloning.config.load_config` — for reading `migration.*` config keys
- `arcgis_cloning.utils.get_logger` — for root logger setup
- `config/secrets.yml` — portal credentials for the resolved environment names
