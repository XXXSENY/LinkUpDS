import logging
from fastapi import APIRouter, HTTPException, Depends, status

from src.db_utils import LinkUpDB
from src.models.post import PostCreate, PostResponse
from src.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

db = LinkUpDB()


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post: PostCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau post avec analyse automatique de sentiment et de topic."""
    
    try:
        new_post = db.create_post(
            user_id=current_user["userId"],
            content=post.content,
            topic=post.topic,
        )
        
        # Analyser automatiquement le sentiment du post
        from src.nlp.sentiment_analysis import analyze_sentiment
        sentiment_result = analyze_sentiment(post.content)
        
        # Analyser automatiquement le topic du post (approche directe sans reconstruction du modèle)
        from src.nlp.topic_modeling import get_dominant_topic
        try:
            dominant_topic = get_dominant_topic(post.content)
            topic_name = dominant_topic.get("topic_name") if dominant_topic else None
            topic_words = dominant_topic.get("words", [])[:5] if dominant_topic else []
            topic_confidence = dominant_topic.get("confidence", 0.0) if dominant_topic else 0.0
        except Exception as e:
            logger.warning(f"Topic modeling échoué: {e}")
            topic_name = None
            topic_words = []
            topic_confidence = 0.0
        
        # Mettre à jour le post avec le sentiment et le topic
        update_query = """
        MATCH (p:Post {postId: $post_id})
        SET p.sentiment = $label,
            p.sentimentPolarity = $polarity,
            p.sentimentSubjectivity = $subjectivity,
            p.detectedTopic = $topic_name,
            p.topicWords = $topic_words,
            p.topicConfidence = $topic_confidence
        RETURN p
        """
        db._execute_write(
            update_query,
            post_id=new_post.get("postId"),
            label=sentiment_result["label"],
            polarity=sentiment_result["polarity"],
            subjectivity=sentiment_result["subjectivity"],
            topic_name=topic_name,
            topic_words=topic_words,
            topic_confidence=topic_confidence,
        )
        
        # Ajouter le sentiment et le topic à la réponse
        new_post["sentiment"] = sentiment_result["label"]
        new_post["sentimentPolarity"] = sentiment_result["polarity"]
        new_post["detectedTopic"] = topic_name
        new_post["topicWords"] = topic_words
        
        logger.info(f"Post créé par {current_user['userId']} : {new_post.get('postId')} (sentiment: {sentiment_result['label']}, topic: {topic_name})")
        return new_post
    except ValueError as e:
        logger.error(f"Erreur lors de la création du post : {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur interne lors de la création du post : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du post"
        )


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: str):
    """Récupérer un post par son ID."""
    
    post = db.get_post(post_id)

    if not post:
        logger.warning(f"GET /posts/{post_id} : post non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post introuvable"
        )

    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer un post.
    ⚠️ Seul l'auteur du post peut le supprimer.
    """
    
    post = db.get_post(post_id)

    if not post:
        logger.warning(f"DELETE /posts/{post_id} : post non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post introuvable"
        )

    # Vérifier que l'utilisateur courant est l'auteur du post
    post_author_id = post.get("author", {}).get("userId")
    if post_author_id != current_user["userId"]:
        logger.warning(f"Tentative de suppression non autorisée : {current_user['userId']} -> post de {post_author_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que vos propres posts"
        )

    try:
        success = db.delete_post(post_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors de la suppression du post"
            )

        logger.info(f"Post {post_id} supprimé par {current_user['userId']}")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du post {post_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du post"
        )
