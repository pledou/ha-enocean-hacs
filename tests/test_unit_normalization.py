"""Tests for EnOcean unit normalization in eep_devices._normalize_unit."""

from custom_components.enocean import eep_devices as ed
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature


def test_percent_normalization() -> None:
    """Test that percent unit strings normalize to the Home Assistant percentage constant."""
    assert ed._normalize_unit("%") == PERCENTAGE
    assert ed._normalize_unit("percent") == PERCENTAGE
    assert ed._normalize_unit("Percentage") == PERCENTAGE


def test_temperature_normalization() -> None:
    """Test that temperature unit strings normalize to Home Assistant constants."""
    assert ed._normalize_unit("°C") == UnitOfTemperature.CELSIUS
    assert ed._normalize_unit("c") == UnitOfTemperature.CELSIUS
    assert ed._normalize_unit("Celsius") == UnitOfTemperature.CELSIUS
    assert ed._normalize_unit("°F") == UnitOfTemperature.FAHRENHEIT
    assert ed._normalize_unit("f") == UnitOfTemperature.FAHRENHEIT


def test_power_normalization() -> None:
    """Test that power unit strings normalize to Home Assistant power constants."""
    assert ed._normalize_unit("W") == UnitOfPower.WATT
    assert ed._normalize_unit("watts") == UnitOfPower.WATT


def test_unknown_and_none_preserved() -> None:
    """Test that unknown unit strings and None are returned unchanged."""
    assert ed._normalize_unit("unknown-unit") == "unknown-unit"
    assert ed._normalize_unit(None) is None
