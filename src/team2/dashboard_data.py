"""Préparation des données du dashboard Streamlit de l'équipe Graph Mining."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.team2.extraction import GraphExtractor
from src.team2.global_metrics import component_size_rows, compute_global_metrics

def read_data_quality(extractor: GraphExtractor, edge_count: int) -> dict[str, int]:
    """Exécute les contrôles Neo4j associés à l'extraction du graphe."""
    with extractor.db._session() as session:
        raw_relationships = session.run(
            "MATCH (:User)-[r:FOLLOWS]->(:User) RETURN count(r) AS count"
        ).single()["count"]
        self_loops = session.run(
            "MATCH (u:User)-[r:FOLLOWS]->(u) RETURN count(r) AS count"
        ).single()["count"]
        missing_ids = session.run(
            "MATCH (u:User) WHERE u.userId IS NULL RETURN count(u) AS count"
        ).single()["count"]
        duplicate_id_groups = session.run(
            """
            MATCH (u:User)
            WITH u.userId AS id, count(*) AS occurrences
            WHERE id IS NOT NULL AND occurrences > 1
            RETURN count(*) AS count
            """
        ).single()["count"]

    return {
        "raw_follow_relationship_count": raw_relationships,
        "duplicate_follow_relationship_count": max(
            0, raw_relationships - edge_count
        ),
        "self_loop_count": self_loops,
        "missing_user_id_count": missing_ids,
        "duplicate_user_id_group_count": duplicate_id_groups,
    }


def load_dashboard_snapshot() -> dict[str, Any]:
    """Charge Neo4j et retourne un instantané sérialisable pour Streamlit."""
    extractor = GraphExtractor()
    try:
        graph = extractor.load_graph()
        metrics = compute_global_metrics(graph)
        data_quality = read_data_quality(extractor, graph.number_of_edges())
        degrees = [
            {
                "user_id": node,
                "in_degree": graph.in_degree(node),
                "out_degree": graph.out_degree(node),
                "total_degree": graph.degree(node),
            }
            for node in graph.nodes
        ]
        components = component_size_rows(graph)
    finally:
        extractor.close()

    return {
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "metrics": metrics.to_dict(),
        "degrees": degrees,
        "components": components,
        "data_quality": data_quality,
        "source": "Neo4j · nœuds :User · relations :FOLLOWS",
    }
