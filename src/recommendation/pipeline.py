from __future__ import annotations

import logging
from typing import Dict, List, Optional

from src.recommendation.graph_queries import (
    get_second_degree_candidates,
    get_all_user_ids,
    get_following_ids,
    user_exists,
)
from src.recommendation.proximity import (
    common_neighbors,
    jaccard_similarity,
    adamic_adar,
    interests_similarity,
)

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "common_neighbors": 0.25,
    "jaccard":          0.25,
    "adamic_adar":      0.25,
    "interest_similarity": 0.25,
}

CN_NORM = 10.0
AA_NORM =  3.0


def get_proximity_scores(
    user_id: str,
    limit: int = 10,
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict]:
    if not user_exists(user_id):
        logger.warning(f"Utilisateur {user_id} n'existe pas")
        return []

    w = weights or DEFAULT_WEIGHTS

    candidates = get_second_degree_candidates(user_id, limit=100)

    if len(candidates) < limit:
        following = set(get_following_ids(user_id))
        all_users = set(get_all_user_ids())
        extra = list(all_users - following - set(candidates) - {user_id})
        candidates = list(set(candidates) | set(extra))

    if not candidates:
        return []

    results = []
    for candidate in candidates:
        cn  = common_neighbors(user_id, candidate)
        jac = jaccard_similarity(user_id, candidate)
        aa  = adamic_adar(user_id, candidate)
        sim = interests_similarity(user_id, candidate)

        cn_norm = min(cn / CN_NORM, 1.0)
        aa_norm = min(aa / AA_NORM, 1.0)

        final = (
            w["common_neighbors"]    * cn_norm +
            w["jaccard"]             * jac     +
            w["adamic_adar"]         * aa_norm +
            w["interest_similarity"] * sim
        )

        results.append({
            "user_id":             candidate,
            "common_neighbors":    cn,
            "jaccard":             jac,
            "adamic_adar":         aa,
            "interest_similarity": sim,
            "final_score":         round(final, 4),
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:limit]


def generate_recommendations(user_id: str, top_n: int = 10) -> List[Dict]:
    return get_proximity_scores(user_id, limit=top_n)


def get_recommendations_with_details(user_id: str, top_n: int = 10) -> List[Dict]:
    from src.recommendation.graph_queries import get_user_interests
    recs = get_proximity_scores(user_id, limit=top_n)
    user_interests = set(get_user_interests(user_id))
    for rec in recs:
        candidate_interests = set(get_user_interests(rec["user_id"]))
        common = list(user_interests & candidate_interests)
        rec["common_interests"]       = common[:5]
        rec["common_interests_count"] = len(common)
    return recs