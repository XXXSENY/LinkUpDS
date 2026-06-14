import logging
from fastapi import APIRouter, HTTPException, Depends, status

from src.db_utils import LinkUpDB
from src.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/likes",
    tags=["Likes"]
)

db = LinkUpDB()


@router.post("/{post_id}", status_code=status.HTTP_201_CREATED)
def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Liker un post."""
    
    user_id = current_user["userId"]
    
    # Vérifier que le post existe
    post = db.get_post(post_id)
    if not post:
        logger.warning(f"Like échoué : post {post_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post introuvable"
        )
    
    try:
        success = db.like_post(user_id, post_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors du like"
            )
        logger.info(f"{user_id} a liké le post {post_id}")
    except Exception as e:
        logger.error(f"Erreur lors du like du post {post_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du like"
        )
    
    return {
        "message": "Post liké",
        "post_id": post_id,
        "user_id": user_id
    }


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retirer un like d'un post."""
    
    user_id = current_user["userId"]
    
    # Vérifier que le post existe
    post = db.get_post(post_id)
    if not post:
        logger.warning(f"Unlike échoué : post {post_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post introuvable"
        )
    
    try:
        success = db.unlike_post(user_id, post_id)
        
        if not success:
            logger.warning(f"Unlike échoué : {user_id} n'avait pas liké {post_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous n'avez pas liké ce post"
            )
        
        logger.info(f"{user_id} a retiré son like du post {post_id}")
    except Exception as e:
        logger.error(f"Erreur lors du unlike du post {post_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du unlike"
        )
