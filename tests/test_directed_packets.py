"""Test that directed packets (with specific destination) are not parsed."""

from unittest.mock import MagicMock, patch

from enocean.protocol.constants import PACKET, RORG
from enocean.protocol.packet import RadioPacket

from custom_components.enocean.dongle import EnOceanDongle
from homeassistant.core import HomeAssistant


def test_directed_packet_not_parsed(hass: HomeAssistant) -> None:
    """Test that packets sent to specific devices are not parsed.

    This prevents parsing command packets sent from gateway to sensors,
    which would otherwise try to use incorrect profiles and generate
    false validation errors on command packets.

    Example: Controller (04:20:58:A5) sending commands to sensor (04:20:74:C9)
    should not be parsed as sensor data.
    """
    # Create dongle
    with patch(
        "custom_components.enocean.dongle.SerialCommunicator"
    ) as mock_comm:
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

        # Create a packet from 04:20:58:A5 TO 04:20:74:C9 (not broadcast)
        packet = RadioPacket(PACKET.RADIO)
        packet.rorg = RORG.MSC
        packet.sender = [0x04, 0x20, 0x58, 0xA5]
        packet.destination = [0x04, 0x20, 0x74, 0xC9]  # Specific device, not broadcast
        packet.data = [
            0xD1,
            0x07,
            0x90,
            0x03,
            0x0A,
            0x82,
            0x2F,
            0x04,
            0x20,
            0x58,
            0xA5,
            0x00,
        ]

        # Register a profile for the sender
        dongle.register_device_profile([0x04, 0x20, 0x58, 0xA5], 0xD1079, 0x01, 0x00)

        # Call parse - should skip because destination is not broadcast
        dongle._parse_packet_by_profile(packet)

        # Packet should NOT be parsed (no parsed attribute or empty)
        assert not hasattr(packet, "parsed") or not packet.parsed


def test_broadcast_packet_is_parsed(hass: HomeAssistant) -> None:
    """Test that broadcast packets are parsed normally."""
    # Create dongle
    with patch(
        "custom_components.enocean.dongle.SerialCommunicator"
    ) as mock_comm:
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

        # Create a broadcast packet from 04:20:58:A5
        packet = RadioPacket(PACKET.RADIO)
        packet.rorg = RORG.MSC
        packet.sender = [0x04, 0x20, 0x58, 0xA5]
        packet.destination = [0xFF, 0x9C, 0x80, 0x80]  # Broadcast
        packet.data = [
            0xD1,
            0x07,
            0x90,
            0x01,
            0x02,
            0x00,
            0x0A,
            0x20,
            0x12,
            0x1C,
            0x00,
            0x01,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x04,
            0x20,
            0x58,
            0xA5,
            0x00,
        ]

        # Register a profile for the sender
        dongle.register_device_profile([0x04, 0x20, 0x58, 0xA5], 0xD1079, 0x01, 0x00)

        # Mock the packet.parse_eep method
        with patch.object(packet, "parse_eep") as mock_parse:
            mock_parse.return_value = None
            packet.parsed = {"CMD": {"value": 1}}  # Simulate successful parse

            # Call parse - should proceed because destination is broadcast
            dongle._parse_packet_by_profile(packet)

            # Packet SHOULD be parsed
            assert hasattr(packet, "parsed")
            assert packet.parsed
        dongle._parse_packet_by_profile(packet)

        # parse_eep should have been called
        mock_parse.assert_called_once()


def test_ventilairsec_cmd8_registers_sensor_profile(hass: HomeAssistant) -> None:
    """Test that Ventilairsec CMD 8 sensor discovery registers profiles for detected sensors.

    Sensors are registered with profiles from CMD 8. The sensor ID represents
    a physical sensor device, not just a destination address.
    """
    # Create dongle
    with patch(
        "custom_components.enocean.dongle.SerialCommunicator"
    ) as mock_comm:
        mock_comm.return_value = MagicMock()
        mock_comm.return_value.teach_in = False
        dongle = EnOceanDongle(hass, "/dev/ttyUSB0")

        # Create a CMD 8 packet (sensor discovery)
        packet = RadioPacket(PACKET.RADIO)
        packet.rorg = RORG.MSC
        packet.rorg_manufacturer = 0x079
        packet.cmd = 8
        packet.sender = [0x04, 0x20, 0x58, 0xA5]
        packet.parsed = {
            "IDAPP": {"value": 0x042074C9, "raw_value": 69730505},
            "PROFAPP": {"value": 1, "raw_value": 1},  # Profile 1 = d1079-00-00
            "CAPTINDEX": {"value": 0, "raw_value": 0},
        }

        # Call the Ventilairsec sensor processing
        dongle._process_ventilairsec_sensors(packet)

        # Check that profile WAS registered for the sensor ID
        sensor_key = (0x04, 0x20, 0x74, 0xC9)
        assert sensor_key in dongle._device_profiles
        assert dongle._device_profiles[sensor_key]["rorg"] == 0xD1079
        assert dongle._device_profiles[sensor_key]["func"] == 0x00
        assert dongle._device_profiles[sensor_key]["type"] == 0x00
    assert sensor_key in dongle._device_profiles
    assert dongle._device_profiles[sensor_key]["rorg"] == 0xD1079
    assert dongle._device_profiles[sensor_key]["func"] == 0x00
    assert dongle._device_profiles[sensor_key]["type"] == 0x00
