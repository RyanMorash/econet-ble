"""Tests for the wire-protocol layer: CRC, packet building, response parsing."""
import struct
import os
import importlib.util
import pytest

_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "rheem_ble", "rheem_ble.py"
)
_spec = importlib.util.spec_from_file_location("cc_rheem_ble", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

calc_crc = _mod.calc_crc
build_read_packet = _mod.build_read_packet
parse_response = _mod.parse_response
encode_command_name = _mod.encode_command_name
BOARD_ADDR_FURNACE = _mod.BOARD_ADDR_FURNACE
BOARD_ADDR_HWH = _mod.BOARD_ADDR_HWH
EQUIPMENT_BOARD_ADDR = _mod.EQUIPMENT_BOARD_ADDR
EquipmentType = _mod.EquipmentType
DATA_TYPE_IEEE = _mod.DATA_TYPE_IEEE
DATA_TYPE_TEXT = _mod.DATA_TYPE_TEXT
DATA_TYPE_ENUMERATED_TEXT = _mod.DATA_TYPE_ENUMERATED_TEXT
DATA_TYPE_BYTE_STREAM = _mod.DATA_TYPE_BYTE_STREAM
DATA_TYPE_OBJ_NOT_FOUND = _mod.DATA_TYPE_OBJ_NOT_FOUND


# ---------------------------------------------------------------------------
# CRC
# ---------------------------------------------------------------------------

class TestCalcCrc:
    def test_empty_packet_returns_zeros(self):
        assert calc_crc(b"") == (0, 0)

    def test_single_zero_byte(self):
        c1, c2 = calc_crc(b"\x00")
        assert isinstance(c1, int) and isinstance(c2, int)
        assert 0 <= c1 <= 255 and 0 <= c2 <= 255

    def test_known_packet_crc(self):
        # Build a packet and verify the last two bytes satisfy a round-trip:
        # appending the CRC bytes and recalculating should give (0, 0) if the
        # algorithm were self-checking — but here we just check idempotency.
        pkt = build_read_packet("HVACMODE", BOARD_ADDR_FURNACE)
        c1, c2 = calc_crc(pkt[:-2])
        assert pkt[-2] == c1
        assert pkt[-1] == c2

    def test_crc_changes_with_payload(self):
        crc_a = calc_crc(b"\x01\x02\x03")
        crc_b = calc_crc(b"\x01\x02\x04")
        assert crc_a != crc_b


# ---------------------------------------------------------------------------
# Packet building
# ---------------------------------------------------------------------------

class TestEncodeCommandName:
    def test_short_name_null_padded(self):
        result = encode_command_name("HI")
        assert result == b"HI\x00\x00\x00\x00\x00\x00"

    def test_exactly_8_chars(self):
        result = encode_command_name("HVACMODE")
        assert result == b"HVACMODE"

    def test_truncated_to_8(self):
        result = encode_command_name("TOOLONGNAME")
        assert len(result) == 8
        assert result == b"TOOLONGN"


class TestBuildReadPacket:
    def test_packet_is_28_bytes(self):
        pkt = build_read_packet("HVACMODE", BOARD_ADDR_FURNACE)
        assert len(pkt) == 28

    def test_packet_starts_with_board_address(self):
        pkt = build_read_packet("HVACMODE", BOARD_ADDR_FURNACE)
        assert pkt[:4] == BOARD_ADDR_FURNACE

    def test_read_opcode_at_byte_13(self):
        pkt = build_read_packet("HVACMODE", BOARD_ADDR_FURNACE)
        assert pkt[13] == 0x1E

    def test_command_name_at_bytes_18_to_25(self):
        pkt = build_read_packet("HVACMODE", BOARD_ADDR_FURNACE)
        assert pkt[18:26] == b"HVACMODE"

    def test_different_commands_produce_different_packets(self):
        p1 = build_read_packet("HVACMODE", BOARD_ADDR_FURNACE)
        p2 = build_read_packet("CFM_CMND", BOARD_ADDR_FURNACE)
        assert p1 != p2

    def test_mwh_uses_water_heater_board(self):
        """MWH reads go to the water-heater board, not the outdoor unit."""
        assert EQUIPMENT_BOARD_ADDR[EquipmentType.MWH] == BOARD_ADDR_HWH
        packet = build_read_packet("WHTRSETP", EQUIPMENT_BOARD_ADDR[EquipmentType.MWH])
        assert packet[:4] == BOARD_ADDR_HWH


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _make_header(data_len: int = 12) -> bytearray:
    """Build a minimal 14-byte response header."""
    hdr = bytearray(14)
    hdr[10] = data_len & 0xFF
    return hdr


def _make_ieee_response(value: float) -> bytes:
    """29-byte IEEE response containing *value* at bytes 25-28."""
    buf = bytearray(29)
    buf[10] = 15  # data_len
    buf[14] = DATA_TYPE_IEEE
    buf[17:21] = struct.pack(">f", 0.0)   # min
    buf[21:25] = struct.pack(">f", 100.0) # max
    buf[25:29] = struct.pack(">f", value)
    return bytes(buf)


class TestParseResponse:
    def test_too_short_returns_error(self):
        result = parse_response(b"\x00" * 10, "HVACMODE")
        assert result.data_type == "error"
        assert "too short" in result.error

    def test_ieee_value_parsed_correctly(self):
        data = _make_ieee_response(72.5)
        result = parse_response(data, "SAT_TEMP")
        assert result.data_type == "ieee"
        assert abs(result.value - 72.5) < 0.01

    def test_ieee_min_max_parsed(self):
        data = _make_ieee_response(50.0)
        result = parse_response(data, "SAT_TEMP")
        assert result.min_value == pytest.approx(0.0)
        assert result.max_value == pytest.approx(100.0)

    def test_text_response(self):
        buf = bytearray(40)
        text = b"HEATING\x00"
        buf[10] = len(text) + 12
        buf[14] = DATA_TYPE_TEXT
        buf[25:25 + len(text)] = text
        result = parse_response(bytes(buf), "HVACMODE")
        assert result.data_type == "text"
        assert result.value == "HEATING"

    def test_enum_text_response(self):
        buf = bytearray(40)
        label = b"ON\x00"
        buf[10] = len(label) + 14
        buf[14] = DATA_TYPE_ENUMERATED_TEXT
        buf[27:27 + len(label)] = label
        result = parse_response(bytes(buf), "GASSTATE")
        assert result.data_type == "enum_text"
        assert result.value == "ON"

    def test_byte_stream_response(self):
        buf = bytearray(30)
        payload = b"\xDE\xAD\xBE\xEF"
        buf[10] = len(payload) + 12
        buf[14] = DATA_TYPE_BYTE_STREAM
        buf[25:25 + len(payload)] = payload
        result = parse_response(bytes(buf), "ALARMS")
        assert result.data_type == "byte_stream"
        assert result.value == payload

    def test_obj_not_found_error(self):
        buf = bytearray(15)
        buf[14] = DATA_TYPE_OBJ_NOT_FOUND
        result = parse_response(bytes(buf), "UNKNOWN")
        assert result.data_type == "error"
        assert "OBJ_NOT_FOUND" in result.error

    def test_unknown_dtype_returns_error(self):
        buf = bytearray(15)
        buf[14] = 0xFF  # unrecognised type
        result = parse_response(bytes(buf), "TEST")
        assert result.data_type == "error"
