from __future__ import annotations

"""Base entity helpers for NomaIQ platforms."""

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .devices import build_device_info, device_dsn, rebind_device


class NomaIQEntity(CoordinatorEntity):
    """Base class that keeps Ayla device references fresh."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Any,
        device: Any,
        name: str | None,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._dsn = device_dsn(device)

        self._attr_name = name
        self._attr_unique_id = f"{self._dsn}_{unique_suffix}"
        self._attr_device_info = build_device_info(device)

    @property
    def available(self) -> bool:
        return self._device is not None

    def _rebind_device(self) -> None:
        device = rebind_device(self.coordinator, self._dsn)
        if device is not None:
            self._device = device
            self._attr_device_info = build_device_info(device)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._rebind_device()
        self.async_write_ha_state()
