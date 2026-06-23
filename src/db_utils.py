"""
Fonctions d'accès aux données Neo4j pour LinkUpDS.
DAO central utilisé par Streamlit, FastAPI et tests.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from src.config import NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

DEFAULT_URI = NEO4J_URI
DEFAULT_USER = NEO4J_USER
DEFAULT_PASSWORD = NEO4J_PASSWORD
DEFAULT_DATABASE = NEO4J_DATABASE


class LinkUpDB:
    """DAO Neo4j pour LinkUpDS."""

    def __init__(
        self,
        uri: str = DEFAULT_URI,
        user: str = DEFAULT_USER,
        password: str = DEFAULT_PASSWORD,
        database: Optional[str] = DEFAULT_DATABASE,
    ) -> None:
        if not uri:
            raise ValueError(
                "NEO4J_URI non défini. Créez un fichier .env à la racine du projet."
            )
        if not user or not password:
            raise ValueError("NEO4J_USER et NEO4J_PASSWORD requis.")

        self.uri = uri
        self.user = user
        self.database = database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self.driver.close()

    def verify_connection(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except (ServiceUnavailable, AuthError):
            return False

    # =========================
    # SCHEMA
    # =========================
    def init_schema(self) -> None:
        queries = [
            "CREATE CONSTRAINT constraint_user_id IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.userId IS UNIQUE",
            "CREATE CONSTRAINT constraint_post_id IF NOT EXISTS "
            "FOR (p:Post) REQUIRE p.postId IS UNIQUE",
            "CREATE INDEX idx_user_email IF NOT EXISTS "
            "FOR (u:User) ON (u.email)",
            "CREATE INDEX idx_user_name IF NOT EXISTS "
            "FOR (u:User) ON (u.name)",
            "CREATE INDEX idx_post_timestamp IF NOT EXISTS "
            "FOR (p:Post) ON (p.createdAt)",
            "CREATE INDEX idx_post_sentiment IF NOT EXISTS "
            "FOR (p:Post) ON (p.sentiment)",
        ]
        for q in queries:
            self._execute_write(q)

    # =========================
    # USER
    # =========================
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
        if not name:
            raise ValueError("Nom requis")
        if not email:
            raise ValueError("Email requis")

        user_id = user_id or self._new_id("user")
        username = username or email.split("@")[0]
        now = self._now()

        query = """
        MERGE (u:User {userId: $user_id})
        SET u.name = $name,
            u.email = $email,
            u.username = $username,
            u.password = coalesce($password, u.password),
            u.bio = $bio,
            u.city = $city,
            u.interests = $interests,
            u.createdAt = coalesce(u.createdAt, datetime($now)),
            u.updatedAt = datetime($now)
        RETURN u {
            .userId, .name, .email, .username,
            .bio, .city, .interests,
            createdAt: toString(u.createdAt),
            updatedAt: toString(u.updatedAt)
        } AS user
        """
        rows = self._execute_write(
            query,
            user_id=user_id,
            name=name,
            email=email,
            username=username,
            password=password,
            bio=bio,
            city=city,
            interests=interests or [],
            now=now,
        )
        return rows[0]["user"]

    def get_user(self, user_id: str):
        query = """
        MATCH (u:User {userId: $user_id})
        RETURN u {
            .userId,.name,.email,.username,
            .bio,.city,.interests,
            createdAt: toString(u.createdAt),
            updatedAt: toString(u.updatedAt)
        } AS user
        """
        rows = self._execute_read(query, user_id=user_id)
        return rows[0]["user"] if rows else None

    def get_user_by_email(self, email: str):
        """Récupérer un utilisateur par email (SANS password pour sécurité)."""
        query = """
        MATCH (u:User {email: $email})
        RETURN u {
            .userId,.name,.email,.username,
            .bio,.city,.interests,
            createdAt: toString(u.createdAt),
            updatedAt: toString(u.updatedAt)
        } AS user
        """
        rows = self._execute_read(query, email=email)
        return rows[0]["user"] if rows else None

    def get_user_auth_by_email(self, email: str):
        """Récupérer un utilisateur avec password UNIQUEMENT pour authentification."""
        query = """
        MATCH (u:User {email: $email})
        RETURN u {
            .userId,.name,.email,.username,
            .bio,.city,.interests,.password,
            createdAt: toString(u.createdAt),
            updatedAt: toString(u.updatedAt)
        } AS user
        """
        rows = self._execute_read(query, email=email)
        return rows[0]["user"] if rows else None

    def get_all_users(self):
        """Récupère tous les utilisateurs (sans les mots de passe)"""
        query = """
        MATCH (u:User)
        RETURN u {
            .userId, .name, .email, .username,
            .bio, .city, .interests,
            createdAt: toString(u.createdAt)
        } AS user
        ORDER BY u.name
        """
        rows = self._execute_read(query)
        return [row["user"] for row in rows]

    def update_user(
        self,
        user_id: str,
        name: str = None,
        bio: str = None,
        city: str = None,
        interests: Optional[List[str]] = None,
    ):
        query = """
        MATCH (u:User {userId: $user_id})
        SET u.name = coalesce($name, u.name),
            u.bio = coalesce($bio, u.bio),
            u.city = coalesce($city, u.city),
            u.interests = coalesce($interests, u.interests),
            u.updatedAt = datetime($now)
        RETURN u {
            .userId,.name,.email,.username,
            .bio,.city,.interests,
            createdAt: toString(u.createdAt),
            updatedAt: toString(u.updatedAt)
        } AS user
        """
        rows = self._execute_write(
            query,
            user_id=user_id,
            name=name,
            bio=bio,
            city=city,
            interests=interests,
            now=self._now(),
        )
        return rows[0]["user"] if rows else None

    def delete_user(self, user_id: str) -> bool:
        query = """
        MATCH (u:User {userId: $user_id})
        DETACH DELETE u
        RETURN true
        """
        rows = self._execute_write(query, user_id=user_id)
        return bool(rows)

    # =========================
    # POST
    # =========================
    def create_post(
        self,
        user_id: str,
        content: str,
        post_id: Optional[str] = None,
        topic: str = "general",
        sentiment: str = "neutral",
        sentiment_score: float = 0.0,
    ):
        if not user_id or not content:
            raise ValueError("user_id et content requis")

        post_id = post_id or self._new_id("post")
        now = self._now()

        query = """
        MATCH (u:User {userId: $user_id})
        MERGE (p:Post {postId: $post_id})
        SET p.content = $content,
            p.topic = $topic,
            p.sentiment = $sentiment,
            p.sentimentScore = $sentiment_score,
            p.createdAt = coalesce(p.createdAt, datetime($now)),
            p.updatedAt = datetime($now)
        MERGE (u)-[:POSTED]->(p)
        RETURN p {
            .postId,.content,.topic,.sentiment,.sentimentScore,
            createdAt: toString(p.createdAt),
            updatedAt: toString(p.updatedAt)
        } AS post
        """
        rows = self._execute_write(
            query,
            user_id=user_id,
            post_id=post_id,
            content=content,
            topic=topic,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            now=now,
        )
        if not rows:
            raise ValueError("Utilisateur introuvable")
        return rows[0]["post"]

    def get_post(self, post_id: str):
        query = """
        MATCH (u:User)-[:POSTED]->(p:Post {postId: $post_id})
        OPTIONAL MATCH (p)<-[:LIKES]-(:User)
        WITH p, u, count(*) AS likeCount
        RETURN p {
            .postId,.content,.topic,.sentiment,.sentimentScore,
            createdAt: toString(p.createdAt),
            updatedAt: toString(p.updatedAt),
            likeCount: likeCount,
            author: u {.userId,.name,.username,.email}
        } AS post
        """
        rows = self._execute_read(query, post_id=post_id)
        return rows[0]["post"] if rows else None

    def delete_post(self, post_id: str) -> bool:
        query = """
        MATCH (p:Post {postId: $post_id})
        DETACH DELETE p
        RETURN true
        """
        rows = self._execute_write(query, post_id=post_id)
        return bool(rows)

    def get_posts_by_user(self, user_id: str, limit: int = 20):
        query = """
        MATCH (u:User {userId: $user_id})-[:POSTED]->(p:Post)
        OPTIONAL MATCH (p)<-[:LIKES]-(:User)
        WITH p, u, count(*) AS likeCount
        ORDER BY p.createdAt DESC
        LIMIT $limit
        RETURN p {
            .postId,.content,.topic,.sentiment,.sentimentScore,
            .detectedTopic,.topicWords,
            createdAt: toString(p.createdAt),
            updatedAt: toString(p.updatedAt),
            likeCount: likeCount,
            author: u {.userId,.name,.username,.email}
        } AS post
        """
        rows = self._execute_read(query, user_id=user_id, limit=limit)
        return [row["post"] for row in rows]

    def get_feed(self, user_id: str, limit: int = 20, offset: int = 0):
        query = """
        MATCH (u:User {userId: $user_id})-[:FOLLOWS]->(followed:User)-[:POSTED]->(p:Post)
        OPTIONAL MATCH (p)<-[:LIKES]-(:User)
        WITH p, followed, count(*) AS likeCount
        ORDER BY p.createdAt DESC
        SKIP $offset
        LIMIT $limit
        RETURN p {
            .postId,.content,.topic,.sentiment,.sentimentScore,
            .detectedTopic,.topicWords,
            createdAt: toString(p.createdAt),
            updatedAt: toString(p.updatedAt),
            likeCount: likeCount,
            author: followed {.userId,.name,.username,.email}
        } AS post
        """
        rows = self._execute_read(query, user_id=user_id, limit=limit, offset=offset)
        return [row["post"] for row in rows]

    # =========================
    # FOLLOW
    # =========================
    def follow(self, follower_id: str, followed_id: str):
        if follower_id == followed_id:
            raise ValueError("Auto-follow interdit")
        query = """
        MATCH (a:User {userId: $follower_id})
        MATCH (b:User {userId: $followed_id})
        MERGE (a)-[f:FOLLOWS]->(b)
        SET f.createdAt = coalesce(f.createdAt, datetime($now))
        RETURN f
        """
        rows = self._execute_write(
            query,
            follower_id=follower_id,
            followed_id=followed_id,
            now=self._now(),
        )
        return bool(rows)

    def unfollow(self, follower_id: str, followed_id: str) -> bool:
        query = """
        MATCH (a:User {userId: $follower_id})-[f:FOLLOWS]->(b:User {userId: $followed_id})
        DELETE f
        RETURN true
        """
        rows = self._execute_write(
            query, follower_id=follower_id, followed_id=followed_id
        )
        return bool(rows)

    def get_followers(self, user_id: str):
        query = """
        MATCH (follower:User)-[:FOLLOWS]->(u:User {userId: $user_id})
        RETURN follower {
            .userId, .name, .username, .email
        } AS follower
        """
        rows = self._execute_read(query, user_id=user_id)
        return [row["follower"] for row in rows]

    def get_following(self, user_id: str):
        query = """
        MATCH (u:User {userId: $user_id})-[:FOLLOWS]->(followed:User)
        RETURN followed {
            .userId, .name, .username, .email
        } AS followed
        """
        rows = self._execute_read(query, user_id=user_id)
        return [row["followed"] for row in rows]

    # =========================
    # LIKE
    # =========================
    def like_post(self, user_id: str, post_id: str):
        query = """
        MATCH (u:User {userId: $user_id})
        MATCH (p:Post {postId: $post_id})
        MERGE (u)-[l:LIKES]->(p)
        SET l.createdAt = coalesce(l.createdAt, datetime($now))
        RETURN l
        """
        rows = self._execute_write(
            query, user_id=user_id, post_id=post_id, now=self._now()
        )
        return bool(rows)

    def unlike_post(self, user_id: str, post_id: str) -> bool:
        query = """
        MATCH (u:User {userId: $user_id})-[l:LIKES]->(p:Post {postId: $post_id})
        DELETE l
        RETURN true
        """
        rows = self._execute_write(query, user_id=user_id, post_id=post_id)
        return bool(rows)

    def get_likes_count(self, post_id: str) -> int:
        query = """
        MATCH (p:Post {postId: $post_id})<-[:LIKES]-(:User)
        RETURN count(*) AS likeCount
        """
        rows = self._execute_read(query, post_id=post_id)
        return rows[0]["likeCount"] if rows else 0

    # =========================
    # UTILS
    # =========================
    def _session(self):
        return (
            self.driver.session(database=self.database)
            if self.database
            else self.driver.session()
        )

    def _execute_read(self, query: str, **params):
        def work(tx):
            return [r.data() for r in tx.run(query, **params)]

        with self._session() as s:
            return (
                s.execute_read(work)
                if hasattr(s, "execute_read")
                else s.read_transaction(work)
            )

    def _execute_write(self, query: str, **params):
        def work(tx):
            return [r.data() for r in tx.run(query, **params)]

        with self._session() as s:
            return (
                s.execute_write(work)
                if hasattr(s, "execute_write")
                else s.write_transaction(work)
            )

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _new_id(prefix: str):
        return f"{prefix}_{uuid4().hex}"
