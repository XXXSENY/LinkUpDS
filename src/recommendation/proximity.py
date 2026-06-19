"""
src/recommendation/proximity.py
=================================
Indicateurs de proximité entre utilisateurs pour LinkUpDS.

Calcule des scores de similarité basés sur le graphe (FOLLOWS)
et sur le contenu (interests), utilisés par le moteur de
recommandation d'amis et le Smart Feed.

Réutilise exclusivement les briques de src/recommendation/graph_queries.py
(get_following_ids, get_user_interests, user_exists) — aucune connexion
ni requête Cypher dupliquée ici, conformément au pattern de l'équipe.

Auteur : Oumou — Équipe 3 (NLP & Recommandation)
"""

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional

from src.recommendation.graph_queries import (
    get_following_ids,
    get_user_interests,
    user_exists,
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 1. COMMON NEIGHBORS
# ----------------------------------------------------------------------

def common_neighbors(user_a: str, user_b: str) -> int:
    """
    Nombre de comptes suivis en commun entre deux utilisateurs.

    Si A suit {x, y, z} et B suit {y, z, w},
    alors common_neighbors(A, B) = 2  (y et z)

    Paramètres
    ----------
    user_a : str
        userId du premier utilisateur.
    user_b : str
        userId du second utilisateur.

    Retour
    ------
    int
        Nombre de voisins (comptes suivis) en commun.
        Retourne 0 si l'un des deux utilisateurs n'existe pas.
    """
    if not _validate_pair(user_a, user_b):
        return 0

    following_a = set(get_following_ids(user_a))
    following_b = set(get_following_ids(user_b))

    return len(following_a & following_b)


# ----------------------------------------------------------------------
# 2. COEFFICIENT DE JACCARD (sur les FOLLOWS)
# ----------------------------------------------------------------------

def jaccard_similarity(user_a: str, user_b: str) -> float:
    """
    Similarité de Jaccard entre les ensembles de comptes suivis.

    Formule : |A ∩ B| / |A ∪ B|

    Résultat entre 0.0 (aucun follow en commun) et 1.0
    (suivent exactement les mêmes comptes).

    Paramètres
    ----------
    user_a : str
        userId du premier utilisateur.
    user_b : str
        userId du second utilisateur.

    Retour
    ------
    float
        Score de Jaccard entre 0.0 et 1.0.
        Retourne 0.0 si les deux ensembles sont vides ou si
        l'un des deux utilisateurs n'existe pas.
    """
    if not _validate_pair(user_a, user_b):
        return 0.0

    following_a = set(get_following_ids(user_a))
    following_b = set(get_following_ids(user_b))

    union = following_a | following_b
    if not union:
        return 0.0

    intersection = following_a & following_b
    return round(len(intersection) / len(union), 4)


# ----------------------------------------------------------------------
# 3. ADAMIC-ADAR
# ----------------------------------------------------------------------

def adamic_adar(user_a: str, user_b: str) -> float:
    """
    Score Adamic-Adar entre deux utilisateurs.

    Idée : un voisin commun qui suit très peu de comptes au total
    est un signal plus fort de proximité qu'un voisin commun
    "populaire" qui suit tout le monde.

    Formule : somme sur chaque voisin commun w de 1 / log(deg(w))
    où deg(w) = nombre de comptes que w suit.

    Paramètres
    ----------
    user_a : str
        userId du premier utilisateur.
    user_b : str
        userId du second utilisateur.

    Retour
    ------
    float
        Score Adamic-Adar (>= 0.0). Plus le score est élevé,
        plus les utilisateurs sont proches. Retourne 0.0 si
        aucun voisin commun ou si l'un des deux n'existe pas.
    """
    if not _validate_pair(user_a, user_b):
        return 0.0

    following_a = set(get_following_ids(user_a))
    following_b = set(get_following_ids(user_b))

    common = following_a & following_b
    if not common:
        return 0.0

    score = 0.0
    for neighbor in common:
        degree = len(get_following_ids(neighbor))

        # Si le voisin commun suit 0 ou 1 compte, log(degree) est
        # négatif ou nul -> on l'ignore pour éviter une division
        # par zéro ou un score négatif aberrant.
        if degree <= 1:
            continue

        score += 1 / math.log(degree)

    return round(score, 4)


# ----------------------------------------------------------------------
# 4. SIMILARITÉ D'INTÉRÊTS (Jaccard sur les "interests")
# ----------------------------------------------------------------------

def interests_similarity(user_a: str, user_b: str) -> float:
    """
    Similarité de Jaccard entre les listes d'intérêts (`interests`)
    de deux utilisateurs.

    Formule : |interests_A ∩ interests_B| / |interests_A ∪ interests_B|

    Paramètres
    ----------
    user_a : str
        userId du premier utilisateur.
    user_b : str
        userId du second utilisateur.

    Retour
    ------
    float
        Score de Jaccard entre 0.0 et 1.0.
        Retourne 0.0 si les deux listes sont vides ou si l'un
        des deux utilisateurs n'existe pas.
    """
    if not _validate_pair(user_a, user_b):
        return 0.0

    interests_a = set(_normalize_interests(get_user_interests(user_a)))
    interests_b = set(_normalize_interests(get_user_interests(user_b)))

    union = interests_a | interests_b
    if not union:
        return 0.0

    intersection = interests_a & interests_b
    return round(len(intersection) / len(union), 4)


def _normalize_interests(interests: Optional[List[str]]) -> List[str]:
    """
    Normalise une liste d'intérêts pour éviter les faux négatifs
    dus à la casse ou aux espaces (ex: "Sport " vs "sport").
    """
    if not interests:
        return []
    return [i.strip().lower() for i in interests if i and i.strip()]


# ----------------------------------------------------------------------
# 5. SCORE COMBINÉ
# ----------------------------------------------------------------------

def proximity_score(
    user_a: str,
    user_b: str,
    weights: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Calcule les 4 indicateurs en un seul appel et retourne
    un score combiné pondéré, prêt à être consommé par le
    moteur de recommandation ou le Smart Feed.

    Paramètres
    ----------
    user_a : str
        userId du premier utilisateur.
    user_b : str
        userId du second utilisateur.
    weights : dict, optionnel
        Pondération, ex: {"jaccard": 0.4, "adamic_adar": 0.3, "interests": 0.3}.
        common_neighbors n'est pas inclus car non normalisé entre 0 et 1.

    Retour
    ------
    dict
        Chaque score individuel + le score combiné (combined_score).
    """
    default_weights = {
        "jaccard": 0.4,
        "adamic_adar": 0.3,
        "interests": 0.3,
    }
    weights = weights or default_weights

    cn = common_neighbors(user_a, user_b)
    jac = jaccard_similarity(user_a, user_b)
    aa = adamic_adar(user_a, user_b)
    interests_sim = interests_similarity(user_a, user_b)

    # Normalisation simple d'Adamic-Adar pour le score combiné
    # (cappé à 1.0, les scores AA dépassant rarement 3-4 en pratique)
    aa_normalized = min(aa / 3.0, 1.0)

    combined = (
        weights.get("jaccard", 0) * jac
        + weights.get("adamic_adar", 0) * aa_normalized
        + weights.get("interests", 0) * interests_sim
    )

    return {
        "user_a": user_a,
        "user_b": user_b,
        "common_neighbors": cn,
        "jaccard": jac,
        "adamic_adar": aa,
        "interests_similarity": interests_sim,
        "combined_score": round(combined, 4),
    }


# ----------------------------------------------------------------------
# VALIDATION INTERNE
# ----------------------------------------------------------------------

def _validate_pair(user_a: str, user_b: str) -> bool:
    """
    Vérifie que les deux utilisateurs existent avant tout calcul.
    Log un warning si l'un des deux est introuvable.
    """
    if not user_exists(user_a):
        logger.warning(f"_validate_pair: user_a inconnu ({user_a})")
        return False
    if not user_exists(user_b):
        logger.warning(f"_validate_pair: user_b inconnu ({user_b})")
        return False
    return True