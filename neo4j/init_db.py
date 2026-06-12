"""
Initialisation Neo4j LinkUpDS (Neo4j 5+ compatible)
"""

import logging
import sys
from neo4j import GraphDatabase, exceptions

# ---------------- CONFIG LOGS ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("neo4j-init")

# ---------------- CONFIG DB ----------------
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "motdepasse"

# ---------------- CONSTRAINTS (NEO4J 5+) ----------------
CONSTRAINTS = [
    {
        "name": "user_id_unique",
        "query": """
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS
        FOR (u:User)
        REQUIRE u.userId IS UNIQUE
        """
    },
    {
        "name": "post_id_unique",
        "query": """
        CREATE CONSTRAINT post_id_unique IF NOT EXISTS
        FOR (p:Post)
        REQUIRE p.postId IS UNIQUE
        """
    }
]

# ---------------- INDEXES ----------------
INDEXES = [
    {
        "name": "idx_user_email",
        "query": """
        CREATE INDEX idx_user_email IF NOT EXISTS
        FOR (u:User)
        ON (u.email)
        """
    },
    {
        "name": "idx_user_name",
        "query": """
        CREATE INDEX idx_user_name IF NOT EXISTS
        FOR (u:User)
        ON (u.name)
        """
    },
    {
        "name": "idx_post_timestamp",
        "query": """
        CREATE INDEX idx_post_timestamp IF NOT EXISTS
        FOR (p:Post)
        ON (p.timestamp)
        """
    },
    {
        "name": "idx_post_sentiment",
        "query": """
        CREATE INDEX idx_post_sentiment IF NOT EXISTS
        FOR (p:Post)
        ON (p.sentiment)
        """
    }
]

# ---------------- DEFAULT DATA ----------------
DEFAULT_NODES = [
    {
        "label": "User",
        "key": "userId",
        "props": {
            "userId": "admin_system",
            "name": "Admin System",
            "email": "admin@linkupds.local",
            "role": "admin",
            "password": "admin123"
        }
    },
    {
        "label": "Category",
        "key": "categoryId",
        "props": {
            "categoryId": "cat_general",
            "name": "General",
            "description": "Discussions générales"
        }
    },
    {
        "label": "Category",
        "key": "categoryId",
        "props": {
            "categoryId": "cat_tech",
            "name": "Technologie",
            "description": "Programmation et tech"
        }
    },
    {
        "label": "Category",
        "key": "categoryId",
        "props": {
            "categoryId": "cat_social",
            "name": "Social",
            "description": "Discussions sociales"
        }
    }
]


# ================= CLASS =================
class Neo4jInitializer:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    # -------- CONNECTION --------
    def connect(self):
        try:
            self.driver.verify_connectivity()
            logger.info(f"Connexion réussie → {URI}")
            return True
        except exceptions.ServiceUnavailable:
            logger.error("Neo4j indisponible (Docker ?)")
            return False
        except exceptions.AuthError:
            logger.error("Erreur authentification Neo4j")
            return False

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Connexion fermée")

    # -------- EXEC QUERY SAFE --------
    def run(self, query, params=None, label=""):
        try:
            with self.driver.session() as session:
                session.run(query, params or {})
                if label:
                    logger.info(f"✓ {label}")
                return True
        except Exception as e:
            logger.error(f"✗ {label or query[:40]}")
            logger.error(str(e))
            return False

    # -------- CONSTRAINTS --------
    def create_constraints(self):
        logger.info("Création contraintes...")
        ok = 0

        for c in CONSTRAINTS:
            if self.run(c["query"], label=c["name"]):
                ok += 1

        logger.info(f"Contraintes : {ok}/{len(CONSTRAINTS)}")
        return ok

    # -------- INDEX --------
    def create_indexes(self):
        logger.info("Création index...")
        ok = 0

        for i in INDEXES:
            if self.run(i["query"], label=i["name"]):
                ok += 1

        logger.info(f"Index : {ok}/{len(INDEXES)}")
        return ok

    # -------- NODES --------
    def create_nodes(self):
        logger.info("Création des noeuds...")

        for node in DEFAULT_NODES:
            label = node["label"]
            key = node["key"]

            query = f"""
            MERGE (n:{label} {{{key}: $value}})
            SET n += $props, n.createdAt = datetime()
            """

            params = {
                "value": node["props"][key],
                "props": node["props"]
            }

            self.run(query, params, f"{label}:{params['value']}")

    # -------- VERIFY (NEO4J 5+) --------
    def verify(self):
        logger.info("Vérification...")

        checks = {
            "constraints": "SHOW CONSTRAINTS",
            "indexes": "SHOW INDEXES",
            "nodes": "MATCH (n) RETURN count(n) AS count"
        }

        results = {}

        for name, q in checks.items():
            try:
                with self.driver.session() as session:
                    res = session.run(q)

                    if name == "nodes":
                        value = res.single()["count"]
                    else:
                        value = len(list(res))

                    results[name] = value
                    logger.info(f"{name}: {value}")

            except Exception as e:
                logger.error(f"Erreur {name}: {e}")
                results[name] = 0

        return results

    # -------- INIT FULL --------
    def initialize(self):
        logger.info("=" * 50)
        logger.info("INITIALISATION NEO4J LINKUPDS")
        logger.info("=" * 50)

        self.create_constraints()
        self.create_indexes()
        self.create_nodes()

        results = self.verify()

        logger.info("=" * 50)
        logger.info("INITIALISATION TERMINÉE")
        logger.info(results)
        logger.info("=" * 50)


# ================= MAIN =================
def main():
    neo = Neo4jInitializer(URI, USER, PASSWORD)

    if not neo.connect():
        return 1

    try:
        neo.initialize()
    finally:
        neo.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())