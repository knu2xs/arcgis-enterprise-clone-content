# ArcGIS Enterprise Clone Content

<!--start-->

## What it does

**ArcGIS Enterprise Clone Content** is a Python tool for migrating content between
ArcGIS portals (ArcGIS Enterprise or ArcGIS Online). Point it at a source and a
destination portal and it clones all accessible items — preserving folder structure
and handling errors per-item so one bad item never stops the run.

Key capabilities:

- **Fresh run** — clone everything from source to destination.
- **Resume mode** — skip items already present in the destination (matched by title
  and type), so interrupted runs can be continued safely.
- **Folder mirroring** — recreates the source owner's folder structure in the
  destination portal.
- **Structured logging** — a full DEBUG-level audit trail is written to a timestamped
  log file at `data/logs/clone_content_YYMMDDHHMM.log`.
- **Failure isolation** — per-item failures are captured and reported without stopping
  the migration; inspect `MigrationResult.failures` for details.

## Prerequisites

- **ArcGIS Pro** (provides the `arcgis` Python package and `arcpy`) — or the
  standalone **ArcGIS API for Python** in a compatible conda environment.
- **Portal credentials** — source and destination portal connection details stored in
  `config/secrets.yml` (copied from `config/secrets_template.yml`).

## Quick Start

**1. Configure credentials**

Copy the secrets template to a new file protected by `.gitignore` so it will not be 
committed to version control. This protects your portal credentials while allowing 
you to customize them for your environment.

```bash
cp config/secrets_template.yml config/secrets.yml
```

Open `config/secrets.yml` and fill in your portal details:

```yaml
source:
  profile: ""       # ArcGIS named profile (takes precedence if set)
  url: "https://source-portal.example.com/arcgis"
  username: "your_source_username"
  password: "your_source_password"

destination:
  profile: ""
  url: "https://destination-portal.example.com/arcgis"
  username: "your_destination_username"
  password: "your_destination_password"
```

**2. Run the migration (CLI)**

```bash
make data
```

A timestamped log is written to `data/logs/clone_content_YYMMDDHHMM.log`.
The final console line shows: `Migration complete: migrated=N, skipped=N, failed=N`.
<!--end-->

<p><small>Project based on the <a target="_blank" href="https://github.com/knu2xs/cookiecutter-geoai">cookiecutter 
GeoAI project template</a>. This template, in turn, is simply an extension and light modification of the 
<a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project 
template</a>. #cookiecutterdatascience</small></p>
