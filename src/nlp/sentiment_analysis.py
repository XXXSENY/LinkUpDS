"""
src/nlp/sentiment_analysis.py (VERSION RENFORCÉE)
=================================================
Analyse de sentiment avancée pour LinkUpDS.

Utilise une approche multi-couche :
1. Lexique français ultra-étendu avec poids et contexte
2. Analyse des expressions complexes (n-grammes)
3. Détection des négations et intensificateurs
4. Analyse des emojis et de la ponctuation
5. Contexte thématique pour éviter les erreurs

Auteur : Équipe 3 (NLP & Recommandation)
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple, Optional, Set

logger = logging.getLogger(__name__)

# =========================
# LEXIQUE ULTRA-ÉTENDU AVEC POIDS
# =========================

LEXIQUE_SENTIMENT = {
    # ========================
    # TRÈS POSITIFS (poids +3)
    # ========================
    "excellent": 3, "excellente": 3, "excellents": 3, "excellentes": 3,
    "magnifique": 3, "magnifiques": 3, "splendide": 3, "splendides": 3,
    "merveilleux": 3, "merveilleuse": 3, "merveilleuses": 3,
    "extraordinaire": 3, "extraordinaires": 3, "incroyable": 3, "incroyables": 3,
    "fantastique": 3, "fantastiques": 3, "formidable": 3, "formidables": 3,
    "exceptionnel": 3, "exceptionnelle": 3, "exceptionnels": 3, "exceptionnelles": 3,
    "parfait": 3, "parfaite": 3, "parfaits": 3, "parfaites": 3,
    "génial": 3, "géniale": 3, "géniaux": 3, "géniales": 3,
    "genial": 3, "geniale": 3, "geniaux": 3, "geniales": 3,
    "superbe": 3, "superbes": 3, "sublime": 3, "sublimes": 3,
    "délicieux": 3, "délicieuse": 3, "délicieuses": 3,
    "délicieux": 3, "délicieuse": 3, "délicieuses": 3,
    "époustouflant": 3, "époustouflante": 3, "époustouflants": 3, "époustouflantes": 3,
    "renversant": 3, "renversante": 3, "renversants": 3, "renversantes": 3,
    "phénoménal": 3, "phénoménale": 3, "phénoménaux": 3, "phénoménales": 3,
    "divin": 3, "divine": 3, "divins": 3, "divines": 3,
    "magique": 3, "magiques": 3, "enchanteur": 3, "enchanteresse": 3, "enchanteresses": 3,
    "éblouissant": 3, "éblouissante": 3, "éblouissants": 3, "éblouissantes": 3,
    "étincelant": 3, "étincelante": 3, "étincelants": 3, "étincelantes": 3,
    "resplendissant": 3, "resplendissante": 3, "resplendissants": 3, "resplendissantes": 3,
    "exquis": 3, "exquise": 3, "exquises": 3,
    "somptueux": 3, "somptueuse": 3, "somptueuses": 3,
    "prodigieux": 3, "prodigieuse": 3, "prodigieuses": 3,
    "remarquable": 3, "remarquables": 3,
    "impressionnant": 3, "impressionnante": 3, "impressionnants": 3, "impressionnantes": 3,
    "épatant": 3, "épatante": 3, "épatants": 3, "épatantes": 3,
    "bluffant": 3, "bluffante": 3, "bluffants": 3, "bluffantes": 3,
    "stupéfiant": 3, "stupéfiante": 3, "stupéfiants": 3, "stupéfiantes": 3,
    
    # ========================
    # POSITIFS MOYENS (poids +2)
    # ========================
    "super": 2, "top": 2, "cool": 2, "chouette": 2, "chouettes": 2,
    "bravo": 2, "félicitations": 2,
    "adore": 2, "adoree": 2, "adoré": 2, "adorée": 2, "adorer": 2,
    "j'adore": 2, "j adore": 2,
    "aime": 2, "aimée": 2, "aimé": 2, "aimer": 2,
    "j'aime": 2, "j aime": 2,
    "kiffé": 2, "kiffée": 2, "kiffer": 2, "kiffe": 2,
    "amour": 2, "amoureux": 2, "amoureuse": 2, "amoureuses": 2,
    "heureux": 2, "heureuse": 2, "heureuses": 2,
    "content": 2, "contente": 2, "contents": 2, "contentes": 2,
    "ravi": 2, "ravie": 2, "ravis": 2, "ravies": 2,
    "enthousiaste": 2, "enthousiastes": 2,
    "réussi": 2, "réussie": 2, "réussis": 2, "réussies": 2,
    "succès": 2, "réussite": 2,
    "plaisir": 2, "agréable": 2, "agréables": 2,
    "joli": 2, "jolie": 2, "jolis": 2, "jolies": 2,
    "beau": 2, "belle": 2, "beaux": 2, "belles": 2,
    "drôle": 2, "drôles": 2, "rigolo": 2, "rigolote": 2, "rigolotes": 2,
    "amusant": 2, "amusante": 2, "amusants": 2, "amusantes": 2,
    "hilarant": 2, "hilarante": 2, "hilarants": 2, "hilarantes": 2,
    "intéressant": 2, "intéressante": 2, "intéressants": 2, "intéressantes": 2,
    "passionnant": 2, "passionnante": 2, "passionnants": 2, "passionnantes": 2,
    "captivant": 2, "captivante": 2, "captivants": 2, "captivantes": 2,
    "utile": 2, "utiles": 2, "pratique": 2, "pratiques": 2,
    "merci": 2, "remercie": 2, "remercié": 2, "remerciée": 2,
    "reconnaissant": 2, "reconnaissante": 2, "reconnaissants": 2, "reconnaissantes": 2,
    "fier": 2, "fière": 2, "fiers": 2, "fières": 2, "fierté": 2,
    "respect": 2, "admiration": 2, "admire": 2, "admiré": 2, "admirée": 2,
    "inspirant": 2, "inspirante": 2, "inspirants": 2, "inspirantes": 2,
    "motivant": 2, "motivante": 2, "motivants": 2, "motivantes": 2,
    "encourageant": 2, "encourageante": 2, "encourageants": 2, "encourageantes": 2,
    "réconfortant": 2, "réconfortante": 2, "réconfortants": 2, "réconfortantes": 2,
    "touchant": 2, "touchante": 2, "touchants": 2, "touchantes": 2,
    "émouvant": 2, "émouvante": 2, "émouvants": 2, "émouvantes": 2,
    "généreux": 2, "généreuse": 2, "généreuses": 2,
    "chaleureux": 2, "chaleureuse": 2, "chaleureuses": 2,
    "accueillant": 2, "accueillante": 2, "accueillants": 2, "accueillantes": 2,
    "convivial": 2, "conviviale": 2, "conviviales": 2,
    "sympathique": 2, "sympathiques": 2, "sympa": 2,
    "adorable": 2, "adorables": 2,
    "charmant": 2, "charmante": 2, "charmants": 2, "charmantes": 2,
    "craquant": 2, "craquante": 2, "craquants": 2, "craquantes": 2,
    "mignon": 2, "mignonne": 2, "mignons": 2, "mignonnes": 2,
    "savoureux": 2, "savoureuse": 2, "savoureuses": 2,
    "gourmand": 2, "gourmande": 2, "gourmands": 2, "gourmandes": 2,
    "régal": 2, "festin": 2, "délice": 2,
    "paradisiaque": 2, "paradisiaques": 2,
    "idyllique": 2, "idylliques": 2,
    "paisible": 2, "paisibles": 2, "calme": 2, "calmes": 2,
    "reposant": 2, "reposante": 2, "reposants": 2, "reposantes": 2,
    "relaxant": 2, "relaxante": 2, "relaxants": 2, "relaxantes": 2,
    "zen": 2, "serein": 2, "sereine": 2, "sereins": 2, "sereines": 2,
    "ressourçant": 2, "ressourçante": 2, "ressourçants": 2, "ressourçantes": 2,
    "énergisant": 2, "énergisante": 2, "énergisants": 2, "énergisantes": 2,
    "vivifiant": 2, "vivifiante": 2, "vivifiants": 2, "vivifiantes": 2,
    "rafraîchissant": 2, "rafraîchissante": 2, "rafraîchissants": 2, "rafraîchissantes": 2,
    "pétillant": 2, "pétillante": 2, "pétillants": 2, "pétillantes": 2,
    
    # ========================
    # LÉGÈREMENT POSITIFS (poids +1)
    # ========================
    "bon": 1, "bonne": 1, "bons": 1, "bonnes": 1,
    "bien": 1, "mieux": 1, "meilleur": 1, "meilleure": 1, "meilleurs": 1, "meilleures": 1,
    "gentil": 1, "gentille": 1, "gentils": 1, "gentilles": 1,
    "aimable": 1, "aimables": 1,
    "positif": 1, "positive": 1, "positifs": 1, "positives": 1,
    "espoir": 1, "espérer": 1, "espère": 1, "espéré": 1,
    "espoir": 1, "confiant": 1, "confiante": 1, "confiants": 1, "confiantes": 1,
    "optimiste": 1, "optimistes": 1,
    "doux": 1, "douce": 1, "doux": 1, "douces": 1,
    "simple": 1, "simples": 1, "facile": 1, "faciles": 1, "efficace": 1, "efficaces": 1,
    "vrai": 1, "vraie": 1, "vrais": 1, "vraies": 1,
    "juste": 1, "justes": 1, "clair": 1, "claire": 1, "clairs": 1, "claires": 1,
    "sourire": 1, "sourires": 1, "rire": 1, "rires": 1,
    "soleil": 1, "ensoleillé": 1, "ensoleillée": 1,
    "chaleur": 1, "chaud": 1, "chaude": 1, "chauds": 1, "chaudes": 1,
    "amis": 1, "amie": 1, "famille": 1, "maison": 1, "foyer": 1,
    "partage": 1, "partager": 1, "partagé": 1, "partagée": 1,
    "ensemble": 1, "communauté": 1, "collectif": 1, "collective": 1,
    "cadeau": 1, "cadeaux": 1, "surprise": 1, "surprises": 1,
    "voyage": 1, "vacances": 1, "aventure": 1, "découverte": 1,
    "nature": 1, "jardin": 1, "fleurs": 1, "fleur": 1,
    "musique": 1, "chanson": 1, "concert": 1,
    "film": 1, "cinéma": 1, "livre": 1, "lecture": 1,
    "sport": 1, "santé": 1, "forme": 1,
    "cuisine": 1, "manger": 1, "repas": 1, "dîner": 1, "déjeuner": 1,
    "café": 1, "thé": 1, "chocolat": 1,
    "repos": 1, "dormir": 1, "sommeil": 1, "sieste": 1,
    "dimanche": 1, "week-end": 1, "weekend": 1, "samedi": 1,
    "apprendre": 1, "découvrir": 1, "comprendre": 1, "savoir": 1,
    "créatif": 1, "créative": 1, "créatifs": 1, "créatives": 1,
    "projet": 1, "idée": 1, "idées": 1, "solution": 1, "solutions": 1,
    "travail": 1, "boulot": 1, "job": 1, "métier": 1,
    "lumineux": 1, "lumineuse": 1, "lumineuses": 1,
    "coloré": 1, "colorée": 1, "colorés": 1, "colorées": 1,
    "vivant": 1, "vivante": 1, "vivants": 1, "vivantes": 1,
    "animé": 1, "animée": 1, "animés": 1, "animées": 1,
    "dynamique": 1, "dynamiques": 1,
    "énergique": 1, "énergiques": 1,
    "tonique": 1, "toniques": 1,
    "frais": 1, "fraîche": 1, "frais": 1, "fraîches": 1,
    "nouveau": 1, "nouvelle": 1, "nouveaux": 1, "nouvelles": 1,
    "original": 1, "originale": 1, "originaux": 1, "originales": 1,
    "innovant": 1, "innovante": 1, "innovants": 1, "innovantes": 1,
    "moderne": 1, "modernes": 1,
    "élégant": 1, "élégante": 1, "élégants": 1, "élégantes": 1,
    "raffiné": 1, "raffinée": 1, "raffinés": 1, "raffinées": 1,
    "soigné": 1, "soignée": 1, "soignés": 1, "soignées": 1,
    "propre": 1, "propres": 1, "net": 1, "nette": 1, "nets": 1, "nettes": 1,
    "confortable": 1, "confortables": 1,
    "spacieux": 1, "spacieuse": 1, "spacieuses": 1,
    "lumineux": 1, "lumineuse": 1, "lumineuses": 1,
    "aéré": 1, "aérée": 1, "aérés": 1, "aérées": 1,
    "rapide": 1, "rapides": 1, "vite": 1,
    "fluide": 1, "fluides": 1,
    "stable": 1, "stables": 1,
    "solide": 1, "solides": 1, "robuste": 1, "robustes": 1,
    "fiable": 1, "fiables": 1,
    "sûr": 1, "sûre": 1, "sûrs": 1, "sûres": 1,
    "sécurisé": 1, "sécurisée": 1, "sécurisés": 1, "sécurisées": 1,
    "complet": 1, "complète": 1, "complets": 1, "complètes": 1,
    "riche": 1, "riches": 1,
    "abondant": 1, "abondante": 1, "abondants": 1, "abondantes": 1,
    "varié": 1, "variée": 1, "variés": 1, "variées": 1,
    "diversifié": 1, "diversifiée": 1, "diversifiés": 1, "diversifiées": 1,
    "gratuit": 1, "gratuite": 1, "gratuits": 1, "gratuites": 1,
    "offert": 1, "offerte": 1, "offerts": 1, "offertes": 1,
    
    # ========================
    # TRÈS NÉGATIFS (poids -3)
    # ========================
    "horrible": -3, "horribles": -3,
    "atroce": -3, "atroces": -3,
    "épouvantable": -3, "épouvantables": -3,
    "abominable": -3, "abominables": -3,
    "insupportable": -3, "insupportables": -3,
    "intolérable": -3, "intolérables": -3,
    "catastrophique": -3, "catastrophiques": -3,
    "désastreux": -3, "désastreuse": -3, "désastreuses": -3,
    "terrifiant": -3, "terrifiante": -3, "terrifiants": -3, "terrifiantes": -3,
    "effroyable": -3, "effroyables": -3,
    "cauchemardesque": -3, "cauchemardesques": -3,
    "exécrable": -3, "exécrables": -3,
    "ignoble": -3, "ignobles": -3,
    "répugnant": -3, "répugnante": -3, "répugnants": -3, "répugnantes": -3,
    "immonde": -3, "immondes": -3,
    "sordide": -3, "sordides": -3,
    "infâme": -3, "infâmes": -3,
    "odieux": -3, "odieuse": -3, "odieuses": -3,
    "haïssable": -3, "haïssables": -3,
    "insoutenable": -3, "insoutenables": -3,
    "invivable": -3,
    "infernal": -3, "infernale": -3, "infernales": -3,
    "démoniaque": -3, "démoniaques": -3,
    "diabolique": -3, "diaboliques": -3,
    "monstrueux": -3, "monstrueuse": -3, "monstrueuses": -3,
    "écœurant": -3, "écœurante": -3, "écœurants": -3, "écœurantes": -3,
    "nauséabond": -3, "nauséabonde": -3, "nauséabonds": -3, "nauséabondes": -3,
    "putride": -3, "putrides": -3,
    "pestilentiel": -3, "pestilentielle": -3, "pestilentielles": -3,
    "infect": -3, "infecte": -3, "infects": -3, "infectes": -3,
    
    # ========================
    # NÉGATIFS MOYENS (poids -2)
    # ========================
    "déteste": -2, "détesté": -2, "détestée": -2, "détester": -2,
    "je déteste": -2, "je deteste": -2,
    "hais": -2, "haïr": -2, "haine": -2, "haineux": -2, "haineuse": -2,
    "je hais": -2,
    "terrible": -2, "terribles": -2,
    "affreux": -2, "affreuse": -2, "affreuses": -2,
    "nul": -2, "nulle": -2, "nuls": -2, "nulles": -2,
    "mauvais": -2, "mauvaise": -2, "mauvaises": -2,
    "décevant": -2, "décevante": -2, "décevants": -2, "décevantes": -2,
    "déception": -2, "déçu": -2, "déçue": -2, "déçus": -2, "déçues": -2,
    "triste": -2, "tristes": -2, "tristesse": -2,
    "malheureux": -2, "malheureuse": -2, "malheureuses": -2,
    "pleurer": -2, "pleure": -2, "pleurs": -2, "larmes": -2,
    "souffrir": -2, "souffre": -2, "souffrance": -2, "douleur": -2,
    "douloureux": -2, "douloureuse": -2, "douloureuses": -2,
    "colère": -2, "énervé": -2, "énervée": -2, "énervés": -2, "énervées": -2,
    "énervement": -2,
    "fâché": -2, "fâchée": -2, "fâchés": -2, "fâchées": -2,
    "furieux": -2, "furieuse": -2, "furieuses": -2,
    "rage": -2, "rageux": -2, "rageuse": -2,
    "frustré": -2, "frustrée": -2, "frustrés": -2, "frustrées": -2,
    "frustration": -2, "frustrant": -2, "frustrante": -2, "frustrants": -2, "frustrantes": -2,
    "agacé": -2, "agacée": -2, "agacés": -2, "agacées": -2,
    "agacement": -2, "agaçant": -2, "agaçante": -2, "agaçants": -2, "agaçantes": -2,
    "énervant": -2, "énervante": -2, "énervants": -2, "énervantes": -2,
    "irritant": -2, "irritante": -2, "irritants": -2, "irritantes": -2,
    "échec": -2, "échouer": -2, "échoué": -2, "échouée": -2,
    "raté": -2, "ratée": -2, "ratés": -2, "ratées": -2, "rater": -2,
    "perdre": -2, "perdu": -2, "perdue": -2, "perdus": -2, "perdues": -2,
    "perdant": -2, "perdante": -2, "perdants": -2, "perdantes": -2,
    "inutile": -2, "inutiles": -2, "vain": -2, "vaine": -2,
    "ennuyeux": -2, "ennuyeuse": -2, "ennuyeuses": -2,
    "ennui": -2, "ennuyer": -2, "ennuie": -2,
    "chiant": -2, "chiante": -2, "chiants": -2, "chiantes": -2,
    "pénible": -2, "pénibles": -2,
    "difficile": -2, "difficiles": -2,
    "compliqué": -2, "compliquée": -2, "compliqués": -2, "compliquées": -2,
    "fatigué": -2, "fatiguée": -2, "fatigués": -2, "fatiguées": -2,
    "épuisé": -2, "épuisée": -2, "épuisés": -2, "épuisées": -2, "épuisement": -2,
    "malade": -2, "malades": -2, "maladie": -2,
    "peur": -2, "effrayé": -2, "effrayée": -2, "effrayés": -2, "effrayées": -2,
    "angoissé": -2, "angoissée": -2, "angoissés": -2, "angoissées": -2,
    "angoisse": -2, "angoissant": -2, "angoissante": -2, "angoissants": -2, "angoissantes": -2,
    "stress": -2, "stressé": -2, "stressée": -2, "stressés": -2, "stressées": -2,
    "stressant": -2, "stressante": -2, "stressants": -2, "stressantes": -2,
    "inquiet": -2, "inquiète": -2, "inquiets": -2, "inquiètes": -2,
    "inquiétude": -2, "inquiétant": -2, "inquiétante": -2, "inquiétants": -2, "inquiétantes": -2,
    "déprimé": -2, "déprimée": -2, "déprimés": -2, "déprimées": -2,
    "déprimant": -2, "déprimante": -2, "déprimants": -2, "déprimantes": -2,
    "seul": -2, "seule": -2, "seuls": -2, "seules": -2, "solitude": -2,
    "isolé": -2, "isolée": -2, "isolés": -2, "isolées": -2,
    "abandonné": -2, "abandonnée": -2, "abandonnés": -2, "abandonnées": -2,
    "abandon": -2,
    "trahir": -2, "trahi": -2, "trahie": -2, "trahison": -2,
    "mensonge": -2, "mentir": -2, "ment": -2, "menteur": -2, "menteuse": -2, "menteurs": -2, "menteuses": -2,
    "voler": -2, "volé": -2, "volée": -2, "volés": -2, "volées": -2,
    "voleur": -2, "voleuse": -2, "voleurs": -2, "voleuses": -2,
    "ridicule": -2, "ridicules": -2,
    "absurde": -2, "absurdes": -2,
    "stupide": -2, "stupides": -2,
    "idiot": -2, "idiote": -2, "idiots": -2, "idiotes": -2,
    "con": -2, "conne": -2, "cons": -2, "connes": -2,
    "connard": -2, "connasse": -2, "connards": -2, "connasses": -2,
    "imbécile": -2, "imbéciles": -2,
    "crétin": -2, "crétine": -2, "crétins": -2, "crétines": -2,
    "débile": -2, "débiles": -2,
    "médiocre": -2, "médiocres": -2,
    "lamentable": -2, "lamentables": -2,
    "pitoyable": -2, "pitoyables": -2,
    "pathétique": -2, "pathétiques": -2,
    "minable": -2, "minables": -2,
    "misérable": -2, "misérables": -2,
    "pauvre": -2, "pauvres": -2,
    "faible": -2, "faibles": -2,
    "fragile": -2, "fragiles": -2,
    "cassé": -2, "cassée": -2, "cassés": -2, "cassées": -2,
    "brisé": -2, "brisée": -2, "brisés": -2, "brisées": -2,
    "détruit": -2, "détruite": -2, "détruits": -2, "détruites": -2,
    "ruiné": -2, "ruinée": -2, "ruinés": -2, "ruinées": -2,
    "anéanti": -2, "anéantie": -2, "anéantis": -2, "anéanties": -2,
    "foutu": -2, "foutue": -2, "foutus": -2, "foutues": -2,
    "fichu": -2, "fichue": -2, "fichus": -2, "fichues": -2,
    "mort": -2, "morte": -2, "morts": -2, "mortes": -2,
    "crevé": -2, "crevée": -2, "crevés": -2, "crevées": -2,
    "vaincu": -2, "vaincue": -2, "vaincus": -2, "vaincues": -2,
    "humilié": -2, "humiliée": -2, "humiliés": -2, "humiliées": -2,
    "humiliation": -2, "humiliant": -2, "humiliante": -2, "humiliants": -2, "humiliantes": -2,
    "honte": -2, "honteux": -2, "honteuse": -2, "honteuses": -2,
    "gênant": -2, "gênante": -2, "gênants": -2, "gênantes": -2,
    "embarrassant": -2, "embarrassante": -2, "embarrassants": -2, "embarrassantes": -2,
    "désagréable": -2, "désagréables": -2,
    "déplaisant": -2, "déplaisante": -2, "déplaisants": -2, "déplaisantes": -2,
    "repoussant": -2, "repoussante": -2, "repoussants": -2, "repoussantes": -2,
    "laid": -2, "laide": -2, "laids": -2, "laides": -2,
    "moche": -2, "moches": -2,
    "hideux": -2, "hideuse": -2, "hideuses": -2,
    "vilain": -2, "vilaine": -2, "vilains": -2, "vilaines": -2,
    "sale": -2, "sales": -2,
    "crasseux": -2, "crasseuse": -2, "crasseuses": -2,
    "dégueulasse": -2, "dégueulasses": -2,
    "dégueu": -2,
    "crade": -2, "crades": -2,
    "pourri": -2, "pourrie": -2, "pourris": -2, "pourries": -2,
    "moisi": -2, "moisie": -2, "moisis": -2, "moisies": -2,
    "gâté": -2, "gâtée": -2, "gâtés": -2, "gâtées": -2,
    "avarié": -2, "avariée": -2, "avariés": -2, "avariées": -2,
    "périmé": -2, "périmée": -2, "périmés": -2, "périmées": -2,
    "toxique": -2, "toxiques": -2,
    "dangereux": -2, "dangereuse": -2, "dangereuses": -2,
    "violent": -2, "violente": -2, "violents": -2, "violentes": -2,
    "cruel": -2, "cruelle": -2, "cruels": -2, "cruelles": -2,
    "méchant": -2, "méchante": -2, "méchants": -2, "méchantes": -2,
    "malveillant": -2, "malveillante": -2, "malveillants": -2, "malveillantes": -2,
    "perfide": -2, "perfides": -2,
    "sournois": -2, "sournoise": -2, "sournoises": -2,
    "hypocrite": -2, "hypocrites": -2,
    "menteur": -2, "menteuse": -2, "menteurs": -2, "menteuses": -2,
    "tricheur": -2, "tricheuse": -2, "tricheurs": -2, "tricheuses": -2,
    "escroc": -2, "escroquerie": -2,
    "arnaque": -2, "arnaquer": -2, "arnaqué": -2, "arnaquée": -2,
    "vol": -2, "cambriolage": -2,
    "agression": -2, "attaque": -2,
    "menace": -2, "menaçant": -2, "menaçante": -2, "menaçants": -2, "menaçantes": -2,
    "harcèlement": -2, "harceler": -2, "harcelé": -2, "harcelée": -2,
    "insulte": -2, "insultant": -2, "insultante": -2, "insultants": -2, "insultantes": -2,
    "grossier": -2, "grossière": -2, "grossiers": -2, "grossières": -2,
    "vulgaire": -2, "vulgaires": -2,
    "obscène": -2, "obscènes": -2,
    "scandaleux": -2, "scandaleuse": -2, "scandaleuses": -2,
    "honteux": -2, "honteuse": -2, "honteuses": -2,
    "inadmissible": -2,
    "inacceptable": -2,
    "intolérable": -2, "intolérables": -2,
    "injuste": -2, "injustes": -2,
    "inique": -2, "iniques": -2,
    "arbitraire": -2, "arbitraires": -2,
    "abusif": -2, "abusive": -2, "abusifs": -2, "abusives": -2,
    "excessif": -2, "excessive": -2, "excessifs": -2, "excessives": -2,
    "démesuré": -2, "démesurée": -2, "démesurés": -2, "démesurées": -2,
    "exagéré": -2, "exagérée": -2, "exagérés": -2, "exagérées": -2,
    
    # ========================
    # LÉGÈREMENT NÉGATIFS (poids -1)
    # ========================
    "pas": -1, "non": -1, "jamais": -1, "rien": -1,
    "sans": -1, "moins": -1, "peu": -1,
    "pire": -1, "pires": -1,
    "bizarre": -1, "bizarres": -1,
    "étrange": -1, "étranges": -1,
    "curieux": -1, "curieuse": -1, "curieuses": -1,
    "dommage": -1, "hélas": -1, "malheureusement": -1,
    "problème": -1, "problèmes": -1,
    "souci": -1, "soucis": -1,
    "erreur": -1, "erreurs": -1,
    "faute": -1, "fautes": -1,
    "manque": -1, "manquer": -1, "manqué": -1, "manquée": -1,
    "absence": -1, "absent": -1, "absente": -1, "absents": -1, "absentes": -1,
    "trop": -1,
    "bruyant": -1, "bruyante": -1, "bruyants": -1, "bruyantes": -1,
    "bruit": -1, "bruits": -1,
    "froid": -1, "froide": -1, "froids": -1, "froides": -1,
    "long": -1, "longue": -1, "longs": -1, "longues": -1,
    "lent": -1, "lente": -1, "lents": -1, "lentes": -1,
    "cher": -1, "chère": -1, "chers": -1, "chères": -1,
    "coûteux": -1, "coûteuse": -1, "coûteuses": -1,
    "vieux": -1, "vieille": -1, "vieux": -1, "vieilles": -1,
    "ancien": -1, "ancienne": -1, "anciens": -1, "anciennes": -1,
    "usé": -1, "usée": -1, "usés": -1, "usées": -1,
    "abîmé": -1, "abîmée": -1, "abîmés": -1, "abîmées": -1,
    "dégradé": -1, "dégradée": -1, "dégradés": -1, "dégradées": -1,
    "endommagé": -1, "endommagée": -1, "endommagés": -1, "endommagées": -1,
    "défectueux": -1, "défectueuse": -1, "défectueuses": -1,
    "cassé": -1, "cassée": -1, "cassés": -1, "cassées": -1,
    "panne": -1, "pannes": -1,
    "bug": -1, "bugs": -1,
    "erreur": -1, "erreurs": -1,
    "retard": -1, "retards": -1,
    "attente": -1, "attentes": -1,
    "queue": -1,
    "foule": -1,
    "bondé": -1, "bondée": -1,
    "serré": -1, "serrée": -1, "serrés": -1, "serrées": -1,
    "étroit": -1, "étroite": -1, "étroits": -1, "étroites": -1,
    "sombre": -1, "sombres": -1,
    "obscur": -1, "obscure": -1, "obscurs": -1, "obscures": -1,
    "gris": -1, "grise": -1, "grises": -1,
    "terne": -1, "ternes": -1,
    "fade": -1, "fades": -1,
    "insipide": -1, "insipides": -1,
    "banal": -1, "banale": -1, "banals": -1, "banales": -1,
    "ordinaire": -1, "ordinaires": -1,
    "quelconque": -1, "quelconques": -1,
    "moyen": -1, "moyenne": -1, "moyens": -1, "moyennes": -1,
    "passable": -1, "passables": -1,
    "limite": -1, "limites": -1,
    "juste": -1, "justes": -1,
    "léger": -1, "légère": -1, "légers": -1, "légères": -1,
    "petit": -1, "petite": -1, "petits": -1, "petites": -1,
    "court": -1, "courte": -1, "courts": -1, "courtes": -1,
    "faible": -1, "faibles": -1,
    "insuffisant": -1, "insuffisante": -1, "insuffisants": -1, "insuffisantes": -1,
    "limité": -1, "limitée": -1, "limités": -1, "limitées": -1,
    "restreint": -1, "restreinte": -1, "restreints": -1, "restreintes": -1,
}

# =========================
# INTENSIFICATEURS ET MODIFICATEURS
# =========================

INTENSIFICATEURS = {
    "très": 1.5, "trop": 1.3, "vraiment": 1.4, "tellement": 1.6,
    "absolument": 1.7, "totalement": 1.7, "complètement": 1.6,
    "extrêmement": 1.8, "particulièrement": 1.4, "énormément": 1.7,
    "incroyablement": 1.8, "terriblement": 1.6, "follement": 1.7,
    "super": 1.4, "hyper": 1.5, "méga": 1.5, "ultra": 1.6,
    "si": 1.3, "tant": 1.3, "plus": 1.2, "moins": 0.7,
    "tellement": 1.6, "grave": 1.4, "carrément": 1.4,
}

NEGATIONS = {
    "ne", "n'", "pas", "plus", "jamais", "rien", "aucun", "aucune",
    "personne", "ni", "guère", "point", "nullement", "nul",
}

# =========================
# EXPRESSIONS COMPLEXES (N-GRAMMES)
# =========================

EXPRESSIONS_SENTIMENT = {
    # Expressions très positives
    "je suis heureux": 2, "je suis heureuse": 2,
    "je suis tellement heureux": 3, "je suis tellement heureuse": 3,
    "je suis content": 2, "je suis contente": 2,
    "je suis très content": 3, "je suis très contente": 3,
    "je suis ravi": 2, "je suis ravie": 2,
    "je suis fier": 2, "je suis fière": 2,
    "je suis reconnaissant": 2, "je suis reconnaissante": 2,
    "je me sens bien": 2, "je me sens super bien": 3,
    "je me sens mieux": 2, "je me sens beaucoup mieux": 3,
    "ça me plaît": 2, "ça me plait": 2, "ça m'a plu": 2,
    "ça m'a beaucoup plu": 3,
    "j'ai adoré": 2, "j'ai vraiment adoré": 3,
    "j'ai aimé": 2, "j'ai beaucoup aimé": 3,
    "j'ai kiffé": 2, "j'ai trop kiffé": 3,
    "j'ai apprécié": 2, "j'ai beaucoup apprécié": 3,
    "j'ai passé un bon moment": 2,
    "j'ai passé une excellente journée": 3,
    "j'ai passé une journée magnifique": 3,
    "c'est super": 2, "c'est vraiment super": 3,
    "c'est génial": 3, "c'est vraiment génial": 3,
    "c'est top": 2, "c'est vraiment top": 3,
    "c'est cool": 2,
    "c'est magnifique": 3, "c'est absolument magnifique": 3,
    "c'est splendide": 3,
    "c'est merveilleux": 3,
    "c'est excellent": 3, "c'est vraiment excellent": 3,
    "c'est parfait": 3, "c'est absolument parfait": 3,
    "c'est une bonne nouvelle": 3,
    "c'est une excellente nouvelle": 3,
    "quelle bonne nouvelle": 3,
    "quelle excellente nouvelle": 3,
    "je recommande": 2, "je recommande vivement": 3,
    "je conseille": 2, "je conseille fortement": 3,
    "bonne journée": 1, "bonne soirée": 1,
    "bon week-end": 1, "bon weekend": 1,
    "bonne nuit": 1, "bon appétit": 1, "bon appetit": 1,
    "joyeux anniversaire": 2, "bon anniversaire": 2,
    "félicitations": 3, "toutes mes félicitations": 3,
    "tous mes vœux": 2, "tous mes voeux": 2,
    "bien joué": 2, "très bien joué": 3,
    "bien fait": 2, "très bien fait": 3,
    "beau travail": 2, "très beau travail": 3,
    "bon courage": 1, "bonne chance": 1,
    "bon rétablissement": 1, "bon retablissement": 1,
    "je suis d'accord": 1, "tout à fait d'accord": 2,
    "tu as raison": 1, "vous avez raison": 1,
    "cela a du sens": 1, "c'est logique": 1, "c'est juste": 1,
    "c'est intéressant": 1, "c'est passionnant": 2, "c'est captivant": 2,
    "c'est incroyable": 3, "c'est vraiment incroyable": 3,
    "c'est fantastique": 3,
    "c'est formidable": 3,
    "c'est extraordinaire": 3,
    "quelle merveille": 3,
    "quel bonheur": 3,
    "quelle joie": 3,
    "quel plaisir": 2,
    "c'est un régal": 3,
    "c'est un délice": 3,
    "c'est une tuerie": 3,
    "c'est une pépite": 3,
    "c'est une merveille": 3,
    "je suis aux anges": 3,
    "je suis comblé": 2, "je suis comblée": 2,
    "je suis enchanté": 2, "je suis enchantée": 2,
    "je suis émerveillé": 3, "je suis émerveillée": 3,
    "je suis ébloui": 3, "je suis éblouie": 3,
    "je suis impressionné": 2, "je suis impressionnée": 2,
    "je suis époustouflé": 3, "je suis époustouflée": 3,
    "je suis bluffé": 3, "je suis bluffée": 3,
    "je suis conquis": 2, "je suis conquise": 2,
    "je suis séduit": 2, "je suis séduite": 2,
    "je suis charmé": 2, "je suis charmée": 2,
    "je suis fan": 2,
    "je suis accro": 2,
    "ça déchire": 3, "ça déchire tout": 3,
    "ça tue": 3,
    "ça envoie": 3,
    "ça assure": 2,
    "ça gère": 2,
    "ça roxe": 2,
    "ça claque": 3,
    "c'est de la bombe": 3,
    "c'est le feu": 3,
    "c'est ouf": 2, "c'est un truc de ouf": 3,
    "c'est dingue": 2, "c'est complètement dingue": 3,
    "c'est fou": 2, "c'est complètement fou": 3,
    "je kiffe": 2, "je kiffe trop": 3, "je kiffe grave": 3,
    "j'adore trop": 3, "j'adore grave": 3,
    "trop bien": 3, "vraiment trop bien": 3,
    "grave bien": 3,
    "super bon": 3, "super bonne": 3,
    "hyper bon": 3, "hyper bonne": 3,
    
    # Expressions très négatives
    "je suis triste": -2, "je suis très triste": -3,
    "je suis déçu": -2, "je suis déçue": -2,
    "je suis très déçu": -3, "je suis très déçue": -3,
    "je suis en colère": -2, "je suis très en colère": -3,
    "je suis énervé": -2, "je suis énervée": -2,
    "je suis très énervé": -3, "je suis très énervée": -3,
    "je suis fatigué": -1, "je suis fatiguée": -1,
    "je suis très fatigué": -2, "je suis très fatiguée": -2,
    "je suis épuisé": -2, "je suis épuisée": -2,
    "je suis malade": -2,
    "je suis stressé": -2, "je suis stressée": -2,
    "je suis inquiet": -2, "je suis inquiète": -2,
    "je suis angoissé": -2, "je suis angoissée": -2,
    "je suis déprimé": -3, "je suis déprimée": -3,
    "je me sens mal": -2, "je me sens très mal": -3,
    "je me sens seul": -2, "je me sens seule": -2,
    "je me sens perdu": -2, "je me sens perdue": -2,
    "je n'aime pas": -2, "je n'aime pas du tout": -3,
    "je déteste": -2, "je déteste ça": -3,
    "j'ai horreur": -3, "j'ai horreur de ça": -3,
    "je ne supporte pas": -3, "je ne supporte plus": -3,
    "j'en ai marre": -2, "j'en ai assez": -2, "j'en ai ras le bol": -3,
    "j'en peux plus": -3,
    "c'est nul": -2, "c'est nul à chier": -3,
    "c'est horrible": -3, "c'est affreux": -3, "c'est terrible": -2,
    "c'est une catastrophe": -3, "c'est un désastre": -3,
    "c'est une mauvaise nouvelle": -2,
    "c'est une très mauvaise nouvelle": -3,
    "c'est pas normal": -2, "c'est pas juste": -2,
    "c'est du n'importe quoi": -2, "n'importe quoi": -2,
    "c'est ridicule": -2, "c'est absurde": -2, "c'est stupide": -2,
    "c'est incompréhensible": -2, "je ne comprends pas": -1,
    "c'est trop dur": -2, "c'est trop difficile": -2,
    "c'est trop cher": -2, "c'est hors de prix": -3,
    "c'est une perte de temps": -3, "c'est une perte d'argent": -3,
    "ça ne sert à rien": -3, "ça ne vaut pas le coup": -2,
    "je suis désolé": -1, "je suis désolée": -1,
    "toutes mes excuses": -1,
    "ce n'est pas grave": -1, "c'est pas grave": -1,
    "tant pis": -1, "c'est dommage": -1, "quel dommage": -1,
    "c'est trop tard": -1, "c'est fini": -1, "c'est terminé": -1,
    "j'ai peur": -2, "j'ai très peur": -3,
    "j'ai la trouille": -2, "j'ai les boules": -2,
    "ça me fait peur": -2, "ça m'effraie": -2,
    "ça m'inquiète": -2, "ça me stresse": -2,
    "ça m'énerve": -2, "ça m'agace": -1,
    "ça me fatigue": -1, "ça m'ennuie": -1,
    "ça me déçoit": -2,
    "ça me rend triste": -2, "ça me rend malade": -3,
    "ça me prend la tête": -2, "ça me casse la tête": -2,
    "ça me fait chier": -3,
    "ça me gave": -2, "ça me soûle": -2, "ça me soule": -2,
    "ça craint": -2, "c'est la loose": -2,
    "c'est mort": -1, "c'est foutu": -2, "c'est fichu": -2,
    "je suis à bout": -3, "je suis au bout du rouleau": -3,
    "c'est de la merde": -3, "c'est de la daube": -3,
    "c'est pourri": -3, "c'est complètement pourri": -3,
    "c'est moisi": -3, "c'est complètement moisi": -3,
    "c'est dégueulasse": -3, "c'est vraiment dégueulasse": -3,
    "c'est dégueu": -3,
    "c'est crade": -3,
    "c'est sale": -2,
    "c'est moche": -2, "c'est vraiment moche": -3,
    "c'est laid": -2, "c'est vraiment laid": -3,
    "c'est mauvais": -2, "c'est vraiment mauvais": -3,
    "c'est immangeable": -3,
    "c'est imbuvable": -3,
    "c'est infect": -3,
    "c'est répugnant": -3,
    "c'est écœurant": -3,
    "c'est à vomir": -3,
    "ça pue": -3, "ça pue la merde": -3,
    "c'est l'enfer": -3,
    "c'est un cauchemar": -3,
    "c'est la galère": -2,
    "c'est la loose": -2,
    "c'est la honte": -2,
    "c'est honteux": -3,
    "c'est scandaleux": -3,
    "c'est inacceptable": -3,
    "c'est inadmissible": -3,
    "c'est intolérable": -3,
    "c'est insupportable": -3,
    "c'est une honte": -3,
    "c'est une arnaque": -3,
    "c'est du vol": -3,
    "c'est du racket": -3,
    "c'est de l'escroquerie": -3,
    "je regrette": -2, "je regrette amèrement": -3,
    "je m'en veux": -2, "je m'en veux terriblement": -3,
    "je suis dégoûté": -3, "je suis dégoûtée": -3,
    "je suis écœuré": -3, "je suis écœurée": -3,
    "je suis dévasté": -3, "je suis dévastée": -3,
    "je suis anéanti": -3, "je suis anéantie": -3,
    "je suis effondré": -3, "je suis effondrée": -3,
    "je suis désespéré": -3, "je suis désespérée": -3,
    "je suis au fond du trou": -3,
    "je touche le fond": -3,
    "j'ai le moral à zéro": -3,
    "j'ai le cafard": -2,
    "j'ai le blues": -2,
    "j'ai un coup de blues": -2,
    "je broie du noir": -3,
    "je vois tout en noir": -3,
    "tout va mal": -3,
    "rien ne va": -3,
    "tout est de travers": -3,
    "tout part en vrille": -3,
    "tout fout le camp": -3,
}

def _tokenize(text: str) -> List[str]:
    """Tokenisation avancée avec gestion des contractions françaises."""
    # Normaliser les apostrophes
    text = text.replace("'", "'").replace("'", "'").replace("`", "'")
    # Supprimer la ponctuation sauf apostrophes et tirets
    text = re.sub(r'[^\w\s\'\-]', ' ', text.lower())
    return text.split()

def _detect_negation_window(tokens: List[str], index: int, window_size: int = 3) -> bool:
    """Détecte si un mot est dans la portée d'une négation avec contexte élargi."""
    start = max(0, index - window_size)
    for j in range(start, index):
        token = tokens[j]
        # Vérification directe
        if token in NEGATIONS:
            return True
        # Vérification des contractions "n'" suivi d'un mot
        if token.startswith("n'") and token[2:] in {"est", "a", "ont", "ai", "as", "avons", "avez", "avait", "avaient", "était", "étaient", "ont", "aura", "aurait", "auraient"}:
            return True
    return False

def _find_expressions(text_lower: str) -> Tuple[float, int]:
    """Recherche les expressions complexes dans le texte."""
    expression_score = 0.0
    expressions_found = 0
    
    # Trier les expressions par longueur décroissante pour prioriser les plus longues
    sorted_expressions = sorted(EXPRESSIONS_SENTIMENT.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Marquer les parties déjà traitées pour éviter les doubles comptages
    covered_positions: Set[int] = set()
    
    for expression, weight in sorted_expressions:
        pos = text_lower.find(expression)
        while pos != -1:
            # Vérifier que cette portion n'est pas déjà couverte par une expression plus longue
            positions = set(range(pos, pos + len(expression)))
            if not positions.intersection(covered_positions):
                expression_score += weight
                expressions_found += 1
                covered_positions.update(positions)
            
            # Chercher l'occurrence suivante
            pos = text_lower.find(expression, pos + 1)
    
    return expression_score, expressions_found

def _analyze_by_lexicon(text: str) -> Tuple[float, float, int, Dict[str, int]]:
    """
    Analyse avancée basée sur le lexique ultra-étendu.
    
    Returns:
        Tuple[score, confidence, items_found, details]
    """
    text_lower = text.lower()
    
    # Étape 1: Expressions complexes (priorité maximale)
    expression_score, expressions_found = _find_expressions(text_lower)
    
    # Étape 2: Analyse mot par mot avec contexte
    tokens = _tokenize(text_lower)
    word_score = 0.0
    words_found = 0
    intensifier_active = 1.0
    negation_active = False
    
    for i, token in enumerate(tokens):
        # Détecter la négation
        if token in NEGATIONS or (token.startswith("n'") and len(token) > 2):
            negation_active = True
            continue
        
        # Vérifier les intensificateurs
        if token in INTENSIFICATEURS:
            intensifier_active = INTENSIFICATEURS[token]
            continue
        
        # Vérifier le lexique
        if token in LEXIQUE_SENTIMENT:
            weight = LEXIQUE_SENTIMENT[token]
            
            # Appliquer la négation si dans la fenêtre
            if negation_active or _detect_negation_window(tokens, i, window_size=4):
                weight *= -1
            
            # Appliquer l'intensificateur
            weighted_score = weight * intensifier_active
            
            word_score += weighted_score
            words_found += 1
            
            # Réinitialiser après un mot du lexique
            intensifier_active = 1.0
            negation_active = False
    
    # Étape 3: Analyse des emojis et ponctuation
    emoji_score = _analyze_emojis_and_punctuation(text)
    
    # Combiner les scores
    total_items = expressions_found + words_found
    lexical_score = 0.0
    
    if expressions_found > 0:
        lexical_score += expression_score
    
    if words_found > 0:
        lexical_score += word_score
    
    if total_items > 0:
        # Moyenne pondérée
        lexical_score = lexical_score / total_items
        # Ajouter le score emoji (max ±0.5)
        lexical_score += emoji_score * 0.5
    elif emoji_score != 0:
        lexical_score = emoji_score
    
    # Normalisation
    lexical_score = max(-3.0, min(3.0, lexical_score))
    normalized_score = lexical_score / 3.0  # Normaliser entre -1 et 1
    
    # Confiance basée sur la diversité et la force
    confidence = min(1.0, (total_items / max(len(tokens), 1)) * 2 + abs(normalized_score) * 0.5)
    
    details = {
        "expressions_found": expressions_found,
        "words_found": words_found,
        "emoji_score": emoji_score,
        "tokens_count": len(tokens),
        "expression_score": expression_score,
        "word_score": word_score,
    }
    
    return normalized_score, confidence, total_items, details

def _analyze_emojis_and_punctuation(text: str) -> float:
    """Analyse fine des émojis et de la ponctuation."""
    score = 0.0
    
    # Émojis positifs
    positive_emojis = [
        r'😊', r'😄', r'😃', r'😀', r'😁', r'😍', r'🥰', r'😘', r'😚', r'😙',
        r'👍', r'👏', r'🙌', r'💪', r'❤️', r'💕', r'💖', r'💗', r'💝', r'💘',
        r'🌟', r'⭐', r'✨', r'🎉', r'🎊', r'🥳', r'🎈', r'🎁', r'🎀',
        r'😎', r'🤩', r'🥹', r'😌', r'😇', r'🙏', r'💯', r'🔥', r'⚡',
        r'🌈', r'☀️', r'🌸', r'🌺', r'🌻', r'🌷', r'💐', r'🍀',
        r'🎵', r'🎶', r'🎸', r'🎹', r'🎺', r'🎻', r'🥁',
        r'⚽', r'🏀', r'🏈', r'⚾', r'🎾', r'🏆', r'🥇', r'🥈', r'🥉',
    ]
    
    # Émojis négatifs
    negative_emojis = [
        r'😢', r'😭', r'😤', r'😡', r'🤬', r'😠', r'😞', r'😔', r'😟', r'😕',
        r'👎', r'💔', r'😩', r'😫', r'🥺', r'😰', r'😨', r'😱', r'😓', r'😥',
        r'🤮', r'🤢', r'🥱', r'😴', r'💀', r'☠️', r'👿', r'😈',
        r'🌧️', r'⛈️', r'🌩️', r'💩', r'🖕', r'🤐', r'😬', r'😧', r'😦',
    ]
    
    # Compter les émojis
    positive_count = sum(len(re.findall(emoji, text)) for emoji in positive_emojis)
    negative_count = sum(len(re.findall(emoji, text)) for emoji in negative_emojis)
    
    # Émoticônes textuels positifs
    positive_text = [
        r':\)', r':-\)', r':D', r':-D', r':o\)', r':O\)',
        r'\^\^', r'\^_\^', r'\^-\^',
        r'\)\)+', r'\(:',
    ]
    
    # Émoticônes textuels négatifs
    negative_text = [
        r':\(', r':-\(', r':\'\(', r':\'\(', r'\(\(+',
        r'>_<', r'>\.<', r'>_>', r':/', r':-/', r':\\', r':-\\',
        r':\|', r':-\|', r'\):',
    ]
    
    positive_count += sum(len(re.findall(pattern, text)) for pattern in positive_text)
    negative_count += sum(len(re.findall(pattern, text)) for pattern in negative_text)
    
    total_emoji = positive_count + negative_count
    if total_emoji > 0:
        score += (positive_count - negative_count) / total_emoji
    
    # Points d'exclamation (intensité)
    excl_count = text.count('!')
    if excl_count > 0:
        # L'intensité renforce le score existant
        intensity = min(0.3, excl_count * 0.08)
        if positive_count > negative_count:
            score += intensity
        elif negative_count > positive_count:
            score -= intensity
    
    # Points d'interrogation multiples
    question_marks = len(re.findall(r'\?{2,}', text))
    if question_marks > 0:
        score -= 0.15 * question_marks
    
    # MAJUSCULES (intensité)
    uppercase_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if uppercase_ratio > 0.3:
        score *= 1.3
    
    # Points de suspension
    if '...' in text or '…' in text:
        score -= 0.15
    
    return max(-1.0, min(1.0, score))

def _analyze_text_structure(text: str) -> float:
    """Analyse de la structure du texte."""
    score = 0.0
    words = text.split()
    
    if len(words) < 3:
        return 0.0
    
    # Mots longs = discours élaboré
    avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
    if avg_word_length > 6:
        score += 0.1
    
    return score

def analyze_sentiment(text: str) -> Dict[str, any]:
    """
    Analyse du sentiment avec approche multi-couche renforcée.
    """
    if not text or not text.strip():
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "label": "neutre",
            "confidence": 0.0,
            "method": "empty",
            "details": {},
        }
    
    # Analyse multi-couche
    lexicon_score, lexicon_confidence, items_found, details = _analyze_by_lexicon(text)
    structure_score = _analyze_text_structure(text)
    
    # Combinaison
    if items_found > 0:
        final_score = lexicon_score * 0.8 + structure_score * 0.2
        confidence = lexicon_confidence
        method = "lexicon"
    else:
        emoji_score = _analyze_emojis_and_punctuation(text)
        final_score = emoji_score * 0.7 + structure_score * 0.3
        confidence = 0.2 if final_score != 0 else 0.1
        method = "light"
    
    # Normalisation
    final_score = max(-1.0, min(1.0, final_score))
    
    # Classification avec seuils
    if final_score > 0.08:
        label = "positif"
    elif final_score < -0.08:
        label = "negatif"
    else:
        label = "neutre"
    
    # Subjectivité
    subjectivity = min(1.0, abs(final_score) * 0.7 + (min(items_found, 5) / 5) * 0.3)
    
    return {
        "polarity": round(final_score, 4),
        "subjectivity": round(subjectivity, 4),
        "label": label,
        "confidence": round(confidence, 4),
        "method": method,
        "items_found": items_found,
        "details": details,
    }


# =========================
# API COMPATIBLE
# =========================

def batch_analyze_sentiment(texts: List[str]) -> List[Dict[str, any]]:
    """Analyse le sentiment d'une liste de textes."""
    return [analyze_sentiment(text) for text in texts]

def get_sentiment_emoji(label: str) -> str:
    """Retourne un emoji correspondant au label."""
    emoji_map = {
        "positif": "😊",
        "negatif": "😔",
        "neutre": "😐",
    }
    return emoji_map.get(label.lower(), "😐")

def get_sentiment_color(label: str) -> str:
    """Retourne une couleur CSS correspondant au label."""
    color_map = {
        "positif": "#4CAF50",
        "negatif": "#F44336",
        "neutre": "#9E9E9E",
    }
    return color_map.get(label.lower(), "#9E9E9E")


# =========================
# INTÉGRATION NEO4J
# =========================

def update_post_sentiment(db, post_id: str) -> bool:
    """Met à jour le sentiment d'un post dans Neo4j."""
    from src.db_utils import LinkUpDB

    if not isinstance(db, LinkUpDB):
        logger.error("Instance db invalide")
        return False

    post = db.get_post(post_id)
    if not post:
        logger.warning(f"Post {post_id} non trouvé")
        return False

    content = post.get("content", "")
    if not content:
        logger.warning(f"Post {post_id} sans contenu")
        return False

    sentiment_result = analyze_sentiment(content)

    query = """
    MATCH (p:Post {postId: $post_id})
    SET p.sentiment = $label,
        p.sentimentPolarity = $polarity,
        p.sentimentSubjectivity = $subjectivity,
        p.sentimentConfidence = $confidence
    RETURN p
    """

    try:
        db._execute_write(
            query,
            post_id=post_id,
            label=sentiment_result["label"],
            polarity=sentiment_result["polarity"],
            subjectivity=sentiment_result["subjectivity"],
            confidence=sentiment_result["confidence"],
        )
        logger.info(f"Sentiment mis à jour pour le post {post_id}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du sentiment: {e}")
        return False


def batch_update_posts_sentiment(db, limit: int = 100, reanalyze_all: bool = False) -> int:
    """Met à jour le sentiment de tous les posts sans analyse."""
    from src.db_utils import LinkUpDB

    if not isinstance(db, LinkUpDB):
        logger.error("Instance db invalide")
        return 0

    if reanalyze_all:
        query = """
        MATCH (p:Post)
        RETURN p.postId AS post_id, p.content AS content
        LIMIT $limit
        """
    else:
        query = """
        MATCH (p:Post)
        WHERE p.sentiment IS NULL
        RETURN p.postId AS post_id, p.content AS content
        LIMIT $limit
        """

    try:
        rows = db._execute_read(query, limit=limit)
        updated_count = 0

        for row in rows:
            post_id = row["post_id"]
            content = row["content"]

            if content:
                sentiment_result = analyze_sentiment(content)
                update_query = """
                MATCH (p:Post {postId: $post_id})
                SET p.sentiment = $label,
                    p.sentimentPolarity = $polarity,
                    p.sentimentSubjectivity = $subjectivity,
                    p.sentimentConfidence = $confidence
                """
                db._execute_write(
                    update_query,
                    post_id=post_id,
                    label=sentiment_result["label"],
                    polarity=sentiment_result["polarity"],
                    subjectivity=sentiment_result["subjectivity"],
                    confidence=sentiment_result["confidence"],
                )
                updated_count += 1

        logger.info(f"{updated_count} posts mis à jour avec sentiment")
        return updated_count
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour batch: {e}")
        return 0


if __name__ == "__main__":
    test_texts = [
        # Très positifs
        "J'adore ce réseau social, c'est génial ! 😊",
        "Excellent travail, je suis vraiment très content du résultat !",
        "Quelle bonne nouvelle ! Je suis tellement heureux aujourd'hui !",
        "C'est magnifique, splendide, extraordinaire ! Bravo à toute l'équipe ! 👏🎉",
        "Ce film est un chef-d'œuvre absolu, la réalisation est époustouflante !",
        "J'ai trop kiffé ce concert, c'était une tuerie ! 🔥",
        "La cuisine maison, rien de meilleur au monde ! Surtout quand c'est réussi.",
        "Je suis comblé par cette expérience, tout était parfait.",
        
        # Positifs modérés
        "C'est un bon film, j'ai bien aimé.",
        "La journée était agréable et ensoleillée.",
        "Merci pour votre aide, c'est très gentil.",
        "Bon courage pour la suite du projet !",
        "Ce gâteau est délicieux, tu as la recette ?",
        
        # Neutres
        "Le train arrive à 15h.",
        "J'ai acheté du pain et du lait.",
        "Je cherche des recommandations de films pour ce soir.",
        "Rendez-vous chez le dentiste la semaine prochaine.",
        
        # Négatifs modérés
        "Je suis un peu fatigué aujourd'hui.",
        "C'est dommage qu'il pleuve.",
        "Le film était décevant, je m'attendais à mieux.",
        "J'ai perdu mon portefeuille, quelle galère.",
        "Encore une panne de métro, je vais être en retard.",
        
        # Très négatifs
        "Je déteste ce temps pourri, c'est horrible ! 😡",
        "Quelle catastrophe ! Tout est fichu, c'est un désastre total !",
        "Je suis extrêmement déçu et en colère, c'est inacceptable !",
        "C'est nul à chier, j'en ai vraiment marre de cette situation ! 🤬",
        "Ce restaurant est une arnaque totale, nourriture infecte et service déplorable.",
        "Je suis au bout du rouleau, tout va mal en ce moment.",
        "Quelle honte ce spectacle, c'était lamentable du début à la fin.",
        
        # Avec négations
        "Je ne suis pas content du tout.",
        "Ce n'est pas une bonne nouvelle.",
        "Je n'aime pas du tout cette idée.",
        "Ce n'est pas mauvais, mais je m'attendais à mieux.",
        
        # Avec intensificateurs
        "C'est vraiment très très bien !",
        "C'est absolument horrible et terriblement décevant.",
        "Je suis tellement heureux que c'en est presque incroyable !",
        "Ce gâteau est vraiment délicieux, hyper moelleux et pas trop sucré.",
        
        # Ironie / sarcasme
        "Super, encore une panne. C'est exactement ce dont j'avais besoin.",
        "Génial, le train est encore en retard. Quelle surprise.",
    ]

    print("=" * 80)
    print("TESTS D'ANALYSE DE SENTIMENT AVANCÉE")
    print("=" * 80)
    
    correct = 0
    total = len(test_texts)
    
    expected = [
        "positif", "positif", "positif", "positif", "positif", "positif", "positif", "positif",
        "positif", "positif", "positif", "positif", "positif",
        "neutre", "neutre", "neutre", "neutre",
        "negatif", "negatif", "negatif", "negatif", "negatif",
        "negatif", "negatif", "negatif", "negatif", "negatif",
        "negatif", "negatif", "negatif", "negatif", "negatif",
        "positif", "negatif",
        "positif", "negatif",
    ]
    
    for i, (text, exp) in enumerate(zip(test_texts, expected)):
        result = analyze_sentiment(text)
        emoji = get_sentiment_emoji(result["label"])
        
        status = "✅" if result["label"] == exp else "❌"
        if result["label"] == exp:
            correct += 1
        
        print(f"\n{status} {emoji} {text[:80]}...")
        print(f"   Attendu: {exp} | Obtenu: {result['label']}")
        print(f"   Polarité: {result['polarity']:.4f} | Confiance: {result['confidence']:.4f}")
        if "details" in result:
            d = result["details"]
            print(f"   Expressions: {d.get('expressions_found', 0)} | Mots: {d.get('words_found', 0)} | Emojis: {d.get('emoji_score', 0):.2f}")
    
    print("\n" + "=" * 80)
    print(f"Précision: {correct}/{total} ({correct/total*100:.1f}%)")
    print("=" * 80)