from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID

class SourceInfo(BaseModel):
    id: int
    name: str
    base_url: str

    model_config = ConfigDict(from_attributes=True)

class ArticleFeed(BaseModel):
    id: UUID
    title: str
    original_url: str
    thumbnail_url: Optional[str] = None
    ai_summary: List[str]
    published_at: datetime
    importance_score: float
    source: SourceInfo

    model_config = ConfigDict(from_attributes=True)

    @field_validator('ai_summary', mode='before')
    @classmethod
    def extract_summary_list(cls, v: Any) -> List[str]:
        if isinstance(v, dict) and 'summary' in v:
            return v['summary']
        elif isinstance(v, list):
            return v
        return []

class CategoryFeed(BaseModel):
    id: int
    slug: str
    name: str
    articles: List[ArticleFeed]

    model_config = ConfigDict(from_attributes=True)
