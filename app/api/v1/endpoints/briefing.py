from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import AudioBriefing
from app.schemas.briefing import AudioBriefingResponse

router = APIRouter()

@router.get("/latest", response_model=AudioBriefingResponse)
def get_latest_briefing(
    region: str = Query("vn", description="Region to get the latest audio briefing for"),
    db: Session = Depends(get_db)
):
    """
    Get the most recent generated Audio Briefing for the specified region.
    """
    latest_briefing = (
        db.query(AudioBriefing)
        .filter(AudioBriefing.region == region)
        .order_by(AudioBriefing.created_at.desc())
        .first()
    )
    
    if not latest_briefing:
        raise HTTPException(status_code=404, detail=f"No audio briefing found for region '{region}'.")
        
    return latest_briefing
