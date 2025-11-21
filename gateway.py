import time
import json
import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt

# ============================================================
# USER CONFIGURATION
# ============================================================
AIO_USERNAME = "ntk_cse"
AIO_KEY      = "rwJ51Y6x1c4VLCA"   
AIO_SERVER   = "io.adafruit.com"
AIO_PORT     = 1883

# Feed names 
FEED_RT  = f"{AIO_USERNAME}/feeds/rt"
FEED_RH  = f"{AIO_USERNAME}/feeds/rh"
FEED_LUX = f"{AIO_USERNAME}/feeds/lux"

# ============================================================
# SERIAL CONFIG (PC receiving data from microcontroller)
# ============================================================
BAUDRATE = 115200
SERIAL_TIMEOUT = 0.2


# ============================================================
# Find a serial port automatically
# ============================================================
def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        print("Detected:", p.device, p.description)
        if "USB" in p.description or "ACM" in p.description or "COM" in p.device:
            return p.device
    return None


# ============================================================
# MQTT CALLBACKS
# ============================================================
def on_connect(client, userdata, flags, rc):
    print("Connected to Adafruit IO with result code", rc)


def on_disconnect(client, userdata, rc):
    print("Disconnected from Adafruit IO. Reconnecting...")
    time.sleep(3)
    try:
        client.reconnect()
    except:
        pass


# ============================================================
# CREATE MQTT CLIENT
# ============================================================
def create_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(AIO_USERNAME, AIO_KEY)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    print("Connecting to Adafruit IO...")
    client.connect(AIO_SERVER, AIO_PORT, keepalive=60)

    client.loop_start()
    return client


# ============================================================
# SEND RT/RH/LUX TO ADAFRUIT IO
# ============================================================
def publish_data(client, RT, RH, LUX):
    try:
        client.publish(FEED_RT,  RT)
        client.publish(FEED_RH,  RH)
        client.publish(FEED_LUX, LUX)
        print(f"PUBLISHED → RT={RT}, RH={RH}, LUX={LUX}")
    except Exception as e:
        print("Publish error:", e)


# ============================================================
# PARSE SERIAL PACKETS FROM MICROCONTROLLER
#
# Expected data format from sensor device:
#   !RT:25:RH:60:LUX:300#
#
# Example:
#   !RT:24:RH:58:LUX:700#
# ============================================================
def parse_packet(packet):
    try:
        data = packet.replace("!", "").replace("#", "")
        parts = data.split(":")
        # RT:<value>, RH:<value>, LUX:<value>
        RT  = float(parts[1])
        RH  = float(parts[3])
        LUX = float(parts[5])
        return RT, RH, LUX
    except:
        return None


# ============================================================
# MAIN LOOP
# ============================================================
def main():
    # --- Setup MQTT ---
    client = create_mqtt_client()

    # --- Find Serial Port ---
    port = find_serial_port()
    if port is None:
        print("ERROR: No microcontroller detected!")
        return

    print("Using Serial Port:", port)
    ser = serial.Serial(port, BAUDRATE, timeout=SERIAL_TIMEOUT)

    buffer = ""

    # --- MAIN LOOP ---
    while True:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode(errors="ignore")

        # Process packets of form ! ... #
        while "!" in buffer and "#" in buffer:
            start = buffer.find("!")
            end   = buffer.find("#", start)

            if end == -1:
                break

            packet = buffer[start:end+1]
            buffer = buffer[end+1:]

            print("Received packet:", packet)
            parsed = parse_packet(packet)

            if parsed:
                RT, RH, LUX = parsed
                publish_data(client, RT, RH, LUX)
            else:
                print("Malformed packet:", packet)

        time.sleep(0.2)


# ============================================================
# RUN PROGRAM
# ============================================================
if __name__ == "__main__":
    print("Starting IoT Gateway...")
    main()
import time
import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt

# ============================================================
# USER CONFIGURATION
# ============================================================
AIO_USERNAME = "ntk_cse"
AIO_KEY      = "rwJ51Y6x1c4VLCA"
AIO_SERVER   = "io.adafruit.com"
AIO_PORT     = 1883

# Feed names
FEED_RT  = f"{AIO_USERNAME}/feeds/rt"
FEED_RH  = f"{AIO_USERNAME}/feeds/rh"
FEED_LUX = f"{AIO_USERNAME}/feeds/lux"

# ============================================================
# SERIAL CONFIG
# ============================================================
BAUDRATE = 115200
SERIAL_TIMEOUT = 0.2


# ============================================================
# MQTT CALLBACKS
# ============================================================
def on_connect(client, userdata, flags, rc):
    print("Connected to Adafruit IO. rc =", rc)


def on_disconnect(client, userdata, rc):
    print("Disconnected from Adafruit IO. Reconnecting...")
    time.sleep(2)
    try:
        client.reconnect()
    except:
        pass


# ============================================================
# Create MQTT client
# ============================================================
def create_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(AIO_USERNAME, AIO_KEY)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    print("Connecting to Adafruit IO...")
    client.connect(AIO_SERVER, AIO_PORT, keepalive=60)
    client.loop_start()

    return client


# ============================================================
# Test connection BEFORE starting serial logic
# ============================================================
def test_adafruit_connection():
    print("=== Testing Adafruit IO connection ===")

    test_client = mqtt.Client()
    test_client.username_pw_set(AIO_USERNAME, AIO_KEY)

    try:
        test_client.connect(AIO_SERVER, AIO_PORT, keepalive=30)
        test_client.loop_start()

        print("✓ Connected to Adafruit IO")

        print("Publishing test values...")
        test_client.publish(FEED_RT,  "TEST_RT")
        test_client.publish(FEED_RH,  "TEST_RH")
        test_client.publish(FEED_LUX, "TEST_LUX")

        time.sleep(1)
        print("✓ Test publish OK")

        test_client.loop_stop()
        test_client.disconnect()
        return True

    except Exception as e:
        print("❌ Failed to connect to Adafruit IO:", e)
        return False


# ============================================================
# Find serial port automatically
# ============================================================
def find_serial_port():
    ports = serial.tools.list_ports.comports()

    for p in ports:
        print("Detected port:", p.device, "-", p.description)

        # Ignore virtual ports
        if "Bluetooth" in p.device or "debug" in p.device:
            continue

        # Accept any real USB serial device
        if "usb" in p.device.lower() or "serial" in p.description.lower() or "uart" in p.description.lower():
            print("✓ Using serial:", p.device)
            return p.device

    return None


# ============================================================
# Parse packets like:
#    !RT:25:RH:60:LUX:300#
# ============================================================
def parse_packet(packet):
    try:
        clean = packet.replace("!", "").replace("#", "")
        parts = clean.split(":")  # ["RT", "25", "RH", "60", "LUX", "300"]

        RT  = float(parts[1])
        RH  = float(parts[3])
        LUX = float(parts[5])

        return RT, RH, LUX
    except:
        return None


# ============================================================
# Publish values to Adafruit IO
# ============================================================
def publish_data(client, RT, RH, LUX):
    client.publish(FEED_RT,  RT)
    client.publish(FEED_RH,  RH)
    client.publish(FEED_LUX, LUX)
    print(f"Published → RT={RT}, RH={RH}, LUX={LUX}")


# ============================================================
# MAIN
# ============================================================
def main():
    print("=== Starting PC Gateway ===")

    # --- Test Adafruit IO first ---
    if not test_adafruit_connection():
        print("\nERROR: Cannot reach Adafruit IO. Exiting.\n")
        return

    print("\n✓ Adafruit IO OK. Proceeding...\n")

    # --- Create real MQTT client ---
    client = create_mqtt_client()

    # --- Detect serial port ---
    port = find_serial_port()
    if port is None:
        print("❌ ERROR: No microcontroller detected!")
        return

    ser = serial.Serial(port, BAUDRATE, timeout=SERIAL_TIMEOUT)
    print("✓ Serial opened:", port)

    buffer = ""

    # --- Main loop ---
    while True:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode(errors="ignore")

        # Extract complete packets
        while "!" in buffer and "#" in buffer:
            start = buffer.find("!")
            end   = buffer.find("#", start)

            if end == -1:
                break

            packet = buffer[start:end+1]
            buffer = buffer[end+1:]

            print("Received:", packet)

            parsed = parse_packet(packet)
            if parsed:
                RT, RH, LUX = parsed
                publish_data(client, RT, RH, LUX)
            else:
                print("Malformed packet:", packet)

        time.sleep(0.1)


# ============================================================
if __name__ == "__main__":
    main()
