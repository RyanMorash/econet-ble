"""Diagnostics support for Rheem HVAC BLE."""

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import REDACTED, async_redact_data

from .const import CONF_MAC_ADDRESS
from .coordinator import RheemBLEConfigEntry
from .rheem_ble import COMMAND_LABELS

TO_REDACT = {CONF_MAC_ADDRESS}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: RheemBLEConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    commands: dict[str, Any] = {}

    if coordinator.data:
        for command, result in coordinator.data.items():
            value = result.value
            if isinstance(value, bytes | bytearray):
                value = value.hex()
            commands[command] = {
                "label": COMMAND_LABELS.get(command, command),
                "data_type": result.data_type,
                "value": value,
                "min_value": result.min_value,
                "max_value": result.max_value,
                "error": result.error,
            }

    if (serial := commands.get("SERIAL_N")) is not None:
        serial["value"] = REDACTED

    return async_redact_data(
        {
            CONF_MAC_ADDRESS: coordinator.address,
            "equipment_type": coordinator.equipment_type.value,
            "commands": commands,
        },
        TO_REDACT,
    )
