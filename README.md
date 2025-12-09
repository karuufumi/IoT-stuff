# 🌱 IoT Sensor Gateway (Micro:bit → PC → Adafruit IO → Backend)

This project collects real-time sensor data from a BBC Micro:bit, sends it over USB serial to a Python IoT Gateway, which forwards values to Adafruit IO (MQTT) for dashboards and backend processing.

Windows-compatible. Micro:bit-compatible. Plug-and-play.

------------------------------------------------------------
📦 1. Project Overview
------------------------------------------------------------

Micro:bit (sensors)
    ↓ USB UART
PC Gateway (Python)
    ↓ MQTT
Adafruit IO
    ↓
Backend API (FastAPI / Express)

The Micro:bit sends temperature, humidity, and light in a strict packet format.
The PC reads packets, parses them, and publishes them to Adafruit IO feeds.

------------------------------------------------------------
🧩 2. Hardware Requirements
------------------------------------------------------------

- BBC Micro:bit V1 or V2
- Micro USB cable (data-capable)
- Windows PC or laptop
- Optional sensors (temperature, humidity, light)

------------------------------------------------------------
🔌 3. Connect Micro:bit to Windows
------------------------------------------------------------

1. Plug in Micro:bit via USB
2. Windows will auto-install drivers
3. A new drive appears named: MICROBIT

To find the COM port:
- Open Device Manager
- Expand "Ports (COM & LPT)"
- Look for:

    BBC micro:bit CMSIS-DAP (COM3)

Your COM number (COM3, COM4, etc.) is auto-detected by the gateway.

------------------------------------------------------------
🛠️ 4. Install Software (Windows)
------------------------------------------------------------

Install Python:
https://www.python.org/downloads/windows/

Make sure to check:
[✓] Add Python to PATH

Install required libraries:

pip install pyserial paho-mqtt

(OPTIONAL) Install a serial monitor:
- CoolTerm: https://freeware.the-meiers.org/
- PuTTY: https://www.putty.org/

------------------------------------------------------------
📡 5. Serial Packet Format (VERY IMPORTANT)
------------------------------------------------------------

Micro:bit MUST send data in this exact format:

!RT:25:RH:60:LUX:300#

Rules:
- Must start with !
- Must end with #
- No spaces
- No newlines
- Always follow this order: RT, RH, LUX
- Values must be numeric

------------------------------------------------------------
🧪 6. Micro:bit Code (MicroPython)
------------------------------------------------------------

Use this MicroPython code:

from microbit import uart, sleep

uart.init(baudrate=115200)

while True:
    RT = 25
    RH = 60
    LUX = 300

    packet = "!RT:{}:RH:{}:LUX:{}#".format(RT, RH, LUX)
    uart.write(packet)

    sleep(1000)

------------------------------------------------------------
🚀 7. Running the Python Gateway
------------------------------------------------------------

Run the gateway:

python gateway.py

Expected output:

=== Starting PC Gateway ===
✓ Connected to Adafruit IO
Detected port: COM3 - BBC micro:bit CMSIS-DAP
✓ Using serial: COM3
Received: !RT:25:RH:60:LUX:300#
Published → RT=25, RH=60, LUX=300

------------------------------------------------------------
🔍 8. Debugging Guide
------------------------------------------------------------

❗ Micro:bit not detected
- Try a different cable
- Try another USB port
- Check Device Manager
- Reinstall drivers

❗ No data appears
- Check baudrate: must be 115200
- Check uart.write()
- Ensure Micro:bit code running
- Serial monitor tools can block COM port → close CoolTerm/PuTTY

❗ “Malformed packet”
Your packet must be exactly:

!RT:<value>:RH:<value>:LUX:<value>#

Common mistakes:
- Missing !
- Missing #
- Extra spaces
- Wrong order of values

❗ Adafruit IO not receiving
- Check username/key in gateway.py
- Check feed names: rt, rh, lux
- Run gateway → should show “✓ Test publish OK”

------------------------------------------------------------
🔁 9. Recommended Send Rate
------------------------------------------------------------

Send 1 packet per second:

sleep(1000)

Sending too fast may overflow serial buffer.

------------------------------------------------------------
🔄 10. Reset Procedure
------------------------------------------------------------

1. Unplug Micro:bit
2. Close all serial monitors
3. Restart gateway.py
4. Reconnect Micro:bit
5. Confirm COM port in Device Manager

------------------------------------------------------------
🏁 11. Hardware Checklist
------------------------------------------------------------

✓ Micro:bit connected via USB  
✓ Python installed  
✓ pyserial + paho-mqtt installed  
✓ Baudrate = 115200  
✓ Packet format correct  
✓ Gateway receives packets  
✓ Adafruit IO updates correctly  

------------------------------------------------------------
🎉 12. Summary
------------------------------------------------------------

Completed data flow:

Micro:bit → USB Serial → Python Gateway → Adafruit IO → Backend

This enables real-time IoT monitoring and future ML backend processing.