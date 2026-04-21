"""Useful utility functions for arcgis_cloning."""

from ._logging import get_logger

# set up module-level logger
logger = get_logger("arcgis_cloning.utils", level="DEBUG", add_stream_handler=False)
