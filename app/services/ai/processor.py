import os
import json
import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from sentence_transformers import SentenceTransformer
from openai import OpenAI

from app.models.models import Article, Category
from app.core.config import settings

logger = logging.getLogger(__name__)

# 1. Initialization:
# Initialize OpenAI client for OpenRouter
openrouter_api_key = os.getenv("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY)
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
)

# Initialize SentenceTransformer globally so it loads into RAM only once
logger.info("Loading sentence-transformers model...")
try:
    embedding_model = SentenceTransformer('all-mpnet-base-v2')
except Exception as e:
    logger.error(f"Failed to load sentence-transformers model globally: {e}")
    embedding_model = None


def vectorize_incoming_articles(db: Session, batch_size: int = 50):
    """
    Mass embedding for the "Perspective Radar" feature. Free local execution.
    Combines title and description to generate a 768-dimensional vector using the local embedder.
    """
    if not embedding_model:
        logger.error("Embedding model not loaded. Skipping vectorization.")
        return

    try:
        # Query up to batch_size articles where content_embedding IS NULL and length(description) > 10
        articles = db.query(Article).filter(
            Article.content_embedding.is_(None),
            Article.description.isnot(None),
            func.length(Article.description) > 10
        ).limit(batch_size).all()

        if not articles:
            logger.info("No new articles to vectorize.")
            return

        logger.info(f"Vectorizing {len(articles)} articles.")

        for article in articles:
            try:
                # Combine title and description
                text_to_embed = f"{article.title}. {article.description}"
                
                # Generate a 768-dimensional vector using the local embedder
                embedding_vector = embedding_model.encode(text_to_embed).tolist()
                
                # Update content_embedding
                article.content_embedding = embedding_vector
                
                # Commit the transaction per article per instructions
                db.commit()
                logger.info(f"Vectorized article ID: {article.id}")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to vectorize article ID {article.id}: {e}")

    except Exception as e:
        logger.error(f"Error querying articles for vectorization: {e}")
        db.rollback()

LANGUAGE_MAP = {
    "vi": "Tiếng Việt",
    "en": "English"
}

def summarize_top_articles(db: Session):
    """
    Lazy summarization. Spend API tokens ONLY on articles that make it to the Top 3 feed
    of the homepage for each category.
    """
    try:
        categories = db.query(Category).all()
        
        for category in categories:
            # For each category, query the top 3 articles
            # CRITICAL: Order the query by Article.importance_score.desc()
            top_articles = db.query(Article).filter(
                Article.category_id == category.id,
                Article.ai_summary.is_(None),
                Article.description.isnot(None),
                func.length(Article.description) > 50
            ).order_by(Article.importance_score.desc()).limit(3).all()
            
            if not top_articles:
                continue
                
            logger.info(f"Summarizing {len(top_articles)} top articles for category {category.slug}.")
            
            for article in top_articles:
                try:
                    source_lang_code = article.source.language if article.source else 'en'
                    target_lang_name = LANGUAGE_MAP.get(source_lang_code, "English")
                    logger.info(f'Current language: {target_lang_name}')
    
                    # Truncate the article's description to a maximum of 800 characters to save tokens
                    desc_text = article.description
                    if len(desc_text) > 800:
                        desc_text = desc_text[:797] + "..."
                        
                    # Prompt Engineering
                    prompt = f"""
                    You are an expert news editor. Summarize the following news article based on its title and description.
                    Strictly output EXACTLY 3 short bullet points (under 20 words each).
                    Important: The entire output MUST be in {target_lang_name}. Do not use any other languages except for essential technical terms.
                    
                    Title: {article.title}
                    Description: {desc_text}
                    """
                    
                    response = openrouter_client.chat.completions.create(
                        model="google/gemma-3-27b-it",
                        messages=[
                            {"role": "system", "content": f"You are a helpful AI news editor that strictly outputs valid JSON. Return ONLY a JSON object in this format: {{\"summary\": [\"Point 1\", \"Point 2\", \"Point 3\"]}}. All content inside the JSON values must be written in {target_lang_name}."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2
                    )
                    
                    content = response.choices[0].message.content
                    if not content:
                        raise ValueError("Received empty content from OpenRouter")
                    
                    # Parse the JSON and update the ai_summary JSONB column
                    ai_summary_dict = json.loads(content)
                    
                    # Double-check the dict format. We don't enforce exact 3 points here just in case,
                    # but the prompt strongly insists on it.
                    if "summary" not in ai_summary_dict:
                        raise ValueError(f"Missing 'summary' key in JSON response: {ai_summary_dict}")
                        
                    article.ai_summary = ai_summary_dict
                    
                    db.commit()
                    logger.info(f"Successfully summarized article ID: {article.id}")
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"Failed to summarize article ID {article.id}: {e}")
                    
    except Exception as e:
        logger.error(f"Error querying categories/articles for summarization: {e}")
        db.rollback()
