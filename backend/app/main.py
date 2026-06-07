import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import router
from app.api.websocket import ws_manager, redis_listener
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    start_scheduler()
    listener_task = asyncio.create_task(redis_listener())
    logger.info("NSE Scanner started")
    yield
    # Shutdown
    listener_task.cancel()
    stop_scheduler()
    logger.info("NSE Scanner stopped")

app = FastAPI(
    title="NSE F&O Scanner API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        # Send initial state
        from app.core.redis_client import cache_get
        cached = await cache_get("scanner:all_signals")
        if cached:
            await ws_manager.send_personal(ws, {"type": "initial_state", "data": cached})
        while True:
            # Keep alive
            try:
                data = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                if data == "ping":
                    await ws_manager.send_personal(ws, {"type": "pong"})
            except asyncio.TimeoutError:
                await ws_manager.send_personal(ws, {"type": "heartbeat"})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception as e:
        logger.error(f"WS error: {e}")
        ws_manager.disconnect(ws)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "nse-scanner"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
