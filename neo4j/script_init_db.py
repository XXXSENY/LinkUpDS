import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
import random
import time

load_dotenv(dotenv_path=r"C:\Users\DELL\Desktop\Cours\Exam_NoSQL\LinkUpDS\neo4j\database.env")

class ReseauSocialDB:
    
    def __init__(self):
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        mongo_db_name = os.getenv('MONGODB_DATABASE', 'mini_socialnetwork')
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        
        # Connexion MongoDB
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client[mongo_db_name]
        self.users_collection: Collection = self.mongo_db['users']
        self.posts_collection: Collection = self.mongo_db['posts']
        
        # Connexion Neo4j
        self.neo4j_driver = None
        try:
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_user, neo4j_password)
            )
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            print("Connexion Neo4j établie")
        except Exception as e:
            print(f"⚠️ Erreur Neo4j: {e}")
            self.neo4j_driver = None
        
        self.init_indexes()
        
    def init_indexes(self):
        
        try:
            self.users_collection.create_index('email', unique=True)
            self.users_collection.create_index('username', unique=True)
            self.users_collection.create_index('id')
        except Exception as e:
            print(f" Index MongoDB: {e}")
        
        self.posts_collection.create_index('author_id')
        self.posts_collection.create_index('date_publication')
        
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            except Exception as e:
                print(f" Contrainte Neo4j: {e}")
            
    def close(self):
        self.mongo_client.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
    
    def generate_unique_id(self, prefix: str) -> str:
        """Génère un ID unique avec timestamp + random + microsecondes"""
        timestamp = int(time.time() * 1000) 
        random_suffix = random.randint(10000, 99999)
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def create_user(self, username: str, email: str, force: bool = False):
        """Crée un utilisateur avec vérification d'existence"""
        
        # Vérifier si l'utilisateur existe déjà
        existing = self.users_collection.find_one({'username': username})
        if existing:
            if force:
                print(f"Suppression de l'utilisateur existant: {username}")
                self.users_collection.delete_one({'username': username})
                if self.neo4j_driver:
                    try:
                        with self.neo4j_driver.session() as session:
                            session.run(
                                "MATCH (u:User {username: $username}) DETACH DELETE u",
                                username=username
                            )
                    except:
                        pass
            else:
                print(f"Utilisateur '{username}' existe déjà (ID: {existing['id']})")
                return existing
        
        # Générer un ID unique
        user_id = self.generate_unique_id('user')
        
        # Tentative avec vérification
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                user_data = {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'created_at': datetime.now(),
                    'stats': {
                        'followers_count': 0,
                        'following_count': 0,
                        'posts_count': 0
                    }
                }
                
                self.users_collection.insert_one(user_data)
                
                # Neo4j
                if self.neo4j_driver:
                    try:
                        with self.neo4j_driver.session() as session:
                            session.run(
                                """
                                CREATE (u:User {
                                    id: $id,
                                    username: $username,
                                    created_at: $created_at
                                })
                                """,
                                id=user_id,
                                username=username,
                                created_at=datetime.now().isoformat()
                            )
                    except Exception as e:
                        print(f"Erreur Neo4j (create_user): {e}")
                
                return user_data
                
            except Exception as e:
                if 'duplicate key' in str(e) and attempt < max_attempts - 1:
                    print(f"Collision d'ID, régénération... (tentative {attempt+1}/{max_attempts})")
                    user_id = self.generate_unique_id('user')
                    time.sleep(0.01)  # Petit délai
                else:
                    raise e
        
        raise Exception("Impossible de créer l'utilisateur après plusieurs tentatives")
    
    def create_post(self, author_id: str, content: str) -> Dict[str, Any]:
        """Crée un post avec ID unique"""
        post_id = self.generate_unique_id('post')
        
        post_data = {
            'id': post_id,
            'author_id': author_id,
            'content': content,
            'date_publication': datetime.now(),
            'stats': {
                'likes_count': 0,
                'comments_count': 0,
                'shares_count': 0
            }
        }
        
        # Tentative avec vérification
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.posts_collection.insert_one(post_data)
                break
            except Exception as e:
                if 'duplicate key' in str(e) and attempt < max_attempts - 1:
                    post_id = self.generate_unique_id('post')
                    post_data['id'] = post_id
                    time.sleep(0.01)
                else:
                    raise e
        
        # Mettre à jour le compteur
        self.users_collection.update_one(
            {'id': author_id},
            {'$inc': {'stats.posts_count': 1}}
        )
        
        # Neo4j
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    session.run(
                        """
                        MATCH (u:User {id: $author_id})
                        CREATE (p:Post {
                            id: $post_id,
                            content: $content,
                            date_publication: $date_publication
                        })
                        CREATE (u)-[:PUBLISH]->(p)
                        """,
                        author_id=author_id,
                        post_id=post_id,
                        content=content,
                        date_publication=datetime.now().isoformat()
                    )
            except Exception as e:
                print(f" Erreur Neo4j (create_post): {e}")
        
        return post_data
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users_collection.find_one({'id': user_id})
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        return self.users_collection.find_one({'username': username})
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = self.users_collection.update_one(
            {'id': user_id},
            {'$set': updates}
        )
        if result.modified_count > 0:
            return self.get_user(user_id)
        return None
    
    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self.posts_collection.find_one({'id': post_id})
    
    def get_user_posts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return list(self.posts_collection.find(
            {'author_id': user_id}
        ).sort('date_publication', -1).limit(limit))
    
    def update_post(self, post_id: str, content: str) -> Optional[Dict[str, Any]]:
        result = self.posts_collection.update_one(
            {'id': post_id},
            {'$set': {
                'content': content,
                'updated_at': datetime.now()
            }}
        )
        if result.modified_count > 0:
            return self.get_post(post_id)
        return None
    
    def delete_post(self, post_id: str) -> bool:
        post = self.get_post(post_id)
        if not post:
            return False
        
        self.posts_collection.delete_one({'id': post_id})
        
        self.users_collection.update_one(
            {'id': post['author_id']},
            {'$inc': {'stats.posts_count': -1}}
        )
        
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session() as session:
                    session.run(
                        "MATCH (p:Post {id: $post_id}) DETACH DELETE p",
                        post_id=post_id
                    )
            except Exception as e:
                print(f" Erreur Neo4j (delete_post): {e}")
        
        return True
    
    # Relations
    
    def follow_user(self, follower_id: str, followed_id: str) -> bool:
        if follower_id == followed_id or not self.neo4j_driver:
            return False
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (follower:User {id: $follower_id})
                    MATCH (followed:User {id: $followed_id})
                    RETURN EXISTS((follower)-[:FOLLOWS]->(followed)) AS follows
                    """,
                    follower_id=follower_id,
                    followed_id=followed_id
                )
                
                record = result.single()
                if record and record['follows']:
                    return False
                
                session.run(
                    """
                    MATCH (follower:User {id: $follower_id})
                    MATCH (followed:User {id: $followed_id})
                    CREATE (follower)-[:FOLLOWS {created_at: $created_at}]->(followed)
                    """,
                    follower_id=follower_id,
                    followed_id=followed_id,
                    created_at=datetime.now().isoformat()
                )
                
                self.users_collection.update_one(
                    {'id': follower_id},
                    {'$inc': {'stats.following_count': 1}}
                )
                self.users_collection.update_one(
                    {'id': followed_id},
                    {'$inc': {'stats.followers_count': 1}}
                )
                
                return True
        except Exception as e:
            print(f" Erreur Neo4j (follow_user): {e}")
            return False
    
    def unfollow_user(self, follower_id: str, followed_id: str) -> bool:
        if not self.neo4j_driver:
            return False
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (follower:User {id: $follower_id})
                    MATCH (followed:User {id: $followed_id})
                    MATCH (follower)-[r:FOLLOWS]->(followed)
                    RETURN r IS NOT NULL AS follows
                    """,
                    follower_id=follower_id,
                    followed_id=followed_id
                )
                
                record = result.single()
                if not record or not record['follows']:
                    return False
                
                session.run(
                    """
                    MATCH (follower:User {id: $follower_id})
                    MATCH (followed:User {id: $followed_id})
                    MATCH (follower)-[r:FOLLOWS]->(followed)
                    DELETE r
                    """,
                    follower_id=follower_id,
                    followed_id=followed_id
                )
                
                self.users_collection.update_one(
                    {'id': follower_id},
                    {'$inc': {'stats.following_count': -1}}
                )
                self.users_collection.update_one(
                    {'id': followed_id},
                    {'$inc': {'stats.followers_count': -1}}
                )
                
                return True
        except Exception as e:
            print(f"Erreur Neo4j (unfollow_user): {e}")
            return False
    
    def like_post(self, user_id: str, post_id: str) -> bool:
        if not self.neo4j_driver:
            return False
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (p:Post {id: $post_id})
                    RETURN EXISTS((u)-[:LIKES]->(p)) AS liked
                    """,
                    user_id=user_id,
                    post_id=post_id
                )
                
                record = result.single()
                if record and record['liked']:
                    return False
                
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (p:Post {id: $post_id})
                    CREATE (u)-[:LIKES {created_at: $created_at}]->(p)
                    """,
                    user_id=user_id,
                    post_id=post_id,
                    created_at=datetime.now().isoformat()
                )
                
                self.posts_collection.update_one(
                    {'id': post_id},
                    {'$inc': {'stats.likes_count': 1}}
                )
                
                return True
        except Exception as e:
            print(f" Erreur Neo4j (like_post): {e}")
            return False
    
    def unlike_post(self, user_id: str, post_id: str) -> bool:
        if not self.neo4j_driver:
            return False
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (p:Post {id: $post_id})
                    MATCH (u)-[r:LIKES]->(p)
                    RETURN r IS NOT NULL AS liked
                    """,
                    user_id=user_id,
                    post_id=post_id
                )
                
                record = result.single()
                if not record or not record['liked']:
                    return False
                
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MATCH (p:Post {id: $post_id})
                    MATCH (u)-[r:LIKES]->(p)
                    DELETE r
                    """,
                    user_id=user_id,
                    post_id=post_id
                )
                
                self.posts_collection.update_one(
                    {'id': post_id},
                    {'$inc': {'stats.likes_count': -1}}
                )
                
                return True
        except Exception as e:
            print(f" Erreur Neo4j (unlike_post): {e}")
            return False
    
    def get_mutual_friends(self, user1_id: str, user2_id: str) -> List[Dict[str, Any]]:
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (u1:User {id: $user1_id})
                    MATCH (u2:User {id: $user2_id})
                    MATCH (u1)-[:FOLLOWS]->(common:User)<-[:FOLLOWS]-(u2)
                    RETURN common.id AS user_id
                    """,
                    user1_id=user1_id,
                    user2_id=user2_id
                )
                
                mutual_ids = [record['user_id'] for record in result]
                
                return list(self.users_collection.find(
                    {'id': {'$in': mutual_ids}}
                ))
        except Exception as e:
            print(f" Erreur Neo4j (get_mutual_friends): {e}")
            return []
    
    def get_followers(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (follower:User)-[:FOLLOWS]->(u:User {id: $user_id})
                    RETURN follower.id AS user_id
                    """,
                    user_id=user_id
                )
                
                follower_ids = [record['user_id'] for record in result]
                
                return list(self.users_collection.find(
                    {'id': {'$in': follower_ids}}
                ))
        except Exception as e:
            print(f"Erreur Neo4j (get_followers): {e}")
            return []
    
    def get_following(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(
                    """
                    MATCH (u:User {id: $user_id})-[:FOLLOWS]->(followed:User)
                    RETURN followed.id AS user_id
                    """,
                    user_id=user_id
                )
                
                following_ids = [record['user_id'] for record in result]
                
                return list(self.users_collection.find(
                    {'id': {'$in': following_ids}}
                ))
        except Exception as e:
            print(f"Erreur Neo4j (get_following): {e}")
            return []

def main():
    print(" Initialisation du réseau social...\n")
    
    db = ReseauSocialDB()
    
    try:
        print("Nettoyage des données existantes...")
        db.users_collection.delete_many({})
        db.posts_collection.delete_many({})
        if db.neo4j_driver:
            try:
                with db.neo4j_driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
                print("Neo4j nettoyé")
            except:
                pass
        print("Données nettoyées\n")
        
        
        print(" Création des utilisateurs...")
        alice = db.create_user(
            username="alice",
            email="alice@example.com",
            force=True
        )
        bob = db.create_user(
            username="bob",
            email="bob@example.com",
            force=True
        )
        charlie = db.create_user(
            username="charlie",
            email="charlie@example.com",
            force=True
        )
        
        print(f"Utilisateurs créés: {alice['username']} (ID: {alice['id'][:20]}...), {bob['username']}, {charlie['username']}")
        
        # 2. Créer des relations
        print("\nCréation des relations...")
        db.follow_user(alice['id'], bob['id'])
        db.follow_user(alice['id'], charlie['id'])
        db.follow_user(bob['id'], alice['id'])
        db.follow_user(charlie['id'], alice['id'])
        print(" Relations de suivi créées")
        
        # 3. Créer des posts
        print("\n Création des posts...")
        post1 = db.create_post(alice['id'], "Hello world! Bienvenue sur mon réseau social 🎉")
        post2 = db.create_post(bob['id'], "Aujourd'hui je construis une nouvelle application!")
        post3 = db.create_post(charlie['id'], "Quelqu'un a un bon livre à recommander?")
        post4 = db.create_post(alice['id'], "J'adore Neo4j pour les réseaux sociaux!")
        print(f" Posts créés")
        
        # 4. Ajouter des likes
        print("\n Ajout des likes...")
        db.like_post(bob['id'], post1['id'])
        db.like_post(charlie['id'], post1['id'])
        db.like_post(alice['id'], post2['id'])
        db.like_post(bob['id'], post3['id'])
        db.like_post(alice['id'], post3['id'])
        print("Likes ajoutés")
        
        # 5. Afficher les statistiques
        print("\nStatistiques:")
        alice_stats = db.get_user(alice['id'])
        print(f"  Alice:")
        print(f"    - Followers: {alice_stats['stats']['followers_count']}")
        print(f"    - Following: {alice_stats['stats']['following_count']}")
        print(f"    - Posts: {alice_stats['stats']['posts_count']}")
        
        # 6. Afficher les followers
        followers = db.get_followers(alice['id'])
        print(f"\n👥 Followers d'Alice ({len(followers)}):")
        for follower in followers:
            print(f"  - {follower['username']}")
        
        # 7. Afficher les posts du feed
        print(f"\n📱 Posts d'Alice:")
        posts = db.get_user_posts(alice['id'])
        for post in posts:
            print(f"  - {post['content'][:50]}... ({post['stats']['likes_count']})")
        
        print("\nInitialisation terminée avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        print("\nConnexions fermées")

if __name__ == "__main__":
    main()