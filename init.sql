-- Activate pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Sources table (News sources)
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    base_url VARCHAR(255) UNIQUE NOT NULL,
    trust_score FLOAT DEFAULT 1.0,
    slant VARCHAR(50) DEFAULT 'neutral',
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. Categories table (Categories)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);

-- 3. Articles table (Articles - Heart of the system)
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id INT REFERENCES sources(id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(id),
    title VARCHAR(500) NOT NULL,
    original_url TEXT UNIQUE NOT NULL,
    thumbnail_url TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    ai_summary JSONB,
    tts_audio_url TEXT,
    importance_score FLOAT DEFAULT 0.0,
    content_embedding vector(768), -- Ready for all-MiniLM model
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Events & event_articles table (Perspective Radar)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    category_id INT REFERENCES categories(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_articles (
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, article_id)
);

-- CREATE INDEXING FOR OPTIMIZE PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_articles_category_published ON articles (category_id, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_embedding ON articles USING hnsw (content_embedding vector_cosine_ops);

-- Insert some sample data
INSERT INTO categories (slug, name) VALUES 
('cong-nghe', 'Công nghệ'), 
('tai-chinh', 'Tài chính'), 
('ai-robotics', 'AI & Robotics') ON CONFLICT DO NOTHING;