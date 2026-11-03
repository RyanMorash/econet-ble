"""Tests for RheemBLEClient connection logic.

Covers:
- Adapter selection: establish_connection receives ble_device (not hardcoded hci0)
- No direct BlueZ pairing
- Response collection when the notification arrives during the write
- Failure propagation
- Context manager protocol
"""
import asyncio
import os
import importlib.util
import struct
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Import rheem_ble.py directly to avoid pulling in homeassistant via __init__.py
_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "rheem_ble", "rheem_ble.py"
)
_spec = importlib.util.spec_from_file_location("cc_rheem_ble", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

RheemBLEClient = _mod.RheemBLEClient
NUS_TX_UUID = _mod.NUS_TX_UUID
NUS_RX_UUID = _mod.NUS_RX_UUID


def _make_mock_client(connected=True):
    """Return a mock BleakClient that reports as connected."""
    mock = AsyncMock()
    mock.is_connected = connected
    mock.services = _make_nus_services()
    return mock


def _make_nus_services():
    """Minimal GATT service list exposing the NUS TX and RX characteristics."""
    rx_char = MagicMock()
    rx_char.uuid = NUS_RX_UUID
    rx_char.properties = ["notify"]

    tx_char = MagicMock()
    tx_char.uuid = NUS_TX_UUID
    tx_char.properties = ["write-without-response"]

    service = MagicMock()
    service.characteristics = [rx_char, tx_char]

    return [service]


def _patch_establish(return_value=None, side_effect=None):
    """Patch establish_connection on the loaded module object."""
    mock = AsyncMock(return_value=return_value, side_effect=side_effect)
    return patch.object(_mod, "establish_connection", mock)


def _ieee_response(value=72.5):
    """Build a complete IEEE response whose length matches data_len."""
    buf = bytearray(29)
    buf[10] = 15
    buf[14] = 0x80
    buf[25:29] = struct.pack(">f", value)
    return bytes(buf)


# ---------------------------------------------------------------------------
# No direct adapter or pairing control
# ---------------------------------------------------------------------------

class TestNoDirectBlueZ:
    def test_no_ensure_paired_method(self):
        """_ensure_paired must not exist on RheemBLEClient."""
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF")
        assert not hasattr(client, "_ensure_paired")

    def test_no_pairing_or_cache_helpers(self):
        """Connection goes through Bleak only."""
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF")
        assert not hasattr(client, "_register_pairing_agent")
        assert not hasattr(client, "_unregister_pairing_agent")
        assert not hasattr(client, "_pair_via_dbus")
        assert not hasattr(client, "_remove_device_cache")


# ---------------------------------------------------------------------------
# Adapter selection via establish_connection
# ---------------------------------------------------------------------------

class TestAdapterSelection:
    @pytest.mark.asyncio
    async def test_connect_passes_ble_device_to_establish_connection(self):
        """establish_connection must receive the BLEDevice, not the MAC string.

        HA's bluetooth manager encodes adapter/proxy choice in the BLEDevice.
        establish_connection uses that to route the connection correctly.
        """
        mock_device = MagicMock(name="BLEDevice")
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF", ble_device=mock_device)

        mock_bleak = _make_mock_client()
        with _patch_establish(return_value=mock_bleak) as mock_ec:
            await client.connect()

        args = mock_ec.call_args
        assert args[0][1] is mock_device, (
            "establish_connection should receive the BLEDevice as second arg"
        )

    @pytest.mark.asyncio
    async def test_connect_passes_address_when_no_ble_device(self):
        """Falls back to MAC address string when no BLEDevice is supplied."""
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF")

        mock_bleak = _make_mock_client()
        with _patch_establish(return_value=mock_bleak) as mock_ec:
            await client.connect()

        args = mock_ec.call_args
        assert args[0][1] == "AA:BB:CC:DD:EE:FF"

    @pytest.mark.asyncio
    async def test_connect_passes_max_attempts(self):
        """establish_connection should receive our MAX_CONNECT_ATTEMPTS."""
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF")

        mock_bleak = _make_mock_client()
        with _patch_establish(return_value=mock_bleak) as mock_ec:
            await client.connect()

        kwargs = mock_ec.call_args[1]
        assert kwargs.get("max_attempts") == RheemBLEClient.MAX_CONNECT_ATTEMPTS




# ---------------------------------------------------------------------------
# Failure propagation
# ---------------------------------------------------------------------------

class TestConnectFailure:
    @pytest.mark.asyncio
    async def test_connect_raises_runtime_error_when_establish_fails(self):
        """RuntimeError is raised when establish_connection raises."""
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF")

        with _patch_establish(side_effect=OSError("BLE timeout")):
            with pytest.raises(RuntimeError, match="Failed to connect"):
                await client.connect()

    @pytest.mark.asyncio
    async def test_connect_raises_when_disconnected_after_service_discovery(self):
        """RuntimeError is raised if the client is not connected after _find_characteristics."""
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF")

        mock_bleak = _make_mock_client(connected=False)
        with _patch_establish(return_value=mock_bleak):
            with pytest.raises(RuntimeError, match="Disconnected after service discovery"):
                await client.connect()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class TestContextManager:
    @pytest.mark.asyncio
    async def test_async_context_manager_connects_and_disconnects(self):
        """async with RheemBLEClient(...) must connect on enter, disconnect on exit."""
        mock_bleak = _make_mock_client()

        with _patch_establish(return_value=mock_bleak):
            async with RheemBLEClient("AA:BB:CC:DD:EE:FF") as client:
                assert client._client is mock_bleak

        mock_bleak.disconnect.assert_awaited()


# ---------------------------------------------------------------------------
# Response collection
# ---------------------------------------------------------------------------

class TestSendAndReceive:
    @pytest.mark.asyncio
    async def test_notification_during_write_returns_immediately(self):
        """A full response delivered inside the write must not wait out the timeout."""
        payload = _ieee_response()
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF", timeout=5.0)
        client._write_uuid = NUS_TX_UUID

        async def write_gatt_char(_uuid, _packet, response=False):
            client._notification_handler(0, bytearray(payload))

        mock_bleak = AsyncMock()
        mock_bleak.write_gatt_char = write_gatt_char
        client._client = mock_bleak

        loop = asyncio.get_running_loop()
        started = loop.time()
        data = await client._send_and_receive(b"\x00" * 28)
        elapsed = loop.time() - started

        assert data == payload
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_split_notification_waits_for_the_rest(self):
        """A partial packet waits for the remaining bytes, not the full timeout."""
        payload = _ieee_response()
        first, second = payload[:10], payload[10:]
        client = RheemBLEClient("AA:BB:CC:DD:EE:FF", timeout=5.0)
        client._write_uuid = NUS_TX_UUID

        async def write_gatt_char(_uuid, _packet, response=False):
            client._notification_handler(0, bytearray(first))

            async def send_rest():
                await asyncio.sleep(0.05)
                client._notification_handler(0, bytearray(second))

            asyncio.create_task(send_rest())

        mock_bleak = AsyncMock()
        mock_bleak.write_gatt_char = write_gatt_char
        client._client = mock_bleak

        loop = asyncio.get_running_loop()
        started = loop.time()
        data = await client._send_and_receive(b"\x00" * 28)
        elapsed = loop.time() - started

        assert data == payload
        assert elapsed < 1.0
