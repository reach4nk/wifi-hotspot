"""Core functionality for the hotspot package."""

from hotspot.core.interface import InterfaceManager
from hotspot.core.mac import MACClassifier
from hotspot.core.process import ProcessManager
from hotspot.core.network import NetworkManager
from hotspot.core.firewall import FirewallManager

__all__ = [
    "InterfaceManager",
    "MACClassifier",
    "ProcessManager",
    "NetworkManager",
    "FirewallManager",
]
