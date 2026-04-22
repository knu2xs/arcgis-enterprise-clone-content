# Research: Documentation and README

## D1 — README include markers strategy

**Decision**: Keep the existing `<!--start-->` / `<!--end-->` comment markers in `README.md`.

**Rationale**: `docsrc/mkdocs/index.md` uses the `mkdocs-include-markdown-plugin`
`{% include %}` directive which respects these markers. Content inside the markers
renders on both GitHub and the MkDocs site; content outside (e.g., the `<small>` template
credit footer) is suppressed on the docs site. This is the intended pattern for this
project template.

**Alternatives considered**:
- Remove the markers and use the full README — rejected because the template credit
  `<small>` block would appear on the docs home page.
- Separate README entirely from the docs index — rejected because it creates a
  maintenance burden (two sources of truth).

---

## D2 — README quick-start depth vs. quickstart.md page

**Decision**: README contains a concise quick-start (5 numbered steps, one code block
each). `docsrc/mkdocs/quickstart.md` expands each step with admonitions, expected output,
and error troubleshooting notes.

**Rationale**: GitHub visitors need a fast answer; MkDocs readers have more patience
and benefit from the extra detail. The same five steps appear in both places so they
stay consistent, but the docs page is the authoritative deep-dive.

**Alternatives considered**:
- README only (no quickstart.md) — rejected because FR-004 explicitly requires the
  MkDocs page and SC-001 requires a 10-minute onboarding path.
- All content in quickstart.md, README just links — rejected because GitHub visitors
  cannot follow the link without leaving the repository page.

---

## D3 — Parameter documentation strategy for usage.md

**Decision**: `usage.md` uses a Markdown table for all 7 `migrate_content()` parameters
plus a second table for `MigrationResult` fields, supplemented by code examples for
each non-trivial combination.

**Rationale**: The auto-generated `api.md` (mkdocstrings) renders the full docstring,
but presents it as prose inside a collapsible block. A dedicated reference table is
easier to scan for "what does `resume` do?" queries. `usage.md` does NOT duplicate
the full docstring — it distils it into scannable tables plus runnable examples.

**Alternatives considered**:
- Expand the docstring further and rely on `api.md` only — rejected because the
  existing docstring is already complete; a table format adds navigability, not
  redundancy.

---

## D4 — configuration.md example environments

**Decision**: Replace all `dev`/`test`/`prod` example blocks in `configuration.md`
with `source` and `destination`, matching the actual `config.yml` and
`secrets_template.yml` in this repository.

**Rationale**: The existing page was generated from the cookiecutter template and does
not match the project. Any reader who copies the example will create wrong environment
names and get a `ValueError: Invalid environment` error. The fix is low-effort and
eliminates the mismatch entirely.

**Alternatives considered**:
- Add `source`/`destination` as additional examples alongside `dev`/`test`/`prod` —
  rejected because it creates confusion about which examples to follow.

---

## D5 — mkdocs.yml navigation order

**Decision**: `Home → Quickstart → Usage → Configuration → API → Cookiecutter Reference`

**Rationale**: Matches the new-user reading journey: understand the project (Home) →
run it for the first time (Quickstart) → understand all options (Usage) → understand
the config files (Configuration) → look up the Python API (API). The Cookiecutter
Reference is legacy template content and goes last.

**Alternatives considered**:
- Keep current order and append new pages — rejected because inserting Quickstart and
  Usage after Configuration would break the logical reading flow.

---

## D6 — Authentication path coverage

**Decision**: Both authentication paths are documented everywhere credentials are
shown: (a) ArcGIS named profile (`profile: "my_profile"`), (b) explicit URL + username
+ password. Profile takes precedence when set; the other fields are ignored.

**Rationale**: `_connect_gis()` in `src/arcgis_cloning/_main.py` implements exactly
this precedence logic. Documenting both paths prevents support questions from users
who use enterprise SSO profiles instead of username/password.

**Alternatives considered**:
- Document profile-only — rejected because many users authenticate with URL + credentials.
- Document URL+username+password only — rejected because ArcGIS Pro users commonly
  prefer named profiles for security (password not stored in YAML).

---

## D7 — MkDocs plugin requirements

**Decision**: No new plugins needed. All required plugins are already in
`docsrc/requirements.txt`:
- `mkdocs-include-markdown-plugin` — used by `index.md` to include `README.md`
- `mkdocstrings[python]` — used by `api.md`
- `mkdocs-material` — theme with admonition and code-copy support

**Rationale**: Avoiding new plugin dependencies keeps the environment stable and does
not require `environment.yml` or `docsrc/requirements.txt` changes, which are out of
scope for this feature.

---

## Summary table

| ID | Decision | Impact |
|----|----------|--------|
| D1 | Preserve `<!--start-->`/`<!--end-->` markers in README | README + index.md stay in sync |
| D2 | README: concise 5-step; quickstart.md: detailed | Both audiences served without duplication |
| D3 | usage.md: parameter tables + code examples | Faster scan than reading full docstring |
| D4 | Replace dev/test/prod with source/destination | Eliminates template placeholder confusion |
| D5 | Nav order: Home → Quickstart → Usage → Config → API | Follows new-user reading journey |
| D6 | Show both profile and URL+credentials auth paths | Covers all real-world auth scenarios |
| D7 | No new MkDocs plugins required | No dependency changes needed |
