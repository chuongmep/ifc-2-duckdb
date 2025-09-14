"""
IFC to DuckDB conversion utility.

This package provides tools to convert IFC (Industry Foundation Classes) files
to DuckDB format for fast analysis and querying of Building Information
Modeling (BIM) data.
"""

from .patcher import Patcher
from .version import __version__

__all__ = ["Patcher", "__version__"]
__version__ = __version__
