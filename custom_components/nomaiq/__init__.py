from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ayla_api import AylaApi
from .const import CLIENT_ID, CLIENT_SECRET, DOMAIN, NORMAL_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    "switch",
    "number",
    "sensor",
    "select",
    "binary_sensor",
    "humidifier",
    "climate",
]


class NomaIQDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for polling Ayla-backed NOMA iQ devices."""

    def __init__(self, hass: HomeAssistant, api: AylaApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=NORMAL_UPDATE_INTERVAL),
        )
        self._api = api
        self._last_full_update = 0.0
        self._devices_in_transition: set[str] = set()
        self.devices_by_serial: dict[str, Any] = {}

    async def _async_update_data(self) -> list[Any]:
        try:
            try:
                self._api.check_auth()
            except Exception:
                await self._api.async_refresh_auth()

            fetched_devices = await self._api.async_get_devices()
            current_time = self.hass.loop.time()

            is_full_update = (
                self.update_interval.total_seconds() == NORMAL_UPDATE_INTERVAL
                or current_time - self._last_full_update >= NORMAL_UPDATE_INTERVAL
            )

            if is_full_update:
                for device in fetched_devices:
                    await device.async_update()
                    self.devices_by_serial[device.serial_number] = device

                self._last_full_update = current_time

            return list(self.devices_by_serial.values())

        except Exception as ex:
            raise UpdateFailed(f"Exception on getting NomaIQ states: {ex}") from ex


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    api = AylaApi(
        username=entry.data["username"],
        password=entry.data["password"],
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    await api.async_login()

    coordinator = NomaIQDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: NomaIQDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    await coordinator._api.async_logout()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
