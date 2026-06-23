"""Calcul des indicateurs topologiques globaux du réseau LinkUpDS."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import networkx as nx


@dataclass(frozen=True)
class GlobalGraphMetrics:
    """Indicateurs d'un graphe social orienté simple."""
    node_count: int
    edge_count: int
    density: float
    average_degree: float
    average_in_degree: float
    average_out_degree: float
    average_distance: float | None
    average_distance_scope: str
    reachable_pairs_average_distance: float | None
    reachable_ordered_pairs: int
    reachable_ordered_pair_fraction: float
    weak_component_count: int
    strong_component_count: int
    largest_weak_component_size: int
    largest_strong_component_size: int
    largest_weak_component_fraction: float
    largest_strong_component_fraction: float
    isolated_node_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _mean(values: list[int]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_global_metrics(graph: nx.DiGraph) -> GlobalGraphMetrics:
    """Calcule les métriques globales avec une convention explicite.
    La distance moyenne principale est calculée sur la plus grande composante
    fortement connexe. Cette convention évite les distances infinies dans un
    graphe orienté non fortement connexe.
    """
    if not graph.is_directed():
        raise TypeError("Un nx.DiGraph est requis pour le réseau FOLLOWS.")
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()

    in_degrees = [degree for _, degree in graph.in_degree()]
    out_degrees = [degree for _, degree in graph.out_degree()]
    total_degrees = [degree for _, degree in graph.degree()]
    
    if node_count:
        weak_components = sorted(
            nx.weakly_connected_components(graph), key=len, reverse=True
        )
        strong_components = sorted(
            nx.strongly_connected_components(graph), key=len, reverse=True
        )
    else:
        weak_components = []
        strong_components = []

    largest_weak_size = len(weak_components[0]) if weak_components else 0
    largest_strong_size = len(strong_components[0]) if strong_components else 0
    
    average_distance: float | None = None
    distance_scope = "indisponible (graphe vide)"
    if strong_components:
        largest_strong_graph = graph.subgraph(strong_components[0])
        if largest_strong_size == 1:
            average_distance = 0.0
        else:
            average_distance = nx.average_shortest_path_length(
                largest_strong_graph
            )
        distance_scope = (
            "plus grande composante fortement connexe "
            f"({largest_strong_size}/{node_count} nœuds)"
        )

    reachable_distance_sum = 0
    reachable_pairs = 0
    for source, lengths in nx.all_pairs_shortest_path_length(graph):
        for target, distance in lengths.items():
            if source == target:
                continue
            reachable_distance_sum += distance
            reachable_pairs += 1

    possible_ordered_pairs = node_count * (node_count - 1)
    reachable_average = (
        reachable_distance_sum / reachable_pairs if reachable_pairs else None
    )

    return GlobalGraphMetrics(
        node_count=node_count,
        edge_count=edge_count,
        density=nx.density(graph) if node_count > 1 else 0.0,
        average_degree=_mean(total_degrees),
        average_in_degree=_mean(in_degrees),
        average_out_degree=_mean(out_degrees),
        average_distance=average_distance,
        average_distance_scope=distance_scope,
        reachable_pairs_average_distance=reachable_average,
        reachable_ordered_pairs=reachable_pairs,
        reachable_ordered_pair_fraction=(
            reachable_pairs / possible_ordered_pairs
            if possible_ordered_pairs
            else 0.0
        ),
        weak_component_count=len(weak_components),
        strong_component_count=len(strong_components),
        largest_weak_component_size=largest_weak_size,
        largest_strong_component_size=largest_strong_size,
        largest_weak_component_fraction=(
            largest_weak_size / node_count if node_count else 0.0
        ),
        largest_strong_component_fraction=(
            largest_strong_size / node_count if node_count else 0.0
        ),
        isolated_node_count=len(list(nx.isolates(graph))),
    )


def component_size_rows(graph: nx.DiGraph) -> list[dict[str, int | str]]:
    """Retourne les tailles des composantes faibles et fortes."""
    rows: list[dict[str, int | str]] = []
    component_sets = {
        "Faible": nx.weakly_connected_components(graph),
        "Forte": nx.strongly_connected_components(graph),
    }
    for component_type, components in component_sets.items():
        sizes = sorted((len(component) for component in components), reverse=True)
        rows.extend(
            {
                "component_type": component_type,
                "component_rank": rank,
                "size": size,
            }
            for rank, size in enumerate(sizes, start=1)
        )
    return rows
