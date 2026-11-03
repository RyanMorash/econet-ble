"""Shared Rheem BLE entity helpers."""

from typing import Any, override

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription

from .const import DOMAIN
from .coordinator import RheemBLECoordinator
from .rheem_ble import CommandResult, EquipmentType


def text_result(data: dict[str, CommandResult], command: str) -> str | None:
    """Return a command value when the read succeeded."""
    result = data.get(command)
    if result is None or result.error or result.value is None:
        return None
    text = str(result.value).strip()
    return text or None


def build_device_info(
    address: str,
    equipment_type: EquipmentType,
    data: dict[str, CommandResult],
) -> DeviceInfo:
    """Build device registry info from a status poll."""
    info = DeviceInfo(
        identifiers={(DOMAIN, address)},
        connections={(CONNECTION_BLUETOOTH, address)},
        manufacturer="Rheem",
        model=equipment_type.value,
        name=f"Rheem {equipment_type.value.replace('_', ' ').title()}",
    )
    if (sw_version := text_result(data, "SW_VERSN")) is not None:
        info.sw_version = sw_version
    if (hw_version := text_result(data, "MDPRTNUM")) is not None:
        info.hw_version = hw_version
    return info


class RheemBLEEntity(PassiveBluetoothProcessorEntity):
    """Rheem entity that keeps the existing device and unique ids."""

    def __init__(
        self,
        processor: PassiveBluetoothDataProcessor[Any, Any],
        entity_key: PassiveBluetoothEntityKey,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity and preserve registry ids."""
        super().__init__(processor, entity_key, description)
        address = processor.coordinator.address
        self._attr_unique_id = f"{address}_{entity_key.key}"
        self._attr_device_info = self._rheem_device_info()

    def _rheem_device_info(self) -> DeviceInfo:
        """Return device info identified by this integration."""
        coordinator: RheemBLECoordinator = self.processor.coordinator
        address = coordinator.address
        stored = self.processor.devices.get(None)
        if stored is None:
            return build_device_info(address, coordinator.equipment_type, {})
        info = DeviceInfo()
        info.update(stored)
        info.identifiers = {(DOMAIN, address)}
        info.connections = {(CONNECTION_BLUETOOTH, address)}
        return info

    @override
    @callback
    def _handle_processor_update(self, new_data: Any) -> None:
        """Refresh device info, then write state."""
        self._attr_device_info = self._rheem_device_info()
        super()._handle_processor_update(new_data)
