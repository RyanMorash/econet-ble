"""Sensor platform for the Rheem HVAC BLE integration."""

from typing import override

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
)
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SENSOR_DESCRIPTIONS, RheemSensorMetadata
from .coordinator import RheemBLEConfigEntry, RheemBLECoordinator
from .entity import RheemBLEEntity, build_device_info
from .rheem_ble import COMMAND_LABELS, CommandResult, sensor_native_value

PARALLEL_UPDATES = 0


def _expects_numeric(metadata: RheemSensorMetadata) -> bool:
    """Return True when Home Assistant expects a number from this sensor."""
    return metadata.state_class is not None or metadata.device_class is not None


def _description(metadata: RheemSensorMetadata) -> SensorEntityDescription:
    """Build the entity description for one command."""
    return SensorEntityDescription(
        key=metadata.command,
        device_class=metadata.device_class,
        state_class=metadata.state_class,
        native_unit_of_measurement=metadata.native_unit_of_measurement,
        entity_category=metadata.entity_category,
        icon=metadata.icon,
        name=COMMAND_LABELS.get(metadata.command, metadata.command),
    )


def _sensor_update(
    coordinator: RheemBLECoordinator, data: dict[str, CommandResult]
) -> PassiveBluetoothDataUpdate[float | str | None]:
    """Turn a status poll into sensor entities.

    An empty map means the update came from an advertisement and changes nothing.
    """
    if not data:
        return PassiveBluetoothDataUpdate()

    descriptions: dict[PassiveBluetoothEntityKey, SensorEntityDescription] = {}
    names: dict[PassiveBluetoothEntityKey, str] = {}
    values: dict[PassiveBluetoothEntityKey, float | str | None] = {}
    for command, metadata in SENSOR_DESCRIPTIONS.items():
        result = data.get(command)
        # OBJ_NOT_FOUND is never created. Any other error is left out of this
        # update so an existing entity keeps its previous value.
        if result is None or result.error:
            continue
        key = PassiveBluetoothEntityKey(command, None)
        label = COMMAND_LABELS.get(command, command)
        descriptions[key] = _description(metadata)
        names[key] = label
        values[key] = sensor_native_value(
            result, numeric=_expects_numeric(metadata)
        )

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


class RheemBLESensor(RheemBLEEntity, SensorEntity):
    """A Rheem BLE sensor."""

    @property
    @override
    def native_value(self) -> float | str | None:
        """Return the sensor value."""
        return self.processor.entity_data.get(self.entity_key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RheemBLEConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rheem BLE sensors from a config entry."""
    coordinator = entry.runtime_data
    processor = PassiveBluetoothDataProcessor(
        lambda data: _sensor_update(coordinator, data)
    )
    entry.async_on_unload(
        processor.async_add_entities_listener(RheemBLESensor, async_add_entities)
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )
