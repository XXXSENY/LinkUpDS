import random
import requests
from faker import Faker

fake = Faker("fr_FR")

BASE_URL = "http://127.0.0.1:8000"

# Centres d'intérêt possibles (ajouté pour l'équipe NLP & Recommandation)
INTERESTS_POOL = [
    "sport", "musique", "cinema", "technologie", "voyage",
    "cuisine", "lecture", "mode", "jeux_video", "politique",
    "sante", "art", "nature", "finance", "education"
]

# Templates de posts par centre d'intérêt
POST_TEMPLATES = {
    "sport": [
        "Je viens de battre mon record personnel sur {} !",
        "Quel match incroyable entre {} et {} !",
        "La saison de {} commence fort cette année.",
        "Je me suis inscrit au marathon de {}, qui vient ?",
        "Le sport c'est la vie ! Aujourd'hui j'ai fait {}."
    ],
    "musique": [
        "Je viens de découvrir l'album de {}, c'est une pépite !",
        "Concert de {} hier soir, absolument magique !",
        "Cette nouvelle chanson de {} est en boucle chez moi.",
        "Le dernier festival de {} était incroyable.",
        "Ma playlist du moment : {} en tête."
    ],
    "cinema": [
        "J'ai adoré le dernier film de {}, à voir absolument !",
        "La bande-annonce de {} est sortie, j'ai hâte !",
        "Soirée ciné avec {}, on a regardé {}.",
        "{} remporte l'Oscar du meilleur film, mérité !",
        "Le nouveau {} est un chef-d'œuvre."
    ],
    "technologie": [
        "Je teste actuellement le nouveau {}, c'est révolutionnaire !",
        "La dernière mise à jour de {} apporte plein de nouvelles fonctionnalités.",
        "J'ai enfin acheté un {}, j'adore !",
        "L'IA de {} est impressionnante.",
        "Les avancées technologiques dans {} sont fascinantes."
    ],
    "voyage": [
        "Je prépare mon voyage à {}, des conseils ?",
        "Je suis actuellement à {}, la ville est magnifique !",
        "Les plages de {} sont incroyables cet été.",
        "Prochaines vacances : direction {} !",
        "J'ai découvert un endroit secret à {}, c'est magique."
    ],
    "cuisine": [
        "J'ai testé la recette de {}, un délice !",
        "Le restaurant {} est une vraie découverte.",
        "Ma spécialité : le {}, un vrai régal !",
        "J'ai enfin réussi ma recette de {} !",
        "Ce soir au menu : {}, miam !"
    ],
    "lecture": [
        "Je lis actuellement {}, c'est captivant.",
        "Le nouveau roman de {} est un best-seller mérité.",
        "Je recommande absolument {} à tous les amateurs de lecture.",
        "La bibliothèque de {} est une mine d'or.",
        "J'ai adoré {}, je l'ai dévoré en une nuit !"
    ],
    "mode": [
        "La nouvelle collection de {} est magnifique.",
        "Mon look du jour : {} associé à {}.",
        "Les tendances de l'automne : {} en force.",
        "Ce que j'ai acheté chez {} : un vrai coup de cœur.",
        "Le style de {} m'inspire énormément."
    ],
    "jeux_video": [
        "Je suis en train de finir {}, un chef-d'œuvre !",
        "La nouvelle mise à jour de {} est géniale.",
        "Qui veut jouer à {} avec moi ce soir ?",
        "Le dernier jeu de {} a des graphismes époustouflants.",
        "J'ai passé 10 heures sur {}, impossible de décrocher !"
    ],
    "politique": [
        "Les élections approchent, il faut aller voter !",
        "La nouvelle politique de {} est très controversée.",
        "Je soutiens {} pour les prochaines élections.",
        "Le débat sur {} est essentiel aujourd'hui.",
        "Les décisions de {} impactent tout le monde."
    ],
    "sante": [
        "Je me suis mis au {}, ma santé va beaucoup mieux !",
        "La nutrition, c'est la clé : j'ai changé mon alimentation.",
        "Le yoga m'aide énormément à gérer mon stress.",
        "Mon médecin m'a conseillé de {}, je me sens mieux.",
        "La santé mentale est aussi importante que la santé physique."
    ],
    "art": [
        "J'ai visité l'exposition de {}, j'ai été émerveillé.",
        "Je crée actuellement une œuvre d'art sur {}.",
        "L'art contemporain de {} est fascinant.",
        "Ce tableau de {} est une véritable émotion.",
        "J'apprends la peinture, mes premiers essais sur {}."
    ],
    "nature": [
        "Randonnée aujourd'hui à {}, les paysages sont sublimes.",
        "La biodiversité dans {} est incroyable.",
        "Je protège la nature en faisant {}.",
        "Le coucher de soleil à {} est magique.",
        "Les animaux sauvages de {} sont fascinants."
    ],
    "finance": [
        "Je viens d'investir dans {}, un placement prometteur.",
        "La bourse a fait un bond aujourd'hui avec {}.",
        "Mon conseiller financier m'a recommandé de {}.",
        "Le bitcoin atteint de nouveaux sommets, que faire ?",
        "Mes placements dans {} sont très rentables cette année."
    ],
    "education": [
        "Je me forme en {} pour me reconvertir.",
        "Les cours en ligne de {} sont super bien faits.",
        "J'ai obtenu mon diplôme en {} !",
        "L'éducation est la clé de tout, j'investis dans {}.",
        "Les MOOCs sur {} sont d'une grande qualité."
    ]
}

# Compléments pour enrichir les posts
COMPLEMENTS = [
    "et c'était incroyable !",
    "je suis vraiment impressionné !",
    "hâte d'y retourner !",
    "quelle expérience !",
    "à ne pas manquer !",
    "je recommande chaudement !",
    "tout simplement parfait !",
    "j'en ai rêvé toute la semaine !",
    "je n'en reviens pas !",
    "un vrai bonheur !"
]

NB_USERS = 30
POSTS_PER_USER = 3
FOLLOW_PROBABILITY = 0.2
LIKE_PROBABILITY = 0.3


# =========================
# HELPERS API
# =========================

def register_user(name, email, password, interests=None):
    payload = {
        "name": name,
        "email": email,
        "password": password,
        "interests": interests or [],
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

def generate_meaningful_post(interests, is_question=False):
    """
    Génère un post avec du sens basé sur les intérêts de l'utilisateur
    """
    if not interests:
        interests = random.sample(INTERESTS_POOL, k=1)
    
    # Choisir un intérêt principal
    main_interest = random.choice(interests)
    
    # Sélectionner un template pour cet intérêt
    if main_interest in POST_TEMPLATES:
        templates = POST_TEMPLATES[main_interest]
        template = random.choice(templates)
        
        # Remplir le template avec des valeurs réalistes
        if "{}" in template:
            if random.random() < 0.3:
                # Ajouter un nom ou un lieu réaliste
                placeholders = [
                    fake.city(),
                    fake.name(),
                    fake.company(),
                    fake.word(),
                    fake.country(),
                    fake.catch_phrase()
                ]
                template = template.format(random.choice(placeholders))
            else:
                # Ajouter des mots de remplissage
                fillers = [
                    "mon nouveau projet",
                    "cette magnifique région",
                    "ce talentueux artiste",
                    "cette innovation",
                    "cette rencontre",
                    "cet événement marquant"
                ]
                template = template.format(random.choice(fillers))
        
        # Ajouter un complément aléatoire avec 50% de chance
        if random.random() < 0.5:
            template += " " + random.choice(COMPLEMENTS)
        
        # Pour les questions, ajouter un point d'interrogation
        if is_question or random.random() < 0.15:
            template = template.rstrip('.!') + ' ?'
        
        return template
    
    # Fallback : utiliser Faker pour générer un texte plus libre
    return fake.sentence(nb_words=random.randint(8, 15))


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
        interests = random.sample(INTERESTS_POOL, k=random.randint(2, 5))

        user = register_user(name, email, password, interests=interests)
        if not user:
            continue

        token = login(email, password)
        if not token:
            continue

        users.append({
            "id": user["userId"] if "userId" in user else user.get("id"),
            "email": email,
            "token": token,
            "interests": interests
        })

        print(f"User créé: {email} (Intérêts: {', '.join(interests)})")

    print(f"\n{len(users)} users créés\n")

    # =========================
    # 2. POSTS (avec du sens !)
    # =========================
    posts = []

    for u in users:
        # Chaque utilisateur poste entre 1 et POSTS_PER_USER fois
        nb_posts = random.randint(1, POSTS_PER_USER)
        
        for _ in range(nb_posts):
            # Générer un post basé sur ses intérêts
            content = generate_meaningful_post(u.get("interests", []))
            
            # Parfois, créer un post plus long
            if random.random() < 0.2:
                content += " " + fake.sentence(nb_words=random.randint(5, 10))
            
            # Parfois, une question pour engager l'interaction
            if random.random() < 0.1:
                content += " Qu'en pensez-vous ?"
            
            post = create_post(u["token"], content)

            if post:
                posts.append({
                    "postId": post.get("postId"),
                    "author": u["id"],
                    "content": content
                })
                print(f"Post créé par {u['email']}: {content[:50]}...")

    print(f"\n{len(posts)} posts créés\n")

    # =========================
    # 3. FOLLOW RELATIONS
    # =========================
    follow_count = 0
    for u in users:
        for v in users:
            if u["id"] != v["id"] and random.random() < FOLLOW_PROBABILITY:
                if follow(u["token"], v["id"]):
                    follow_count += 1

    print(f"{follow_count} relations follow créées\n")

    # =========================
    # 4. LIKES
    # =========================
    like_count = 0
    for u in users:
        for p in posts:
            if random.random() < LIKE_PROBABILITY:
                if like(u["token"], p["postId"]):
                    like_count += 1

    print(f"{like_count} likes créés\n")
    
    # =========================
    # STATS
    # =========================
    print("=== Statistiques ===")
    print(f"Utilisateurs: {len(users)}")
    print(f"Posts: {len(posts)}")
    print(f"Follows: {follow_count}")
    print(f"Likes: {like_count}")
    print("\nExemples de posts générés:")
    for i, p in enumerate(posts[:5]):
        print(f"{i+1}. {p['content']}")
    
    print("\nTerminé ✔")


if __name__ == "__main__":
    main()