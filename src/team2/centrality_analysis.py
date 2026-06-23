import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from src.team2.extraction import GraphExtractor

class CentralityAnalyzer:
    def __init__(self, graph):
        self.G = graph
        self.betweenness_scores = {}
        self.closeness_scores = {}

    # =========================
    # CALCUL CENTRALITES
    # =========================
    def compute_centralities(self):
        print("\n=== CALCUL DES CENTRALITES ===")
        if self.G.number_of_nodes() == 0:
            print(" Le graphe est vide. Calcul impossible.")
            return
        self.betweenness_scores = nx.betweenness_centrality(self.G, normalized=True)
        self.closeness_scores = nx.closeness_centrality(self.G)
        print(" Betweenness + Closeness calculés")

    # =========================
    # TOP K
    # =========================
    def get_top_k(self, scores_dict, k=10):
        return sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)[:k]

    # =========================
    # INSIGHTS + ANALYSE STRATEGIQUE
    # =========================
    def display_insights(self):
        print("\n=== TOP ANALYSE RESEAU ===")
        if not self.betweenness_scores or not self.closeness_scores:
            print(" Aucun score disponible. Calculez les centralités d'abord.")
            return

        top_betweenness = self.get_top_k(self.betweenness_scores)
        top_closeness = self.get_top_k(self.closeness_scores)

        print("\n TOP 10 BETWEENNESS (PONTS / INTERMEDIAIRES)")
        for i, (node, score) in enumerate(top_betweenness, 1):
            degree = self.G.degree(node)
            print(f"{i}. User {node} -> score={score:.4f} | degré={degree}")

        print("\n TOP 10 CLOSENESS (PROXIMITE AU RESEAU)")
        for i, (node, score) in enumerate(top_closeness, 1):
            print(f"{i}. User {node} -> {score:.4f}")

    # =========================
    # IDENTIFICATION DES PONTS ENTRE COMMUNAUTES
    # =========================
    def identify_bridges(self):
        print("\n=== IDENTIFICATION DES PONTS ENTRE COMMUNAUTES ===")
        if self.G.number_of_nodes() == 0:
            print("⚠ Le graphe est vide.")
            return ([], [])

        # Convertir en non-dirigé simple pour détecter les ponts structurels
        G_undirected = self.G.to_undirected() if self.G.is_directed() else self.G
        if G_undirected.is_multigraph():
            G_undirected = nx.Graph(G_undirected)

        # Ponts structurels
        bridges = list(nx.bridges(G_undirected))
        print(f"\n Nombre de ponts structurels détectés : {len(bridges)}")
        if bridges:
            print("Exemples de ponts (arêtes critiques) :")
            for u, v in bridges[:5]:
                print(f"  → {u} ↔ {v}")

        # Noeuds d'articulation
        articulation_points = list(nx.articulation_points(G_undirected))
        print(f"\n  Nœuds d'articulation (utilisateurs critiques) : {len(articulation_points)}")
        
        # Croiser avec betweenness
        strategic = sorted(
            [(n, self.betweenness_scores.get(n, 0)) for n in articulation_points],
            key=lambda x: -x[1]
        )[:10]

        print("\n🔑 Top utilisateurs stratégiques (pont + betweenness élevé) :")
        for node, score in strategic:
            degree = self.G.degree(node)
            print(f"  → User {node} | betweenness={score:.4f} | degré={degree}")
            print(f"     ⚡ Sa suppression pourrait fragmenter le réseau.")

        return articulation_points, bridges

    # =========================
    # ANALYSE ECRITE AUTOMATIQUE
    # =========================
    def generate_analysis(self):
        print("\n=== ANALYSE AUTOMATIQUE ===")
        
        # Sécurité : vérifier que les listes ne sont pas vides
        top_b_list = self.get_top_k(self.betweenness_scores, k=1)
        top_c_list = self.get_top_k(self.closeness_scores, k=1)
        
        if not top_b_list or not top_c_list:
            print(" Données insuffisantes pour générer un rapport.")
            return

        top_b = top_b_list[0]
        top_c = top_c_list[0]

        print(f"""
 RAPPORT D'ANALYSE — CENTRALITÉ & FLUX D'INFORMATION

1. BETWEENNESS CENTRALITY
   L'utilisateur {top_b[0]} possède le score Betweenness le plus élevé ({top_b[1]:.4f}).
   Cela signifie qu'il se trouve sur le chemin le plus court entre de nombreuses paires
   d'utilisateurs. Il joue un rôle d'intermédiaire clé dans la circulation de l'information.
   Sa suppression du réseau pourrait fragmenter plusieurs groupes et ralentir
   significativement la diffusion des contenus.

2. CLOSENESS CENTRALITY
   L'utilisateur {top_c[0]} a le score Closeness le plus élevé ({top_c[1]:.4f}).
   Il peut atteindre l'ensemble des autres utilisateurs en un minimum d'étapes.
   C'est le profil idéal pour diffuser une information rapidement à tout le réseau.

3. FLUX D'INFORMATION
   Les utilisateurs à fort Betweenness contrôlent les flux entre communautés.
   Supprimer ou cibler ces nœuds aurait un impact maximal sur la connectivité globale.
        """)

    # =========================
    # VISUALISATION
    # =========================
    def plot_top_nodes(self):
        if self.G.number_of_nodes() == 0:
            print(" Graphe vide, impossible de générer le rendu visuel.")
            return
            
        top_nodes = set([n for n, _ in self.get_top_k(self.betweenness_scores)])
        colors = ["red" if node in top_nodes else "skyblue" for node in self.G.nodes()]

        plt.figure(figsize=(12, 8))
        nx.draw(self.G, node_color=colors, node_size=300, with_labels=False,
                edge_color="gray", alpha=0.8)
        plt.title("Centralité Betweenness\n(rouge = utilisateurs intermédiaires stratégiques)")
        plt.tight_layout()
        os.makedirs("outputs", exist_ok=True)
        plt.savefig("outputs/centralite_graph.png", dpi=150)
        print(" Graphe sauvegardé : outputs/centralite_graph.png")
        plt.show()
        plt.close() 

    # =========================
    # EXPORT CSV
    # =========================
    def export_results(self, output_path="outputs/centrality_scores.csv"):
        if not self.betweenness_scores:
            print(" Aucun résultat à exporter.")
            return
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_betweenness = pd.Series(self.betweenness_scores, name="betweenness")
        df_closeness = pd.Series(self.closeness_scores, name="closeness")
        df = pd.concat([df_betweenness, df_closeness], axis=1)
        df.index.name = "userId"
        df = df.reset_index()
        df = df.sort_values("betweenness", ascending=False)
        df.to_csv(output_path, index=False)
        print(f" CSV exporté : {output_path}")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    extractor = GraphExtractor()
    G = extractor.load_graph()

    analyzer = CentralityAnalyzer(G)
    analyzer.compute_centralities()
    analyzer.display_insights()
    analyzer.identify_bridges()      
    analyzer.generate_analysis()     
    analyzer.plot_top_nodes()
    analyzer.export_results()
