# Feature Specification: Documentation and README

**Feature Branch**: `004-docs-and-readme`
**Created**: 2026-04-21
**Status**: Draft
**Input**: User description: "Build documentation on how to use this package in
docsrc/mkdocs, and also ensure the readme correctly reflects the purpose and use for
the project."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate README for New Visitors (Priority: P1)

A developer discovers this project on GitHub and reads the README to understand
what the tool does, what the prerequisites are, and how to get started. The current
README contains only generic cookiecutter boilerplate with no mention of ArcGIS
portal migration.

**Why this priority**: The README is the first (and often only) thing a visitor reads.
It must accurately reflect the project's actual purpose and workflow before any other
documentation is useful.

**Independent Test**: Open `README.md` cold, without any other context. Within 60 seconds
a reader should be able to answer: (1) What problem does this solve? (2) What do I need
to install/configure? (3) How do I run a migration?

**Acceptance Scenarios**:

1. **Given** a developer visits the GitHub repository, **When** they read `README.md`,
   **Then** they see a clear description of the ArcGIS portal content migration purpose,
   key prerequisites (ArcGIS Pro conda environment, portal credentials), and a minimal
   quick-start showing the CLI command and Python API call.
2. **Given** the README is updated, **When** the MkDocs home page (`docsrc/mkdocs/index.md`)
   is built, **Then** it automatically reflects the same content because it uses
   `{% include "../../README.md" %}`.
3. **Given** the project has a `secrets_template.yml`, **When** a reader follows the
   README setup steps, **Then** they know to copy the template to `secrets.yml` and
   fill in their portal credentials.

---

### User Story 2 - Quickstart Guide in MkDocs (Priority: P2)

A developer who has installed the package wants a single page that walks them through
configuring credentials, setting environment names, and running their first migration
end-to-end — both via the CLI script and via the Python API.

**Why this priority**: Configuration (two YAML files, portal credentials, environment
naming) is the main setup friction. A focused quickstart page removes that friction
and is the natural next step after reading the README.

**Independent Test**: Follow the quickstart page verbatim with a real (or mock) ArcGIS
environment. The migration should complete with a log file written to `data/logs/`.

**Acceptance Scenarios**:

1. **Given** a developer has installed the package, **When** they open
   `docsrc/mkdocs/quickstart.md`, **Then** they find numbered steps covering:
   set up `secrets.yml`, set portal env names in `config.yml`, run via CLI
   (`python scripts/make_data.py`), and interpret the summary log line.
2. **Given** the quickstart page exists, **When** `mkdocs.yml` is built,
   **Then** the page appears in the site navigation under "Quickstart".
3. **Given** a reader prefers Python over the CLI, **When** they read the quickstart,
   **Then** they also see a Python API example using `migrate_content()` directly.

---

### User Story 3 - Detailed Usage Reference in MkDocs (Priority: P3)

An experienced user wants a reference page covering `migrate_content()` parameters
(`resume`, `max_items`, `query`), the `MigrationResult` fields, failure handling,
and the log file format — without needing to read the source code.

**Why this priority**: The API reference page (`api.md`) auto-generates docstring
content but does not explain *when* to use optional parameters or how to interpret
results. A usage reference page fills that gap.

**Independent Test**: A developer who has never seen the source code reads the usage
page and correctly configures a resume-mode run with a custom item query.

**Acceptance Scenarios**:

1. **Given** a developer reads `docsrc/mkdocs/usage.md`, **When** they want to run
   a resume migration (skip already-cloned items), **Then** they find a clear example
   of `migrate_content(resume=True)`.
2. **Given** a developer reads the usage page, **When** they want to understand the
   summary output, **Then** they find a table explaining `migrated`, `skipped`,
   `failed`, and how to inspect per-item `failures`.
3. **Given** the usage page exists, **When** `mkdocs.yml` is built,
   **Then** the page appears in the site navigation under "Usage".

---

### User Story 4 - Configuration Page Updated for Portal Environments (Priority: P2)

A developer reading `docsrc/mkdocs/configuration.md` should see examples specific to
this project (source/destination portal environments and the `migration` key) rather
than the generic `dev`/`test`/`prod` placeholders left by the project template.

**Why this priority**: The configuration page is already linked in the nav and is
where users naturally look after the README. Placeholder examples create confusion
about how environments are actually used in this project.

**Independent Test**: Open `configuration.md` and replace every generic example
(`dev`, `test`, `prod`) with project-specific ones (`source`, `destination`) and the
`migration` section. The page should need no additional files to understand real usage.

**Acceptance Scenarios**:

1. **Given** a developer reads the configuration page, **When** they see the
   `config.yml` example, **Then** it shows `source` and `destination` environments
   with a `migration.source_env` / `migration.destination_env` block.
2. **Given** a developer reads the configuration page, **When** they see the
   `secrets.yml` example, **Then** it shows both a `source` and a `destination`
   block with `url`, `username`, `password`, and `profile` fields.
3. **Given** the configuration page references `config/secrets_template.yml`,
   **When** a developer follows the instructions, **Then** they can copy the
   template and fill in values without consulting any other file.

---

### Edge Cases

- What if `secrets.yml` is missing entirely — the docs should explain the error
  and remediation step (copy from `secrets_template.yml`).
- Portal profile authentication (ArcGIS named credential store) vs. explicit
  URL + username + password — both authentication paths must be shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `README.md` MUST describe the project as an ArcGIS portal content
  migration tool, replacing the generic cookiecutter boilerplate.
- **FR-002**: `README.md` MUST include a prerequisites section listing ArcGIS Pro
  (or ArcGIS API for Python), a conda environment setup step, and valid portal
  credentials in `secrets.yml`.
- **FR-003**: `README.md` MUST include a minimal quick-start showing both the CLI
  invocation (`python scripts/make_data.py`) and the Python API call
  (`from arcgis_cloning import migrate_content; migrate_content()`).
- **FR-004**: A new `docsrc/mkdocs/quickstart.md` page MUST be created with
  step-by-step instructions: copy `secrets_template.yml` → `secrets.yml`, fill in
  credentials, confirm environment names in `config.yml`, run via CLI, read the
  summary log line.
- **FR-005**: `docsrc/mkdocs/quickstart.md` MUST include a Python API example using
  `migrate_content()` with and without the `resume` parameter.
- **FR-006**: A new `docsrc/mkdocs/usage.md` page MUST document all
  `migrate_content()` parameters (`source_env`, `destination_env`, `resume`,
  `max_items`, `query`, `source_gis`, `destination_gis`), the `MigrationResult`
  fields, and the log file naming convention (`clone_content_YYMMDDHHMM.log`).
- **FR-007**: `docsrc/mkdocs/configuration.md` MUST be updated to replace generic
  placeholder environments (`dev`/`test`/`prod`) with `source`/`destination`
  examples and add the `migration` key documentation.
- **FR-008**: `docsrc/mkdocs/configuration.md` MUST show the `secrets.yml` schema
  for both a `source` and a `destination` portal entry, including the `profile`
  field alongside `url`, `username`, and `password`.
- **FR-009**: `docsrc/mkdocs.yml` nav MUST be updated to include `Quickstart` and
  `Usage` pages in the correct reading order.

### Key Entities

- **README.md**: Project root overview; source of truth for the MkDocs home page
  via `{% include %}`.
- **quickstart.md**: New MkDocs page — end-to-end setup and first-run guide.
- **usage.md**: New MkDocs page — comprehensive parameter and result reference.
- **configuration.md**: Existing MkDocs page — updated with project-specific examples.
- **mkdocs.yml**: Site configuration — nav updated to include new pages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new contributor can complete a first successful migration within
  10 minutes of reading the README + quickstart, without consulting source code.
- **SC-002**: Every generic placeholder (`dev`, `test`, `prod`, "your description
  here", "$ARGUMENTS") is eliminated from `README.md` and all updated MkDocs pages.
- **SC-003**: `mkdocs build` completes without errors or broken-link warnings on any
  of the new or updated pages.
- **SC-004**: The full `migrate_content()` public API (all 7 parameters) is
  documented in `usage.md` so that no parameter lookup requires reading source code.

## Assumptions

- ArcGIS Pro (which provides `arcpy` and `arcgis`) is already installed; the docs do
  not need to cover ArcGIS Pro installation itself.
- The `environment.yml` / `make env` conda setup workflow is assumed working; the
  docs reference it but do not need to reproduce it in detail.
- The `cookiecutter_reference.md` page is template boilerplate and is out of scope
  for this feature — it should not be modified.
- The existing `api.md` auto-generation via mkdocstrings is sufficient for the raw
  API reference; `usage.md` supplements it with conceptual guidance.
- The MkDocs Material theme and all required plugins are already installed in the
  conda environment via `docsrc/requirements.txt`.
