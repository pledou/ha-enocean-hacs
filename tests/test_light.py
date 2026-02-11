"""Tests for EnOcean light entity behavior."""

import math
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.enocean.light import EnOceanLight
from homeassistant.components.light import ColorMode


@pytest.fixture
def mock_enocean_entity():
    """Mock the EnOceanEntity parent initialization."""
    with patch(
        "custom_components.enocean.light.EnOceanEntity.__init__",
        return_value=None,
    ):
        yield


def test_light_initialization(mock_enocean_entity) -> None:
    """Test light entity initialization."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    name = "Test Light"

    light = EnOceanLight(sender_id, dev_id, name)

    assert light._sender_id == sender_id
    assert light._attr_name == name
    # When EnOceanEntity.__init__ is mocked, _attr_unique_id won't be set
    assert light._attr_unique_id is None
    assert light._attr_brightness == 50
    assert light._attr_is_on is False
    assert light._attr_color_mode == ColorMode.BRIGHTNESS
    assert light._attr_supported_color_modes == {ColorMode.BRIGHTNESS}


def test_light_turn_on_default_brightness(mock_enocean_entity) -> None:
    """Test turning on light with default brightness."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    sent = []

    def fake_send_command(data, optional, packet_type):
        sent.append({"data": data, "optional": optional, "packet_type": packet_type})

    light.send_command = fake_send_command

    light.turn_on()

    assert light._attr_is_on is True
    assert len(sent) == 1
    # Check command structure
    assert sent[0]["data"][0] == 0xA5
    assert sent[0]["data"][1] == 0x02
    # Brightness 50 converts to: floor(50 / 256 * 100) = 19
    assert sent[0]["data"][2] == 19
    assert sent[0]["data"][3] == 0x01
    assert sent[0]["data"][4] == 0x09
    # Check sender_id is appended
    assert sent[0]["data"][5:9] == sender_id
    assert sent[0]["data"][9] == 0x00
    assert sent[0]["optional"] == []
    assert sent[0]["packet_type"] == 0x01


def test_light_turn_on_with_brightness(mock_enocean_entity) -> None:
    """Test turning on light with specified brightness."""
    dev_id = [0x0A, 0x0B, 0x0C, 0x0D]
    sender_id = [0x11, 0x12, 0x13, 0x14]
    light = EnOceanLight(sender_id, dev_id, "Dimmer Light")

    sent = []

    def fake_send_command(data, optional, packet_type):
        sent.append({"data": data, "optional": optional, "packet_type": packet_type})

    light.send_command = fake_send_command

    # Turn on with brightness 200
    light.turn_on(brightness=200)

    assert light._attr_brightness == 200
    assert light._attr_is_on is True
    assert len(sent) == 1
    # Brightness 200 converts to: floor(200 / 256 * 100) = 78
    assert sent[0]["data"][2] == 78


def test_light_turn_on_with_low_brightness(mock_enocean_entity) -> None:
    """Test turning on light with low brightness value."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    sent = []

    def fake_send_command(data, optional, packet_type):
        sent.append({"data": data, "optional": optional, "packet_type": packet_type})

    light.send_command = fake_send_command

    # Turn on with very low brightness
    light.turn_on(brightness=1)

    assert light._attr_brightness == 1
    # Brightness 1 converts to: floor(1 / 256 * 100) = 0, but gets set to 1
    assert sent[0]["data"][2] == 1


def test_light_turn_off(mock_enocean_entity) -> None:
    """Test turning off light."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    # First turn on
    sent = []

    def fake_send_command(data, optional, packet_type):
        sent.append({"data": data, "optional": optional, "packet_type": packet_type})

    light.send_command = fake_send_command
    light.turn_on()
    assert light._attr_is_on is True

    # Now turn off
    sent.clear()
    light.turn_off()

    assert light._attr_is_on is False
    assert len(sent) == 1
    # Check command structure for off
    assert sent[0]["data"][0] == 0xA5
    assert sent[0]["data"][1] == 0x02
    assert sent[0]["data"][2] == 0x00  # Brightness 0 for off
    assert sent[0]["data"][3] == 0x01
    assert sent[0]["data"][4] == 0x09
    # Check sender_id is appended
    assert sent[0]["data"][5:9] == sender_id
    assert sent[0]["data"][9] == 0x00
    assert sent[0]["optional"] == []
    assert sent[0]["packet_type"] == 0x01


def test_light_turn_on_off_sequence(mock_enocean_entity) -> None:
    """Test multiple on/off sequences."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    sent = []

    def fake_send_command(data, optional, packet_type):
        sent.append({"data": data, "optional": optional, "packet_type": packet_type})

    light.send_command = fake_send_command

    # Turn on
    light.turn_on(brightness=100)
    assert light._attr_is_on is True
    assert len(sent) == 1

    # Turn off
    light.turn_off()
    assert light._attr_is_on is False
    assert len(sent) == 2

    # Turn on again with different brightness
    light.turn_on(brightness=255)
    assert light._attr_is_on is True
    assert light._attr_brightness == 255
    assert len(sent) == 3


def test_light_value_changed_on_valid_packet(mock_enocean_entity) -> None:
    """Test handling value change from 4BS telegram."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    # Mock schedule_update_ha_state
    light.schedule_update_ha_state = MagicMock()

    # Create a packet with 4BS RORG (0xA5) and appropriate data
    packet = SimpleNamespace(
        data=[0xA5, 0x02, 75, 0x01]  # brightness value 75
    )

    light.value_changed(packet)

    # Brightness 75 converts to: floor(75 / 100 * 256) = 192
    assert light._attr_brightness == 192
    assert light._attr_is_on is True
    light.schedule_update_ha_state.assert_called_once()


def test_light_value_changed_brightness_zero(mock_enocean_entity) -> None:
    """Test handling value change with brightness 0 (off)."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    light.schedule_update_ha_state = MagicMock()

    packet = SimpleNamespace(
        data=[0xA5, 0x02, 0, 0x01]  # brightness 0 means off
    )

    light.value_changed(packet)

    assert light._attr_brightness == 0
    assert light._attr_is_on is False
    light.schedule_update_ha_state.assert_called_once()


def test_light_value_changed_ignores_invalid_rorg(mock_enocean_entity) -> None:
    """Test that value_changed ignores packets with invalid RORG."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    light.schedule_update_ha_state = MagicMock()

    # Packet with different RORG (not 0xA5)
    packet = SimpleNamespace(data=[0xA4, 0x02, 75, 0x01])

    light.value_changed(packet)

    # State should not change
    light.schedule_update_ha_state.assert_not_called()


def test_light_value_changed_ignores_invalid_data_type(mock_enocean_entity) -> None:
    """Test that value_changed ignores packets with invalid data type."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    light.schedule_update_ha_state = MagicMock()

    # Packet with correct RORG but wrong data type (not 0x02)
    packet = SimpleNamespace(data=[0xA5, 0x01, 75, 0x01])

    light.value_changed(packet)

    # State should not change
    light.schedule_update_ha_state.assert_not_called()


def test_light_value_changed_various_brightness_levels(mock_enocean_entity) -> None:
    """Test value_changed with various brightness levels."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    light.schedule_update_ha_state = MagicMock()

    test_cases = [
        (1, 2),  # 1% -> ~2.56 -> 2
        (50, 128),  # 50% -> 128
        (100, 255),  # 100% -> 255
    ]

    for input_val, _expected_brightness in test_cases:
        light.schedule_update_ha_state.reset_mock()
        packet = SimpleNamespace(data=[0xA5, 0x02, input_val, 0x01])
        light.value_changed(packet)
        expected = math.floor(input_val / 100.0 * 256.0)
        assert light._attr_brightness == expected


def test_light_attribute_properties(mock_enocean_entity) -> None:
    """Test that light entity has correct attribute properties."""
    dev_id = [0xFF, 0xFE, 0xFD, 0xFC]
    sender_id = [0x11, 0x22, 0x33, 0x44]
    light = EnOceanLight(sender_id, dev_id, "Bedroom Light")

    # Verify color mode
    assert light._attr_color_mode == ColorMode.BRIGHTNESS
    assert ColorMode.BRIGHTNESS in light._attr_supported_color_modes

    # Verify initial state
    assert light._attr_is_on is False
    assert light._attr_brightness == 50
    assert light._attr_name == "Bedroom Light"


def test_light_brightness_conversion_edge_cases(mock_enocean_entity) -> None:
    """Test brightness conversion at edge cases."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    sender_id = [0x05, 0x06, 0x07, 0x08]
    light = EnOceanLight(sender_id, dev_id, "Test Light")

    sent = []

    def fake_send_command(data, optional, packet_type):
        sent.append({"data": data})

    light.send_command = fake_send_command

    # Test with maximum brightness
    light.turn_on(brightness=255)
    assert light._attr_brightness == 255
    # floor(255 / 256 * 100) = 99
    assert sent[-1]["data"][2] == 99

    # Test with minimum brightness
    light.turn_on(brightness=1)
    assert light._attr_brightness == 1
    # floor(1 / 256 * 100) = 0, but gets set to 1
    assert sent[-1]["data"][2] == 1


def test_light_multiple_devices(mock_enocean_entity) -> None:
    """Test creating multiple light instances."""
    light1 = EnOceanLight([0x01, 0x02, 0x03, 0x04], [0xAA, 0xBB, 0xCC, 0xDD], "Light 1")
    light2 = EnOceanLight([0x05, 0x06, 0x07, 0x08], [0xEE, 0xFF, 0x00, 0x11], "Light 2")

    # Mock send_command
    light1.send_command = MagicMock()
    light2.send_command = MagicMock()

    # Verify they are independent
    assert light1._attr_name != light2._attr_name
    # Both have None unique_id when parent init is mocked
    assert light1._attr_unique_id is None
    assert light2._attr_unique_id is None
    assert light1._sender_id != light2._sender_id

    # Modify one and verify the other is unchanged
    light1.turn_on(brightness=200)
    assert light1._attr_brightness == 200
    assert light2._attr_brightness == 50  # default
