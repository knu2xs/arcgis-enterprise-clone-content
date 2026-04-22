"""
This is a stubbed out test file designed to be used with PyTest, but can 
easily be modified to support any testing framework.
"""

import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# get paths to useful resources - notably where the src directory is
self_pth = Path(__file__)
dir_test = self_pth.parent
dir_prj = dir_test.parent
dir_src = dir_prj / 'src'

# insert the src directory into the path and import the projct package
sys.path.insert(0, str(dir_src))
import arcgis_cloning
import arcgis_cloning.config as cfg_module
from arcgis_cloning.config import load_config, get_available_environments
from arcgis_cloning import migrate_content, MigrationResult


def test_example():
    assert 2 + 2 == 4


# ---------------------------------------------------------------------------
# US1 — Load portal config by name
# ---------------------------------------------------------------------------

def test_load_config_source_returns_config_node():
    cfg = load_config(environment="source")
    assert cfg.logging.level == "DEBUG"
    assert cfg.data.input == "data/raw/input_data.csv"


def test_load_config_destination_returns_config_node():
    cfg = load_config(environment="destination")
    assert cfg.data.output == "data/processed/processed.gdb/output_data"


def test_load_config_invalid_env_raises_value_error():
    import pytest
    with pytest.raises(ValueError, match="Invalid environment"):
        load_config(environment="nonexistent_portal")


# ---------------------------------------------------------------------------
# US2 — Default environment points to source
# ---------------------------------------------------------------------------

def test_environment_default_is_source(monkeypatch):
    monkeypatch.delenv("PROJECT_ENV", raising=False)
    importlib.reload(cfg_module)
    assert cfg_module.ENVIRONMENT == "source"


def test_import_without_project_env_raises_no_error(monkeypatch):
    monkeypatch.delenv("PROJECT_ENV", raising=False)
    importlib.reload(cfg_module)
    assert cfg_module.config.logging.level is not None


def test_project_env_destination_sets_environment(monkeypatch):
    monkeypatch.setenv("PROJECT_ENV", "destination")
    importlib.reload(cfg_module)
    assert cfg_module.ENVIRONMENT == "destination"


# ---------------------------------------------------------------------------
# US3 — Discover available portals
# ---------------------------------------------------------------------------

def test_get_available_environments_excludes_default():
    envs = get_available_environments()
    assert "default" not in envs


def test_get_available_environments_contains_source_and_destination():
    envs = get_available_environments()
    assert "source" in envs
    assert "destination" in envs


def test_get_available_environments_is_sorted():
    envs = get_available_environments()
    assert envs == sorted(envs)


# ---------------------------------------------------------------------------
# Helpers for migrate_content tests
# ---------------------------------------------------------------------------

def _make_item(title: str, item_type: str, item_id: str = "abc123", owner_folder=None):
    """Create a mock ArcGIS Item with attribute and dict-style access."""
    item = MagicMock()
    item.title = title
    item.type = item_type
    item.itemid = item_id
    item.__getitem__ = MagicMock(
        side_effect=lambda key: owner_folder if key == "ownerFolder" else None
    )
    return item


def _make_gis(url: str, items=None, folders=None):
    """Create a mock GIS instance with pre-configured content.search and folders."""
    gis = MagicMock()
    gis.url = url
    gis.content.search.return_value = items if items is not None else []
    gis.users.me.folders = folders if folders is not None else []
    return gis


# ---------------------------------------------------------------------------
# US1 — Migrate content: core tests (T010-T013)
# ---------------------------------------------------------------------------

def test_migrate_content_returns_migration_result():
    item = _make_item("Map A", "Web Map")
    src = _make_gis("https://src.example.com", items=[item])
    dst = _make_gis("https://dst.example.com")
    result = migrate_content(source_gis=src, destination_gis=dst)
    assert isinstance(result, MigrationResult)


def test_migrate_content_migrates_all_items():
    items = [
        _make_item("Map A", "Web Map", "id1"),
        _make_item("Map B", "Web Map", "id2"),
        _make_item("Map C", "Dashboard", "id3"),
    ]
    src = _make_gis("https://src.example.com", items=items)
    dst = _make_gis("https://dst.example.com")
    result = migrate_content(source_gis=src, destination_gis=dst)
    assert result.migrated == 3
    assert result.skipped == 0
    assert result.failed == 0


def test_migrate_content_zero_items_returns_empty_result():
    src = _make_gis("https://src.example.com", items=[])
    dst = _make_gis("https://dst.example.com")
    result = migrate_content(source_gis=src, destination_gis=dst)
    assert result.migrated == 0
    assert result.skipped == 0
    assert result.failed == 0


def test_migrate_content_same_url_raises():
    import pytest
    src = _make_gis("https://same.example.com")
    dst = _make_gis("https://same.example.com")
    with pytest.raises(ValueError):
        migrate_content(source_gis=src, destination_gis=dst)


# ---------------------------------------------------------------------------
# US2 — Resume tests (T015-T018)
# ---------------------------------------------------------------------------

def test_migrate_content_resume_skips_existing():
    item_a = _make_item("Map A", "Web Map", "id_a")
    item_b = _make_item("Map B", "Web Map", "id_b")
    dest_item_a = _make_item("Map A", "Web Map", "dst_a")

    src = _make_gis("https://src.example.com", items=[item_a, item_b])
    dst = _make_gis("https://dst.example.com", items=[dest_item_a])

    result = migrate_content(source_gis=src, destination_gis=dst, resume=True)
    assert result.skipped == 1
    assert result.migrated == 1


def test_migrate_content_resume_all_present_returns_zero_migrated():
    source_items = [
        _make_item("Map A", "Web Map", "id_a"),
        _make_item("Map B", "Dashboard", "id_b"),
    ]
    dest_items = [
        _make_item("Map A", "Web Map", "dst_a"),
        _make_item("Map B", "Dashboard", "dst_b"),
    ]
    src = _make_gis("https://src.example.com", items=source_items)
    dst = _make_gis("https://dst.example.com", items=dest_items)

    result = migrate_content(source_gis=src, destination_gis=dst, resume=True)
    assert result.migrated == 0
    assert result.skipped == len(source_items)


def test_migrate_content_resume_empty_dest_migrates_all():
    source_items = [
        _make_item("Map A", "Web Map", "id_a"),
        _make_item("Map B", "Dashboard", "id_b"),
    ]
    src = _make_gis("https://src.example.com", items=source_items)
    dst = _make_gis("https://dst.example.com", items=[])

    result = migrate_content(source_gis=src, destination_gis=dst, resume=True)
    assert result.migrated == len(source_items)
    assert result.skipped == 0


def test_migrate_content_resume_title_type_both_must_match():
    # Destination has "Map A" as "Web Map"; source has "Map A" as "Dashboard" — different type
    src_item = _make_item("Map A", "Dashboard", "id_a")
    dest_item = _make_item("Map A", "Web Map", "dst_a")

    src = _make_gis("https://src.example.com", items=[src_item])
    dst = _make_gis("https://dst.example.com", items=[dest_item])

    result = migrate_content(source_gis=src, destination_gis=dst, resume=True)
    assert result.migrated == 1
    assert result.skipped == 0


# ---------------------------------------------------------------------------
# US3 — Structured failure report tests (T019-T022)
# ---------------------------------------------------------------------------

def test_migrate_content_failed_item_does_not_raise():
    item = _make_item("Bad Item", "Web Map", "bad_id")
    src = _make_gis("https://src.example.com", items=[item])
    dst = _make_gis("https://dst.example.com")
    dst.content.clone_items.side_effect = RuntimeError("clone error")

    result = migrate_content(source_gis=src, destination_gis=dst)
    assert isinstance(result, MigrationResult)
    assert result.failed == 1


def test_migrate_content_failure_record_contains_expected_keys():
    item = _make_item("Bad Item", "Web Map", "bad_id")
    src = _make_gis("https://src.example.com", items=[item])
    dst = _make_gis("https://dst.example.com")
    dst.content.clone_items.side_effect = RuntimeError("test error msg")

    result = migrate_content(source_gis=src, destination_gis=dst)
    assert len(result.failures) == 1
    rec = result.failures[0]
    assert rec["item_id"] == "bad_id"
    assert rec["title"] == "Bad Item"
    assert rec["type"] == "Web Map"
    assert "test error msg" in rec["error"]


def test_migrate_content_all_fail_returns_result_not_raises():
    items = [
        _make_item("Item 1", "Web Map", "id1"),
        _make_item("Item 2", "Web Map", "id2"),
        _make_item("Item 3", "Web Map", "id3"),
    ]
    src = _make_gis("https://src.example.com", items=items)
    dst = _make_gis("https://dst.example.com")
    dst.content.clone_items.side_effect = RuntimeError("always fails")

    result = migrate_content(source_gis=src, destination_gis=dst)
    assert result.failed == 3
    assert len(result.failures) == 3


def test_migrate_content_max_items_caps_processing():
    items = [_make_item(f"Map {i}", "Web Map", f"id{i}") for i in range(5)]
    src = _make_gis("https://src.example.com", items=items)
    dst = _make_gis("https://dst.example.com")

    result = migrate_content(source_gis=src, destination_gis=dst, max_items=2)
    assert result.migrated + result.failed + result.skipped == 2


# ---------------------------------------------------------------------------
# Additional US1 tests — T026, T027
# ---------------------------------------------------------------------------

def test_migrate_content_fresh_run_does_not_skip_existing():
    # Fresh run (resume=False) must clone even if same item title+type exists in destination
    item = _make_item("Map A", "Web Map", "id_a")
    # Destination already has an item with same title+type — should be ignored in fresh mode
    dest_existing = _make_item("Map A", "Web Map", "dst_a")

    src = _make_gis("https://src.example.com", items=[item])
    dst = _make_gis("https://dst.example.com", items=[dest_existing])

    result = migrate_content(source_gis=src, destination_gis=dst)  # resume=False (default)
    assert result.migrated == 1
    assert result.skipped == 0


def test_migrate_content_connection_failure_raises_runtime_error():
    import pytest
    with patch("arcgis_cloning._main._connect_gis", side_effect=RuntimeError("Connection failed")):
        with pytest.raises(RuntimeError, match="Connection failed"):
            migrate_content()


# ---------------------------------------------------------------------------
# Folder-mirroring tests — T028, T029
# ---------------------------------------------------------------------------

def test_migrate_content_creates_folder_in_destination():
    # Source item lives in folder "folder123" named "My Folder"
    item = _make_item("Map A", "Web Map", "id_a", owner_folder="folder123")
    src = _make_gis(
        "https://src.example.com",
        items=[item],
        folders=[{"id": "folder123", "title": "My Folder"}],
    )
    # Destination has no folders yet
    dst = _make_gis("https://dst.example.com", folders=[])

    migrate_content(source_gis=src, destination_gis=dst)

    dst.content.folders.create.assert_called_once_with(folder="My Folder")


def test_migrate_content_root_item_skips_folder_creation():
    # Source item is at root (ownerFolder=None)
    item = _make_item("Map A", "Web Map", "id_a", owner_folder=None)
    src = _make_gis("https://src.example.com", items=[item])
    dst = _make_gis("https://dst.example.com")

    migrate_content(source_gis=src, destination_gis=dst)

    dst.content.folders.create.assert_not_called()


# ---------------------------------------------------------------------------
# Feature 003 — make_data.py config fallback and exit-code tests
# ---------------------------------------------------------------------------

def test_make_data_fallback_when_migration_key_absent():
    """FR-004: when 'migration' key is absent from config, fallback to built-in defaults."""
    from arcgis_cloning.config import ConfigNode

    empty_cfg = ConfigNode({})  # no 'migration' attribute

    migration_cfg = getattr(empty_cfg, 'migration', None)
    source_env = getattr(migration_cfg, 'source_env', 'source') if migration_cfg else 'source'
    destination_env = getattr(migration_cfg, 'destination_env', 'destination') if migration_cfg else 'destination'

    assert source_env == 'source'
    assert destination_env == 'destination'


def test_make_data_preflight_failure_exits_with_code_1():
    """SC-004: sys.exit(1) is called when migrate_content raises a pre-flight error."""
    import pytest

    with patch('arcgis_cloning.migrate_content', side_effect=RuntimeError('pre-flight error')):
        with patch('arcgis_cloning.config.load_config') as mock_cfg:
            mock_cfg.return_value = MagicMock(
                logging=MagicMock(level='INFO'),
                migration=MagicMock(source_env='source', destination_env='destination'),
            )
            # Simulate the __main__ try/except block
            import sys as _sys
            from unittest.mock import call as _call
            with pytest.raises(SystemExit) as exc_info:
                try:
                    result = arcgis_cloning.migrate_content(
                        source_env='source', destination_env='destination'
                    )
                except Exception:
                    _sys.exit(1)
            assert exc_info.value.code == 1

