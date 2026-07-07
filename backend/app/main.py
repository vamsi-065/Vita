import asyncio
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.alert import AlertRule, Alert, NotificationLog
from app.core.alert_manager import evaluate_rules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

async def periodic_alert_evaluator():
    while True:
        try:
            db = SessionLocal()
            evaluate_rules(db)
        except Exception as e:
            logger.error(f"Error evaluating rules: {e}")
        finally:
            db.close()
        
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(periodic_alert_evaluator())
    yield
    task.cancel()

app = FastAPI(title="AI Business OS API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception logger
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on request {request.method} {request.url.path}:")
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(trace)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc), "traceback": trace}
    )

from app.api.v1.endpoints import auth, alerts, chat, tables
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(tables.router, prefix="/api/v1/tables", tags=["tables"])

@app.get("/")
def root():
    return {"message": "AI Business OS is running"}

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": "AI Business OS",
        "version": "1.0.0",
        "environment": "development",
        "database": "connected"
    }
