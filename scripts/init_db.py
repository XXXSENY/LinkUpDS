"""
Script d'initialisation de la base de données Neo4j pour LinkUpDS

Ce script crée :
- Les contraintes d'unicité sur userId et postId
- Les index pour accélérer les requêtes
- Les noeuds de base (admin, catégories)

Exécution : python scripts/init_db.py
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration de connexion
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not PASSWORD:
    raise SystemExit("NEO4J_PASSWORD manquant dans .env")

# Liste des contraintes à créer
CONSTRAINTS = [
    {
        "name": "constraint_user_id",
        "query": "CREATE CONSTRAINT constraint_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE"
    },
    {
        "name": "constraint_post_id", 
        "query": "CREATE CONSTRAINT constraint_post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.postId IS UNIQUE"
    }
]

# Liste des index à créer
INDEXES = [
    {
        "name": "idx_user_email",
        "query": "CREATE INDEX idx_user_email IF NOT EXISTS FOR (u:User) ON (u.email)"
    },
    {
        "name": "idx_user_name",
        "query": "CREATE INDEX idx_user_name IF NOT EXISTS FOR (u:User) ON (u.name)"
    },
    {
        "name": "idx_post_timestamp",
        "query": "CREATE INDEX idx_post_timestamp IF NOT EXISTS FOR (p:Post) ON (p.createdAt)"
    },
    {
        "name": "idx_post_sentiment",
        "query": "CREATE INDEX idx_post_sentiment IF NOT EXISTS FOR (p:Post) ON (p.sentiment)"
    }
]

# Liste des noeuds par défaut à créer
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
                "role": "admin",
            },
        },
    {
        "type": "Category",
        "properties": {
            "categoryId": "cat_general",
            "name": "General",
            "description": "Discussions generales"
        }
    },
    {
        "type": "Category",
        "properties": {
            "categoryId": "cat_tech",
            "name": "Technologie",
            "description": "Sujets techniques et programmation"
        }
    },
    {
        "type": "Category",
        "properties": {
            "categoryId": "cat_social",
            "name": "Social",
            "description": "Discussions sociales et communautaires"
        }
    },
    ]


DEFAULT_NODES = _default_nodes()


class Neo4jInitializer:
    """Classe pour initialiser et configurer la base Neo4j"""
    
    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def connect(self):
        """Etablit la connexion à Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.driver.verify_connectivity()
            logger.info(f"Connexion reussie à Neo4j sur {self.uri}")
            return True
        except exceptions.ServiceUnavailable:
            logger.error(f"Impossible de se connecter à Neo4j sur {self.uri}. Verifiez que Neo4j est demarre.")
            return False
        except exceptions.AuthError:
            logger.error("Erreur d'authentification. Verifiez le nom d'utilisateur et le mot de passe.")
            return False
        except Exception as e:
            logger.error(f"Erreur de connexion : {str(e)}")
            return False
    
    def close(self):
        """Ferme la connexion"""
        if self.driver:
            self.driver.close()
            logger.info("Connexion fermee")
    
    def execute_query(self, query, description=""):
        """Execute une requête Cypher avec gestion d'erreur"""
        try:
            with self.driver.session() as session:
                session.run(query)
                if description:
                    logger.info(f"✓ {description}")
                return True
        except Exception as e:
            logger.error(f"✗ Erreur : {description or query[:50]}")
            logger.error(f"  {str(e)}")
            return False
    
    def create_constraints(self):
        """Cree toutes les contraintes d'unicite"""
        logger.info("Creation des contraintes...")
        success_count = 0
        for constraint in CONSTRAINTS:
            if self.execute_query(constraint["query"], constraint["name"]):
                success_count += 1
        logger.info(f"Contraintes creees : {success_count}/{len(CONSTRAINTS)}")
        return success_count == len(CONSTRAINTS)
    
    def create_indexes(self):
        """Cree tous les index"""
        logger.info("Creation des index...")
        success_count = 0
        for index in INDEXES:
            if self.execute_query(index["query"], index["name"]):
                success_count += 1
        logger.info(f"Index crees : {success_count}/{len(INDEXES)}")
        return success_count == len(INDEXES)
    
    def create_default_nodes(self):
        """Cree les noeuds par defaut s'ils n'existent pas"""
        logger.info("Creation des noeuds par defaut...")
        success_count = 0
        
        for node in DEFAULT_NODES:
            props = node["properties"].copy()
            
            # Identifier le champ d'identification
            if node["type"] == "User":
                match_field = "userId"
            elif node["type"] == "Category":
                match_field = "categoryId"
            else:
                match_field = list(props.keys())[0]
            
            match_value = props.get(match_field, "")
            
            # Construire la requête
            set_parts = []
            for key, value in props.items():
                if key != match_field:
                    set_parts.append(f"n.{key} = ${key}")
            
            set_clause = ", ".join(set_parts)
            
            query = f"""
            MERGE (n:{node["type"]} {{{match_field}: ${match_field}}})
            SET {set_clause}, n.createdAt = datetime()
            RETURN n
            """
            
            try:
                with self.driver.session() as session:
                    session.run(query, **props)
                    logger.info(f"✓ Noeud : {node['type']} ({match_field}={match_value})")
                    success_count += 1
            except Exception as e:
                logger.error(f"✗ Erreur noeud {node['type']} : {str(e)}")
        
        logger.info(f"Noeuds crees : {success_count}/{len(DEFAULT_NODES)}")
        return success_count == len(DEFAULT_NODES)
    
    def verify_setup(self):
        """Verifie que l'initialisation est correcte"""
        logger.info("Verification de l'installation...")
        
        checks = {
            "contraintes": "CALL db.constraints() YIELD name RETURN count(*) AS count",
            "indexes": "SHOW INDEXES YIELD name RETURN count(*) AS count",
            "noeuds": "MATCH (n) RETURN count(n) AS count"
        }
        
        results = {}
        for name, query in checks.items():
            try:
                with self.driver.session() as session:
                    result = session.run(query)
                    count = result.single()["count"]
                    results[name] = count
                    logger.info(f"✓ {name} : {count} element(s)")
            except Exception as e:
                logger.error(f"✗ Erreur verification {name} : {str(e)}")
                results[name] = 0
        
        return results


def main():
    """Fonction principale"""
    logger.info("=" * 50)
    logger.info("Initialisation de Neo4j pour LinkUpDS")
    logger.info("=" * 50)
    
    initializer = Neo4jInitializer(URI, USER, PASSWORD)
    
    if not initializer.connect():
        logger.error("Impossible de continuer sans connexion Neo4j")
        return 1
    
    print("\n")
    constraints_ok = initializer.create_constraints()
    indexes_ok = initializer.create_indexes()
    nodes_ok = initializer.create_default_nodes()
    
    print("\n")
    results = initializer.verify_setup()
    
    print("\n")
    logger.info("=" * 50)
    if constraints_ok and indexes_ok:
        logger.info("✅ INITIALISATION REUSSIE")
    else:
        logger.warning("⚠️ INITIALISATION PARTIELLE")
    
    logger.info(f"Statistiques : {results}")
    logger.info("=" * 50)
    
    initializer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())