import logging
from fastapi import FastAPI

from src.routers import (
    auth,
    users,
    posts,
    follows,
    likes,
    feed,
    recommendations,
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LinkUpDS API",
    description="Backend du réseau social LinkUpDS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enregistrer les routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(follows.router)
app.include_router(likes.router)
app.include_router(feed.router)
app.include_router(recommendations.router)


@app.on_event("startup")
async def startup_event():
    """Événement au démarrage de l'application."""
    from src.db_utils import LinkUpDB
    from src.nlp.sentiment_analysis import batch_update_posts_sentiment
    from src.nlp.topic_modeling import batch_update_posts_topics

    db = LinkUpDB()
    db.init_schema()
    
    # Analyser automatiquement le sentiment de TOUS les posts (réanalyse forcée)
    try:
        updated_count = batch_update_posts_sentiment(db, limit=500, reanalyze_all=True)
        logger.info(f"📊 Sentiment analysé pour {updated_count} posts au démarrage")
    except Exception as e:
        logger.warning(f"Impossible d'analyser le sentiment au démarrage: {e}")
    
    # Analyser automatiquement les topics de TOUS les posts (réanalyse forcée)
    try:
        updated_topics = batch_update_posts_topics(db, limit=500, reanalyze_all=True)
        logger.info(f"🏷️ Topics analysés pour {updated_topics} posts au démarrage")
    except Exception as e:
        logger.warning(f"Impossible d'analyser les topics au démarrage: {e}")
    
    db.close()
    logger.info("🚀 LinkUpDS API démarrée")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement à l'arrêt de l'application."""
    logger.info("🛑 LinkUpDS API arrêtée")


@app.get("/health")
def health_check():
    """Vérifier l'état de l'API."""
    return {
        "status": "ok",
        "service": "LinkUpDS API"
    }