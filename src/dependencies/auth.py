"""
Dépendances d'authentification FastAPI.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.utils.security import decode_access_token
from src.db_utils import LinkUpDB

logger = logging.getLogger(__name__)

security = HTTPBearer()
db = LinkUpDB()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dépendance pour récupérer l'utilisateur courant via JWT.
    À utiliser avec Depends(get_current_user) dans les routes protégées.
    
    Lève HTTPException 401 si le token est invalide ou expiré.
    
    Returns:
        dict: Données de l'utilisateur sans le password
    """
    token = credentials.credentials
    
    # Décoder le token
    payload = decode_access_token(token)
    
    if payload is None:
        logger.warning("Tentative d'accès avec token invalide")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    
    if user_id is None:
        logger.warning("Token valide mais sans user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Récupérer l'utilisateur de la BD
    user = db.get_user(user_id)
    
    if user is None:
        logger.warning(f"Utilisateur {user_id} non trouvé en BD")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

