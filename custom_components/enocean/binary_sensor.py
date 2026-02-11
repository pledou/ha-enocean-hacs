"""Support for EnOcean binary sensors."""

from __future__ import annotations

import contextlib
import logging
import struct

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as BINARY_SENSOR_PLATFORM_SCHEMA,
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_CLASS, CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ENOCEAN, LOGGER
from .eep_devices import EEPEntityDef
from .entity import DynamicEnoceanEntity, EnOceanEntity, async_create_entities_from_eep

_LOGGER = logging.getLogger(__name__)


DEFAULT_NAME = "EnOcean binary sensor"
DEPENDENCIES = ["enocean"]
EVENT_BUTTON_PRESSED = "button_pressed"

PLATFORM_SCHEMA = BINARY_SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EnOcean binary sensor entities."""
    enocean_data = hass.data.get(DATA_ENOCEAN, {})
    entities: list[BinarySensorEntity] = []

    # Device-specific binary sensors are created dynamically from discovery
    # events.

    if entities:
        async_add_entities(entities)

    # Register callback for EEP-discovered entities
    async def _add_binary_from_eep(
        device_id: list[int],
        entities_list: list[EEPEntityDef],
        rorg: int,
        rorg_func: int,
        rorg_type: int,
    ):
        """Add binary sensor entities for a discovered device from EEP profile."""

        await async_create_entities_from_eep(
            hass,
            config_entry,
            device_id,
            entities_list,
            rorg,
            rorg_func,
            rorg_type,
            platform_type="binary_sensor",
            entity_class=DynamicEnOceanBinarySensor,
            async_add_entities=async_add_entities,
            entity_kwargs_factory=None,
        )

    # Register the callback in the platform callbacks registry
    platform_callbacks = enocean_data.get("platform_callbacks", {})
    platform_callbacks["binary_sensor"] = _add_binary_from_eep


class EnOceanBinarySensor(EnOceanEntity, BinarySensorEntity):
    """Representation of an EnOcean binary sensor device.

    EEPs (EnOcean Equipment Profiles):
    - F6-02-01 (Light and Blind Control - Application Style 2)
    - F6-02-02 (Light and Blind Control - Application Style 1)
    """

    def __init__(
        self,
        dev_id: list[int],
        dev_name: str,
        data_field: str,
        device_class: BinarySensorDeviceClass | None,
        entity_name: str | None = None,
    ) -> None:
        """Initialize the EnOcean binary sensor."""
        BinarySensorEntity.__init__(self)
        EnOceanEntity.__init__(
            self,
            dev_id=dev_id,
            data_field=data_field,
            attr_name=entity_name,
            dev_name=dev_name,
        )
        self._attr_device_class = device_class
        self.which = -1
        self.onoff = -1

    @callback
    def value_changed(self, packet):
        """Fire an event with the data that have changed.

        This method is called when there is an incoming packet associated
        with this platform.

        Example packet data:
        - 2nd button pressed
            ['0xf6', '0x10', '0x00', '0x2d', '0xcf', '0x45', '0x30']
        - button released
            ['0xf6', '0x00', '0x00', '0x2d', '0xcf', '0x45', '0x20']
        """
        # Energy Bow
        pushed = None

        if packet.data[6] == 0x30:
            pushed = 1
        elif packet.data[6] == 0x20:
            pushed = 0

        self.schedule_update_ha_state()

        action = packet.data[1]
        if action == 0x70:
            self.which = 0
            self.onoff = 0
        elif action == 0x50:
            self.which = 0
            self.onoff = 1
        elif action == 0x30:
            self.which = 1
            self.onoff = 0
        elif action == 0x10:
            self.which = 1
            self.onoff = 1
        elif action == 0x37:
            self.which = 10
            self.onoff = 0
        elif action == 0x15:
            self.which = 10
            self.onoff = 1
        self.hass.bus.fire(
            EVENT_BUTTON_PRESSED,
            {
                "id": self.dev_id,
                "pushed": pushed,
                "which": self.which,
                "onoff": self.onoff,
            },
        )


class DynamicEnOceanBinarySensor(DynamicEnoceanEntity, BinarySensorEntity):
    """Generic dynamic binary sensor that parses EEP profiles using Parser.

    This binary sensor can be configured per-instance with explicit EEP
    identifiers (rorg/func/type) and an optional fields mapping.
    """

    def __init__(
        self,
        dev_id: list[int],
        dev_name: str,
        rorg: int,
        rorg_func: int,
        rorg_type: int,
        data_field: str,
        device_class: BinarySensorDeviceClass | None = None,
        fields: EEPEntityDef | None = None,
        attr_name: str | None = None,
    ) -> None:
        """Initialize the dynamic EnOcean binary sensor."""
        # Initialize shared dynamic behaviour then set device-specific attrs
        DynamicEnoceanEntity.__init__(
            self,
            dev_id=dev_id,
            dev_name=dev_name,
            data_field=data_field,
            rorg=rorg,
            rorg_func=rorg_func,
            rorg_type=rorg_type,
            fields=fields,
            attr_name=attr_name,
        )
        BinarySensorEntity.__init__(self)
        # Normalize device class enum
        if isinstance(device_class, str):
            try:
                device_class_enum = BinarySensorDeviceClass(device_class)
            except ValueError:
                device_class_enum = None
        else:
            device_class_enum = device_class
        self._attr_device_class = device_class_enum

        # Apply binary sensor specific device_class from EEPEntityDef if available
        if (
            fields is not None
            and isinstance(fields, EEPEntityDef)
            and fields.device_class
        ):
            with contextlib.suppress(ValueError):
                self._attr_device_class = BinarySensorDeviceClass(fields.device_class)

    @callback
    def value_changed(self, packet) -> None:
        """Update the internal state when a packet arrives."""
        try:
            # Packet should already be parsed by dongle callback
            if not packet.parsed or not self._data_field:
                return
            value = self._get_parsed_value(packet, self._data_field)

            if value is not None:
                # Convert to boolean
                try:
                    self._attr_is_on = bool(value)
                except (TypeError, ValueError):
                    self._attr_is_on = bool(int(value))
            else:
                self._attr_is_on = False

                self.schedule_update_ha_state()
        except (ValueError, TypeError, KeyError, OSError, struct.error) as err:
            LOGGER.error(
                "Error parsing dynamic binary sensor packet for %s: %s",
                self._attr_name,
                err,
            )
