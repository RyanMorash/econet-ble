"""Coordinator for Rheem HVAC BLE."""

import logging

from homeassistant.components.bluetooth import (
    BluetoothReachabilityIntent,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_address_reachability_diagnostics,
    async_ble_device_from_address,
    async_clear_advertisement_history,
)
from homeassistant.components.bluetooth.active_update_processor import (
    ActiveBluetoothProcessorCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.redact import partial_redact

from .const import DEFAULT_SCAN_INTERVAL, SCAN_DURATION
from .rheem_ble import (
    CommandResult,
    EquipmentType,
    RheemBLEClient,
    commands_from_advertisement,
    poll_is_due,
)

_LOGGER = logging.getLogger(__name__)


class RheemBLECoordinator(
    ActiveBluetoothProcessorCoordinator[dict[str, CommandResult]]
):
    """Poll a Rheem unit when a connectable advertisement shows it is nearby."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        equipment_type: EquipmentType,
        config_entry_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            address=address,
            mode=BluetoothScanningMode.ACTIVE,
            update_method=self._parse_advertisement,
            needs_poll_method=self._needs_poll,
            poll_method=self._async_poll,
            connectable=True,
            scan_interval=float(DEFAULT_SCAN_INTERVAL),
            scan_duration=float(SCAN_DURATION),
        )
        self.equipment_type = equipment_type
        self.config_entry_id = config_entry_id
        self.data: dict[str, CommandResult] | None = None

    def _parse_advertisement(
        self, service_info: BluetoothServiceInfoBleak
    ) -> dict[str, CommandResult]:
        """Ignore advertisement payloads. Status is read over a connection."""
        return commands_from_advertisement()

    @callback
    def _needs_poll(
        self,
        service_info: BluetoothServiceInfoBleak,
        seconds_since_last_poll: float | None,
    ) -> bool:
        """Return whether a connectable adapter can reach the unit and a poll is due."""
        if self.hass.state is not CoreState.running:
            return False
        if not poll_is_due(seconds_since_last_poll, DEFAULT_SCAN_INTERVAL):
            return False
        return bool(
            async_ble_device_from_address(
                self.hass, service_info.address, connectable=True
            )
        )

    async def _async_poll(
        self, service_info: BluetoothServiceInfoBleak
    ) -> dict[str, CommandResult]:
        """Connect and read the status commands for this equipment type."""
        try:
            ble_device = service_info.device if service_info.connectable else None
            if ble_device is None:
                ble_device = async_ble_device_from_address(
                    self.hass, service_info.address, connectable=True
                )
            if ble_device is None:
                raise RuntimeError("No connectable adapter can reach the device")
            async with RheemBLEClient(self.address, ble_device=ble_device) as client:
                results = await client.read_system_status(self.equipment_type)
            self.data = {result.command: result for result in results}
            self._async_sync_device_registry(self.data)
            return self.data
        except Exception as err:
            reason = async_address_reachability_diagnostics(
                self.hass,
                service_info.address,
                BluetoothReachabilityIntent.CONNECTION,
            )
            raise RuntimeError(reason) from err
        finally:
            async_clear_advertisement_history(self.hass, self.address)

    def _async_sync_device_registry(self, data: dict[str, CommandResult]) -> None:
        """Publish model and firmware from this poll to the device registry.

        Entity setup reads device info only when an entity is added. Later
        polls still have to write SW_VERSN and MDPRTNUM themselves.
        """
        # Imported lazily: entity.py imports this coordinator.
        from .entity import build_device_info

        try:
            dr.async_get(self.hass).async_get_or_create_from_info(
                config_entry_id=self.config_entry_id,
                device_info=build_device_info(
                    self.address, self.equipment_type, data
                ),
            )
        except Exception:
            _LOGGER.exception(
                "Could not update the device registry for %s",
                partial_redact(self.address),
            )


type RheemBLEConfigEntry = ConfigEntry[RheemBLECoordinator]
