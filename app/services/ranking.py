import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.models import Article, Source

logger = logging.getLogger(__name__)

GRAVITY_DEFAULT = 1.8

def calculate_initial_score(trust_score: float, published_at: datetime, gravity: float = GRAVITY_DEFAULT) -> float:
    """
    Calculates the importance score using a Hacker News-style time decay algorithm.
    Formula: Score = (trust_score) / ((age_in_hours + 2) ^ gravity)
    """
    current_time = datetime.now(timezone.utc)
    
    # Ensure published_at is timezone-aware for the math to work
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
        
    delta = current_time - published_at
    age_in_hours = delta.total_seconds() / 3600.0
    
    # Ensure age_in_hours is not negative (in case of future publish dates from RSS)
    if age_in_hours < 0:
        age_in_hours = 0.0
        
    score = trust_score / ((age_in_hours + 2.0) ** gravity)
    return score

def update_recent_article_scores(db: Session, gravity: float = GRAVITY_DEFAULT):
    """
    Bulk operation function to recalculate importance_score for articles published within the last 72 hours.
    Designed to be run periodically (e.g., by APScheduler).
    """
    logger.info("Starting bulk update of recent article scores...")
    try:
        # Calculate the threshold for 72 hours ago
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=72)
        
        # Query articles within the last 72 hours and join with sources to get trust_score
        recent_articles = db.query(Article, Source).join(
            Source, Article.source_id == Source.id
        ).filter(
            Article.published_at >= time_threshold
        ).all()
        
        if not recent_articles:
            logger.info("No recent articles found in the last 72 hours to update.")
            return

        # Prepare bulk update data
        update_mappings = []
        for article, source in recent_articles:
            new_score = calculate_initial_score(
                trust_score=source.trust_score, 
                published_at=article.published_at, 
                gravity=gravity
            )
            update_mappings.append({
                "id": article.id,
                "importance_score": new_score
            })
            
        # Perform bulk update
        if update_mappings:
            db.bulk_update_mappings(Article, update_mappings)
            db.commit()
            logger.info(f"Successfully updated importance_score for {len(update_mappings)} articles.")
            
    except Exception as e:
        logger.error(f"Error updating recent article scores: {e}")
        db.rollback()

def run_ranking_update():
    """
    Wrapper function to be called by APScheduler.
    Handles database session creation and closure.
    """
    from app.db.database import SessionLocal
    db: Session = SessionLocal()
    try:
        update_recent_article_scores(db)
    finally:
        db.close()
