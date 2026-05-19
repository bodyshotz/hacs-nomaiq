from __future__ import annotations

"""Shared helpers for classifying and describing NomaIQ/Ayla devices.

NOMA iQ devices can expose overlapping Ayla model numbers even when the
physical appliance type is different. For example, a tested NOMA iQ window AC
reports ``_device_model_number == "AY028MHA1"``, which overlaps with the
originally supported dehumidifier, but it also reports ``_oem_model_number ==
"win-ac"`` and exposes AC-specific properties such as ``target_temp`` and
``ambient_temp``.

Platform files should use these helpers rather than checking Ayla model numbers
directly.
"""

from typing import Any

from .const import DOMAIN

DEHUMIDIFIER_MODEL = "AY028MHA1"
WINDOW_AC_OEM_MODEL = "win-ac"

AC_SIGNATURE_PROPERTIES = {
    "target_temp",
    "ambient_temp",
    "temp_unit",
    "temp_unit_display",
    "energy_save",
    "super",
    "dimmer",
    "filter_change_alarm",
}

DEHUMIDIFIER_SIGNATURE_PROPERTIES = {
    "humidity",
    "indoor_humidity",
    "water_bucket_full",
    "humidity_sensor_fault",
    "filter_clean_alarm",
}


def _first_attr(device: Any, *names: str) -> Any:
    """Return the first non-None attribute found on an Ayla device object."""
    for name in names:
        value = getattr(device, name, None)
        if value is not None:
            return value
    return None


def device_model(device: Any) -> str | None:
    """Return the Ayla model number exposed by the device object."""
    return _first_attr(
        device,
        "_device_model_number",
        "device_model_number",
        "_model_number",
        "model_number",
        "model",
    )


def oem_model(device: Any) -> str | None:
    """Return the OEM model identifier exposed by the device object."""
    return _first_attr(
        device,
        "_oem_model_number",
        "oem_model_number",
        "_oem_model",
        "oem_model",
    )


def device_dsn(device: Any) -> str:
    """Return a stable unique identifier for Home Assistant unique IDs."""
    return str(
        _first_attr(
            device,
            "_dsn",
            "dsn",
            "serial_number",
            "_serial_number",
            "_name",
            "name",
        )
        or "noma_iq_device"
    )


def device_name(device: Any) -> str:
    """Return the device name shown in Home Assistant."""
    return str(_first_attr(device, "_name", "name") or "NOMA iQ Device")


def property_names(device: Any) -> set[str]:
    """Return all known property names for a device.

    The Ayla library has exposed properties in a few slightly different shapes
    across versions, so this checks public and private dictionaries.
    """
    names: set[str] = set()

    for attr_name in (
        "properties_full",
        "property_values",
        "_properties_full",
        "_property_values",
    ):
        props = getattr(device, attr_name, None)

        if not isinstance(props, dict):
            continue

        names.update(str(key) for key in props.keys())

        for value in props.values():
            if isinstance(value, dict) and value.get("name") is not None:
                names.add(str(value["name"]))

    return names


def get_property(device: Any, prop: str, default: Any = None) -> Any:
    """Safely read a property value from an Ayla device."""
    try:
        value = device.get_property_value(prop)
    except Exception:
        return default

    return default if value is None else value


def property_exists(device: Any, prop: str) -> bool:
    """Return True if a property appears to exist on the device."""
    if prop in property_names(device):
        return True

    return get_property(device, prop) is not None


def _has_ac_signature(device: Any) -> bool:
    props = property_names(device)

    if "target_temp" in props and ("ambient_temp" in props or "temp_unit" in props):
        return True

    if len(AC_SIGNATURE_PROPERTIES.intersection(props)) >= 3:
        return True

    # Fallback for Ayla objects that do not expose populated property dicts.
    return property_exists(device, "target_temp") and (
        property_exists(device, "ambient_temp") or property_exists(device, "temp_unit")
    )


def _has_dehumidifier_signature(device: Any) -> bool:
    props = property_names(device)

    if "humidity" in props and "indoor_humidity" in props:
        return True

    if len(DEHUMIDIFIER_SIGNATURE_PROPERTIES.intersection(props)) >= 2:
        return True

    return property_exists(device, "humidity") and property_exists(
        device, "indoor_humidity"
    )


def is_window_ac(device: Any) -> bool:
    """Return True if this Ayla device is a supported NOMA iQ window AC."""
    if str(oem_model(device) or "").lower() == WINDOW_AC_OEM_MODEL:
        return True

    return _has_ac_signature(device)


def is_dehumidifier(device: Any) -> bool:
    """Return True if this Ayla device is a supported NOMA iQ dehumidifier."""
    if is_window_ac(device):
        return False

    if device_model(device) == DEHUMIDIFIER_MODEL:
        # Most known dehumidifiers use AY028MHA1. If properties are populated,
        # prefer a positive dehumidifier signature; otherwise preserve legacy
        # behaviour for this known model.
        props = property_names(device)
        return not props or _has_dehumidifier_signature(device)

    return False


def build_device_info(device: Any) -> dict[str, Any]:
    """Return device registry information for Home Assistant."""
    info: dict[str, Any] = {
        "identifiers": {(DOMAIN, device_dsn(device))},
        "name": device_name(device),
        "manufacturer": "NOMA iQ",
        "model": oem_model(device) or device_model(device),
    }

    sw_version = get_property(device, "version")
    if sw_version is not None:
        info["sw_version"] = str(sw_version)

    return info


def rebind_device(coordinator: Any, dsn: str) -> Any | None:
    """Find the latest device object for a DSN after coordinator refreshes."""
    for dev in getattr(coordinator, "data", []) or []:
        if device_dsn(dev) == dsn:
            return dev

    for dev in getattr(coordinator, "devices_by_serial", {}).values():
        if device_dsn(dev) == dsn:
            return dev

    return None
