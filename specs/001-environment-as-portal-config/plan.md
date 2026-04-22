# Implementation Plan: Environment as Portal Configuration

**Feature**: `001-environment-as-portal-config`
**Branch**: `001-environment-as-portal-config`
**Created**: 2026-04-21
**Spec**: [spec.md](./spec.md)

---

## 1. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python 3.x | No new dependencies |
| Config serialization | PyYAML (`yaml.safe_load`) | Already used in `config.py` |
| Config access | `ConfigNode` (project-internal) | Existing class; no changes required |
| Merging | `_deep_merge` (project-internal) | Existing helper; no changes required |
| Environment control | `PROJECT_ENV` environment variable | Already wired; only default value changes |
| Testing | PyTest | Existing framework; new test functions added |

No new packages are added to `pyproject.toml` or `environment.yml`.

---

## 2. Architecture

The configuration system is already portal-agnostic. The existing `load_config`,
`load_secrets`, and `get_available_environments` functions accept arbitrary environment
names and read directly from YAML — no code changes are needed beyond:

1. Updating the `ENVIRONMENT` default string from `"dev"` to `"source"`.
2. Updating documentation (module docstring + `config.yml` header comments) to reflect
   the portal model.

The `load_secrets` signature is **not** changed. Callers load the full secrets file and
access portal credentials via the top-level key that matches the environment name:

```python
source_sec = load_secrets()          # returns full ConfigNode
url = source_sec.source.url          # portal-keyed access
```

This matches the existing `secrets.yml` structure, which already has `source` and
`destination` as top-level keys.

### Merge order (unchanged)

```
top-level config.yml keys
  → environments.default   (shared fallbacks: logging.level, data.input, data.output)
    → environments.<name>  (portal-specific overrides)
```

---

## 3. File Structure — Exact Changes

### 3.1 `config/config.yml` *(documentation-only change)*

Update the header comment block that references `dev / test / prod` to describe the
portal-based model. The `source:` and `destination:` environment blocks already exist
and are correctly empty (inheriting all values from `default`).

**Lines to change** — header comment block (lines 8–11):

```yaml
# Before
# ENVIRONMENT constant in src/arcgis_cloning/config.py
# (or the PROJECT_ENV environment variable) to switch between dev / test / prod.

# After
# ENVIRONMENT constant in src/arcgis_cloning/config.py
# (or the PROJECT_ENV environment variable) to switch between source / destination.
```

**Lines to change** — `environments` section comment (around line 27):

```yaml
# Before
# The special "default" section provides fallback values for any key that is
# not explicitly defined in a named environment (dev / test / prod).

# After
# The special "default" section provides fallback values for any key that is
# not explicitly defined in a named portal environment (source / destination).
```

No structural YAML changes are needed; `source:` and `destination:` blocks already exist.

---

### 3.2 `config/secrets_template.yml` *(new file)*

This file does not currently exist. Create it to mirror `secrets.yml` with the same
structure but clearly labelled placeholder values, so that onboarding developers know
exactly what keys to provide.

```yaml
# =============================================================================
# Secrets Configuration Template - arcgis-enterprise-clone-content
# =============================================================================
# Copy this file to secrets.yml and fill in your actual values.
# NEVER commit secrets.yml to version control!
#
# Ensure secrets.yml is listed in .gitignore.
# =============================================================================

source:
  url: "https://source-arcgis-enterprise.example.com/arcgis"
  username: "source_username"
  password: "source_password"

destination:
  url: "https://destination-arcgis-enterprise.example.com/arcgis"
  username: "destination_username"
  password: "destination_password"
```

!!! note
    The existing `secrets.yml` has two-space leading indentation on `source:` and
    `destination:`. While `yaml.safe_load` parses this correctly (the first element's
    column sets the root indent baseline), `secrets_template.yml` is written with
    zero-indented root keys (standard practice) and `secrets.yml` should be normalised
    to match during this task.

---

### 3.3 `src/arcgis_cloning/config.py` *(two targeted changes)*

#### Change A — Default environment constant

```python
# Before
ENVIRONMENT: str = os.environ.get("PROJECT_ENV", "dev")

# After
ENVIRONMENT: str = os.environ.get("PROJECT_ENV", "source")
```

#### Change B — Module docstring

Replace the module-level docstring to reflect the portal model and update the usage
example. The key changes are:

- Replace "deployment stages" framing with "portal environment" framing.
- Replace `secrets.esri.gis_url` example with `secrets.source.url` /
  `secrets.destination.url`.
- Add the recommended per-call pattern for clone scripts.

Full replacement docstring:

```python
"""
Configuration loader for the project.

Reads settings from YAML configuration files in the ``config/`` directory using
a singleton pattern so the files are parsed once and reused across modules.

The YAML config supports *portal environment* sections defined under the
``environments`` key in ``config.yml``.  A special ``default`` sub-section
provides fallback values for any key that is not overridden in a named portal.
The merge order is:

1. Top-level keys in ``config.yml``
2. ``environments.default`` (if present) — overrides top-level defaults
3. ``environments.<active-env>`` — overrides both of the above

Environments represent connectable ArcGIS Enterprise portal instances (e.g.
``source``, ``destination``).  Add, rename, or remove portal environments by
editing the ``environments`` block in ``config.yml`` — no Python changes required.
Change the :pydata:`ENVIRONMENT` constant below — or set the ``PROJECT_ENV``
environment variable — to select the active portal.

Usage — module-level singleton (single portal)::

    from arcgis_cloning.config import config, secrets, ENVIRONMENT

    # dot-notation access
    log_level = config.logging.level

    # dict-style access
    input_path = config["data"]["input"]

    # secrets for the source portal (loaded from config/secrets.yml)
    gis_url = secrets.source.url

    # check current portal environment
    print(f"Running against {ENVIRONMENT} portal")

Usage — per-call pattern (clone scripts that need both portals)::

    from arcgis_cloning.config import load_config, load_secrets

    source_cfg = load_config("source")
    source_sec = load_secrets()
    dest_cfg   = load_config("destination")
    dest_sec   = load_secrets()

    source_url   = source_sec.source.url
    dest_url     = dest_sec.destination.url
    log_level    = source_cfg.logging.level
    output_path  = dest_cfg.data.output
"""
```

---

## 4. Implementation Steps

Ordered tasks suitable for generating a `tasks.md`:

### Task 1 — Update `config/config.yml` header comment

- File: `config/config.yml`
- Change: Replace `dev / test / prod` references in the two comment blocks with
  `source / destination`.
- Risk: None — comments only.

### Task 2 — Create `config/secrets_template.yml`

- File: `config/secrets_template.yml` *(create)*
- Change: New file with `source` and `destination` blocks containing clearly labelled
  placeholder values (see §3.2).
- Risk: None — new file, no existing callers.

### Task 3 — Normalise `config/secrets.yml` root indentation

- File: `config/secrets.yml`
- Change: Remove the two-space leading indent from `source:` and `destination:` so the
  file matches the template style (root keys at column 0).
- Risk: Low. `yaml.safe_load` already parses both forms identically; this is cosmetic.
- Note: `secrets.yml` is gitignored; communicate to team members to update their local
  copies.

### Task 4 — Change `ENVIRONMENT` default in `config.py`

- File: `src/arcgis_cloning/config.py`
- Change: `os.environ.get("PROJECT_ENV", "dev")` → `os.environ.get("PROJECT_ENV", "source")`
- Risk: **Breaking for any caller that relied on the implicit `"dev"` default and had a
  `dev` block in their local `config.yml`.** However, `config.yml` no longer has a `dev`
  block, so this was already broken; the fix is correct.

### Task 5 — Update module docstring in `config.py`

- File: `src/arcgis_cloning/config.py`
- Change: Replace module-level docstring with portal-model version (see §3.3 Change B).
- Risk: None — documentation only; no runtime behaviour changes.

### Task 6 — Write new tests in `testing/test_arcgis_cloning.py`

- File: `testing/test_arcgis_cloning.py`
- Change: Add test functions (see §5 below). Keep existing `test_example`.
- Risk: None — additive only.

### Task 7 — Verify `get_available_environments` returns correct list

- This is covered by the new tests (Task 6); no code change required. Included as a
  verification step.

---

## 5. Testing Strategy

### Existing tests

`test_arcgis_cloning.py` currently contains one stub test (`test_example`) that does not
reference any environment name. No modifications to existing tests are needed.

### New test functions to add

Add the following to `testing/test_arcgis_cloning.py`. Each test is independent and
requires no ArcPy or network access.

```python
import os
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

dir_prj = Path(__file__).parent.parent
dir_config = dir_prj / "config"

# ---------------------------------------------------------------------------
# Tests: load_config
# ---------------------------------------------------------------------------

def test_load_config_source_returns_config_node():
    """load_config("source") returns a ConfigNode with inherited defaults."""
    from arcgis_cloning.config import load_config
    cfg = load_config("source")
    assert cfg.logging.level == "DEBUG"
    assert cfg.data.input == "data/raw/input_data.csv"


def test_load_config_destination_returns_config_node():
    """load_config("destination") returns a ConfigNode with inherited defaults."""
    from arcgis_cloning.config import load_config
    cfg = load_config("destination")
    assert cfg.logging.level == "DEBUG"
    assert cfg.data.output == "data/processed/processed.gdb/output_data"


def test_load_config_invalid_env_raises_value_error():
    """load_config with an unknown env name raises ValueError."""
    from arcgis_cloning.config import load_config
    with pytest.raises(ValueError, match="Invalid environment"):
        load_config("nonexistent_portal")


# ---------------------------------------------------------------------------
# Tests: get_available_environments
# ---------------------------------------------------------------------------

def test_get_available_environments_excludes_default():
    """get_available_environments never returns 'default'."""
    from arcgis_cloning.config import get_available_environments
    envs = get_available_environments()
    assert "default" not in envs


def test_get_available_environments_contains_source_and_destination():
    """get_available_environments returns source and destination."""
    from arcgis_cloning.config import get_available_environments
    envs = get_available_environments()
    assert "source" in envs
    assert "destination" in envs


def test_get_available_environments_is_sorted():
    """get_available_environments returns a sorted list."""
    from arcgis_cloning.config import get_available_environments
    envs = get_available_environments()
    assert envs == sorted(envs)


# ---------------------------------------------------------------------------
# Tests: ENVIRONMENT default and module-level singleton
# ---------------------------------------------------------------------------

def test_environment_default_is_source(monkeypatch):
    """When PROJECT_ENV is unset, ENVIRONMENT defaults to 'source'."""
    monkeypatch.delenv("PROJECT_ENV", raising=False)
    import importlib
    import arcgis_cloning.config as cfg_module
    importlib.reload(cfg_module)
    assert cfg_module.ENVIRONMENT == "source"


def test_import_without_project_env_raises_no_error(monkeypatch):
    """Importing config without PROJECT_ENV set does not raise ValueError."""
    monkeypatch.delenv("PROJECT_ENV", raising=False)
    import importlib
    import arcgis_cloning.config as cfg_module
    importlib.reload(cfg_module)
    # If this line runs, no ValueError was raised during module init
    assert cfg_module.config.logging.level is not None


def test_project_env_destination_sets_environment(monkeypatch):
    """PROJECT_ENV=destination is respected by the ENVIRONMENT constant."""
    monkeypatch.setenv("PROJECT_ENV", "destination")
    import importlib
    import arcgis_cloning.config as cfg_module
    importlib.reload(cfg_module)
    assert cfg_module.ENVIRONMENT == "destination"
```

### Notes on test design

- `monkeypatch` + `importlib.reload` is used for ENVIRONMENT tests to avoid relying
  on import order or cached module state.
- No `arcpy` or network calls; all tests run in a plain Python environment.
- Tests assert against values in the actual `config/config.yml`, so if defaults are
  changed in the YAML the tests serve as a regression signal.

---

## 6. Design Decisions

| Decision | Rationale |
|---|---|
| Keep `load_secrets` signature unchanged | Spec assumption is explicit: "No new parameter is added to `load_secrets`". Portal secrets are accessed via `secrets.source.url` pattern instead. |
| No new Python classes | The `ConfigNode` + `_deep_merge` pattern already handles arbitrary portal names; introducing a `PortalConfig` or `PortalSecrets` wrapper would be over-engineering. |
| `secrets_template.yml` uses zero-indent root keys | Standard YAML convention; reduces confusion for new contributors. Normalise `secrets.yml` to match. |
| `config.yml` structural change is zero | `source:` and `destination:` blocks already exist and are correctly empty — they inherit all defaults. Only comments need updating. |
| Tests use `importlib.reload` | Avoids test-order coupling; each ENVIRONMENT test starts from a clean module state regardless of prior imports. |
| No `staging` environment added | Spec scope is `source` + `destination` only; `staging` is called out as a forward-compatible example, not a deliverable. |
