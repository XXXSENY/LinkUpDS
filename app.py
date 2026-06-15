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
# CSS PREMIUM
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

.stApp {
    background: radial-gradient(circle at 12% 18%, #e8f2ff 0%, #f5f9ff 42%, #eef2ff 100%);
    color: #0f172a;
}
.stApp, .stApp p, .stApp span, .stApp label, .stApp div { color: #0f172a; }

.block-container {
    max-width: 920px;
    padding-top: 2rem;
    animation: fadeIn 0.7s cubic-bezier(0.2, 0.9, 0.4, 1);
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ——— Branding LinkUpDS ——— */
.brand-logo {
    display: inline-flex;
    align-items: center;
    gap: 14px;
    justify-content: center;
}
.brand-icon {
    font-size: 52px;
    filter: drop-shadow(0 0 18px rgba(46, 144, 255, 0.45));
    animation: pulseIcon 3s ease-in-out infinite;
}
@keyframes pulseIcon {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.06); }
}
.brand-text {
    font-size: clamp(42px, 7vw, 68px);
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(120deg, #2563eb 0%, #0891b2 45%, #7c3aed 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: brandShine 4s linear infinite;
    filter: drop-shadow(0 2px 24px rgba(37, 99, 235, 0.25));
}
@keyframes brandShine {
    0% { background-position: 0% center; }
    100% { background-position: 200% center; }
}
.page-title {
    text-align: center;
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 1.5rem;
    background: linear-gradient(90deg, #1d4ed8, #6d28d9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ——— Hero & cards ——— */
.hero {
    text-align: center;
    padding: 48px 28px;
    background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(224,242,254,0.88));
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 32px;
    margin-bottom: 32px;
    box-shadow: 0 20px 50px rgba(37, 99, 235, 0.1);
}
.hero-subtitle {
    font-size: 1.15rem;
    color: #475569 !important;
    margin-top: 12px;
}

.post-card {
    background: #ffffff;
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 20px;
    padding: 20px 22px;
    margin-bottom: 8px;
    box-shadow: 0 8px 28px rgba(15, 23, 42, 0.06);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.post-card:hover {
    border-color: rgba(59, 130, 246, 0.45);
    box-shadow: 0 12px 32px rgba(37, 99, 235, 0.1);
}
.post-header {
    display: flex;
    align-items: center;
    gap: 14px;
}
.post-author {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
}
.post-content {
    margin: 14px 0 0 62px;
    font-size: 1rem;
    line-height: 1.6;
    color: #334155;
}
.post-stats {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 14px 0 0 62px;
    font-size: 0.95rem;
    color: #64748b;
}
.post-stats .like-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(239, 68, 68, 0.08);
    color: #dc2626;
    padding: 4px 12px;
    border-radius: 999px;
    font-weight: 600;
}

/* ——— Avatar ——— */
.avatar {
    width: 48px;
    height: 48px;
    min-width: 48px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 18px;
    color: white;
    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
}
.avatar-lg {
    width: 88px;
    height: 88px;
    min-width: 88px;
    font-size: 32px;
    margin: 0 auto;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
}

/* ——— Profil dashboard ——— */
.profile-card {
    text-align: center;
    background: linear-gradient(160deg, #ffffff 0%, #f0f7ff 100%);
    border: 1px solid rgba(59, 130, 246, 0.18);
    border-radius: 28px;
    padding: 36px 28px 28px;
    margin-bottom: 28px;
    box-shadow: 0 16px 40px rgba(37, 99, 235, 0.08);
}
.profile-name {
    font-size: 1.75rem;
    font-weight: 800;
    margin: 16px 0 4px;
    color: #0f172a;
}
.profile-username {
    color: #2563eb;
    font-weight: 600;
    font-size: 1rem;
    margin: 0 0 6px;
}
.profile-email {
    color: #64748b !important;
    font-size: 0.95rem;
    margin: 0 0 24px;
}
.profile-stats {
    display: flex;
    justify-content: center;
    gap: 48px;
    padding-top: 8px;
    border-top: 1px solid rgba(148, 163, 184, 0.2);
}
.stat-item b {
    display: block;
    font-size: 1.5rem;
    font-weight: 800;
    color: #1e40af;
}
.stat-item span {
    font-size: 0.85rem;
    color: #64748b !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.section-title {
    text-align: center;
    font-size: 1.35rem;
    font-weight: 700;
    margin: 32px 0 20px;
    color: #1e293b;
}

/* ——— Boutons uniformes ——— */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white !important;
    border: none;
    border-radius: 14px;
    min-height: 48px;
    padding: 10px 18px;
    font-weight: 600;
    font-size: 0.95rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    width: 100%;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.32);
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
}
.stButton > button:active {
    transform: translateY(0);
}
.stButton > button p,
.stButton > button span,
.stButton > button div {
    color: white !important;
}

/* Boutons icône (colonnes actions) */
div[data-testid="column"]:has(.stButton) .stButton > button {
    min-height: 44px;
    font-size: 1.35rem;
    padding: 8px 10px;
    border-radius: 12px;
}
.stButton > button[kind="secondary"] {
    background: #f1f5f9;
    color: #334155 !important;
    box-shadow: none;
    border: 1px solid #e2e8f0;
}

/* ——— Sidebar ——— */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-right: 1px solid rgba(59, 130, 246, 0.15);
}
section[data-testid="stSidebar"] * { color: #0f172a; }
.sidebar-brand {
    font-size: 1.1rem;
    font-weight: 800;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.sidebar-user {
    font-size: 0.9rem;
    color: #64748b !important;
    margin-bottom: 16px;
}
.sidebar-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(59,130,246,0.25), transparent);
    margin: 16px 0;
}
.suggestion-box {
    background: rgba(239, 246, 255, 0.9);
    border: 1px dashed rgba(59, 130, 246, 0.3);
    border-radius: 16px;
    padding: 14px;
    text-align: center;
}
.suggestion-box p {
    color: #64748b !important;
    font-size: 0.85rem;
    margin: 0;
}
section[data-testid="stSidebar"] .stButton > button {
    min-height: 42px;
    font-size: 0.88rem;
    border-radius: 12px;
    margin-bottom: 4px;
}
section[data-testid="stSidebar"] .stButton:last-of-type > button {
    background: linear-gradient(135deg, #64748b, #475569);
    box-shadow: 0 4px 12px rgba(71, 85, 105, 0.2);
}

/* ——— Formulaires ——— */
.stTextInput input, .stTextArea textarea {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid rgba(59, 130, 246, 0.22);
    border-radius: 12px;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
div[data-baseweb="tab-list"] button p {
    color: #0f172a;
    font-weight: 700;
}

/* ——— Action row feed/profil ——— */
.action-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
    justify-content: flex-start;
    padding-top: 8px;
}
</style>
""", unsafe_allow_html=True)


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
    st.markdown(f"""
    <div class="hero">
        {brand_logo_html()}
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