---
title: Quickstart
---
# Quick Start

This page walks you through setting up and running your first ArcGIS portal content
migration in four steps.

---

## Step 1 — Configure credentials

All portal credentials live in `config/secrets.yml`, which is **never committed** to
version control.

**1.** Copy the template to create your own file:

```bash
cp config/secrets_template.yml config/secrets.yml
```

**2.** Open `config/secrets.yml` and fill in your source and destination portal details.

!!! tip "Profile vs. URL authentication"
    You can authenticate with an **ArcGIS named profile** (set up via ArcGIS Pro or
    the ArcGIS API) *or* with an explicit URL, username, and password.
    If `profile` is set to a non-empty string, the other three fields are ignored.

```yaml
source:
  profile: ""                                            # ArcGIS named profile (takes precedence)
  url: "https://source-arcgis-enterprise.example.com/arcgis"
  username: "your_source_username"
  password: "your_source_password"

destination:
  profile: ""
  url: "https://destination-arcgis-enterprise.example.com/arcgis"
  username: "your_destination_username"
  password: "your_destination_password"
```

!!! warning
    `config/secrets.yml` is listed in `.gitignore`. **Never commit credentials.**

---

## Step 2 — Configure portal environment names (optional)

The migration reads the active portal environment names from `config/config.yml`.
The default values (`source` and `destination`) match the sections in
`secrets.yml` created in Step 1 — **no change is required unless you want to use
different key names.**

```yaml
environments:
  default:
    migration:
      source_env: "source"        # key in secrets.yml for the source portal
      destination_env: "destination"  # key in secrets.yml for the destination portal
```

!!! note
    The key names in `migration.source_env` / `migration.destination_env` must exactly
    match the top-level keys in `secrets.yml`. If you rename them, update both files.

---

## Step 3a — Run the migration (CLI)

From the project root:

```bash
make data
```

You will see progress messages in the console. A full DEBUG-level audit trail is written
to a timestamped log file:

```
data/logs/clone_content_YYMMDDHHMM.log
```

**Example summary line** (printed at the end of a successful run):

```
INFO  Migration complete: migrated=42, skipped=0, failed=0
```

!!! tip "Interpreting the summary"
    - `migrated` — items successfully cloned to the destination portal.
    - `skipped` — items that already existed in the destination (resume mode only).
    - `failed` — items that could not be cloned; details are in the log file and in
      `MigrationResult.failures`.

!!! danger "If the migration fails immediately on startup"
    If `secrets.yml` is missing or incomplete, the migration exits with code `1` and
    logs a `KeyError`. Copy `config/secrets_template.yml` to `config/secrets.yml`
    and fill in your portal credentials before re-running.

---

## Step 3b — Run the migration (Python API)

You can also call `migrate_content()` directly from Python:

```python
from arcgis_cloning import migrate_content

# Fresh run — clone everything from source to destination
result = migrate_content()
print(f"Migrated: {result.migrated}, Skipped: {result.skipped}, Failed: {result.failed}")
```

**Resume mode** — skip items already present in the destination:

```python
result = migrate_content(resume=True)
```

**Inspect per-item failures:**

```python
for failure in result.failures:
    print(failure["title"], failure["type"], failure["error"])
```

!!! tip
    See the [Usage Reference](usage.md) page for all available parameters,
    `MigrationResult` fields, filtering options, and log file details.
