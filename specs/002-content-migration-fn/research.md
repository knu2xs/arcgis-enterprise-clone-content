# Research: Content Migration Function

**Feature**: `002-content-migration-fn` | **Date**: 2026-04-21

## ArcGIS API for Python — Confirmed Patterns

### Decision 1: Clone method

**Decision**: Use `destination_gis.content.clone_items(items=[item], folder=folder_name)` — one item per call.

**Rationale**: Passing one item at a time enables per-item exception handling and accurate
failure recording in `MigrationResult`. Batch cloning would require additional error
decomposition logic to identify which item in a batch failed.

**Alternatives considered**: `Item.clone()` instance method — not the documented pattern
for cross-portal migration; `clone_items` on the destination GIS is the canonical API.

---

### Decision 2: Source item pagination

**Decision**: Use `gis.content.search(query or "", max_items=-1)` to retrieve all items.
Apply `max_items` cap after fetching if the parameter is set.

**Rationale**: `max_items=-1` is the documented way to retrieve all results without manual
pagination loops. Applying the caller-supplied cap post-fetch keeps the pagination logic
simple and avoids off-by-one errors in paged requests.

**Alternatives considered**: `gis.content.advanced_search()` with manual `nextStart` paging —
more complex, not needed since `max_items=-1` is supported on `search()`.

---

### Decision 3: Folder identity on source items

**Decision**: Read `item["ownerFolder"]` which returns a folder ID string (`None` for root).
Build a folder ID → name lookup from `src_gis.users.me.folders` (list of dicts with `id`
and `title` keys). Root items (`ownerFolder is None`) clone to the destination root
(`folder=None`).

**Rationale**: `ownerFolder` exposes the folder ID, not the display name. The user's folder
list provides the ID-to-name mapping. This is stable across portal versions.

**Alternatives considered**: Accessing `item.ownerFolder` as attribute — same value,
dict-style access is more reliable across API versions.

---

### Decision 4: Destination folder creation and deduplication

**Decision**: Before creating a folder, check `dest_gis.users.me.folders` for an existing
entry with a matching `title`. Only call `dest_gis.content.folders.create(folder=name)`
when no match is found.

**Rationale**: `folders.create()` does NOT raise on duplicate names — it silently creates
another folder with the same name, which would scatter items across identically-named folders.
Pre-checking avoids accidental duplication.

**Alternatives considered**: Always create and handle duplicates post-hoc — introduces
cleanup complexity and potential data scatter.

---

### Decision 5: Resume comparison key

**Decision**: `(item.title, item.type)` tuple as the identity key for resume comparison.
Build a `set[tuple[str, str]]` from `destination_gis.content.search("", max_items=-1)`.

**Rationale**: Matches the spec assumption. Stable, simple, requires no persistent state
file. Trade-off (documented in spec Assumptions): items with duplicate title+type in the
destination will be over-skipped — acceptable for v1.

**Alternatives considered**: Item ID mapping via a persisted JSON file — more accurate but
requires file I/O and state management; out of scope for v1.

---

### Decision 6: No new package dependencies

**Decision**: Use only stdlib (`dataclasses`, `time`) and `arcgis` (already in ArcGIS Pro
env). Do not add `arcgis` to `pyproject.toml`.

**Rationale**: Per constitution Spatial & ArcGIS Constraints — ArcPy and `arcgis` are
provided by the ArcGIS Pro conda environment and must not be listed in `pyproject.toml`.
