from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pymongo import AsyncMongoClient
from fastapi.responses import HTMLResponse
import asyncio

from data.mongo import mongo
from controller.AuthController import router as auth_router
from controller.SystemController import router as system_router
from gateway.adafruit_gateway import start_adafruit_gateway

load_dotenv()


# ======================
# MongoDB wait helper
# ======================

async def wait_for_mongo(client, retries: int = 10, delay: int = 1):
    for i in range(retries):
        try:
            await client.admin.command("ping")
            print("✅ MongoDB connected")
            return
        except Exception:
            print(f"⏳ Waiting for MongoDB primary ({i+1}/{retries})")
            await asyncio.sleep(delay)

    raise RuntimeError("MongoDB not available after retries")


# ======================
# FastAPI lifespan
# ======================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 LIFESPAN STARTING")

    # 1️⃣ Connect MongoDB
    mongo.client = AsyncMongoClient(
        "mongodb+srv://Cluster76516:WGtse3VmfVZx@cluster76516.zzq9k.mongodb.net/IoT_?appName=Cluster76516",
        serverSelectionTimeoutMS=5000,
        readPreference="primaryPreferred",
    )

    # Wait until Mongo is usable
    await wait_for_mongo(mongo.client)

    # 2️⃣ Start Adafruit Gateway
    gateway_task = asyncio.create_task(start_adafruit_gateway())

    yield

    # 3️⃣ Shutdown
    print("🛑 LIFESPAN SHUTDOWN")
    gateway_task.cancel()
    await mongo.client.close()


# ======================
# FastAPI app
# ======================

app = FastAPI(
    title="IoT Backend",
    version="0.1.0",
    lifespan=lifespan,
)


# ======================
# Root UI
# ======================

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <head><title>IoT Backend</title></head>
        <body style="font-family: system-ui; background:#020617; color:#e5e7eb; padding:40px">
            <h1>🚀 IoT Backend API</h1>
            <ul>
                <li><a href="/docs">Swagger</a></li>
                <li><a href="/redoc">ReDoc</a></li>
                <li><code>POST /auth/register</code></li>
                <li><code>POST /auth/login</code></li>
                <li><code>GET /system/health</code></li>
                <li><code>WS /ws/metrics</code></li>
            </ul>
            <p>Status: <strong>running</strong></p>
        </body>
    </html>
    """


# ======================
# Routers
# ======================

app.include_router(auth_router)
app.include_router(system_router)