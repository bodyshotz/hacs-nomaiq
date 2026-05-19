from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .devices import is_dehumidifier, property_exists
from .entity import NomaIQEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = []

    for device in coordinator.data:
        if is_dehumidifier(device) and property_exists(device, "humidity"):
            entities.append(TargetHumidityNumber(coordinator, device))

    async_add_entities(entities)


class TargetHumidityNumber(NomaIQEntity, NumberEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Target Humidity", "target_humidity")
        self._attr_native_min_value = 30
        self._attr_native_max_value = 80
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> int | None:
        return self._device.get_property_value("humidity")

    async def async_set_native_value(self, value: float) -> None:
        await self._device.async_set_property_value("humidity", int(value))
        await self.coordinator.async_request_refresh()
