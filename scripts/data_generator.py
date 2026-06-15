import random
import requests
from faker import Faker

fake = Faker("fr_FR")

BASE_URL = "http://127.0.0.1:8000"

NB_USERS = 30
POSTS_PER_USER = 3
FOLLOW_PROBABILITY = 0.2
LIKE_PROBABILITY = 0.3


# =========================
# HELPERS API
# =========================

def register_user(name, email, password):
    payload = {
        "name": name,
        "email": email,
        "password": password
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if r.status_code not in (200, 201):
        print("Register error:", r.text)
        return None
    return r.json()


def login(email, password):
    payload = {"email": email, "password": password}
    r = requests.post(f"{BASE_URL}/auth/login", json=payload)
    if r.status_code != 200:
        print("Login error:", r.text)
        return None
    return r.json()["access_token"]


def create_post(token, content):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"content": content}
    r = requests.post(f"{BASE_URL}/posts/", json=payload, headers=headers)
    return r.json() if r.status_code in (200, 201) else None


def follow(token, user_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE_URL}/follows/{user_id}", headers=headers)
    return r.status_code == 200


def like(token, post_id):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE_URL}/likes/{post_id}", headers=headers)
    return r.status_code == 200


def get_feed(user_id):
    r = requests.get(f"{BASE_URL}/feed/{user_id}")
    return r.json() if r.status_code == 200 else []


# =========================
# GENERATION
# =========================

def main():
    print("Génération via API LinkUpDS\n")

    users = []

    # =========================
    # 1. USERS
    # =========================
    for i in range(NB_USERS):
        name = fake.name()
        email = fake.unique.email().strip().lower()
        password = "password123"

        user = register_user(name, email, password)
        if not user:
            continue

        token = login(email, password)
        if not token:
            continue

        users.append({
            "id": user["userId"] if "userId" in user else user.get("id"),
            "email": email,
            "token": token
        })

        print(f"User créé: {email}")

    print(f"\n{len(users)} users créés\n")

    # =========================
    # 2. POSTS
    # =========================
    posts = []

    for u in users:
        for _ in range(random.randint(1, POSTS_PER_USER)):
            content = fake.sentence(nb_words=12)
            post = create_post(u["token"], content)

            if post:
                posts.append({
                    "postId": post.get("postId"),
                    "author": u["id"]
                })

    print(f"{len(posts)} posts créés\n")

    # =========================
    # 3. FOLLOW RELATIONS
    # =========================
    for u in users:
        for v in users:
            if u["id"] != v["id"] and random.random() < FOLLOW_PROBABILITY:
                follow(u["token"], v["id"])

    print("Relations follow créées\n")

    # =========================
    # 4. LIKES
    # =========================
    for u in users:
        for p in posts:
            if random.random() < LIKE_PROBABILITY:
                like(u["token"], p["postId"])

    print("Likes créés\n")
    print("Terminé ✔")


if __name__ == "__main__":
    main()