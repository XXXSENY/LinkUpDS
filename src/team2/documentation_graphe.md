---

# 📄 Documentation de la structure du graphe — LinkUpDS (Équipe 2)

## 1. Introduction

Dans le cadre du projet LinkUpDS (réseau social intelligent), cette partie a pour objectif de décrire la structure du graphe social construit à partir des données stockées dans Neo4j.
Le rôle de ce module est d’extraire les données relationnelles (utilisateurs et connexions) et de les transformer en un graphe exploitable avec NetworkX pour des analyses ultérieures.

---

## 2. Type de graphe

Le graphe construit est :

- **Type :** Graphe orienté (Directed Graph)

- **Librairie utilisée :** NetworkX

- **Source de données :** Neo4j (base de données graphe)

Chaque relation possède une direction :

> 
> Un utilisateur A peut suivre un utilisateur B, sans réciprocité obligatoire.
> 

---

## 3. Structure des nœuds (Nodes)

Les nœuds représentent les utilisateurs du réseau social.

### 🔹 Type de nœud :

- `User`

### 🔹 Propriétés principales :

- `userId` : identifiant unique de l’utilisateur

### 🔹 Représentation :

Chaque utilisateur de la base de données est transformé en un nœud du graphe.

---

## 4. Structure des relations (Edges)

Les relations représentent les interactions sociales entre utilisateurs.

### 🔹 Type de relation :

- `FOLLOWS`

### 🔹 Sens de la relation :

- `(User A) → (User B)` signifie que A suit B

### 🔹 Représentation :

Chaque relation FOLLOWS dans Neo4j devient une arête dirigée dans NetworkX.

---

## 5. Modélisation dans NetworkX

Le graphe est construit de la manière suivante :

- Initialisation d’un graphe orienté :

```
```
G = nx.DiGraph()
```
```

- Ajout des relations extraites depuis Neo4j :

```
```
G.add_edge(user_source, user_target)
```
```

Ainsi :

- chaque utilisateur devient un nœud

- chaque relation devient une arête dirigée

---

## 6. Taille du graphe (jeu de données actuel)

Après génération des données fictives :

- **Nombre de nœuds (utilisateurs) :** 30

- **Nombre de relations (follows) :** 157

Ces valeurs peuvent évoluer en fonction du volume de données générées par l’équipe backend.

---

## 7. Source des données

Les données utilisées proviennent de :

- Une API FastAPI (équipe Infrastructure)

- Un générateur de données fictives (`data_generator.py`)

- Une base Neo4j locale

Processus :

1. Création des utilisateurs via API

2. Génération de posts, likes et follows

3. Stockage dans Neo4j

4. Extraction vers NetworkX

---

## 8. Objectif du graphe

Ce graphe est utilisé pour :

- L’analyse de la structure sociale

- L’étude des relations entre utilisateurs

- La préparation des algorithmes avancés (centralité, communautés, recommandations)

---

## 9. Conclusion

Le module d’extraction permet de transformer les données stockées dans Neo4j en un graphe orienté exploitable avec NetworkX.
Il constitue une étape essentielle pour les analyses de réseau effectuées par l’équipe Graph Mining.
