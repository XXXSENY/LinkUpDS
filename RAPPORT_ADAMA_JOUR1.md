\# RAPPORT JOUR 1 - Adama Kané

\## Support données \& validation



\*\*Date :\*\* 16/06/2026

\*\*Heure de vérification :\*\* 23:01



\---



\## 1. Environnement



| Élément | Statut |

|---------|--------|

| Environnement virtuel | ✅ |

| Dépendances installées | ✅ |

| Neo4j | ✅ Connecté |

| MongoDB | ✅ Connecté |

| API FastAPI | ✅ Lancée (port 8000) |



\---



\## 2. Exécution de data\_generator.py



\*\*Commande :\*\* `py scripts/data\_generator.py`



\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*





\---



\## 3. Vérification des données



\*\*Commande :\*\* `py -m scripts.verification\_donnees`



\### Statistiques générales



| Métrique | Valeur | Statut |

|----------|--------|--------|

| Utilisateurs | 31 | ✅ |

| Posts | 53 | ✅ |

| Relations FOLLOWS | 180 | ✅ |

| Likes | 0 | ⚠️ |

| Posts avec contenu | 53 | ✅ |

| Utilisateurs avec intérêts | 0 | ⚠️ |



\### Structure du graphe



| Métrique | Valeur |

|----------|--------|

| Degré moyen (following) | 5.81 |

| Plus influent | adele01 (13 followers) |



\### Exemples de relations FOLLOWS



\- xguibert suit nfaure

\- xguibert suit adele01

\- xguibert suit susan61

\- xguibert suit dianemenard

\- xguibert suit theodoresauvage



\### Exemples de posts



1\. "Dépasser ruine vaste recommencer avant en etc agiter voisin afin de coup quelqu'un lutte roman secon..."

2\. "Aller visible loup admettre épais couleur lever art recueillir aile mer docteur pleurer sauvage eh c..."

3\. "Possible sur elle taire compagnie fait race repousser remplacer durer regard enfin rencontre mon vol..."



\---



\## 4. Vérification pour les équipes



\### Équipe 2 - Oumou (Graph Mining)



\- ✅ Suffisamment de relations FOLLOWS (180) pour les calculs

\- ⚠️ Peu d'utilisateurs avec intérêts (0) → \*\*impact sur la similarité d'intérêts\*\*



\### Équipe 3 - Ibrahima (NLP \& Recommandations)



\- ✅ 30 utilisateurs avec ≥ 2 follows → \*\*suffisant pour les recommandations\*\*

\- ✅ 53 posts avec contenu → \*\*suffisant pour l'analyse NLP\*\*



\---



\## 5. Résumé des vérifications



| Critère | Statut |

|---------|--------|

| Utilisateurs > 0 | ✅ |

| Posts > 0 | ✅ |

| Relations FOLLOWS > 0 | ✅ |

| Posts avec contenu > 0 | ✅ |



\*\*Conclusion :\*\* 🎉 TOUTES LES VÉRIFICATIONS SONT OK



\---



\## 6. Anomalies identifiées



| Problème | Description | Impact | Suggestion |

|----------|-------------|--------|------------|

| Absence de likes | La relation LIKES n'existe pas dans la base | Équipe 3 : analyse de sentiment limitée | Vérifier la génération des likes |

| Absence d'intérêts | Le champ interests est vide pour tous les utilisateurs | Équipe 2 : similarité d'intérêts impossible | Ajouter des intérêts dans data\_generator |



\---



\## 7. Conclusion du JOUR 1



✅ \*\*JOUR 1 VALIDÉ\*\*



\- Environnement opérationnel

\- Données générées avec succès

\- Relations FOLLOWS exploitables (180 relations)

\- 31 utilisateurs et 53 posts disponibles



\*\*Les données sont exploitables pour les équipes 2 et 3.\*\*



\---



\## 8. Prochaines étapes (JOUR 2)



\- \[ ] Tester les fonctions d'Oumou (Common Neighbors, Jaccard)

\- \[ ] Tester les fonctions d'Ibrahima (recommandations)

\- \[ ] Valider les résultats sur 2-3 utilisateurs

\- \[ ] Remonter les anomalies



\---



\## 9. Annexes



\### Log complet de la vérification



