import sys
import time
from Adafruit_IO import MQTTClient

# --- CONFIGURATION ---
AIO_USERNAME = "ntk_cse"
AIO_KEY = "rwJ51Y6x1c4VLCA"

# The specific feeds you want to fetch
# Note: Ensure these match your Adafruit IO Feed Keys exactly (hyphen vs underscore)
FEED_IDS = ["dadn-humid", "dadn-temp", "dadn-light"]

# --- CALLBACK FUNCTIONS ---

def connected(client):
    print("Connected to Adafruit IO! Initializing subscriptions...")
    # Loop through your list and subscribe to each one
    for feed in FEED_IDS:
        feed_path = f"{AIO_USERNAME}/feeds/{feed}"
        client.subscribe(feed_path)
        print(f" >> Subscribed to: {feed}")

def subscribe(client, userdata, mid, granted_qos):
    
    pass

def disconnected(client):
    print("Disconnected from Adafruit IO!")
    sys.exit(1)

def message(client, feed_id, payload):
    """
    This function triggers AUTOMATICALLY when data arrives.
    """
    # Clean up the feed_id to just get the name (removes "username/feeds/")
    feed_name = feed_id.split('/')[-1]
    
    print(f"[DATA FETCHED] {feed_name}: {payload}")

    # --- FUTURE INTELLIGENCE GOES HERE ---
    # This is where you will add your logic later.
    # Example:
    # if feed_name == "dadn-temp":
    #     save_to_history(payload)
    #     perform_regression()


# --- MAIN SETUP ---

# 1. Initialize the Client
client = MQTTClient(AIO_USERNAME, AIO_KEY)

# 2. Link the callback functions
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe

# 3. Connect to the Cloud
client.connect()

# 4. Start the background listener
# This creates a separate thread to handle incoming network messages
client.loop_background()

print("Gateway is running. Waiting for data from Yolo:Bit...")

# --- MAIN LOOP ---
while True:
    # The script needs to stay alive to keep listening.
    # We just sleep to save CPU power.
    time.sleep(1)