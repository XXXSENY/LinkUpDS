import networkx as nx

from src.db_utils import LinkUpDB


class GraphExtractor:

    def __init__(self):
        self.db = LinkUpDB()
        self.G = nx.DiGraph()

    # 1. CONNEXION + EXTRACTION
    def load_graph(self):
        """Charge tous les utilisateurs et les relations FOLLOWS.
        Les utilisateurs sont chargés séparément afin de conserver les nœuds
        isolés, qui seraient sinon absents d'une extraction basée uniquement
        sur les relations.
        """
        users_query = """
        MATCH (u:User)
        RETURN u.userId AS user_id
        """
        edges_query = """
        MATCH (a:User)-[:FOLLOWS]->(b:User)
        RETURN DISTINCT a.userId AS src, b.userId AS dst
        """

        self.G.clear()
        with self.db._session() as session:
            self.G.add_nodes_from(
                row["user_id"] for row in session.run(users_query)
            )
            self.G.add_edges_from(
                (row["src"], row["dst"])
                for row in session.run(edges_query)
            )

        return self.G

    def close(self):
        self.db.close()

    # 2. VERIFICATION QUALITE
    def check_quality(self):

        print("\n=== QUALITE DES DONNEES ===")

        print("Nombre de noeuds :", self.G.number_of_nodes())
        print("Nombre de relations :", self.G.number_of_edges())
        
        isolated = list(nx.isolates(self.G))
        print("Utilisateurs isolés :", len(isolated))

        if len(isolated) == 0:
            print("✔ Données propres (aucun utilisateur isolé)")
        else:
            print("⚠ Certains utilisateurs n'ont aucune connexion")

if __name__ == "__main__":
    extractor = GraphExtractor()
    try:
        G = extractor.load_graph()
        extractor.check_quality()

        print("\n=== VERIFICATION NETWORKX ===")
        print("Type :", type(G))
        print("Noeuds :", G.number_of_nodes())
        print("Relations :", G.number_of_edges())
    finally:
        extractor.close()
