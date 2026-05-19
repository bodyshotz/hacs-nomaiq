from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.humidifier import HumidifierEntity, HumidifierEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NomaIQDataUpdateCoordinator
from .const import DOMAIN
from .devices import build_device_info, device_dsn, device_name, is_dehumidifier, rebind_device

_LOGGER = logging.getLogger(__name__)

USER_MODES = ["Manual", "Continuous", "Auto Dry"]

MODE_MAP = {
    "Manual": "Normal",
    "Continuous": "Persistent",
    "Auto Dry": "Auto",
}
AYLA_TO_HASS_MODE = {value: key for key, value in MODE_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            NomaIQDehumidifier(coordinator, device)
            for device in coordinator.data
            if is_dehumidifier(device)
        ]
    )


class NomaIQDehumidifier(HumidifierEntity):
    """NOMA iQ dehumidifier."""

    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_min_humidity = 30
    _attr_max_humidity = 80
    _attr_available_modes = USER_MODES
    _attr_device_class = "dehumidifier"

    def __init__(self, coordinator: NomaIQDataUpdateCoordinator, device: Any) -> None:
        self.coordinator = coordinator
        self._device = device
        self._dsn = device_dsn(device)

        self._attr_has_entity_name = True
        self._attr_name = None
        self._attr_unique_id = f"{self._dsn}_humidifier"
        self._attr_device_info = build_device_info(device)

        coordinator.async_add_listener(self._handle_coordinator_update)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._device is not None

    @property
    def is_on(self) -> bool:
        return bool(self._device.get_property_value("power"))

    @property
    def current_humidity(self) -> int | None:
        return self._device.get_property_value("indoor_humidity")

    @property
    def target_humidity(self) -> int | None:
        return self._device.get_property_value("humidity")

    @property
    def mode(self) -> str:
        raw_mode = self._device.get_property_value("mode")
        return AYLA_TO_HASS_MODE.get(raw_mode, "Manual")

    async def async_set_humidity(self, humidity: int) -> None:
        await self._set_property_safe("humidity", humidity)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_property_safe("power", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_property_safe("power", False)

    async def async_set_mode(self, mode: str) -> None:
        ayla_mode = MODE_MAP.get(mode)
        if ayla_mode is not None:
            await self._set_property_safe("mode", ayla_mode)

    async def _set_property_safe(self, property_name: str, value: Any) -> None:
        if property_name == "power":
            value = 1 if value else 0

        try:
            await self._device.async_set_property_value(property_name, value)
        except Exception as ex:
            _LOGGER.error(
                "Failed to set NOMA iQ dehumidifier property %s=%s on %s: %s",
                property_name,
                value,
                device_name(self._device),
                ex,
            )
            return

        await self.coordinator.async_request_refresh()

    def _rebind_device(self) -> None:
        device = rebind_device(self.coordinator, self._dsn)
        if device is not None:
            self._device = device
            self._attr_device_info = build_device_info(device)

    def _handle_coordinator_update(self) -> None:
        self._rebind_device()
        self.async_write_ha_state()
