from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# 🔹 PyMongo async client (new official async driver)
from pymongo import AsyncMongoClient
from controller.HistoryController import router as history_router

from data.mongo import mongo
from controller.AuthController import router as auth_router
from controller.controllers import router as system_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 LIFESPAN STARTING")

    mongo.client = AsyncMongoClient(
        "mongodb+srv://Cluster76516:WGtse3VmfVZx@cluster76516.zzq9k.mongodb.net/IoT_?appName=Cluster76516",
        serverSelectionTimeoutMS=5000,
    )

    # 🔑 Force MongoDB connection check
    await mongo.client.admin.command("ping")
    print("✅ MongoDB connected")

    yield

    print("🛑 LIFESPAN SHUTDOWN")
    if mongo.client:
        await mongo.client.close()


app = FastAPI(
    title="IoT Backend",
    version="0.1.0",
    lifespan=lifespan,  # ✅ Correct place for Mongo initialization
)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IoT Backend API</title>
        <style>
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                background: #0f172a;
                color: #e5e7eb;
                padding: 40px;
            }
            .container {
                max-width: 720px;
                margin: auto;
                background: #020617;
                padding: 32px;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            }
            h1 {
                color: #38bdf8;
            }
            code {
                background: #020617;
                padding: 4px 8px;
                border-radius: 6px;
                color: #a5f3fc;
            }
            a {
                color: #38bdf8;
                text-decoration: none;
                font-weight: 600;
            }
            a:hover {
                text-decoration: underline;
            }
            ul {
                margin-top: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 IoT Backend API</h1>

            <p>This is the backend service for the IoT monitoring platform.</p>

            <h3>📘 API Documentation</h3>
            <ul>
                <li><a href="/docs">Swagger UI</a></li>
                <li><a href="/redoc">ReDoc</a></li>
            </ul>

            

            <h3>ℹ️ Notes</h3>
            <ul>
                <li>All protected endpoints require a JWT token</li>
                <li>Use <code>Authorization: Bearer &lt;token&gt;</code></li>
                <li>Time-series data is stored in MongoDB</li>
            </ul>

            <p style="margin-top: 24px; opacity: 0.8;">
                Status: <strong>API running</strong>
            </p>
        </div>
    </body>
    </html>
    """


# 🔹 Routers
app.include_router(auth_router)
app.include_router(system_router)
app.include_router(history_router)