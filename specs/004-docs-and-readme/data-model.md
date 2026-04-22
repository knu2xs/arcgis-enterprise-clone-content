# Data Model: Documentation and README

*This feature is documentation-only — no data models, database schemas, or Python
dataclasses are introduced. This file documents the **content model** for the pages
being created or updated.*

---

## Page Inventory

| File | Action | Sections |
|------|--------|----------|
| `README.md` | Rewrite inside `<!--start-->`/`<!--end-->` | What it does, Prerequisites, Quick Start (5 steps) |
| `docsrc/mkdocs/quickstart.md` | Create | Steps 1–5 with full detail, expected output, troubleshooting |
| `docsrc/mkdocs/usage.md` | Create | Parameters table, MigrationResult table, log file, resume mode, filtering |
| `docsrc/mkdocs/configuration.md` | Update | Replace placeholder envs; add migration key; add secrets schema |
| `docsrc/mkdocs.yml` | Update | Nav order: Home → Quickstart → Usage → Configuration → API → Cookiecutter |

---

## README.md content model

```
<!--start-->
## What it does
  One paragraph: ArcGIS portal content migration tool.
  Key capabilities: fresh run, resume mode, folder mirroring, structured log.

## Prerequisites
  - ArcGIS Pro (provides arcgis Python package)
  - Conda environment (make env)
  - Portal credentials in config/secrets.yml

## Quick Start
  1. Set up the environment       → make env
  2. Configure credentials        → copy secrets_template.yml → secrets.yml
  3. (Optional) Adjust portal names → config.yml migration.source_env / destination_env
  4. Run the migration (CLI)      → python scripts/make_data.py
  5. Run the migration (Python)   → from arcgis_cloning import migrate_content; migrate_content()
<!--end-->
<small>template credit</small>
```

---

## quickstart.md content model

```
title: Quickstart

# Quick Start

## Step 1 — Set up the environment
  make env  (or conda activate ...)

## Step 2 — Configure credentials
  !!! tip "Profile vs. URL authentication"
  code block: copy secrets_template.yml → secrets.yml
  YAML example: source + destination blocks (profile path + URL path)
  !!! warning "Never commit secrets.yml"

## Step 3 — Configure portal environment names (optional)
  config.yml migration block
  !!! note "Defaults"

## Step 4 — Run via CLI
  python scripts/make_data.py
  Expected console output snippet
  Log file location: data/logs/clone_content_YYMMDDHHMM.log
  !!! tip "Interpreting the summary line"

## Step 5 — Run via Python API
  from arcgis_cloning import migrate_content
  result = migrate_content()
  print(result.migrated, result.skipped, result.failed)
  --- resume mode ---
  result = migrate_content(resume=True)
```

---

## usage.md content model

```
title: Usage Reference

# Usage Reference

## migrate_content()

Table: all 7 parameters
  | Parameter | Type | Default | Description |
  | source_gis | GIS | None | Pre-built source GIS (skips secrets.yml) |
  | destination_gis | GIS | None | Pre-built destination GIS |
  | source_env | str | "source" | Key in secrets.yml |
  | destination_env | str | "destination" | Key in secrets.yml |
  | resume | bool | False | Skip items already in destination |
  | query | str | None | Item search filter |
  | max_items | int | None | Cap on items processed |

## MigrationResult

Table: 4 fields
  | Field | Type | Description |
  | migrated | int | Items successfully cloned |
  | skipped | int | Items skipped (resume mode) |
  | failed | int | Items that raised an error |
  | failures | list[dict] | Per-item failure records (item_id, title, type, error) |

## Inspecting failures

Code example: iterating result.failures

## Log file

Location: data/logs/clone_content_YYMMDDHHMM.log
Format: YYMMDDHHMM (2-digit year)
Content: DEBUG-level full audit trail; console shows config-level (default DEBUG)

## Resume mode

When to use, how it matches items (title + type), fresh-run vs. resume

## Filtering items

query parameter examples (by owner, type, tag)
max_items for safety testing
```

---

## configuration.md update model

### Sections to change

| Section | Change |
|---------|--------|
| `config.yml` example block | Replace `dev`/`test`/`prod` with `source`/`destination` + add `migration:` key |
| `secrets.yml` example | Replace single-block generic example with `source:` + `destination:` blocks showing `profile`, `url`, `username`, `password` |
| New note after secrets example | Add `!!! tip` explaining profile takes precedence over url+credentials |

### config.yml example target content

```yaml
environments:

  source:
    logging:
      level: DEBUG

  destination:
    logging:
      level: INFO

  default:
    logging:
      level: DEBUG
    data:
      input: "data/raw/input_data.csv"
      output: "data/processed/processed.gdb/output_data"
    migration:
      source_env: "source"
      destination_env: "destination"
```

### secrets.yml example target content

```yaml
source:
  profile: ""        # ArcGIS named profile (takes precedence if set)
  url: "https://source-arcgis-enterprise.example.com/arcgis"
  username: "your_source_username"
  password: "your_source_password"

destination:
  profile: ""
  url: "https://destination-arcgis-enterprise.example.com/arcgis"
  username: "your_destination_username"
  password: "your_destination_password"
```

---

## mkdocs.yml nav target

```yaml
nav:
  - Home: index.md
  - Quickstart: quickstart.md
  - Usage: usage.md
  - Configuration: configuration.md
  - API: api.md
  - Cookiecutter Reference: cookiecutter_reference.md
```
