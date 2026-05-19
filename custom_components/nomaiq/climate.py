from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NomaIQDataUpdateCoordinator
from .const import DOMAIN
from .devices import build_device_info, device_dsn, device_name, is_window_ac, rebind_device

_LOGGER = logging.getLogger(__name__)

AYLA_MODE_TO_HVAC = {
    "Cool": HVACMode.COOL,
    "Eco": HVACMode.COOL,
    "Dry": HVACMode.DRY,
    "Fan": HVACMode.FAN_ONLY,
}

HVAC_TO_AYLA_MODE = {
    HVACMode.COOL: "Cool",
    HVACMode.DRY: "Dry",
    HVACMode.FAN_ONLY: "Fan",
}

FAN_LOW = "low"
FAN_MEDIUM = "medium"
FAN_HIGH = "high"

HASS_TO_AYLA_FAN = {
    FAN_LOW: "Low",
    FAN_MEDIUM: "Med",
    FAN_HIGH: "High",
}

AYLA_TO_HASS_FAN = {value: key for key, value in HASS_TO_AYLA_FAN.items()}

PRESET_NONE = "none"
PRESET_ECO = "eco"
PRESET_BOOST = "boost"
PRESET_SLEEP = "sleep"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [NomaIQWindowAC(coordinator, device) for device in coordinator.data if is_window_ac(device)]
    )


class NomaIQWindowAC(CoordinatorEntity, ClimateEntity):
    """NOMA iQ window air conditioner."""

    _attr_has_entity_name = True
    _attr_name = None

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )

    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]

    _attr_fan_modes = [
        FAN_LOW,
        FAN_MEDIUM,
        FAN_HIGH,
    ]

    _attr_preset_modes = [
        PRESET_NONE,
        PRESET_ECO,
        PRESET_BOOST,
        PRESET_SLEEP,
    ]

    _attr_target_temperature_step = 1

    def __init__(self, coordinator: NomaIQDataUpdateCoordinator, device: Any) -> None:
        super().__init__(coordinator)
        self._device = device
        self._dsn = device_dsn(device)
        self._attr_unique_id = f"{self._dsn}_climate"
        self._attr_device_info = build_device_info(device)

    @property
    def available(self) -> bool:
        return self._device is not None and not bool(
            self._device.get_property_value("comms_fail")
        )

    @property
    def temperature_unit(self) -> str:
        if self._device.get_property_value("temp_unit") == "C":
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def min_temp(self) -> int:
        return 16 if self.temperature_unit == UnitOfTemperature.CELSIUS else 61

    @property
    def max_temp(self) -> int:
        return 31 if self.temperature_unit == UnitOfTemperature.CELSIUS else 88

    @property
    def current_temperature(self) -> int | None:
        return self._device.get_property_value("ambient_temp")

    @property
    def target_temperature(self) -> int | None:
        return self._device.get_property_value("target_temp")

    @property
    def hvac_mode(self) -> HVACMode:
        if not bool(self._device.get_property_value("power")):
            return HVACMode.OFF

        if bool(self._device.get_property_value("super")):
            return HVACMode.COOL

        return AYLA_MODE_TO_HVAC.get(
            self._device.get_property_value("mode"),
            HVACMode.COOL,
        )

    @property
    def fan_mode(self) -> str | None:
        raw_fan = self._device.get_property_value("fan_speed")
        return AYLA_TO_HASS_FAN.get(raw_fan, raw_fan)

    @property
    def preset_mode(self) -> str:
        if bool(self._device.get_property_value("super")):
            return PRESET_BOOST

        if bool(self._device.get_property_value("sleep")):
            return PRESET_SLEEP

        raw_mode = self._device.get_property_value("mode")
        energy_save = bool(self._device.get_property_value("energy_save"))

        if raw_mode == "Eco" or energy_save:
            return PRESET_ECO

        return PRESET_NONE

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set_property_safe("power", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_property_safe("power", False)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._set_property_safe("power", False)
            return

        ayla_mode = HVAC_TO_AYLA_MODE.get(hvac_mode)
        if ayla_mode is None:
            _LOGGER.warning("Unsupported HVAC mode requested for %s: %s", device_name(self._device), hvac_mode)
            return

        await self._set_property_safe("power", True)

        if hvac_mode == HVACMode.COOL:
            await self._set_property_safe("energy_save", False)
            await self._set_property_safe("super", False)

        await self._set_property_safe("mode", ayla_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self._set_property_safe("target_temp", int(round(temperature)))

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        ayla_fan = HASS_TO_AYLA_FAN.get(fan_mode, fan_mode)

        if ayla_fan not in {"Low", "Med", "High"}:
            _LOGGER.warning("Unsupported fan mode requested for %s: %s", device_name(self._device), fan_mode)
            return

        await self._set_property_safe("fan_speed", ayla_fan)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_ECO:
            await self._set_property_safe("power", True)
            await self._set_property_safe("super", False)
            await self._set_property_safe("sleep", False)
            await self._set_property_safe("mode", "Eco")
            await self._set_property_safe("energy_save", True)
            return

        if preset_mode == PRESET_BOOST:
            await self._set_property_safe("power", True)
            await self._set_property_safe("energy_save", False)
            await self._set_property_safe("sleep", False)
            await self._set_property_safe("super", True)
            return

        if preset_mode == PRESET_SLEEP:
            await self._set_property_safe("power", True)
            await self._set_property_safe("super", False)
            await self._set_property_safe("sleep", True)
            return

        if preset_mode == PRESET_NONE:
            await self._set_property_safe("super", False)
            await self._set_property_safe("sleep", False)
            await self._set_property_safe("energy_save", False)

            if self._device.get_property_value("mode") == "Eco":
                await self._set_property_safe("mode", "Cool")
            return

        _LOGGER.warning("Unsupported preset mode requested for %s: %s", device_name(self._device), preset_mode)

    async def _set_property_safe(self, property_name: str, value: Any) -> None:
        if property_name in {"power", "energy_save", "sleep", "super", "dimmer"}:
            value = 1 if value else 0

        try:
            await self._device.async_set_property_value(property_name, value)
        except Exception as ex:
            _LOGGER.error(
                "Failed to set NOMA iQ property %s=%s on %s: %s",
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

    @callback
    def _handle_coordinator_update(self) -> None:
        self._rebind_device()
        self.async_write_ha_state()
