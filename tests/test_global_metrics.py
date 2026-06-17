import networkx as nx
import pytest

from src.team2.global_metrics import compute_global_metrics


def test_metrics_preserve_isolates_and_directed_definitions():
    graph = nx.DiGraph()
    graph.add_nodes_from(["a", "b", "c"])
    graph.add_edges_from([("a", "b"), ("b", "a")])

    metrics = compute_global_metrics(graph)

    assert metrics.node_count == 3
    assert metrics.edge_count == 2
    assert metrics.density == pytest.approx(2 / 6)
    assert metrics.average_degree == pytest.approx(4 / 3)
    assert metrics.average_in_degree == pytest.approx(2 / 3)
    assert metrics.average_out_degree == pytest.approx(2 / 3)
    assert metrics.average_distance == pytest.approx(1.0)
    assert metrics.weak_component_count == 2
    assert metrics.strong_component_count == 2
    assert metrics.largest_strong_component_size == 2
    assert metrics.isolated_node_count == 1
    assert metrics.reachable_ordered_pair_fraction == pytest.approx(2 / 6)


def test_metrics_empty_graph():
    metrics = compute_global_metrics(nx.DiGraph())

    assert metrics.node_count == 0
    assert metrics.edge_count == 0
    assert metrics.average_distance is None
    assert metrics.weak_component_count == 0
    assert metrics.strong_component_count == 0


def test_rejects_undirected_graph():
    with pytest.raises(TypeError):
        compute_global_metrics(nx.Graph())
