"""Credential generation utilities."""

from __future__ import annotations

import random
import secrets
import string
from dataclasses import dataclass
from typing import Optional

from hotspot.utils.logging import get_logger

logger = get_logger("credentials")


ADJECTIVES = (
    "Blue", "Grey", "Dark", "Warm", "Cold", "Bold", "Soft", "Calm",
    "Fast", "Tiny", "Huge", "Kind", "Wild", "Free", "Pure", "Safe",
    "Rich", "Fair", "New", "Old", "Hot", "Wet", "Dry", "Zen",
    "Red", "Cyan", "Gold", "Iron", "Snow", "Rain", "Star", "Moon",
    "Glow", "Fire", "Wind", "Mist", "Wave", "Rock", "Echo", "Core",
    "Peak", "Deep", "Sage", "Lush", "Hush", "Fury", "Dawn", "Fate",
    "Nova", "Bolt"
)

NOUNS = (
    "Node", "Link", "Port", "Net", "Hub", "Beam", "Star", "Moon",
    "Comet", "Nova", "Orb", "Core", "Ring", "Axis", "Wave", "Pixel",
    "Echo", "Flag", "Mine", "Bolt", "Lamp", "Grid", "Lens", "Path",
    "Root", "Peak", "Gate", "Bolt", "Drip", "Loom", "Drift", "Scan",
    "Ship", "Leaf", "Dust", "Mist", "Rain", "Hawk", "Wolf", "Lion",
    "Bear", "Fox", "Rex", "Jet", "Sky", "Sun", "Sea", "Ark",
    "Frog", "Owl"
)

SPECIAL_CHARS = ("!", "@", "#", "$", "%", "&", "*", "+", "-", "=", "?", "_", "~")


@dataclass
class Credentials:
    """Represents generated WiFi credentials."""

    ssid: str
    password: str
    encryption: str

    def __str__(self) -> str:
        return f"SSID: {self.ssid}, Password: {self.password}, Encryption: {self.encryption}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "ssid": self.ssid,
            "password": self.password,
            "encryption": self.encryption,
        }


class CredentialGenerator:
    """Generates WiFi credentials."""

    @staticmethod
    def random_element(arr: tuple[str, ...]) -> str:
        """Pick a random element from a tuple.

        Args:
            arr: Tuple of elements.

        Returns:
            Random element.
        """
        return random.choice(arr)

    @classmethod
    def word(cls) -> str:
        """Generate a memorable random word (adjective + noun + number).

        Returns:
            Random word like 'BlueNode482'.
        """
        adj = cls.random_element(ADJECTIVES)
        noun = cls.random_element(NOUNS)
        num = random.randint(100, 999)
        return f"{adj}{noun}{num}"

    @classmethod
    def word_simple(cls) -> str:
        """Generate a random word without number suffix.

        Returns:
            Random word like 'BlueNode'.
        """
        adj = cls.random_element(ADJECTIVES)
        noun = cls.random_element(NOUNS)
        return f"{adj}{noun}"

    @classmethod
    def password(cls) -> str:
        """Generate a WPA/WPA2 password (word + special char).

        Returns:
            Password like 'BlueNode382#'.
        """
        base = cls.word()
        special = cls.random_element(SPECIAL_CHARS)
        return f"{base}{special}"

    @classmethod
    def password_simple(cls) -> str:
        """Generate a simple password (just words, no special char).

        Returns:
            Password like 'BlueNode382'.
        """
        return cls.word()

    @classmethod
    def passphrase(cls, word_count: int = 3) -> str:
        """Generate a passphrase from multiple random words.

        Args:
            word_count: Number of words.

        Returns:
            Passphrase like 'Blue Node 482'.
        """
        words = [cls.word_simple() for _ in range(word_count)]
        num = random.randint(10, 99)
        return " ".join(words) + f" {num}"

    @classmethod
    def wep_key(cls) -> str:
        """Generate a WEP encryption key (26 hex characters).

        Returns:
            26-character hex string.
        """
        return secrets.token_hex(13)

    @classmethod
    def wep_key_128bit(cls) -> str:
        """Generate a 128-bit WEP key (32 hex characters).

        Returns:
            32-character hex string.
        """
        return secrets.token_hex(16)

    @classmethod
    def ssid(cls, prefix: str = "!") -> str:
        """Generate a WiFi SSID with distinctive prefix.

        Args:
            prefix: Prefix character.

        Returns:
            SSID like '!BlueNode482🛜'.
        """
        return f"{prefix}{cls.word()}🛜"

    @classmethod
    def ssid_simple(cls) -> str:
        """Generate a simple SSID without emoji.

        Returns:
            SSID like 'BlueNode482'.
        """
        return cls.word()

    @classmethod
    def generate(
        cls,
        ssid: Optional[str] = None,
        password: Optional[str] = None,
        encryption: str = "wpa2"
    ) -> Credentials:
        """Generate or use provided credentials.

        Args:
            ssid: SSID to use (generated if None).
            password: Password to use (generated if None).
            encryption: Encryption mode.

        Returns:
            Generated credentials.

        Raises:
            ValueError: If encryption mode is invalid.
        """
        if encryption not in ("open", "wep", "wpa", "wpa2"):
            raise ValueError(f"Invalid encryption mode: {encryption}")

        if encryption == "open":
            password = ""
            if not ssid:
                ssid = cls.ssid()
        elif encryption == "wep":
            if not ssid:
                ssid = cls.ssid()
            if not password:
                password = cls.wep_key()
        elif encryption in ("wpa", "wpa2"):
            if not ssid:
                ssid = cls.ssid()
            if not password:
                password = cls.password()

        return Credentials(
            ssid=ssid or "",
            password=password or "",
            encryption=encryption
        )
