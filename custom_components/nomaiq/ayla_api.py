"""Small wrapper around ayla_iot_unofficial for NomaIQ."""

from __future__ import annotations

import contextlib

import ayla_iot_unofficial


class AylaApi:
    """Wrapper for the Ayla unofficial API client."""

    def __init__(self, username, password, client_id, client_secret, session=None):
        self._api = ayla_iot_unofficial.new_ayla_api(
            username,
            password,
            client_id,
            client_secret,
            websession=session,
        )

    async def async_login(self):
        """Sign in to Ayla."""
        await self._api.async_sign_in()

    def check_auth(self):
        """Raise if the current auth token is invalid/expired."""
        self._api.check_auth()

    async def async_refresh_auth(self):
        """Refresh Ayla auth tokens."""
        await self._api.async_refresh_auth()

    async def async_get_devices(self):
        """Return Ayla devices."""
        return await self._api.async_get_devices()

    async def async_logout(self):
        """Best-effort cleanup of the underlying web session, if present."""
        # The upstream library does not consistently expose a logout method.
        logout = getattr(self._api, "async_logout", None)
        if logout is not None:
            with contextlib.suppress(Exception):
                await logout()

        websession = getattr(self._api, "websession", None)
        if websession is not None and not getattr(websession, "closed", True):
            with contextlib.suppress(Exception):
                await websession.close()
