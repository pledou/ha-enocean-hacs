"""Tests for EnOcean number entity min/max/unit handling."""

from custom_components.enocean.number import DynamicEnOceanNumber
from custom_components.enocean.types import EEPEntityDef, EntityType


def test_number_uses_min_max_unit_from_constructor() -> None:
    """Ensure min, max and unit provided to constructor are used."""
    dev_id = [0x01, 0x02, 0x03, 0x04]
    # Create dynamic number with explicit min/max/unit
    num = DynamicEnOceanNumber(
        dev_id,
        "Test Device",
        0xF6,
        0x02,
        0x01,
        data_field="temperature",
        min_value=1.5,
        max_value=9.5,
        unit="kW",
        fields=None,
    )

    assert num._attr_native_min_value == 1.5
    assert num._attr_native_max_value == 9.5
    assert num._attr_native_unit_of_measurement == "kW"


def test_number_defaults_when_no_min_max_unit() -> None:
    """Ensure attributes are None when not provided."""
    dev_id = [0x0A, 0x0B, 0x0C, 0x0D]
    num = DynamicEnOceanNumber(
        dev_id,
        "Another Device",
        0xF6,
        0x02,
        0x01,
        data_field="level",
        fields=None,
    )

    assert getattr(num, "_attr_native_min_value", None) is None
    assert getattr(num, "_attr_native_max_value", None) is None
    assert num._attr_native_unit_of_measurement is None


def test_number_extracts_min_max_unit_from_fields() -> None:
    """Ensure min, max and unit are extracted from provided EEP fields."""
    dev_id = [0x0E, 0x0F, 0x10, 0x11]
    fields = EEPEntityDef(
        description="level",
        rorg=0xF6,
        rorg_func=0x02,
        rorg_type=0x01,
        data_field="level",
        entity_type=EntityType.NUMBER,
        min_value=0,
        max_value=100,
        unit="%",
    )

    num = DynamicEnOceanNumber(
        dev_id,
        "EEP Device",
        0xF6,
        0x02,
        0x01,
        data_field="level",
        fields=fields,
    )

    assert num._attr_native_min_value == 0.0
    assert num._attr_native_max_value == 100.0
    assert num._attr_native_unit_of_measurement == "%"
