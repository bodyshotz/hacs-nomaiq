# NomaIQ Home Assistant Integration

Local Home Assistant custom integration for **NomaIQ / Noma Smart Home** devices that communicate through the **Ayla IoT Cloud**.

This project expands support beyond the community-maintained integration to include additional NomaIQ devices such as the **AY028MHA1 Dehumidifier**, alongside the existing **garage door opener** and **smart light switches**.

> ⚠️ This integration is unofficial and not affiliated with Noma, Ayla, or Canadian Tire.

---

## ✨ Features

### ✔ NomaIQ Window AC (win ac/ AY028MHA1)
Supported controls and sensors:

- Climate entity
  - Off
  - Cool
  - Dry
  - Fan only
  - Target temperature
  - Current ambient temperature
  - Fan speed: Low / Medium / High
  - Presets: Eco / Boost / Sleep
- Power switch
- Display dimmer switch
- Mode select
- Fan speed select
- Filter alert
- Sensor fault diagnostics
- Mechanical fault diagnostics
- Ambient temperature sensor
- Internal coil temperature sensor, when exposed
- Wi-Fi RSSI diagnostic sensor

All values update using the Ayla Cloud API.


---

### ✔ NomaIQ Dehumidifier (AY028MHA1)
Full support for the common NomaIQ dehumidifier, including:

- 🔌 **Power control** (On / Off)
- 💧 **Target humidity setpoint**
- 🌡️ **Temperature sensor**
- 💦 **Current humidity sensor**
- 🪣 **Bucket full sensor**
- 💨 **Fan speed selection**
  - Low  
  - High
- 🔧 **Mode selection**
  - Auto  
  - Continuous  
  - Manual / Custom (if supported)
- ⚠️ **Error reporting**
- 🌐 **Online / offline device state**

All values update using the Ayla Cloud API.

---

### ✔ NomaIQ Smart Garage Door
Supports the cloud-based NomaIQ Garage Door Controller:

- 🚪 Open / close control  
- 📡 Door status sensor  
- 📶 Signal strength and other telemetry (varies by model)

---

### ✔ NomaIQ Smart Light Switches / Plug
Supports the basic NomaIQ lighting devices:

- 💡 On / Off toggle  
- 📊 Additional telemetry when exposed by Ayla

---

## 🔧 Installation

### Manual Installation
1. Download this repository as a ZIP.  
2. Extract it to:

```
/config/custom_components/nomaiq/
```

3. Restart Home Assistant.  
4. Add the integration through:  
**Settings → Devices & Services → Add Integration → NomaIQ**

---

## 🔑 Configuration

You will need:

- 📧 **Email** used in the NomaIQ mobile app  
- 🔒 **Password**  
- Devices already registered in the official app  
- Internet access for Ayla Cloud API communication  

---

## 🚧 Known Limitations

- 🌐 Cloud-only (no local control).  
- ⏱️ Polling frequency limited to avoid API rate limits.  
- 🧪 Some devices not fully documented; testing contributions are helpful.  

## Contributions

Contributions are welcome!
