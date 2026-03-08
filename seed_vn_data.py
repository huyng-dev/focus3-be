import sys
import os

# Make sure Python can recognize the root directory of the project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.models import Category, Source

# 1. English Categories (Source of Truth)
CATEGORIES = [
    {"slug": "technology", "name": "Technology"},
    {"slug": "finance", "name": "Finance & Business"},
    {"slug": "ai-robotics", "name": "AI & Robotics"},
]

# 2. Vietnamese Sources (Labeled for Perspective Radar)
SOURCES = [
    {
        "name": "VNExpress",
        "base_url": "https://vnexpress.net",
        "trust_score": 10.0,
        "slant": "objective",
        "region": "vn",
        "language": "vi"
    },
    {
        "name": "CafeF",
        "base_url": "https://cafef.vn",
        "trust_score": 8.5,
        "slant": "analytical",
        "region": "vn",
        "language": "vi"
    },
    {
        "name": "Dân Trí",
        "base_url": "https://dantri.com.vn",
        "trust_score": 9.0,
        "slant": "populist",
        "region": "vn",
        "language": "vi"
    },
    {
        "name": "GenK",
        "base_url": "https://genk.vn",
        "trust_score": 8.0,
        "slant": "analytical",
        "region": "vn",
        "language": "vi"
    },
    {
        "name": "VNEconomy",
        "base_url": "https://vneconomy.vn",
        "trust_score": 9.0,
        "slant": "objective",
        "region": "vn",
        "language": "vi"
    }
]

def seed_database():
    db: Session = SessionLocal()
    try:
        print("Seeding Categories (English)...")
        for cat_data in CATEGORIES:
            existing_cat = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing_cat:
                new_cat = Category(**cat_data)
                db.add(new_cat)
            else:
                # Update name if it was previously saved in Vietnamese or incorrect
                existing_cat.name = cat_data["name"]

        print("Seeding Sources (Vietnamese)...")
        for source_data in SOURCES:
            existing_source = db.query(Source).filter(Source.base_url == source_data["base_url"]).first()
            if not existing_source:
                new_source = Source(**source_data)
                db.add(new_source)
            else:
                # Update metadata for existing sources to ensure consistency
                existing_source.trust_score = source_data["trust_score"]
                existing_source.slant = source_data["slant"]
                existing_source.region = source_data["region"]
                existing_source.language = source_data["language"]

        # Commit entire transaction
        db.commit()
        print("✅ Completed seeding data for Focus3 system.")

    except Exception as e:
        db.rollback()
        print(f"❌ Transaction error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()