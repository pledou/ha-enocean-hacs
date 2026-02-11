"""Support for EnOcean number entities."""

from __future__ import annotations

from contextlib import suppress

from enocean.protocol.eep_metadata import get_field_value_with_enum

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_ENOCEAN, DOMAIN, ENOCEAN_DONGLE, LOGGER
from .entity import (
    DynamicEnoceanEntity,
    EnOceanEntity,
    async_create_entities_from_eep,
    format_device_id_hex,
)
from .types import EEPEntityDef


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EnOcean number entities."""
    enocean_data = hass.data.get(DATA_ENOCEAN, {})
    dongle = enocean_data.get(ENOCEAN_DONGLE)

    if not dongle:
        return

    entities = [
        EnOceanLearningDurationNumber(dongle),
    ]

    async_add_entities(entities)

    # Register callback for EEP-discovered number entities using shared factory
    async def _add_numbers_from_eep(
        device_id, entities_list, rorg, rorg_func, rorg_type
    ):
        """Add number entities for a discovered device from EEP profile."""
        if not entities_list:
            return

        await async_create_entities_from_eep(
            hass,
            config_entry,
            device_id,
            entities_list,
            rorg,
            rorg_func,
            rorg_type,
            platform_type="number",
            entity_class=DynamicEnOceanNumber,
            async_add_entities=async_add_entities,
        )

    # Register the callback in the platform callbacks registry
    platform_callbacks = enocean_data.get("platform_callbacks", {})
    platform_callbacks["number"] = _add_numbers_from_eep


class EnOceanNumber(RestoreNumber, EnOceanEntity):
    """Representation of an EnOcean number entity from EEP."""

    def __init__(
        self,
        dev_id: list[int],
        dev_name: str,
        data_field: str,
        min_value: float | None = None,
        max_value: float | None = None,
        unit: str | None = None,
        attr_name: str | None = None,
        dev_class: str | None = None,
        fields: EEPEntityDef | None = None,
    ) -> None:
        """Initialize the EnOcean number entity."""
        EnOceanEntity.__init__(
            self,
            dev_id=dev_id,
            data_field=data_field or "value",
            attr_name=attr_name,
            dev_name=dev_name,
            dev_class=dev_class,
            fields=fields,
        )
        if min_value is not None:
            self._attr_native_min_value = min_value
        if max_value is not None:
            self._attr_native_max_value = max_value
        self._attr_native_unit_of_measurement = unit

    def value_changed(self, packet) -> None:  # optional: allow subclass override
        """Hook for subclasses to process incoming packets."""
        return


class DynamicEnOceanNumber(DynamicEnoceanEntity, EnOceanNumber):
    """Dynamic number that uses EEP parser/fields when available."""

    def __init__(
        self,
        dev_id: list[int],
        dev_name: str,
        rorg: int,
        rorg_func: int,
        rorg_type: int,
        data_field: str,
        dev_class: str | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        unit: str | None = None,
        fields: EEPEntityDef | None = None,
        attr_name: str | None = None,
    ) -> None:
        """Initialize the dynamic EnOcean number and store parser parameters for lazy initialization."""
        # Initialize shared dynamic behaviour
        EnOceanNumber.__init__(
            self,
            dev_id=dev_id,
            dev_name=dev_name,
            data_field=data_field,
            attr_name=attr_name,
            dev_class=dev_class,
            fields=fields,
        )
        DynamicEnoceanEntity.__init__(
            self,
            dev_id=dev_id,
            data_field=data_field or "number",
            rorg=rorg,
            rorg_func=rorg_func,
            rorg_type=rorg_type,
            dev_name=dev_name,
            fields=fields,
            dev_class=dev_class,
            attr_name=attr_name,
        )
        # Set number-specific attributes
        # Extract from provided fields metadata when available
        extracted_min = None
        extracted_max = None
        extracted_unit = None
        extracted_command_template = None
        extracted_mode = None

        if fields is not None and isinstance(fields, EEPEntityDef):
            extracted_min = fields.min_value
            extracted_max = fields.max_value
            extracted_unit = fields.unit
            extracted_command_template = fields.command_template
            extracted_mode = fields.mode

            # Apply number-specific device_class if available
            if fields.device_class:
                self._attr_device_class = fields.device_class  # type: ignore[assignment]

        # Use provided min/max/unit, fall back to extracted values, then None
        if min_value is not None:
            self._attr_native_min_value = min_value
        elif extracted_min is not None:
            self._attr_native_min_value = extracted_min

        if max_value is not None:
            self._attr_native_max_value = max_value
        elif extracted_max is not None:
            self._attr_native_max_value = extracted_max

        # Only assign unit if a non-None value is available to avoid
        # assigning `None` to attributes that expect `str`.
        if unit is not None:
            self._attr_native_unit_of_measurement = unit
        elif extracted_unit is not None:
            self._attr_native_unit_of_measurement = extracted_unit

        # Apply mode if available from fields
        if extracted_mode:
            self._attr_mode = extracted_mode  # type: ignore[assignment]

        # Store command template for sending values to device if present
        self._command_template = extracted_command_template

    async def async_set_native_value(self, value: float) -> None:
        """Set new value and send command to device if template available."""
        if self._command_template:
            # Send command using the template
            await self.hass.async_add_executor_job(
                self._send_message,
                self._command_template,
                {
                    "value": value,
                    "device_id": self.dev_id,
                    "data_field": self._data_field,
                },
                self._rorg,
                self._rorg_func,
                self._rorg_type,
            )

            # Update local state
            self._attr_native_value = value
            self.async_write_ha_state()
        else:
            # Provide richer context to help debug why sending is skipped
            has_fields = self._fields is not None
            raw_fields_info = getattr(self._fields, "raw_fields", None)
            with suppress(Exception):
                LOGGER.debug(
                    "No command_template configured for %s (device=%s). Cannot send value. rorg=0x%02x, func=0x%02x, type=0x%02x, data_field=%s, has_fields=%s, raw_fields=%s",
                    self._attr_unique_id,
                    format_device_id_hex(self.dev_id),
                    self._rorg or 0,
                    self._rorg_func or 0,
                    self._rorg_type or 0,
                    self._data_field,
                    has_fields,
                    bool(raw_fields_info),
                )

    @callback
    def value_changed(self, packet) -> None:
        """Update numeric value from parsed packet when available."""
        if not packet.data or len(packet.data) < 2:
            return

        # Packet should already be parsed by dongle callback
        if not packet.parsed or not self._data_field:
            return

        # Use the original EEP fields mapping (dict) for enum resolution when
        # possible. If an EEPEntityDef dataclass was provided, it may include
        # the raw mapping on `raw_fields`.
        fields_mapping = None
        if isinstance(self._fields, dict):
            fields_mapping = self._fields
        else:
            fields_mapping = getattr(self._fields, "raw_fields", None)

        if fields_mapping and get_field_value_with_enum is not None:
            value = get_field_value_with_enum(
                packet.parsed, self._data_field, fields_mapping
            )
        else:
            value = self._get_parsed_value(packet, self._data_field)

        if value is not None:
            try:
                self._attr_native_value = float(value)
                self.async_write_ha_state()
            except (TypeError, ValueError):
                pass


class EnOceanLearningDurationNumber(RestoreNumber):
    """Representation of the EnOcean learning mode duration number."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:timer-settings"
    _attr_name = "Learning duration"
    _attr_native_min_value = 1
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "minutes"

    def __init__(self, dongle) -> None:
        """Initialize the learning duration number."""
        self._dongle = dongle
        super().__init__()
        self._attr_unique_id = f"{dongle.identifier}-learning-duration"
        self._attr_native_value = dongle.learning_duration

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for the dongle."""
        return {
            "identifiers": {(DOMAIN, self._dongle.identifier)},
            "name": f"EnOcean Dongle ({self._dongle.identifier})",
            "manufacturer": "EnOcean",
        }

    async def async_added_to_hass(self) -> None:
        """Restore the last known state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in ("unknown", "unavailable"):
                try:
                    self._attr_native_value = int(float(last_state.state))
                    self._dongle.learning_duration = self._attr_native_value
                except (ValueError, TypeError):
                    pass

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = int(value)
        self._dongle.learning_duration = int(value)
        self.async_write_ha_state()
