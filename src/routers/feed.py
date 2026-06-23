import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional

from src.db_utils import LinkUpDB
from src.models.post import PostResponse
from src.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)

db = LinkUpDB()


@router.get("/{user_id}", response_model=List[PostResponse])
def get_feed(
    user_id: str,
    skip: int = Query(0, ge=0, description="Nombre de posts à sauter"),
    limit: int = Query(20, ge=1, le=100, description="Nombre de posts à retourner"),
    smart: bool = Query(False, description="Activer le Smart Feed (tri par pertinence)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer le feed personnalisé d'un utilisateur (posts des utilisateurs suivis).
    
    Pagination avec skip/limit pour optimiser les requêtes.
    
    Args:
        user_id: ID de l'utilisateur
        skip: Nombre de posts à sauter (défaut: 0)
        limit: Nombre de posts à retourner (défaut: 20, max: 100)
        smart: Activer le Smart Feed pour trier par pertinence (défaut: False)
        current_user: Utilisateur courant (JWT)
    
    Returns:
        Liste des posts du feed, triés par date décroissante ou par pertinence (Smart Feed)
    """
    
    # Vérifier que l'utilisateur existe
    user = db.get_user(user_id)
    if not user:
        logger.warning(f"Feed : utilisateur {user_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    try:
        if smart:
            # Smart Feed: récupérer plus de posts et trier par pertinence
            feed = db.get_feed(
                user_id=user_id,
                limit=limit * 2,  # Récupérer plus pour le filtrage
                offset=skip,
            )
            scored_feed = _apply_smart_feed_scoring(user_id, feed)
            return scored_feed[:limit]
        else:
            # Feed classique: tri par date
            feed = db.get_feed(
                user_id=user_id,
                limit=limit,
                offset=skip,
            )
            logger.debug(f"Feed chargé pour {user_id} : {len(feed)} posts")
            return feed
    except Exception as e:
        logger.error(f"Erreur lors du chargement du feed : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du chargement du feed"
        )


def _apply_smart_feed_scoring(user_id: str, feed: List[dict]) -> List[dict]:
    """
    Applique le Smart Feed scoring aux posts du feed.
    
    Le scoring prend en compte:
    - Proximité sociale avec l'auteur (indicateurs de l'équipe 2)
    - Centralité de l'auteur (Betweenness/Closeness - métriques équipe 2)
    - Sentiment du post (positif priorisé)
    - Engagement (likes)
    - Récence
    - Topic matching (si l'utilisateur aime les mêmes thèmes)
    
    Args:
        user_id: ID de l'utilisateur courant
        feed: Liste des posts du feed
        
    Returns:
        Liste des posts triés par score de pertinence
    """
    if not feed:
        return []
    
    try:
        from src.recommendation.proximity import jaccard_similarity, interests_similarity
        from src.team2.centrality_analysis import CentralityAnalyzer
        from src.team2.extraction import GraphExtractor
        
        # Charger le graphe et calculer les centralités (cache possible)
        try:
            extractor = GraphExtractor()
            G = extractor.load_graph()
            analyzer = CentralityAnalyzer(G)
            analyzer.compute_centralities()
            betweenness_scores = analyzer.betweenness_scores
            closeness_scores = analyzer.closeness_scores
        except Exception as e:
            logger.warning(f"Impossible de charger les centralités: {e}")
            betweenness_scores = {}
            closeness_scores = {}
        
        # Récupérer les intérêts de l'utilisateur pour le topic matching
        try:
            from src.recommendation.graph_queries import get_user_interests
            user_interests = set(get_user_interests(user_id))
        except Exception:
            user_interests = set()
        
        scored_feed = []
        for post in feed:
            score = 0.0
            author_id = post.get("author", {}).get("userId") if post.get("author") else None
            
            # 1. Proximité sociale (25% du score)
            if author_id and author_id != user_id:
                try:
                    jac = jaccard_similarity(user_id, author_id)
                    int_sim = interests_similarity(user_id, author_id)
                    score += 0.15 * jac + 0.10 * int_sim
                except Exception:
                    pass
            
            # 2. Centralité de l'auteur (20% du score) - métriques équipe 2
            if author_id:
                betweenness = betweenness_scores.get(author_id, 0.0)
                closeness = closeness_scores.get(author_id, 0.0)
                # Les utilisateurs avec high betweenness sont des ponts stratégiques
                # Les utilisateurs avec high closeness diffusent l'info rapidement
                score += 0.12 * betweenness + 0.08 * closeness
            
            # 3. Sentiment du post (15% du score)
            sentiment = post.get("sentiment", "").lower()
            if sentiment == "positif":
                score += 0.15
            elif sentiment == "neutre":
                score += 0.05
            
            # 4. Engagement (20% du score)
            likes_count = post.get("likeCount", 0)
            engagement_score = min(likes_count / 5.0, 1.0)
            score += 0.20 * engagement_score
            
            # 5. Topic matching (10% du score)
            post_topic = post.get("detectedTopic")
            if post_topic and user_interests:
                if post_topic.lower() in [i.lower() for i in user_interests]:
                    score += 0.10
            
            # 6. Récence (10% du score)
            # Bonus basé sur l'ordre dans le feed (déjà trié par date)
            score += 0.10
            
            post["relevanceScore"] = round(score, 4)
            scored_feed.append(post)
        
        # Trier par score de pertinence
        scored_feed.sort(key=lambda x: x.get("relevanceScore", 0), reverse=True)
        
        # Log pour debug
        if scored_feed:
            top_score = scored_feed[0].get("relevanceScore", 0)
            bottom_score = scored_feed[-1].get("relevanceScore", 0)
            logger.debug(f"Smart Feed pour {user_id}: {len(scored_feed)} posts, score range: {bottom_score:.3f} - {top_score:.3f}")
        
        return scored_feed
    except Exception as e:
        logger.error(f"Erreur lors du Smart Feed scoring: {e}")
        # En cas d'erreur, retourner le feed non scoré
        return feed

