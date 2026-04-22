# Tasks: Environment as Portal Configuration

**Feature**: `001-environment-as-portal-config`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Exact file paths are included in every task description

---

## Phase 1: Setup

No new project structure required — this feature is a pure Python/YAML refactoring of
an existing module. Proceed directly to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Normalize the YAML configuration files to the portal-based model so that all
downstream tests and the `ENVIRONMENT` default change have a consistent foundation.

**⚠️ CRITICAL**: US1 and US3 tests assert against live `config.yml` values; US2 tests
reload `arcgis_cloning.config` — both require the YAML files to be in their final state
before execution. No user story work can begin until this phase is complete.

- [X] T001 Fix `config/secrets.yml` root indentation: remove the leading 2-space indent from the `source:` block and the `destination:` block so both root keys sit at column 0
- [X] T002 [P] Create `config/secrets_template.yml` with a `source` block (`url`, `username`, `password` placeholders) and a `destination` block (`url`, `username`, `password` placeholders); include the standard header comment warning against committing `secrets.yml`
- [X] T003 [P] Update `config/config.yml` header comment (line ~10): replace `"switch between dev / test / prod"` with `"switch between source / destination"`; update the environments section comment (line ~21): replace `"named environment (dev / test / prod)"` with `"named portal environment (source / destination)"`

**Checkpoint**: YAML files normalized; `config.yml` comment describes the portal model;
`config/secrets_template.yml` exists for onboarding; downstream phases may now proceed

---

## Phase 3: User Story 1 — Load Portal Config by Name (Priority: P1) 🎯 MVP

**Goal**: Verify that `load_config("source")` and `load_config("destination")` each return
a correctly merged `ConfigNode` inheriting shared defaults, and that an unknown environment
name raises `ValueError`.

**Independent Test**: Call `load_config("source")` after Phase 2 completes; assert
`cfg.logging.level == "DEBUG"` and `cfg.data.input == "data/raw/input_data.csv"` — these
values come from `environments.default` in `config.yml`.

> **Note**: No implementation code changes are required for US1. `load_config` already
> supports arbitrary named environments via the existing `_deep_merge` logic. The tasks
> below add verification tests only.

### Tests for User Story 1

- [X] T004 [US1] Add `test_load_config_source_returns_config_node` to `testing/test_arcgis_cloning.py`: call `load_config("source")` and assert `cfg.logging.level == "DEBUG"` and `cfg.data.input == "data/raw/input_data.csv"`
- [X] T005 [P] [US1] Add `test_load_config_destination_returns_config_node` to `testing/test_arcgis_cloning.py`: call `load_config("destination")` and assert `cfg.data.output == "data/processed/processed.gdb/output_data"`
- [X] T006 [P] [US1] Add `test_load_config_invalid_env_raises_value_error` to `testing/test_arcgis_cloning.py`: assert `load_config("nonexistent_portal")` raises `ValueError` with message matching `"Invalid environment"`

**Checkpoint**: `load_config` named-portal contract is verified; acceptance scenarios 1 and 3
from US1 are covered by automated tests

---

## Phase 4: User Story 2 — Default Environment Points to Source (Priority: P2)

**Goal**: Change the `ENVIRONMENT` constant default in `config.py` from `"dev"` to
`"source"` so the module-level `config` singleton works without setting `PROJECT_ENV`.
Update the module docstring to replace the deployment-stage framing with the
portal-environment model and the recommended per-call clone pattern.

**Independent Test**: Import `arcgis_cloning.config` without setting `PROJECT_ENV`; assert
`ENVIRONMENT == "source"` and `config.logging.level` is accessible without `ValueError`.

### Implementation for User Story 2

- [X] T007 [US2] Update `src/arcgis_cloning/config.py` line ~55: change `os.environ.get("PROJECT_ENV", "dev")` to `os.environ.get("PROJECT_ENV", "source")`
- [X] T008 [US2] Update the module-level docstring in `src/arcgis_cloning/config.py`: replace `secrets.esri.gis_url` example with `secrets.source.url`; replace deployment-stages framing with portal-environment framing; add per-call clone pattern (`load_config("source")` / `load_config("destination")` / `source_sec.source.url` / `dest_sec.destination.url`)

### Tests for User Story 2

- [X] T009 [US2] Add `test_environment_default_is_source` to `testing/test_arcgis_cloning.py`: use `monkeypatch.delenv("PROJECT_ENV", raising=False)` + `importlib.reload(arcgis_cloning.config)` and assert `cfg_module.ENVIRONMENT == "source"`
- [X] T010 [P] [US2] Add `test_import_without_project_env_raises_no_error` to `testing/test_arcgis_cloning.py`: reload module without `PROJECT_ENV` and assert `cfg_module.config.logging.level is not None`
- [X] T011 [P] [US2] Add `test_project_env_destination_sets_environment` to `testing/test_arcgis_cloning.py`: use `monkeypatch.setenv("PROJECT_ENV", "destination")` + `importlib.reload` and assert `cfg_module.ENVIRONMENT == "destination"`

**Checkpoint**: `arcgis_cloning.config` imports without errors when `PROJECT_ENV` is unset;
`ENVIRONMENT` defaults to `"source"`; US2 acceptance scenarios 1 and 2 are covered

---

## Phase 5: User Story 3 — Discover Available Portals (Priority: P3)

**Goal**: Verify that `get_available_environments()` returns a sorted list of all portal
names from `config.yml` excluding `"default"`, so toolbox tools can enumerate portals
dynamically without code changes when entries are added or removed.

**Independent Test**: Call `get_available_environments()` and assert the result is
`["destination", "source"]` (sorted alphabetically, `"default"` absent).

> **Note**: No implementation code changes are required for US3. `get_available_environments`
> already reads environment keys directly from the YAML and excludes `"default"`. The tasks
> below add verification tests only.

### Tests for User Story 3

- [X] T012 [US3] Add `test_get_available_environments_excludes_default` to `testing/test_arcgis_cloning.py`: assert `"default" not in get_available_environments()`
- [X] T013 [P] [US3] Add `test_get_available_environments_contains_source_and_destination` to `testing/test_arcgis_cloning.py`: assert `"source" in envs` and `"destination" in envs`
- [X] T014 [P] [US3] Add `test_get_available_environments_is_sorted` to `testing/test_arcgis_cloning.py`: assert `envs == sorted(envs)`

**Checkpoint**: `get_available_environments()` contract is verified; adding a third portal to
`config.yml` is immediately discoverable by callers without any Python changes

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T015 [P] Run full test suite (`pytest testing/ -v`) in the project root and confirm all existing tests plus all new tests pass with zero failures
- [X] T016 [P] Verify `config/secrets.yml` is listed in `.gitignore`; confirm no credential values appear in `config.yml` or any other committed file

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 2 (Foundational)  ← start here; no prerequisites
  ├─► Phase 3 (US1)     ← start immediately after Phase 2
  ├─► Phase 4 (US2)     ← T007/T008 (impl) must precede T009/T010/T011 (tests)
  └─► Phase 5 (US3)     ← start immediately after Phase 2
         Phase 3 + Phase 4 + Phase 5
             └─► Phase 6 (Polish)
```

### User Story Dependencies

| Story | Depends on | Independent of |
|---|---|---|
| US1 (P1) | Phase 2 complete | US2, US3 |
| US2 (P2) | Phase 2 complete; T007+T008 before T009–T011 | US1, US3 |
| US3 (P3) | Phase 2 complete | US1, US2 |

### Within Phase 2

- T001 must complete before T002 (the template mirrors the corrected `secrets.yml` format)
- T002 and T003 can run in parallel (different files, no shared dependencies)

### Within Phase 4

- T007 and T008 both edit `src/arcgis_cloning/config.py` — run sequentially; T007 first
- T009, T010, T011 can run in parallel after T007 and T008 are complete

---

## Parallel Execution Examples

### Phase 2

```
T001  (fix secrets.yml indentation)
  ├─► T002 [P]  (create secrets_template.yml)  ─── parallel with T003
  └─► T003 [P]  (update config.yml comments)   ─── parallel with T002
```

### After Phase 2 — US1, US2, US3 in parallel

```
Phase 3 (T004 / T005 [P] / T006 [P])
Phase 4 (T007 → T008 → T009 / T010 [P] / T011 [P])    ─── all three phases
Phase 5 (T012 / T013 [P] / T014 [P])                   ─── can overlap
```

### Phase 3 (US1 tests)

```
T004  (test source config)
T005  [P]  (test destination config)  ─── parallel with T004
T006  [P]  (test invalid env error)   ─── parallel with T004
```

---

## Implementation Strategy

**Delivery order** (user-specified file sequence mapped to user story phases):

| Step | File(s) | Tasks | Phase |
|---|---|---|---|
| 1 | `config/secrets.yml` | T001 | Phase 2 |
| 2 | `config/secrets_template.yml` | T002 | Phase 2 |
| 3 | `config/config.yml` | T003 | Phase 2 |
| 4 | `src/arcgis_cloning/config.py` | T007, T008 | Phase 4 (US2) |
| 5 | `testing/test_arcgis_cloning.py` | T004–T006 (US1), T009–T011 (US2), T012–T014 (US3) | Phases 3, 4, 5 |

**MVP Scope** (Phases 2–4, T001–T011): After these 11 tasks a developer can write a complete
two-portal clone script and `arcgis_cloning.config` imports without errors regardless of
`PROJECT_ENV`.

**Full scope** (all phases, T001–T016): Adds US3 portal enumeration and final test run.

### Task Count Summary

| Phase | Story | Tasks |
|---|---|---|
| Phase 2 — Foundational | — | 3 (T001–T003) |
| Phase 3 — US1 | US1 | 3 (T004–T006) |
| Phase 4 — US2 | US2 | 5 (T007–T011) |
| Phase 5 — US3 | US3 | 3 (T012–T014) |
| Phase 6 — Polish | — | 2 (T015–T016) |
| **Total** | | **16** |

**Parallel opportunities**: 10 tasks marked `[P]` — T002, T003, T005, T006, T010, T011,
T013, T014, T015, T016
