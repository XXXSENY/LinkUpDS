"""
Gestion de la sécurité : JWT, hashing password, etc.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from src.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hacher un mot de passe avec bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier qu'un mot de passe correspond à un hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du password : {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Créer un JWT access token.

    Args:
        data: dict contenant les données à encoder (ex: {"sub": user_id})
        expires_delta: durée de validité du token (défaut: 24h)

    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Erreur lors de la création du token : {e}")
        raise


def decode_access_token(token: str) -> Optional[dict]:
    """
    Décoder et valider un JWT token.

    Args:
        token: JWT token à décoder

    Returns:
        dict avec les données du token, ou None si invalide/expiré
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token invalide ou expiré : {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors du décodage du token : {e}")
        return None
