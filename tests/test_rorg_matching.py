"""Tests for RORG matching when stored profile RORG is a combined numeric value."""

from __future__ import annotations

from unittest.mock import Mock, patch

from enocean.protocol.constants import RORG
import pytest

from custom_components.enocean.dongle import EnOceanDongle
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


@pytest.fixture
def mock_serial_communicator():
    """Mock the SerialCommunicator used by EnOceanDongle."""
    with patch(
        "custom_components.enocean.dongle.SerialCommunicator"
    ) as mock_comm:
        mock_instance = Mock()
        mock_instance.teach_in = False
        mock_instance.start = Mock()
        mock_instance.base_id = [0xFF, 0x00, 0x00, 0x00]
        mock_comm.return_value = mock_instance
        yield mock_instance


async def test_parse_accepts_combined_numeric_rorg(
    hass: HomeAssistant, mock_serial_communicator
) -> None:
    """When profile.rorg is combined ((RORG<<12)|manuf), UTE teach-in RORG byte should match.

    We mock packet.parse_eep to return a known parsed result so we can assert that
    `_parse_packet_by_profile` proceeded past the rorg check and applied parsing.
    """
    # Setup config entry and dongle
    config_entry = MockConfigEntry(
        domain="enocean",
        data={
            "device": "/dev/ttyUSB0",
        },
        unique_id="test_dongle",
    )
    config_entry.add_to_hass(hass)

    dongle = EnOceanDongle(hass, "/dev/ttyUSB0", config_entry)

    # Device and profile: sender + combined rorg ((0xD1 << 12) | 0x079)
    sender = [0x04, 0x20, 0x58, 0xA5]
    combined_rorg = (0xD1 << 12) | 0x079  # decimal 856185
    dongle._device_profiles[tuple(sender)] = {
        "rorg": combined_rorg,
        "func": 0x07,
        "type": 0x90,
    }

    # Create a fake packet with rorg_of_eep == RORG.MSC (0xD1)
    packet = Mock()
    packet.sender = sender
    packet.destination = [0xFF, 0x9C, 0x80, 0x80]  # Broadcast address
    packet.data = [0x00]
    packet.cmd = None
    packet.rorg = RORG.MSC
    packet.rorg_of_eep = RORG.MSC
    packet.parsed = {}

    # Mock parse_eep to populate packet.parsed
    def mock_parse_eep(rorg_func, rorg_type, direction, command):
        packet.parsed = {"test_key": {"raw_value": 123, "value": 123}}

    packet.parse_eep = Mock(side_effect=mock_parse_eep)

    # Invoke the method under test
    dongle._parse_packet_by_profile(packet)

    # Ensure parse_eep was called with the stored profile values
    packet.parse_eep.assert_called_once_with(
        rorg_func=0x07, rorg_type=0x90, direction=None, command=None
    )
    # Ensure packet.parsed was updated
    assert "test_key" in packet.parsed
