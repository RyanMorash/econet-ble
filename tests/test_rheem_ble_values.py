"""Tests for advertisement, poll timing, and command value conversion."""
import os
import importlib.util

_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "rheem_ble", "rheem_ble.py"
)
_spec = importlib.util.spec_from_file_location("cc_rheem_ble_values", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

CommandResult = _mod.CommandResult
binary_is_on = _mod.binary_is_on
commands_from_advertisement = _mod.commands_from_advertisement
poll_is_due = _mod.poll_is_due
redact_address = _mod.redact_address
sensor_native_value = _mod.sensor_native_value


class TestAdvertisementAndPollTiming:
    def test_advertisement_carries_no_commands(self):
        assert commands_from_advertisement() == {}

    def test_poll_is_due_before_the_first_attempt(self):
        assert poll_is_due(None, 60) is True

    def test_poll_is_not_due_inside_the_interval(self):
        assert poll_is_due(59.9, 60) is False

    def test_poll_is_due_at_the_interval(self):
        assert poll_is_due(60, 60) is True

    def test_address_mask_keeps_the_ends_of_a_mac(self):
        assert redact_address("AA:BB:CC:DD:EE:FF") == "AA:B***E:FF"

    def test_short_address_is_fully_masked(self):
        assert redact_address("AA:BB") == "**REDACTED**"


class TestSensorNativeValue:
    def test_numeric_value_is_rounded(self):
        result = CommandResult("SAT_TEMP", "ieee", value=72.54)
        assert sensor_native_value(result, numeric=True) == 72.5

    def test_numeric_sensor_drops_unexpected_text(self):
        result = CommandResult("HTEXOTMP", "text", value="Closed")
        assert sensor_native_value(result, numeric=True) is None

    def test_text_sensor_keeps_text(self):
        result = CommandResult("HVACMODE", "text", value=" HEATING ")
        assert sensor_native_value(result, numeric=False) == "HEATING"

    def test_error_has_no_value(self):
        result = CommandResult("SAT_TEMP", "error", error="OBJ_NOT_FOUND")
        assert sensor_native_value(result, numeric=True) is None


class TestBinaryIsOn:
    def test_numeric_one_is_on(self):
        result = CommandResult("FLAMEPRS", "ieee", value=1.0)
        assert binary_is_on(result) is True

    def test_numeric_zero_is_off(self):
        result = CommandResult("FLAMEPRS", "ieee", value=0.0)
        assert binary_is_on(result) is False

    def test_on_text_is_on(self):
        result = CommandResult("GASSTATE", "enum_text", value="on")
        assert binary_is_on(result) is True

    def test_off_text_is_off(self):
        result = CommandResult("GASSTATE", "text", value="Off")
        assert binary_is_on(result) is False

    def test_error_is_unknown(self):
        result = CommandResult("GASSTATE", "error", error="No response received")
        assert binary_is_on(result) is None
