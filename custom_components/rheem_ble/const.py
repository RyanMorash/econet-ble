"""Constants for the Rheem HVAC BLE integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
)

DOMAIN = "rheem_ble"
DEFAULT_SCAN_INTERVAL = 60
SCAN_DURATION = 10
DEVICE_NAME_PREFIX = "EcoNet-"
CONF_MAC_ADDRESS = "mac_address"
CONF_DEVICE = "device"


@dataclass(frozen=True)
class RheemSensorMetadata:
    """Metadata for a Rheem sensor entity."""

    command: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    native_unit_of_measurement: str | None = None
    entity_category: EntityCategory | None = None
    icon: str | None = None


@dataclass(frozen=True)
class RheemBinarySensorMetadata:
    """Metadata for a Rheem binary sensor entity."""

    command: str
    device_class: BinarySensorDeviceClass | None = None
    entity_category: EntityCategory | None = None
    icon: str | None = None


# --- Sensor descriptions keyed by command name ---

SENSOR_DESCRIPTIONS: dict[str, RheemSensorMetadata] = {
    # Temperature sensors (°F)
    "SAT_TEMP": RheemSensorMetadata(
        command="SAT_TEMP",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "RAT_TEMP": RheemSensorMetadata(
        command="RAT_TEMP",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "OAT_TEMP": RheemSensorMetadata(
        command="OAT_TEMP",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMPSUCT": RheemSensorMetadata(
        command="TEMPSUCT",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_SST": RheemSensorMetadata(
        command="TEMP_SST",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "HTEXOTMP": RheemSensorMetadata(
        command="HTEXOTMP",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_OAT": RheemSensorMetadata(
        command="TEMP_OAT",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_OLT": RheemSensorMetadata(
        command="TEMP_OLT",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_CPT": RheemSensorMetadata(
        command="TEMP_CPT",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_SLT": RheemSensorMetadata(
        command="TEMP_SLT",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_OST": RheemSensorMetadata(
        command="TEMP_OST",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMPCOIL": RheemSensorMetadata(
        command="TEMPCOIL",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "TEMP_DIS": RheemSensorMetadata(
        command="TEMP_DIS",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "IDU_SUCT": RheemSensorMetadata(
        command="IDU_SUCT",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    "IDU__SST": RheemSensorMetadata(
        command="IDU__SST",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    # STATIC_P is duct static air pressure in inches of water column (inH₂O),
    # not PSI. Confirmed from Android app string resource unit_static_pressure="H2O
    # and live readings (typical 0.1–1.0 inH₂O, device max 20).
    "STATIC_P": RheemSensorMetadata(
        command="STATIC_P",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.INH2O,
    ),
    "PRES_SUC": RheemSensorMetadata(
        command="PRES_SUC",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.PSI,
    ),
    "PRESSUCG": RheemSensorMetadata(
        command="PRESSUCG",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.PSI,
    ),
    "PRESLIQG": RheemSensorMetadata(
        command="PRESLIQG",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.PSI,
    ),
    "PRES_LIQ": RheemSensorMetadata(
        command="PRES_LIQ",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.PSI,
    ),
    "IDU_SUCP": RheemSensorMetadata(
        command="IDU_SUCP",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.PSI,
    ),
    # Speed/RPM sensors
    "RPM_CURR": RheemSensorMetadata(
        command="RPM_CURR",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        icon="mdi:fan",
    ),
    "ODFANRPM": RheemSensorMetadata(
        command="ODFANRPM",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        icon="mdi:fan",
    ),
    "ISCSPEED": RheemSensorMetadata(
        command="ISCSPEED",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        icon="mdi:fan",
    ),
    "INVSPEED": RheemSensorMetadata(
        command="INVSPEED",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        icon="mdi:fan",
    ),
    # Airflow (CFM)
    "CFM_CMND": RheemSensorMetadata(
        command="CFM_CMND",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="CFM",
        icon="mdi:air-filter",
    ),
    "CFM_CURR": RheemSensorMetadata(
        command="CFM_CURR",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="CFM",
        icon="mdi:air-filter",
    ),
    "ELECDCFM": RheemSensorMetadata(
        command="ELECDCFM",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="CFM",
        icon="mdi:air-filter",
    ),
    "EMIDDCFM": RheemSensorMetadata(
        command="EMIDDCFM",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="CFM",
        icon="mdi:air-filter",
    ),
    "ELOWDCFM": RheemSensorMetadata(
        command="ELOWDCFM",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="CFM",
        icon="mdi:air-filter",
    ),
    # Electrical
    "ISACINPV": RheemSensorMetadata(
        command="ISACINPV",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    "ISACINPC": RheemSensorMetadata(
        command="ISACINPC",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    "IS_COMPC": RheemSensorMetadata(
        command="IS_COMPC",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    "C_MAXCUR": RheemSensorMetadata(
        command="C_MAXCUR",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    # Percentage
    "PRCNTCAP": RheemSensorMetadata(
        command="PRCNTCAP",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gauge",
    ),
    "STG1DRIV": RheemSensorMetadata(
        command="STG1DRIV",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gauge",
    ),
    "STG2DRIV": RheemSensorMetadata(
        command="STG2DRIV",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:gauge",
    ),
    # Superheat / Subcooling (temperature delta, °F)
    "EXVSUPER": RheemSensorMetadata(
        command="EXVSUPER",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:thermometer-lines",
    ),
    "SUB_COOL": RheemSensorMetadata(
        command="SUB_COOL",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:thermometer-lines",
    ),
    "IDUEXVSH": RheemSensorMetadata(
        command="IDUEXVSH",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        icon="mdi:thermometer-lines",
    ),
    # EXV position (steps)
    "EXACTUAL": RheemSensorMetadata(
        command="EXACTUAL",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="steps",
        icon="mdi:valve",
    ),
    "IDUEVPOS": RheemSensorMetadata(
        command="IDUEVPOS",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="steps",
        icon="mdi:valve",
    ),
    # Timer
    "LOCKTIMR": RheemSensorMetadata(
        command="LOCKTIMR",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer-lock-outline",
    ),
    # Flame strength
    "STRENGT2": RheemSensorMetadata(
        command="STRENGT2",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire",
    ),
    # Text / enum sensors (no device_class, no state_class)
    "HVACMODE": RheemSensorMetadata(command="HVACMODE", icon="mdi:hvac"),
    "INDSTATE": RheemSensorMetadata(command="INDSTATE", icon="mdi:fan"),
    "JAG_MODE": RheemSensorMetadata(command="JAG_MODE"),
    "ECONTROL": RheemSensorMetadata(command="ECONTROL"),
    "VSHP_CMD": RheemSensorMetadata(command="VSHP_CMD"),
    "ALARMS": RheemSensorMetadata(command="ALARMS", icon="mdi:alert-circle"),
    "ALERTS": RheemSensorMetadata(command="ALERTS", icon="mdi:alert"),
    "HTR_SIZE": RheemSensorMetadata(command="HTR_SIZE"),
    "U__INPUT": RheemSensorMetadata(command="U__INPUT"),
    # Diagnostic sensors
    "SERIAL_N": RheemSensorMetadata(
        command="SERIAL_N",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
    ),
    "SW_VERSN": RheemSensorMetadata(
        command="SW_VERSN",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:information-outline",
    ),
    "SW_VERSN_BLE": RheemSensorMetadata(
        command="SW_VERSN_BLE",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:bluetooth",
    ),
    "MDPRTNUM": RheemSensorMetadata(
        command="MDPRTNUM",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:card-bulleted-outline",
    ),
    "CDPRTNUM": RheemSensorMetadata(
        command="CDPRTNUM",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:card-bulleted-outline",
    ),
    "CPPRTNUM": RheemSensorMetadata(
        command="CPPRTNUM",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:card-bulleted-outline",
    ),
    "FNPRTNUM": RheemSensorMetadata(
        command="FNPRTNUM",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:card-bulleted-outline",
    ),
}


# --- Binary sensor descriptions keyed by command name ---

BINARY_SENSOR_DESCRIPTIONS: dict[str, RheemBinarySensorMetadata] = {
    "FLAMEPRS": RheemBinarySensorMetadata(
        command="FLAMEPRS",
        icon="mdi:fire",
    ),
    "GASSTATE": RheemBinarySensorMetadata(
        command="GASSTATE",
        icon="mdi:gas-burner",
    ),
    "ROLL_OUT": RheemBinarySensorMetadata(
        command="ROLL_OUT",
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    "WATRTRIP": RheemBinarySensorMetadata(
        command="WATRTRIP",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    "HT1_RELY": RheemBinarySensorMetadata(
        command="HT1_RELY",
        icon="mdi:electric-switch",
    ),
    "HT2_RELY": RheemBinarySensorMetadata(
        command="HT2_RELY",
        icon="mdi:electric-switch",
    ),
    "CONDENSE": RheemBinarySensorMetadata(
        command="CONDENSE",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    "G_DISCIN": RheemBinarySensorMetadata(
        command="G_DISCIN",
        icon="mdi:electric-switch",
    ),
    "AUX1_DIN": RheemBinarySensorMetadata(
        command="AUX1_DIN",
        icon="mdi:electric-switch",
    ),
    "AUX2_DIN": RheemBinarySensorMetadata(
        command="AUX2_DIN",
        icon="mdi:electric-switch",
    ),
    "AUX__DIN": RheemBinarySensorMetadata(
        command="AUX__DIN",
        icon="mdi:electric-switch",
    ),
    "W1DISCIN": RheemBinarySensorMetadata(
        command="W1DISCIN",
        icon="mdi:electric-switch",
    ),
    "W2DISCIN": RheemBinarySensorMetadata(
        command="W2DISCIN",
        icon="mdi:electric-switch",
    ),
    "Y1DISCIN": RheemBinarySensorMetadata(
        command="Y1DISCIN",
        icon="mdi:electric-switch",
    ),
    "Y2DISCIN": RheemBinarySensorMetadata(
        command="Y2DISCIN",
        icon="mdi:electric-switch",
    ),
    "INDUCELP": RheemBinarySensorMetadata(
        command="INDUCELP",
        icon="mdi:fan-alert",
    ),
    "INDUCEHP": RheemBinarySensorMetadata(
        command="INDUCEHP",
        icon="mdi:fan-alert",
    ),
}
