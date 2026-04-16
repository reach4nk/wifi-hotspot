"""Custom exceptions for the hotspot package."""

from __future__ import annotations


class HotspotError(Exception):
    """Base exception for hotspot-related errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InterfaceError(HotspotError):
    """Exception raised for interface-related errors."""

    def __init__(self, message: str, interface: str | None = None) -> None:
        self.interface = interface
        super().__init__(message)


class ServiceError(HotspotError):
    """Exception raised for service-related errors."""

    def __init__(self, message: str, service: str | None = None) -> None:
        self.service = service
        super().__init__(message)


class ConfigurationError(HotspotError):
    """Exception raised for configuration-related errors."""

    pass


class ValidationError(HotspotError):
    """Exception raised for validation errors."""

    pass


class CredentialError(ValidationError):
    """Exception raised for credential-related errors."""

    pass
