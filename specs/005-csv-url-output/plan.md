# Implementation Plan: CSV URL Mapping Output for Migrated Content

**Branch**: `005-csv-url-output` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)

## Summary

Add an optional `url_csv_path` parameter to `migrate_content()` in `src/arcgis_cloning/_main.py`.
When provided, the function collects a URL mapping record (name, type, original URL, updated URL)
for each successfully cloned item and writes a CSV at that path after the migration loop completes.
Update `scripts/make_data.py` to accept an optional `--csv` CLI flag that derives the CSV path
from the same timestamp and `data/logs/` directory as the log file and passes it to
`migrate_content()`.

## Technical Context

**Language/Version**: Python 3.x (ArcGIS Pro conda environment)
**Primary Dependencies**: `pandas` (already imported in `_main.py`), `pathlib.Path`,
`csv` (stdlib) — no new dependencies
**Storage**: `data/logs/clone_content_YYMMDDHHMM.csv` when invoked via `make_data.py`
**Testing**: Unit tests in `testing/test_arcgis_cloning.py`; mock `clone_items()` return value
**Target Platform**: ArcGIS Pro conda environment; same as existing `_main.py`
**Performance Goals**: CSV written once after migration loop — no streaming
**Constraints**: Additive only — no existing parameter, return value, or behaviour of
`migrate_content()` may change when `url_csv_path` is `None` (FR-009)

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Source-First Architecture | ✅ PASS | CSV write is a pure output step; no logic changes to migration flow |
| II. Configuration-Driven Behavior | ✅ PASS | CSV path derived from config-driven log path in script; function accepts any path |
| III. Structured Observability | ✅ PASS | Log messages added for CSV write start and completion |
| IV. Testing Discipline | ✅ PASS | New unit tests cover CSV written, CSV omitted, empty CSV on zero migrated |
| V. Coding Standards | ✅ PASS | `pathlib.Path`, type hints, Google docstring, no `print()` |

## Project Structure

### Documentation (this feature)

```text
specs/005-csv-url-output/
├── plan.md              ← this file
├── spec.md              ← feature specification
├── tasks.md             ← task breakdown
└── checklists/
    └── requirements.md  ← specification quality checklist
```

### Source Code Changes

```text
src/arcgis_cloning/
└── _main.py             ← add url_csv_path param; collect URL rows; write CSV

scripts/
└── make_data.py         ← add --csv flag; derive csv_file; pass to migrate_content()

testing/
└── test_arcgis_cloning.py  ← add tests for CSV output
```

**Structure Decision**: Modify three existing files. No new modules needed.
`pandas.DataFrame.to_csv()` is used for CSV output since `pandas` is already a dependency.

## Implementation Design

### `_main.py` changes

**New parameter on `migrate_content()`**:

```python
url_csv_path: Path | str | None = None,
```

**Pre-flight validation** (before the migration loop, after portal connection):

```python
if url_csv_path is not None:
    csv_path = Path(url_csv_path)
    if not csv_path.parent.exists():
        msg = f"CSV output directory does not exist: '{csv_path.parent}'"
        logger.error(msg)
        raise ValueError(msg)
```

**URL row accumulator** (declared before the migration loop):

```python
url_rows: list[dict] = []
```

**Capture cloned item URL** (inside the successful `clone_items()` branch):

```python
cloned = dest_gis.content.clone_items(items=[item], folder=folder_name)
dest_url = cloned[0].url if cloned else None
url_rows.append({
    "name": title,
    "type": item_type,
    "original_url": item.url or "",
    "updated_url": dest_url or "",
})
result.migrated += 1
```

**Write CSV after the loop** (after the final `logger.info` migration complete line):

```python
if url_csv_path is not None:
    csv_path = Path(url_csv_path)
    logger.debug(f"Writing URL mapping CSV: {csv_path} ({len(url_rows)} rows)")
    pd.DataFrame(url_rows, columns=["name", "type", "original_url", "updated_url"]).to_csv(
        csv_path, index=False
    )
    logger.info(f"URL mapping CSV written: {csv_path}")
```

### `make_data.py` changes

Add `import argparse` and parse `--csv` / `--no-csv` after the existing imports.

```python
import argparse

parser = argparse.ArgumentParser(description="Run ArcGIS portal content migration.")
parser.add_argument(
    "--csv",
    action="store_true",
    default=False,
    help="Write a URL mapping CSV alongside the log file.",
)
args = parser.parse_args()
```

Derive the CSV path from the same stem as the log file (same `date_string`):

```python
csv_file = log_dir / f'clone_content_{date_string}.csv' if args.csv else None
```

Pass to `migrate_content()`:

```python
result = migrate_content(
    source_env=source_env,
    destination_env=destination_env,
    url_csv_path=csv_file,
)
```

Log the CSV path when enabled:

```python
if csv_file:
    logger.info(f'CSV output: {csv_file}')
```
