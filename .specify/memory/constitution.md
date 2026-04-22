<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0
Initial ratification — all content is new.

Added sections:
  - Core Principles (I–V)
  - Spatial & ArcGIS Constraints
  - Development Workflow
  - Governance

Modified principles: N/A (first version)
Removed sections: N/A

Templates reviewed:
  ✅ .specify/templates/plan-template.md  — Constitution Check section present; no updates required
  ✅ .specify/templates/spec-template.md  — no principle-specific references; no updates required
  ✅ .specify/templates/tasks-template.md — no principle-specific references; no updates required

Deferred TODOs: none
-->

# ArcGIS Enterprise Clone Content Constitution

## Core Principles

### I. Source-First Architecture (NON-NEGOTIABLE)

All business logic, domain rules, data transformation, spatial analysis, and processing
algorithms MUST live exclusively in `src/arcgis_cloning/` as importable, testable Python
functions and classes.

Scripts in `scripts/` MUST be thin entry points only. A script is permitted to:
- Bootstrap logging (call `get_logger`) and derive a log-file path
- Read runtime parameters from `config` / `secrets` or command-line arguments
- Call one or more functions imported from `src/arcgis_cloning/`
- Write final outputs or report results

A script MUST NOT contain conditional branching, data transformations, spatial operations,
or any logic that belongs in a testable unit. If logic needs to move from a script into
`src/`, that move is always correct and never requires justification.

**Rationale**: Logic confined to `src/` is independently importable, unit-testable, and
reusable by toolboxes (`arcgis/*.pyt`), notebooks, and future callers. Scripts that grow
their own logic become untestable monoliths and violate the reuse model this project depends
on.

### II. Configuration-Driven Behavior

All tuneable values — paths, log levels, environment flags, API endpoints — MUST be read
from `config/config.yml` via the `config` singleton exposed by `arcgis_cloning.config`.
Credentials and secrets MUST be read from `config/secrets.yml` via the `secrets` singleton.

- Hardcoding paths, URLs, or environment-specific strings in source code is PROHIBITED.
- Use `pathlib.Path` for all file-system paths; string concatenation for paths is PROHIBITED.
- The active environment is selected via the `PROJECT_ENV` environment variable (default:
  `"dev"`). Switch environments at the shell; do not modify `config.py` for local overrides.
- Never commit `config/secrets.yml` to version control. Add new secrets to
  `config/secrets_template.yml` with placeholder values alongside the real entry.

**Rationale**: Externalising configuration enables environment parity, safe secret
management, and zero-code environment switching.

### III. Structured Observability

Every module in `src/arcgis_cloning/` MUST configure a module-level logger at file scope
using `get_logger(__name__, level="DEBUG", add_stream_handler=False)`. Scripts MUST
configure the root logger once at their entry point with an appropriate level and optional
logfile path. `print()` MUST NOT be used in production code paths; use `logger.*` instead.

Exception handling MUST follow the build-message → log → raise pattern:
1. Build the error string into a named variable.
2. Log it at the correct level (`logger.error`, `logger.warning`, etc.).
3. Raise the exception with that message so callers see the same text.

**Rationale**: Consistent structured logging allows failures to be diagnosed from log files
alone without interactive reproduction — critical for ArcGIS Pro geoprocessing workflows
where interactive debugging is cumbersome.

### IV. Testing Discipline

All new functionality added to `src/arcgis_cloning/` MUST have corresponding tests in
`testing/` following the naming convention `test_<module_name>.py`. Tests MUST:

- Be independent and isolated — no reliance on test execution order or shared mutable state.
- Use plain `assert` statements (PyTest rewrites them for rich output).
- Use the pre-defined fixtures from `testing/conftest.py` (`temp_dir`, `temp_gdb`,
  `setup_environment`) rather than reimplementing equivalent setup.
- Mock external calls (`arcpy`, GIS connections, file I/O) using `unittest.mock` or
  `pytest-mock` to keep unit tests fast and environment-independent.
- Never test third-party library internals — only test project code.

Run the full suite with `make test`. A new feature is NOT complete until its tests pass.

**Rationale**: Tests in `testing/` exercising only `src/` code give confident, fast feedback
and are unaffected by ArcGIS Pro installation state when mocked appropriately.

### V. Coding Standards

All Python code in `src/arcgis_cloning/` and `scripts/` MUST comply with:

- **PEP 8** style (line length ≤ 100 chars preferred; 120 absolute maximum).
- **Type hints** on all function and method signatures — arguments and return values.
- **Google-style docstrings** on every public function and class, including `Args:`,
  `Returns:`, and `Raises:` sections where applicable. Use MkDocs admonition syntax
  (`!!! note`, `!!! warning`, `!!! tip`, `!!! danger`) for callout blocks inside
  docstrings.
- **`pathlib.Path`** for all filesystem operations; `os.path` is PROHIBITED in new code.
- **Vectorised operations** in pandas/NumPy over row-wise iteration (`iterrows`, `apply`
  with Python lambdas) wherever feasible.
- **Conservative change scope** — do not refactor, rename public symbols, or add features
  beyond what is directly requested. Dead code gets a `# TODO` comment, not deletion,
  unless explicitly instructed.

## Spatial & ArcGIS Constraints

These constraints apply to all code that touches ArcPy or the ArcGIS API for Python.

- **ArcPy is implicit**: Do not add `arcpy` to `pyproject.toml` or `environment.yml`; it
  is provided by the ArcGIS Pro conda environment.
- **Intermediate data management**:
  - Small datasets (< tens of thousands of features): use the `memory/` workspace.
  - Large datasets: use the `@with_temp_fgdb` decorator from `arcgis_cloning.utils` which
    provides a scoped temporary file geodatabase and cleans up on exit.
- **Cursor style**: Use `arcpy.da.*Cursor` classes with `with` statements; legacy cursor
  classes are PROHIBITED in new code.
- **Tool calls**: Use `arcpy.<toolbox>.<ToolName>(param=value)` named-parameter form.
  Do not use `arcpy.ToolName_toolbox` aliases or rely on positional argument order.
- **Spatial references**: Never hardcode WKID integers in business logic; read from
  `config` or accept as parameters.
- **Toolboxes** (`arcgis/*.pyt`): Call functions from `src/arcgis_cloning/`; do not
  duplicate logic. Pass `add_arcpy_handler=True` to `get_logger` so messages appear in
  the ArcGIS Pro geoprocessing pane.
- **GIS connections**: Obtain credentials exclusively from `secrets.esri.*`; never
  hardcode URLs or profile names.
- **Source data safety**: Never call arcpy functions that modify a source geodatabase
  without confirming the target is a copy or a test fixture.

## Development Workflow

### Environment & Dependencies

| Scenario | Add to |
|---|---|
| `import foo` inside `src/arcgis_cloning/` | `pyproject.toml` `[project] dependencies` |
| MkDocs plugin, JupyterLab extension, dev/test tool | `environment.yml` |
| ArcPy or any `arcpy.*` import | Neither — provided by ArcGIS Pro |

Never upgrade pinned dependency versions as a side effect of unrelated changes. Flag new
dependencies explicitly when proposing changes; additions require review.

### Common Commands

| Command | Purpose |
|---|---|
| `make env` | Create/update conda environment |
| `make test` | Run full PyTest suite |
| `make docserve` | Serve live MkDocs docs at http://localhost:8000 |
| `make docs` | Build static documentation |
| `make data` | Run `scripts/make_data.py` data pipeline |
| `make pytzip` | Package the ArcGIS Pro toolbox for distribution |

### Data Safety

- Files under `data/raw/` are **read-only**. Never overwrite or delete raw data.
- Processed outputs go to `data/interim/` or `data/processed/` — never back to `data/raw/`.
- Derive all output paths from `config` values; do not hardcode them.

## Governance

This constitution supersedes all other practices and informal conventions for this project.
The authoritative runtime coding guidance is `.github/copilot-instructions.md` (AGENTS.md);
when a detail is not covered here, fall back to that document.

**Amendment procedure**:
1. Propose the change with a rationale and impact assessment.
2. Update this file and increment the version following semantic versioning:
   - **MAJOR**: backward-incompatible principle removal or redefinition.
   - **MINOR**: new principle or section added / materially expanded guidance.
   - **PATCH**: clarifications, wording fixes, non-semantic refinements.
3. Update `LAST_AMENDED_DATE` to the date of the change.
4. Propagate changes to any affected templates under `.specify/templates/`.

All pull requests and code reviews MUST verify compliance with the Source-First Architecture
principle (I) and the Coding Standards principle (V) at minimum. Violations require explicit
justification documented in a `## Complexity Tracking` section of the relevant plan.

**Version**: 1.0.0 | **Ratified**: 2026-04-21 | **Last Amended**: 2026-04-21
