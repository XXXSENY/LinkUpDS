"""
src/routers/recommendations.py
==============================
API endpoints pour le système de recommandation de LinkUpDS.

Expose les endpoints pour:
- Recommandations d'amis (Link Prediction)
- Smart Feed (Fil d'actualité intelligent)

Auteur : Équipe 3 (NLP & Recommandation)
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel

from src.dependencies.auth import get_current_user
from src.recommendation.pipeline import (
    generate_recommendations,
    get_recommendations_with_details,
)
from src.db_utils import LinkUpDB

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

db = LinkUpDB()


# =========================
# MODELES
# =========================

class RecommendationResponse(BaseModel):
    """Modèle de réponse pour une recommandation."""
    user_id: str
    common_neighbors: int
    jaccard: float
    adamic_adar: float
    interest_similarity: float
    final_score: float
    common_interests: Optional[List[str]] = None
    common_interests_count: Optional[int] = None


class SmartFeedItem(BaseModel):
    """Modèle de réponse pour un item du Smart Feed."""
    post_id: str
    content: str
    author_id: str
    author_name: str
    created_at: str
    likes_count: int
    relevance_score: float
    sentiment: Optional[str] = None
    topic: Optional[str] = None


# =========================
# ENDPOINTS RECOMMANDATIONS AMIS
# =========================

@router.get("/friends", response_model=List[RecommendationResponse])
def get_friend_recommendations(
    user_id: str,
    top_n: int = Query(10, ge=1, le=50, description="Nombre de recommandations"),
    with_details: bool = Query(True, description="Inclure les détails d'intérêts"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtenir des recommandations d'amis basées sur la proximité dans le graphe.

    Utilise les indicateurs de proximité (Common Neighbors, Jaccard, Adamic-Adar)
    et la similarité des intérêts pour recommander des utilisateurs à suivre.

    Args:
        user_id: ID de l'utilisateur pour lequel générer les recommandations
        top_n: Nombre de recommandations à retourner (défaut: 10, max: 50)
        with_details: Inclure les détails des intérêts communs (défaut: True)
        current_user: Utilisateur courant (JWT)

    Returns:
        Liste des recommandations triées par score de pertinence
    """
    # Vérifier que l'utilisateur existe
    user = db.get_user(user_id)
    if not user:
        logger.warning(f"Recommandations: utilisateur {user_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    try:
        if with_details:
            recommendations = get_recommendations_with_details(user_id, top_n=top_n)
        else:
            recommendations = generate_recommendations(user_id, top_n=top_n)

        logger.debug(f"Recommandations générées pour {user_id}: {len(recommendations)}")
        return recommendations
    except Exception as e:
        logger.error(f"Erreur lors de la génération des recommandations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération des recommandations"
        )


@router.get("/friends/{user_id}", response_model=List[RecommendationResponse])
def get_friend_recommendations_by_id(
    user_id: str,
    top_n: int = Query(10, ge=1, le=50),
    with_details: bool = Query(True),
    current_user: dict = Depends(get_current_user)
):
    """Endpoint alternatif avec user_id dans le chemin."""
    return get_friend_recommendations(user_id, top_n, with_details, current_user)


# =========================
# SMART FEED
# =========================

@router.get("/feed/{user_id}", response_model=List[SmartFeedItem])
def get_smart_feed(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="Nombre de posts"),
    skip: int = Query(0, ge=0, description="Nombre de posts à sauter"),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtenir un fil d'actualité intelligent (Smart Feed).

    Le Smart Feed priorise les posts en fonction de:
    - Proximité sociale avec l'auteur (indicateurs de l'équipe 2)
    - Sentiment du post (positif priorisé)
    - Pertinence des thèmes
    - Engagement (likes)

    Args:
        user_id: ID de l'utilisateur
        limit: Nombre de posts à retourner (défaut: 20, max: 100)
        skip: Nombre de posts à sauter (pagination)
        current_user: Utilisateur courant (JWT)

    Returns:
        Liste des posts du Smart Feed triés par score de pertinence
    """
    # Vérifier que l'utilisateur existe
    user = db.get_user(user_id)
    if not user:
        logger.warning(f"Smart Feed: utilisateur {user_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    try:
        # Récupérer le feed de base
        feed = db.get_feed(user_id=user_id, limit=limit * 2, offset=skip)

        if not feed:
            return []

        # Calculer les scores de pertinence
        scored_feed = []
        for post in feed:
            relevance_score = _calculate_relevance_score(user_id, post)
            scored_feed.append({
                "post_id": post.get("postId"),
                "content": post.get("content"),
                "author_id": post.get("authorId"),
                "author_name": post.get("authorName", "Unknown"),
                "created_at": post.get("createdAt"),
                "likes_count": post.get("likesCount", 0),
                "relevance_score": relevance_score,
                "sentiment": post.get("sentiment"),
                "topic": post.get("topic"),
            })

        # Trier par score de pertinence
        scored_feed.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Appliquer la limite
        return scored_feed[:limit]
    except Exception as e:
        logger.error(f"Erreur lors du chargement du Smart Feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du chargement du Smart Feed"
        )


def _calculate_relevance_score(user_id: str, post: dict) -> float:
    """
    Calcule un score de pertinence pour un post dans le Smart Feed.

    Facteurs pris en compte:
    - Proximité sociale avec l'auteur (via les indicateurs de l'équipe 2)
    - Sentiment du post (positif = bonus)
    - Engagement (likes)
    - Récence

    Args:
        user_id: ID de l'utilisateur courant
        post: Dictionnaire contenant les informations du post

    Returns:
        float: Score de pertinence entre 0 et 1
    """
    from src.recommendation.proximity import jaccard_similarity, interests_similarity

    score = 0.0

    # 1. Proximité sociale (40% du score)
    author_id = post.get("authorId")
    if author_id and author_id != user_id:
        try:
            jac = jaccard_similarity(user_id, author_id)
            int_sim = interests_similarity(user_id, author_id)
            score += 0.3 * jac + 0.1 * int_sim
        except Exception:
            pass

    # 2. Sentiment (20% du score)
    sentiment = post.get("sentiment", "").lower()
    if sentiment == "positif":
        score += 0.2
    elif sentiment == "neutre":
        score += 0.1
    # Negatif = 0 bonus

    # 3. Engagement (20% du score)
    likes_count = post.get("likesCount", 0)
    engagement_score = min(likes_count / 10.0, 1.0)  # Cap à 10 likes
    score += 0.2 * engagement_score

    # 4. Récence (20% du score) - posts récents prioritaires
    # Pour simplifier, on donne un bonus fixe pour l'instant
    score += 0.2

    return round(score, 4)


# =========================
# ANALYSE DE SENTIMENT
# =========================

@router.post("/sentiment/analyze/{post_id}")
def analyze_post_sentiment(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyser le sentiment d'un post et le mettre à jour dans la base.

    Args:
        post_id: ID du post à analyser
        current_user: Utilisateur courant (JWT)

    Returns:
        Résultat de l'analyse de sentiment
    """
    from src.nlp.sentiment_analysis import update_post_sentiment

    try:
        success = update_post_sentiment(db, post_id)
        if success:
            return {"ok": True, "message": "Sentiment analysé et mis à jour"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors de l'analyse du sentiment"
            )
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse de sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse de sentiment"
        )


@router.post("/sentiment/batch")
def batch_analyze_sentiment(
    limit: int = Query(100, ge=1, le=1000),
    reanalyze_all: bool = Query(False, description="Ré-analyser tous les posts"),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyser le sentiment de plusieurs posts en batch.

    Args:
        limit: Nombre maximum de posts à analyser
        reanalyze_all: Si True, ré-analyse tous les posts (même ceux déjà analysés)
        current_user: Utilisateur courant (JWT)

    Returns:
        Nombre de posts analysés
    """
    from src.nlp.sentiment_analysis import batch_update_posts_sentiment

    try:
        updated_count = batch_update_posts_sentiment(db, limit=limit, reanalyze_all=reanalyze_all)
        return {
            "ok": True,
            "updated_count": updated_count,
            "reanalyze_all": reanalyze_all,
            "message": f"{updated_count} posts analysés"
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse batch"
        )


@router.get("/debug/posts")
def debug_posts(
    limit: int = Query(5, ge=1, le=20)
):
    """
    Endpoint de debug pour vérifier les données des posts dans Neo4j.
    """
    query = """
    MATCH (p:Post)
    RETURN p.postId AS postId, p.content AS content, p.sentiment AS sentiment, p.detectedTopic AS detectedTopic, p.topicWords AS topicWords
    LIMIT $limit
    """
    
    try:
        rows = db._execute_read(query, limit=limit)
        posts = []
        for row in rows:
            posts.append({
                "postId": row["postId"],
                "content": row["content"],
                "sentiment": row["sentiment"],
                "detectedTopic": row["detectedTopic"],
                "topicWords": row["topicWords"]
            })
        return {
            "ok": True,
            "posts": posts,
            "count": len(posts)
        }
    except Exception as e:
        logger.error(f"Erreur debug posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du debug"
        )


# =========================
# ANALYSE DE TOPICS
# =========================

@router.post("/topics/analyze/{post_id}")
def analyze_post_topic(
    post_id: str, 
    method: str = Query("keywords", description="Méthode: 'keywords' ou 'lda'"),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyser le topic d'un post spécifique.
    
    Args:
        post_id: ID du post à analyser
        method: Méthode de détection ('keywords' ou 'lda')
        current_user: Utilisateur courant (JWT)
    
    Returns:
        Résultat de l'analyse de topic
    """
    try:
        post = db.get_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post non trouvé")
        
        content = post.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="Post sans contenu")
        
        from src.nlp.topic_modeling import get_dominant_topic
        dominant_topic = get_dominant_topic(content, method=method)
        
        if not dominant_topic:
            return {"post_id": post_id, "detectedTopic": None, "topicWords": [], "confidence": 0.0, "method": method}
        
        return {
            "post_id": post_id,
            "detectedTopic": dominant_topic.get("topic_name"),
            "topicWords": dominant_topic.get("words", [])[:5],
            "confidence": dominant_topic.get("confidence", 0.0),
            "method": dominant_topic.get("method", method),
        }
    except Exception as e:
        logger.error(f"Erreur analyse topic: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'analyse")


@router.post("/topics/batch")
def batch_analyze_topics(
    limit: int = Query(100, ge=1, le=1000),
    reanalyze_all: bool = Query(False, description="Ré-analyser tous les posts"),
    method: str = Query("keywords", description="Méthode: 'keywords' ou 'lda'"),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyser les topics de plusieurs posts en batch.
    
    Args:
        limit: Nombre maximum de posts à analyser
        reanalyze_all: Si True, ré-analyse tous les posts (sinon seulement ceux sans topic)
        method: Méthode de détection ('keywords' ou 'lda')
        current_user: Utilisateur courant (JWT)
    
    Returns:
        Nombre de posts mis à jour
    """
    from src.nlp.topic_modeling import batch_update_posts_topics
    
    try:
        updated_count = batch_update_posts_topics(db, limit=limit, reanalyze_all=reanalyze_all)
        return {
            "ok": True,
            "updated_count": updated_count,
            "reanalyze_all": reanalyze_all,
            "method": method,
            "message": f"{updated_count} posts analysés avec méthode {method}"
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse batch topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse batch"
        )
