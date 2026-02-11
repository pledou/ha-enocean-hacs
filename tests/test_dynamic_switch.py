"""Tests for DynamicEnOceanSwitch parsing behavior."""

from custom_components.enocean.switch import DynamicEnOceanSwitch


class DummyPacket:
    """Dummy packet for testing."""

    def __init__(self, data) -> None:
        """Initialize the dummy packet."""
        self.data = data
        self.parsed = {
            "IO": {"raw_value": 3},
            "OV": {"raw_value": 1},
            "CMD": {"raw_value": 4},
        }

    def parse_eep(self, func, rorg_type):
        """Mock parse_eep method."""


def test_dynamic_switch_updates_state_from_parsed_dicts() -> None:
    """Test that dynamic switch updates state from parsed dict values."""
    # Create dynamic switch that listens on channel 3
    dev_id = [0x05, 0x06, 0x07, 0x08]
    sw = DynamicEnOceanSwitch(
        dev_id,
        rorg=0xD2,
        rorg_func=0x01,
        rorg_type=0x00,
        data_field="switch",
        dev_name="dev",
        channel=3,
    )

    # Monkeypatch the parser to return dict-style parsed values
    def fake_parse(packet):
        return {"IO": {"raw_value": 3}, "OV": {"raw_value": 1}}

    sw._parse_packet = fake_parse  # type: ignore[attr-defined]
    # Mock schedule_update_ha_state to avoid needing hass instance
    sw.schedule_update_ha_state = lambda: None  # type: ignore[assignment]

    pkt = DummyPacket([0xD2, 0x01])
    sw.value_changed(pkt)
    assert sw._attr_is_on is True


def test_dynamic_switch_ignores_mismatch_channel() -> None:
    """Test that dynamic switch ignores mismatched channel in parsed values."""
    dev_id = [0x05, 0x06, 0x07, 0x08]
    sw = DynamicEnOceanSwitch(
        dev_id,
        rorg=0xD2,
        rorg_func=0x01,
        rorg_type=0x00,
        data_field="switch",
        dev_name="dev",
        channel=2,
    )

    def fake_parse(packet):
        return {"IO": {"raw_value": 3}, "OV": {"raw_value": 1}}

    sw._parse_packet = fake_parse  # type: ignore[attr-defined]

    pkt = DummyPacket([0xD2, 0x01])
    sw.value_changed(pkt)
    # channel 3 does not match configured channel 2 -> no change
    assert sw._attr_is_on is False
