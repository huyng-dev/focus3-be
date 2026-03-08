from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, contains_eager
from typing import List

from app.db.database import get_db
from app.models.models import Category, Article, Source
from app.schemas.feed import CategoryFeed

router = APIRouter()

@router.get("", response_model=List[CategoryFeed])
def get_feed(
    region: str = Query("vn", description="Region to filter articles by"),
    db: Session = Depends(get_db)
):
    """
    Get the top 3 articles for each category, formatted for the Bento Grid layout on the frontend.
    Only includes articles that have an AI summary.
    """
    # 2a. Query all active categories
    categories = db.query(Category).all()
    
    # 2b. Initialize empty list for response
    feed_response = []
    
    # 2c. Loop through each category
    for category in categories:
        # 2d, 2e, 2f, 2g. Query Article joined with Source
        # optimize with contains_eager to prevent N+1 queries when accessing article.source
        articles = (
            db.query(Article)
            .join(Source)
            .options(contains_eager(Article.source))
            .filter(
                Article.category_id == category.id,
                Article.ai_summary.isnot(None),
                Source.region == region,
                Source.is_active == True
            )
            .order_by(Article.importance_score.desc())
            .limit(3)
            .all()
        )
        
        # 2h. If category has articles, append to response
        if articles:
            feed_response.append({
                "id": category.id,
                "slug": category.slug,
                "name": category.name,
                "articles": articles
            })
            
    # 2i. Return the grouped list
    return feed_response
