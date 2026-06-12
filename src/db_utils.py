"""
Fonctions d'acces aux donnees Neo4j pour LinkUpDS.

Ce module contient la classe LinkUpDB. Elle regroupe les operations DAO
utilisees par l'interface Streamlit, l'API FastAPI et les tests :
- creer un utilisateur ;
- creer un post ;
- suivre / ne plus suivre un utilisateur ;
- liker / retirer un like ;
- recuperer un fil d'actualite.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable


DEFAULT_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_PASSWORD = os.getenv("NEO4J_PASSWORD", "motdepasse123")
DEFAULT_DATABASE = os.getenv("NEO4J_DATABASE") or None


class LinkUpDB:
    """DAO Neo4j pour les entites principales de LinkUpDS."""

    def __init__(
        self,
        uri: str = DEFAULT_URI,
        user: str = DEFAULT_USER,
        password: str = DEFAULT_PASSWORD,
        database: Optional[str] = DEFAULT_DATABASE,
    ) -> None:
        self.uri = uri
        self.user = user
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        """Ferme proprement la connexion Neo4j."""
        self.driver.close()

    def verify_connection(self) -> bool:
        """Verifie que Neo4j est accessible."""
        try:
            self.driver.verify_connectivity()
            return True
        except (ServiceUnavailable, AuthError):
            return False

    def init_schema(self) -> None:
        """Cree les contraintes/index utiles si le script init_db n'a pas ete lance."""
        queries = [
            "CREATE CONSTRAINT constraint_user_id IF NOT EXISTS "
            "FOR (user:User) REQUIRE user.userId IS UNIQUE",
            "CREATE CONSTRAINT constraint_post_id IF NOT EXISTS "
            "FOR (post:Post) REQUIRE post.postId IS UNIQUE",
            "CREATE INDEX idx_user_email IF NOT EXISTS "
            "FOR (user:User) ON (user.email)",
            "CREATE INDEX idx_post_created_at IF NOT EXISTS "
            "FOR (post:Post) ON (post.createdAt)",
        ]
        for query in queries:
            self._execute_write(query)

    def create_user(
        self,
        user_id: Optional[str] = None,
        name: str = "",
        email: str = "",
        username: Optional[str] = None,
        password: Optional[str] = None,
        bio: str = "",
        city: str = "",
        interests: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Cree ou met a jour un utilisateur."""
        if not name:
            raise ValueError("Le nom de l'utilisateur est obligatoire.")
        if not email:
            raise ValueError("L'email de l'utilisateur est obligatoire.")

        final_user_id = user_id or self._new_id("user")
        final_username = username or email.split("@")[0]

        query = """
        MERGE (user:User {userId: $user_id})
        SET user.name = $name,
            user.email = $email,
            user.username = $username,
            user.password = coalesce($password, user.password),
            user.bio = $bio,
            user.city = $city,
            user.interests = $interests,
            user.createdAt = coalesce(user.createdAt, datetime($created_at)),
            user.updatedAt = datetime($updated_at)
        RETURN user {
            .userId,
            .name,
            .email,
            .username,
            .bio,
            .city,
            .interests,
            createdAt: toString(user.createdAt),
            updatedAt: toString(user.updatedAt)
        } AS user
        """
        rows = self._execute_write(
            query,
            user_id=final_user_id,
            name=name,
            email=email,
            username=final_username,
            password=password,
            bio=bio,
            city=city,
            interests=interests or [],
            created_at=self._now(),
            updated_at=self._now(),
        )
        return rows[0]["user"]

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retourne un utilisateur par son identifiant."""
        query = """
        MATCH (user:User {userId: $user_id})
        RETURN user {
            .userId,
            .name,
            .email,
            .username,
            .bio,
            .city,
            .interests,
            createdAt: toString(user.createdAt),
            updatedAt: toString(user.updatedAt)
        } AS user
        """
        rows = self._execute_read(query, user_id=user_id)
        return rows[0]["user"] if rows else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retourne un utilisateur par son email."""
        query = """
        MATCH (user:User {email: $email})
        RETURN user {
            .userId,
            .name,
            .email,
            .username,
            .bio,
            .city,
            .interests,
            createdAt: toString(user.createdAt),
            updatedAt: toString(user.updatedAt)
        } AS user
        """
        rows = self._execute_read(query, email=email)
        return rows[0]["user"] if rows else None

    def create_post(
        self,
        user_id: str,
        content: str,
        post_id: Optional[str] = None,
        topic: str = "general",
        sentiment: str = "neutral",
        sentiment_score: float = 0.0,
    ) -> Dict[str, Any]:
        """Cree un post et le relie a son auteur."""
        if not user_id:
            raise ValueError("L'identifiant de l'auteur est obligatoire.")
        if not content:
            raise ValueError("Le contenu du post est obligatoire.")

        final_post_id = post_id or self._new_id("post")
        created_at = self._now()
        query = """
        MATCH (author:User {userId: $user_id})
        MERGE (post:Post {postId: $post_id})
        SET post.content = $content,
            post.topic = $topic,
            post.sentiment = $sentiment,
            post.sentimentScore = $sentiment_score,
            post.createdAt = coalesce(post.createdAt, datetime($created_at)),
            post.updatedAt = datetime($created_at)
        MERGE (author)-[posted:POSTED]->(post)
        SET posted.createdAt = coalesce(posted.createdAt, datetime($created_at))
        RETURN post {
            .postId,
            .content,
            .topic,
            .sentiment,
            .sentimentScore,
            createdAt: toString(post.createdAt),
            updatedAt: toString(post.updatedAt),
            author: author {
                .userId,
                .name,
                .username,
                .email
            }
        } AS post
        """
        rows = self._execute_write(
            query,
            user_id=user_id,
            post_id=final_post_id,
            content=content,
            topic=topic,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            created_at=created_at,
        )
        if not rows:
            raise ValueError(f"Utilisateur introuvable : {user_id}")
        return rows[0]["post"]

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Retourne un post avec son auteur et son nombre de likes."""
        query = """
        MATCH (author:User)-[:POSTED]->(post:Post {postId: $post_id})
        OPTIONAL MATCH (post)<-[like:LIKES]-(:User)
        WITH post, author, count(like) AS likeCount
        RETURN post {
            .postId,
            .content,
            .topic,
            .sentiment,
            .sentimentScore,
            createdAt: toString(post.createdAt),
            updatedAt: toString(post.updatedAt),
            likeCount: likeCount,
            author: author {
                .userId,
                .name,
                .username,
                .email
            }
        } AS post
        """
        rows = self._execute_read(query, post_id=post_id)
        return rows[0]["post"] if rows else None

    def follow(self, follower_id: str, followed_id: str) -> bool:
        """Cree une relation FOLLOWS entre deux utilisateurs."""
        if follower_id == followed_id:
            raise ValueError("Un utilisateur ne peut pas se suivre lui-meme.")

        query = """
        MATCH (follower:User {userId: $follower_id})
        MATCH (followed:User {userId: $followed_id})
        MERGE (follower)-[follow:FOLLOWS]->(followed)
        SET follow.createdAt = coalesce(follow.createdAt, datetime($created_at))
        RETURN follower.userId AS followerId, followed.userId AS followedId
        """
        rows = self._execute_write(
            query,
            follower_id=follower_id,
            followed_id=followed_id,
            created_at=self._now(),
        )
        if not rows:
            raise ValueError("Utilisateur follower ou followed introuvable.")
        return True

    def unfollow(self, follower_id: str, followed_id: str) -> bool:
        """Supprime une relation FOLLOWS si elle existe."""
        query = """
        MATCH (:User {userId: $follower_id})-[follow:FOLLOWS]->(:User {userId: $followed_id})
        WITH follow
        DELETE follow
        RETURN 1 AS deleted
        """
        rows = self._execute_write(
            query,
            follower_id=follower_id,
            followed_id=followed_id,
        )
        return bool(rows)

    def like_post(self, user_id: str, post_id: str) -> bool:
        """Cree un like entre un utilisateur et un post."""
        query = """
        MATCH (user:User {userId: $user_id})
        MATCH (post:Post {postId: $post_id})
        MERGE (user)-[like:LIKES]->(post)
        SET like.createdAt = coalesce(like.createdAt, datetime($created_at))
        RETURN user.userId AS userId, post.postId AS postId
        """
        rows = self._execute_write(
            query,
            user_id=user_id,
            post_id=post_id,
            created_at=self._now(),
        )
        if not rows:
            raise ValueError("Utilisateur ou post introuvable.")
        return True

    def unlike_post(self, user_id: str, post_id: str) -> bool:
        """Supprime un like si la relation existe."""
        query = """
        MATCH (:User {userId: $user_id})-[like:LIKES]->(:Post {postId: $post_id})
        WITH like
        DELETE like
        RETURN 1 AS deleted
        """
        rows = self._execute_write(query, user_id=user_id, post_id=post_id)
        return bool(rows)

    def get_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retourne les posts de l'utilisateur et des comptes qu'il suit."""
        query = """
        MATCH (viewer:User {userId: $user_id})
        MATCH (author:User)-[:POSTED]->(post:Post)
        WHERE author = viewer OR EXISTS {
            (viewer)-[:FOLLOWS]->(author)
        }
        OPTIONAL MATCH (post)<-[like:LIKES]-(:User)
        WITH post, author, count(like) AS likeCount
        RETURN post {
            .postId,
            .content,
            .topic,
            .sentiment,
            .sentimentScore,
            createdAt: toString(post.createdAt),
            updatedAt: toString(post.updatedAt),
            likeCount: likeCount,
            author: author {
                .userId,
                .name,
                .username,
                .email
            }
        } AS post
        ORDER BY post.createdAt DESC
        LIMIT $limit
        """
        rows = self._execute_read(query, user_id=user_id, limit=max(1, int(limit)))
        return [row["post"] for row in rows]

    def get_following(self, user_id: str) -> List[Dict[str, Any]]:
        """Liste les utilisateurs suivis par un utilisateur."""
        query = """
        MATCH (:User {userId: $user_id})-[:FOLLOWS]->(followed:User)
        RETURN followed {
            .userId,
            .name,
            .email,
            .username,
            .bio,
            .city
        } AS user
        ORDER BY followed.name
        """
        rows = self._execute_read(query, user_id=user_id)
        return [row["user"] for row in rows]

    def get_followers(self, user_id: str) -> List[Dict[str, Any]]:
        """Liste les utilisateurs qui suivent un utilisateur."""
        query = """
        MATCH (follower:User)-[:FOLLOWS]->(:User {userId: $user_id})
        RETURN follower {
            .userId,
            .name,
            .email,
            .username,
            .bio,
            .city
        } AS user
        ORDER BY follower.name
        """
        rows = self._execute_read(query, user_id=user_id)
        return [row["user"] for row in rows]

    def count_all(self) -> Dict[str, int]:
        """Retourne un resume du contenu principal de la base."""
        query = """
        MATCH (user:User)
        OPTIONAL MATCH (post:Post)
        OPTIONAL MATCH ()-[follow:FOLLOWS]->()
        OPTIONAL MATCH ()-[like:LIKES]->()
        RETURN count(DISTINCT user) AS users,
               count(DISTINCT post) AS posts,
               count(DISTINCT follow) AS follows,
               count(DISTINCT like) AS likes
        """
        rows = self._execute_read(query)
        return rows[0] if rows else {"users": 0, "posts": 0, "follows": 0, "likes": 0}

    def _session(self):
        if self.database:
            return self.driver.session(database=self.database)
        return self.driver.session()

    def _execute_read(self, query: str, **parameters: Any) -> List[Dict[str, Any]]:
        def work(transaction):
            result = transaction.run(query, **parameters)
            return [record.data() for record in result]

        with self._session() as session:
            if hasattr(session, "execute_read"):
                return session.execute_read(work)
            return session.read_transaction(work)

    def _execute_write(self, query: str, **parameters: Any) -> List[Dict[str, Any]]:
        def work(transaction):
            result = transaction.run(query, **parameters)
            return [record.data() for record in result]

        with self._session() as session:
            try:
                if hasattr(session, "execute_write"):
                    return session.execute_write(work)
                return session.write_transaction(work)
            except Neo4jError:
                raise

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"
