from fastapi import APIRouter
from app.api.v1.endpoints import articles, feed, briefing

api_router = APIRouter()
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(feed.router, prefix="/feed", tags=["Feed"])
api_router.include_router(briefing.router, prefix="/briefing", tags=["Briefing"])
