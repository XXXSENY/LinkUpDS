import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query

from src.db_utils import LinkUpDB
from src.models.user import UserResponse, UserUpdate
from src.models.post import PostResponse
from src.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

db = LinkUpDB()


@router.get("/{user_id}/followers", response_model=List[UserResponse])
def get_user_followers(user_id: str):
    """Récupérer la liste des abonnés d'un utilisateur."""

    user = db.get_user(user_id)
    if not user:
        logger.warning(f"GET /users/{user_id}/followers : utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    try:
        followers = db.get_followers(user_id)
        logger.debug(f"Followers chargés pour {user_id} : {len(followers)}")
        return followers
    except Exception as e:
        logger.error(f"Erreur lors du chargement des followers de {user_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du chargement des abonnés",
        )


@router.get("/{user_id}/following", response_model=List[UserResponse])
def get_user_following(user_id: str):
    """Récupérer la liste des abonnements d'un utilisateur."""

    user = db.get_user(user_id)
    if not user:
        logger.warning(f"GET /users/{user_id}/following : utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    try:
        following = db.get_following(user_id)
        logger.debug(f"Following chargé pour {user_id} : {len(following)}")
        return following
    except Exception as e:
        logger.error(f"Erreur lors du chargement du following de {user_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du chargement des abonnements",
        )


@router.get("/{user_id}/posts", response_model=List[PostResponse])
def get_user_posts(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="Nombre de posts à retourner"),
):
    """Récupérer les publications d'un utilisateur."""

    user = db.get_user(user_id)
    if not user:
        logger.warning(f"GET /users/{user_id}/posts : utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    try:
        posts = db.get_posts_by_user(user_id, limit=limit)
        logger.debug(f"Posts chargés pour {user_id} : {len(posts)}")
        return posts
    except Exception as e:
        logger.error(f"Erreur lors du chargement des posts de {user_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors du chargement des publications",
        )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str):
    """Récupérer les informations publiques d'un utilisateur."""
    
    user = db.get_user(user_id)

    if not user:
        logger.warning(f"GET /users/{user_id} : utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Mettre à jour le profil d'un utilisateur.
    ⚠️ Chaque utilisateur ne peut modifier que son propre profil.
    """
    
    # Vérification de permission : ne modifier que son propre profil
    if current_user["userId"] != user_id:
        logger.warning(f"Tentative de modification non autorisée : {current_user['userId']} -> {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez modifier que votre propre profil"
        )

    user = db.get_user(user_id)
    if not user:
        logger.warning(f"PUT /users/{user_id} : utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    try:
        updated_user = db.update_user(
            user_id=user_id,
            name=user_update.name,
            bio=user_update.bio,
            city=user_update.city,
            interests=user_update.interests,
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors de la mise à jour"
            )

        logger.info(f"Profil de {user_id} mis à jour")
        return updated_user
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de {user_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du profil"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer un compte utilisateur.
    ⚠️ Chaque utilisateur ne peut supprimer que son propre compte.
    """
    
    # Vérification de permission : ne supprimer que son propre compte
    if current_user["userId"] != user_id:
        logger.warning(f"Tentative de suppression non autorisée : {current_user['userId']} -> {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que votre propre compte"
        )

    user = db.get_user(user_id)
    if not user:
        logger.warning(f"DELETE /users/{user_id} : utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    try:
        success = db.delete_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors de la suppression"
            )

        logger.info(f"Compte utilisateur {user_id} supprimé")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de {user_id} : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression du compte"
        )

