"""Find interfaces command for the hotspot CLI."""

from __future__ import annotations

from hotspot.cli.base import CLICommand
from hotspot.core.interface import InterfaceManager
from hotspot.utils.logging import get_logger

logger = get_logger("cli.find_interfaces")


class FindInterfacesCommand(CLICommand):
    """Display detected WiFi interfaces."""

    name = "find-interfaces"
    help_text = """\
Usage: hotspot find-interfaces

Display detected WiFi interfaces on the system:
  - Internet interface: Interface in managed mode (connected to internet)
  - Hotspot interface: Interface in master/monitor mode (for hosting)
"""

    def run(self, args) -> int:
        """Run the find-interfaces command.

        Args:
            args: Parsed command line arguments.

        Returns:
            Exit code.
        """
        logger.info("Detecting WiFi interfaces...")

        internal = InterfaceManager.get_internal_interface()
        external = InterfaceManager.get_external_interface()
        all_wireless = InterfaceManager.get_all_wireless()

        print()
        print("Wireless Interfaces:")
        print("----------------------------------------")
        if all_wireless:
            for iface in all_wireless:
                print(f"  {iface}")
        else:
            print("  None found")

        print()
        print("Detected Roles:")
        print("----------------------------------------")
        print(f"  Internet (Managed mode): {internal if internal else 'None'}")
        print(f"  Hotspot (Master/Monitor): {external if external else 'None'}")

        print()
        return 0
