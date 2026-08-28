"""
FastAPI Application Entry Point with Lifespan management, CORS, and WebSocket streaming.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger, format_ist_timestamp
from app.database.session import init_db
from app.api.v1.router import router as v1_router
from app.api.v1.websocket import ws_manager
from app.trading.auto_trader import auto_trader
from app.monitoring.failsafe import failsafe_monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Institutional Quantitative Trading Platform backend...")
    init_db()
    
    # Load stored credentials from database
    try:
        from app.database.session import SessionLocal
        from app.database.repository import Repository
        from app.execution.manager import broker_manager
        with SessionLocal() as session:
            repo = Repository(session)
            creds = repo.get_all_broker_credentials()
            if creds:
                broker_manager.load_persisted_credentials(creds)
                logger.info(f"Loaded {len(creds)} encrypted broker credentials from database.")
    except Exception as e:
        logger.warning(f"Could not load persisted credentials on boot: {e}")

    failsafe_monitor.start()
    if settings.AUTOTRADER_AUTOSTART_ON_BOOT:
        auto_trader.start()
        logger.info(f"System fully operational in {settings.APP_ENV} mode. Master Live Gate: {settings.LIVE_TRADING_ENABLED}. AutoTrader: ACTIVE (ON).")
    else:
        logger.info(f"System fully operational in {settings.APP_ENV} mode. Master Live Gate: {settings.LIVE_TRADING_ENABLED}. AutoTrader: STANDBY (OFF).")
    yield
    logger.info("Shutting down background daemons...")
    auto_trader.stop()
    failsafe_monitor.stop()
    logger.info("Platform shutdown complete.")


app = FastAPI(
    title="Institutional AI Quantitative Trading Platform API",
    description="Deterministic rule-based quantitative trading platform backend with multi-broker execution, event bus, and unbypassable risk controls.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(v1_router, prefix="/api")


# Mount Live WebSocket Streaming
@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                # Wait for any client message (ping/pong or keepalive) with a 30-second timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo any client-sent data back as an ack (supports client-initiated pings)
                if data:
                    await websocket.send_text('{"event_type":"PONG"}')
            except asyncio.TimeoutError:
                # No message received in 30s — send a server-initiated ping to keep the connection alive
                try:
                    await websocket.send_text('{"event_type":"PING"}')
                except Exception:
                    break  # Connection is dead; exit cleanly
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "platform": "Institutional AI Quantitative Trading Platform",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs_url": "/docs",
        "timestamp_ist": format_ist_timestamp(),
    }
