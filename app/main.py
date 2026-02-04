from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

from app.database import init_db
from app.routes.api import router as api_router
from app.services.telegram_bot import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Indie Fantrax...")
    init_db()
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down Indie Fantrax...")
    stop_scheduler()


app = FastAPI(title="Indie Fantrax", lifespan=lifespan)

# Include API routes
app.include_router(api_router)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    return FileResponse("app/static/index.html")
