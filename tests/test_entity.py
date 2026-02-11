"""Unit tests for custom_components.enocean.entity module."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.enocean import entity as eno_entity
from homeassistant.core import HomeAssistant


def test_format_helpers() -> None:
    """Test formatting helper functions."""
    assert eno_entity.format_device_id_hex([0x01, 0x02, 0x0A, 0xFF]) == "01:02:0a:ff"
    assert (
        eno_entity.format_device_id_hex_underscore([0x01, 0x02, 0x0A, 0xFF])
        == "01_02_0a_ff"
    )


def test_message_received_callback_calls_value_changed() -> None:
    """Test that message received callback invokes value_changed."""

    class TestEntity(eno_entity.EnOceanEntity):
        """Test entity class."""

        def __init__(self) -> None:
            """Initialize test entity."""
            super().__init__([0x01, 0x02, 0x03, 0x04], data_field="field")
            self.called = False

        def value_changed(self, _packet) -> None:
            """Record that value changed was called."""
            self.called = True

    e = TestEntity()
    # Create a fake packet with matching sender
    pkt = SimpleNamespace(sender=[0x01, 0x02, 0x03, 0x04])

    e._message_received_callback(pkt)
    assert e.called


def test_message_received_callback_ignores_other_senders() -> None:
    """Test that message callback ignores packets from other senders."""

    class TestEntity(eno_entity.EnOceanEntity):
        """Test entity class."""

        def __init__(self) -> None:
            """Initialize test entity."""
            super().__init__([0x01, 0x02, 0x03, 0x04], data_field="field")
            self.called = False

        def value_changed(self, _packet) -> None:
            """Record that value changed was called."""
            self.called = True

    e = TestEntity()
    pkt = SimpleNamespace(sender=[0xDE, 0xAD, 0xBE, 0xEF])
    e._message_received_callback(pkt)
    assert not e.called


def test_send_command_dispatches_packet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that send_command dispatches a packet."""
    sent = []

    class FakePacket:
        def __init__(self, packet_type, data=None, optional=None) -> None:
            self.packet_type = packet_type
            self.data = data
            self.optional = optional

    def fake_dispatcher_send(hass: HomeAssistant, signal, packet) -> None:
        sent.append((hass, signal, packet))

    monkeypatch.setattr(eno_entity, "Packet", FakePacket)
    monkeypatch.setattr(eno_entity, "dispatcher_send", fake_dispatcher_send)

    e = eno_entity.EnOceanEntity([0x01, 0x02, 0x03, 0x04], data_field="f")
    # hass can be any object; dispatcher_send receives it and we capture it
    e.hass = "hass-instance"
    e.send_command([1, 2, 3], [4, 5], 0x01)

    assert len(sent) == 1
    hass_arg, signal_arg, pkt = sent[0]
    assert hass_arg == "hass-instance"
    assert signal_arg is not None  # Signal should be present
    assert pkt.packet_type == 0x01
    assert pkt.data == [1, 2, 3]
