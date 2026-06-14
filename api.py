import logging
from fastapi import FastAPI

from src.routers import (
    auth,
    users,
    posts,
    follows,
    likes,
    feed,
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


@app.on_event("startup")
async def startup_event():
    """Événement au démarrage de l'application."""
    from src.db_utils import LinkUpDB

    db = LinkUpDB()
    db.init_schema()
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