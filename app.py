"""
LinkUpDS – Design Premium + Feed Intelligent + Suggestions
Frontend Streamlit connecté au backend FastAPI.
"""

import streamlit as st
import sys
import os
import requests
import pandas as pd
import plotly.express as px
import networkx as nx
import plotly.graph_objects as go
from neo4j import GraphDatabase

from src.team2.dashboard_data import load_dashboard_snapshot

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# =========================
# CONFIG BACKEND URL
# =========================
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

# Endpoints profil (définis dans src/routers/users.py — redémarrer l'API si 404)
API_USER_FOLLOWERS = "/users/{user_id}/followers"
API_USER_FOLLOWING = "/users/{user_id}/following"
API_USER_POSTS = "/users/{user_id}/posts"

CSS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "style.css")


def _auth_headers():
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_request(method, path, json_data=None, params=None, auth=True):
    """Appel HTTP centralisé vers le backend FastAPI."""
    try:
        headers = _auth_headers() if auth else {}
        kwargs = {"timeout": 15, "headers": headers}
        if json_data is not None:
            kwargs["json"] = json_data
        if params:
            kwargs["params"] = params

        resp = requests.request(method, f"{API_URL}{path}", **kwargs)

        if resp.status_code == 204:
            return {"ok": True, "data": None}

        data = None
        if resp.content:
            try:
                data = resp.json()
            except ValueError:
                data = resp.text

        if resp.ok:
            return {"ok": True, "data": data}

        error = "Erreur inconnue"
        if isinstance(data, dict):
            detail = data.get("detail")
            if isinstance(detail, list):
                error = detail[0].get("msg", str(detail)) if detail else error
            elif detail:
                error = detail
        elif isinstance(data, str) and data:
            error = data

        return {"ok": False, "status": resp.status_code, "error": error}

    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Backend indisponible. Lancez l'API avec : python -m uvicorn api:app"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Le backend met trop de temps à répondre."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def api_get(path, params=None, auth=True):
    return api_request("GET", path, params=params, auth=auth)


def api_post(path, data=None, auth=True):
    return api_request("POST", path, json_data=data, auth=auth)


def api_delete(path, auth=True):
    return api_request("DELETE", path, auth=auth)


def _api_error_message(res, fallback="Erreur API"):
    """Message d'erreur lisible selon le code HTTP."""
    status_code = res.get("status")
    error = res.get("error", fallback)

    if status_code == 401:
        return "Session expirée. Reconnecte-toi."
    if status_code == 403:
        return error or "Action non autorisée."
    if status_code == 404 and error == "Not Found":
        return (
            "Endpoint backend introuvable. "
            "Redémarre l'API : python -m uvicorn api:app --reload"
        )
    if status_code == 404:
        return error or "Ressource introuvable."
    if status_code == 500:
        return error or "Erreur interne du serveur."
    return error or fallback


def _is_endpoint_missing(res):
    return res.get("status") == 404 and res.get("error") == "Not Found"


def load_follow_stats(user_id):
    """Récupère followers et following depuis le backend."""
    followers_res = api_get(API_USER_FOLLOWERS.format(user_id=user_id))
    following_res = api_get(API_USER_FOLLOWING.format(user_id=user_id))

    errors = []
    followers = []
    following = []

    if followers_res["ok"] and isinstance(followers_res["data"], list):
        followers = followers_res["data"]
    elif _is_endpoint_missing(followers_res):
        errors.append(_api_error_message(followers_res))
    elif not followers_res["ok"]:
        errors.append(_api_error_message(followers_res, "Impossible de charger les abonnés."))

    if following_res["ok"] and isinstance(following_res["data"], list):
        following = following_res["data"]
    elif _is_endpoint_missing(following_res):
        if not errors:
            errors.append(_api_error_message(following_res))
    elif not following_res["ok"]:
        errors.append(_api_error_message(following_res, "Impossible de charger les abonnements."))

    return followers, following, errors


def get_following_ids():
    _, following, _ = load_follow_stats(st.session_state.user_id)
    api_ids = {u.get("userId") for u in following if u.get("userId")}
    if api_ids:
        st.session_state.following_ids = api_ids
        return api_ids

    if "following_ids" not in st.session_state or not isinstance(st.session_state.following_ids, set):
        st.session_state.following_ids = set()
    return st.session_state.following_ids


def remember_created_post(post_data):
    if not isinstance(post_data, dict):
        return
    post_id = post_data.get("postId")
    if not post_id:
        return
    if "my_post_ids" not in st.session_state:
        st.session_state.my_post_ids = []
    if post_id not in st.session_state.my_post_ids:
        st.session_state.my_post_ids.insert(0, post_id)


def load_user_posts(user_id, limit=100):
    """Récupère les publications via GET /users/{user_id}/posts."""
    res = api_get(API_USER_POSTS.format(user_id=user_id), params={"limit": limit})
    if res["ok"] and isinstance(res["data"], list):
        for post in res["data"]:
            remember_created_post(post)
        return res["data"], None

    if _is_endpoint_missing(res):
        return _load_user_posts_fallback(), _api_error_message(res)

    return [], _api_error_message(res, "Impossible de charger vos publications.")


def _load_user_posts_fallback():
    """Secours : GET /posts/{post_id} pour les posts mémorisés en session."""
    posts = []
    for post_id in st.session_state.get("my_post_ids", []):
        res = api_get(f"/posts/{post_id}")
        if res["ok"] and isinstance(res["data"], dict):
            posts.append(res["data"])
    return posts


# =========================
# STYLES
# =========================
def inject_styles():
    """Charge le CSS externe (assets/style.css)."""
    try:
        with open(CSS_FILE, encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Fichier CSS introuvable : assets/style.css")


# =========================
# CONFIG PAGE
# =========================
st.set_page_config(
    page_title="LinkUpDS – Le réseau intelligent",
    page_icon="🌐",
    layout="wide"
)

# =========================
# SESSION STATE
# =========================
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "flash_message" not in st.session_state:
    st.session_state.flash_message = None
if "flash_type" not in st.session_state:
    st.session_state.flash_type = "success"
if "following_ids" not in st.session_state:
    st.session_state.following_ids = set()
if "my_post_ids" not in st.session_state:
    st.session_state.my_post_ids = []

# =========================
# STYLES (injection)
# =========================
inject_styles()


def show_flash_message():
    if not st.session_state.flash_message:
        return

    message = st.session_state.flash_message
    flash_type = st.session_state.flash_type
    st.session_state.flash_message = None
    st.session_state.flash_type = "success"

    if flash_type == "error":
        st.error(message)
    elif flash_type == "warning":
        st.warning(message)
    else:
        st.success(message)


show_flash_message()


def avatar(name, large=False):
    initial = name[0].upper() if name else "?"
    css_class = "avatar avatar-lg" if large else "avatar"
    return f'<div class="{css_class}">{initial}</div>'


def brand_logo_html():
    return """
    <div class="brand-logo">
        <span class="brand-icon">🌐</span>
        <span class="brand-text">LinkUpDS</span>
    </div>
    """


def load_feed_posts(limit=100):
    feed_res = api_get(
        f"/feed/{st.session_state.user_id}",
        params={"limit": limit},
    )

    if not feed_res["ok"]:
        return None, feed_res.get("error", "Impossible de charger le feed.")

    if not isinstance(feed_res["data"], list):
        return None, "Réponse API invalide pour le feed."

    return feed_res["data"], None


@st.cache_data(ttl=60, show_spinner=False)
def load_network_dashboard_snapshot():
    """Instantané Neo4j mis en cache pendant une minute."""
    return load_dashboard_snapshot()

def get_neo4j_driver():
    """Crée le driver Neo4j à partir des variables d'environnement."""
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))

def load_graph_from_neo4j():
    """Récupère tous les utilisateurs et relations FOLLOWS depuis Neo4j et construit un DiGraph NetworkX."""
    driver = get_neo4j_driver()
    G = nx.DiGraph()
    with driver.session() as session:
        # Récupère tous les nœuds User (on suppose un label :User avec propriété userId)
        result_users = session.run("MATCH (u:User) RETURN u.userId AS userId")
        for record in result_users:
            G.add_node(record["userId"])

        # Récupère toutes les relations FOLLOWS
        result_rels = session.run(
            "MATCH (a:User)-[r:FOLLOWS]->(b:User) RETURN a.userId AS source, b.userId AS target"
        )
        for record in result_rels:
            G.add_edge(record["source"], record["target"])
    driver.close()
    return G

def compute_pagerank(G):
    """Calcule le PageRank et retourne un DataFrame trié."""
    pr = nx.pagerank(G, alpha=0.85)
    df = pd.DataFrame(list(pr.items()), columns=["Utilisateur", "PageRank"])
    df = df.sort_values(by="PageRank", ascending=False)
    return df

def _style_dashboard_figure(figure, height=410):
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=65, b=30),
        font=dict(family="Inter, sans-serif", color="#172033"),
        title_font=dict(size=18),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        hoverlabel=dict(bgcolor="#172033", font_color="#FFFFFF"),
    )
    figure.update_xaxes(gridcolor="#E2E8F0", zerolinecolor="#94A3B8")
    figure.update_yaxes(gridcolor="#E2E8F0", zerolinecolor="#94A3B8")
    return figure


def network_dashboard_page():
    """Dashboard Streamlit des indicateurs topologiques globaux."""
    top_left, top_right = st.columns([0.78, 0.22])
    with top_left:
        st.markdown(
            """
            <div class="dashboard-hero">
                <span class="dashboard-kicker">ÉQUIPE 2 · GRAPH MINING</span>
                <h1>Structure globale du réseau</h1>
                <p>Une lecture vivante de la densité, de la distance et de la connexité du graphe FOLLOWS.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        if st.button("← Retour", key="dashboard_back", width="stretch"):
            st.session_state.page = "home"
            st.rerun()
        if st.button("↻ Actualiser", key="dashboard_refresh", width="stretch"):
            load_network_dashboard_snapshot.clear()
            st.rerun()

    try:
        with st.spinner("Lecture du graphe Neo4j…"):
            snapshot = load_network_dashboard_snapshot()
    except Exception as exc:
        st.error(
            "Impossible de charger le graphe Neo4j. Vérifiez que la base est "
            "démarrée et que les variables NEO4J_* sont configurées."
        )
        with st.expander("Détail technique"):
            st.code(str(exc))
        return

    metrics = snapshot["metrics"]
    degree_df = pd.DataFrame(snapshot["degrees"])
    components_df = pd.DataFrame(snapshot["components"])

    if metrics["node_count"] == 0:
        st.warning(
            "Le graphe Neo4j ne contient encore aucun utilisateur. "
            "Générez les données, puis utilisez le bouton Actualiser."
        )
        return

    st.caption(
        f"Source : {snapshot['source']} · actualisé le "
        f"{snapshot['generated_at'].replace('T', ' ').replace('+00:00', ' UTC')}"
    )

    row1 = st.columns(4)
    row1[0].metric("Nœuds", f"{metrics['node_count']:,}".replace(",", " "))
    row1[1].metric("Arêtes", f"{metrics['edge_count']:,}".replace(",", " "))
    row1[2].metric("Densité", f"{metrics['density']:.1%}")
    row1[3].metric("Degré moyen", f"{metrics['average_degree']:.2f}")

    row2 = st.columns(4)
    distance_value = metrics["average_distance"]
    row2[0].metric(
        "Distance moyenne",
        "—" if distance_value is None else f"{distance_value:.2f}",
        help=metrics["average_distance_scope"],
    )
    row2[1].metric("Composantes faibles", metrics["weak_component_count"])
    row2[2].metric("Composantes fortes", metrics["strong_component_count"])
    row2[3].metric("Nœuds isolés", metrics["isolated_node_count"])

    core_size = metrics["largest_strong_component_size"]
    core_share = metrics["largest_strong_component_fraction"]
    st.info(
        f"Le réseau s'organise autour d'un cœur fortement connexe de "
        f"{core_size} utilisateurs ({core_share:.1%} du réseau). "
        f"La distance moyenne de {distance_value:.2f} arcs montre que les "
        "utilisateurs du cœur sont rapidement accessibles les uns depuis les autres."
    )

    st.markdown("### Distribution et équilibre des connexions")
    chart_controls, _ = st.columns([0.38, 0.62])
    degree_label = chart_controls.selectbox(
        "Type de degré",
        options=["Total", "Entrant", "Sortant"],
        index=0,
        help="Entrant = abonnés · Sortant = abonnements",
    )
    degree_column = {
        "Total": "total_degree",
        "Entrant": "in_degree",
        "Sortant": "out_degree",
    }[degree_label]

    chart_left, chart_right = st.columns(2)
    with chart_left:
        histogram = px.histogram(
            degree_df,
            x=degree_column,
            nbins=max(5, min(12, int(degree_df[degree_column].max()) + 1)),
            title=f"Distribution du degré {degree_label.lower()}",
            labels={degree_column: f"Degré {degree_label.lower()}", "count": "Utilisateurs"},
            color_discrete_sequence=["#356DF3"],
        )
        histogram.update_traces(marker_line_color="#2148B8", marker_line_width=1)
        histogram.update_layout(bargap=0.08, showlegend=False)
        histogram.update_yaxes(title="Utilisateurs")
        st.plotly_chart(
            _style_dashboard_figure(histogram),
            width="stretch",
            config={"displayModeBar": False},
            theme=None,
        )

    with chart_right:
        scatter = px.scatter(
            degree_df,
            x="out_degree",
            y="in_degree",
            size="total_degree",
            hover_name="user_id",
            title="Abonnements vs abonnés",
            labels={
                "out_degree": "Degré sortant (abonnements)",
                "in_degree": "Degré entrant (abonnés)",
                "total_degree": "Degré total",
            },
            color_discrete_sequence=["#D6A531"],
            size_max=25,
        )
        max_degree = max(
            int(degree_df["in_degree"].max()),
            int(degree_df["out_degree"].max()),
        )
        scatter.add_shape(
            type="line",
            x0=0,
            y0=0,
            x1=max_degree,
            y1=max_degree,
            line=dict(color="#475569", width=1, dash="dot"),
        )
        st.plotly_chart(
            _style_dashboard_figure(scatter),
            width="stretch",
            config={"displayModeBar": False},
            theme=None,
        )

    st.markdown("### Connexité du réseau")
    components_df["component"] = (
        "Composante " + components_df["component_rank"].astype(str)
    )
    component_chart = px.bar(
        components_df,
        x="component",
        y="size",
        color="component_type",
        barmode="group",
        text_auto=True,
        title="Taille des composantes faibles et fortes",
        labels={
            "component": "",
            "size": "Nombre de nœuds",
            "component_type": "Connexité",
        },
        color_discrete_map={"Faible": "#356DF3", "Forte": "#D6A531"},
    )
    component_chart.update_traces(marker_line_color="#172033", marker_line_width=0.8)
    st.plotly_chart(
        _style_dashboard_figure(component_chart, height=390),
        width="stretch",
        config={"displayModeBar": False},
        theme=None,
    )

    st.markdown("### Tableau des indicateurs")
    metric_table = pd.DataFrame(
        [
            ["Nombre de nœuds", metrics["node_count"], "Utilisateurs :User"],
            ["Nombre d'arêtes", metrics["edge_count"], "Relations FOLLOWS distinctes"],
            ["Densité", f"{metrics['density']:.4f}", "m / [n(n − 1)]"],
            ["Degré moyen total", f"{metrics['average_degree']:.3f}", "2m / n"],
            ["Degré entrant moyen", f"{metrics['average_in_degree']:.3f}", "m / n"],
            ["Degré sortant moyen", f"{metrics['average_out_degree']:.3f}", "m / n"],
            ["Distance moyenne", f"{distance_value:.3f}", metrics["average_distance_scope"]],
            ["Composantes faibles", metrics["weak_component_count"], "Orientation ignorée"],
            ["Composantes fortes", metrics["strong_component_count"], "Accessibilité mutuelle"],
        ],
        columns=["Indicateur", "Valeur", "Définition / périmètre"],
    )
    metric_table["Valeur"] = metric_table["Valeur"].astype(str)
    st.dataframe(metric_table, hide_index=True, width="stretch")

    with st.expander("Qualité des données et détail par utilisateur"):
        quality = snapshot["data_quality"]
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Boucles", quality["self_loop_count"])
        q2.metric("Relations dupliquées", quality["duplicate_follow_relationship_count"])
        q3.metric("IDs manquants", quality["missing_user_id_count"])
        q4.metric("IDs dupliqués", quality["duplicate_user_id_group_count"])
        st.dataframe(
            degree_df.sort_values("total_degree", ascending=False),
            hide_index=True,
            width="stretch",
            column_config={
                "user_id": "Utilisateur",
                "in_degree": "Entrant",
                "out_degree": "Sortant",
                "total_degree": "Total",
            },
        )

    st.markdown("### Analyse")
    st.markdown(
        f"""
        - **Connectivité élevée du cœur.** {core_size} utilisateurs forment une composante
          fortement connexe : chacun peut atteindre tous les autres en respectant le sens
          des abonnements.
        - **Réseau modérément dense.** La densité de {metrics['density']:.1%} signifie
          qu'environ une relation possible sur cinq existe déjà dans le jeu simulé.
        - **Faible éloignement.** {distance_value:.2f} arcs suffisent en moyenne dans le
          cœur, un terrain favorable à la diffusion rapide des contenus.
        - **Point de vigilance.** {metrics['isolated_node_count']} utilisateur reste isolé
          et devrait recevoir des recommandations d'abonnement spécifiques.
        """
    )

def pagerank_page():
    st.markdown("""
    <div class="dashboard-hero">
        <span class="dashboard-kicker">ÉQUIPE 2 · MEMBRE 3</span>
        <h1>Influenceurs selon le PageRank</h1>
        <p>Classement des utilisateurs les plus stratégiques du réseau.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Retour", key="pagerank_back"):
        st.session_state.page = "home"
        st.rerun()

    with st.spinner("Chargement du graphe et calcul du PageRank…"):
        try:
            G = load_graph_from_neo4j()
            if G.number_of_nodes() == 0:
                st.warning("Le graphe est vide. Générez d'abord les données.")
                return
            df_pr = compute_pagerank(G)
        except Exception as e:
            st.error(f"Erreur lors du chargement ou du calcul : {e}")
            st.stop()

    top10 = df_pr.head(10)

    # ---- Tableau Top 10 ----
    st.subheader("🏆 Top 10 des influenceurs")
    st.dataframe(
        top10.style.format({"PageRank": "{:.6f}"}),
        hide_index=True,
        column_config={
            "Utilisateur": "Utilisateur",
            "PageRank": st.column_config.NumberColumn("Score PageRank", format="%.6f")
        },
        use_container_width=True
    )

    # ---- Diagramme en barres ----
    st.subheader("📊 Scores des 10 premiers")
    fig_bar = px.bar(
        top10,
        x="Utilisateur",
        y="PageRank",
        text_auto=".4f",
        color="PageRank",
        color_continuous_scale="Blues",
        title="Top 10 PageRank"
    )
    fig_bar.update_traces(marker_line_color="#172033", marker_line_width=1)
    fig_bar.update_layout(coloraxis_showscale=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)

    # ---- Visualisation du réseau (taille = PageRank) ----
    st.subheader("🌐 Réseau global (taille des nœuds = PageRank)")

    # Pour un graphe volumineux, on échantillonne les 200 plus gros degrés pour la lisibilité
    if G.number_of_nodes() > 200:
        top_degree_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:200]
        sub_nodes = [n for n, _ in top_degree_nodes]
        sub_G = G.subgraph(sub_nodes).copy()
    else:
        sub_G = G.copy()

    # Calcul des positions avec spring_layout (peut être long sur >1000 nœuds)
    with st.spinner("Calcul de la disposition du graphe…"):
        pos = nx.spring_layout(sub_G, k=0.15, iterations=20, seed=42)

    # Création des traces Plotly
    edge_x = []
    edge_y = []
    for edge in sub_G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.3, color="#888"),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    node_size = []
    node_text = []
    pr_dict = nx.pagerank(sub_G, alpha=0.85)  # recalcule uniquement pour le sous-graphe
    max_pr = max(pr_dict.values()) if pr_dict else 1
    for node in sub_G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        score = pr_dict.get(node, 0)
        node_size.append(10 + 50 * (score / max_pr))  # taille proportionnelle
        node_text.append(f"{node}<br>PageRank: {score:.6f}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color='#356DF3',
            size=node_size,
            line_width=1,
            line_color='#172033'
        )
    )

    fig_network = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                title='Réseau FOLLOWS (taille ∝ PageRank)',
                                titlefont_size=16,
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=20, l=5, r=5, t=40),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                plot_bgcolor='white'
                            ))
    st.plotly_chart(fig_network, use_container_width=True)

    # ---- Analyse écrite ----
    st.subheader("📝 Interprétation")
    st.markdown(f"""
    - **{top10.iloc[0]['Utilisateur']}** est le nœud le plus influent avec un PageRank de **{top10.iloc[0]['PageRank']:.6f}**.  
      Cela signifie qu'il est suivi par des utilisateurs eux‑mêmes très suivis.  
    - La distribution des scores (voir l'histogramme ci‑dessus) est très asymétrique : quelques nœuds captent l'essentiel de l'autorité.  
    - Les utilisateurs du Top 10 sont de véritables **têtes de pont** : ils occupent une position privilégiée pour diffuser rapidement de l'information.
    """)

    # Export CSV (optionnel)
    csv = df_pr.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Télécharger le classement complet (CSV)",
        data=csv,
        file_name="pagerank_scores.csv",
        mime="text/csv"
    )



def render_post_card(post):
    author = post.get("author") or {}
    name = author.get("name", "Membre")
    content = post.get("content", "")
    likes = post.get("likeCount", 0)

    st.markdown(f"""
    <div class="post-card">
        <div class="post-header">
            {avatar(name)}
            <p class="post-author">{name}</p>
        </div>
        <p class="post-content">{content}</p>
        <div class="post-stats">
            <span class="like-badge">❤️ {likes}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# LOGIN / REGISTER (BACKEND)
# =========================
def login_page():
    st.markdown("""
<div class="hero">
    <div class="brand-logo">
        <span class="brand-icon">🌐</span>
        <span class="brand-text">LinkUpDS</span>
    </div>
    <p class="hero-subtitle">Le réseau social qui comprend tes connexions</p>
</div>
""", unsafe_allow_html=True)

    if st.button("📊 Explorer l'analyse du réseau", key="public_dashboard", width="stretch"):
        st.session_state.page = "network_dashboard"
        st.rerun()

    tab1, tab2 = st.tabs(["Se connecter", "S'inscrire"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Mot de passe", type="password")

            if st.form_submit_button("Connexion", use_container_width=True):
                res = api_post("/auth/login", {"email": email, "password": pwd}, auth=False)

                if res["ok"]:
                    token_data = res.get("data")
                    if not isinstance(token_data, dict) or not token_data.get("access_token"):
                        st.error("Réponse de connexion invalide.")
                        return

                    st.session_state.access_token = token_data["access_token"]
                    me = api_get("/auth/me")
                    user_data = me.get("data")
                    if me["ok"] and isinstance(user_data, dict) and user_data.get("userId"):
                        st.session_state.user_id = user_data["userId"]
                        st.session_state.user_name = user_data.get("name", "Membre")
                        st.session_state.page = "home"
                        st.session_state.following_ids = set()
                        st.session_state.my_post_ids = []
                        st.rerun()
                    else:
                        st.session_state.access_token = None
                        st.error(me.get("error", "Impossible de récupérer le profil."))
                else:
                    st.error(res.get("error", "Identifiants invalides"))

    with tab2:
        with st.form("signup"):
            name = st.text_input("Nom complet")
            email = st.text_input("Email")
            pwd = st.text_input("Mot de passe", type="password")

            if st.form_submit_button("✨ Créer mon compte", use_container_width=True):
                res = api_post("/auth/register", {
                    "name": name,
                    "email": email,
                    "password": pwd,
                }, auth=False)

                if res["ok"]:
                    login_res = api_post("/auth/login", {"email": email, "password": pwd}, auth=False)
                    token_data = login_res.get("data")

                    if login_res["ok"] and isinstance(token_data, dict) and token_data.get("access_token"):
                        st.session_state.access_token = token_data["access_token"]
                        me = api_get("/auth/me")
                        user_data = me.get("data")

                        if me["ok"] and isinstance(user_data, dict) and user_data.get("userId"):
                            st.session_state.user_id = user_data["userId"]
                            st.session_state.user_name = user_data.get("name", name or "Membre")
                            st.session_state.page = "home"
                            st.session_state.following_ids = set()
                            st.session_state.my_post_ids = []
                            st.session_state.flash_message = "Compte créé avec succès. Bienvenue sur LinkUpDS."
                            st.session_state.flash_type = "success"
                            st.rerun()

                    st.session_state.flash_message = "Compte créé avec succès. Connecte-toi pour continuer."
                    st.session_state.flash_type = "success"
                    st.rerun()
                else:
                    st.error(res.get("error", "Erreur création compte"))


# =========================
# HOME
# =========================
def home_page():
    st.markdown(f"""
    <div class="hero">
        <p class="page-title" style="margin-bottom:8px;">👋 Bienvenue, {st.session_state.user_name}</p>
        <p class="hero-subtitle">Explore, partage, connecte-toi intelligemment.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("Feed", use_container_width=True):
            st.session_state.page = "feed"
            st.rerun()
    with c2:
        if st.button("Publier", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
    with c3:
        if st.button("Profil", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
    with c4:
        if st.button("Analyse réseau", use_container_width=True):
            st.session_state.page = "network_dashboard"
            st.rerun()


# =========================
# FEED INTELLIGENT (BACKEND)
# =========================
def feed_page():
    st.markdown('<p class="page-title">Fil d\'actualité</p>', unsafe_allow_html=True)

    all_posts, error = load_feed_posts()
    if error:
        st.error(error)
        return

    if not all_posts:
        st.info("Aucun post à afficher pour le moment.")
        return

    following_ids = get_following_ids()

    for post in all_posts:
        if not isinstance(post, dict):
            continue

        author = post.get("author") or {}
        author_id = author.get("userId")
        post_id = post.get("postId")

        col1, col2 = st.columns([0.84, 0.16])

        with col1:
            render_post_card(post)

        with col2:
            if author_id and author_id != st.session_state.user_id:
                if author_id in following_ids:
                    if st.button("👤−", key=f"unfollow_{post_id}", help="Ne plus suivre", use_container_width=True):
                        res = api_delete(f"/follows/{author_id}")
                        if res["ok"]:
                            st.session_state.following_ids.discard(author_id)
                            st.rerun()
                        else:
                            st.error(_api_error_message(res, "Erreur lors du désabonnement."))
                else:
                    if st.button("👤+", key=f"follow_{post_id}", help="Suivre", use_container_width=True):
                        res = api_post(f"/follows/{author_id}")
                        if res["ok"]:
                            st.session_state.following_ids.add(author_id)
                            st.rerun()
                        else:
                            st.error(_api_error_message(res, "Erreur lors du suivi."))

            if st.button("❤️", key=f"like_{post_id}", help="Like", use_container_width=True):
                res = api_post(f"/likes/{post_id}")
                if res["ok"]:
                    st.rerun()
                else:
                    st.error(_api_error_message(res, "Erreur lors du like."))


# =========================
# CREER POST (BACKEND)
# =========================
def create_post_page():
    st.markdown('<p class="page-title">Nouvelle pensée</p>', unsafe_allow_html=True)

    with st.form("post"):
        content = st.text_area("Exprime‑toi", height=160, placeholder="Quoi de neuf ?")

        if st.form_submit_button("Publier", use_container_width=True):
            if content.strip():
                res = api_post("/posts/", {"content": content.strip(), "topic": "general"})
                if res["ok"]:
                    remember_created_post(res.get("data"))
                    st.success("Post publié")
                    st.session_state.page = "feed"
                    st.rerun()
                else:
                    st.error(res.get("error", "Erreur lors de la publication."))
            else:
                st.warning("Le contenu ne peut pas être vide.")


# =========================
# PROFIL AVEC STATS (BACKEND)
# =========================
def profile_page():
    user_res = api_get(f"/users/{st.session_state.user_id}")

    if not user_res["ok"]:
        st.error(user_res.get("error", "Impossible de charger le profil."))
        return

    user = user_res["data"]

    if not isinstance(user, dict):
        st.error("Réponse API invalide pour le profil.")
        return

    # Compteurs followers / following synchronisés avec le backend
    followers, following, stats_errors = load_follow_stats(st.session_state.user_id)
    for msg in stats_errors:
        st.warning(msg)

    st.markdown(f"""
    <div class="profile-card">
        <div style="display:flex; justify-content:center;">{avatar(user.get('name', '?'), large=True)}</div>
        <p class="profile-name">{user.get('name')}</p>
        <p class="profile-username">@{user.get('username') or user.get('userId', '')[:12]}</p>
        <p class="profile-email">{user.get('email')}</p>
        <div class="profile-stats">
            <div class="stat-item"><b>{len(followers)}</b><span>abonnés</span></div>
            <div class="stat-item"><b>{len(following)}</b><span>abonnements</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="section-title">Mes publications</p>', unsafe_allow_html=True)

    my_posts, posts_error = load_user_posts(st.session_state.user_id)
    if posts_error:
        st.warning(posts_error)

    if not my_posts:
        st.info("Aucune publication personnelle à afficher pour le moment.")
        return

    for post in my_posts:
        if not isinstance(post, dict):
            continue

        post_id = post.get("postId")
        col1, col2 = st.columns([0.84, 0.16])

        with col1:
            render_post_card(post)

        with col2:
            if post_id and st.button("🗑️", key=f"delete_post_{post_id}", help="Supprimer", use_container_width=True):
                res = api_delete(f"/posts/{post_id}")
                if res["ok"]:
                    if post_id in st.session_state.my_post_ids:
                        st.session_state.my_post_ids.remove(post_id)
                    st.session_state.flash_message = "Publication supprimée avec succès."
                    st.session_state.flash_type = "success"
                    st.rerun()
                else:
                    st.error(_api_error_message(res, "Erreur lors de la suppression."))


# =========================
# SUGGESTIONS D'ABONNEMENTS (BACKEND)
# =========================
def suggestions_section():
    st.markdown("### 👥 Suggestions")
    st.markdown("""
    <div class="suggestion-box">
        <p>Suggestions d'abonnements bientôt disponibles</p>
    </div>
    """, unsafe_allow_html=True)


# =========================
# SIDEBAR
# =========================
if st.session_state.user_id:
    with st.sidebar:
        st.markdown(f'<p class="sidebar-brand">LinkUpDS</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="sidebar-user">✨ {st.session_state.user_name}</p>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        if st.button("Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("Feed", use_container_width=True):
            st.session_state.page = "feed"
            st.rerun()
        if st.button("Publier", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
        if st.button("Profil", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()
        if st.button("Analyse réseau", use_container_width=True):
            st.session_state.page = "network_dashboard"
            st.rerun()
        if st.button("Influenceurs", use_container_width=True):
            st.session_state.page = "pagerank"
            st.rerun()


        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        suggestions_section()
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        if st.button("Déconnexion", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.page = "home"
            st.session_state.following_ids = set()
            st.session_state.my_post_ids = []
            st.rerun()


# =========================
# ROUTAGE PRINCIPAL
# =========================
if st.session_state.page == "network_dashboard":
    network_dashboard_page()
elif st.session_state.page == "pagerank":
    pagerank_page()
elif not st.session_state.user_id:
    login_page()
else:
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "feed":
        feed_page()
    elif st.session_state.page == "create":
        create_post_page()
    elif st.session_state.page == "profile":
        profile_page()
    else:
        home_page()
