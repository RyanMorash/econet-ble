"""Rheem HVAC BLE integration for Home Assistant."""

from homeassistant.components.bluetooth import async_rediscover_address
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import RheemBLEConfigEntry, RheemBLECoordinator
from .rheem_ble import EquipmentType

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: RheemBLEConfigEntry) -> bool:
    """Set up Rheem BLE from a config entry."""
    address = entry.unique_id or entry.data["mac_address"]
    coordinator = RheemBLECoordinator(
        hass,
        address,
        EquipmentType(entry.data["equipment_type"]),
        entry.entry_id,
    )
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(coordinator.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RheemBLEConfigEntry) -> bool:
    """Unload a Rheem BLE config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: RheemBLEConfigEntry) -> None:
    """Rediscover the device after its config entry is removed."""
    address = entry.unique_id or entry.data.get("mac_address")
    if address:
        async_rediscover_address(hass, address)
