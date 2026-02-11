"""Support for EnOcean select entities derived from EEP enums.

Select entities are created dynamically from discovery using EEP enum
definitions. The dispatcher receives (device_id, entities) where `entities`
are `EEPEntityDef`-like objects produced by the EEP loader.
"""

from __future__ import annotations

from typing import Any

from enocean.protocol.eep_metadata import get_field_value_with_enum

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_ENOCEAN, LOGGER
from .entity import DynamicEnoceanEntity, EnOceanEntity, async_create_entities_from_eep
from .types import EEPEntityDef


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EnOcean select entities."""
    enocean_data = hass.data.get(DATA_ENOCEAN, {})
    # Selects are created dynamically from discovery events

    async def _add_selects_from_eep(device_id, entities_list, rorg, func, type_):
        """Add select entities for a discovered device from EEP profile."""
        await async_create_entities_from_eep(
            hass,
            config_entry,
            device_id,
            entities_list,
            rorg,
            func,
            type_,
            platform_type="select",
            entity_class=DynamicEnOceanSelect,
            async_add_entities=async_add_entities,
        )

    # Register the callback in the platform callbacks registry
    platform_callbacks = enocean_data.get("platform_callbacks", {})
    platform_callbacks["select"] = _add_selects_from_eep


class EnOceanSelect(EnOceanEntity, SelectEntity):
    """Representation of an EnOcean select entity (EEP enum)."""

    def __init__(
        self,
        dev_id: list[int],
        dev_name: str,
        data_field: str,
        options: list[str] | None = None,
        entity_name: str | None = None,
        attr_name: str | None = None,
        fields: EEPEntityDef | None = None,
    ) -> None:
        """Initialize the select entity."""
        EnOceanEntity.__init__(
            self,
            dev_id,
            data_field=data_field or dev_name,
            dev_name=dev_name,
            dev_class=None,
            attr_name=attr_name or entity_name,
            fields=fields,
        )
        SelectEntity.__init__(self)
        self._data_field: str = data_field or dev_name
        self._attr_options = options or []
        self._current_option: str | None = None

    @property
    def current_option(self) -> str | None:
        """Return currently selected option."""
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Select an option.

        NOTE: This implementation only updates local state. Sending the
        selection back to the device requires composing and sending the
        appropriate EEP command; that can be implemented later when a
        command mapping is available.
        """
        if option not in self._attr_options:
            return
        self._current_option = option
        self.async_write_ha_state()

    @callback
    def value_changed(self, packet: Any) -> None:
        """Update current option based on incoming packet.

        Try to pick a meaningful value from `packet.parsed` when available.
        """
        # If packet provides parsed values, try to extract the field
        parsed = getattr(packet, "parsed", None)
        if parsed and self._data_field:
            try:
                entry = parsed.get(self._data_field)
                if isinstance(entry, dict):
                    raw = (
                        entry.get("raw_value") or entry.get("value") or entry.get("raw")
                    )
                else:
                    raw = entry

                # Match raw value to options by description or numeric value
                if raw is not None:
                    raw_str = str(raw)
                    for opt in self._attr_options:
                        if opt == raw_str or opt.lower() == raw_str.lower():
                            self._current_option = opt
                            self.schedule_update_ha_state()
                            return
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                LOGGER.debug(
                    "Failed to map packet to select option for %s: error: %s",
                    self._attr_unique_id,
                    err,
                )


class DynamicEnOceanSelect(DynamicEnoceanEntity, EnOceanSelect):
    """Generic dynamic select that parses EEP enums using Parser.

    This select can be configured per-instance with explicit EEP
    identifiers (rorg/func/type) and an optional fields mapping.
    """

    def __init__(
        self,
        dev_id: list[int],
        rorg: int,
        rorg_func: int,
        rorg_type: int,
        dev_name: str,
        data_field: str,
        device_class: str | None = None,
        fields: EEPEntityDef | None = None,
        enum_options: list[str] | None = None,
        attr_name: str | None = None,
    ) -> None:
        """Initialize the dynamic select entity."""
        # Initialize shared dynamic behaviour then set device-specific attrs
        options = enum_options or []

        DynamicEnoceanEntity.__init__(
            self,
            dev_id,
            dev_name=dev_name,
            data_field=data_field,
            rorg=rorg,
            rorg_func=rorg_func,
            rorg_type=rorg_type,
            dev_class=device_class,
            fields=fields,
            attr_name=attr_name,
        )
        EnOceanSelect.__init__(
            self,
            dev_id,
            dev_name=dev_name,
            data_field=data_field,
            options=options,
            attr_name=attr_name,
            fields=fields,
        )

        # Store command template for sending selected option when available
        if fields is not None and isinstance(fields, EEPEntityDef):
            if fields.command_template is not None:
                self._command_template = fields.command_template

    async def async_select_option(self, option: str) -> None:
        """Select an option and send command to device if template available."""
        if option not in self._attr_options:
            return

        if self._command_template:
            # Find the numeric value for the selected option
            option_index = self._attr_options.index(option)

            # Send command using the template
            await self.hass.async_add_executor_job(
                self._send_message,
                self._command_template,
                {
                    "value": option_index,
                    "option": option,
                    "device_id": self.dev_id,
                    "data_field": self._data_field,
                },
                self._rorg,
                self._rorg_func,
                self._rorg_type,
            )

        self._current_option = option
        self.async_write_ha_state()

    @callback
    def value_changed(self, packet: Any) -> None:
        """Update current option based on incoming packet using parser when available."""
        # Prefer packet.parsed if present
        parsed = getattr(packet, "parsed", None)
        if not parsed or not self._data_field:
            return

        # Try to get the enum-resolved value first (for proper description mapping)
        # Prefer using the original EEP fields mapping (dict) for enum resolution
        fields_mapping = None
        if isinstance(self._fields, dict):
            fields_mapping = self._fields
        else:
            fields_mapping = getattr(self._fields, "raw_fields", None)

        # Use get_field_value_with_enum to properly map raw values to descriptions
        if fields_mapping and get_field_value_with_enum is not None:
            try:
                value = get_field_value_with_enum(
                    parsed, self._data_field, fields_mapping
                )
                if value is not None:
                    value_str = str(value)
                    for opt in self._attr_options:
                        if opt == value_str or opt.lower() == value_str.lower():
                            self._current_option = opt
                            self.schedule_update_ha_state()
                            return
            except (AttributeError, KeyError, TypeError, ValueError) as err:
                LOGGER.debug(
                    "Failed to get enum value for %s: %s",
                    self._attr_unique_id,
                    err,
                )

        # Fallback: try direct value extraction without enum mapping
        # For enum fields, prefer 'value' (enum description) over 'raw_value' (numeric)
        try:
            entry = parsed.get(self._data_field)
            if isinstance(entry, dict):
                raw = entry.get("value") or entry.get("raw_value") or entry.get("raw")
            else:
                raw = entry

            if raw is not None:
                raw_str = str(raw)
                for opt in self._attr_options:
                    if opt == raw_str or opt.lower() == raw_str.lower():
                        self._current_option = opt
                        self.schedule_update_ha_state()
                        return
        except (AttributeError, KeyError, TypeError, ValueError) as err:
            LOGGER.debug(
                "Failed to map packet to select option for %s: error: %s",
                self._attr_unique_id,
                err,
            )
