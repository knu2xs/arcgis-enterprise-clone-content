# Tasks: Documentation and README

**Feature**: `004-docs-and-readme`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Exact file paths are included in every task description

---

## Phase 1: Setup

- [X] T001 Verify `mkdocs build` baseline passes before any changes by running
  `mkdocs build --strict` from `docsrc/` (establishes a clean baseline; confirms
  no pre-existing warnings that would contaminate later verification)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update `docsrc/mkdocs.yml` navigation first — adding `quickstart.md`
and `usage.md` to the nav before those files exist will cause `mkdocs build` to
fail, so the nav must be updated in sync with (or after) file creation. The nav
update is a shared prerequisite for US2 and US3 acceptance.

- [X] T002 Update the `nav:` section in `docsrc/mkdocs.yml` to:
  ```yaml
  nav:
    - Home: index.md
    - Quickstart: quickstart.md
    - Usage: usage.md
    - Configuration: configuration.md
    - API: api.md
    - Cookiecutter Reference: cookiecutter_reference.md
  ```
  Leave all other keys (`site_name`, `theme`, `markdown_extensions`, plugins) unchanged

!!! warning
    Do NOT run `mkdocs build` after completing T002 until T004 and T005 are also complete.
    The nav references `quickstart.md` and `usage.md` which won't exist yet, causing the
    build to fail. Run `mkdocs build` only after Phases 4 and 5 are done (T008 gate).

**Checkpoint**: `docsrc/mkdocs.yml` nav block matches the target exactly (FR-009).

---

## Phase 3: User Story 1 — Accurate README for New Visitors (Priority: P1) MVP

**Goal**: Replace the generic cookiecutter boilerplate inside `<!--start-->`/`<!--end-->`
with an accurate description of the ArcGIS portal migration tool, prerequisites, and
a concise 5-step quick-start covering both the CLI and Python API.

**Independent Test**: Read `README.md` cold. Within 60 seconds answer: (1) what does
this do? (2) what do I need? (3) how do I run it? — all three answers must be present.

### Implementation for User Story 1

- [X] T003 [US1] Rewrite the content inside the `<!--start-->` / `<!--end-->` markers
  in `README.md`:
  - Replace the generic opening sentence with a `## What it does` section (one paragraph
    covering ArcGIS portal content migration, fresh-run, resume mode, folder mirroring,
    and timestamped log output)
  - Add a `## Prerequisites` section as a bullet list: ArcGIS Pro (or ArcGIS API for
    Python), conda environment setup via `make env`, and `config/secrets.yml` credentials
  - Add a `## Quick Start` section with 5 numbered steps, each with exactly one code
    block:
    1. `make env` (environment setup)
    2. `cp config/secrets_template.yml config/secrets.yml` (credentials)
    3. Edit `config/config.yml` migration keys (optional, with YAML snippet)
    4. `python scripts/make_data.py` (CLI run)
    5. Python API call (`from arcgis_cloning import migrate_content; migrate_content()`)
  - Do NOT modify anything outside the `<!--start-->` / `<!--end-->` markers
  - Do NOT modify `docsrc/mkdocs/index.md` (it auto-includes README)

**Checkpoint**: Open `README.md` — zero generic placeholder sentences remain; 3 sections
present (`What it does`, `Prerequisites`, `Quick Start`); all code blocks are syntactically
valid (FR-001, FR-002, FR-003).

---

## Phase 4: User Story 2 — Quickstart Guide in MkDocs (Priority: P2)

**Goal**: Create `docsrc/mkdocs/quickstart.md` — an expanded step-by-step guide with
admonitions, expected CLI output, and a Python API alternative. Nav entry confirmed
working in `mkdocs build`.

**Independent Test**: Follow the quickstart page verbatim (with mocked or real portals);
the page renders without MkDocs warnings and all steps are numbered and complete.

### Implementation for User Story 2

- [X] T004 [US2] Create `docsrc/mkdocs/quickstart.md` using the draft at
  `specs/004-docs-and-readme/quickstart.md` as the authoritative source. The file MUST:
  - Begin with front matter `---\ntitle: Quickstart\n---`
  - Contain exactly 5 `##` sections in order: Step 1 (env setup), Step 2 (credentials),
    Step 3 (config, optional), Step 4 (CLI run), Step 5 (Python API)
  - Step 2 must include: a `bash` code block for the copy command, a `yaml` code block
    showing the full `source:` + `destination:` schema with `profile`, `url`, `username`,
    `password` fields, an `!!! warning` about not committing `secrets.yml`, and an
    `!!! tip` about profile taking precedence over URL credentials
  - Step 3 must include: a `yaml` code block showing the `migration:` block in
    `config.yml`, and an `!!! note` explaining the defaults
  - Step 4 must include: a `bash` code block (`python scripts/make_data.py`), expected
    console output snippet, the log file path pattern
    (`data/logs/clone_content_YYMMDDHHMM.log`), an `!!! tip` explaining
    `migrated`/`skipped`/`failed`, and a `!!! danger` admonition: "If `secrets.yml` is
    missing or incomplete, the migration exits with code 1 and logs a `KeyError`. Copy
    `config/secrets_template.yml` to `config/secrets.yml` and fill in your credentials."
  - Step 5 must include: a `python` code block for the basic API call, a second block
    for resume mode (`migrate_content(resume=True)`), and a link to the Usage Reference
    page (`usage.md`)
  - All code blocks use fenced syntax with language identifiers (`bash`, `yaml`, `python`)

**Checkpoint**: `docsrc/mkdocs/quickstart.md` exists; `mkdocs build` from `docsrc/`
completes without warnings (FR-004, FR-005).

---

## Phase 5: User Story 3 — Detailed Usage Reference in MkDocs (Priority: P3)

**Goal**: Create `docsrc/mkdocs/usage.md` covering all 7 `migrate_content()` parameters,
`MigrationResult` fields, failure inspection, log file format, resume mode, and item
filtering — so no reader needs to open source code for parameter lookups.

**Independent Test**: A reader with no source code access can, after reading `usage.md`,
correctly write a resume-mode call with a custom query and interpret all fields of the
returned `MigrationResult`.

### Implementation for User Story 3

- [X] T005 [US3] Create `docsrc/mkdocs/usage.md` with front matter
  `---\ntitle: Usage Reference\n---` and the following sections:

  **`## migrate_content()`** — one-sentence description + a pipe-delimited Markdown
  table with all 7 parameters (columns: Parameter, Type, Default, Description):
  `source_gis` (`GIS | None`, `None`), `destination_gis` (`GIS | None`, `None`),
  `source_env` (`str`, `"source"`), `destination_env` (`str`, `"destination"`),
  `resume` (`bool`, `False`), `query` (`str | None`, `None`),
  `max_items` (`int | None`, `None`)

  **`## MigrationResult`** — pipe-delimited table with 4 fields: `migrated` (int),
  `skipped` (int), `failed` (int), `failures` (list[dict])

  **`## Inspecting failures`** — a `python` code block iterating `result.failures`;
  a table of the 4 dict keys each record contains: `item_id`, `title`, `type`, `error`

  **`## Log file`** — log file location (`data/logs/`), filename pattern
  (`clone_content_YYMMDDHHMM.log`), explanation of 2-digit year (`%y`), what is
  written at DEBUG vs. INFO level

  **`## Resume mode`** — when to use; how items are matched (title + type); comparison
  with fresh-run (default); `python` code example

  **`## Filtering items`** — `query` parameter examples (by type, by owner, by tag);
  `max_items` use case (safety testing); `python` code examples

**Checkpoint**: `docsrc/mkdocs/usage.md` exists with all 6 sections; all 7 parameters
appear in the table; `mkdocs build` from `docsrc/` completes without warnings (FR-006,
SC-004).

---

## Phase 6: User Story 4 — Configuration Page Updated for Portal Environments (Priority: P2)

**Goal**: Update `docsrc/mkdocs/configuration.md` to replace all `dev`/`test`/`prod`
placeholder examples with `source`/`destination` and add the `migration` key and
full `secrets.yml` schema.

**Independent Test**: Open `configuration.md` — zero occurrences of `dev`, `test`,
or `prod` as environment names; both `source` and `destination` environment blocks
are shown; `migration:` key is present; `secrets.yml` example has `source:` and
`destination:` blocks with all four credential fields.

### Implementation for User Story 4

- [X] T006 [US4] In `docsrc/mkdocs/configuration.md`, replace the `config.yml`
  example YAML block (the one currently showing `dev:`, `test:`, `prod:` environments)
  with a block showing:
  - `environments.default` containing `logging.level: DEBUG`, `data.input`,
    `data.output`, and a `migration:` sub-key with `source_env: "source"` and
    `destination_env: "destination"`
  - An `environments.source:` block (minimal, can be empty or have a `logging.level`
    override)
  - An `environments.destination:` block (minimal)
  - Update the surrounding prose and the `!!! tip "Custom environments"` admonition
    to reference ArcGIS portal naming rather than `staging`

- [X] T007 [US4] In `docsrc/mkdocs/configuration.md`, replace the `secrets.yml`
  example block with the full two-portal schema (matching `config/secrets_template.yml`):
  - A `source:` block with `profile:`, `url:`, `username:`, `password:` fields
    (with inline comments explaining profile precedence)
  - A `destination:` block with the same four fields
  - Add an `!!! tip` admonition (immediately after the YAML block) explaining:
    "If `profile` is set to a non-empty string, `url`, `username`, and `password`
    are ignored."

**Checkpoint**: `configuration.md` contains no occurrences of `dev`, `test`, or `prod`
as environment names; both portal blocks present in secrets example; `!!! tip` about
profile precedence present (FR-007, FR-008).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T008 [P] Run `mkdocs build --strict` from `docsrc/` and confirm zero errors
  and zero warnings across all pages (SC-003); fix any broken links or missing anchors
  before marking this task done
- [X] T009 [P] Grep `README.md` and all updated/created MkDocs pages for any
  remaining generic placeholder strings (`dev`, `test`, `prod` as env names,
  "Useful tooling", "Start Building", "your description here", `$ARGUMENTS`) and
  confirm none are present (SC-002)

---

## Dependencies & Execution Order

```
Phase 1 (Setup: T001)  ← baseline mkdocs build check
  └─► Phase 2 (Foundational: T002)  ← nav update; must precede mkdocs build
        ├─► Phase 3 (US1: T003)     ← README rewrite; independent of US2/US3/US4
        ├─► Phase 4 (US2: T004)     ← create quickstart.md; depends on T002 (nav)
        ├─► Phase 5 (US3: T005)     ← create usage.md; depends on T002 (nav)
        └─► Phase 6 (US4: T006, T007)  ← update configuration.md; independent of US1/US2/US3
              └─► Phase 7 (Polish: T008, T009 [P])
```

### Parallel execution within phases

- **Phase 2**: T002 is a single task; no parallelism
- **Phase 3**: T003 is a single task; no parallelism
- **Phases 4, 5, 6**: T004, T005, T006/T007 operate on different files and can
  run in parallel once T002 is complete
- **Phase 7**: T008 and T009 are fully independent and can run simultaneously

### Implementation strategy (MVP first)

**MVP = Phases 1–3 (T001–T003)**: Delivers US1 — accurate README. The project's most
visible artifact is fixed independently of any MkDocs site changes. Independently
demonstrable on GitHub.

**Increment 2 = Phases 4 + 6 (T002, T004, T006, T007)**: Adds Quickstart page and
fixes the Configuration page — the two pages users reach next after the README.
Demonstrated by serving `mkdocs serve` and navigating to both pages.

**Increment 3 = Phase 5 (T005)**: Adds the Usage Reference — the deeper reference
material for experienced users.

**Final = Phase 7 (T008, T009)**: Build verification and placeholder sweep.
