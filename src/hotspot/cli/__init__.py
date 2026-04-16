"""CLI commands for the hotspot package."""

from hotspot.cli.base import CLICommand, require_root
from hotspot.cli.start import StartCommand
from hotspot.cli.stop import StopCommand
from hotspot.cli.monitor import MonitorCommand
from hotspot.cli.scan import ScanCommand
from hotspot.cli.setup import SetupCommand
from hotspot.cli.teardown import TeardownCommand
from hotspot.cli.find_interfaces import FindInterfacesCommand

__all__ = [
    "CLICommand",
    "require_root",
    "StartCommand",
    "StopCommand",
    "MonitorCommand",
    "ScanCommand",
    "SetupCommand",
    "TeardownCommand",
    "FindInterfacesCommand",
]
