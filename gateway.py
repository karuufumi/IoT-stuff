import network
import time
from umqtt.simple import MQTTClient

# ============================================================
# GLOBAL SENSOR VARIABLES  (values updated by your sensor code)
# ============================================================
RT = 0      # temperature
RH = 0      # humidity
LUX = 0     # light intensity

# ============================================================
# USER CONFIGURATION
# ============================================================
WIFI_SSID = 'abcd'       
WIFI_PASS = '123456789'  

# ============================================================
# ADAFRUIT IO CONFIGURATION
# ============================================================
AIO_SERVER = 'io.adafruit.com'
AIO_PORT   = 1883
AIO_USER   = 'ntk_cse'                # your username
AIO_KEY    = 'rwJ51Y6x1c4VLCA'        # your AIO key

# Feed names on Adafruit IO
FEED_RT  = 'ntk_cse/feeds/rt'
FEED_RH  = 'ntk_cse/feeds/rh'
FEED_LUX = 'ntk_cse/feeds/lux'


# ============================================================
# CONNECT TO WIFI
# ============================================================
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)

        retry = 0
        while not wlan.isconnected():
            print("Waiting for WiFi...", retry)
            retry += 1
            time.sleep(1)

    print("WiFi Connected:", wlan.ifconfig())
    return True


# ============================================================
# CONNECT TO ADAFRUIT IO (MQTT)
# ============================================================
def connect_mqtt():
    client_id = "ESP32_AQI_GATEWAY"
    client = MQTTClient(client_id, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)
    
    try:
        client.connect()
        print("Connected to Adafruit IO MQTT.")
    except Exception as e:
        print("MQTT Connection failed:", e)
        time.sleep(3)
        machine.reset()
    
    return client


# ============================================================
# PUBLISH SENSOR DATA
# ============================================================
def publish_all(client):
    global RT, RH, LUX

    try:
        client.publish(FEED_RT,  str(RT))
        client.publish(FEED_RH,  str(RH))
        client.publish(FEED_LUX, str(LUX))

        print("Published → RT:", RT, "| RH:", RH, "| LUX:", LUX)

    except Exception as e:
        print("Publish error:", e)


# ============================================================
# MAIN LOOP
# ============================================================
def loop(client):
    global RT, RH, LUX

    while True:
        # TODO: update RT, RH, LUX from your sensors here
        # Example (fake values):
        RT  += 1
        RH  += 2
        LUX += 3

        publish_all(client)

        time.sleep(5)   # publish interval (seconds)


# ============================================================
# RUN PROGRAM
# ============================================================
connect_wifi()
client = connect_mqtt()
loop(client)
