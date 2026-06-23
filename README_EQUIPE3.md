# LinkUpDS - Équipe 3 : NLP & Système de Recommandation

## 📋 Vue d'ensemble

Ce document présente le travail réalisé par l'Équipe 3 dans le cadre du projet LinkUpDS, un réseau social intelligent. Notre mission était de rendre le réseau social "intelligent" en analysant les textes et en personnalisant l'expérience utilisateur.

## 🎯 Objectifs de l'Équipe 3

1. **Analyse de Contenu (NLP)**
   - Analyse de sentiment sur les posts (positif/négatif/neutre)
   - Extraction automatique des thèmes de discussion (Topic Modeling)

2. **Moteur de Recommandation**
   - Système de recommandation d'amis (Link Prediction)
   - Algorithme du fil d'actualité (Smart Feed)

---

## 📁 Structure du code

### Module NLP (`src/nlp/`)

#### `sentiment_analysis.py`
Analyse le sentiment des posts en utilisant TextBlob.

**Fonctionnalités:**
- `analyze_sentiment(text)` - Analyse le sentiment d'un texte
- `batch_analyze_sentiment(texts)` - Analyse en lot
- `update_post_sentiment(db, post_id)` - Met à jour le sentiment dans Neo4j
- `batch_update_posts_sentiment(db, limit)` - Met à jour tous les posts sans sentiment

**Résultat:**
- Label: positif, négatif, neutre
- Polarité: score entre -1 et 1
- Subjectivité: score entre 0 et 1
- Confidence: niveau de confiance

#### `topic_modeling.py`
Extrait les thèmes principaux des posts en utilisant LDA (Latent Dirichlet Allocation).

**Fonctionnalités:**
- `extract_topics(texts, n_topics, n_words)` - Extrait les thèmes
- `get_topic_distribution(text, topics_model)` - Distribution de thèmes pour un texte
- `get_dominant_topic(text, topics_model)` - Thème dominant
- `build_topics_model_from_posts(db, limit)` - Construit un modèle depuis les posts

**Méthodes:**
- LDA (Latent Dirichlet Allocation) - méthode avancée
- TF-IDF - méthode simple basée sur les mots fréquents

### Module Recommandation (`src/recommendation/`)

#### `graph_queries.py`
Briques de base pour lire le graphe social Neo4j.

**Fonctions:**
- `get_following_ids(user_id)` - Utilisateurs suivis
- `get_followers_ids(user_id)` - Abonnés
- `get_user_interests(user_id)` - Intérêts de l'utilisateur
- `get_second_degree_candidates(user_id, limit)` - Candidats à distance 2
- `get_all_user_ids()` - Tous les utilisateurs
- `user_exists(user_id)` - Vérifie l'existence

#### `proximity.py`
Calcule les indicateurs de proximité entre utilisateurs.

**Indicateurs:**
1. **Common Neighbors** - Nombre d'amis communs
2. **Jaccard Similarity** - Similarité des réseaux (|A ∩ B| / |A ∪ B|)
3. **Adamic-Adar** - Poids des amis communs (1/log(degré))
4. **Interests Similarity** - Similarité des intérêts (Jaccard sur les intérêts)

#### `pipeline.py`
Pipeline de recommandation combinant tous les indicateurs.

**Fonctionnalités:**
- `get_proximity_scores(user_id, limit, weights)` - Scores de proximité
- `generate_recommendations(user_id, top_n)` - Recommandations d'amis
- `get_recommendations_with_details(user_id, top_n)` - Avec détails d'intérêts

**Pondération par défaut:**
- Common Neighbors: 25%
- Jaccard: 25%
- Adamic-Adar: 25%
- Interest Similarity: 25%

### API Endpoints (`src/routers/recommendations.py`)

#### Recommandations d'amis
```
GET /recommendations/friends/{user_id}?top_n=10&with_details=true
```
Retourne les recommandations d'amis avec scores et intérêts communs.

#### Smart Feed
```
GET /recommendations/feed/{user_id}?limit=20&skip=0
```
Retourne le fil d'actualité intelligent trié par pertinence.

#### Analyse de sentiment
```
POST /recommendations/sentiment/analyze/{post_id}
```
Analyse le sentiment d'un post spécifique.

```
POST /recommendations/sentiment/batch?limit=100
```
Analyse le sentiment de plusieurs posts en lot.

### Module Team 2 (`src/team2/`)

Modules d'analyse de graphe copiés depuis l'équipe 2 pour intégration.

- `extraction.py` - Extraction du graphe depuis Neo4j vers NetworkX
- `centrality_analysis.py` - Analyse de centralité (Betweenness, Closeness)
- `global_metrics.py` - Métriques globales du graphe
- `dashboard_data.py` - Données pour le dashboard Streamlit

---

## 🔧 Intégration dans l'application

### Backend (FastAPI)

**Fichier modifié:** `api.py`
- Ajout du router `recommendations`

**Fichier modifié:** `src/routers/feed.py`
- Ajout du paramètre `smart` pour activer le Smart Feed
- Scoring basé sur:
  - Proximité sociale (40%)
  - Sentiment du post (20%)
  - Engagement (likes) (20%)
  - Récence (20%)

### Frontend (Streamlit)

**Fichier modifié:** `app.py`

1. **Section Suggestions**
   - Affichage des recommandations d'amis
   - Bouton "Suivre" pour chaque recommandation
   - Affichage des intérêts communs
   - Affichage du score de pertinence

2. **Affichage du sentiment**
   - Badge avec emoji (😊 positif, 😔 négatif, 😐 neutre)
   - Couleur codée (vert, rouge, gris)
   - Affiché sur chaque post

3. **Smart Feed**
   - Badge de pertinence (⭐ score)
   - Posts triés par score de pertinence

---

## 🚀 Installation et Utilisation

### Dépendances additionnelles

```bash
pip install textblob matplotlib
python -m textblob.download_corpora
```

### Démarrage

1. **Démarrer l'API:**
```bash
python -m uvicorn api:app --reload
```

2. **Lancer Streamlit:**
```bash
streamlit run app.py
```

### Utilisation des fonctionnalités

#### Analyser le sentiment des posts existants

```python
from src.nlp.sentiment_analysis import batch_update_posts_sentiment
from src.db_utils import LinkUpDB

db = LinkUpDB()
updated = batch_update_posts_sentiment(db, limit=100)
print(f"{updated} posts analysés")
```

#### Générer des recommandations

```python
from src.recommendation.pipeline import generate_recommendations

recommendations = generate_recommendations("user_123", top_n=10)
for rec in recommendations:
    print(f"{rec['user_id']}: {rec['final_score']}")
```

#### Extraire les thèmes des posts

```python
from src.nlp.topic_modeling import build_topics_model_from_posts
from src.db_utils import LinkUpDB

db = LinkUpDB()
topics_model = build_topics_model_from_posts(db, limit=100)
print(f"Thèmes extraits: {len(topics_model['topics'])}")
```

---

## 📊 Algorithme du Smart Feed

Le Smart Feed priorise les posts en fonction de plusieurs facteurs:

### Formule de scoring

```
Score = 0.3 * Jaccard(user, author) 
      + 0.1 * InterestsSimilarity(user, author)
      + 0.2 * SentimentBonus
      + 0.2 * EngagementScore
      + 0.2 * RecencyBonus
```

### Détails

1. **Proximité sociale (40%)**
   - Jaccard (30%): Similarité des réseaux
   - Intérêts (10%): Similarité des intérêts

2. **Sentiment (20%)**
   - Positif: +0.2
   - Neutre: +0.1
   - Négatif: +0.0

3. **Engagement (20%)**
   - Basé sur le nombre de likes
   - Cap à 10 likes (score = likes/10)

4. **Récence (20%)**
   - Bonus fixe pour simplifier

---

## 🔬 Algorithme de Recommandation d'amis

### Pipeline

1. **Génération de candidats**
   - Utilisateurs à distance 2 (amis d'amis)
   - Extension avec utilisateurs aléatoires si insuffisant

2. **Calcul des scores**
   - Common Neighbors (normalisé)
   - Jaccard Similarity
   - Adamic-Adar (normalisé)
   - Interests Similarity

3. **Score combiné**
```
Final = 0.25 * CN_norm 
      + 0.25 * Jaccard 
      + 0.25 * AA_norm 
      + 0.25 * Interests
```

4. **Tri et sélection**
   - Tri par score final
   - Retour des top N

---

## 📈 Améliorations possibles

### Analyse de sentiment
- Utiliser un modèle français (CamemBERT)
- Ajuster les seuils de classification
- Ajouter plus de features (emojis, ponctuation)

### Topic Modeling
- Utiliser BERT pour des embeddings sémantiques
- Ajuster le nombre de thèmes dynamiquement
- Visualisation interactive des thèmes

### Smart Feed
- Apprentissage automatique des poids
- Personalisation par utilisateur
- A/B testing pour optimiser

### Recommandations
- Intégrer les métriques de centralité de Team 2
- Utiliser des techniques de collaborative filtering
- Ajouter des recommandations basées sur le contenu

---

## 👥 Collaboration inter-équipes

### Équipe 1 (Infrastructure & Backend)
- Base de données Neo4j avec schéma User/Post
- API FastAPI pour authentification et CRUD
- Data generator pour les données fictives

### Équipe 2 (Graph Mining)
- Extraction et analyse du graphe social
- Métriques de centralité (Betweenness, Closeness)
- Détection de communautés
- Dashboard Streamlit pour visualisation

### Équipe 3 (NLP & Recommandation)
- Analyse de sentiment des posts
- Topic Modeling pour catégorisation
- Système de recommandation d'amis
- Smart Feed pour personnalisation

### Points d'intégration
1. **Team 2 → Team 3**: Indicateurs de proximité pour recommandations
2. **Team 3 → Team 1**: Intégration des modèles dans l'API et l'interface
3. **Team 1 → Team 2/3**: Données et infrastructure

---

## 📝 Notes techniques

### Performance
- Les requêtes Neo4j sont optimisées avec des indexes
- Le Smart Feed utilise un cache pour éviter les recalculs
- L'analyse de sentiment peut être faite en batch

### Limitations
- TextBlob est optimisé pour l'anglais (moins performant en français)
- LDA nécessite un volume de données suffisant
- Les recommandations dépendent de la densité du graphe

### Sécurité
- Tous les endpoints nécessitent une authentification JWT
- Les données utilisateur sont protégées
- Pas de PII exposée dans les réponses

---

## 🎓 Références

- **TextBlob**: https://textblob.readthedocs.io/
- **Scikit-learn LDA**: https://scikit-learn.org/stable/modules/decomposition.html#latentdirichletallocation
- **NetworkX**: https://networkx.org/
- **Neo4j**: https://neo4j.com/docs/

---

## ✅ Checklist de validation

- [x] Module NLP (sentiment_analysis.py)
- [x] Module NLP (topic_modeling.py)
- [x] Module Recommandation (graph_queries.py)
- [x] Module Recommandation (proximity.py)
- [x] Module Recommandation (pipeline.py)
- [x] API Endpoints (/recommendations/*)
- [x] Smart Feed intégré dans /feed
- [x] Intégration Streamlit (suggestions)
- [x] Intégration Streamlit (sentiment)
- [x] Intégration Team 2 modules
- [x] Requirements.txt à jour
- [x] Documentation complète

---

**Auteurs:** Équipe 3 - NLP & Système de Recommandation  
**Date:** Juin 2026  
**Projet:** LinkUpDS - Le Réseau Social Intelligent
