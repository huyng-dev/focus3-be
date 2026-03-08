from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AudioBriefingResponse(BaseModel):
    id: int
    title: str
    audio_url: str
    duration_seconds: int
    region: str
    created_at: datetime
    
    class Config:
        from_attributes = True
