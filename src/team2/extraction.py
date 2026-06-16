from src.db_utils import LinkUpDB
import networkx as nx


class GraphExtractor:

    def __init__(self):
        self.db = LinkUpDB()
        self.G = nx.DiGraph()

    # 1. CONNEXION + EXTRACTION
    def load_graph(self):

        query = """
        MATCH (a:User)-[:FOLLOWS]->(b:User)
        RETURN a.userId AS src, b.userId AS dst
        """

        with self.db.driver.session() as session:
            result = session.run(query)

            for r in result:
                self.G.add_edge(r["src"], r["dst"])

        return self.G

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
    G = extractor.load_graph()
    extractor.check_quality()