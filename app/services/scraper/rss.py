import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime
from sqlalchemy.orm import Session
from app.models.models import Article, Source, Category
from app.db.database import SessionLocal
from app.services.ranking import calculate_initial_score
from bs4 import BeautifulSoup

# RSS Feeds to scrape
RSS_FEEDS = [
    # --- Technology ---
    {
        "url": "https://vnexpress.net/rss/so-hoa.rss",
        "source_name": "VNExpress",
        "category_slug": "technology"
    },
    {
        "url": "https://dantri.com.vn/rss/suc-manh-so.rss",
        "source_name": "Dân Trí",
        "category_slug": "technology"
    },

    # --- Finance & Business ---
    {
        "url": "https://vnexpress.net/rss/kinh-doanh.rss",
        "source_name": "VNExpress",
        "category_slug": "finance"
    },
    {
        "url": "https://cafef.vn/tai-chinh-ngan-hang.rss",
        "source_name": "CafeF",
        "category_slug": "finance"
    },
    {
        "url": "https://vneconomy.vn/tai-chinh.rss",
        "source_name": "VNEconomy",
        "category_slug": "finance"
    },

    # --- AI & Robotics ---
    {
        "url": "https://genk.vn/rss/ai.rss",
        "source_name": "GenK",
        "category_slug": "ai-robotics"
    }
]

def extract_thumbnail(entry) -> str:
    """
    Extract thumbnail URL from feedparser entry using a 3-step fallback strategy.
    """
    # Step 1: Check standard Enclosure/Link (VNExpress case)
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type', '').startswith('image/'):
                return link.href

    # Step 2: Check Media RSS (VNEconomy case)
    # feedparser automatically parses <media:content> into list 'media_content'
    if hasattr(entry, 'media_content'):
        for media in entry.media_content:
            if 'url' in media and media.get('medium') == 'image':
                return media['url']
            # Sometimes 'medium' is missing, just take the URL if it has an image extension
            elif 'url' in media:
                return media['url']
                
    if hasattr(entry, 'media_thumbnail'):
        for media in entry.media_thumbnail:
            if 'url' in media:
                return media['url']

    # Step 3: Check HTML embedded in Description/Content (GenK, Dân Trí, CafeF)
    # feedparser automatically parses <description> into 'summary' and <content:encoded> into 'content'
    html_content = ""
    if hasattr(entry, 'content') and entry.content:
        html_content = entry.content[0].value
    elif hasattr(entry, 'summary'):
        html_content = entry.summary

    if html_content:
        # Use BeautifulSoup to safely extract <img> tag
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            return img_tag['src']

    # If all attempts fail, return an empty string
    return ""

def clean_html_text(raw_html: str) -> str:
    """Remove all HTML tags, leaving only plain text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # separator=" " helps prevent words from sticking together when removing tags
    return soup.get_text(separator=" ", strip=True)

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
            
            # Limit to top 20 entries per feed to avoid overloading
            for entry in feed.entries[:20]:
                # Check if article already exists
                exists = db.query(Article).filter(Article.original_url == entry.link).first()
                if exists:
                    continue
                
                # Extract publication time
                pub_date = parsedate_to_datetime(entry.published) if hasattr(entry, 'published') else datetime.now()
                
                # Extract image
                thumbnail = extract_thumbnail(entry)

                raw_description = entry.get('summary', '')
                clean_description = clean_html_text(raw_description)
                
                # Calculate initial importance score
                initial_score = calculate_initial_score(source.trust_score, pub_date)
                
                new_article = Article(
                    source_id=source.id,
                    category_id=category.id,
                    title=entry.title,
                    original_url=entry.link,
                    published_at=pub_date,
                    thumbnail_url=thumbnail,
                    description=clean_description,
                    importance_score=initial_score
                )
                db.add(new_article)
                new_articles_count += 1
                
            db.commit()
            print(f"[{feed_info['source_name']}] Saved {new_articles_count} new articles.")
            
        print(f"[{datetime.now()}] RSS scrape completed. Triggering AI processing pipeline...")
        from app.services.ai.processor import vectorize_incoming_articles, summarize_top_articles
        vectorize_incoming_articles(db)
        summarize_top_articles(db)
        print(f"[{datetime.now()}] AI processing pipeline completed.")
            
    except Exception as e:
        print(f"Error scraping data: {e}")
        db.rollback()
    finally:
        db.close()
