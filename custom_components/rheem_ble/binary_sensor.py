"""Binary sensor platform for the Rheem HVAC BLE integration."""

from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BINARY_SENSOR_DESCRIPTIONS, RheemBinarySensorMetadata
from .coordinator import RheemBLEConfigEntry, RheemBLECoordinator
from .entity import RheemBLEEntity, build_device_info
from .rheem_ble import COMMAND_LABELS, CommandResult, binary_is_on

PARALLEL_UPDATES = 0


def _description(metadata: RheemBinarySensorMetadata) -> BinarySensorEntityDescription:
    """Build the entity description for one command."""
    return BinarySensorEntityDescription(
        key=metadata.command,
        device_class=metadata.device_class,
        entity_category=metadata.entity_category,
        icon=metadata.icon,
        name=COMMAND_LABELS.get(metadata.command, metadata.command),
    )


def _binary_sensor_update(
    coordinator: RheemBLECoordinator, data: dict[str, CommandResult]
) -> PassiveBluetoothDataUpdate[bool | None]:
    """Turn a status poll into binary sensor entities.

    An empty map means the update came from an advertisement and changes nothing.
    """
    if not data:
        return PassiveBluetoothDataUpdate()

    descriptions: dict[PassiveBluetoothEntityKey, BinarySensorEntityDescription] = {}
    names: dict[PassiveBluetoothEntityKey, str] = {}
    values: dict[PassiveBluetoothEntityKey, bool | None] = {}
    for command, metadata in BINARY_SENSOR_DESCRIPTIONS.items():
        result = data.get(command)
        # OBJ_NOT_FOUND is never created. Any other error is left out of this
        # update so an existing entity keeps its previous value.
        if result is None or result.error:
            continue
        key = PassiveBluetoothEntityKey(command, None)
        label = COMMAND_LABELS.get(command, command)
        descriptions[key] = _description(metadata)
        names[key] = label
        values[key] = binary_is_on(result)

    return PassiveBluetoothDataUpdate(
        devices={
            None: build_device_info(
                coordinator.address, coordinator.equipment_type, data
            )
        },
        entity_descriptions=descriptions,
        entity_names=names,
        entity_data=values,
    )


class RheemBLEBinarySensor(RheemBLEEntity, BinarySensorEntity):
    """A Rheem BLE binary sensor."""

    @property
    @override
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        return self.processor.entity_data.get(self.entity_key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RheemBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rheem BLE binary sensors from a config entry."""
    coordinator = entry.runtime_data
    processor = PassiveBluetoothDataProcessor(
        lambda data: _binary_sensor_update(coordinator, data)
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(
            RheemBLEBinarySensor, async_add_entities
        )
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, BinarySensorEntityDescription)
    )
