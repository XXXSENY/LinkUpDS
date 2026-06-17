"""
Initialisation des bases de donnees LinkUpDS (Neo4j + MongoDB).

Neo4j  : contraintes, index, noeuds par defaut (graphe social).
MongoDB: collections users et posts (stockage documentaire).

Execution : python scripts/init_db.py
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions
from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "mini_socialnetwork")

if not PASSWORD:
    raise SystemExit("NEO4J_PASSWORD manquant dans .env")

CONSTRAINTS = [
    {
        "name": "constraint_user_id",
        "query": (
            "CREATE CONSTRAINT constraint_user_id IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.userId IS UNIQUE"
        ),
    },
    {
        "name": "constraint_post_id",
        "query": (
            "CREATE CONSTRAINT constraint_post_id IF NOT EXISTS "
            "FOR (p:Post) REQUIRE p.postId IS UNIQUE"
        ),
    },
]

INDEXES = [
    {
        "name": "idx_user_email",
        "query": (
            "CREATE INDEX idx_user_email IF NOT EXISTS "
            "FOR (u:User) ON (u.email)"
        ),
    },
    {
        "name": "idx_user_name",
        "query": (
            "CREATE INDEX idx_user_name IF NOT EXISTS "
            "FOR (u:User) ON (u.name)"
        ),
    },
    {
        "name": "idx_post_timestamp",
        "query": (
            "CREATE INDEX idx_post_timestamp IF NOT EXISTS "
            "FOR (p:Post) ON (p.createdAt)"
        ),
    },
    {
        "name": "idx_post_sentiment",
        "query": (
            "CREATE INDEX idx_post_sentiment IF NOT EXISTS "
            "FOR (p:Post) ON (p.sentiment)"
        ),
    },
]


def _default_nodes():
    from src.utils.security import hash_password

    return [
        {
            "type": "User",
            "properties": {
                "userId": "admin_system",
                "name": "Administrateur Systeme",
                "email": "admin@linkupds.local",
                "username": "admin",
                "password": hash_password("admin123"),
                "bio": "",
                "city": "",
                "interests": [],
                "role": "admin",
            },
        },
        {
            "type": "Category",
            "properties": {
                "categoryId": "cat_general",
                "name": "General",
                "description": "Discussions generales",
            },
        },
        {
            "type": "Category",
            "properties": {
                "categoryId": "cat_tech",
                "name": "Technologie",
                "description": "Sujets techniques et programmation",
            },
        },
        {
            "type": "Category",
            "properties": {
                "categoryId": "cat_social",
                "name": "Social",
                "description": "Discussions sociales et communautaires",
            },
        },
    ]


DEFAULT_NODES = _default_nodes()


class Neo4jInitializer:
    """Initialisation Neo4j."""

    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            logger.info("Connexion reussie a Neo4j sur %s", self.uri)
            return True
        except exceptions.ServiceUnavailable:
            logger.error(
                "Impossible de se connecter a Neo4j sur %s. "
                "Verifiez que Neo4j est demarre.",
                self.uri,
            )
            return False
        except exceptions.AuthError:
            logger.error(
                "Erreur d'authentification Neo4j. "
                "Verifiez NEO4J_USER / NEO4J_PASSWORD."
            )
            return False

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermee")

    def execute_query(self, query, description=""):
        try:
            with self.driver.session() as session:
                session.run(query)
                if description:
                    logger.info("Neo4j OK : %s", description)
                return True
        except Exception as exc:
            logger.error("Neo4j erreur : %s", description or query[:50])
            logger.error("  %s", exc)
            return False

    def create_constraints(self):
        logger.info("Creation des contraintes Neo4j...")
        success = sum(
            1
            for item in CONSTRAINTS
            if self.execute_query(item["query"], item["name"])
        )
        logger.info("Contraintes creees : %s/%s", success, len(CONSTRAINTS))
        return success == len(CONSTRAINTS)

    def create_indexes(self):
        logger.info("Creation des index Neo4j...")
        success = sum(
            1 for item in INDEXES if self.execute_query(item["query"], item["name"])
        )
        logger.info("Index crees : %s/%s", success, len(INDEXES))
        return success == len(INDEXES)

    def create_default_nodes(self):
        logger.info("Creation des noeuds par defaut Neo4j...")
        success_count = 0

        for node in DEFAULT_NODES:
            props = node["properties"].copy()
            if node["type"] == "User":
                match_field = "userId"
            elif node["type"] == "Category":
                match_field = "categoryId"
            else:
                match_field = list(props.keys())[0]

            match_value = props.get(match_field, "")
            set_parts = [
                f"n.{key} = ${key}"
                for key in props
                if key != match_field
            ]
            set_clause = ", ".join(set_parts)

            query = f"""
            MERGE (n:{node["type"]} {{{match_field}: ${match_field}}})
            SET {set_clause}, n.createdAt = datetime()
            RETURN n
            """

            try:
                with self.driver.session() as session:
                    session.run(query, **props)
                    logger.info(
                        "Noeud Neo4j : %s (%s=%s)",
                        node["type"],
                        match_field,
                        match_value,
                    )
                    success_count += 1
            except Exception as exc:
                logger.error("Erreur noeud %s : %s", node["type"], exc)

        logger.info(
            "Noeuds crees : %s/%s", success_count, len(DEFAULT_NODES)
        )
        return success_count == len(DEFAULT_NODES)

    def verify_setup(self):
        logger.info("Verification Neo4j...")
        checks = {
            "contraintes": "SHOW CONSTRAINTS YIELD name RETURN count(*) AS count",
            "indexes": "SHOW INDEXES YIELD name RETURN count(*) AS count",
            "noeuds": "MATCH (n) RETURN count(n) AS count",
        }
        results = {}
        for name, query in checks.items():
            try:
                with self.driver.session() as session:
                    count = session.run(query).single()["count"]
                    results[name] = count
                    logger.info("Neo4j %s : %s element(s)", name, count)
            except Exception as exc:
                logger.error("Erreur verification Neo4j %s : %s", name, exc)
                results[name] = 0
        return results


def init_mongodb():
    """Initialise les collections MongoDB users et posts (sans supprimer de donnees)."""
    logger.info("Initialisation MongoDB...")

    if not MONGODB_URI:
        logger.warning("MONGODB_URI manquant dans .env — MongoDB ignore")
        return False

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[MONGODB_DATABASE]
        users = db["users"]
        posts = db["posts"]

        users.create_index("userId", unique=True)
        users.create_index("email", unique=True)
        posts.create_index("postId", unique=True)

        admin_node = next(
            (n for n in DEFAULT_NODES if n["type"] == "User"),
            None,
        )
        if admin_node:
            props = admin_node["properties"]
            mongo_user = {
                "userId": props["userId"],
                "name": props["name"],
                "email": props["email"],
                "username": props["username"],
                "password": props["password"],
                "bio": props.get("bio", ""),
                "city": props.get("city", ""),
                "interests": props.get("interests", []),
            }
            users.update_one(
                {"userId": props["userId"]},
                {"$set": mongo_user},
                upsert=True,
            )

        users_count = users.count_documents({})
        posts_count = posts.count_documents({})
        logger.info(
            "MongoDB OK — base %s, users=%s docs, posts=%s docs",
            MONGODB_DATABASE,
            users_count,
            posts_count,
        )
        client.close()
        return True
    except Exception as exc:
        logger.error("Erreur initialisation MongoDB : %s", exc)
        return False


def main():
    logger.info("=" * 50)
    logger.info("Initialisation LinkUpDS — Neo4j + MongoDB")
    logger.info("=" * 50)

    initializer = Neo4jInitializer(URI, USER, PASSWORD)
    if not initializer.connect():
        return 1

    constraints_ok = initializer.create_constraints()
    indexes_ok = initializer.create_indexes()
    nodes_ok = initializer.create_default_nodes()
    neo4j_results = initializer.verify_setup()
    initializer.close()

    mongo_ok = init_mongodb()

    logger.info("=" * 50)
    if constraints_ok and indexes_ok:
        logger.info("Neo4j : INITIALISATION REUSSIE")
    else:
        logger.warning("Neo4j : INITIALISATION PARTIELLE")

    if mongo_ok:
        logger.info("MongoDB : INITIALISATION REUSSIE")
    else:
        logger.warning("MongoDB : INITIALISATION IGNOREE OU PARTIELLE")

    logger.info("Statistiques Neo4j : %s", neo4j_results)
    logger.info("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
