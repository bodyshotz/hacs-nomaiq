from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .devices import is_dehumidifier, is_window_ac, property_exists
from .entity import NomaIQEntity

_LOGGER = logging.getLogger(__name__)

DEHUMIDIFIER_FAN_SPEED_MAP = {
    "Auto": "Smart",
    "Low": "Low",
    "High": "High",
}
DEHUMIDIFIER_AYLA_TO_HASS_FAN = {
    value: key for key, value in DEHUMIDIFIER_FAN_SPEED_MAP.items()
}

DEHUMIDIFIER_MODE_MAP = {
    "Manual": "Normal",
    "Continuous": "Persistent",
    "Auto Dry": "Auto",
}
DEHUMIDIFIER_AYLA_TO_HASS_MODE = {
    value: key for key, value in DEHUMIDIFIER_MODE_MAP.items()
}

WINDOW_AC_FAN_SPEED_MAP = {
    "Low": "Low",
    "Medium": "Med",
    "High": "High",
}
WINDOW_AC_AYLA_TO_HASS_FAN = {
    value: key for key, value in WINDOW_AC_FAN_SPEED_MAP.items()
}

WINDOW_AC_MODE_MAP = {
    "Cool": "Cool",
    "Eco": "Eco",
    "Dry": "Dry",
    "Fan": "Fan",
}
WINDOW_AC_AYLA_TO_HASS_MODE = {
    value: key for key, value in WINDOW_AC_MODE_MAP.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SelectEntity] = []

    for device in coordinator.data:
        if is_window_ac(device):
            if property_exists(device, "mode"):
                entities.append(WindowACModeSelect(coordinator, device))
            if property_exists(device, "fan_speed"):
                entities.append(WindowACFanSpeedSelect(coordinator, device))

        elif is_dehumidifier(device):
            if property_exists(device, "mode"):
                entities.append(DehumidifierModeSelect(coordinator, device))
            if property_exists(device, "fan_speed"):
                entities.append(DehumidifierFanSpeedSelect(coordinator, device))

    async_add_entities(entities)


class DehumidifierModeSelect(NomaIQEntity, SelectEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Mode", "mode_select")
        self._attr_options = list(DEHUMIDIFIER_MODE_MAP.keys())

    @property
    def current_option(self) -> str:
        raw_mode = self._device.get_property_value("mode")
        return DEHUMIDIFIER_AYLA_TO_HASS_MODE.get(raw_mode, "Manual")

    async def async_select_option(self, option: str) -> None:
        if option not in DEHUMIDIFIER_MODE_MAP:
            return

        _LOGGER.debug(
            "Setting dehumidifier mode to %s (%s)",
            option,
            DEHUMIDIFIER_MODE_MAP[option],
        )
        await self._device.async_set_property_value("mode", DEHUMIDIFIER_MODE_MAP[option])
        await self.coordinator.async_request_refresh()


class DehumidifierFanSpeedSelect(NomaIQEntity, SelectEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Fan Speed", "fan_speed_select")
        self._attr_options = list(DEHUMIDIFIER_FAN_SPEED_MAP.keys())

    @property
    def current_option(self) -> str:
        raw_speed = self._device.get_property_value("fan_speed")
        return DEHUMIDIFIER_AYLA_TO_HASS_FAN.get(raw_speed, "Auto")

    async def async_select_option(self, option: str) -> None:
        if option not in DEHUMIDIFIER_FAN_SPEED_MAP:
            return

        _LOGGER.debug(
            "Setting dehumidifier fan speed to %s (%s)",
            option,
            DEHUMIDIFIER_FAN_SPEED_MAP[option],
        )
        await self._device.async_set_property_value(
            "fan_speed", DEHUMIDIFIER_FAN_SPEED_MAP[option]
        )
        await self.coordinator.async_request_refresh()


class WindowACModeSelect(NomaIQEntity, SelectEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Mode", "mode_select")
        self._attr_options = list(WINDOW_AC_MODE_MAP.keys())

    @property
    def current_option(self) -> str | None:
        raw_mode = self._device.get_property_value("mode")
        return WINDOW_AC_AYLA_TO_HASS_MODE.get(raw_mode, raw_mode)

    async def async_select_option(self, option: str) -> None:
        if option not in WINDOW_AC_MODE_MAP:
            return

        await self._device.async_set_property_value("power", 1)
        await self._device.async_set_property_value("mode", WINDOW_AC_MODE_MAP[option])
        await self.coordinator.async_request_refresh()


class WindowACFanSpeedSelect(NomaIQEntity, SelectEntity):
    def __init__(self, coordinator, device):
        super().__init__(coordinator, device, "Fan Speed", "fan_speed_select")
        self._attr_options = list(WINDOW_AC_FAN_SPEED_MAP.keys())

    @property
    def current_option(self) -> str | None:
        raw_speed = self._device.get_property_value("fan_speed")
        return WINDOW_AC_AYLA_TO_HASS_FAN.get(raw_speed, raw_speed)

    async def async_select_option(self, option: str) -> None:
        if option not in WINDOW_AC_FAN_SPEED_MAP:
            return

        await self._device.async_set_property_value(
            "fan_speed", WINDOW_AC_FAN_SPEED_MAP[option]
        )
        await self.coordinator.async_request_refresh()
