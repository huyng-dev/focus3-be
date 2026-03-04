import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime
from sqlalchemy.orm import Session
from app.models.models import Article, Source, Category
from app.db.database import SessionLocal

# RSS Feeds to scrape
RSS_FEEDS = [
    {
        "url": "https://vnexpress.net/rss/so-hoa.rss",
        "source_name": "VNExpress",
        "category_slug": "cong-nghe"
    },
    {
        "url": "https://vneconomy.vn/tai-chinh.rss",
        "source_name": "VNEconomy",
        "category_slug": "tai-chinh"
    }
]

def fetch_and_save_articles():
    db: Session = SessionLocal()
    try:
        print(f"[{datetime.now()}] Starting to scrape RSS feeds...")
        
        for feed_info in RSS_FEEDS:
            # 1. Find or create Source
            source = db.query(Source).filter(Source.name == feed_info["source_name"]).first()
            if not source:
                source = Source(name=feed_info["source_name"], base_url=feed_info["url"])
                db.add(source)
                db.commit()
                db.refresh(source)
                
            # 2. Find Category
            category = db.query(Category).filter(Category.slug == feed_info["category_slug"]).first()
            if not category:
                print(f"Category {feed_info['category_slug']} not found in DB. Skipping.")
                continue

            # 3. Parse RSS Feed
            feed = feedparser.parse(feed_info["url"])
            new_articles_count = 0
            
            for entry in feed.entries:
                # Check if article already exists
                exists = db.query(Article).filter(Article.original_url == entry.link).first()
                if exists:
                    continue
                
                # Extract publication time
                pub_date = parsedate_to_datetime(entry.published) if hasattr(entry, 'published') else datetime.now()
                
                # Extract image
                thumbnail = ""
                if hasattr(entry, 'links'):
                    for link in entry.links:
                        if link.get('type', '').startswith('image/'):
                            thumbnail = link.href
                            break
                
                new_article = Article(
                    source_id=source.id,
                    category_id=category.id,
                    title=entry.title,
                    original_url=entry.link,
                    published_at=pub_date,
                    thumbnail_url=thumbnail
                )
                db.add(new_article)
                new_articles_count += 1
                
            db.commit()
            print(f"[{feed_info['source_name']}] Saved {new_articles_count} new articles.")
            
    except Exception as e:
        print(f"Error scraping data: {e}")
        db.rollback()
    finally:
        db.close()
