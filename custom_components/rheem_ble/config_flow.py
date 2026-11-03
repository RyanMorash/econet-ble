"""Config flow for the Rheem HVAC BLE integration."""

import logging
import re
from typing import Any

from bleak import BleakError
from bluetooth_data_tools import human_readable_name
import probatio

from homeassistant.components.bluetooth import (
    BluetoothReachabilityIntent,
    BluetoothServiceInfoBleak,
    async_address_reachability_diagnostics,
    async_ble_device_from_address,
    async_discovered_service_info,
    async_request_active_scan,
    async_scanner_count,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.redact import partial_redact

from .const import CONF_DEVICE, CONF_MAC_ADDRESS, DEVICE_NAME_PREFIX, DOMAIN
from .rheem_ble import EquipmentType, RheemBLEClient

_LOGGER = logging.getLogger(__name__)

MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")

WATER_HEATER_TYPES = {EquipmentType.MWH, EquipmentType.HWH}


class CannotConnect(Exception):
    """Error to indicate we cannot connect to the device."""


class UnsupportedDevice(Exception):
    """Error to indicate the device is not supported."""


class RheemBLEConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rheem HVAC BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_name = ""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        self._did_active_scan = False
        self._errors: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a discovered EcoNet device."""
        if not discovery_info.connectable:
            return self.async_abort(reason="not_connectable")
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self._discovered_name = human_readable_name(
            None, discovery_info.name, discovery_info.address
        )
        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered device and detect its equipment type."""
        if user_input is not None:
            assert self._discovery_info is not None
            created = await self._async_create_for(self._discovery_info.address)
            if created is not None:
                return created
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovered_name},
            errors=self._errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a manual setup."""
        if async_scanner_count(self.hass, connectable=True) == 0:
            return self.async_abort(reason="no_scanner")

        if user_input is not None:
            selected = self._address_from_user_input(user_input)
            if selected is not None:
                await self.async_set_unique_id(selected)
                self._abort_if_unique_id_configured()
                created = await self._async_create_for(selected)
                if created is not None:
                    return created
        else:
            await self._async_find_devices()

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(),
            errors=self._errors,
        )

    async def _async_find_devices(self) -> None:
        """Collect nearby EcoNet devices, scanning actively once if needed."""
        self._collect_discovered_devices()
        if self._discovered_devices or self._did_active_scan:
            return
        self._did_active_scan = True
        await async_request_active_scan(self.hass)
        self._collect_discovered_devices()

    def _collect_discovered_devices(self) -> None:
        """Store connectable EcoNet devices that are not already set up."""
        current = self._async_current_ids(include_ignore=False)
        for discovery in async_discovered_service_info(self.hass, connectable=True):
            if not discovery.name.startswith(DEVICE_NAME_PREFIX):
                continue
            if (
                discovery.address in current
                or discovery.address in self._discovered_devices
            ):
                continue
            self._discovered_devices[discovery.address] = discovery

    def _user_schema(self) -> probatio.Schema:
        """Return the manual setup schema."""
        if self._discovered_devices:
            return probatio.Schema(
                {
                    probatio.Optional(CONF_DEVICE): probatio.In(
                        {
                            service_info.address: (
                                f"{service_info.name} ({service_info.address})"
                            )
                            for service_info in self._discovered_devices.values()
                        }
                    ),
                    probatio.Optional(CONF_MAC_ADDRESS): str,
                }
            )
        return probatio.Schema({probatio.Required(CONF_MAC_ADDRESS): str})

    def _address_from_user_input(self, user_input: dict[str, Any]) -> str | None:
        """Return the chosen address, or None when the form should be shown again."""
        typed = str(user_input.get(CONF_MAC_ADDRESS) or "").strip()
        if typed:
            address = typed.upper()
            if not MAC_REGEX.match(address):
                self._errors = {CONF_MAC_ADDRESS: "invalid_mac"}
                return None
            self._errors = {}
            return address
        selected = user_input.get(CONF_DEVICE)
        if isinstance(selected, str) and selected:
            self._errors = {}
            return selected
        self._errors = {"base": "no_device"}
        return None

    async def _async_create_for(self, address: str) -> ConfigFlowResult | None:
        """Detect the equipment and create the entry."""
        try:
            equipment_type = await self._async_detect_equipment(address)
        except CannotConnect:
            self._errors = {"base": "cannot_connect"}
            return None
        except UnsupportedDevice:
            self._errors = {"base": "unsupported_device"}
            return None
        except Exception:
            _LOGGER.exception(
                "Unexpected error connecting to %s", partial_redact(address)
            )
            self._errors = {"base": "unknown"}
            return None
        self._errors = {}
        return self.async_create_entry(
            title=f"Rheem {equipment_type.value} ({address})",
            data={
                CONF_MAC_ADDRESS: address,
                "equipment_type": equipment_type.value,
            },
        )

    async def _async_detect_equipment(self, address: str) -> EquipmentType:
        """Connect to the device and detect its equipment type."""
        ble_device = async_ble_device_from_address(
            self.hass, address, connectable=True
        )
        if ble_device is None:
            self._log_unreachable(address, "device has not been seen")
            raise CannotConnect

        try:
            async with RheemBLEClient(address, ble_device=ble_device) as client:
                equipment_type = await client.detect_equipment_type()
        except (BleakError, OSError, TimeoutError, RuntimeError) as err:
            self._log_unreachable(address, err)
            raise CannotConnect from err

        if equipment_type is None or equipment_type == EquipmentType.UNKNOWN:
            self._log_unreachable(address, "equipment type was not detected")
            raise CannotConnect

        if equipment_type in WATER_HEATER_TYPES:
            _LOGGER.debug(
                "Device %s is a water heater (%s), which is not supported",
                partial_redact(address),
                equipment_type.value,
            )
            raise UnsupportedDevice

        return equipment_type

    def _log_unreachable(self, address: str, err: object) -> None:
        """Log why a connection failed, without a raw address."""
        reason = async_address_reachability_diagnostics(
            self.hass, address, BluetoothReachabilityIntent.CONNECTION
        )
        _LOGGER.debug(
            "Could not connect to %s: %s. %s",
            partial_redact(address),
            err,
            reason,
        )
