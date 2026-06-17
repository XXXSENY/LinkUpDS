"""
src/recommendation/graph_queries.py
====================================
Briques de base pour la lecture du graphe social Neo4j.
Utilisé par :
  - Oumou  → calcul des indicateurs de proximité (Jaccard, Common Neighbors, Adamic-Adar)
  - Ibrahima → pipeline de génération de candidats (link prediction)

Pattern de connexion : réutilise LinkUpDB (src/db_utils.py) — même driver,
même gestion de session, même credentials .env. Aucune connexion dupliquée.

Usage :
    from src.recommendation.graph_queries import (
        get_following_ids,
        get_followers_ids,
        get_user_interests,
        get_second_degree_candidates,
        get_all_user_ids,
        user_exists,
    )
"""

from __future__ import annotations

import logging
from typing import List

from src.db_utils import LinkUpDB

logger = logging.getLogger(__name__)

# Instance partagée — même pattern que src/routers/*.py
# Lit NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD depuis .env via src/config.py
_db = LinkUpDB()


# =============================================================================
# VOISINAGE DIRECT
# =============================================================================

def get_following_ids(user_id: str) -> List[str]:
    """
    Retourne les userId que user_id suit (arêtes FOLLOWS sortantes).

    Paramètres
    ----------
    user_id : str
        Identifiant de l'utilisateur source.

    Retour
    ------
    List[str]
        Liste des userId suivis. Liste vide si user_id inexistant ou ne suit personne.

    Exemple
    -------
    >>> ids = get_following_ids("user_abc123")
    >>> print(ids)  # ["user_def456", "user_ghi789"]
    """
    query = """
    MATCH (u:User {userId: $user_id})-[:FOLLOWS]->(followed:User)
    RETURN followed.userId AS userId
    """
    try:
        rows = _db._execute_read(query, user_id=user_id)
        return [r["userId"] for r in rows]
    except Exception as e:
        logger.error(f"get_following_ids({user_id}): {e}")
        return []


def get_followers_ids(user_id: str) -> List[str]:
    """
    Retourne les userId qui suivent user_id (arêtes FOLLOWS entrantes).

    Paramètres
    ----------
    user_id : str
        Identifiant de l'utilisateur cible.

    Retour
    ------
    List[str]
        Liste des userId followers. Liste vide si user_id inexistant ou sans followers.

    Exemple
    -------
    >>> ids = get_followers_ids("user_abc123")
    >>> print(ids)  # ["user_xyz111", "user_xyz222"]
    """
    query = """
    MATCH (follower:User)-[:FOLLOWS]->(u:User {userId: $user_id})
    RETURN follower.userId AS userId
    """
    try:
        rows = _db._execute_read(query, user_id=user_id)
        return [r["userId"] for r in rows]
    except Exception as e:
        logger.error(f"get_followers_ids({user_id}): {e}")
        return []


# =============================================================================
# INTÉRÊTS
# =============================================================================

def get_user_interests(user_id: str) -> List[str]:
    """
    Retourne les centres d'intérêt déclarés par l'utilisateur.

    Paramètres
    ----------
    user_id : str
        Identifiant de l'utilisateur.

    Retour
    ------
    List[str]
        Liste des intérêts (ex. ["sport", "musique", "voyage"]).
        Liste vide si user_id inexistant ou si le champ interests est null/vide.

    Exemple
    -------
    >>> interests = get_user_interests("user_abc123")
    >>> print(interests)  # ["sport", "musique", "voyage"]
    """
    query = """
    MATCH (u:User {userId: $user_id})
    RETURN coalesce(u.interests, []) AS interests
    """
    try:
        rows = _db._execute_read(query, user_id=user_id)
        if not rows:
            return []
        return list(rows[0]["interests"])
    except Exception as e:
        logger.error(f"get_user_interests({user_id}): {e}")
        return []


# =============================================================================
# CANDIDATS SECOND DEGRÉ (pipeline Ibrahima)
# =============================================================================

def get_second_degree_candidates(user_id: str, limit: int = 50) -> List[str]:
    """
    Retourne les userId à distance 2 dans le graphe FOLLOWS.

    Définition : comptes suivis par les comptes que user_id suit déjà,
    en excluant user_id lui-même et ses followings directs (déjà connus).
    Ces candidats sont la base du pipeline de link prediction.

    Paramètres
    ----------
    user_id : str
        Identifiant de l'utilisateur pour lequel générer les candidats.
    limit : int, optionnel
        Nombre maximum de candidats retournés. Défaut : 50.

    Retour
    ------
    List[str]
        Liste des userId candidats (non triés — le scoring est fait en aval).
        Liste vide si user_id inexistant ou aucun candidat trouvé.

    Exemple
    -------
    >>> candidates = get_second_degree_candidates("user_abc123", limit=20)
    >>> print(len(candidates))  # ex. 14
    """
    query = """
    MATCH (u:User {userId: $user_id})-[:FOLLOWS]->(intermediate:User)-[:FOLLOWS]->(candidate:User)
    WHERE candidate.userId <> $user_id
      AND NOT (u)-[:FOLLOWS]->(candidate)
    RETURN DISTINCT candidate.userId AS userId
    LIMIT $limit
    """
    try:
        rows = _db._execute_read(query, user_id=user_id, limit=limit)
        return [r["userId"] for r in rows]
    except Exception as e:
        logger.error(f"get_second_degree_candidates({user_id}): {e}")
        return []


# =============================================================================
# UTILITAIRES
# =============================================================================

def get_all_user_ids() -> List[str]:
    """
    Retourne la liste de tous les userId présents en base.

    Utile pour les tests, la validation et les boucles de calcul batch.

    Retour
    ------
    List[str]
        Liste complète des userId. Liste vide si la base est vide.

    Exemple
    -------
    >>> all_ids = get_all_user_ids()
    >>> print(len(all_ids))  # 30
    """
    query = """
    MATCH (u:User)
    RETURN u.userId AS userId
    ORDER BY u.userId
    """
    try:
        rows = _db._execute_read(query)
        return [r["userId"] for r in rows]
    except Exception as e:
        logger.error(f"get_all_user_ids(): {e}")
        return []


def user_exists(user_id: str) -> bool:
    """
    Vérifie si un utilisateur existe en base.

    Fonctionne correctement pour un userId inexistant (retourne False sans exception).

    Paramètres
    ----------
    user_id : str
        Identifiant à vérifier.

    Retour
    ------
    bool
        True si l'utilisateur existe, False sinon.

    Exemple
    -------
    >>> user_exists("user_abc123")   # True
    >>> user_exists("user_inconnu")  # False
    """
    query = """
    MATCH (u:User {userId: $user_id})
    RETURN count(u) > 0 AS exists
    """
    try:
        rows = _db._execute_read(query, user_id=user_id)
        return bool(rows[0]["exists"]) if rows else False
    except Exception as e:
        logger.error(f"user_exists({user_id}): {e}")
        return False
