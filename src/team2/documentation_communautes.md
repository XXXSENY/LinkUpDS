# Équipe 2 — Détection des communautés (membre 5)

## Objectif

Le module `src.team2.community_detection` détecte les groupes d'utilisateurs
du réseau `FOLLOWS` avec l'algorithme Louvain. Comme Louvain travaille sur un
graphe non orienté, une relation est considérée comme un lien social dès que
l'un des deux utilisateurs suit l'autre. Les utilisateurs isolés sont
conservés et forment chacun leur propre communauté.

## Méthode

1. Le graphe `NetworkX` est chargé depuis Neo4j avec le module d'extraction.
2. Les boucles sur soi-même sont ignorées pour éviter de fausser Louvain.
3. Louvain est lancé avec une graine fixe (`seed=42`) pour rendre les résultats
   reproductibles.
4. La modularité mesure la séparation des groupes. Une valeur élevée signifie
   que les liens sont davantage concentrés à l'intérieur des communautés.
5. Chaque communauté est caractérisée par sa taille, sa part du réseau, son
   nombre de liens internes et externes et sa densité interne.

## Exécution

Depuis la racine du projet :

```bash
pip install -r requirements.txt
python scripts/data_generator.py
python -m src.team2.community_detection
```

Neo4j doit être lancé et les variables `NEO4J_URI`, `NEO4J_USER` et
`NEO4J_PASSWORD` doivent être définies dans le fichier `.env` local.

## Livrables générés

Le dossier `outputs/` reçoit automatiquement :

| Fichier | Contenu |
|---|---|
| `community_members.csv` | Une ligne par utilisateur avec son identifiant de communauté et la taille du groupe |
| `community_summary.csv` | Tableau de caractérisation des communautés |
| `community_graph.png` | Graphe coloré par communauté |
| `community_report.md` | Rapport d'interprétation automatique avec modularité et communauté principale |

## Réutilisation dans Streamlit

Le membre 6 peut calculer les données de l'onglet Communautés sans relire les
CSV :

```python
from src.team2.community_detection import (
    build_community_rows,
    detect_communities,
)

analysis = detect_communities(graph)
community_table = build_community_rows(graph, analysis)

# Indicateurs disponibles
community_count = analysis.community_count
modularity = analysis.modularity
partition = analysis.partition
```

`partition` associe chaque `user_id` à un `community_id`. Il peut donc aussi
être utilisé directement pour colorer les nœuds du graphe interactif.

## Tests

Les tests n'ont pas besoin de Neo4j et utilisent un petit graphe déterministe :

```bash
python -m pytest tests/test_community_detection.py -q
```
