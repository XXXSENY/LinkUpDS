from pathlib import Path

import networkx as nx
import pandas as pd
import pytest

from src.team2.community_detection import (
    CommunityAnalysis,
    build_community_rows,
    detect_communities,
    export_community_results,
)


def _two_group_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("a", "b"),
            ("b", "c"),
            ("c", "a"),
            ("d", "e"),
            ("e", "f"),
            ("f", "d"),
            ("c", "d"),
        ]
    )
    return graph


def test_detects_louvain_communities_and_preserves_every_node():
    graph = _two_group_graph()

    analysis = detect_communities(graph, seed=42)

    assert analysis.algorithm == "Louvain"
    assert analysis.community_count == 2
    assert set(analysis.partition) == set(graph.nodes)
    assert analysis.partition["a"] == analysis.partition["b"]
    assert analysis.partition["d"] == analysis.partition["e"]
    assert analysis.partition["a"] != analysis.partition["d"]
    assert analysis.modularity == pytest.approx(0.3571428571)


def test_empty_graph_and_isolated_nodes_are_supported():
    empty = detect_communities(nx.DiGraph())
    isolates = nx.DiGraph()
    isolates.add_nodes_from(["u1", "u2"])

    isolated_analysis = detect_communities(isolates)

    assert empty == CommunityAnalysis({}, 0.0, "Louvain")
    assert isolated_analysis.community_count == 2
    assert isolated_analysis.modularity == 0.0
    assert set(isolated_analysis.partition) == {"u1", "u2"}


def test_community_rows_characterize_internal_and_external_links():
    graph = _two_group_graph()
    analysis = CommunityAnalysis(
        partition={"a": 1, "b": 1, "c": 1, "d": 2, "e": 2, "f": 2},
        modularity=0.3,
        algorithm="Louvain",
    )

    rows = build_community_rows(graph, analysis)

    assert rows == [
        {
            "community_id": 1,
            "size": 3,
            "network_percentage": 50.0,
            "internal_edges": 3,
            "external_edges": 1,
            "internal_density": 1.0,
        },
        {
            "community_id": 2,
            "size": 3,
            "network_percentage": 50.0,
            "internal_edges": 3,
            "external_edges": 1,
            "internal_density": 1.0,
        },
    ]


def test_exports_tables_report_and_colored_graph(tmp_path: Path):
    graph = _two_group_graph()
    analysis = detect_communities(graph, seed=42)

    paths = export_community_results(graph, analysis, tmp_path)

    assert set(paths) == {"members", "summary", "report", "graph"}
    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())

    members = pd.read_csv(paths["members"])
    summary = pd.read_csv(paths["summary"])
    report = paths["report"].read_text(encoding="utf-8")
    assert set(members.columns) == {"user_id", "community_id", "community_size"}
    assert len(members) == graph.number_of_nodes()
    assert len(summary) == analysis.community_count
    assert f"Modularité : **{analysis.modularity:.4f}**" in report
    assert "communauté la plus importante" in report
