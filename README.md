# rheem-ble

Home Assistant custom component for Rheem/EcoNet HVAC equipment via Bluetooth Low Energy.

Reverse-engineered from the decompiled Rheem Contractor Android app.

## Supported devices

Any `EcoNet-` prefixed BLE device using the Nordic UART Service (NUS):
- Gas furnaces, UlNOx furnaces, ResiPak
- Air handlers
- Outdoor units, heat pumps, condensing units

Water heaters (MWH, HWH) are recognized during setup and left unconfigured. The integration has no water-heater entities.

## Installation

Copy `custom_components/rheem_ble/` into your Home Assistant `config/custom_components/` directory and restart HA. Home Assistant discovers devices named `EcoNet-*` through its Bluetooth integration. You can also add **Rheem HVAC BLE** and pick a discovered device, or enter a MAC address that a connectable adapter has already seen.

Status is read over a connection about once a minute, after a connectable adapter hears the device. Home Assistant chooses the adapter, including a remote proxy. This integration does not talk to BlueZ itself. Bluetooth libraries come from Home Assistant; do not install them into the Home Assistant environment for this integration.

## Protocol

See [`BLE.md`](BLE.md) for the BLE connection flow, SMP security handling, and command protocol details.

## Diagnostics

`rheem_diag.py` is a standalone CLI for reading furnace status without Home Assistant:

```
pip install bleak bleak-retry-connector
python rheem_diag.py <MAC_ADDRESS>
python rheem_diag.py <MAC_ADDRESS> --type furnace
python rheem_diag.py scan
```

## Tests

```
pip install pytest pytest-asyncio
python -m pytest tests/
```
