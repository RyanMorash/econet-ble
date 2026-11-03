# Rheem HVAC BLE Protocol Notes

## Hardware

- **Device name**: `EcoNet-FRN-W262536112` (furnace; other models use `EcoNet-` prefix)
- **Service**: Nordic UART Service (NUS)
  - Service UUID: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
  - TX (phone → device, write-without-response): `6e400002-b5a3-f393-e0a9-e50e24dcca9e`
  - RX (device → phone, notify): `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- **Scan filter**: service UUID `6e400001-...` OR `00000c56-0000-1000-8000-00805f9b34fb`, device name prefix `EcoNet`

## Connection Sequence

Derived from `BluetoothConnector.java` in the decompiled Android app and Linux/BlueZ testing.

### Android (reference)

```
connectGatt(ctx, autoConnect=false, callback, TRANSPORT_LE=2)
→ onConnectionStateChange(STATE_CONNECTED)
  → gatt.discoverServices()          # immediate, no explicit pairing
→ onServicesDiscovered
  → gatt.requestMtu(517)
→ onMtuChanged
  → setCharacteristicNotification(rxChar, true)
  → writeDescriptor(CCCD, ENABLE_NOTIFICATION_VALUE)
→ ReadyForDataExchange
```

Android's BLE stack silently handles the furnace's SMP Security Request at the HCI layer before `onConnectionStateChange` fires — the app never sees it.

If `onCharacteristicRead/Write` returns status `5` (GATT_INSUFF_AUTHENTICATION), the app calls `device.removeBond()` (via reflection) and retries from scratch.

### Linux / BlueZ

BlueZ does **not** silently handle peripheral-initiated SMP Security Requests (opcode `0x0b`). Without the stack completing that exchange, the furnace can disconnect during GATT service discovery with:

```
kernel: Bluetooth: hci0: Unexpected SMP command 0x0b from ...
```

That behavior is protocol background. The Home Assistant integration does not register a pairing agent, call `Pair()`, or use BlueZ D-Bus. It connects with `establish_connection()` and the `BLEDevice` from Home Assistant's Bluetooth integration:

```
1. Home Assistant reports a connectable advertisement for EcoNet-*
2. async_ble_device_from_address(hass, address, connectable=True)
3. establish_connection(BleakClient, ble_device, name)
4. start_notify(rx_uuid)
5. Read status commands, then disconnect
```

## Adapter Selection

- Do **not** hardcode `hci0` (or any adapter). The system may have multiple adapters.
- In Home Assistant, use `async_ble_device_from_address(hass, mac, connectable=True)` to get the best `BLEDevice` (highest RSSI, any connectable adapter or proxy).
- Pass the `BLEDevice` to `establish_connection()`. It encodes the adapter choice.
- Do not open a D-Bus connection to BlueZ from the integration.

## Command Protocol

See `rheem_ble.py` for full implementation. Summary:

- **Packet size**: 28 bytes for a single-command READ
- **Opcode byte 13**: `0x1E` = READ
- **Byte 14**: `0x01` = single command, **Byte 15**: `0x01` = SHORT property
- **Bytes 18–25**: command name, 8 ASCII bytes, null-padded
- **Bytes 26–27**: CRC (custom algorithm, see `calc_crc()`)
- **Destination**: board address in bytes 0–3; source (BLE chip) in bytes 5–8

### Board Addresses

| Equipment | Address |
|-----------|---------|
| Furnace / ResiPak | `80 00 01 C0` |
| Air Handler | `80 00 03 C0` |
| ODU / Heat Pump | `80 00 04 00` |
| HWH / MWH | `80 00 20 80` |
| BLE chip (for `SW_VERSN_BLE`) | `80 00 03 00` |

### Response Data Types (byte 14)

| Byte | Type | Value location |
|------|------|---------------|
| `0x80` | IEEE float | bytes 25–28 (big-endian) |
| `0x81` | Text | bytes 25–(10+data_len) |
| `0x82` | Enumerated text | bytes 27–(11+data_len) |
| `0x83` | Enumerated number | bytes 25–28 |
| `0x84` | Byte stream | bytes 25–(10+data_len) |
| `0x01` | Error: OBJ_NOT_FOUND | — |
| `0x02` | Error: CANNOT_BE_WRITTEN | — |
| `0x04` | Error: DATA_TYPE_CONFLICT | — |

## Pressure Units

IEEE float responses that represent pressure use different units depending on the physical quantity:

| Command | Unit | Notes |
|---------|------|-------|
| `STATIC_P` | inH₂O | Duct static air pressure. Android string resource: `unit_static_pressure = "H2O"`. Typical 0.1–1.0 inH₂O, device-reported max 20. **Not PSI.** |
| `PRES_SUC` | PSIA | Refrigerant suction pressure (absolute). |
| `PRESSUCG` | PSIG | Refrigerant suction pressure (gauge). |
| `PRES_LIQ` | PSIA | Refrigerant liquid-line pressure (absolute). |
| `PRESLIQG` | PSIG | Refrigerant liquid-line pressure (gauge). |
| `IDU_SUCP` | PSIA | Indoor unit suction pressure (absolute). |

## MTU

The Android app requests MTU 517 after service discovery. The Linux implementation does not currently request a custom MTU (BlueZ defaults to 23 bytes). Larger MTU would allow multi-byte packets in a single ATT transaction, but the protocol uses short command names and the default MTU appears sufficient for all known commands.
