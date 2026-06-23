"""
LinkUpDS – Design Premium + Feed Intelligent + Suggestions
Frontend Streamlit connecté au backend FastAPI.
"""

import streamlit as st
import sys
import os
import requests

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


def render_post_card(post):
    author = post.get("author") or {}
    name = author.get("name", "Membre")
    content = post.get("content", "")
    likes = post.get("likeCount", 0)
    sentiment = post.get("sentiment", "").lower()
    detected_topic = post.get("detectedTopic")
    topic_words = post.get("topicWords", [])
    
    # Déterminer l'emoji et la couleur du sentiment
    sentiment_emoji = "😐"
    sentiment_color = "#9E9E9E"
    if sentiment == "positif":
        sentiment_emoji = "😊"
        sentiment_color = "#4CAF50"
    elif sentiment == "negatif":
        sentiment_emoji = "😔"
        sentiment_color = "#F44336"
    
    # Badge sentiment
    sentiment_badge = f'<span class="sentiment-badge" style="background-color: {sentiment_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 8px;">{sentiment_emoji} {sentiment.capitalize()}</span>' if sentiment else ""
    
    # Badge topic
    topic_badge = ""
    if detected_topic:
        topic_emoji = "🏷️"
        topic_badge = f'<span class="topic-badge" style="background-color: #9C27B0; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 8px;">{topic_emoji} {detected_topic}</span>'
    
    # Score de pertinence (Smart Feed)
    relevance_score = post.get("relevanceScore")
    relevance_badge = f'<span class="relevance-badge" style="background-color: #2196F3; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-left: 8px;">⭐ {relevance_score:.2f}</span>' if relevance_score else ""

    st.markdown(f"""
    <div class="post-card">
        <div class="post-header">
            {avatar(name)}
            <p class="post-author">{name}</p>
        </div>
        <p class="post-content">{content}</p>
        <div class="post-stats">
            <span class="like-badge">❤️ {likes}</span>
            {sentiment_badge}
            {topic_badge}
            {relevance_badge}
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

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Feed", key="home_feed", use_container_width=True):
            st.session_state.page = "feed"
            st.rerun()
    with c2:
        if st.button("Publier", key="home_create", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
    with c3:
        if st.button("Profil", key="home_profile", use_container_width=True):
            st.session_state.page = "profile"
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
    
    # Récupérer les recommandations depuis l'API
    if st.session_state.user_id:
        res = api_get(f"/recommendations/friends/{st.session_state.user_id}", params={"top_n": 5, "with_details": True})
        
        if res["ok"] and res["data"]:
            recommendations = res["data"]
            
            for rec in recommendations:
                user_id = rec.get("user_id")
                score = rec.get("final_score", 0)
                common_interests = rec.get("common_interests", [])
                
                # Récupérer les infos de l'utilisateur
                user_res = api_get(f"/users/{user_id}")
                if user_res["ok"] and user_res["data"]:
                    user = user_res["data"]
                    name = user.get("name", "Utilisateur")
                    username = user.get("username", user_id[:12])
                    
                    with st.container():
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            st.markdown(f"**{name}** (@{username})")
                            if common_interests:
                                st.caption(f"Intérêts communs: {', '.join(common_interests[:3])}")
                            st.caption(f"Score: {score:.2f}")
                        with col2:
                            if st.button("Suivre", key=f"follow_rec_{user_id}", use_container_width=True):
                                follow_res = api_post(f"/follows/{user_id}")
                                if follow_res["ok"]:
                                    st.session_state.following_ids.add(user_id)
                                    st.success("Abonné!")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors du suivi")
                        st.markdown("---")
        else:
            st.markdown("""
            <div class="suggestion-box">
                <p>Aucune suggestion disponible pour le moment</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="suggestion-box">
            <p>Connecte-toi pour voir les suggestions</p>
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

        if st.button("Accueil", key="sidebar_home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("Feed", key="sidebar_feed", use_container_width=True):
            st.session_state.page = "feed"
            st.rerun()
        if st.button("Publier", key="sidebar_create", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
        if st.button("Profil", key="sidebar_profile", use_container_width=True):
            st.session_state.page = "profile"
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
if not st.session_state.user_id:
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