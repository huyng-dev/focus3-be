from app.db.database import SessionLocal
from app.services.ai.audio_briefing import generate_daily_briefing
def test_briefing():
    db = SessionLocal()
    try:
        print("Starting manual briefing generation...")
        result = generate_daily_briefing(db, region="vn")
        if result:
            print(f"Success! Briefing created: {result.audio_url}")
        else:
            print("Failed to generate briefing (maybe no articles?)")
    finally:
        db.close()
if __name__ == "__main__":
    test_briefing()