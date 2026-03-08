from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from app.services.scraper.rss import fetch_and_save_articles
from app.services.ranking import run_ranking_update
from app.services.ai.audio_briefing import generate_daily_briefing
from app.db.database import SessionLocal
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
    
    # Schedule ranking update every 15 minutes
    scheduler.add_job(
        run_ranking_update,
        'interval',
        minutes=15
    )
    
    # Schedule daily briefing at 6:00 AM and 6:00 PM (18:00)
    # Using a wrapper to provide a db session
    def run_daily_briefing_job():
        db = SessionLocal()
        try:
            generate_daily_briefing(db)
        finally:
            db.close()
            
    scheduler.add_job(
        run_daily_briefing_job,
        'cron',
        hour='6,18',
        minute=0
    )
    
    scheduler.start()
    
    # Run once at startup
    fetch_and_save_articles()
    run_ranking_update()
    
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

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Mount static files to serve the generated MP3s
    import os
    audio_dir = os.path.join(os.getcwd(), "app", "static", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "app", "static")), name="static")

    @app.get("/")
    def read_root():
        return {
            "message": f"{settings.PROJECT_NAME} API is running.",
            "scraper_status": "Active"
        }

    return app

app = create_app()
