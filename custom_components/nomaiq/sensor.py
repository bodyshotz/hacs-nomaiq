from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .devices import is_dehumidifier, is_window_ac, property_exists
from .entity import NomaIQEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for device in coordinator.data:
        if is_window_ac(device):
            if property_exists(device, "ambient_temp"):
                entities.append(WindowACAmbientTemperatureSensor(coordinator, device))
            if property_exists(device, "internal_coil_temp"):
                entities.append(WindowACInternalCoilTemperatureSensor(coordinator, device))
            if property_exists(device, "wifi_rssi"):
                entities.append(WifiRssiSensor(coordinator, device))

        elif is_dehumidifier(device):
            if property_exists(device, "indoor_humidity"):
                entities.append(IndoorHumiditySensor(coordinator, device))
            if property_exists(device, "wifi_rssi"):
                entities.append(WifiRssiSensor(coordinator, device))

    async_add_entities(entities)


class IndoorHumiditySensor(NomaIQEntity, SensorEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Indoor Humidity", "indoor_humidity")

    @property
    def native_value(self) -> int | None:
        return self._device.get_property_value("indoor_humidity")


class WindowACAmbientTemperatureSensor(NomaIQEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Ambient Temperature", "ambient_temperature")

    @property
    def native_unit_of_measurement(self) -> str:
        if self._device.get_property_value("temp_unit") == "C":
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_value(self) -> int | None:
        return self._device.get_property_value("ambient_temp")


class WindowACInternalCoilTemperatureSensor(NomaIQEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Internal Coil Temperature", "internal_coil_temperature")

    @property
    def native_unit_of_measurement(self) -> str:
        if self._device.get_property_value("temp_unit") == "F":
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> int | None:
        return self._device.get_property_value("internal_coil_temp")


class WifiRssiSensor(NomaIQEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Wi-Fi RSSI", "wifi_rssi")

    @property
    def native_value(self) -> int | None:
        return self._device.get_property_value("wifi_rssi")
