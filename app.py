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


def get_following_ids():
    if "following_ids" not in st.session_state or not isinstance(st.session_state.following_ids, set):
        st.session_state.following_ids = set()
    return st.session_state.following_ids


def invalidate_following_cache():
    st.session_state.following_ids = set()


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
if "following_ids" not in st.session_state:
    st.session_state.following_ids = None

# =========================
# CSS PREMIUM
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }

.stApp {
    background: radial-gradient(circle at 10% 20%, #0a0f1e, #03050b);
    color: #ffffff;
}
.block-container {
    animation: fadeIn 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(30px);}
    to { opacity: 1; transform: translateY(0);}
}
.premium-card {
    background: rgba(15, 25, 40, 0.6);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(46, 144, 255, 0.2);
    border-radius: 28px;
    padding: 24px;
    transition: all 0.3s ease;
}
.premium-card:hover {
    border-color: rgba(46, 144, 255, 0.6);
    transform: translateY(-6px);
}
.hero {
    text-align: center;
    padding: 50px 20px;
    background: linear-gradient(135deg, rgba(46,144,255,0.15), rgba(0,212,255,0.05));
    border-radius: 60px;
    margin-bottom: 40px;
}
.hero-title {
    font-size: 68px;
    font-weight: 800;
    background: linear-gradient(90deg, #2e90ff, #00d4ff, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 3s infinite alternate;
}
@keyframes glow {
    0% { text-shadow: 0 0 5px rgba(46,144,255,0.3);}
    100% { text-shadow: 0 0 30px rgba(0,212,255,0.6);}
}
.post-card {
    background: rgba(18, 28, 45, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(46, 144, 255, 0.2);
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 20px;
    transition: 0.25s ease;
}
.post-card:hover {
    border-color: #2e90ff;
    transform: scale(1.01);
}
.avatar {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #2e90ff, #7c3aed);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 20px;
    color: white;
}
.stButton > button {
    background: linear-gradient(95deg, #2e90ff, #1c6fd6);
    color: white;
    border: none;
    border-radius: 40px;
    padding: 10px 24px;
    font-weight: 600;
    transition: 0.2s;
    width: 100%;
}
.stButton > button:hover {
    transform: scale(1.02);
    background: linear-gradient(95deg, #3a9eff, #2a7fe6);
}
section[data-testid="stSidebar"] {
    background: rgba(5, 10, 20, 0.9);
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(46,144,255,0.2);
}
.suggestion-item {
    background: rgba(46,144,255,0.1);
    border-radius: 20px;
    padding: 12px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>
""", unsafe_allow_html=True)


def avatar(name):
    initial = name[0].upper() if name else "?"
    return f'<div class="avatar">{initial}</div>'


# =========================
# LOGIN / REGISTER (BACKEND)
# =========================
def login_page():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">🌐 LinkUpDS</div>
        <p style="font-size:20px; color:#94a3b8;">Le réseau social qui comprend tes connexions</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Se connecter", "✨ Rejoindre"])

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
                        invalidate_following_cache()
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

            if st.form_submit_button("Créer mon compte", use_container_width=True):
                res = api_post("/auth/register", {
                    "name": name,
                    "email": email,
                    "password": pwd,
                }, auth=False)

                if res["ok"]:
                    st.success("Compte créé ✅ Connecte-toi")
                    st.rerun()
                else:
                    st.error(res.get("error", "Erreur création compte"))


# =========================
# HOME
# =========================
def home_page():
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">Bienvenue, {st.session_state.user_name}</div>
        <p>Explore, partage, connecte-toi intelligemment.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("📰 Feed", use_container_width=True):
            st.session_state.page = "feed"
            st.rerun()
    with c2:
        if st.button("➕ Publier", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
    with c3:
        if st.button("👤 Profil", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()


# =========================
# FEED INTELLIGENT (BACKEND)
# =========================
def feed_page():
    st.markdown("<h1 style='text-align:center;'>📰 Fil d'actualité</h1>", unsafe_allow_html=True)

    feed_res = api_get(
        f"/feed/{st.session_state.user_id}",
        params={"limit": 100},
    )

    if not feed_res["ok"]:
        st.error(feed_res.get("error", "Impossible de charger le feed."))
        return

    if not isinstance(feed_res["data"], list):
        st.error("Réponse API invalide pour le feed.")
        return

    all_posts = feed_res["data"]

    if not all_posts:
        st.info("✨ Publie ton premier post ou suis d'autres membres.")
        return

    following_ids = get_following_ids()
    for post in all_posts:
        author_id = (post.get("author") or {}).get("userId") if isinstance(post, dict) else None
        if author_id and author_id != st.session_state.user_id:
            following_ids.add(author_id)

    for post in all_posts:
        if not isinstance(post, dict):
            continue

        author = post.get("author") or {}
        author_id = author.get("userId")
        name = author.get("name", "Membre")
        content = post.get("content", "")
        post_id = post.get("postId")
        likes = post.get("likeCount", 0)

        col1, col2 = st.columns([0.9, 0.1])

        with col1:
            st.markdown(f"""
            <div class="post-card">
                <div style="display:flex; align-items:center; gap:14px;">
                    {avatar(name)}
                    <b style="font-size:18px;">{name}</b>
                </div>
                <p style="margin-top:12px; font-size:16px;">{content}</p>
                <div style="display:flex; gap:20px; margin-top:12px;">
                    <span>❤️ {likes}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if author_id and author_id != st.session_state.user_id:
                if author_id in following_ids:
                    if st.button("❌ Ne plus suivre", key=f"unfollow_{post_id}"):
                        res = api_delete(f"/follows/{author_id}")
                        if res["ok"]:
                            following_ids.discard(author_id)
                            invalidate_following_cache()
                            st.rerun()
                        else:
                            st.error(res.get("error", "Erreur lors du désabonnement."))
                else:
                    if st.button("➕ Suivre", key=f"follow_{post_id}"):
                        res = api_post(f"/follows/{author_id}")
                        if res["ok"]:
                            following_ids.add(author_id)
                            invalidate_following_cache()
                            st.rerun()
                        else:
                            st.error(res.get("error", "Erreur lors du suivi."))

            if st.button("❤️ Like", key=f"like_{post_id}"):
                res = api_post(f"/likes/{post_id}")
                if res["ok"]:
                    st.rerun()
                else:
                    st.error(res.get("error", "Erreur lors du like."))


# =========================
# CREER POST (BACKEND)
# =========================
def create_post_page():
    st.markdown("<h1 style='text-align:center;'>✨ Nouvelle pensée</h1>", unsafe_allow_html=True)

    with st.form("post"):
        content = st.text_area("Exprime‑toi", height=160, placeholder="Quoi de neuf ?")

        if st.form_submit_button("Publier", use_container_width=True):
            if content.strip():
                res = api_post("/posts/", {"content": content.strip(), "topic": "general"})
                if res["ok"]:
                    st.success("Post publié 🚀")
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

    st.markdown(f"""
    <div style="text-align:center;">
        <div style="display:flex; justify-content:center;">{avatar(user.get('name', '?'))}</div>
        <h2>{user.get('name')}</h2>
        <p style="color:#2e90ff;">@{user.get('username') or user.get('userId', '')[:12]}</p>
        <p>{user.get('email')}</p>
        <div style="display:flex; gap:30px; justify-content:center; margin-top:20px;">
            <div><b>-</b><br>abonnés</div>
            <div><b>{len(get_following_ids())}</b><br>abonnements</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# SUGGESTIONS D'ABONNEMENTS (BACKEND)
# =========================
def suggestions_section():
    st.markdown("### 👥 Suggestions")
    st.caption("Suggestions indisponibles pour le moment.")


# =========================
# SIDEBAR
# =========================
if st.session_state.user_id:
    with st.sidebar:
        st.markdown(f"### ✨ {st.session_state.user_name}")
        st.markdown("---")

        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        if st.button("📰 Feed", use_container_width=True):
            st.session_state.page = "feed"
            st.rerun()
        if st.button("✏️ Publier", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()
        if st.button("👤 Profil", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()

        st.markdown("---")
        suggestions_section()
        st.markdown("---")

        if st.button("🔓 Déconnexion", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.page = "home"
            invalidate_following_cache()
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
