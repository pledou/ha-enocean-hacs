"""Tests for EnOcean options/runtime_data loading on setup."""

from unittest.mock import patch

from custom_components.enocean.const import DATA_ENOCEAN, DOMAIN, ENOCEAN_DONGLE
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry


class DummySerialCommunicator:
    """Minimal dummy SerialCommunicator for tests.

    Provides just enough interface for the EnOcean integration to
    initialize without accessing real hardware.
    """

    def __init__(self, port, callback) -> None:
        """Initialize the dummy communicator.

        Args:
            port: Serial port path (ignored)
            callback: Packet callback (ignored)
        """
        # mimic minimal attributes used by the integration
        self.port = port
        self.callback = callback
        self.teach_in = False
        self.automatic_answer = False
        self.base_id = b"\x01\x02\x03\x04"

    def start(self) -> None:
        """Start the communicator (no-op)."""

    def send(self, command) -> None:
        """Send a command (no-op)."""


async def test_config_entry_initializes_runtime_data_and_dongle(
    hass: HomeAssistant,
) -> None:
    """Config entry setup should initialize runtime_data and create dongle."""

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_DEVICE: "/dev/ttyUSB0"})
    entry.add_to_hass(hass)

    # Patch SerialCommunicator to avoid touching real hardware
    with patch(
        "custom_components.enocean.dongle.SerialCommunicator",
        DummySerialCommunicator,
    ):
        # Perform config entry setup
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # runtime_data should be initialized on the config entry
    assert hasattr(entry, "runtime_data")
    assert isinstance(entry.runtime_data, dict)

    # The dongle instance should be stored in hass.data under DATA_ENOCEAN
    enocean_data = hass.data.get(DATA_ENOCEAN)
    assert enocean_data is not None
    assert ENOCEAN_DONGLE in enocean_data
