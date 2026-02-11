# EnOcean Extended Integration

This is an enhanced version of the Home Assistant EnOcean integration with extended device support and dynamic EEP parsing.

## Features

- **Extended Device Support**: Additional EnOcean Equipment Profiles (EEPs) including VentilAirSec ventilation units
- **Dynamic EEP Parsing**: Improved parsing of complex EEP profiles with proper enum handling
- **Multiple Platform Support**: Sensors, binary sensors, switches, lights, buttons, numbers, and select entities
- **Config Flow**: Easy setup through the UI with automatic device discovery
- **Serial Port Auto-detection**: Automatically detects EnOcean USB dongles

## Supported Devices

This integration supports a wide range of EnOcean devices including:
- Temperature and humidity sensors
- Window/door contacts
- Motion sensors
- Light switches
- Dimmers
- Ventilation units (including VentilAirSec)
- And many more...

## Configuration

1. Install this integration via HACS
2. Restart Home Assistant
3. Go to Configuration -> Integrations
4. Click the "+" button and search for "EnOcean"
5. Follow the configuration wizard

## Requirements

This integration requires the enhanced enocean Python library from [pledou/enocean](https://github.com/pledou/enocean).

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/pledou/ha-enocean-hacs).
