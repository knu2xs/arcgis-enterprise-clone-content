# Quickstart: Running the Content Migration

**Feature**: `003-make-data-migration-script`

---

## Prerequisites

1. ArcGIS Pro conda environment active (or equivalent with `arcgis` Python API installed)
2. `config/secrets.yml` populated with source and destination portal credentials:

```yaml
source:
  profile: ""          # set to use an ArcGIS named profile, OR fill url/username/password below
  url: "https://source-enterprise.example.com/arcgis"
  username: "my_username"
  password: "my_password"
destination:
  profile: ""
  url: "https://destination-enterprise.example.com/arcgis"
  username: "my_username"
  password: "my_password"
```

## Run the Migration

```bash
python scripts/make_data.py
```

The script will:

1. Read `migration.source_env` and `migration.destination_env` from `config/config.yml`
   (defaults: `"source"` and `"destination"`)
2. Connect to both portals using `secrets.yml` credentials
3. Discover all accessible items on the source portal
4. Clone each item to the mirrored folder in the destination portal
5. Write a complete log to `data/logs/clone_content_YYMMDDHHMM.log`
6. Print a summary to the console

## Check the Log

```bash
# List recent log files
Get-ChildItem data/logs/clone_content_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

## Change Source or Destination Portal

Edit `config/config.yml` — no code changes needed:

```yaml
environments:
  default:
    migration:
      source_env: "my_other_source"    # must match a top-level key in secrets.yml
      destination_env: "my_staging"    # must match a top-level key in secrets.yml
```

Then add matching blocks to `config/secrets.yml`:

```yaml
my_other_source:
  profile: ""
  url: "https://..."
  username: "..."
  password: "..."
my_staging:
  profile: ""
  url: "https://..."
  username: "..."
  password: "..."
```

## Resume an Interrupted Migration

`make_data.py` runs a fresh migration by default. To resume (skip already-present items),
modify the `migrate_content()` call in the script to pass `resume=True`, or wait for a
future feature that exposes resume as a config option.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `KeyError: 'source'` | `source` key missing from `secrets.yml` | Add the block to `secrets.yml` |
| `ValueError: Source and destination portals share the same URL` | Both env names point to same portal | Check `migration.source_env` vs `migration.destination_env` in config |
| `RuntimeError: Failed to connect` | Bad credentials or unreachable portal | Verify URL, username, password or profile in `secrets.yml` |
| Log file not created | `data/logs/` write permission denied | Check directory permissions |
