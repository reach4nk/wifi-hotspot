"""Unit tests for credential generator."""

import pytest

from hotspot.credentials.generator import (
    ADJECTIVES,
    NOUNS,
    SPECIAL_CHARS,
    CredentialGenerator,
    Credentials,
)


class TestCredentialGenerator:
    """Tests for CredentialGenerator class."""

    def test_random_element(self):
        """Test random_element returns element from array."""
        arr = ("a", "b", "c")
        result = CredentialGenerator.random_element(arr)
        assert result in arr

    def test_word_format(self):
        """Test word generates correct format."""
        result = CredentialGenerator.word()
        assert len(result) >= 6
        assert any(result.startswith(adj) for adj in ADJECTIVES)
        # Word ends with 3-digit number, not a noun
        assert len(result) >= 8  # min adj(3) + noun(3) + number(3) = 9 chars
        assert result[-3:].isdigit()  # Ends with 3 digits
        assert any(result.startswith(adj) for adj in ADJECTIVES)

    def test_word_simple_format(self):
        """Test word_simple generates correct format."""
        result = CredentialGenerator.word_simple()
        assert len(result) >= 2
        assert any(result.startswith(adj) for adj in ADJECTIVES)
        assert any(result.endswith(noun) for noun in NOUNS if len(noun) < 5)

    def test_password_format(self):
        """Test password includes special char."""
        result = CredentialGenerator.password()
        assert any(c in SPECIAL_CHARS for c in result)

    def test_wep_key_format(self):
        """Test WEP key is 26 hex characters."""
        result = CredentialGenerator.wep_key()
        assert len(result) == 26
        assert all(c in "0123456789abcdef" for c in result)

    def test_wep_key_128bit_format(self):
        """Test 128-bit WEP key is 32 hex characters."""
        result = CredentialGenerator.wep_key_128bit()
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_ssid_format(self):
        """Test SSID has prefix and emoji."""
        result = CredentialGenerator.ssid()
        assert result.startswith("!")
        assert "🛜" in result

    def test_ssid_custom_prefix(self):
        """Test SSID with custom prefix."""
        result = CredentialGenerator.ssid(prefix="@")
        assert result.startswith("@")
        assert "🛜" in result

    def test_passphrase_word_count(self):
        """Test passphrase has correct number of words."""
        result = CredentialGenerator.passphrase(word_count=4)
        words = result.split()
        assert len(words) == 5  # 4 words + 1 number

    def test_generate_open_network(self):
        """Test generate for open network."""
        creds = CredentialGenerator.generate(encryption="open")
        assert creds.encryption == "open"
        assert creds.password == ""
        assert creds.ssid != ""

    def test_generate_wpa_with_password(self):
        """Test generate for WPA with password."""
        creds = CredentialGenerator.generate(
            ssid="TestNet",
            password="TestPass123",
            encryption="wpa2"
        )
        assert creds.ssid == "TestNet"
        assert creds.password == "TestPass123"
        assert creds.encryption == "wpa2"

    def test_generate_invalid_encryption(self):
        """Test generate with invalid encryption raises."""
        with pytest.raises(ValueError):
            CredentialGenerator.generate(encryption="invalid")


class TestCredentials:
    """Tests for Credentials dataclass."""

    def test_to_dict(self):
        """Test to_dict returns correct structure."""
        creds = Credentials(
            ssid="TestNet",
            password="TestPass123",
            encryption="wpa2"
        )
        result = creds.to_dict()
        assert result == {
            "ssid": "TestNet",
            "password": "TestPass123",
            "encryption": "wpa2",
        }

    def test_str_representation(self):
        """Test string representation."""
        creds = Credentials(
            ssid="TestNet",
            password="TestPass123",
            encryption="wpa2"
        )
        result = str(creds)
        assert "TestNet" in result
        assert "TestPass123" in result
        assert "wpa2" in result
