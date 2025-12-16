from fastapi import FastAPI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pymongo import AsyncMongoClient
from fastapi.responses import HTMLResponse

from data.mongo import mongo

# HTTP controllers
from controller.AuthController import router as auth_router
from controller.HistoryController import router as history_router
from controller.IngestController import router as ingest_router

# WebSocket controller (IMPORTANT)
from controller.RealTimeController import router as realtime_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 LIFESPAN STARTING")

    mongo.client = AsyncMongoClient(
        "mongodb+srv://Cluster76516:WGtse3VmfVZx@cluster76516.zzq9k.mongodb.net/IoT_?appName=Cluster76516",
        serverSelectionTimeoutMS=5000,
    )

    # Force connection test
    await mongo.client.admin.command("ping")
    print("✅ MongoDB connected")

    yield

    print("🛑 LIFESPAN SHUTDOWN")
    if mongo.client:
        await mongo.client.close()


app = FastAPI(
    title="IoT Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# --------------------
# Root UI
# --------------------
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h1>🚀 IoT Backend API</h1>
    <ul>
        <li><a href="/docs">Swagger Docs</a></li>
        <li><a href="/history/lux">GET /history/lux</a></li>
        <li><code>POST /ingest</code></li>
        <li><code>WS /ws/metrics</code></li>
    </ul>
    """


# --------------------
# Register HTTP routes
# --------------------
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(ingest_router)

# --------------------
# Register WebSocket routes
# --------------------
app.include_router(realtime_router)