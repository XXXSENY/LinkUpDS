# LinkUpDS

## 🌐 GUIDE COMPLET – LinkUpDS

## Réseau Social Intelligent (Neo4j + Streamlit + API FastAPI)

Bienvenue dans le guide complet du projet LinkUpDS. Ce notebook contient :

- La structure détaillée du projet
- Le rôle exact de chaque fichier
- Ce que chaque équipe (1, 2, 3) doit faire
- La procédure pas à pas pour tout lancer
- Des exemples de code pour l’analyse de graphe (équipe 2) et le NLP (équipe 3)

---

## 1. Arborescence du projet

```text
LinkUpDS/
├── .env                          # Variables d’environnement (Neo4j, JWT)
├── requirements.txt              # Dépendances Python
├── README.md
├── GUIDE_COMPLET.ipynb           # Ce notebook
├── app.py                        # Interface Streamlit (Équipe 1)
├── api.py                        # API REST (Équipe 1)
├── scripts/
│   ├── init_db.py                # Initialisation Neo4j (Adjetou)
│   └── data_generator.py         # Données fictives (Moussa)
├── src/
│   ├── db_utils.py               # DAO principal (Khadija)
│   ├── config.py                 # Lecture .env
│   ├── exceptions.py
│   ├── utils/
│   │   └── security.py           # JWT + bcrypt (Hadjara)
│   ├── routers/                  # Endpoints API (Hadjara)
│   ├── models/                   # Pydantic (Hadjara)
│   └── dependencies/             # get_current_user (Hadjara)
└── docs/
```

## 2. Rôle détaillé des fichiers clés

| Fichier                     | Équipe           | Rôle                                                                 |
| --------------------------- | ---------------- | -------------------------------------------------------------------- |
| `app.py`                    | 1 (Tabara / toi) | Interface Streamlit (feed, posts, likes, follow, profil)             |
| `api.py`                    | 1 (Hadjara)      | Point d’entrée de l’API REST                                         |
| `scripts/init_db.py`        | 1 (Adjetou)      | Crée les contraintes, index et noeuds par défaut                     |
| `scripts/data_generator.py` | 1 (Moussa)       | Génère faux utilisateurs, posts, likes, follows                      |
| `src/db_utils.py`           | 1 (Khadija)      | Toutes les fonctions d’accès à Neo4j                                 |
| `src/config.py`             | 1                | Charge le fichier `.env`                                             |
| `src/utils/security.py`     | 1 (Hadjara)      | Hash bcrypt + JWT                                                    |
| `src/routers/*.py`          | 1 (Hadjara)      | Endpoints `/auth`, `/users`, `/posts`, `/follows`, `/likes`, `/feed` |
| `src/models/*.py`           | 1 (Hadjara)      | Validation des données (Pydantic)                                    |

---

## 3. Ce que chaque équipe doit utiliser

### 🔹 Équipe 1 (vous – infrastructure & backend)

- **Fichiers concernés** : tous ceux listés ci-dessus.
- **Objectif** : faire tourner le projet, générer les données, maintenir l’API et l’interface.
- **Commandes de base** :
  - Lancer Neo4j : `docker start neo4j`
  - Activer l’environnement : `source venv/Scripts/activate`
  - Interface : `streamlit run app.py`
  - API : `uvicorn api:app --reload`

### 🔹 Équipe 2 (Graph Mining – analyse du réseau)

- **Données disponibles** : utilisateurs et relations `FOLLOWS` dans Neo4j.
- **Comment accéder aux données** :
  ```python
  from src.db_utils import LinkUpDB
  db = LinkUpDB()
  # Récupérer tous les utilisateurs
  users = db.get_all_users()
  # Construire le graphe (exemple avec NetworkX)
  import networkx as nx
  G = nx.DiGraph()
  with db.driver.session() as session:
      result = session.run("MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN a.userId AS src, b.userId AS dst")
      for r in result:
          G.add_edge(r["src"], r["dst"])
  ```
- **Travail attendu** :
  - Densité, distance moyenne, distribution des degrés.
  - PageRank (influenceurs).
  - Détection de communautés (Louvain).
  - Visualisation interactive (Plotly, pyvis).
- **Intégration dans Streamlit** : vous pouvez créer une page dédiée dans `app.py`.

### 🔹 Équipe 3 (NLP & Recommandation)

- **Données disponibles** : posts (champ `content`), relations `FOLLOWS`, likes.
- **Analyse de sentiment** :
  ```python
  from transformers import pipeline
  sentiment = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
  post = db.get_post("post_xxx")
  result = sentiment(post["content"][:512])[0]
  # result['label'] = '1 star' ... '5 stars'
  ```
- **Recommandation d’amis (link prediction)** :
  - Utilisez le graphe existant (NetworkX ou requêtes Cypher).
  - Implémentez Adamic/Adar, Jaccard, etc.
  - Proposez une liste de `user_id` à suivre.
- **Intégration** : vous pouvez exposer vos recommandations via un endpoint `/recommendations/{user_id}` ou directement dans l’interface.

---

## 4. Procédure pas à pas (pour toute l’équipe)

```bash
# 1. Lancer Docker Desktop et Neo4j
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/motdepasse123 neo4j:latest

# 2. Aller dans le projet et activer l’environnement
cd ~/Documents/LinkUpDS
python -m venv venv
source venv/Scripts/activate        # Windows
# source venv/bin/activate          # Mac/Linux

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer le fichier .env (cf. section 5)

# 5. Initialiser Neo4j
python scripts/init_db.py

# 6. Générer des données fictives
python scripts/data_generator.py

# 7. Lancer l’interface Streamlit (dans un terminal)
streamlit run app.py

# 8. Lancer l’API (dans un autre terminal)
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

---

## 5. Contenu du fichier `.env` (obligatoire)

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=motdepasse123
NEO4J_DATABASE=neo4j

SECRET_KEY=ma_super_cle_secrete_linkupds
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

LOG_LEVEL=INFO
```

---

## 6. Exemple complet pour l’équipe 2 (PageRank + communautés)

```python
from src.db_utils import LinkUpDB
import networkx as nx
import community as community_louvain
import plotly.graph_objects as go

db = LinkUpDB()

# Construire le graphe orienté FOLLOWS
with db.driver.session() as session:
    result = session.run("MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN a.userId AS src, b.userId AS dst")
    edges = [(r["src"], r["dst"]) for r in result]

G = nx.DiGraph()
G.add_edges_from(edges)

# PageRank
pagerank = nx.pagerank(G)
top_influencers = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
print("Top influenceurs :", top_influencers)

# Communautés (Louvain sur graphe non orienté)
G_und = G.to_undirected()
partition = community_louvain.best_partition(G_und)
print("Nombre de communautés :", len(set(partition.values())))

# Visualisation simplifiée avec Plotly (extraite de NetworkX)
pos = nx.spring_layout(G_und, k=0.15, iterations=20)
edge_trace = go.Scatter(x=[], y=[], mode='lines', line=dict(width=0.5, color='#888'))
for edge in G_und.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_trace['x'] += (x0, x1, None)
    edge_trace['y'] += (y0, y1, None)

node_x, node_y = zip(*[pos[n] for n in G_und.nodes()])
node_trace = go.Scatter(x=node_x, y=node_y, mode='markers', text=list(G_und.nodes()), marker=dict(size=5))

fig = go.Figure(data=[edge_trace, node_trace])
fig.show()
```

---

## 7. Exemple complet pour l’équipe 3 (Sentiment + recommandation)

```python
from src.db_utils import LinkUpDB
from transformers import pipeline
import networkx as nx

db = LinkUpDB()

# Analyse de sentiment sur tous les posts
sentiment_pipeline = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

with db.driver.session() as session:
    posts = session.run("MATCH (p:Post) RETURN p.postId AS pid, p.content AS content")
    for record in posts:
        pid = record["pid"]
        text = record["content"]
        result = sentiment_pipeline(text[:512])[0]
        stars = int(result["label"].split()[0])
        sentiment = "POSITIVE" if stars >= 4 else ("NEGATIVE" if stars <= 2 else "NEUTRAL")
        session.run("MATCH (p:Post {postId: $pid}) SET p.sentiment = $sentiment, p.sentimentScore = $stars",
                    pid=pid, sentiment=sentiment, stars=stars)

# Recommandation d’amis (Adamic/Adar) – nécessite un graphe NetworkX
with db.driver.session() as session:
    result = session.run("MATCH (a:User)-[:FOLLOWS]->(b:User) RETURN a.userId AS src, b.userId AS dst")
    edges = [(r["src"], r["dst"]) for r in result]

G = nx.DiGraph()
G.add_edges_from(edges)

def recommend_friends(user_id, G, top_n=5):
    if user_id not in G:
        return []
    preds = nx.adamic_adar_index(G, [(user_id, n) for n in G.nodes() if n != user_id and not G.has_edge(user_id, n)])
    sorted_preds = sorted(preds, key=lambda x: x[2], reverse=True)[:top_n]
    return [p[1] for p in sorted_preds]

print(recommend_friends("user_xxx", G))
```

---

## 8. Commandes utiles et dépannage

| Problème                                        | Solution                                                                    |
| ----------------------------------------------- | --------------------------------------------------------------------------- |
| `docker: command not found`                     | Docker Desktop n’est pas lancé ou pas installé                              |
| `NEO4J_PASSWORD manquant`                       | Vérifier le fichier `.env`                                                  |
| `ModuleNotFoundError: No module named 'dotenv'` | `pip install python-dotenv`                                                 |
| `neo4j.exceptions.AuthError`                    | Le mot de passe dans `.env` ne correspond pas à celui de la commande Docker |
| `Address already in use` (port 8000)            | Changer de port : `uvicorn api:app --reload --port 8001`                    |
| Le feed reste vide                              | Avez-vous exécuté `data_generator.py` ? Avez-vous suivi quelqu’un ?         |

---

## 9. Liens utiles

- [Documentation Streamlit](https://docs.streamlit.io/)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Neo4j Python Driver](https://neo4j.com/docs/api/python-driver/current/)
- [NetworkX – Algorithmes de graphe](https://networkx.org/)
- [Hugging Face Transformers – Sentiment Analysis](https://huggingface.co/docs/transformers/en/tasks/sequence_classification)

---

**Ce notebook contient tout ce dont vous avez besoin pour comprendre, lancer et enrichir LinkUpDS.**

Bon courage !
