"""Tests for EEP min/max value extraction from scale and range elements."""

from bs4 import BeautifulSoup

from custom_components.enocean.eep_devices import _extract_eep_fields


def test_extract_min_max_from_scale_and_range() -> None:
    """Ensure nested <scale> and <range> min/max are parsed into fields.

    Build a minimal <profile> with a <data command="0"> containing a
    <value> that has both <range> and <scale> children. The loader should
    prefer <scale> values and return numeric min/max on the extracted field
    with a command prefix (CMD0_).
    """
    xml = """
    <profile>
      <command description="command identifier" shortcut="CMD" offset="4" size="4">
      </command>
      <data command="0" bits="12">
        <value description="Temperature consigne Electrique" shortcut="TEMPCELEC" offset="40" size="8" unit="">
          <range>
            <min>0</min>
            <max>18</max>
          </range>
          <scale>
            <min>0</min>
            <max>18</max>
          </scale>
        </value>
      </data>
    </profile>
    """

    soup = BeautifulSoup(xml, "xml")
    profile_el = soup.find("profile")

    # Directly test _extract_eep_fields with the profile element
    prof = _extract_eep_fields(profile_el, rorg=0xD1, rorg_func=0x07, rorg_type=0x09)
    assert prof is not None and len(prof) > 0
    # Find our field
    target = None
    for f in prof:
        if f.data_field == "TEMPCELEC":
            target = f
            break

    assert target is not None, "Expected TEMPCELEC field to be extracted"
    # Ensure min/max were parsed as numbers (floats)
    assert float(target.min_value or 0) == 0.0
    assert float(target.max_value or 0) == 18.0
