"""Détection et caractérisation des communautés du réseau FOLLOWS.

Louvain s'applique à une vue non orientée du réseau : deux utilisateurs sont
considérés liés dès que l'un suit l'autre. Le graphe orienté original reste
utilisé pour compter les relations internes et externes dans les livrables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Hashable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from src.team2.extraction import GraphExtractor


@dataclass(frozen=True)
class CommunityAnalysis:
    """Résultat sérialisable d'une détection de communautés."""

    partition: dict[Hashable, int]
    modularity: float
    algorithm: str = "Louvain"

    @property
    def community_count(self) -> int:
        return len(set(self.partition.values()))


def _undirected_simple_graph(graph: nx.Graph) -> nx.Graph:
    undirected = nx.Graph()
    undirected.add_nodes_from(graph.nodes(data=True))
    undirected.add_edges_from(graph.edges())
    undirected.remove_edges_from(nx.selfloop_edges(undirected))
    return undirected


def detect_communities(
    graph: nx.Graph,
    *,
    seed: int = 42,
    resolution: float = 1.0,
) -> CommunityAnalysis:
    """Détecte les communautés Louvain et calcule leur modularité.

    Les identifiants commencent à 1. La communauté la plus grande reçoit
    l'identifiant 1 afin de faciliter l'interprétation dans le dashboard.
    """
    undirected = _undirected_simple_graph(graph)
    if undirected.number_of_nodes() == 0:
        return CommunityAnalysis({}, 0.0)

    if undirected.number_of_edges() == 0:
        communities = [{node} for node in undirected.nodes]
        modularity = 0.0
    else:
        communities = list(
            nx.community.louvain_communities(
                undirected,
                seed=seed,
                resolution=resolution,
            )
        )
        modularity = nx.community.modularity(
            undirected,
            communities,
            resolution=resolution,
        )

    communities.sort(
        key=lambda nodes: (-len(nodes), min(str(node) for node in nodes))
    )
    partition = {
        node: community_id
        for community_id, nodes in enumerate(communities, start=1)
        for node in nodes
    }
    return CommunityAnalysis(partition, float(modularity))


def build_community_rows(
    graph: nx.Graph,
    analysis: CommunityAnalysis,
) -> list[dict[str, int | float]]:
    """Caractérise chaque communauté pour le tableau récapitulatif."""
    undirected = _undirected_simple_graph(graph)
    node_count = graph.number_of_nodes()
    rows: list[dict[str, int | float]] = []

    for community_id in sorted(set(analysis.partition.values())):
        nodes = {
            node
            for node, assigned_id in analysis.partition.items()
            if assigned_id == community_id
        }
        subgraph = undirected.subgraph(nodes)
        external_edges = sum(
            1
            for source, target in undirected.edges
            if (source in nodes) != (target in nodes)
        )
        rows.append(
            {
                "community_id": community_id,
                "size": len(nodes),
                "network_percentage": round(
                    100 * len(nodes) / node_count if node_count else 0.0, 2
                ),
                "internal_edges": subgraph.number_of_edges(),
                "external_edges": external_edges,
                "internal_density": round(
                    nx.density(subgraph) if len(nodes) > 1 else 0.0, 4
                ),
            }
        )
    return rows


def _member_rows(
    analysis: CommunityAnalysis,
    summary_rows: list[dict[str, int | float]],
) -> list[dict[str, Hashable | int]]:
    sizes = {row["community_id"]: row["size"] for row in summary_rows}
    return [
        {
            "user_id": node,
            "community_id": community_id,
            "community_size": sizes[community_id],
        }
        for node, community_id in sorted(
            analysis.partition.items(), key=lambda item: (item[1], str(item[0]))
        )
    ]


def _write_report(
    analysis: CommunityAnalysis,
    rows: list[dict[str, int | float]],
    output_path: Path,
) -> None:
    if not rows:
        interpretation = "Le graphe est vide : aucune communauté n'a été détectée."
    else:
        largest = rows[0]
        interpretation = (
            f"L'algorithme Louvain a détecté **{analysis.community_count} "
            f"communauté(s)**. La communauté la plus importante est la "
            f"communauté **{largest['community_id']}**, avec "
            f"**{largest['size']} utilisateurs** "
            f"({largest['network_percentage']:.2f} % du réseau)."
        )

    lines = [
        "# Rapport de détection des communautés",
        "",
        "## Résultats globaux",
        "",
        f"- Algorithme : **{analysis.algorithm}**",
        f"- Nombre de communautés : **{analysis.community_count}**",
        f"- Modularité : **{analysis.modularity:.4f}**",
        "",
        "## Interprétation",
        "",
        interpretation,
        "",
        (
            "Une modularité élevée indique que les relations sont davantage "
            "concentrées à l'intérieur des communautés qu'entre elles."
        ),
        "",
        "## Caractérisation des communautés",
        "",
        "| Communauté | Utilisateurs | Part du réseau | Liens internes | "
        "Liens externes | Densité interne |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(
        "| {community_id} | {size} | {network_percentage:.2f} % | "
        "{internal_edges} | {external_edges} | {internal_density:.4f} |".format(
            **row
        )
        for row in rows
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot_colored_graph(
    graph: nx.Graph,
    analysis: CommunityAnalysis,
    output_path: Path,
    *,
    seed: int = 42,
) -> None:
    undirected = _undirected_simple_graph(graph)
    figure, axis = plt.subplots(figsize=(12, 8))
    axis.set_title(
        f"Communautés Louvain — {analysis.community_count} groupe(s), "
        f"modularité {analysis.modularity:.3f}"
    )
    axis.axis("off")

    if undirected.number_of_nodes():
        positions = nx.spring_layout(undirected, seed=seed)
        colors = [analysis.partition[node] for node in undirected.nodes]
        nx.draw_networkx_edges(
            undirected,
            positions,
            ax=axis,
            edge_color="#94a3b8",
            alpha=0.35,
            width=0.8,
        )
        nx.draw_networkx_nodes(
            undirected,
            positions,
            ax=axis,
            node_color=colors,
            cmap=plt.get_cmap("tab20"),
            node_size=90,
            linewidths=0.4,
            edgecolors="white",
        )

    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def export_community_results(
    graph: nx.Graph,
    analysis: CommunityAnalysis,
    output_directory: str | Path = "outputs",
) -> dict[str, Path]:
    """Génère les deux tableaux, le rapport et le graphe coloré."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "members": output_directory / "community_members.csv",
        "summary": output_directory / "community_summary.csv",
        "report": output_directory / "community_report.md",
        "graph": output_directory / "community_graph.png",
    }

    summary_rows = build_community_rows(graph, analysis)
    pd.DataFrame(
        _member_rows(analysis, summary_rows),
        columns=["user_id", "community_id", "community_size"],
    ).to_csv(paths["members"], index=False)
    pd.DataFrame(
        summary_rows,
        columns=[
            "community_id",
            "size",
            "network_percentage",
            "internal_edges",
            "external_edges",
            "internal_density",
        ],
    ).to_csv(paths["summary"], index=False)
    _write_report(analysis, summary_rows, paths["report"])
    _plot_colored_graph(graph, analysis, paths["graph"])
    return paths


def main() -> None:
    """Charge Neo4j puis produit tous les livrables du membre 5."""
    extractor = GraphExtractor()
    try:
        graph = extractor.load_graph()
    finally:
        extractor.close()

    analysis = detect_communities(graph)
    paths = export_community_results(graph, analysis)
    print(
        f"Louvain : {analysis.community_count} communauté(s), "
        f"modularité = {analysis.modularity:.4f}"
    )
    for label, path in paths.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
