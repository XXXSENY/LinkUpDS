import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List

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
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer le feed personnalisé d'un utilisateur (posts des utilisateurs suivis).
    
    Pagination avec skip/limit pour optimiser les requêtes.
    
    Args:
        user_id: ID de l'utilisateur
        skip: Nombre de posts à sauter (défaut: 0)
        limit: Nombre de posts à retourner (défaut: 20, max: 100)
        current_user: Utilisateur courant (JWT)
    
    Returns:
        Liste des posts du feed, triés par date décroissante
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
        # Récupérer le feed avec pagination
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

