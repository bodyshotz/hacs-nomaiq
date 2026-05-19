from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NomaIQDataUpdateCoordinator
from .const import DOMAIN
from .devices import is_dehumidifier, is_window_ac, property_exists
from .entity import NomaIQEntity

WINDOW_AC_SENSOR_FAULT_PROPS = (
    "int_temp_sensor_fail",
    "int_coil_temp_sensor_fail",
    "ext_coil_temp_sensor_fail",
    "int_pcb_eeprom_fail",
)

WINDOW_AC_MECHANICAL_FAULT_PROPS = (
    "int_fan_motor_fail",
    "ext_fan_motor_fail",
    "internal_drain_pump_fail",
    "int_anti_freeze_ol_prot",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    for device in coordinator.data:
        if is_window_ac(device):
            if property_exists(device, "filter_change_alarm"):
                entities.append(WindowACFilterAlertSensor(coordinator, device))

            if any(property_exists(device, prop) for prop in WINDOW_AC_SENSOR_FAULT_PROPS):
                entities.append(WindowACSensorFaultSensor(coordinator, device))

            if any(property_exists(device, prop) for prop in WINDOW_AC_MECHANICAL_FAULT_PROPS):
                entities.append(WindowACMechanicalFaultSensor(coordinator, device))

            continue

        if is_dehumidifier(device):
            if property_exists(device, "water_bucket_full"):
                entities.append(DehumidifierTankFullSensor(coordinator, device))

            if property_exists(device, "filter_clean_alarm"):
                entities.append(DehumidifierFilterAlertSensor(coordinator, device))

            if property_exists(device, "humidity_sensor_fault"):
                entities.append(DehumidifierSensorFaultSensor(coordinator, device))

    async_add_entities(entities)


class DehumidifierTankFullSensor(NomaIQEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.MOISTURE

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Tank Full", "tank_full")

    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value("water_bucket_full"))


class DehumidifierFilterAlertSensor(NomaIQEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Filter Alert", "filter_alert")

    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value("filter_clean_alarm"))


class DehumidifierSensorFaultSensor(NomaIQEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Sensor Fault", "sensor_fault")

    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value("humidity_sensor_fault"))


class WindowACFilterAlertSensor(NomaIQEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Filter Alert", "filter_alert")

    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value("filter_change_alarm"))


class WindowACSensorFaultSensor(NomaIQEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Sensor Fault", "sensor_fault")

    @property
    def is_on(self) -> bool:
        return any(
            bool(self._device.get_property_value(prop))
            for prop in WINDOW_AC_SENSOR_FAULT_PROPS
        )


class WindowACMechanicalFaultSensor(NomaIQEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Mechanical Fault", "mechanical_fault")

    @property
    def is_on(self) -> bool:
        return any(
            bool(self._device.get_property_value(prop))
            for prop in WINDOW_AC_MECHANICAL_FAULT_PROPS
        )
