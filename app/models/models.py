from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from pgvector.sqlalchemy import Vector
from app.db.database import Base

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(255), unique=True, nullable=False)
    trust_score = Column(Float, default=1.0)
    slant = Column(String(50), default="neutral")
    is_active = Column(Boolean, default=True)
    
    articles = relationship("Article", back_populates="source")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    
    articles = relationship("Article", back_populates="category")

class Article(Base):
    __tablename__ = "articles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    title = Column(String(500), nullable=False)
    original_url = Column(Text, unique=True, nullable=False)
    thumbnail_url = Column(Text)
    published_at = Column(DateTime(timezone=True), nullable=False)
    
    ai_summary = Column(JSONB)
    tts_audio_url = Column(Text)
    importance_score = Column(Float, default=0.0)
    
    # Vector column for 768 dimensions (e.g. BERT/MiniLM)
    content_embedding = Column(Vector(768)) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", back_populates="articles")
    category = relationship("Category", back_populates="articles")
