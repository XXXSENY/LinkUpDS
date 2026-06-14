"""
LinkUpDS – Design Premium + Feed Intelligent + Suggestions
"""

import streamlit as st
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.db_utils import LinkUpDB

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
if "db" not in st.session_state:
    st.session_state.db = LinkUpDB()
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "refresh_feed" not in st.session_state:
    st.session_state.refresh_feed = False

# =========================
# CSS PREMIUM
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(46, 144, 255, 0.12), transparent 28%),
        linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
    color: #0f172a;
}
.block-container {
    animation: fadeIn 0.8s cubic-bezier(0.2, 0.9, 0.4, 1.1);
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(30px);}
    to { opacity: 1; transform: translateY(0);}
}
.premium-card {
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 16px 45px rgba(15, 23, 42, 0.08);
    transition: all 0.3s ease;
}
.premium-card:hover {
    border-color: rgba(46, 144, 255, 0.36);
    transform: translateY(-3px);
}
.hero {
    text-align: center;
    padding: 50px 20px;
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 28px;
    margin-bottom: 40px;
    box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
}
.hero-title {
    font-size: 58px;
    font-weight: 800;
    background: linear-gradient(90deg, #1769e0, #0891b2, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero p, .post-meta, .muted {
    color: #64748b;
}
.post-card {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 18px;
    padding: 22px;
    margin: 8px 0 10px;
    box-shadow: 0 14px 34px rgba(15, 23, 42, 0.07);
    transition: 0.25s ease;
}
.post-card:hover {
    border-color: rgba(46, 144, 255, 0.38);
    transform: translateY(-2px);
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
    background: #ffffff;
    color: #1e293b;
    border: 1px solid #dbe3ee;
    border-radius: 999px;
    padding: 9px 18px;
    font-weight: 600;
    transition: all 0.2s ease;
    width: 100%;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
}
.stButton > button:hover {
    color: #1769e0;
    border-color: rgba(46, 144, 255, 0.45);
    background: #f8fbff;
    transform: translateY(-1px);
}
.stButton > button:focus {
    box-shadow: 0 0 0 3px rgba(46, 144, 255, 0.16);
}
button[kind="primary"] {
    color: #be123c !important;
    border: 1px solid rgba(225, 29, 72, 0.26) !important;
    background: #fff5f7 !important;
}
button[kind="primary"]:hover {
    color: #9f1239 !important;
    border-color: rgba(225, 29, 72, 0.42) !important;
    background: #ffe9ee !important;
}
.post-actions {
    margin: -4px 0 22px;
    padding: 0 6px;
}
.post-actions .stButton > button {
    min-height: 38px;
    padding: 8px 14px;
}
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.86);
    border-right: 1px solid rgba(148, 163, 184, 0.24);
}
.suggestion-item {
    background: rgba(241, 245, 249, 0.85);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 14px;
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
# LOGIN / REGISTER
# =========================
def login_page():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">🌐 LinkUpDS</div>
        <p style="font-size:20px; color:#94a3b8;">Le réseau social qui comprend tes connexions</p>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Se connecter", "S'inscrire"])
    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Connexion", use_container_width=True):
                user = st.session_state.db.get_user_by_email(email)
                if user:
                    st.session_state.user_id = user["userId"]
                    st.session_state.user_name = user["name"]
                    st.rerun()
                else:
                    st.error("Identifiants invalides")
    with tab2:
        with st.form("signup"):
            name = st.text_input("Nom complet")
            email = st.text_input("Email")
            pwd = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Créer mon compte", use_container_width=True):
                uid = f"user_{uuid.uuid4().hex[:8]}"
                st.session_state.db.create_user(uid, name, email, pwd)
                st.success("Compte créé-Connecte-toi")
                st.rerun()

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
# FEED INTELLIGENT
# =========================
def feed_page():
    st.markdown("<h1 style='text-align:center;'>Fil d’actualité</h1>", unsafe_allow_html=True)
    
    # Récupération des posts des suivis + propres posts
    followed_posts = st.session_state.db.get_feed(st.session_state.user_id)
    own_posts = st.session_state.db.get_posts_by_user(st.session_state.user_id)
    
    all_posts = followed_posts + own_posts
    all_posts = list({p.get("postId"): p for p in all_posts if p}.values())
    
    if not all_posts:
        st.info("Publie ton premier post ou suis d'autres membres.")
        return
    
    for post in all_posts:
        author = post.get("author", {})
        author_id = author.get("userId")
        name = author.get("name", "Membre")
        content = post.get("content", "")
        post_id = post.get("postId")
        likes = st.session_state.db.get_likes_count(post_id)
        
        st.markdown(f"""
        <div class="post-card">
            <div style="display:flex; align-items:center; gap:14px;">
                {avatar(name)}
                <div>
                    <b style="font-size:18px;">{name}</b>
                    <div class="post-meta">Publication</div>
                </div>
            </div>
            <p style="margin-top:14px; margin-bottom:0; font-size:16px; line-height:1.6;">{content}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="post-actions">', unsafe_allow_html=True)
        if author_id != st.session_state.user_id:
            action_cols = st.columns([0.22, 0.32, 0.46])
        else:
            action_cols = st.columns([0.22, 0.78])

        with action_cols[0]:
            if st.button(f"♥ {likes}", key=f"like_{post_id}", help="Aimer", type="primary"):
                st.session_state.db.like_post(st.session_state.user_id, post_id)
                st.rerun()
        if author_id != st.session_state.user_id:
            with action_cols[1]:
                following = [f["userId"] for f in st.session_state.db.get_following(st.session_state.user_id)]
                if author_id in following:
                    if st.button("Ne plus suivre", key=f"unfollow_{post_id}"):
                        st.session_state.db.unfollow(st.session_state.user_id, author_id)
                        st.rerun()
                else:
                    if st.button("Suivre", key=f"follow_{post_id}"):
                        st.session_state.db.follow(st.session_state.user_id, author_id)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# CREER POST
# =========================
def create_post_page():
    st.markdown("<h1 style='text-align:center;'>Nouvelle pensée</h1>", unsafe_allow_html=True)
    with st.form("post"):
        content = st.text_area("Exprime‑toi", height=160, placeholder="Quoi de neuf ?")
        if st.form_submit_button("Publier", use_container_width=True):
            if content.strip():
                pid = f"post_{uuid.uuid4().hex[:8]}"
                st.session_state.db.create_post(st.session_state.user_id, content, pid)
                st.success("Post publié")
                st.session_state.page = "feed"
                st.rerun()

# =========================
# PROFIL AVEC STATS
# =========================
def profile_page():
    user = st.session_state.db.get_user(st.session_state.user_id)
    if user:
        followers = st.session_state.db.get_followers(st.session_state.user_id)
        following = st.session_state.db.get_following(st.session_state.user_id)
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="display:flex; justify-content:center;">{avatar(user.get('name','?'))}</div>
            <h2>{user.get('name')}</h2>
            <p style="color:#2e90ff;">@{user.get('userId')[:12]}</p>
            <p>{user.get('email')}</p>
            <div style="display:flex; gap:30px; justify-content:center; margin-top:20px;">
                <div><b>{len(followers)}</b><br>abonnés</div>
                <div><b>{len(following)}</b><br>abonnements</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================
# SUGGESTIONS D'ABONNEMENTS
# =========================
def suggestions_section():
    st.markdown("### Suggestions")
    all_users = st.session_state.db.get_all_users()
    following = [f["userId"] for f in st.session_state.db.get_following(st.session_state.user_id)]
    suggestions = [u for u in all_users if u["userId"] != st.session_state.user_id and u["userId"] not in following][:5]
    for u in suggestions:
        st.write(f"**{u['name']}**")
        if st.button("Suivre", key=f"suggest_{u['userId']}", use_container_width=True):
            st.session_state.db.follow(st.session_state.user_id, u["userId"])
            st.rerun()

# =========================
# SIDEBAR
# =========================
if st.session_state.user_id:
    with st.sidebar:
        st.markdown(f"### {st.session_state.user_name}")
        st.markdown("---")
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
        st.markdown("---")
        suggestions_section()
        st.markdown("---")
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.user_name = None
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
