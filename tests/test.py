from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "azerty1234"

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print("Connexion réussie !")
    driver.close()
except Exception as e:
    print("Erreur :", e)