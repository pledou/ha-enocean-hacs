"""Test device profiles persistence for EnOcean integration."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from custom_components.enocean.const import CONF_DEVICE_PROFILES
from custom_components.enocean.dongle import EnOceanDongle
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

DOMAIN = "enocean"


@pytest.fixture
def mock_serial_communicator():
    """Mock the SerialCommunicator."""
    with patch(
        "custom_components.enocean.dongle.SerialCommunicator"
    ) as mock_comm:
        mock_instance = Mock()
        mock_instance.teach_in = False
        mock_instance.start = Mock()
        mock_instance.base_id = [0xFF, 0x00, 0x00, 0x00]
        mock_comm.return_value = mock_instance
        yield mock_instance


async def test_device_profile_persistence(
    hass: HomeAssistant, mock_serial_communicator
) -> None:
    """Test that device profiles persist across restarts."""
    # Create a test config entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/ttyUSB0", CONF_DEVICE_PROFILES: {}},
        unique_id="test_dongle",
    )
    config_entry.add_to_hass(hass)

    # Create dongle
    dongle = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)

    # Register a device profile
    test_device_id = [0x04, 0x20, 0x58, 0xA5]
    dongle.register_device_profile(test_device_id, 0xD1, 0x07, 0x90)
    await hass.async_block_till_done()

    # Verify the profile was saved to config_entry.data
    assert CONF_DEVICE_PROFILES in config_entry.data
    profiles = config_entry.data[CONF_DEVICE_PROFILES]
    assert len(profiles) > 0

    # Verify the profile content
    device_key_str = "4,32,88,165"  # String representation of [0x04, 0x20, 0x58, 0xA5]
    assert device_key_str in profiles
    assert profiles[device_key_str]["rorg"] == 0xD1
    assert profiles[device_key_str]["func"] == 0x07
    assert profiles[device_key_str]["type"] == 0x90


async def test_device_profile_loading_after_restart(
    hass: HomeAssistant, mock_serial_communicator
) -> None:
    """Test that device profiles are loaded after Home Assistant restart."""
    # Create a config entry with pre-existing device profiles
    test_device_id = [0x04, 0x20, 0x58, 0xA5]
    device_key_str = "4,32,88,165"
    existing_profiles = {device_key_str: {"rorg": 0xD1, "func": 0x07, "type": 0x90}}

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/ttyUSB0", CONF_DEVICE_PROFILES: existing_profiles},
        unique_id="test_dongle",
    )
    config_entry.add_to_hass(hass)

    # Create a new dongle instance (simulates restart)
    dongle = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)

    # Load the profiles
    await dongle.async_load_device_profiles()

    # Verify the profile was loaded
    device_key = tuple(test_device_id)
    assert device_key in dongle._device_profiles
    profile = dongle._device_profiles[device_key]
    assert profile["rorg"] == 0xD1
    assert profile["func"] == 0x07
    assert profile["type"] == 0x90


async def test_multiple_device_profiles_persistence(
    hass: HomeAssistant, mock_serial_communicator
) -> None:
    """Test that multiple device profiles persist correctly."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/ttyUSB0", CONF_DEVICE_PROFILES: {}},
        unique_id="test_dongle",
    )
    config_entry.add_to_hass(hass)

    dongle = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)

    # Register multiple device profiles
    devices = [
        ([0x04, 0x20, 0x58, 0xA5], 0xD1, 0x07, 0x90),
        ([0x04, 0x20, 0x74, 0xC9], 0xA5, 0x04, 0x01),
        ([0x01, 0x02, 0x03, 0x04], 0xD2, 0x04, 0x08),
    ]

    for device_id, rorg, func, type_ in devices:
        dongle.register_device_profile(device_id, rorg, func, type_)
    await hass.async_block_till_done()

    # Verify all profiles were saved
    profiles = config_entry.data[CONF_DEVICE_PROFILES]
    assert len(profiles) == 3

    # Create a new dongle and load profiles
    dongle2 = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)
    await dongle2.async_load_device_profiles()

    # Verify all profiles were loaded
    assert len(dongle2._device_profiles) == 3
    for device_id, rorg, func, type_ in devices:
        device_key = tuple(device_id)
        assert device_key in dongle2._device_profiles
        profile = dongle2._device_profiles[device_key]
        assert profile["rorg"] == rorg
        assert profile["func"] == func
        assert profile["type"] == type_


async def test_device_profile_loading_with_invalid_data(
    hass: HomeAssistant, mock_serial_communicator, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that invalid device profile data is handled gracefully."""
    # Create config entry with invalid profile data
    invalid_profiles = {
        "invalid,key,format": {"rorg": 0xD1, "func": 0x07, "type": 0x90},
        "4,32,88,165": {"rorg": "invalid", "func": 0x07, "type": 0x90},
        "1,2,3,4": {"rorg": 0xA5, "func": 0x04, "type": 0x01},  # Valid profile
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/ttyUSB0", CONF_DEVICE_PROFILES: invalid_profiles},
        unique_id="test_dongle",
    )
    config_entry.add_to_hass(hass)

    dongle = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)
    await dongle.async_load_device_profiles()

    # Only the valid profile should be loaded
    assert len(dongle._device_profiles) == 1

    # Verify the valid profile was loaded
    valid_key = (1, 2, 3, 4)
    assert valid_key in dongle._device_profiles
    assert dongle._device_profiles[valid_key]["rorg"] == 0xA5

    # Check that warnings were logged for invalid profiles
    assert "Failed to load device profile invalid,key,format" in caplog.text
    assert "Failed to load device profile 4,32,88,165" in caplog.text


async def test_device_profile_update_existing(
    hass: HomeAssistant, mock_serial_communicator
) -> None:
    """Test that updating an existing device profile works correctly."""
    test_device_id = [0x04, 0x20, 0x58, 0xA5]

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/ttyUSB0", CONF_DEVICE_PROFILES: {}},
        unique_id="test_dongle",
    )
    config_entry.add_to_hass(hass)

    dongle = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)

    # Register a device profile
    dongle.register_device_profile(test_device_id, 0xD1, 0x07, 0x90)
    await hass.async_block_till_done()

    # Update the same device with different EEP values
    dongle.register_device_profile(test_device_id, 0xA5, 0x04, 0x01)
    await hass.async_block_till_done()

    # Verify the profile was updated
    device_key = tuple(test_device_id)
    profile = dongle._device_profiles[device_key]
    assert profile["rorg"] == 0xA5
    assert profile["func"] == 0x04
    assert profile["type"] == 0x01

    # Verify it's saved to config entry
    profiles = config_entry.data[CONF_DEVICE_PROFILES]
    device_key_str = "4,32,88,165"
    assert profiles[device_key_str]["rorg"] == 0xA5
    assert profiles[device_key_str]["func"] == 0x04
    assert profiles[device_key_str]["type"] == 0x01
