"""Unit tests for MAC address utilities."""

import pytest

from hotspot.core.mac import (
    MACClass,
    MACClassifier,
    is_valid_mac,
    is_randomized_mac,
    normalize_mac,
)


class TestIsValidMac:
    """Tests for is_valid_mac function."""

    def test_valid_mac_colons(self):
        """Test valid MAC with colons."""
        assert is_valid_mac("AA:BB:CC:DD:EE:FF") is True

    def test_valid_mac_lowercase(self):
        """Test valid MAC with lowercase."""
        assert is_valid_mac("aa:bb:cc:dd:ee:ff") is True

    def test_valid_mac_mixed(self):
        """Test valid MAC with mixed case."""
        assert is_valid_mac("Aa:Bb:Cc:Dd:Ee:Ff") is True

    def test_valid_mac_no_colons(self):
        """Test valid MAC without separators - actually not valid per is_valid_mac."""
        # The is_valid_mac function requires colons, so this should be False
        assert is_valid_mac("aabbccddeeff") is False

    def test_invalid_mac_too_short(self):
        """Test MAC that is too short."""
        assert is_valid_mac("AA:BB:CC:DD:EE") is False

    def test_invalid_mac_too_long(self):
        """Test MAC that is too long."""
        assert is_valid_mac("AA:BB:CC:DD:EE:FF:00") is False

    def test_invalid_mac_invalid_chars(self):
        """Test MAC with invalid characters."""
        assert is_valid_mac("GG:HH:II:JJ:KK:LL") is False

    def test_invalid_mac_empty(self):
        """Test empty MAC."""
        assert is_valid_mac("") is False

    def test_realistic_macs_from_probes(self):
        """Test realistic MACs found in real WiFi probe requests."""
        assert is_valid_mac("D4:AB:CD:9E:23:11") is True
        assert is_valid_mac("12:BA:8F:34:D5:07") is True
        assert is_valid_mac("78:CA:39:BB:1B:E3") is True


class TestIsRandomizedMac:
    """Tests for is_randomized_mac function."""

    def test_local_mac_2(self):
        """Test local MAC with 2 as second char of first byte."""
        assert is_randomized_mac("2A:BB:CC:DD:EE:FF") is True

    def test_local_mac_6(self):
        """Test local MAC with 6 as second char of first byte."""
        assert is_randomized_mac("6A:BB:CC:DD:EE:FF") is True

    def test_local_mac_a(self):
        """Test local MAC with A as second char of first byte."""
        assert is_randomized_mac("AA:BB:CC:DD:EE:FF") is True

    def test_local_mac_e(self):
        """Test local MAC with E as second char of first byte."""
        assert is_randomized_mac("EA:BB:CC:DD:EE:FF") is True

    def test_actual_mac_0(self):
        """Test actual MAC with 0 as second char of first byte."""
        assert is_randomized_mac("00:BB:CC:DD:EE:FF") is False

    def test_actual_mac_1(self):
        """Test actual MAC with 1 as second char of first byte."""
        assert is_randomized_mac("10:BB:CC:DD:EE:FF") is False

    def test_actual_mac_8(self):
        """Test actual MAC with 8 as second char of first byte."""
        assert is_randomized_mac("80:BB:CC:DD:EE:FF") is False

    def test_actual_mac_c(self):
        """Test actual MAC with C as second char of first byte."""
        assert is_randomized_mac("C0:BB:CC:DD:EE:FF") is False

    def test_invalid_mac_returns_false(self):
        """Test invalid MAC returns False."""
        assert is_randomized_mac("invalid") is False

    def test_realistic_randomized_macs(self):
        """Test realistic randomized MACs from real device probes."""
        # Local MACs have 2nd char of 1st byte as 2, 6, A, or E
        assert is_randomized_mac("12:BA:8F:34:D5:07") is True   # 1 is local (0x12)
        assert is_randomized_mac("66:A3:92:39:49:11") is True   # 6 is local (0x66)
        assert is_randomized_mac("9A:F1:85:30:20:6A") is True   # 9 is local (0x9A)
        assert is_randomized_mac("AA:50:F3:21:AC:30") is True   # A is local (0xAA)
        assert is_randomized_mac("82:45:FB:CB:86:24") is True   # 8 is local (0x82)
        assert is_randomized_mac("8E:F0:34:A8:69:29") is True   # 8 is local (0x8E)
        assert is_randomized_mac("E2:2B:CB:DA:42:FF") is True   # E is local (0xE2)

    def test_realistic_actual_macs(self):
        """Test realistic actual MACs from real device probes."""
        # These MACs have OUI from real manufacturers
        assert is_randomized_mac("78:CA:39:BB:1B:E3") is False  # 7 is actual


class TestNormalizeMac:
    """Tests for normalize_mac function."""

    def test_normalize_with_colons(self):
        """Test MAC already has colons."""
        result = normalize_mac("aa:bb:cc:dd:ee:ff")
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_normalize_with_dashes(self):
        """Test MAC with dashes."""
        result = normalize_mac("aa-bb-cc-dd-ee-ff")
        assert result == "AA:BB:CC:DD:EE:FF"

    def test_normalize_no_separators(self):
        """Test MAC with no separators - normalize_mac only handles colons/dashes."""
        # normalize_mac replaces colons/dashes but doesn't add them
        result = normalize_mac("aabbccddeeff")
        assert result == "AABBCCDDEEFF"

    def test_normalize_realistic_mac(self):
        """Test normalizing realistic MAC from probe data."""
        result = normalize_mac("d4:ab:cd:9e:23:11")
        assert result == "D4:AB:CD:9E:23:11"


class TestMACClassifier:
    """Tests for MACClassifier class."""

    def test_classify_local(self):
        """Test classifying local MAC."""
        result = MACClassifier.classify("2A:BB:CC:DD:EE:FF")
        assert result == MACClass.LOCAL

    def test_classify_actual(self):
        """Test classifying actual MAC."""
        result = MACClassifier.classify("00:BB:CC:DD:EE:FF")
        assert result == MACClass.ACTUAL

    def test_classify_unknown(self):
        """Test classifying invalid MAC."""
        result = MACClassifier.classify("invalid")
        assert result == MACClass.UNKNOWN

    def test_is_local_true(self):
        """Test is_local returns True for local MAC."""
        assert MACClassifier.is_local("2A:BB:CC:DD:EE:FF") is True

    def test_is_local_false(self):
        """Test is_local returns False for actual MAC."""
        assert MACClassifier.is_local("00:BB:CC:DD:EE:FF") is False

    def test_is_actual_true(self):
        """Test is_actual returns True for actual MAC."""
        assert MACClassifier.is_actual("00:BB:CC:DD:EE:FF") is True

    def test_is_actual_false(self):
        """Test is_actual returns False for local MAC."""
        assert MACClassifier.is_actual("2A:BB:CC:DD:EE:FF") is False

    def test_classify_realistic_probe_macs(self):
        """Test classifying realistic MACs from probe requests."""
        assert MACClassifier.classify("12:BA:8F:34:D5:07") == MACClass.LOCAL
        assert MACClassifier.classify("78:CA:39:BB:1B:E3") == MACClass.ACTUAL
        assert MACClassifier.classify("66:A3:92:39:49:11") == MACClass.LOCAL
        assert MACClassifier.classify("AA:50:F3:21:AC:30") == MACClass.LOCAL
