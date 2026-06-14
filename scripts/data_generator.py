"""
Générateur de données fictives pour LinkUpDS
Utilise Faker pour créer des utilisateurs, posts, likes et abonnements
Exécution : python scripts/data_generator.py
"""

import random
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from src.db_utils import LinkUpDB

fake = Faker("fr_FR")  # Données françaises

# Configuration
NB_USERS = 50          # À monter à 500 après test
POSTS_PER_USER = 3
LIKES_PROBABILITY = 0.1
FOLLOW_PROBABILITY = 0.05

def generate_users(db, n=NB_USERS):
    print(f"👥 Création de {n} utilisateurs...")
    users = []
    for i in range(n):
        name = fake.name()
        email = fake.email()
        password = "password123"  # mot de passe simple pour les tests
        user_id = f"user_fake_{i}_{random.randint(1000,9999)}"
        
        try:
            user = db.create_user(
                user_id=user_id,
                name=name,
                email=email,
                password=password,
                bio=fake.sentence(nb_words=10),
                city=fake.city()
            )
            users.append(user_id)
            if (i+1) % 10 == 0:
                print(f"   ✅ {i+1}/{n} utilisateurs créés")
        except Exception as e:
            print(f"   ⚠️ Erreur sur {name} : {e}")
    print(f"✅ {len(users)} utilisateurs créés\n")
    return users

def generate_posts(db, users, posts_per_user=POSTS_PER_USER):
    print(f"📝 Création de posts...")
    total = 0
    for user_id in users:
        nb = random.randint(1, posts_per_user)
        for _ in range(nb):
            content = fake.paragraph(nb_sentences=random.randint(1, 4))
            try:
                db.create_post(user_id=user_id, content=content)
                total += 1
            except:
                pass
    print(f"✅ {total} posts créés\n")

def generate_follows(db, users, probability=FOLLOW_PROBABILITY):
    print(f"🔗 Création d'abonnements...")
    count = 0
    for follower in users:
        for followee in users:
            if follower != followee and random.random() < probability:
                try:
                    db.follow(follower, followee)
                    count += 1
                except:
                    pass
    print(f"✅ {count} abonnements créés\n")

def generate_likes(db, probability=LIKES_PROBABILITY):
    print(f"❤️ Création de likes...")
    
    # Récupérer tous les posts
    with db.driver.session() as session:
        result = session.run("MATCH (p:Post) RETURN p.postId AS postId")
        posts = [r["postId"] for r in result]
    
    # Récupérer tous les utilisateurs
    with db.driver.session() as session:
        result = session.run("MATCH (u:User) RETURN u.userId AS userId")
        users = [r["userId"] for r in result]
    
    count = 0
    for user_id in users:
        for post_id in posts:
            if random.random() < probability:
                try:
                    db.like_post(user_id, post_id)
                    count += 1
                except:
                    pass
    print(f"✅ {count} likes créés\n")

def main():
    print("=" * 50)
    print("🌐 GÉNÉRATION DE DONNÉES POUR LINKUPDS")
    print("=" * 50)
    
    db = LinkUpDB()
    
    # 1. Utilisateurs
    users = generate_users(db)
    
    # 2. Posts
    generate_posts(db, users)
    
    # 3. Abonnements
    generate_follows(db, users)
    
    # 4. Likes
    generate_likes(db)
    
    print("=" * 50)
    print("🎉 GÉNÉRATION TERMINÉE")
    print("=" * 50)
    
    db.close()

if __name__ == "__main__":
    main()
