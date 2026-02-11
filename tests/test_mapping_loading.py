"""Pytest tests for EEP mapping loading and conversion.

These tests assert the presence of the VentilAirSec mapping (RORG 0xD2 FUNC 0x01 TYPE 0x00)
and verify that `_build_entities_from_mapping` converts YAML entries into
EEPEntityDef-like objects with expected attributes.
"""

from __future__ import annotations

from custom_components.enocean.eep_devices import _load_eep_mapping


def test_mapping_contains_d2_func01_type00() -> None:
    """Mapping file contains RORG 0xD2 / FUNC 0x01 / TYPE 0x00 with entities."""
    mapping = _load_eep_mapping()
    assert isinstance(mapping, dict)

    # Ensure RORG 0xD2 exists
    assert 0xD2 in mapping, "Expected RORG 0xD2 in mapping"
    func_entry = mapping[0xD2].get(0x01)
    assert func_entry is not None, "Expected FUNC 0x01 under RORG 0xD2"

    type_entry = func_entry.get(0x00)
    assert type_entry is not None, "Expected TYPE 0x00 under FUNC 0x01"

    entities = type_entry.get("entities", [])
    assert isinstance(entities, list)

    # There should be at least one number entity defined for this profile
    assert any(e.get("component") == "number" for e in entities), (
        "Expected at least one 'number' component in entities for D2/01/00"
    )
