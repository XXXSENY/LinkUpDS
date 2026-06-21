"""Dashboard Streamlit du team2 - Graph Mining LinkUpDS.

Cette application est volontairement separee de app.py pour pouvoir presenter
le livrable "Visualisation et Dashboard" sans authentification ni backend API.
Elle lit directement Neo4j, construit le graphe NetworkX, puis affiche les
statistiques, influenceurs, communautes et une visualisation interactive.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from neo4j import GraphDatabase

from src.config import NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
from src.team2.community_detection import build_community_rows, detect_communities
from src.team2.global_metrics import compute_global_metrics


st.set_page_config(
    page_title="LinkUpDS - Dashboard Graph Mining",
    page_icon="LU",
    layout="wide",
)


def require_neo4j_config() -> None:
    missing = [
        name
        for name, value in {
            "NEO4J_URI": NEO4J_URI,
            "NEO4J_USER": NEO4J_USER,
            "NEO4J_PASSWORD": NEO4J_PASSWORD,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Variables Neo4j manquantes dans .env : " + ", ".join(missing)
        )


@st.cache_data(ttl=120, show_spinner=False)
def load_graph_from_neo4j() -> nx.DiGraph:
    """Charge les utilisateurs et les relations FOLLOWS depuis Neo4j."""
    require_neo4j_config()
    graph = nx.DiGraph()
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        session_kwargs = {"database": NEO4J_DATABASE} if NEO4J_DATABASE else {}
        with driver.session(**session_kwargs) as session:
            users = session.run(
                """
                MATCH (u:User)
                RETURN coalesce(u.userId, elementId(u)) AS user_id,
                       coalesce(u.name, u.username, u.email, u.userId) AS label
                """
            )
            for row in users:
                graph.add_node(row["user_id"], label=row["label"] or row["user_id"])

            follows = session.run(
                """
                MATCH (a:User)-[:FOLLOWS]->(b:User)
                RETURN DISTINCT coalesce(a.userId, elementId(a)) AS source,
                                coalesce(b.userId, elementId(b)) AS target
                """
            )
            graph.add_edges_from((row["source"], row["target"]) for row in follows)
    finally:
        driver.close()
    return graph


@st.cache_data(ttl=120, show_spinner=False)
def build_dashboard_snapshot() -> dict[str, Any]:
    graph = load_graph_from_neo4j()
    metrics = compute_global_metrics(graph).to_dict()

    pagerank = nx.pagerank(graph) if graph.number_of_nodes() else {}
    betweenness = (
        nx.betweenness_centrality(graph, normalized=True)
        if graph.number_of_nodes()
        else {}
    )

    communities = detect_communities(graph)
    community_rows = build_community_rows(graph, communities)

    node_rows = []
    for node in graph.nodes:
        node_rows.append(
            {
                "Utilisateur": node,
                "Nom": graph.nodes[node].get("label", node),
                "PageRank": pagerank.get(node, 0.0),
                "Betweenness": betweenness.get(node, 0.0),
                "Communaute": communities.partition.get(node),
                "Degre entrant": graph.in_degree(node),
                "Degre sortant": graph.out_degree(node),
                "Degre total": graph.degree(node),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "graph": graph,
        "metrics": metrics,
        "nodes": pd.DataFrame(node_rows),
        "communities": pd.DataFrame(community_rows),
        "modularity": communities.modularity,
        "community_count": communities.community_count,
    }


def style_plotly(figure: go.Figure, height: int = 430) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=60, b=35),
        font=dict(family="Arial, sans-serif", size=13, color="#172033"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
    )
    return figure


def render_header(snapshot: dict[str, Any]) -> None:
    st.title("LinkUpDS - Dashboard Graph Mining")
    st.caption(
        " visualisation du reseau, influenceurs, communautes et statistiques."
    )
    left, right = st.columns([0.75, 0.25])
    with left:
        st.caption(
            "Derniere lecture UTC : "
            + snapshot["generated_at"].replace("T", " ")
        )
    with right:
        if st.button("Actualiser les donnees", use_container_width=True):
            load_graph_from_neo4j.clear()
            build_dashboard_snapshot.clear()
            st.rerun()


def render_stats_tab(snapshot: dict[str, Any]) -> None:
    metrics = snapshot["metrics"]
    distance = metrics["average_distance"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nombre d'utilisateurs", metrics["node_count"])
    c2.metric("Nombre de relations", metrics["edge_count"])
    c3.metric("Densite", f"{metrics['density']:.4f}")
    c4.metric("Distance moyenne", "N/A" if distance is None else f"{distance:.2f}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Degre moyen", f"{metrics['average_degree']:.2f}")
    c6.metric("Composantes faibles", metrics["weak_component_count"])
    c7.metric("Composantes fortes", metrics["strong_component_count"])
    c8.metric("Utilisateurs isoles", metrics["isolated_node_count"])

    nodes = snapshot["nodes"]
    if nodes.empty:
        st.warning("Le graphe est vide. Generez les donnees avant d'analyser.")
        return

    left, right = st.columns(2)
    with left:
        hist = px.histogram(
            nodes,
            x="Degre total",
            nbins=max(5, min(20, int(nodes["Degre total"].max()) + 1)),
            title="Distribution du degre total",
            labels={"Degre total": "Degre total", "count": "Utilisateurs"},
            color_discrete_sequence=["#2563eb"],
        )
        st.plotly_chart(style_plotly(hist), use_container_width=True)

    with right:
        scatter = px.scatter(
            nodes,
            x="Degre sortant",
            y="Degre entrant",
            size="Degre total",
            hover_name="Nom",
            hover_data=["Utilisateur"],
            title="Abonnements vs abonnes",
            color_discrete_sequence=["#d97706"],
        )
        st.plotly_chart(style_plotly(scatter), use_container_width=True)

    st.subheader("Tableau des indicateurs")
    st.dataframe(
        pd.DataFrame(
            [
                ["Nombre d'utilisateurs", metrics["node_count"]],
                ["Nombre de relations", metrics["edge_count"]],
                ["Densite", f"{metrics['density']:.4f}"],
                ["Distance moyenne", "N/A" if distance is None else f"{distance:.4f}"],
                ["Perimetre distance", metrics["average_distance_scope"]],
                ["Degre moyen", f"{metrics['average_degree']:.4f}"],
                ["Composantes faibles", metrics["weak_component_count"]],
                ["Composantes fortes", metrics["strong_component_count"]],
            ],
            columns=["Indicateur", "Valeur"],
        ),
        hide_index=True,
        use_container_width=True,
    )


def render_influencers_tab(snapshot: dict[str, Any]) -> None:
    nodes = snapshot["nodes"]
    if nodes.empty:
        st.warning("Aucun utilisateur a afficher.")
        return

    top_pr = nodes.sort_values("PageRank", ascending=False).head(10)
    top_bet = nodes.sort_values("Betweenness", ascending=False).head(10)

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 PageRank")
        st.dataframe(
            top_pr[["Utilisateur", "Nom", "PageRank", "Degre entrant"]],
            hide_index=True,
            use_container_width=True,
            column_config={"PageRank": st.column_config.NumberColumn(format="%.6f")},
        )
        fig = px.bar(
            top_pr,
            x="Nom",
            y="PageRank",
            title="Scores PageRank",
            color="PageRank",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(style_plotly(fig), use_container_width=True)

    with right:
        st.subheader("Top 10 Betweenness")
        st.dataframe(
            top_bet[["Utilisateur", "Nom", "Betweenness", "Degre total"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Betweenness": st.column_config.NumberColumn(format="%.6f")
            },
        )
        fig = px.bar(
            top_bet,
            x="Nom",
            y="Betweenness",
            title="Scores Betweenness",
            color="Betweenness",
            color_continuous_scale="Oranges",
        )
        st.plotly_chart(style_plotly(fig), use_container_width=True)

    best_pr = top_pr.iloc[0]
    best_bet = top_bet.iloc[0]
    st.info(
        f"{best_pr['Nom']} possede le PageRank le plus eleve "
        f"({best_pr['PageRank']:.6f}). {best_bet['Nom']} est le meilleur "
        f"intermediaire selon la betweenness ({best_bet['Betweenness']:.6f})."
    )


def render_communities_tab(snapshot: dict[str, Any]) -> None:
    communities = snapshot["communities"]
    nodes = snapshot["nodes"]

    c1, c2 = st.columns(2)
    c1.metric("Nombre de communautes", snapshot["community_count"])
    c2.metric("Modularite Louvain", f"{snapshot['modularity']:.4f}")

    if communities.empty:
        st.warning("Aucune communaute detectee.")
        return

    st.subheader("Liste et taille des communautes")
    st.dataframe(
        communities.rename(
            columns={
                "community_id": "Communaute",
                "size": "Taille",
                "network_percentage": "Part du reseau (%)",
                "internal_edges": "Liens internes",
                "external_edges": "Liens externes",
                "internal_density": "Densite interne",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    fig = px.bar(
        communities,
        x="community_id",
        y="size",
        text="size",
        title="Taille des communautes",
        labels={"community_id": "Communaute", "size": "Utilisateurs"},
        color="size",
        color_continuous_scale="Teal",
    )
    st.plotly_chart(style_plotly(fig), use_container_width=True)

    selected = st.selectbox(
        "Consulter les membres d'une communaute",
        sorted(nodes["Communaute"].dropna().unique()),
    )
    st.dataframe(
        nodes[nodes["Communaute"] == selected][
            ["Utilisateur", "Nom", "PageRank", "Betweenness", "Degre total"]
        ].sort_values("PageRank", ascending=False),
        hide_index=True,
        use_container_width=True,
    )


def network_figure(
    graph: nx.DiGraph,
    nodes: pd.DataFrame,
    *,
    max_nodes: int,
    color_by: str,
) -> go.Figure:
    if graph.number_of_nodes() > max_nodes:
        selected_nodes = (
            nodes.sort_values("Degre total", ascending=False)
            .head(max_nodes)["Utilisateur"]
            .tolist()
        )
        graph = graph.subgraph(selected_nodes).copy()
        nodes = nodes[nodes["Utilisateur"].isin(selected_nodes)]

    undirected = graph.to_undirected()
    pos = nx.spring_layout(undirected, seed=42, k=None, iterations=60)

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for source, target in graph.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=0.45, color="#94a3b8"),
        hoverinfo="none",
        showlegend=False,
    )

    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    node_lookup = nodes.set_index("Utilisateur").to_dict("index")
    max_degree = max((graph.degree(node) for node in graph.nodes), default=1)

    for node in graph.nodes:
        x, y = pos[node]
        info = node_lookup.get(node, {})
        node_x.append(x)
        node_y.append(y)
        node_size.append(8 + 24 * graph.degree(node) / max(max_degree, 1))
        node_color.append(info.get(color_by, 0))
        node_text.append(
            f"{info.get('Nom', node)}<br>"
            f"ID: {node}<br>"
            f"Communaute: {info.get('Communaute', 'N/A')}<br>"
            f"PageRank: {info.get('PageRank', 0):.6f}<br>"
            f"Betweenness: {info.get('Betweenness', 0):.6f}<br>"
            f"Degre: {graph.degree(node)}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        text=node_text,
        hoverinfo="text",
        marker=dict(
            size=node_size,
            color=node_color,
            colorscale="Turbo",
            showscale=True,
            colorbar=dict(title=color_by),
            line=dict(width=0.7, color="#ffffff"),
        ),
        showlegend=False,
    )

    figure = go.Figure(data=[edge_trace, node_trace])
    figure.update_layout(
        title="Graphe interactif FOLLOWS",
        height=720,
        showlegend=False,
        margin=dict(l=5, r=5, t=45, b=5),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#ffffff",
    )
    return figure


def render_graph_tab(snapshot: dict[str, Any]) -> None:
    graph = snapshot["graph"]
    nodes = snapshot["nodes"]
    if graph.number_of_nodes() == 0:
        st.warning("Le graphe est vide.")
        return

    c1, c2 = st.columns([0.35, 0.65])
    with c1:
        max_nodes = st.slider(
            "Nombre maximum de noeuds affiches",
            min_value=20,
            max_value=max(20, min(500, graph.number_of_nodes())),
            value=min(150, graph.number_of_nodes()),
            step=10,
        )
        color_by = st.selectbox(
            "Colorer les noeuds par",
            ["Communaute", "PageRank", "Betweenness", "Degre total"],
        )
    with c2:
        st.caption(
            "La taille des noeuds depend du degre total. Si le reseau est grand, "
            "le graphe affiche les utilisateurs les plus connectes pour rester lisible."
        )

    st.plotly_chart(
        network_figure(graph, nodes, max_nodes=max_nodes, color_by=color_by),
        use_container_width=True,
    )


def main() -> None:
    try:
        with st.spinner("Chargement du graphe depuis Neo4j..."):
            snapshot = build_dashboard_snapshot()
    except Exception as exc:
        st.error("Impossible de charger les donnees Neo4j.")
        st.markdown(
            """
            Verifiez que :
            - le fichier `.env` contient `NEO4J_URI`, `NEO4J_USER`,
              `NEO4J_PASSWORD` et `NEO4J_DATABASE` ;
            - Neo4j est demarre ;
            - les donnees ont ete generees avec `scripts/data_generator.py`.
            """
        )
        with st.expander("Detail technique"):
            st.code(str(exc))
        return

    render_header(snapshot)
    tab_stats, tab_influencers, tab_communities, tab_graph = st.tabs(
        [
            "Statistiques generales",
            "Influenceurs",
            "Communautes",
            "Graphe interactif",
        ]
    )
    with tab_stats:
        render_stats_tab(snapshot)
    with tab_influencers:
        render_influencers_tab(snapshot)
    with tab_communities:
        render_communities_tab(snapshot)
    with tab_graph:
        render_graph_tab(snapshot)


if __name__ == "__main__":
    main()
