"""
tests/test_graph_queries.py
============================
Tests minimaux pour src/recommendation/graph_queries.py.

Objectif : vérifier que chaque fonction s'exécute sans erreur sur les données
générées par scripts/data_generator.py, et que les types de retour sont corrects.
Pas d'assertions sur des valeurs spécifiques (les userId changent à chaque
regénération) — on vérifie uniquement les contrats de type et l'absence d'exception.

Lancement :
    source .venv/bin/activate
    python -m pytest tests/test_graph_queries.py -v
"""

import sys
import os

# S'assure que la racine du projet est dans le path (pour "from src.*")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.recommendation.graph_queries import (
    get_following_ids,
    get_followers_ids,
    get_user_interests,
    get_second_degree_candidates,
    get_all_user_ids,
    user_exists,
)


# =============================================================================
# FIXTURE : récupère un userId réel en base pour les tests
# =============================================================================

@pytest.fixture(scope="module")
def real_user_id():
    """Récupère le premier userId disponible en base pour les tests."""
    all_ids = get_all_user_ids()
    if not all_ids:
        pytest.skip("Base vide — lance scripts/data_generator.py d'abord")
    return all_ids[0]


FAKE_ID = "user_inexistant_000000"


# =============================================================================
# get_all_user_ids
# =============================================================================

class TestGetAllUserIds:
    def test_returns_list(self):
        result = get_all_user_ids()
        assert isinstance(result, list), "Doit retourner une liste"

    def test_contains_strings(self):
        result = get_all_user_ids()
        if result:
            assert all(isinstance(uid, str) for uid in result), \
                "Tous les éléments doivent être des str"

    def test_non_empty_with_data(self):
        result = get_all_user_ids()
        assert len(result) > 0, "La base doit contenir des utilisateurs"


# =============================================================================
# user_exists
# =============================================================================

class TestUserExists:
    def test_existing_user_returns_true(self, real_user_id):
        assert user_exists(real_user_id) is True

    def test_fake_user_returns_false(self):
        assert user_exists(FAKE_ID) is False

    def test_returns_bool(self, real_user_id):
        result = user_exists(real_user_id)
        assert isinstance(result, bool), "Doit retourner un bool"

    def test_empty_string_returns_false(self):
        assert user_exists("") is False


# =============================================================================
# get_following_ids
# =============================================================================

class TestGetFollowingIds:
    def test_returns_list(self, real_user_id):
        result = get_following_ids(real_user_id)
        assert isinstance(result, list), "Doit retourner une liste"

    def test_contains_strings(self, real_user_id):
        result = get_following_ids(real_user_id)
        if result:
            assert all(isinstance(uid, str) for uid in result), \
                "Tous les éléments doivent être des str"

    def test_fake_user_returns_empty_list(self):
        result = get_following_ids(FAKE_ID)
        assert result == [], "Utilisateur inexistant → liste vide"

    def test_no_self_follow(self, real_user_id):
        result = get_following_ids(real_user_id)
        assert real_user_id not in result, "Un user ne peut pas se suivre lui-même"


# =============================================================================
# get_followers_ids
# =============================================================================

class TestGetFollowersIds:
    def test_returns_list(self, real_user_id):
        result = get_followers_ids(real_user_id)
        assert isinstance(result, list), "Doit retourner une liste"

    def test_contains_strings(self, real_user_id):
        result = get_followers_ids(real_user_id)
        if result:
            assert all(isinstance(uid, str) for uid in result), \
                "Tous les éléments doivent être des str"

    def test_fake_user_returns_empty_list(self):
        result = get_followers_ids(FAKE_ID)
        assert result == [], "Utilisateur inexistant → liste vide"


# =============================================================================
# get_user_interests
# =============================================================================

class TestGetUserInterests:
    def test_returns_list(self, real_user_id):
        result = get_user_interests(real_user_id)
        assert isinstance(result, list), "Doit retourner une liste"

    def test_contains_strings(self, real_user_id):
        result = get_user_interests(real_user_id)
        if result:
            assert all(isinstance(i, str) for i in result), \
                "Les intérêts doivent être des str"

    def test_interests_not_empty_after_generation(self, real_user_id):
        result = get_user_interests(real_user_id)
        assert len(result) >= 2, \
            "Après data_generator.py, chaque user doit avoir au moins 2 intérêts"

    def test_fake_user_returns_empty_list(self):
        result = get_user_interests(FAKE_ID)
        assert result == [], "Utilisateur inexistant → liste vide"


# =============================================================================
# get_second_degree_candidates
# =============================================================================

class TestGetSecondDegreeCandidates:
    def test_returns_list(self, real_user_id):
        result = get_second_degree_candidates(real_user_id)
        assert isinstance(result, list), "Doit retourner une liste"

    def test_contains_strings(self, real_user_id):
        result = get_second_degree_candidates(real_user_id)
        if result:
            assert all(isinstance(uid, str) for uid in result), \
                "Tous les éléments doivent être des str"

    def test_respects_limit(self, real_user_id):
        limit = 5
        result = get_second_degree_candidates(real_user_id, limit=limit)
        assert len(result) <= limit, f"Ne doit pas dépasser {limit} résultats"

    def test_default_limit_respected(self, real_user_id):
        result = get_second_degree_candidates(real_user_id)
        assert len(result) <= 50, "La limite par défaut est 50"

    def test_no_self_in_candidates(self, real_user_id):
        result = get_second_degree_candidates(real_user_id)
        assert real_user_id not in result, \
            "L'utilisateur ne doit pas apparaître dans ses propres candidats"

    def test_no_already_followed_in_candidates(self, real_user_id):
        following = set(get_following_ids(real_user_id))
        candidates = set(get_second_degree_candidates(real_user_id))
        overlap = following & candidates
        assert not overlap, \
            f"Les candidats ne doivent pas inclure des followings directs : {overlap}"

    def test_fake_user_returns_empty_list(self):
        result = get_second_degree_candidates(FAKE_ID)
        assert result == [], "Utilisateur inexistant → liste vide"
