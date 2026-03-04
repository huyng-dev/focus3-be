# Focus3 Backend - AI-Powered News Aggregator

**Focus3** is an automated news aggregation platform powered by AI. This repository contains the **Backend API**, built with FastAPI and refactored for scalability and performance.

## 🎨 Features & Tech Stack
- **Backend:** FastAPI, Pydantic v2, APScheduler (Background Tasks).
- **Database:** PostgreSQL + **pgvector** (Vector search for AI features).
- **Caching:** Redis.
- **ORM:** SQLAlchemy 2.0 + Alembic for migrations.
- **Integrations:** RSS Scrapers, LLM Summarization support (OpenAI), TTS conversion.

---

## 📂 Project Structure
```text
.
├── app/                  # Main logic (API, Models, Services, Tasks)
├── alembic/              # Database migration versioning
├── tests/                # Unit and integration tests
├── .env.example          # Template for environment variables
├── Dockerfile            # Container definition for the app
├── docker-compose.yml    # Full service stack (API, DB, Redis, Adminer)
├── init.sql              # Database initialization script
└── requirements.txt      # Project dependencies
```

---

## 🚀 Getting Started

### Option 1: Docker (Fastest)
Ensure you have Docker & Docker Compose installed. From this directory:
```bash
docker-compose up -d --build
```
This will build the API and pull the required services (DB, Redis, Adminer).
- **API:** `http://localhost:8000`
- **Docs:** `http://localhost:8000/docs`
- **Adminer (Database Browser):** `http://localhost:8000:8080` (Server: `db`, Port: `5432`)

### Option 2: Local Setup
Prerequisites: Python 3.10+ and a running PostgreSQL instance with `pgvector` extension.

1. **Activate Virtual Environment:**
   ```bash
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Setup Database:**
   Ensure your `.env` file matches your local DB credentials.
4. **Start the API:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📡 Core API Endpoints (v1)
- `GET /`: Health check.
- `GET /api/v1/articles/`: List collected articles.
- `POST /api/v1/articles/trigger-scraper`: Trigger manual RSS crawl.

---
*This repository contains the backend core of Focus3.*
