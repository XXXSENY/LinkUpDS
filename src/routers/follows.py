import logging
from fastapi import APIRouter, HTTPException, Depends, status

from src.db_utils import LinkUpDB
from src.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/follows",
    tags=["Follows"]
)

db = LinkUpDB()


@router.post("/{followed_id}", status_code=status.HTTP_201_CREATED)
def follow_user(
    followed_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Suivre un utilisateur."""
    
    follower_id = current_user["userId"]
    
    # Vérifier qu'on ne se suit pas soi-même
    if follower_id == followed_id:
        logger.warning(f"Tentative d'auto-suivi : {follower_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas vous suivre vous-même"
        )
    
    # Vérifier que l'utilisateur suivi existe
    followed_user = db.get_user(followed_id)
    if not followed_user:
        logger.warning(f"Suivi échoué : utilisateur {followed_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    try:
        success = db.follow(follower_id, followed_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors du suivi"
            )
        logger.info(f"{follower_id} suit maintenant {followed_id}")
    except ValueError as e:
        logger.error(f"Erreur lors du suivi : {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erreur interne lors du suivi : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du suivi"
        )
    
    return {
        "message": f"Vous suivez maintenant {followed_user.get('username', followed_user['name'])}",
        "followed_id": followed_id
    }


@router.delete("/{followed_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    followed_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Arrêter de suivre un utilisateur."""
    
    follower_id = current_user["userId"]
    
    # Vérifier que l'utilisateur suivi existe
    followed_user = db.get_user(followed_id)
    if not followed_user:
        logger.warning(f"Unfollow échoué : utilisateur {followed_id} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )
    
    try:
        success = db.unfollow(follower_id, followed_id)
        
        if not success:
            logger.warning(f"Unfollow échoué : {follower_id} ne suivait pas {followed_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous ne suivez pas cet utilisateur"
            )
        
        logger.info(f"{follower_id} ne suit plus {followed_id}")
    except Exception as e:
        logger.error(f"Erreur lors de l'unfollow : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'arrêt du suivi"
        )
