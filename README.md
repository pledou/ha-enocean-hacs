# EnOcean Extended for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/pledou/ha-enocean.svg)](https://github.com/pledou/ha-enocean/releases)
[![Tests](https://github.com/pledou/ha-enocean/actions/workflows/test.yml/badge.svg)](https://github.com/pledou/ha-enocean/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/pledou/ha-enocean.svg)](LICENSE)

An enhanced Home Assistant integration for EnOcean devices with extended device support and dynamic EEP parsing.

## Overview

This custom integration extends the standard Home Assistant EnOcean integration with:

- **Extended Device Support**: Additional EnOcean Equipment Profiles (EEPs) including VentilAirSec ventilation units
- **Dynamic EEP Parsing**: Improved parsing of complex EEP profiles with proper enum handling
- **Multiple Platform Support**: Full support for sensors, binary sensors, switches, lights, buttons, numbers, and select entities
- **Easy Setup**: Config flow with automatic device discovery
- **Serial Port Auto-detection**: Automatically finds your EnOcean USB dongle

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/pledou/ha-enocean`
6. Select category "Integration"
7. Click "Add"
8. Find "EnOcean Extended" in the integration list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/pledou/ha-enocean/releases)
2. Extract the `custom_components/enocean` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

### Note on HACS Validation

When validating this repository, HACS may show a warning about the brands repository: **"The repository has not been added as a custom domain to the brands repo"**. This is expected and not an issue. This custom integration uses the `enocean` domain (same as the core Home Assistant integration) and automatically inherits the existing EnOcean branding from the [Home Assistant brands repository](https://github.com/home-assistant/brands). Since this integration replaces/extends the core enocean component, it reuses the official enocean brand assets (logo, icon, etc.).

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "EnOcean"
4. Select your serial port from the dropdown (auto-detected)
5. Follow the configuration wizard

## Supported Devices

### Sensors
- Temperature sensors (A5-02-05, A5-02-0B, etc.)
- Humidity sensors (A5-04-01, A5-04-02, etc.)
- Power meters (A5-12-01, A5-12-02, A5-12-03)
- Ventilation units (D2-50-00, D2-50-01)
- And many more...

### Actuators
- Light switches (D2-01-08, D2-01-09, D2-01-12)
- Dimmers (A5-38-08)
- Window handles (F6-10-00)

### Special Devices
- VentilAirSec ventilation units with full control and monitoring

For a complete list of supported profiles, see [EEP Platform Mapping](custom_components/enocean/eep_platform_mapping.yaml).

## Dependencies

This integration uses the enhanced enocean library from PyPI: [enocean-extended](https://pypi.org/project/enocean-extended/)

The library is automatically installed when you install this integration.

## Development

This integration is based on the Home Assistant core EnOcean integration with improvements for:
- Dynamic EEP parsing with proper enum type handling
- Extended device profiles
- Better error handling and logging
- Improved teach-in functionality

## Testing

### Running Tests

Install test dependencies:
```bash
pip install -r requirements_test.txt
```

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=custom_components.enocean --cov-report=html
```

Run specific test files:
```bash
pytest tests/test_config_flow.py
pytest tests/test_light.py
```

### Test Requirements

- Python 3.11 or higher
- pytest 9.0.0
- pytest-homeassistant-custom-component

The test suite includes:
- Config flow tests
- Device profile tests
- EEP parsing and validation tests
- Platform-specific tests (lights, switches, sensors, etc.)
- Dynamic device configuration tests

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Credits

- Based on the Home Assistant core EnOcean integration
- Enhanced enocean library by Pierre Leduc
- Original enocean library by [kipe](https://github.com/kipe/enocean)

## Support

- **Issues**: [GitHub Issues](https://github.com/pledou/ha-enocean/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pledou/ha-enocean/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)
