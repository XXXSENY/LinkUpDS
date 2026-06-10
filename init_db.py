from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "password123"  # À changer selon ton installation

def init_database():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        # Supprimer tout (optionnel, pour repartir de zéro)
        session.run("MATCH (n) DETACH DELETE n")
        
        # Créer les contraintes d'unicité
        session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE")
        session.run("CREATE CONSTRAINT post_id IF NOT EXISTS FOR (p:Post) REQUIRE p.postId IS UNIQUE")
        
        # Créer des index pour les performances
        session.run("CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)")
        session.run("CREATE INDEX post_timestamp IF NOT EXISTS FOR (p:Post) ON (p.timestamp)")
        
        print("Base de données initialisée avec succès")
    
    driver.close()

if __name__ == "__main__":
    init_database()
