"""Script to run ArcGIS portal content migration.

Reads source and destination portal environment names from ``config/config.yml``
(``migration.source_env`` and ``migration.destination_env``), bootstraps a root
logger writing a full DEBUG-level audit trail to
``data/logs/clone_content_YYMMDDHHMM.log``, delegates all migration work to
``arcgis_cloning.migrate_content()``, and exits with code ``0`` on success or
``1`` on pre-flight failure.

This script is a thin entry point — no business logic lives here.
"""
# import core Python libraries
import argparse
import logging
import sys
from datetime import datetime
import importlib.util

# import third-party libraries
from pathlib import Path

# path to the root of the project
DIR_PRJ = Path(__file__).parent.parent

# if the project package is not installed in the environment, add the source directory to the system path
if importlib.util.find_spec('arcgis_cloning') is None:

    # get the relative path to where the source directory is located
    src_dir = DIR_PRJ / 'src'

    # throw an error if the source directory cannot be located
    if not src_dir.exists():
        raise EnvironmentError('Unable to import arcgis_cloning.')

    # add the source directory to the paths searched when importing
    sys.path.insert(0, str(src_dir))

# import arcgis_cloning
import arcgis_cloning
from arcgis_cloning.utils import get_logger
from arcgis_cloning.config import load_config
from arcgis_cloning import migrate_content

if __name__ == '__main__':

    # --- CLI argument parsing ---
    parser = argparse.ArgumentParser(description="Run ArcGIS portal content migration.")
    parser.add_argument(
        "--csv",
        action="store_true",
        default=True,
        help="Write a URL mapping CSV alongside the log file (clone_content_YYMMDDHHMM.csv).",
    )
    parser.add_argument(
        "--no-csv",
        dest="csv",
        action="store_false",
        help="Disable URL mapping CSV output.",
    )
    args = parser.parse_args()

    # --- Log file setup (FR-002, FR-003) ---
    date_string = datetime.now().strftime("%y%m%d%H%M")  # YYMMDDHHMM
    log_dir = DIR_PRJ / 'data' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f'clone_content_{date_string}.log'
    csv_file = log_dir / f'clone_content_{date_string}.csv' if args.csv else None

    # --- Logging bootstrap (FR-007) ---
    # Load config to get the desired console log level; fall back to DEBUG
    cfg = load_config()
    console_level = cfg.logging.level if hasattr(cfg, 'logging') else 'DEBUG'

    # Root logger at DEBUG so all records reach handlers; file captures everything
    logger = get_logger(level='DEBUG', add_stream_handler=True, logfile_path=log_file)

    # Tune the stream (console) handler to the config-driven level
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(console_level)

    # --- Read migration environment names from config (FR-004, FR-005) ---
    migration_cfg = getattr(cfg, 'migration', None)
    source_env = getattr(migration_cfg, 'source_env', 'source') if migration_cfg else 'source'
    destination_env = getattr(migration_cfg, 'destination_env', 'destination') if migration_cfg else 'destination'

    # --- Start banner (FR-006) ---
    logger.info(
        f'Starting migration | source_env={source_env!r} | '
        f'destination_env={destination_env!r} | log={log_file}'
    )
    if csv_file:
        logger.info(f'CSV output: {csv_file}')

    # --- Run migration (FR-001) ---
    try:
        result = migrate_content(
            source_env=source_env,
            destination_env=destination_env,
            url_csv_path=csv_file,
        )
        logger.info(
            f'Migration complete: migrated={result.migrated}, '
            f'skipped={result.skipped}, failed={result.failed}'
        )
    except Exception as e:
        msg = f'Migration failed (pre-flight error): {e}'
        logger.critical(msg)
        sys.exit(1)

