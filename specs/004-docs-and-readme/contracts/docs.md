# Documentation Contracts: Documentation and README

This file defines the **interface contract** for each documentation page in this
feature — its purpose, required sections, nav placement, and acceptance criteria.
These contracts are the authoritative reference for the `/speckit.tasks` and
`/speckit.implement` phases.

---

## Contract: README.md

**File**: `README.md` (project root)
**Action**: Rewrite content inside `<!--start-->` / `<!--end-->` markers

### Purpose

Primary entry point for any visitor who discovers the project on GitHub. Must answer
in under 60 seconds: (1) what the tool does, (2) what is needed to run it, and
(3) how to run it.

### Required Sections

| Section | Heading | Required Content |
|---------|---------|-----------------|
| What it does | `## What it does` | One paragraph describing ArcGIS portal content migration; mentions fresh-run, resume mode, folder mirroring, and timestamped log output |
| Prerequisites | `## Prerequisites` | Bullet list: ArcGIS Pro (or ArcGIS API for Python), conda environment (`make env`), `config/secrets.yml` credentials |
| Quick Start | `## Quick Start` | Numbered list, 5 steps; each step has exactly one code block |

### Constraints

- All changes MUST be inside the `<!--start-->` / `<!--end-->` markers.
- Content outside the markers (template credit `<small>` block) MUST NOT be modified.
- Every heading and code block must render correctly in both GitHub's CommonMark renderer
  and as a MkDocs Material page fragment.

### Acceptance Criteria

- No generic placeholder text remains (no "Useful tooling for cloning", no
  "Start Building", no cookiecutter boilerplate).
- A reader with zero prior knowledge can complete a first run by following only the
  Quick Start section.

---

## Contract: docsrc/mkdocs/quickstart.md

**File**: `docsrc/mkdocs/quickstart.md`
**Action**: Create (new file)

### Purpose

Expanded step-by-step guide for first-time users. Covers everything in the README
Quick Start but adds admonitions, expected output, troubleshooting notes, and a
Python API alternative.

### Front Matter

```yaml
---
title: Quickstart
---
```

### Required Sections

| Section | Heading | Required Content |
|---------|---------|-----------------|
| Step 1 | `## Step 1 — Set up the environment` | `make env`, `conda activate` |
| Step 2 | `## Step 2 — Configure credentials` | Copy template; YAML example with `source:` + `destination:` showing both `profile` and URL paths; `!!! warning` about not committing; `!!! tip` about profile precedence |
| Step 3 | `## Step 3 — Configure portal environment names (optional)` | config.yml migration block; `!!! note` about defaults |
| Step 4 | `## Step 4 — Run the migration (CLI)` | `python scripts/make_data.py`; expected console output; log file path; `!!! tip` interpreting summary line; exit code 1 on pre-flight error |
| Step 5 | `## Step 5 — Run the migration (Python API)` | `migrate_content()` basic call; resume mode; inspect failures; link to Usage Reference |

### Constraints

- Steps must be numbered and sequentially ordered.
- Code blocks must use fenced code with language identifiers (`bash`, `yaml`, `python`).
- Must not duplicate the full `migrate_content()` parameter reference — link to
  `usage.md` instead.

### Acceptance Criteria

- Following the page verbatim (with valid credentials) results in a completed migration.
- No `NEEDS CLARIFICATION` or placeholder text remains.

---

## Contract: docsrc/mkdocs/usage.md

**File**: `docsrc/mkdocs/usage.md`
**Action**: Create (new file)

### Purpose

Comprehensive reference for `migrate_content()` parameters and `MigrationResult`
fields. Supplements the auto-generated docstring rendering in `api.md` with scannable
tables and runnable code examples.

### Front Matter

```yaml
---
title: Usage Reference
---
```

### Required Sections

| Section | Heading | Required Content |
|---------|---------|-----------------|
| Function overview | `## migrate_content()` | One-sentence description + pipe-delimited parameter table (all 7 params) |
| Result fields | `## MigrationResult` | Pipe-delimited table (migrated, skipped, failed, failures) with types and descriptions |
| Failure inspection | `## Inspecting failures` | Code example iterating `result.failures`; table of dict keys (item_id, title, type, error) |
| Log file | `## Log file` | Location pattern, YYMMDDHHMM format, what levels are written to file vs. console |
| Resume mode | `## Resume mode` | When to use; matching logic (title + type); comparison with fresh-run |
| Filtering | `## Filtering items` | `query` parameter examples; `max_items` use case |

### Parameters Table

All 7 parameters must appear:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_gis` | `GIS \| None` | `None` | Pre-built source portal GIS object; skips `secrets.yml` lookup when provided |
| `destination_gis` | `GIS \| None` | `None` | Pre-built destination portal GIS object |
| `source_env` | `str` | `"source"` | Key in `secrets.yml` for the source portal; ignored when `source_gis` is provided |
| `destination_env` | `str` | `"destination"` | Key in `secrets.yml` for the destination portal; ignored when `destination_gis` is provided |
| `resume` | `bool` | `False` | Skip items already present in destination (matched by title and type) |
| `query` | `str \| None` | `None` | ArcGIS content search query; `None` returns all items accessible to the authenticated user |
| `max_items` | `int \| None` | `None` | Cap on the number of source items to process; `None` means no limit |

### Constraints

- Must NOT reproduce the full docstring (that is covered by `api.md`).
- All code examples must be runnable with only `arcgis_cloning` and standard-library
  imports.

### Acceptance Criteria

- SC-004: Every parameter can be looked up without reading source code.
- A reader can correctly configure a resume-mode run with a custom query after reading
  this page alone.

---

## Contract: docsrc/mkdocs/configuration.md

**File**: `docsrc/mkdocs/configuration.md`
**Action**: Update (existing file)

### Purpose

Reference for the two YAML configuration files (`config.yml` and `secrets.yml`).
Currently contains generic `dev`/`test`/`prod` placeholder examples that do not match
this project.

### Changes Required

1. **config.yml example block**: Replace the `dev`/`test`/`prod` environment block
   with a `source`/`destination` block that includes the `migration:` key under
   `default`.

2. **secrets.yml example**: Replace the single-block generic example with a `source:`
   + `destination:` block (matching `secrets_template.yml`) that shows:
   - `profile` field (with `!!! tip` explaining it takes precedence)
   - `url`, `username`, `password` fields

3. **Custom environments tip**: Update the `!!! tip "Custom environments"` admonition
   to reference the ArcGIS portal naming convention rather than `staging`.

### Constraints

- The two-part page structure (config.yml section then secrets.yml section) must be
  preserved.
- All other content in the file (file layout table, merge order explanation, copy
  instructions) should be kept unless it directly references the placeholder envs.

### Acceptance Criteria

- FR-007 and FR-008 satisfied.
- A reader can copy each YAML example verbatim and it will match the real project
  configuration.
- No `dev`, `test`, or `prod` environment names appear in examples.

---

## Contract: docsrc/mkdocs.yml

**File**: `docsrc/mkdocs.yml`
**Action**: Update nav only

### Required nav

```yaml
nav:
  - Home: index.md
  - Quickstart: quickstart.md
  - Usage: usage.md
  - Configuration: configuration.md
  - API: api.md
  - Cookiecutter Reference: cookiecutter_reference.md
```

### Constraints

- Only the `nav:` section changes. All other keys (`site_name`, `theme`, plugins,
  `markdown_extensions`, etc.) must not be modified.

### Acceptance Criteria

- FR-009 satisfied: Quickstart and Usage appear in the site navigation.
- `mkdocs build` resolves all nav pages without errors.
