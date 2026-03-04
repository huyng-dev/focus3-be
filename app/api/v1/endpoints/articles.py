from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.scraper.rss import fetch_and_save_articles

router = APIRouter()

@router.post("/trigger-scraper")
def trigger_scraper():
    """
    Manually trigger the RSS scraper.
    """
    fetch_and_save_articles()
    return {"message": "Scraper triggered successfully."}

@router.get("/")
def list_articles(db: Session = Depends(get_db)):
    """
    List articles (Placeholder for actual implementation).
    """
    return {"articles": []}
