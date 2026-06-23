# src/recommendation/test.py
from src.recommendation.graph_queries import get_all_user_ids
from src.recommendation.proximity import proximity_score

ids = get_all_user_ids()
print(f"{len(ids)} utilisateurs trouvés\n")

# Teste plusieurs paires différentes pour valider sur des cas variés
nb_paires = min(5, len(ids) - 1)

for i in range(nb_paires):
    user_a, user_b = ids[i], ids[i + 1]
    result = proximity_score(user_a, user_b)
    print(f"--- Paire {i+1} ---")
    print(f"A: {user_a}")
    print(f"B: {user_b}")
    print(f"  Common neighbors  : {result['common_neighbors']}")
    print(f"  Jaccard (follows) : {result['jaccard']}")
    print(f"  Adamic-Adar       : {result['adamic_adar']}")
    print(f"  Jaccard (interets): {result['interests_similarity']}")
    print(f"  Score combiné     : {result['combined_score']}")
    print()