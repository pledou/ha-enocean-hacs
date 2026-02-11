"""Test out-of-range value validation for EnOcean entities."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.enocean.dongle import EnOceanDongle
from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_packet_valid():
    """Create a mock packet with valid data."""
    packet = MagicMock()
    packet.sender = [0x04, 0x20, 0x58, 0xA5]
    packet.destination = [0xFF, 0x9C, 0x80, 0x80]
    packet.dBm = -77
    packet.packet_type = 0x01
    packet.data = [0xD1, 0x07, 0x90, 0x01, 0x02, 0x00, 0x04, 0x20, 0x1C, 0x1C, 0x00]
    packet.optional = [0x01, 0xFF, 0x9C, 0x80, 0x80, 0x4D, 0x00]
    packet.parsed = {
        "CMD": {"value": 0, "raw_value": 0, "out_of_range": False},
        "TEMPCELEC": {"value": 4.0, "raw_value": 4, "out_of_range": False},
        "TEMPMSOUFFL": {"value": 32.0, "raw_value": 32, "out_of_range": False},
        "TEMPCHYDROR": {"value": 28.0, "raw_value": 28, "out_of_range": False},
    }
    return packet


@pytest.fixture
def mock_packet_invalid():
    """Create a mock packet with out-of-range data."""
    packet = MagicMock()
    packet.sender = [0x04, 0x20, 0x58, 0xA5]
    packet.destination = [0x04, 0x20, 0x74, 0xC9]
    packet.dBm = -89
    packet.packet_type = 0x01
    packet.data = [0xD1, 0x07, 0x90, 0x04, 0x00, 0x82, 0x2F, 0x04, 0x20, 0x58, 0xA5]
    packet.optional = [0x01, 0x04, 0x20, 0x74, 0xC9, 0x59, 0x00]
    packet.parsed = {
        "CMD": {"value": 4, "raw_value": 4, "out_of_range": False},
        "TEMPCELEC": {
            "value": 47.0,
            "raw_value": 47,
            "out_of_range": True,
        },  # Out of range [0-18]
        "TEMPMSOUFFL": {
            "value": 4.0,
            "raw_value": 4,
            "out_of_range": True,
        },  # Out of range [20-45]
        "TEMPCHYDROR": {
            "value": 32.0,
            "raw_value": 32,
            "out_of_range": True,
        },  # Out of range [8-28]
    }
    return packet


async def test_valid_packet_accepted(
    hass: HomeAssistant, mock_packet_valid, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that valid packets are accepted and processed."""
    with (
        patch(
            "custom_components.enocean.dongle.SerialCommunicator"
        ) as mock_comm,
    ):
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

    # Should validate the packet
    assert dongle._validate_and_track_packet(mock_packet_valid) is True
    assert "out-of-range" not in caplog.text.lower()


async def test_invalid_packet_rejected(
    hass: HomeAssistant, mock_packet_invalid, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that packets with out-of-range values are rejected and logged."""
    with (
        patch(
            "custom_components.enocean.dongle.SerialCommunicator"
        ) as mock_comm,
    ):
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

    # Should NOT validate the packet
    assert dongle._validate_and_track_packet(mock_packet_invalid) is False

    # Should log a warning
    assert "out-of-range" in caplog.text.lower()
    assert "04:20:58:a5" in caplog.text.lower()


async def test_out_of_range_detection(hass: HomeAssistant, mock_packet_invalid) -> None:
    """Test that _has_out_of_range_fields correctly detects invalid fields."""
    with (
        patch(
            "custom_components.enocean.dongle.SerialCommunicator"
        ) as mock_comm,
    ):
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

    # Should detect out-of-range fields
    assert dongle._has_out_of_range_fields(mock_packet_invalid) is True


async def test_no_out_of_range_detection(
    hass: HomeAssistant, mock_packet_valid
) -> None:
    """Test that _has_out_of_range_fields returns False for valid packets."""
    with (
        patch(
            "custom_components.enocean.dongle.SerialCommunicator"
        ) as mock_comm,
    ):
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

    # Should NOT detect out-of-range fields
    assert dongle._has_out_of_range_fields(mock_packet_valid) is False
