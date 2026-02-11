# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-11

### Added
- Initial release of EnOcean Extended integration
- Dynamic EEP parsing with proper enum handling
- Support for VentilAirSec ventilation units (D2-50-00, D2-50-01)
- Extended device profile support
- Config flow with automatic serial port detection
- Multiple platform support (sensor, binary_sensor, switch, light, button, number, select)
- Teach-in functionality for new devices
- Comprehensive device mapping via eep_platform_mapping.yaml

### Changed
- Enhanced enocean library requirement (pledou/enocean)
- Improved error handling and logging
- Better device state management

### Fixed
- Enum parsing for complex EEP profiles
- VentilAirSec MSC packet building
- Device availability tracking

[1.0.0]: https://github.com/pledou/ha-enocean-hacs/releases/tag/v1.0.0
