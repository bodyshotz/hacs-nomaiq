from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NomaIQDataUpdateCoordinator
from .const import DOMAIN
from .devices import is_dehumidifier, is_window_ac, property_exists
from .entity import NomaIQEntity

DEHUMIDIFIER_SWITCHES = {
    "power": "Power",
}

WINDOW_AC_SWITCHES = {
    "power": "Power",
    "dimmer": "Display Dimmer",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []

    for device in coordinator.data:
        if is_window_ac(device):
            switch_types = WINDOW_AC_SWITCHES
        elif is_dehumidifier(device):
            switch_types = DEHUMIDIFIER_SWITCHES
        else:
            continue

        for prop, name in switch_types.items():
            if property_exists(device, prop):
                entities.append(NomaIQSwitch(coordinator, device, prop, name))

    async_add_entities(entities)


class NomaIQSwitch(NomaIQEntity, SwitchEntity):
    def __init__(self, coordinator, device, prop: str, name: str) -> None:
        super().__init__(coordinator, device, name, f"{prop}_switch")
        self._prop = prop

    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value(self._prop))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.async_set_property_value(self._prop, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.async_set_property_value(self._prop, 0)
        await self.coordinator.async_request_refresh()
