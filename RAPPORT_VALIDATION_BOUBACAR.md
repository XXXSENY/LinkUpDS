# Rapport de validation — Boubacar Biro Diallo
## Sprint 1 — Équipe 3 (NLP & Recommandation)

## 1. Environnement
- Branche : `equipe-3-nlp-recommandation`
- Base Neo4j : locale (Neo4j Desktop)
- Date : 22/06/2026

## 2. Données générées
- 30 utilisateurs avec interests remplis ✅
- 59 posts ✅
- Relations FOLLOWS créées ✅
- Likes créés ✅

## 3. Anomalies détectées (J1)
- `u.interests = []` pour tous les users → signalé à Bechir → corrigé ✅
- `p.authorId = null` sur tous les posts → signalé à Bechir ✅

## 4. Jeu de données contrôlé (J2)
Créé manuellement dans Neo4j avec 6 utilisateurs :

| User | Suit | Interests |
|------|------|-----------|
| test_alice | Bob, Cara | tech, music |
| test_bob | Dan, Eva | tech, sport |
| test_cara | Eva | music, art |
| test_dan | Fab | sport, tech |
| test_eva | — | art, music |
| test_fab | — | sport |

## 5. Validation des fonctions d'Oumou (proximity.py)

| Paire | Common Neighbors | Jaccard | Interests sim | Score combiné |
|-------|-----------------|---------|---------------|---------------|
| alice vs dan | 0 | 0.0 | 0.3333 | 0.1 |
| alice vs eva | 0 | 0.0 | 0.3333 | 0.1 |
| bob vs cara | 1 | 0.5 | 0.0 | 0.2 |
| alice vs fab | 0 | 0.0 | 0.0 | 0.0 |

**Résultat : toutes les fonctions sont correctes ✅**

## 6. Validation du pipeline d'Ibrahima (pipeline.py)
Test sur les 30 vrais utilisateurs :

| Rang | user_id | CN | Jaccard | AA | Interests | Score |
|------|---------|----|---------|----|-----------|-------|
| 1 | user_db73... | 3 | 0.2727 | 2.7222 | 0.125 | 0.4083 |
| 2 | user_fd49... | 3 | 0.3333 | 2.5589 | 0.125 | 0.4028 |
| 3 | user_1e2b... | 3 | 0.2727 | 2.4559 | 0.1667 | 0.3895 |

**Résultat : pipeline fonctionnel, recommandations cohérentes ✅**

## 7. Tests automatisés
- 25/25 tests passent ✅