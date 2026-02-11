# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-11

### Added
- CommandTemplateButton for dynamic button entities based on EEP profiles
- Last data received sensor for monitoring device communication
- Min/max value support for better entity classification
- Enhanced dynamic parsing for select entities

### Changed
- Refactored BOOS (Boost) and VAC (Vacances/Holiday) configurations
- Improved handling of "Actif (temps restant inconnu)" state (value 1 after setting)
- Enhanced entity definitions in eep_platform_mapping.yaml
- Better error handling in select platform

### Fixed
- VentilAirSec state handling for temporary modes
- Dynamic enum parsing with proper value ranges

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

[1.0.1]: https://github.com/pledou/ha-enocean/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/pledou/ha-enocean/releases/tag/v1.0.0
