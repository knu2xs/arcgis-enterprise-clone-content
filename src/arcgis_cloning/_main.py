"""Main module for arcgis_cloning package."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from .utils import get_logger
from .config import load_secrets

if TYPE_CHECKING:
    from arcgis.gis import GIS

# configure module logging, the same logger as the package-level logger
logger = get_logger("arcgis_cloning", level="DEBUG", add_stream_handler=False)


@dataclass
class MigrationResult:
    """Result of a content migration operation.

    Args:
        migrated: Number of items successfully cloned to the destination portal.
        skipped: Number of items skipped because they were already present (resume mode).
        failed: Number of items that could not be cloned due to errors.
        failures: List of failure records, each containing ``item_id``, ``title``,
            ``type``, and ``error`` keys.
    """

    migrated: int = 0
    skipped: int = 0
    failed: int = 0
    failures: list[dict] = field(default_factory=list)


def _connect_gis(env_name: str, gis_obj: GIS | None) -> GIS:
    """Return the provided GIS object or connect via ``secrets.yml`` credentials.

    Args:
        env_name: Key name in ``secrets.yml`` (e.g. ``"source"`` or ``"destination"``).
        gis_obj: Pre-built ``GIS`` object. When not ``None`` it is returned as-is.

    Returns:
        GIS: An authenticated ``arcgis.gis.GIS`` instance.

    Raises:
        KeyError: If ``env_name`` is not a key in ``secrets.yml`` or credentials are
            insufficient to connect.
        RuntimeError: If the portal connection attempt fails.
    """
    if gis_obj is not None:
        return gis_obj

    secrets = load_secrets()

    try:
        env_secrets = getattr(secrets, env_name)
    except AttributeError:
        msg = (
            f"Environment '{env_name}' not found in secrets.yml. "
            "Verify the key exists and the file is properly configured."
        )
        logger.critical(msg)
        raise KeyError(msg)

    profile = getattr(env_secrets, "profile", None) or None
    url = getattr(env_secrets, "url", None)
    username = getattr(env_secrets, "username", None)
    password = getattr(env_secrets, "password", None)

    try:
        from arcgis.gis import GIS as _GIS  # local import — arcgis provided by ArcGIS Pro env

        if profile:
            logger.debug(f"Connecting to '{env_name}' portal using profile '{profile}'")
            gis = _GIS(profile=profile)
        elif url and username and password:
            logger.debug(
                f"Connecting to '{env_name}' portal at '{url}' with username '{username}'"
            )
            gis = _GIS(url, username, password)
        else:
            msg = (
                f"Insufficient credentials for environment '{env_name}': "
                "provide 'profile' or 'url' + 'username' + 'password' in secrets.yml."
            )
            logger.critical(msg)
            raise KeyError(msg)

        logger.debug(f"Connected to '{env_name}' portal: {gis.url}")
        return gis

    except KeyError:
        raise
    except Exception as e:
        msg = f"Failed to connect to '{env_name}' portal: {e}"
        logger.critical(msg)
        raise RuntimeError(msg) from e


def _get_all_items(gis: GIS, query: str | None, max_items: int | None) -> list:
    """Fetch all items from a GIS portal matching the given query.

    Args:
        gis: Authenticated ``GIS`` instance to search.
        query: Item query string. ``None`` or empty string returns all accessible items.
        max_items: Optional cap on the number of items returned. ``None`` means no limit.

    Returns:
        list: List of ``arcgis.gis.Item`` objects.
    """
    items = gis.content.search(query or "", max_items=-1)
    if max_items is not None:
        items = items[:max_items]
    logger.debug(
        f"Retrieved {len(items)} items from portal (query={query!r}, max_items={max_items})"
    )
    return items


def _build_dest_index(dest_gis: GIS) -> set[tuple[str, str]]:
    """Build a ``(title, type)`` lookup set for all items in the destination portal.

    Args:
        dest_gis: Authenticated destination ``GIS`` instance.

    Returns:
        set[tuple[str, str]]: Set of ``(title, type)`` tuples for all destination items.
    """
    items = dest_gis.content.search("", max_items=-1)
    index = {(item.title, item.type) for item in items}
    logger.debug(f"Destination index built: {len(index)} items")
    return index


def _resolve_folder_name(src_item: object, src_gis: GIS) -> str | None:
    """Resolve the folder name for a source item from its ``ownerFolder`` ID.

    Args:
        src_item: Source ``arcgis.gis.Item`` object.
        src_gis: Authenticated source ``GIS`` instance (used to look up folder names).

    Returns:
        str | None: Folder name string, or ``None`` if the item is at the root level.
    """
    folder_id = src_item["ownerFolder"]
    if folder_id is None:
        logger.debug(f"Item '{src_item.title}' is at root (no folder)")
        return None
    folder_id_to_name = {f["id"]: f["title"] for f in src_gis.users.me.folders}
    name = folder_id_to_name.get(folder_id)
    logger.debug(f"Item '{src_item.title}' resolved to folder '{name}' (id={folder_id})")
    return name


def _ensure_folder(dest_gis: GIS, folder_name: str | None) -> None:
    """Ensure a folder exists in the destination portal, creating it only if absent.

    Args:
        dest_gis: Authenticated destination ``GIS`` instance.
        folder_name: Folder name to check or create. ``None`` means root; no action taken.
    """
    if folder_name is None:
        return
    existing = {f["title"] for f in dest_gis.users.me.folders}
    if folder_name in existing:
        logger.debug(f"Folder '{folder_name}' already exists in destination; skipping creation")
    else:
        dest_gis.content.folders.create(folder=folder_name)
        logger.debug(f"Created folder '{folder_name}' in destination")


def migrate_content(
    source_gis: GIS | None = None,
    destination_gis: GIS | None = None,
    source_env: str = "source",
    destination_env: str = "destination",
    resume: bool = False,
    query: str | None = None,
    max_items: int | None = None,
) -> MigrationResult:
    """Migrate ArcGIS portal content from a source portal to a destination portal.

    Connects to both portals, discovers all matching source items, and clones each one
    to the destination while mirroring the source folder structure. Per-item clone
    failures are recorded in the returned ``MigrationResult`` and do not halt the
    migration.

    !!! note
        Resume mode compares items by ``(title, type)`` only. Items with the same title
        but a different type are treated as absent and will be cloned. A stable ID-based
        mapping is deferred to a future version.

    ```python
    result = migrate_content(resume=True, query="owner:myuser")
    print(f"Migrated: {result.migrated}, Skipped: {result.skipped}, Failed: {result.failed}")
    ```

    Args:
        source_gis: Pre-built authenticated ``GIS`` object for the source portal. When
            ``None``, credentials are loaded from ``secrets.yml`` using ``source_env``.
        destination_gis: Pre-built authenticated ``GIS`` object for the destination
            portal. When ``None``, credentials are loaded from ``secrets.yml`` using
            ``destination_env``.
        source_env: Key name in ``secrets.yml`` for the source portal credentials.
            Defaults to ``"source"``. Ignored when ``source_gis`` is provided.
        destination_env: Key name in ``secrets.yml`` for the destination portal
            credentials. Defaults to ``"destination"``. Ignored when ``destination_gis``
            is provided.
        resume: When ``True``, items already present in the destination (matched by
            title and type) are skipped. Defaults to ``False`` (fresh-run mode always
            clones).
        query: Item search query string passed to ``gis.content.search()``. ``None``
            returns all items accessible to the authenticated source user.
        max_items: Optional cap on the number of source items to process. ``None`` means
            no limit. Primarily intended for safety checks and testing.

    Returns:
        MigrationResult: Dataclass with ``migrated``, ``skipped``, ``failed``, and
            ``failures`` fields summarising the migration outcome.

    Raises:
        ValueError: If the source and destination portal URLs are identical.
        KeyError: If credentials for ``source_env`` or ``destination_env`` are missing
            from ``secrets.yml`` when a pre-built ``GIS`` object is not supplied.
        RuntimeError: If the connection to either portal fails.
    """
    logger.debug(
        f"migrate_content called: source_env={source_env!r}, destination_env={destination_env!r}, "
        f"resume={resume}, query={query!r}, max_items={max_items}, "
        f"source_gis={'<provided>' if source_gis is not None else None}, "
        f"destination_gis={'<provided>' if destination_gis is not None else None}"
    )

    result = MigrationResult()

    # --- Pre-flight: connect to both portals ---
    src_gis = _connect_gis(source_env, source_gis)
    dest_gis = _connect_gis(destination_env, destination_gis)

    # --- Pre-flight: reject identical source/destination ---
    if src_gis.url == dest_gis.url:
        msg = (
            f"Source and destination portals share the same URL: '{src_gis.url}'. "
            "Migration aborted to prevent unintended self-cloning."
        )
        logger.critical(msg)
        raise ValueError(msg)

    # --- Discover source items ---
    items = _get_all_items(src_gis, query, max_items)
    total = len(items)

    logger.info(
        f"Migration started | source={src_gis.url} | destination={dest_gis.url} | "
        f"resume={resume} | query={query!r} | items_found={total}"
    )

    if total == 0:
        logger.warning(
            f"No items found in source portal for query={query!r}. Nothing to migrate."
        )
        return result

    # --- Resume: build destination index ---
    dest_index: set[tuple[str, str]] = set()
    if resume:
        dest_index = _build_dest_index(dest_gis)
        logger.debug(f"Resume mode active: {len(dest_index)} items already in destination")

    # --- Per-item migration loop with progress tracking ---
    for n, item in enumerate(tqdm(items, start=1, total=total, desc="Migrating items"), start=1):
        title = item.title
        item_type = item.type
        item_id = item.itemid

        logger.debug(
            f"Processing item {n}/{total}: '{title}' ({item_type}, id={item_id})"
        )

        # Skip already-present items in resume mode
        if resume and (title, item_type) in dest_index:
            logger.info(f"Skipping already-present item: {title} ({item_type})")
            result.skipped += 1
            continue

        # Mirror source folder structure
        folder_name = _resolve_folder_name(item, src_gis)
        _ensure_folder(dest_gis, folder_name)

        logger.info(f"Migrating item {n} of {total}: {title} ({item_type})")
        t0 = time.perf_counter()
        try:
            dest_gis.content.clone_items(items=[item], folder=folder_name)
            # TODO (post-clone WARNING): compare cloned item properties against source
            elapsed = time.perf_counter() - t0
            logger.debug(f"Cloned '{title}' ({item_type}) in {elapsed:.2f}s")
            result.migrated += 1
        except Exception as e:
            msg = f"Failed to clone '{title}' ({item_type}, id={item_id}): {e}"
            logger.error(msg)
            result.failed += 1
            result.failures.append(
                {"item_id": item_id, "title": title, "type": item_type, "error": str(e)}
            )

    logger.info(
        f"Migration complete | migrated={result.migrated} | "
        f"skipped={result.skipped} | failed={result.failed}"
    )
    return result
