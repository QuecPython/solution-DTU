# ChangeLog

All significant changes to this project will be documented in this file.

## [v2.0.0] - 2022-05-30

- Adjusted the overall project structure and refactored each module using the observer pattern design.
- Unified all cloud interfaces and middleware Remote interfaces.

## [v2.0.1] - 2022-07-05

- Fixed a bug where only one .py file could be upgraded when updating the Quectel Cloud project script files.
- Fixed a bug where memory allocation failed in gc when extracting tar packages during Quectel Cloud project script upgrades.

## [v3.0.0] - 2022-08-17

- Removed the command mode and Mosbus mode of DTU, only retaining the transparent transmission mode.
- Removed the code and functionality related to the DTU GUI channel.
- DTU now only supports MQTT and TCP protocols.

## [v3.1.0] - 2025-06-05

- Removed Quec Thing support
- Separated serial ports for DTU Tool (GUI app) and the device communication
- Minor enhancements and newer API support
