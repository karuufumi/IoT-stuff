# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from gateway import AdafruitGateway

# ===========================================================
# CONFIG
# ===========================================================
AIO_USERNAME = "ntk_cse"       # ✅ underscore version (matches your Adafruit account)
AIO_KEY = "dadn"               # replace with your actual Adafruit key

# Create the gateway instance (but don’t start yet)
gateway = AdafruitGateway(username=AIO_USERNAME, key=AIO_KEY)

# Initialize FastAPI app
app = FastAPI(title="Yolo:Home IoT API")


# ===========================================================
# EVENT HOOKS
# ===========================================================
@app.on_event("startup")
def startup_event():
    """Start the IoT gateway when the FastAPI app starts."""
    try:
        print("🚀 Starting Adafruit Gateway...")
        gateway.start()
    except Exception as e:
        print(f"⚠️ Failed to start gateway: {e}")


@app.on_event("shutdown")
def shutdown_event():
    """Gracefully stop the gateway when FastAPI stops."""
    print("🛑 Stopping Adafruit Gateway...")
    gateway.stop()


class Command(BaseModel):
    command: str

#Routes
@app.get("/")
def root():
    """Simple health check."""
    return {
        "message": "Yolo:Home API is online",
        "gateway_running": gateway.running,
    }


@app.get("/status")
def status():
    """Return cached sensor data."""
    try:
        return {"status": "ok", "data": gateway.get_status()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/control")
def control(cmd: Command):
    """Send a command to LED (and publish to Adafruit IO)."""
    try:
        gateway.send_command(cmd.command)
        return {"sent": cmd.command}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))