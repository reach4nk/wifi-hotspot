"""WiFi Hotspot Management Package.

A Python package for managing WiFi access points on Linux.
"""

__version__ = "1.0.0"
__author__ = "WiFi Hotspot Team"

from hotspot.utils.logging import setup_logging, get_logger
from hotspot.core.interface import InterfaceManager
from hotspot.core.mac import MACClassifier
from hotspot.services.hotspot import HotspotService

__all__ = [
    "setup_logging",
    "get_logger",
    "InterfaceManager",
    "MACClassifier",
    "HotspotService",
]
