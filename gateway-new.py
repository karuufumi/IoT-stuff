# yolo_home_gateway_pyic.py
from __future__ import annotations
import asyncio
import concurrent.futures
import contextlib
import dataclasses
import functools
import json
import random
import signal
import serial
import serial.tools.list_ports
import time
from typing import Callable, Dict, Iterator, Optional, Tuple

import paho.mqtt.client as mqtt

#EXPERIMENTAL: DO NOT RUN
# ---------------------------
# Configuration
# ---------------------------
@dataclasses.dataclass(frozen=True)
class Config:
    aio_username: str
    aio_key: str
    broker: str = "io.adafruit.com"
    port: int = 8883
    feeds: Dict[str, str] = dataclasses.field(default_factory=dict)
    sensor_interval: float = 30.0      # seconds
    clock_interval: float = 2.0        # seconds (blink colon every call)
    motion_interval: float = 0.1       # seconds (PIR polling)
    reconnect_delay: float = 5.0       # seconds


# ---------------------------
# Utilities (functional style)
# ---------------------------
def choose_microbit_port(prefer_name_substrs=("USB Serial Device", "Yolo:Bit")) -> Optional[str]:
    for p in serial.tools.list_ports.comports():
        pstr = str(p)
        if any(s in pstr for s in prefer_name_substrs):
            # first token typically contains the port path
            return pstr.split(" ")[0]
    return None


def clamp(n: float, a: float, b: float) -> float:
    return max(a, min(b, n))


# parsing micro:bit style packets: !ID:KEY:VALUE#
def parse_packet(packet: str) -> Optional[Tuple[str, str]]:
    """
    Given a packet like '!01:TEMP:26.3#' returns ('TEMP', '26.3')
    returns None if malformed.
    """
    try:
        trimmed = packet.strip()
        if not (trimmed.startswith("!") and trimmed.endswith("#")):
            return None
        body = trimmed[1:-1]
        parts = body.split(":")
        if len(parts) < 3:
            return None
        key = parts[1].upper()
        value = ":".join(parts[2:])  # in case value contains ':'
        return key, value
    except Exception:
        return None


def map_sensor_to_feed(feeds: Dict[str, str], key: str) -> Optional[str]:
    d = {"TEMP": "temp", "HUMI": "humi", "LIGHT": "light", "PIR": "pir"}
    return feeds.get(d.get(key, ""), None)


def make_simulator(seed: Optional[int] = None) -> Callable[[], Dict[str, object]]:
    rnd = random.Random(seed)

    def sim() -> Dict[str, object]:
        return {
            "TEMP": round(rnd.uniform(24.0, 32.0), 1),
            "HUMI": round(rnd.uniform(40.0, 75.0), 1),
            "LIGHT": rnd.randint(0, 800),
            "PIR": 0,
        }

    return sim


# ---------------------------
# Serial context manager (blocking serial)
# ---------------------------
@contextlib.contextmanager
def open_serial(port: str, baudrate: int = 115200, timeout: float = 0.1):
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    try:
        yield ser
    finally:
        try:
            ser.close()
        except Exception:
            pass


# ---------------------------
# Threaded serial reader -> async generator bridge
# ---------------------------
def serial_reader_blocking(ser: serial.Serial, out_queue: "asyncio.Queue[str]"):
    """
    Blocking reader to be run in executor. It reads raw bytes and puts
    newline-delimited or framing-delimited packets into out_queue via loop.call_soon_threadsafe.
    Expected micro:bit framing: !...#
    """
    buffer = ""
    loop = asyncio.get_event_loop()
    while True:
        try:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting).decode(errors="ignore")
                buffer += data
                # process all framed packets
                while "!" in buffer and "#" in buffer:
                    start = buffer.find("!")
                    end = buffer.find("#", start)
                    if end == -1:
                        break
                    packet = buffer[start : end + 1]
                    buffer = buffer[end + 1 :]
                    loop.call_soon_threadsafe(asyncio.create_task, out_queue.put(packet))
            else:
                time.sleep(0.05)
        except serial.SerialException:
            loop.call_soon_threadsafe(asyncio.create_task, out_queue.put("__SERIAL_ERROR__"))
            break
        except Exception:
            # swallow to keep reading; could log
            time.sleep(0.05)
            continue


# ---------------------------
# MQTT wrapper (small functional interface)
# ---------------------------
class MQTTBridge:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.client = mqtt.Client()
        self._setup()

    def _setup(self):
        self.client.username_pw_set(self.cfg.aio_username, self.cfg.aio_key)
        # TLS
        self.client.tls_set()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        # user-provided handlers
        self._message_cb: Optional[Callable[[str, str], None]] = None
        self._connected = asyncio.Event()

    def set_on_message(self, cb: Callable[[str, str], None]):
        self._message_cb = cb

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected_loop_safe(set_event=True)
            # subscribe to LED control if exists
            led_feed = self.cfg.feeds.get("led")
            if led_feed:
                client.subscribe(led_feed)
        else:
            self._connected_loop_safe(set_event=False)

    def _on_disconnect(self, client, userdata, rc):
        self._connected_loop_safe(set_event=False)

    def _on_message(self, client, userdata, msg):
        if self._message_cb:
            try:
                self._message_cb(msg.topic, msg.payload.decode())
            except Exception:
                pass

    def _connected_loop_safe(self, set_event: bool):
        try:
            loop = asyncio.get_event_loop()
            if set_event:
                loop.call_soon_threadsafe(self._connected.set)
            else:
                loop.call_soon_threadsafe(self._connected.clear)
        except RuntimeError:
            # no loop running; ignore
            pass

    async def connect_background(self):
        """Connect and run network loop in background thread."""
        # run connect in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.connect, self.cfg.broker, self.cfg.port, 60)
        # use background loop
        self.client.loop_start()
        # wait for connected event or timeout
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            # still continue; reconnect logic elsewhere
            pass

    def publish(self, topic: str, payload: object):
        payload_str = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)
        # fire-and-forget; paho handles internal buffering
        try:
            self.client.publish(topic, payload_str)
        except Exception:
            pass

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass


# ---------------------------
# The Gateway (composes small functions)
# ---------------------------
class Gateway:
    def __init__(self, cfg: Config, serial_port: Optional[str] = None, sim_seed: Optional[int] = None):
        self.cfg = cfg
        self.serial_port = serial_port or choose_microbit_port()
        self._sim = make_simulator(sim_seed)
        self._mqtt = MQTTBridge(cfg)
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self._serial_task = None
        self._running = False

        # message handlers
        self._mqtt.set_on_message(self._on_mqtt_message)

    # mqtt message handler
    def _on_mqtt_message(self, topic: str, payload: str):
        # simple mapping: if it's LED feed, forward to microbit if serial exists
        if topic == self.cfg.feeds.get("led", ""):
            print(f"[MQTT] LED control: {payload}")
            if self.ser and self.ser.is_open:
                try:
                    self.ser.write((payload + "#").encode())
                except Exception:
                    pass

    async def _start_serial_reader(self):
        if not self.serial_port:
            print("No serial port configured; running in simulation mode.")
            return
        try:
            self.ser_context = open_serial(self.serial_port)
            self.ser = self.ser_context.__enter__()  # manual enter so we can exit later
            print(f"Serial opened at {self.serial_port}")
        except Exception as e:
            print("Could not open serial:", e)
            self.ser = None
            return

        loop = asyncio.get_event_loop()
        # run blocking serial reader in executor
        loop.run_in_executor(self._executor, functools.partial(serial_reader_blocking, self.ser, self._queue))

    async def _stop_serial_reader(self):
        if getattr(self, "ser_context", None):
            try:
                self.ser_context.__exit__(None, None, None)
            except Exception:
                pass

    async def _handle_incoming_packets(self):
        while self._running:
            packet = await self._queue.get()
            if packet == "__SERIAL_ERROR__":
                print("Serial error detected; stopping serial reader.")
                await self._stop_serial_reader()
                # try reconnect after delay
                await asyncio.sleep(self.cfg.reconnect_delay)
                await self._start_serial_reader()
                continue

            parsed = parse_packet(packet)
            if not parsed:
                continue
            key, value = parsed
            feed_topic = map_sensor_to_feed(self.cfg.feeds, key)
            if feed_topic:
                print(f"Parsed {key} -> {value} -> publish to {feed_topic}")
                self._mqtt.publish(feed_topic, value)

    async def _periodic_sensor_task(self):
        """If there is no serial, simulate sensors periodically. If serial exists,
        it will publish as data arrives, so simulation is not used."""
        while self._running:
            if not getattr(self, "ser", None):
                data = self._sim()
                for k, v in data.items():
                    feed_topic = map_sensor_to_feed(self.cfg.feeds, k)
                    if feed_topic:
                        self._mqtt.publish(feed_topic, v)
                print("Simulated sensors:", data)
            await asyncio.sleep(self.cfg.sensor_interval)

    async def _periodic_clock_task(self):
        colon_state = True
        while self._running:
            colon_state = not colon_state
            colon = ":" if colon_state else " "
            current_time = time.strftime(f"%H{colon}%M")
            # publish to a 'clock' feed if present; otherwise console
            clock_feed = self.cfg.feeds.get("clock")
            if clock_feed:
                self._mqtt.publish(clock_feed, current_time)
            else:
                print("Clock:", current_time)
            await asyncio.sleep(self.cfg.clock_interval)

    async def _periodic_motion_task(self):
        """Motion sampling can be passive (serial reports PIR) or active polling (simulate)."""
        while self._running:
            if not getattr(self, "ser", None):
                pir = 0  # simulation: usually zero
                pir_feed = self.cfg.feeds.get("pir")
                if pir_feed:
                    self._mqtt.publish(pir_feed, pir)
            await asyncio.sleep(self.cfg.motion_interval)

    async def start(self):
        self._running = True
        # connect mqtt
        await self._mqtt.connect_background()
        # start serial reader if possible
        await self._start_serial_reader()

        # start coroutine tasks
        tasks = [
            asyncio.create_task(self._handle_incoming_packets()),
            asyncio.create_task(self._periodic_sensor_task()),
            asyncio.create_task(self._periodic_clock_task()),
            asyncio.create_task(self._periodic_motion_task()),
        ]

        # wait until cancelled
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            # cleanup
            await self._stop_serial_reader()
            self._mqtt.stop()
            self._executor.shutdown(wait=False)

    async def stop(self):
        self._running = False


# ---------------------------
# Entrypoint
# ---------------------------
def build_default_config(username: str, key: str) -> Config:
    feeds = {
        "temp": f"{username}/feeds/yolo-temp",
        "humi": f"{username}/feeds/yolo-humi",
        "light": f"{username}/feeds/yolo-light",
        "pir": f"{username}/feeds/yolo-pir",
        "led": f"{username}/feeds/yolo-led",
        # optional clock feed:
        "clock": f"{username}/feeds/yolo-clock",
    }
    return Config(aio_username=username, aio_key=key, feeds=feeds)


async def main():
    import os

    AIO_USERNAME = os.environ.get("AIO_USERNAME", "YOUR_ADAFRUIT_USERNAME")
    AIO_KEY = os.environ.get("AIO_KEY", "YOUR_ADAFRUIT_KEY")

    cfg = build_default_config(AIO_USERNAME, AIO_KEY)
    gw = Gateway(cfg, serial_port=None, sim_seed=42)  # serial_port=None -> auto detect or simulate
    loop = asyncio.get_event_loop()

    # graceful shutdown
    stop_event = asyncio.Event()

    def _signal_handler(signum, frame):
        print("Signal received, stopping...")
        loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # run the gateway
    runner = asyncio.create_task(gw.start())

    await stop_event.wait()
    print("Shutting down gateway...")
    await gw.stop()
    runner.cancel()
    try:
        await runner
    except Exception:
        pass
    print("Gateway stopped.")


if __name__ == "__main__":
    asyncio.run(main())