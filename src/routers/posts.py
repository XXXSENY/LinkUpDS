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
    """Créer un nouveau post."""
    
    try:
        new_post = db.create_post(
            user_id=current_user["userId"],
            content=post.content,
            topic=post.topic,
        )
        logger.info(f"Post créé par {current_user['userId']} : {new_post.get('postId')}")
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
