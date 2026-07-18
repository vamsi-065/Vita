import os
import sys
import asyncio
import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware



from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

# Initialize basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.database import engine, Base, SessionLocal, database_service
from app.models.user import User
from app.models.alert import AlertRule, Alert, NotificationLog
from app.core.alert_manager import evaluate_rules
from app.llm.engine import llm_engine

def run_startup_checks():
    logger.info("Executing Startup Health Checks (Phase 10)...")
    
    # 1. Verify DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.critical("[STARTUP FAILED] DATABASE_URL is not set in environment.")
        sys.exit(1)
        
    # 2. Verify PostgreSQL connection
    try:
        database_service.validate_connection()
    except Exception as e:
        logger.critical(f"[STARTUP FAILED] PostgreSQL connection failed: {e}")
        sys.exit(1)
        
    # 3. Create tables (Schema migration/sync)
    try:
        logger.info("Syncing Database Schema...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database Schema synced successfully.")
    except Exception as e:
        logger.critical(f"[STARTUP FAILED] Schema creation failed: {e}")
        sys.exit(1)
        
    # 4. Verifying CRUD engine (self-test)
    try:
        logger.info("Verifying CRUD engine...")
        with database_service.transaction() as session:
            # We insert a test record, update it, select it, then delete it to verify the AI's sql generator won't fail.
            session.execute(text("INSERT INTO inventory (item_name, quantity, status) VALUES ('startup_test_banana', 10, 'In Stock');"))
            session.execute(text("UPDATE inventory SET quantity = 20 WHERE item_name = 'startup_test_banana';"))
            res = session.execute(text("SELECT quantity FROM inventory WHERE item_name = 'startup_test_banana';")).fetchone()
            if not res or res[0] != 20:
                raise Exception("CRUD update/select verification failed.")
            session.execute(text("DELETE FROM inventory WHERE item_name = 'startup_test_banana';"))
        logger.info("CRUD engine validated successfully.")
    except Exception as e:
        logger.critical(f"[STARTUP FAILED] CRUD engine test failed: {e}")
        sys.exit(1)
        
    # 5. Verify GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.critical("[STARTUP FAILED] GEMINI_API_KEY is not set in environment.")
        sys.exit(1)
        
    # 6. Verify Gemini Key & Model Access
    try:
        llm_engine.validate_api_key()
    except Exception as e:
        logger.critical(f"[STARTUP FAILED] Gemini authentication/model access failed: {e}")
        sys.exit(1)
        
    logger.info("All Startup Health Checks passed successfully! Server is ready.")

# Run startup checks before starting application loops
run_startup_checks()

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
    allow_origins=["https://vita-opal.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception logger
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        content = {"detail": exc.detail}
    else:
        logger.error(f"Unhandled exception on request {request.method} {request.url.path}:")
        trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(trace)
        status_code = 500
        content = {"detail": "Internal Server Error", "error": str(exc), "traceback": trace}

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={
            "Access-Control-Allow-Origin": "https://vita-opal.vercel.app",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

from app.api.v1.endpoints import auth, alerts, chat, tables, profile, telegram
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(tables.router, prefix="/api/v1/tables", tags=["tables"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(telegram.router, prefix="/webhook", tags=["telegram"])

@app.get("/")
def root():
    return {"message": "AI Business OS is running"}

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": "Vita",
        "version": "1.0.0",
        "environment": "development",
        "database": "connected"
    }
