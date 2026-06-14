from fastapi import APIRouter, HTTPException, Depends, status
import logging

from src.db_utils import LinkUpDB
from src.models.auth import LoginRequest, RegisterRequest, Token
from src.models.user import UserResponse
from src.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from src.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

db = LinkUpDB()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: RegisterRequest):
    """Créer un nouvel utilisateur."""
    
    existing = db.get_user_by_email(user.email)

    if existing:
        logger.warning(f"Tentative de registration avec email existant : {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà utilisé"
        )

    try:
        new_user = db.create_user(
            name=user.name,
            email=user.email,
            password=hash_password(user.password),
            username=user.username,
            bio=user.bio,
            city=user.city,
        )
        logger.info(f"Nouvel utilisateur créé : {new_user.get('userId')}")
        return new_user
    except ValueError as e:
        logger.error(f"Erreur lors de la création de l'utilisateur : {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la création du compte",
        )


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest):
    """Authentifier un utilisateur et retourner un token JWT."""
    
    # Récupérer l'utilisateur avec password (méthode dédiée)
    user = db.get_user_auth_by_email(credentials.email)

    if not user:
        logger.warning(f"Login échoué : utilisateur {credentials.email} non trouvé")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides"
        )

    # Vérifier le password
    if not verify_password(
        credentials.password,
        user.get("password", "")
    ):
        logger.warning(f"Login échoué : password incorrect pour {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides"
        )

    # Créer le token JWT
    token = create_access_token(
        {"sub": user["userId"]}
    )

    logger.info(f"Login réussi pour {user['userId']}")
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Récupérer les informations de l'utilisateur courant."""
    return current_user

