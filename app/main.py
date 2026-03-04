from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from app.services.scraper.rss import fetch_and_save_articles
from app.core.config import settings
from app.api.v1.api import api_router

# Initialize Scheduler
scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(f"Starting {settings.PROJECT_NAME}...")
    
    # Schedule scraper
    scheduler.add_job(
        fetch_and_save_articles, 
        'interval', 
        minutes=settings.SCRAPER_INTERVAL_MINUTES
    )
    scheduler.start()
    
    # Run once at startup
    fetch_and_save_articles() 
    
    yield
    
    # Shutdown logic
    print(f"Shutting down {settings.PROJECT_NAME}...")
    scheduler.shutdown()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Include API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/")
    def read_root():
        return {
            "message": f"{settings.PROJECT_NAME} API is running.",
            "scraper_status": "Active"
        }

    return app

app = create_app()
