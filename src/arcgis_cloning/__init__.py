__title__ = "arcgis-enterprise-clone-content"
__version__ = "0.0.0"
__author__ = "Joel McCune (https://github.com/knu2xs)"

__license__ = "Apache 2.0"

__copyright__ = "Copyright 2026 by Joel McCune (https://github.com/knu2xs)"

# add specific imports below if you want to organize your code into modules, which is mostly what I do
from . import config as config
from . import utils
from ._main import migrate_content, MigrationResult

__all__ = ["config", "utils", "migrate_content", "MigrationResult"]

# configure package-level logging
logger = utils.get_logger("arcgis_cloning", level="DEBUG", add_stream_handler=False)
