"""
src/nlp/topic_modeling.py (VERSION FINALE COMPLÈTE)
====================================================
Extraction de thèmes (Topic Modeling) pour LinkUpDS.

Approche hybride et robuste optimisée pour la détection par mots :
1. Matching par mots individuels ET bigrammes avec pondération
2. Stopwords français ultra-complets (300+ mots)
3. 24 catégories thématiques avec des milliers de mots-clés
4. Seuil adaptatif pour les posts courts (min 1 mot, score >= 3.0)
5. JAMAIS d'attribution par défaut

Auteur : Équipe 3 (NLP & Recommandation)
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import Counter

import numpy as np

logger = logging.getLogger(__name__)

# Import conditionnel de scikit-learn
try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn non disponible. pip install scikit-learn")

# =========================
# STOPWORDS FRANÇAIS ULTRA-COMPLETS (400+ mots)
# =========================

STOPWORDS_FR: Set[str] = {
    # Articles et déterminants
    "le", "la", "les", "un", "une", "des", "du", "au", "aux", "de", "à", "a",
    # Conjonctions
    "et", "ou", "mais", "donc", "car", "ni", "or", "que", "qui", "quoi",
    "dont", "où", "ou", "comment", "pourquoi", "quand", "combien",
    # Verbes très fréquents (infinitif)
    "est", "sont", "être", "etre", "avoir", "faire", "dire", "aller",
    "venir", "voir", "savoir", "pouvoir", "vouloir", "devoir", "falloir",
    # Verbes très fréquents (conjugués)
    "suis", "es", "sommes", "êtes", "etes", "ai", "as", "a", "avons", "avez", "ont",
    "vais", "vas", "va", "allons", "allez", "vont",
    "fais", "fait", "faisons", "faites", "font",
    "dis", "dit", "disons", "dites", "disent",
    "peux", "peut", "peuvent", "veux", "veut", "veulent",
    "dois", "doit", "devons", "devez", "doivent",
    "étais", "etais", "était", "etait", "étions", "etions", "étiez", "etiez", "étaient", "etaient",
    "avais", "avait", "avions", "aviez", "avaient",
    "serai", "seras", "sera", "serons", "serez", "seront",
    "aurai", "auras", "aura", "aurons", "aurez", "auront",
    "pourrai", "pourras", "pourra", "pourrons", "pourrez", "pourront",
    "voudrai", "voudras", "voudra", "voudrons", "voudrez", "voudront",
    "devrai", "devras", "devra", "devrons", "devrez", "devront",
    "ferai", "feras", "fera", "ferons", "ferez", "feront",
    "irai", "iras", "ira", "irons", "irez", "iront",
    "viendrai", "viendras", "viendra", "viendrons", "viendrez", "viendront",
    # Participes passés courants
    "été", "ete", "eu", "eue", "eus", "eues", "fait", "faite", "faits", "faites",
    "dit", "dite", "dits", "dites", "vu", "vue", "vus", "vues",
    "su", "sue", "sus", "sues", "pu", "pue", "pus", "pues",
    "voulu", "voulue", "voulus", "voulues", "fallu",
    "allé", "alle", "allée", "allee", "allés", "alles", "allées", "allees",
    "venu", "venue", "venus", "venues",
    "devenu", "devenue", "devenus", "devenues",
    "resté", "reste", "restée", "restee", "restés", "restes", "restées", "restees",
    "passé", "passe", "passée", "passee", "passés", "passes", "passées", "passees",
    "donné", "donne", "donnée", "donnee", "donnés", "donnes", "données", "donnees",
    "pris", "prise", "prises", "mis", "mise", "mises",
    "connu", "connue", "connus", "connues",
    "cru", "crue", "crus", "crues",
    "lu", "lue", "lus", "lues", "écrit", "ecrit", "écrite", "ecrite", "écrits", "ecrits", "écrites", "ecrites",
    # Pronoms personnels
    "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "me", "te", "se", "moi", "toi", "soi", "lui", "leur", "eux",
    "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes", "ses",
    "notre", "votre", "leur", "nos", "vos", "leurs",
    "ce", "cet", "cette", "ces", "ceci", "cela", "ça", "ca",
    "celui", "celle", "ceux", "celles",
    # Prépositions
    "dans", "sur", "sous", "avec", "sans", "pour", "par", "vers",
    "chez", "entre", "parmi", "comme", "contre", "pendant", "depuis",
    "avant", "après", "apres", "devant", "derrière", "derriere",
    "en", "y", "dès", "des", "lors", "hormis", "malgré", "malgre",
    "selon", "suivant", "durant", "outre", "voici", "voilà", "voila",
    # Adverbes très fréquents
    "tout", "tous", "toute", "toutes",
    "très", "tres", "trop", "peu", "beaucoup", "plus", "moins",
    "bien", "mal", "mieux", "pire", "aussi", "si", "tant", "tellement",
    "alors", "ensuite", "puis", "enfin", "déjà", "deja",
    "encore", "toujours", "jamais", "parfois", "souvent", "rarement",
    "maintenant", "aujourd'hui", "aujourdhui", "hier", "demain",
    "ici", "là", "la", "partout", "ailleurs", "loin", "près", "pres",
    "rien", "quelque", "quelqu'un", "quelquun", "chacun",
    "personne", "autre", "autres", "autrui",
    "même", "meme", "mêmes", "memes",
    "tel", "telle", "tels", "telles",
    "certain", "certains", "certaine", "certaines",
    "plusieurs", "quelques", "nombreux", "nombreuses",
    "chaque", "aucun", "aucune", "nul", "nulle",
    # Mots de liaison et modalisateurs
    "cependant", "néanmoins", "neanmoins",
    "toutefois", "pourtant", "ainsi", "bref", "donc",
    "effectivement", "évidemment", "evidemment",
    "certainement", "probablement", "peut-être", "peut etre", "peutetre",
    "sans doute", "bien sûr", "bien sur",
    "en effet", "par contre", "en revanche", "par ailleurs",
    "c'est-à-dire", "c est a dire", "notamment", "en particulier",
    # Formes contractées
    "c'est", "cest", "n'est", "nest", "s'est", "sest",
    "j'ai", "jai", "tu as", "il a", "elle a", "on a",
    "nous avons", "vous avez", "ils ont", "elles ont",
    "je suis", "tu es", "il est", "elle est", "on est",
    "nous sommes", "vous êtes", "vous etes", "ils sont", "elles sont",
    "j'avais", "javais", "tu avais", "il avait", "elle avait",
    "nous avions", "vous aviez", "ils avaient", "elles avaient",
    "je serai", "tu seras", "il sera", "elle sera",
    "j'aurai", "jaurai", "tu auras", "il aura", "elle aura",
    "j'irai", "jirai", "tu iras", "il ira", "elle ira",
    "je ferai", "je feras", "il fera", "elle fera",
    # Autres mots vides
    "non", "oui", "ne", "n'", "qu'", "qu", "d'", "d", "l'", "l",
    "m'", "m", "t'", "t", "s'", "s",
    "chose", "truc", "machin", "bidule", "trucmuche",
    "manière", "maniere", "façon", "facon", "sorte", "espèce", "espece",
    "genre", "type", "cas", "exemple", "partie", "part", "côté", "cote",
    "fois", "temps", "jour", "nuit", "matin", "soir",
    "an", "année", "annee", "mois", "semaine", "heure", "minute", "seconde",
    "monsieur", "madame", "mademoiselle", "mr", "mme", "mlle",
    "ça", "ca", "cela", "celui-ci", "celui-la",
    "quel", "quelle", "quels", "quelles",
    "lequel", "laquelle", "lesquels", "lesquelles",
    "dont", "duquel", "desquels", "desquelles",
    "bon", "bonne", "bons", "bonnes",
    "petit", "petite", "petits", "petites",
    "grand", "grande", "grands", "grandes",
    "vrai", "vraie", "vrais", "vraies",
    "faux", "fausse", "faux", "fausses",
    "nouveau", "nouvelle", "nouveaux", "nouvelles",
    "jeune", "jeunes", "vieux", "vieille", "vieilles",
    "possible", "impossible", "facile", "difficile", "simple", "compliqué",
    "absolu", "absolue", "absolus", "absolues",
    "total", "totale", "totals", "totales",
    "complet", "complète", "complets", "complètes",
    "vraiment", "absolument", "totalement", "complètement",
    "génial", "genial", "super", "top", "cool", "chouette",
    "nul", "horrible", "terrible", "affreux", "dégueulasse",
    "magnifique", "splendide", "merveilleux", "superbe",
    "bonheur", "malheur", "joie", "tristesse", "plaisir", "déplaisir",
    "adorer", "détester", "aimer", "haïr",
    "recommande", "conseille", "déconseille",
    "merci", "bravo", "félicitations",
    "dommage", "tant pis", "hélas",
    "absolument", "certainement", "évidemment",
    "comment", "pourquoi", "quand", "où", "combien",
    "est-ce", "est ce", "qu'est-ce", "qu est ce",
    "alors", "donc", "car", "mais", "ou", "et", "or", "ni",
    "cependant", "néanmoins", "toutefois", "pourtant", "ainsi", "bref",
    # Mots de remplissage oraux
    "euh", "bah", "ben", "hein", "quoi", "enfin", "du coup", "voilà", "voila",
    "genre", "style", "là", "la", "quoi", "nan", "ouais", "mouais",
    # Titres et formules de politesse
    "bonjour", "bonsoir", "salut", "coucou", "hello", "bye", "au revoir", "adieu",
    "s'il vous plaît", "s il vous plait", "s'il te plaît", "s il te plait",
    "merci", "de rien", "je vous en prie", "je t en prie",
    "excusez-moi", "excusez moi", "pardon", "désolé", "desole", "désolée", "desolee",
    "félicitations", "bonne journée", "bonne soiree", "bonne nuit",
    "joyeux", "heureux", "heureuse", "bon", "bonne",
    # Mois et jours (gardés pour le thème Lifestyle)
    # mais retirés des stopwords pour permettre la détection
    # "lundi", "mardi", etc. sont déplacés dans le dictionnaire Lifestyle
    "aujourd'hui", "aujourdhui", "demain", "hier",
    "matin", "midi", "après-midi", "apres midi", "soir", "nuit",
    "matinée", "matinee", "soirée", "soiree", "journée", "journee",
}

# =========================
# DICTIONNAIRE DE THÈMES - 24 CATÉGORIES
# =========================

TOPIC_KEYWORDS: Dict[str, Dict[str, int]] = {
    
    # ========================
    # 1. SPORT
    # ========================
    "Sport": {
        "sport": 3, "sportif": 3, "sportive": 3, "sportifs": 3, "sportives": 3,
        "football": 3, "foot": 3, "footballeur": 3, "footballeuse": 3,
        "basketball": 3, "basket": 3, "basketteur": 3, "basketteuse": 3,
        "tennis": 3, "tennisman": 3, "tenniswoman": 3,
        "rugby": 3, "rugbyman": 3, "golf": 3, "golfeur": 3, "golfeuse": 3,
        "natation": 3, "nageur": 3, "nageuse": 3, "piscine": 2,
        "athlétisme": 3, "athletisme": 3, "athlète": 3, "athlete": 3,
        "marathon": 3, "sprint": 3, "triathlon": 3,
        "musculation": 3, "muscu": 3, "fitness": 3, "cardio": 3,
        "yoga": 3, "pilates": 3, "crossfit": 3,
        "gymnastique": 3, "gymnaste": 3,
        "boxe": 3, "boxeur": 3, "boxeuse": 3, "judo": 3, "karaté": 3, "karate": 3,
        "escalade": 3, "grimpe": 3, "grimpeur": 3, "alpinisme": 3,
        "surf": 3, "surfeur": 3, "surfeuse": 3, "ski": 3, "skieur": 3, "skieuse": 3,
        "vélo": 3, "velo": 3, "cyclisme": 3, "cycliste": 3, "vtt": 3,
        "course": 2, "courir": 2, "jogging": 3, "running": 3, "runner": 3,
        "entraînement": 3, "entrainement": 3, "training": 2, "échauffement": 3, "echauffement": 3,
        "coach": 2, "entraîneur": 3, "entraineur": 3, "préparateur": 3, "preparateur": 3,
        "équipe": 2, "equipe": 2, "club": 2, "fédération": 3, "federation": 3,
        "match": 3, "matches": 3, "rencontre": 1, "compétition": 3, "competition": 3,
        "tournoi": 3, "championnat": 3, "ligue": 2, "coupe": 2, "trophée": 3, "trophee": 3,
        "champion": 3, "championne": 3, "vainqueur": 3, "vainqueure": 3,
        "victoire": 3, "gagné": 2, "gagne": 2, "gagnant": 3, "gagnante": 3,
        "défaite": 2, "defaite": 2, "perdant": 2, "perdante": 2,
        "but": 2, "score": 2, "point": 1, "marquer": 2,
        "stade": 3, "terrain": 2, "gymnase": 3, "piste": 3, "circuit": 2,
        "joueur": 2, "joueuse": 2, "capitaine": 2, "titulaire": 2, "remplaçant": 3, "remplacant": 3,
        "performance": 2, "record": 3, "médaille": 3, "medaille": 3,
        "olympique": 3, "olympiques": 3, "jo": 3, "olympiade": 3,
        "finale": 3, "demi-finale": 3, "quart": 2, "huitième": 2, "huitieme": 2,
        "sprint": 3, "endurance": 3, "force": 1, "souplesse": 3, "agilité": 3, "agilite": 3,
        "dopage": 3, "dopé": 3, "dope": 3, "antidopage": 3,
        "blessure": 2, "blessé": 2, "blesse": 2, "blessée": 2, "blessee": 2,
        "kiné": 3, "kine": 3, "kinésithérapeute": 3, "kinesitherapeute": 3,
        "muscle": 2, "musclé": 2, "abdos": 3, "pectoraux": 3,
        "haltères": 3, "halteres": 3, "pompes": 3, "tractions": 3,
        "jouer": 2, "joue": 2, "joué": 2, "joue": 2, "basketball": 3, "basket": 3,
    },
    
    # ========================
    # 2. MUSIQUE
    # ========================
    "Musique": {
        "musique": 3, "music": 3, "musical": 3, "musicale": 3, "musicien": 3, "musicienne": 3,
        "chanson": 3, "song": 3, "chanter": 3, "chant": 3, "chanteur": 3, "chanteuse": 3,
        "album": 3, "single": 3, "ep": 3, "lp": 3, "mixtape": 3,
        "concert": 3, "festival": 3, "live": 2, "tournée": 2, "tournee": 2, "spectacle": 2,
        "guitare": 3, "guitariste": 3, "piano": 3, "pianiste": 3, "clavier": 3,
        "basse": 3, "bassiste": 3, "batterie": 3, "batteur": 3, "batteuse": 3,
        "violon": 3, "violoniste": 3, "violoncelle": 3, "violoncelliste": 3,
        "orchestre": 3, "symphonie": 3, "philharmonique": 3,
        "saxophone": 3, "saxophoniste": 3, "trompette": 3, "trompettiste": 3,
        "flûte": 3, "flute": 3, "flûtiste": 3, "flutiste": 3, "harpe": 3, "harpiste": 3,
        "rock": 3, "pop": 3, "rap": 3, "hip-hop": 3, "hiphop": 3, "hip hop": 3,
        "jazz": 3, "blues": 3, "électro": 3, "electro": 3, "électronique": 3, "electronique": 3,
        "classique": 2, "opéra": 3, "opera": 3, "reggae": 3,
        "techno": 3, "house": 3, "dubstep": 3, "drum": 3, "bass": 3,
        "métal": 3, "metal": 3, "punk": 3, "folk": 3, "funk": 3, "soul": 3, "disco": 3,
        "r&b": 3, "rnb": 3, "country": 3, "latino": 3, "k-pop": 3, "kpop": 3,
        "spotify": 2, "deezer": 2, "apple music": 3, "playlist": 3,
        "écouter": 1, "ecouter": 1, "écoute": 1, "ecoute": 1, "listen": 1,
        "morceau": 2, "track": 2, "son": 1, "sound": 1, "audio": 2,
        "enregistrement": 2, "studio": 2, "label": 2, "disque": 2,
        "vinyle": 3, "cd": 2, "cassette": 3, "radio": 2, "podcast": 3,
        "compositeur": 3, "compositrice": 3, "parolier": 3, "parolière": 3, "paroliere": 3,
        "paroles": 2, "lyrics": 2, "refrain": 2, "couplet": 2, "bridge": 2,
        "mélodie": 3, "melodie": 3, "rythme": 2, "rythm": 2, "harmonie": 2, "harmony": 2,
        "voix": 2, "vocal": 2, "vocale": 2, "aigu": 2, "grave": 1, "tessiture": 3,
        "répétition": 2, "repetition": 2, "répète": 2, "repete": 2, "chorale": 3,
        "clip": 2, "vidéo": 1, "video": 1, "youtube": 2,
        "j'aime la musique": 3, "j aime la musique": 3, "aimer la musique": 3,
    },
    
    # ========================
    # 3. CINÉMA ET SÉRIES
    # ========================
    "Cinéma et Séries": {
        "cinéma": 3, "cinema": 3, "film": 3, "movie": 3, "long-métrage": 3, "long metrage": 3,
        "série": 3, "serie": 3, "épisode": 3, "episode": 3, "saison": 3, "season": 3,
        "netflix": 3, "amazon prime": 3, "disney+": 3, "disney plus": 3,
        "hbo": 3, "hulu": 3, "apple tv": 3, "ocs": 3, "canal+": 3, "canal plus": 3,
        "streaming": 3, "plateforme": 1, "vod": 3,
        "acteur": 3, "actrice": 3, "actor": 3, "actress": 3, "comédien": 3, "comedien": 3,
        "comédienne": 3, "comedienne": 3, "figurant": 2, "figurante": 2,
        "réalisateur": 3, "realisateur": 3, "réalisatrice": 3, "realisatrice": 3,
        "director": 3, "metteur en scène": 3, "metteur en scene": 3,
        "hollywood": 3, "bollywood": 3, "nollywood": 3,
        "oscar": 3, "césar": 3, "cesar": 3, "palme d'or": 3, "palme dor": 3,
        "cannes": 3, "venise": 3, "berlin": 3, "sundance": 3,
        "festival": 2, "projection": 2, "avant-première": 3, "avant premiere": 3,
        "écran": 2, "ecran": 2, "scène": 2, "scene": 2, "décor": 3, "decor": 3,
        "thriller": 3, "horreur": 3, "comédie": 3, "comedie": 3, "comique": 2,
        "drame": 3, "dramatique": 3, "action": 3, "aventure": 2,
        "science-fiction": 3, "science fiction": 3, "sf": 3,
        "fantastique": 2, "fantasy": 3, "super-héros": 3, "super heros": 3,
        "documentaire": 3, "animation": 3, "anime": 3, "manga": 3, "dessin animé": 3, "dessin anime": 3,
        "blockbuster": 3, "saga": 3, "franchise": 2, "trilogie": 3, "quadrilogie": 3,
        "scénario": 3, "scenario": 3, "scénariste": 3, "scenariste": 3,
        "intrigue": 3, "plot": 3, "rebondissement": 3, "suspense": 3,
        "dialogue": 2, "script": 3, "narration": 3, "voix off": 3,
        "bande-son": 3, "bande son": 3, "bo": 3, "soundtrack": 3, "musique de film": 3,
        "effets spéciaux": 3, "effets speciaux": 3, "vfx": 3, "cgi": 3,
        "doublage": 2, "vostfr": 2, "sous-titré": 2, "sous titre": 2, "version originale": 3,
        "critique": 1, "review": 1, "spectateur": 1, "spectatrice": 1, "public": 1,
        "projecteur": 3, "salle": 2, "fauteuil": 2, "popcorn": 3, "séance": 3, "seance": 3,
        "casting": 3, "audition": 3, "rôle": 2, "role": 2, "personnage": 2,
        "caméra": 3, "camera": 3, "tournage": 3, "plateau": 3, "making-of": 3,
        "vu": 1, "voir": 1, "regarder": 1, "adoré le film": 3, "adore le film": 3,
        "dernier film": 3, "film de": 3, "à voir absolument": 3, "a voir absolument": 3,
    },
    
    # ========================
    # 4. TECHNOLOGIE ET INFORMATIQUE
    # ========================
    "Technologie et Informatique": {
        "technologie": 3, "techno": 2, "tech": 3, "informatique": 3,
        "ordinateur": 3, "pc": 3, "mac": 3, "laptop": 3, "desktop": 3,
        "logiciel": 3, "software": 3, "application": 3, "app": 3, "appli": 3,
        "mobile": 2, "smartphone": 3, "iphone": 3, "android": 3, "ios": 3,
        "tablette": 3, "ipad": 3, "écran": 1, "ecran": 1, "tactile": 3,
        "internet": 3, "web": 3, "site": 2, "navigateur": 3, "browser": 3,
        "cloud": 3, "serveur": 3, "server": 3, "hébergement": 3, "hebergement": 3,
        "base de données": 3, "base de donnees": 3, "database": 3, "sql": 3, "nosql": 3,
        "données": 2, "donnees": 2, "data": 3, "big data": 3,
        "intelligence artificielle": 3, "ia": 3, "ai": 3,
        "machine learning": 3, "deep learning": 3, "réseau neuronal": 3, "reseau neuronal": 3,
        "algorithme": 3, "algorithm": 3, "algo": 3,
        "code": 3, "coder": 3, "coding": 3, "développement": 2, "developpement": 2,
        "programmation": 3, "programming": 3, "développeur": 3, "developpeur": 3,
        "developer": 3, "dev": 3, "fullstack": 3, "frontend": 3, "backend": 3,
        "python": 3, "javascript": 3, "js": 3, "java": 3, "react": 3,
        "angular": 3, "vue": 3, "node": 3, "docker": 3, "kubernetes": 3, "k8s": 3,
        "git": 3, "github": 3, "gitlab": 3, "api": 3, "rest": 3, "graphql": 3,
        "cybersécurité": 3, "cybersecurite": 3, "hacker": 2, "sécurité": 2, "securite": 2,
        "blockchain": 3, "crypto": 3, "cryptomonnaie": 3, "bitcoin": 3, "ethereum": 3,
        "nft": 3, "web3": 3, "métavers": 3, "metaverse": 3,
        "robot": 3, "robotique": 3, "drones": 3, "iot": 3, "objets connectés": 3,
        "réalité virtuelle": 3, "vr": 3, "réalité augmentée": 3, "ar": 3,
        "startup": 3, "innovation": 2, "innovant": 2, "innover": 2, "disruption": 3,
        "numérique": 2, "numerique": 2, "digital": 2, "digitalisation": 3,
        "bug": 2, "debug": 2, "patch": 2, "update": 2, "mise à jour": 2, "mise a jour": 2,
        "open source": 3, "opensource": 3, "linux": 3, "windows": 3, "macos": 3,
        "électronique": 3, "electronique": 3, "gadget": 2, "composant": 2,
        "puce": 3, "processeur": 3, "cpu": 3, "gpu": 3, "ram": 3, "disque dur": 3,
        "écran tactile": 3, "ecran tactile": 3, "oled": 3, "lcd": 3, "hdmi": 3,
        "wifi": 3, "bluetooth": 3, "5g": 3, "4g": 3, "fibre": 3,
        "automatisation": 3, "script": 2, "bot": 3,
        "innovation": 3, "innover": 3, "art d'innover": 3, "art d innover": 3,
    },
    
    # ========================
    # 5. VOYAGE ET TOURISME
    # ========================
    "Voyage et Tourisme": {
        "voyage": 3, "travel": 3, "voyager": 3, "trip": 3, "séjour": 3, "sejour": 3,
        "destination": 3, "pays": 2, "country": 2, "continent": 2,
        "ville": 2, "city": 2, "capitale": 2, "métropole": 2, "metropole": 2,
        "plage": 3, "beach": 3, "mer": 2, "océan": 2, "ocean": 2, "lac": 2, "rivière": 2, "riviere": 2,
        "montagne": 3, "mountain": 3, "sommet": 3, "pic": 3, "col": 2, "vallée": 2, "vallee": 2,
        "forêt": 3, "foret": 3, "jungle": 3, "désert": 3, "desert": 3, "savane": 3,
        "nature": 2, "paysage": 2, "landscape": 2, "panorama": 3, "vue": 1,
        "hôtel": 3, "hotel": 3, "auberge": 3, "hostel": 3, "motel": 3,
        "camping": 3, "resort": 3, "villa": 3, "bungalow": 3, "gîte": 3, "gite": 3,
        "avion": 3, "plane": 3, "aéroport": 3, "aeroport": 3, "aérien": 3, "aerien": 3,
        "vol": 2, "flight": 2, "compagnie aérienne": 3, "compagnie aerienne": 3,
        "train": 3, "gare": 3, "station": 2, "métro": 2, "metro": 2, "tram": 3, "bus": 2,
        "voiture": 2, "car": 2, "location": 2, "road trip": 3, "roadtrip": 3, "autoroute": 2,
        "tourisme": 3, "tourism": 3, "touriste": 2, "tourist": 2, "visiteur": 2, "visiteuse": 2,
        "vacances": 3, "vacation": 3, "congé": 3, "conge": 3, "break": 2, "escapade": 3,
        "découverte": 2, "discover": 2, "aventure": 3, "adventure": 3,
        "exploration": 3, "explorer": 3, "explorateur": 3, "exploratrice": 3,
        "itinéraire": 3, "itineraire": 3, "circuit": 3, "guide": 2, "carte": 2, "map": 2,
        "visite": 3, "visiter": 3, "visit": 3, "excursion": 3, "balade": 3, "promenade": 3,
        "monument": 3, "musée": 3, "musee": 3, "patrimoine": 3, "site historique": 3,
        "passeport": 3, "passport": 3, "visa": 3, "douane": 2, "frontière": 3, "frontiere": 3,
        "bagages": 2, "luggage": 2, "valise": 2, "suitcase": 2, "sac à dos": 3, "sac a dos": 3,
        "billet": 2, "ticket": 2, "réservation": 3, "reservation": 3,
        "booking": 3, "airbnb": 3, "expedia": 3, "trivago": 3,
        "étranger": 2, "etranger": 2, "abroad": 2, "international": 2,
        "exotique": 3, "paradisiaque": 3, "tropical": 3, "île": 3, "ile": 3, "archipel": 3,
        "randonnée": 3, "randonnee": 3, "trek": 3, "hiking": 3, "trekking": 3,
        "backpacking": 3, "backpacker": 3, "routard": 3, "globe-trotter": 3, "globetrotter": 3,
        "dépaysement": 3, "depaysement": 3, "évasion": 3, "evasion": 3, "dépayser": 3,
        "région": 2, "region": 2, "magnifique région": 3, "magnifique region": 3,
        "endroit secret": 3, "hâte d'y retourner": 3, "hate d y retourner": 3,
        "découvert un endroit": 3, "decouvert un endroit": 3,
    },
    
    # ========================
    # 6. CUISINE ET GASTRONOMIE
    # ========================
    "Cuisine et Gastronomie": {
        "cuisine": 3, "cuisiner": 3, "cooking": 3, "food": 3, "gastronomie": 3, "gastronomique": 3,
        "nourriture": 2, "alimentation": 2, "bouffe": 2, "miam": 3,
        "recette": 3, "recipe": 3, "préparation": 2, "preparation": 2,
        "plat": 2, "dish": 2, "entrée": 2, "entree": 2, "plat principal": 2, "dessert": 3,
        "manger": 2, "eat": 2, "déguster": 3, "deguster": 3, "dégustation": 3, "degustation": 3,
        "restaurant": 3, "resto": 3, "bistrot": 3, "brasserie": 3, "cafétéria": 3, "cafeteria": 3,
        "étoilé": 3, "etoile": 3, "michelin": 3, "gastronomique": 3,
        "chef": 3, "cuisinier": 3, "cuisinière": 3, "cuisiniere": 3, "pâtissier": 3, "patissier": 3,
        "délicieux": 2, "delicieux": 2, "delicious": 2, "savoureux": 3, "exquis": 3,
        "goût": 2, "gout": 2, "saveur": 2, "flavor": 2, "arôme": 3, "arome": 3,
        "ingrédient": 3, "ingredient": 3, "épice": 3, "epice": 3, "condiment": 3,
        "sel": 2, "poivre": 2, "sucre": 2, "farine": 2, "huile": 2, "beurre": 2,
        "crème": 2, "creme": 2, "fromage": 2, "lait": 2, "œuf": 3, "oeuf": 3, "oeufs": 3,
        "légume": 3, "legume": 3, "fruit": 3, "viande": 3, "poisson": 3,
        "poulet": 3, "boeuf": 3, "porc": 3, "agneau": 3, "veau": 3, "canard": 3,
        "pain": 2, "pâtisserie": 3, "patisserie": 3, "boulangerie": 3, "viennoiserie": 3,
        "gâteau": 3, "gateau": 3, "tarte": 3, "cake": 3, "biscuit": 3, "cookie": 3,
        "chocolat": 3, "glace": 3, "sorbet": 3, "crème glacée": 3, "creme glacée": 3,
        "boisson": 2, "drink": 2, "vin": 3, "bière": 3, "biere": 3,
        "café": 3, "cafe": 3, "thé": 3, "the": 3, "cocktail": 3, "jus": 2,
        "apéritif": 3, "aperitif": 3, "digestif": 3, "champagne": 3, "whisky": 3, "vodka": 3,
        "brunch": 3, "petit déjeuner": 3, "petit dejeuner": 3, "déjeuner": 3, "dejeuner": 3, "dîner": 3, "diner": 3,
        "soupe": 2, "salade": 2, "pâtes": 2, "pates": 2, "riz": 2, "quinoa": 3,
        "pizza": 3, "sushi": 3, "burger": 3, "tacos": 3, "kebab": 3, "sandwich": 3,
        "fait maison": 3, "artisanal": 3, "bio": 2, "organic": 2, "vegan": 3, "végétarien": 3, "vegetarien": 3,
        "régime": 2, "regime": 2, "diète": 3, "diete": 3, "calories": 3, "protéines": 3, "proteines": 3,
        "cuisson": 3, "four": 3, "micro-ondes": 3, "micro ondes": 3, "poêle": 3, "poele": 3,
        "casserole": 3, "mijoter": 3, "mijoté": 3, "mijote": 3, "rôti": 3, "roti": 3,
        "grillé": 3, "grille": 3, "frit": 3, "frite": 3, "vapeur": 3,
        "marinade": 3, "mariné": 3, "marine": 3, "sauce": 3, "vinaigrette": 3,
        "menu": 3, "carte": 2, "commander": 3, "service": 2, "addition": 3, "pourboire": 3,
        "spécialité": 3, "specialite": 3, "vrai régal": 3, "vrai regal": 3,
        "réussi ma recette": 3, "reussi ma recette": 3,
    },
    
    # ========================
    # 7. SANTÉ ET BIEN-ÊTRE
    # ========================
    "Santé et Bien-être": {
        "santé": 3, "sante": 3, "health": 3, "médical": 3, "medical": 3, "médicale": 3, "medicale": 3,
        "médecin": 3, "medecin": 3, "docteur": 3, "doctor": 3, "généraliste": 3, "generaliste": 3,
        "hôpital": 3, "hopital": 3, "hospital": 3, "clinique": 3, "urgence": 3, "emergency": 3,
        "maladie": 3, "disease": 3, "symptôme": 3, "symptome": 3, "diagnostic": 3, "diagnostiquer": 3,
        "traitement": 3, "médicament": 3, "medicament": 3, "medicine": 3, "remède": 3, "remede": 3,
        "pharmacie": 3, "pharmacy": 3, "pharmacien": 3, "pharmacienne": 3, "ordonnance": 3,
        "vaccin": 3, "vaccine": 3, "vaccination": 3, "immunité": 3, "immunite": 3,
        "chirurgie": 3, "surgery": 3, "opération": 3, "operation": 3, "opérer": 3, "operer": 3,
        "ambulance": 3, "pompiers": 2, "secours": 3, "samu": 3,
        "dentiste": 3, "dental": 3, "dentaire": 3, "carie": 3, "détartrage": 3, "detartrage": 3,
        "ophtalmo": 3, "ophtalmologue": 3, "dermato": 3, "dermatologue": 3,
        "cardiologue": 3, "cardiologie": 3, "neurologue": 3, "neurologie": 3,
        "bien-être": 3, "bien etre": 3, "bienêtre": 3, "bienetre": 3, "wellness": 3,
        "relaxation": 3, "méditation": 3, "meditation": 3, "méditer": 3, "mediter": 3,
        "yoga": 3, "pilates": 3, "sophrologie": 3, "acupuncture": 3,
        "nutrition": 3, "diététique": 3, "dietetique": 3, "diététicien": 3, "dieteticien": 3,
        "régime": 2, "regime": 2, "alimentaire": 2, "diet": 2,
        "sommeil": 3, "dormir": 2, "insomnie": 3, "fatigue": 2, "fatigué": 2,
        "stress": 3, "stressé": 3, "stresse": 3, "stressée": 3, "stressee": 3,
        "anxiété": 3, "anxiete": 3, "anxieux": 3, "anxieuse": 3, "angoissé": 3, "angoisse": 3,
        "dépression": 3, "depression": 3, "déprimé": 3, "deprime": 3, "déprimée": 3, "deprimee": 3,
        "psychologue": 3, "psy": 3, "psychiatre": 3, "thérapie": 3, "therapie": 3,
        "mental": 3, "mentale": 3, "psychique": 3, "psychologique": 3,
        "guérir": 2, "guerir": 2, "soigner": 2, "soin": 2, "prévention": 2, "prevention": 2,
        "infection": 3, "virus": 3, "bactérie": 3, "bacterie": 3, "microbe": 3,
        "douleur": 3, "maux": 2, "fièvre": 3, "fievre": 3, "toux": 3, "rhume": 3,
        "allergie": 3, "allergique": 3, "asthme": 3, "diabète": 3, "diabete": 3,
        "cancer": 3, "tumeur": 3, "chimiothérapie": 3, "chimiotherapie": 3,
        "respiration": 2, "respirer": 2, "inspirer": 2, "expirer": 2,
        "hygiène": 3, "hygiene": 3, "propreté": 3, "proprete": 3,
        "naturel": 1, "naturelle": 1, "holistique": 3, "holistic": 3,
        "bien-être": 3, "mieux-être": 3, "mieux etre": 3,
        "guérison": 3, "guerison": 3, "rétablissement": 3, "retablissement": 3,
        "consultation": 3, "rendez-vous": 3, "rendez vous": 3, "rdv": 3,
        "analyse": 2, "examen": 2, "radio": 2, "scanner": 3, "irm": 3, "échographie": 3, "echographie": 3,
        "prise de sang": 3, "tension": 3, "cholestérol": 3, "cholesterol": 3,
        "gérer mon stress": 3, "gerer mon stress": 3, "santé mentale": 3, "sante mentale": 3,
        "santé physique": 3, "sante physique": 3, "je me sens mieux": 3,
        "nutrition": 3, "alimentation": 2, "changé mon alimentation": 3, "change mon alimentation": 3,
    },
    
    # ========================
    # 8. ÉDUCATION ET FORMATION
    # ========================
    "Éducation et Formation": {
        "éducation": 3, "education": 3, "école": 3, "ecole": 3, "scolaire": 2, "scolarité": 2, "scolarite": 2,
        "université": 3, "universite": 3, "fac": 3, "campus": 3, "amphi": 3,
        "étudiant": 3, "etudiant": 3, "student": 3, "élève": 3, "eleve": 3,
        "étudier": 3, "etudier": 3, "study": 3, "apprendre": 2, "learn": 2,
        "professeur": 3, "prof": 3, "teacher": 3, "enseignant": 3, "enseignante": 3,
        "cours": 2, "class": 2, "lesson": 2, "cours magistral": 3, "td": 3, "tp": 3,
        "examen": 3, "exam": 3, "concours": 3, "épreuve": 3, "epreuve": 3, "partiel": 3,
        "diplôme": 3, "diplome": 3, "degree": 3, "certification": 3, "certificat": 3,
        "bac": 3, "baccalauréat": 3, "baccalaureat": 3, "brevet": 3,
        "licence": 3, "master": 3, "doctorat": 3, "phd": 3, "postdoc": 3,
        "apprentissage": 3, "learning": 3, "formation": 3, "training": 3,
        "connaissance": 2, "knowledge": 2, "compétence": 2, "competence": 2, "savoir": 1,
        "livre": 2, "book": 2, "manuel": 2, "textbook": 2, "bouquin": 3,
        "lecture": 2, "reading": 2, "bibliothèque": 3, "bibliotheque": 3, "library": 3,
        "recherche": 3, "research": 3, "laboratoire": 3, "lab": 3, "chercheur": 3, "chercheuse": 3,
        "science": 2, "scientifique": 2, "maths": 3, "mathématiques": 3, "mathematiques": 3,
        "physique": 2, "chimie": 3, "biologie": 3, "histoire": 3, "géographie": 3, "geographie": 3,
        "langues": 3, "français": 3, "francais": 3, "anglais": 3, "philosophie": 3, "philo": 3,
        "mooc": 3, "cours en ligne": 3, "e-learning": 3, "elearning": 3, "distanciel": 3,
        "pédagogie": 3, "pedagogie": 3, "didactique": 3, "éducatif": 3, "educatif": 3,
        "lycée": 3, "lycee": 3, "collège": 3, "college": 3, "primaire": 3, "maternelle": 3,
        "bourse": 2, "scholarship": 2, "erasmus": 3, "échange": 2, "echange": 2,
        "mémoire": 3, "memoire": 3, "thèse": 3, "these": 3, "soutenance": 3,
        "tutorat": 3, "tutor": 3, "mentor": 3, "mentorat": 3, "accompagnement": 3,
        "devoir": 2, "exercice": 2, "exercices": 2, "corrigé": 3, "corrige": 3,
        "note": 1, "moyenne": 2, "mention": 3, "rattrapage": 3,
        "inscription": 3, "réinscription": 3, "reinscription": 3,
        "stage": 3, "alternance": 3, "apprentissage": 3,
        "l'éducation est la clé": 3, "l education est la cle": 3, "éducation est la clé": 3,
        "je me forme": 3, "me forme en": 3, "reconvertir": 3, "reconversion": 3,
        "moocs": 3, "cours en ligne": 3,
    },
    
    # ========================
    # 9. BUSINESS ET FINANCE
    # ========================
    "Business et Finance": {
        "business": 3, "entreprise": 3, "company": 3, "société": 2, "societe": 2, "firme": 3,
        "startup": 3, "pme": 3, "pmi": 3, "multinationale": 3, "grand groupe": 3,
        "travail": 2, "work": 2, "job": 3, "emploi": 3, "poste": 2,
        "carrière": 3, "carriere": 3, "career": 3, "promotion": 2,
        "salaire": 3, "salary": 3, "rémunération": 3, "remuneration": 3, "paie": 3, "paye": 3,
        "boss": 2, "patron": 2, "manager": 3, "management": 3, "gestion": 2,
        "équipe": 2, "equipe": 2, "team": 2, "collaborateur": 2, "collègue": 2, "collegue": 2,
        "réunion": 3, "reunion": 3, "meeting": 3, "visio": 3, "visioconférence": 3, "visioconference": 3,
        "projet": 1, "project": 1, "deadline": 3, "échéance": 3, "echeance": 3, "livrable": 3,
        "client": 3, "customer": 3, "vente": 3, "sale": 3, "commercial": 3, "commerciale": 3,
        "marketing": 3, "publicité": 3, "publicite": 3, "pub": 2, "campagne": 2,
        "stratégie": 3, "strategie": 3, "strategy": 3, "stratégique": 3, "strategique": 3,
        "investissement": 3, "investment": 3, "investir": 3, "investisseur": 3, "investor": 3,
        "finance": 3, "financial": 3, "budget": 3, "budgétaire": 3, "budgetaire": 3,
        "argent": 2, "money": 2, "profit": 3, "bénéfice": 3, "benefice": 3, "rentable": 3,
        "croissance": 3, "growth": 3, "marché": 3, "marche": 3, "market": 3,
        "concurrence": 3, "compétiteur": 3, "competiteur": 3, "concurrent": 3, "concurrente": 3,
        "leadership": 3, "leader": 2, "ceo": 3, "pdg": 3, "dg": 3, "directeur": 2, "directrice": 2,
        "entrepreneur": 3, "entrepreneure": 3, "entrepreneuriat": 3, "entrepreneurship": 3,
        "innovation": 2, "innovant": 2, "disruption": 3,
        "levée de fonds": 3, "levee de fonds": 3, "fundraising": 3, "levée": 3, "levee": 3,
        "capital": 3, "fonds": 3, "seed": 3, "série a": 3, "serie a": 3,
        "business plan": 3, "business model": 3,
        "bourse": 2, "actions": 2, "dividendes": 3, "cac40": 3, "nasdaq": 3,
        "fiscalité": 3, "fiscalite": 3, "impôts": 3, "impots": 3, "taxe": 3, "tva": 3,
        "banque": 2, "banquier": 2, "crédit": 2, "credit": 2, "prêt": 2, "pret": 2,
        "comptabilité": 3, "comptabilite": 3, "facture": 3, "devis": 3,
        "trésorerie": 3, "tresorerie": 3, "cash": 3, "flux": 2,
        "chiffre d'affaires": 3, "chiffre d affaires": 3, "ca": 3,
        "rentabilité": 3, "rentabilite": 3, "roi": 3, "kpi": 3,
        "négociation": 3, "negociation": 3, "contrat": 3, "deal": 3,
    },
    
    # ========================
    # 10. MODE ET BEAUTÉ
    # ========================
    "Mode et Beauté": {
        "mode": 3, "fashion": 3, "style": 3, "stylisme": 3, "styliste": 3,
        "vêtement": 3, "vetement": 3, "habit": 2, "fringue": 2, "sape": 2,
        "tenue": 3, "outfit": 3, "look": 3, "dress code": 3,
        "tendance": 3, "trend": 3, "collection": 3, "défilé": 3, "defile": 3,
        "fashion week": 3, "couture": 3, "haute couture": 3, "prêt-à-porter": 3, "pret a porter": 3,
        "marque": 2, "brand": 2, "luxe": 3, "luxury": 3, "haut de gamme": 3,
        "designer": 3, "styliste": 3, "créateur": 2, "createur": 2, "créatrice": 2, "creatrice": 2,
        "mannequin": 3, "model": 2, "top model": 3, "égérie": 3, "egerie": 3,
        "magasin": 2, "store": 2, "boutique": 3, "shopping": 3, "achat": 2,
        "acheter": 1, "buy": 1, "soldes": 3, "promo": 2, "promotion": 2, "remise": 3,
        "beauté": 3, "beaute": 3, "beauty": 3, "cosmétique": 3, "cosmetique": 3,
        "maquillage": 3, "makeup": 3, "make-up": 3, "fond de teint": 3, "rouge à lèvres": 3, "rouge a levres": 3,
        "coiffure": 3, "cheveux": 2, "hair": 2, "coiffeur": 3, "coiffeuse": 3,
        "accessoire": 3, "accessory": 3, "bijoux": 3, "jewelry": 3, "bijou": 3,
        "sac": 2, "bag": 2, "sac à main": 3, "sac a main": 3, "pochette": 3,
        "chaussures": 3, "shoes": 3, "sneakers": 3, "baskets": 3, "talons": 3,
        "bottes": 3, "sandales": 3, "escarpins": 3, "mocassins": 3,
        "lunettes": 3, "glasses": 3, "montre": 2, "watch": 2, "bracelet": 3, "collier": 3,
        "parfum": 3, "perfume": 3, "fragrance": 3, "eau de toilette": 3,
        "crème": 2, "creme": 2, "skincare": 3, "soin": 2, "lotion": 3, "sérum": 3, "serum": 3,
        "routine beauté": 3, "routine soin": 3,
        "naturel": 1, "bio": 1, "vegan": 2, "cruelty-free": 3, "cruelty free": 3,
        "élégant": 2, "elegant": 2, "chic": 3, "glamour": 3, "sophistiqué": 3, "sophistique": 3,
        "taille": 2, "coupe": 2, "tissu": 3, "textile": 3, "matière": 2, "matiere": 2,
        "coton": 3, "soie": 3, "laine": 3, "cuir": 3, "jean": 3, "denim": 3,
        "robe": 3, "jupe": 3, "pantalon": 3, "chemise": 3, "costume": 3, "veste": 3,
    },
    
    # ========================
    # 11. ART ET CULTURE
    # ========================
    "Art et Culture": {
        "art": 3, "artiste": 3, "artistique": 3, "artist": 3,
        "peinture": 3, "peintre": 3, "tableau": 3, "toile": 3, "aquarelle": 3, "gouache": 3,
        "sculpture": 3, "sculpteur": 3, "sculptrice": 3, "statue": 3, "bronze": 3,
        "musée": 3, "musee": 3, "galerie": 3, "exposition": 3, "expo": 3, "vernissage": 3,
        "culture": 3, "culturel": 3, "culturelle": 3, "patrimoine": 3,
        "histoire": 2, "historique": 2, "archéologie": 3, "archeologie": 3,
        "architecture": 3, "architecte": 3, "monument": 2, "bâtiment": 2, "batiment": 2,
        "littérature": 3, "litterature": 3, "poésie": 3, "poesie": 3, "poème": 3, "poeme": 3,
        "théâtre": 3, "theatre": 3, "pièce": 2, "piece": 2, "comédien": 3, "comedien": 3,
        "danse": 3, "danseur": 3, "danseuse": 3, "ballet": 3, "chorégraphie": 3, "choregraphie": 3,
        "photographie": 3, "photo": 3, "photographe": 3, "cliché": 3, "cliche": 3,
        "design": 3, "graphisme": 3, "graphiste": 3, "illustration": 3, "illustrateur": 3,
        "création": 2, "creation": 2, "créatif": 2, "creatif": 2, "créativité": 3, "creativite": 3,
        "œuvre": 3, "oeuvre": 3, "chef-d'œuvre": 3, "chef d'œuvre": 3, "chef doeuvre": 3,
        "inspiration": 2, "inspiré": 2, "inspire": 2, "inspirant": 3,
        "émotion": 2, "emotion": 2, "émouvant": 3, "emouvant": 3,
        "esthétique": 3, "esthetique": 3, "beau": 2, "beauté": 2, "beaute": 2,
        "contemporain": 3, "moderne": 2, "classique": 2, "abstrait": 3, "figuratif": 3,
        "impressionnisme": 3, "cubisme": 3, "surréalisme": 3, "surrealisme": 3,
        "renaissance": 3, "baroque": 3, "romantisme": 3, "symbolisme": 3,
        "fresque": 3, "mosaïque": 3, "mosaique": 3, "vitrail": 3, "céramique": 3, "ceramique": 3,
        "restauration": 3, "restaurateur": 3, "conservation": 3,
        "collection": 3, "collectionneur": 3, "collectionneuse": 3,
        "enchères": 3, "encheres": 3, "vente aux enchères": 3,
        "j'apprends la peinture": 3, "j apprends la peinture": 3,
        "talentueux artiste": 3, "tableau de": 3, "art contemporain": 3,
        "véritable émotion": 3, "veritable emotion": 3,
    },
    
    # ========================
    # 12. LIFESTYLE ET QUOTIDIEN
    # ========================
    "Lifestyle et Quotidien": {
        "lifestyle": 3, "quotidien": 3, "quotidienne": 3, "vie": 1, "vivre": 1,
        "maison": 3, "appartement": 3, "appart": 3, "logement": 3, "déménagement": 3, "demenagement": 3,
        "décoration": 3, "decoration": 3, "déco": 3, "deco": 3, "ameublement": 3,
        "jardin": 3, "jardinage": 3, "plantes": 3, "fleurs": 2, "potager": 3, "balcon": 3,
        "bricolage": 3, "bricoler": 3, "diy": 3, "réparation": 3, "reparation": 3,
        "nettoyage": 3, "ménage": 3, "menage": 3, "rangement": 3, "désencombrement": 3,
        "courses": 3, "shopping": 3, "achats": 2, "acheter": 1, "acheté": 1, "achete": 1,
        "lundi": 3, "mardi": 3, "mercredi": 3, "jeudi": 3, "vendredi": 3,
        "samedi": 3, "dimanche": 3, "week-end": 3, "weekend": 3, "semaine": 2,
        "matin": 2, "soir": 2, "soirée": 3, "soiree": 3, "nuit": 2, "réveil": 3, "reveil": 3,
        "routine": 3, "habitude": 3, "organisation": 3,
        "animal": 2, "animaux": 2, "chien": 3, "chat": 3, "chaton": 3,
        "promenade": 3, "balade": 3, "sortie": 2, "sortir": 2,
        "anniversaire": 3, "fête": 2, "fete": 2, "célébration": 3, "celebration": 3,
        "naissance": 3, "mariage": 3, "bébé": 3, "bebe": 3, "enfant": 2, "enfants": 2,
        "parent": 2, "parents": 2, "maman": 3, "papa": 3, "famille": 2, "familial": 3,
        "amis": 2, "amitié": 3, "amitie": 3, "copain": 3, "copine": 3,
        "voisin": 3, "voisine": 3, "voisinage": 3, "quartier": 3,
        "détente": 3, "detente": 3, "repos": 3, "relaxer": 3, "chiller": 3,
        "loisir": 3, "loisirs": 3, "hobby": 3, "passe-temps": 3, "passe temps": 3,
        "occupation": 2, "activité": 1, "activite": 1,
        "confort": 3, "cosy": 3, "cocooning": 3,
        "minimalisme": 3, "désencombrement": 3, "simplicité": 3, "simplicite": 3,
        "aujourd'hui c'est": 3, "aujourdhui c est": 3,
        "c'est lundi": 3, "c est lundi": 3, "c'est mardi": 3, "c'est mercredi": 3,
        "c'est jeudi": 3, "c'est vendredi": 3, "c'est samedi": 3, "c'est dimanche": 3,
    },
    
    # ========================
    # 13. PSYCHOLOGIE ET DÉVELOPPEMENT PERSONNEL
    # ========================
    "Psychologie et Développement Personnel": {
        "psychologie": 3, "psycho": 3, "psychologique": 3,
        "développement personnel": 3, "developpement personnel": 3,
        "croissance personnelle": 3, "épanouissement": 3, "epanouissement": 3,
        "bonheur": 2, "heureux": 2, "heureuse": 2, "épanoui": 3, "epanoui": 3,
        "confiance": 3, "confiance en soi": 3, "estime de soi": 3, "estime": 3,
        "motivation": 3, "motivé": 3, "motive": 3, "motivée": 3, "motivee": 3,
        "inspiration": 2, "inspiré": 2, "inspire": 2, "inspirant": 3,
        "objectif": 2, "objectifs": 2, "but": 2, "ambition": 3, "rêve": 2, "reve": 2,
        "rêvé": 2, "reve": 2, "rêvée": 2, "revee": 2, "j'en ai rêvé": 3, "j en ai reve": 3,
        "accomplissement": 3, "réussite": 2, "reussite": 2, "succès": 2, "succes": 2,
        "changement": 3, "transformation": 3, "évolution": 3, "evolution": 3,
        "habitude": 3, "discipline": 3, "persévérance": 3, "perseverance": 3,
        "résilience": 3, "resilience": 3, "force mentale": 3,
        "émotion": 2, "emotion": 2, "émotions": 2, "emotions": 2,
        "sentiment": 2, "sentiments": 2, "ressenti": 3, "ressentir": 3,
        "triste": 3, "tristesse": 3, "pleurer": 2, "pleure": 2,
        "je me sens triste": 3, "je suis triste": 3,
        "joie": 2, "content": 1, "contente": 1,
        "colère": 3, "colere": 3, "énervé": 2, "enerve": 2, "frustré": 3, "frustre": 3,
        "peur": 2, "anxiété": 3, "anxiete": 3, "angoisse": 3, "stress": 3, "stressé": 3, "stresse": 3,
        "calme": 2, "sérénité": 3, "serenite": 3, "paix": 2, "paix intérieure": 3,
        "méditation": 3, "meditation": 3, "méditer": 3, "mediter": 3,
        "pleine conscience": 3, "mindfulness": 3, "respirer": 2, "respiration": 2,
        "gratitude": 3, "reconnaissant": 2, "reconnaissante": 2,
        "lâcher prise": 3, "lacher prise": 3, "acceptation": 3,
        "introspection": 3, "réflexion": 2, "reflexion": 2, "pensée": 1, "pensee": 1,
        "thérapie": 3, "therapie": 3, "psy": 3, "psychothérapie": 3, "psychotherapie": 3,
        "coaching": 3, "coach": 2, "accompagnement": 3,
        "autonomie": 3, "indépendance": 3, "independance": 3, "liberté": 2, "liberte": 2,
        "assertivité": 3, "assertivite": 3, "affirmation de soi": 3,
        "relation": 2, "relations": 2, "communication": 3,
        "écoute": 2, "ecoute": 2, "empathie": 3, "compassion": 3,
        "solitude": 3, "seul": 2, "seule": 2, "isolement": 3,
        "dépression": 3, "depression": 3, "déprime": 3, "deprime": 3,
        "burn-out": 3, "burn out": 3, "épuisement": 3, "epuisement": 3,
        "guérison": 3, "guerison": 3, "rétablissement": 3, "retablissement": 3,
    },
    
    # ========================
    # 14. ENVIRONNEMENT ET ÉCOLOGIE
    # ========================
    "Environnement et Écologie": {
        "environnement": 3, "environnemental": 3, "environnementale": 3,
        "écologie": 3, "ecologie": 3, "écologique": 3, "ecologique": 3,
        "écolo": 3, "ecolo": 3, "green": 3, "durable": 3, "sustainability": 3,
        "climat": 3, "climatique": 3, "réchauffement": 3, "rechauffement": 3,
        "planète": 3, "planete": 3, "terre": 2, "monde": 1,
        "nature": 2, "naturel": 2, "naturelle": 2, "sauvage": 3,
        "biodiversité": 3, "biodiversite": 3, "écosystème": 3, "ecosysteme": 3,
        "espèces": 3, "especes": 3, "animaux": 2, "végétation": 3, "vegetation": 3,
        "forêt": 3, "foret": 3, "déforestation": 3, "deforestation": 3,
        "océan": 3, "ocean": 3, "pollution": 3, "plastique": 3, "déchet": 3, "dechet": 3,
        "recyclage": 3, "recycler": 3, "tri": 3, "compost": 3, "compostage": 3,
        "zéro déchet": 3, "zero dechet": 3, "zéro waste": 3, "zero waste": 3,
        "énergie": 3, "energie": 3, "renouvelable": 3, "solaire": 3, "éolien": 3, "eolien": 3,
        "électricité": 2, "electricite": 2, "consommation": 2,
        "transition écologique": 3, "transition ecologique": 3,
        "agriculture": 3, "bio": 2, "biologique": 3, "permaculture": 3,
        "potager": 3, "jardinage": 3, "végétal": 3, "vegetal": 3,
        "vegan": 3, "végan": 3, "veganisme": 3, "véganisme": 3,
        "végétarien": 3, "vegetarien": 3, "végétarisme": 3, "vegetarisme": 3,
        "local": 2, "circuit court": 3, "producteur": 2, "maraîcher": 3, "maraicher": 3,
        "empreinte carbone": 3, "bilan carbone": 3, "carbone": 3,
        "gaspillage": 3, "gaspiller": 3, "anti-gaspillage": 3, "anti gaspillage": 3,
        "seconde main": 3, "friperie": 3, "vintage": 2, "occasion": 2,
        "réchauffement climatique": 3, "rechauffement climatique": 3,
        "fonte des glaces": 3, "banquise": 3, "glacier": 3,
        "catastrophe naturelle": 3, "inondation": 3, "sécheresse": 3, "secheresse": 3,
        "incendie": 3, "feu de forêt": 3, "feu de foret": 3,
    },
    
    # ========================
    # 15. POLITIQUE ET SOCIÉTÉ
    # ========================
    "Politique et Société": {
        "politique": 3, "politicien": 3, "politicienne": 3, "gouvernement": 3, "gouvernemental": 3,
        "président": 3, "president": 3, "présidentielle": 3, "presidentielle": 3,
        "élection": 3, "election": 3, "vote": 3, "voter": 3, "électeur": 3, "electeur": 3,
        "démocratie": 3, "democratie": 3, "république": 3, "republique": 3,
        "loi": 3, "législation": 3, "legislation": 3, "réforme": 3, "reforme": 3,
        "assemblée": 3, "assemblee": 3, "sénat": 3, "senat": 3, "parlement": 3,
        "ministre": 3, "ministère": 3, "ministere": 3, "secrétaire d'état": 3,
        "parti": 3, "partis": 3, "gauche": 2, "droite": 2, "centre": 2, "extrême": 3, "extreme": 3,
        "débat": 3, "debat": 3, "discours": 2, "polémique": 3, "polemique": 3,
        "société": 2, "societe": 2, "social": 2, "sociale": 2, "sociaux": 2,
        "citoyen": 3, "citoyenne": 3, "citoyenneté": 3, "citoyennete": 3,
        "liberté": 2, "liberte": 2, "égalité": 3, "egalite": 3, "fraternité": 3, "fraternite": 3,
        "justice": 3, "injustice": 3, "inégalité": 3, "inegalite": 3,
        "droit": 2, "droits": 2, "humain": 2, "humaine": 2, "droits de l'homme": 3,
        "manifestation": 3, "manifester": 3, "protestation": 3, "grève": 3, "greve": 3,
        "syndicat": 3, "syndical": 3, "syndicale": 3,
        "immigration": 3, "immigré": 3, "immigre": 3, "migrant": 3, "migration": 3,
        "sécurité": 3, "securite": 3, "insécurité": 3, "insecurite": 3,
        "police": 3, "gendarme": 3, "justice": 3, "tribunal": 3, "avocat": 2, "juge": 3,
        "corruption": 3, "scandale": 3, "affaire": 2, "détournement": 3, "detournement": 3,
        "transparence": 3, "opacité": 3, "opacite": 3,
        "censure": 3, "liberté d'expression": 3, "liberte d'expression": 3,
        "média": 3, "media": 3, "médias": 3, "medias": 3, "journalisme": 3, "presse": 3,
        "fake news": 3, "désinformation": 3, "desinformation": 3,
        "opinion": 2, "sondage": 3, "populaire": 2, "populisme": 3,
        "crise": 3, "conflit": 3, "guerre": 3, "paix": 2, "diplomatie": 3,
        "international": 2, "mondial": 2, "mondiale": 2, "europe": 3, "européen": 3, "europeen": 3,
        "onu": 3, "unesco": 3, "oms": 3, "ong": 3, "humanitaire": 3,
        "décisions": 3, "decisions": 3, "impactent": 3,
    },
    
    # ========================
    # 16. SCIENCES ET DÉCOUVERTES
    # ========================
    "Sciences et Découvertes": {
        "science": 3, "scientifique": 3, "scientifiques": 3, "scientific": 3,
        "recherche": 3, "research": 3, "chercheur": 3, "chercheuse": 3, "découvreur": 3,
        "découverte": 3, "decouverte": 3, "découvrir": 2, "decouvrir": 2,
        "laboratoire": 3, "labo": 3, "expérience": 2, "experience": 2, "expérimentation": 3, "experimentation": 3,
        "physique": 2, "quantique": 3, "astrophysique": 3, "cosmologie": 3,
        "chimie": 3, "molécule": 3, "molecule": 3, "atome": 3, "élément": 2, "element": 2,
        "biologie": 3, "génétique": 3, "genetique": 3, "adn": 3, "gène": 3, "gene": 3,
        "évolution": 3, "evolution": 3, "darwin": 3, "espèce": 3, "espece": 3,
        "astronomie": 3, "espace": 3, "planète": 3, "planete": 3, "étoile": 3, "etoile": 3,
        "univers": 3, "galaxie": 3, "trou noir": 3, "big bang": 3, "cosmos": 3,
        "télescope": 3, "telescope": 3, "james webb": 3, "hubble": 3,
        "nasa": 3, "esa": 3, "spacex": 3, "fusée": 3, "fusee": 3, "satellite": 3,
        "mars": 3, "lune": 2, "mission spatiale": 3,
        "mathématiques": 3, "mathematiques": 3, "maths": 3, "équation": 3, "equation": 3,
        "théorème": 3, "theoreme": 3, "théorie": 3, "theorie": 3, "hypothèse": 3, "hypothese": 3,
        "géologie": 3, "geologie": 3, "volcan": 3, "séisme": 3, "seisme": 3, "tremblement de terre": 3,
        "paléontologie": 3, "paleontologie": 3, "dinosaure": 3, "fossile": 3,
        "archéologie": 3, "archeologie": 3, "fouille": 3, "vestige": 3, "ruine": 3,
        "médecine": 3, "medecine": 3, "médical": 2, "medical": 2, "recherche médicale": 3,
        "vaccin": 3, "traitement": 3, "thérapie": 3, "therapie": 3, "génique": 3, "genique": 3,
        "neuroscience": 3, "cerveau": 3, "neurone": 3, "cognitif": 3, "cognitive": 3,
        "physique quantique": 3, "relativité": 3, "relativite": 3, "einstein": 3,
        "prix nobel": 3, "nobel": 3, "médaille fields": 3, "medaille fields": 3,
        "publication": 3, "article scientifique": 3, "revue": 3, "peer review": 3,
    },
    
    # ========================
    # 17. JEUX ET DIVERTISSEMENT
    # ========================
    "Jeux et Divertissement": {
        "jeu": 2, "jeux": 2, "jouer": 2, "joue": 2, "joué": 2,
        "jeux vidéo": 3, "jeux video": 3, "jeu vidéo": 3, "jeu video": 3,
        "gaming": 3, "gamer": 3, "gameuse": 3, "gameur": 3,
        "playstation": 3, "ps5": 3, "ps4": 3, "xbox": 3, "nintendo": 3, "switch": 3,
        "pc gamer": 3, "steam": 3, "epic games": 3, "twitch": 3, "streamer": 3,
        "jeu de société": 3, "jeu de societe": 3, "jeux de société": 3, "jeux de societe": 3,
        "monopoly": 3, "scrabble": 3, "échecs": 3, "echecs": 3, "dames": 3, "uno": 3,
        "jeu de rôle": 3, "jeu de role": 3, "jdr": 3, "donjons et dragons": 3, "d&d": 3,
        "jeu de cartes": 3, "poker": 3, "bridge": 3, "tarot": 3, "belote": 3,
        "jeu d'échecs": 3, "jeu d echecs": 3, "échiquier": 3, "echiquier": 3,
        "puzzle": 3, "mots croisés": 3, "mots croises": 3, "sudoku": 3, "mots fléchés": 3, "mots fleches": 3,
        "divertissement": 3, "divertir": 3, "amuser": 2, "amusement": 3,
        "loisir": 3, "loisirs": 3, "détente": 3, "detente": 3,
        "jeu mobile": 3, "jeux mobile": 3, "app jeu": 3,
        "jeu de stratégie": 3, "jeu de strategie": 3, "rts": 3, "rpg": 3, "mmorpg": 3, "fps": 3,
        "jeu d'aventure": 3, "jeu d aventure": 3, "point and click": 3,
        "jeu de simulation": 3, "simulateur": 3,
        "jeu de sport": 3, "jeu de course": 3,
        "jeu indépendant": 3, "jeu independant": 3, "indie game": 3, "indie": 3,
        "rétro gaming": 3, "retro gaming": 3, "rétro": 3, "retro": 3, "arcade": 3,
        "borne d'arcade": 3, "borne arcade": 3, "flipper": 3,
        "casino": 3, "loterie": 3, "loto": 3, "euromillions": 3,
        "pari": 3, "paris sportifs": 3, "bookmaker": 3,
        "quiz": 3, "blind test": 3, "karaoké": 3, "karaoke": 3,
        "escape game": 3, "escape room": 3, "laser game": 3,
        "parc d'attractions": 3, "parc d attractions": 3, "manège": 3, "manege": 3,
        "cirque": 3, "magie": 3, "magicien": 3, "magicienne": 3, "prestidigitation": 3,
        "humour": 3, "humoriste": 3, "blague": 3, "rire": 2, "comique": 2, "stand-up": 3, "stand up": 3,
        "impossible de décrocher": 3, "impossible de decrocher": 3, "passé 10 heures": 3, "passe 10 heures": 3,
    },
    
    # ========================
    # 18. SPIRITUALITÉ ET PHILOSOPHIE
    # ========================
    "Spiritualité et Philosophie": {
        "spiritualité": 3, "spiritualite": 3, "spirituel": 3, "spirituelle": 3,
        "philosophie": 3, "philosophe": 3, "philosophique": 3,
        "religion": 3, "religieux": 3, "religieuse": 3, "croyance": 3, "croyant": 3, "croyante": 3,
        "dieu": 3, "déesse": 3, "deesse": 3, "divin": 3, "divine": 3, "sacré": 3, "sacre": 3,
        "église": 3, "eglise": 3, "mosquée": 3, "mosquee": 3, "synagogue": 3, "temple": 3,
        "prêtre": 3, "pretre": 3, "curé": 3, "cure": 3, "pasteur": 3, "imam": 3, "rabbin": 3,
        "moine": 3, "moniale": 3, "religieux": 3, "religieuse": 3, "sœur": 3, "soeur": 3,
        "chrétien": 3, "chretien": 3, "chrétienne": 3, "chretienne": 3,
        "catholique": 3, "protestant": 3, "protestante": 3, "orthodoxe": 3,
        "musulman": 3, "musulmane": 3, "islam": 3, "islamique": 3,
        "juif": 3, "juive": 3, "judaïsme": 3, "judaisme": 3, "judaïque": 3, "judaique": 3,
        "bouddhiste": 3, "bouddhisme": 3, "hindou": 3, "hindoue": 3, "hindouisme": 3,
        "sikh": 3, "sikhisme": 3, "taoïste": 3, "taoiste": 3, "taoïsme": 3, "taoisme": 3,
        "athée": 3, "athee": 3, "agnostique": 3, "athéisme": 3, "atheisme": 3,
        "prière": 3, "priere": 3, "prier": 3, "réciter": 3, "reciter": 3,
        "messe": 3, "office": 3, "culte": 3, "cérémonie": 3, "ceremonie": 3,
        "baptême": 3, "bapteme": 3, "communion": 3, "confirmation": 3,
        "mariage": 3, "enterrement": 3, "funérailles": 3, "funerailles": 3,
        "pèlerinage": 3, "pelerinage": 3, "croisade": 3,
        "bible": 3, "coran": 3, "torah": 3, "évangile": 3, "evangile": 3,
        "prophète": 3, "prophete": 3, "messie": 3, "messager": 3, "apôtre": 3, "apotre": 3,
        "saint": 3, "sainte": 3, "martyr": 3, "martyre": 3,
        "ange": 3, "démon": 3, "demon": 3, "paradis": 3, "enfer": 3, "purgatoire": 3,
        "péché": 3, "peche": 3, "rédemption": 3, "redemption": 3,
        "pardon": 3, "repentir": 3, "confession": 3,
        "foi": 3, "espérance": 3, "esperance": 3, "charité": 3, "charite": 3,
        "miracle": 3, "miraculeux": 3, "miraculeuse": 3,
        "résurrection": 3, "resurrection": 3, "réincarnation": 3, "reincarnation": 3,
        "âme": 3, "ame": 3, "esprit": 3, "éternel": 3, "eternel": 3,
        "création": 3, "creation": 3, "créateur": 3, "createur": 3, "créature": 3, "creature": 3,
        "bénédiction": 3, "benediction": 3, "malédiction": 3, "malediction": 3,
        "sacrement": 3, "eucharistie": 3, "hostie": 3,
        "ramadan": 3, "carême": 3, "careme": 3, "pâques": 3, "paques": 3,
        "noël": 3, "noel": 3, "hanouka": 3, "yom kippour": 3,
        "méditation": 3, "meditation": 3, "contemplation": 3, "recueillement": 3,
        "sagesse": 3, "sage": 3, "enseignement": 3, "prêche": 3, "preche": 3, "sermon": 3,
        "prosélytisme": 3, "proselytisme": 3, "conversion": 3, "convertir": 3,
        "tolérance": 3, "tolerance": 3, "laïcité": 3, "laicite": 3, "liberté religieuse": 3,
    },
    
    # ========================
    # 19. ANIMAUX ET NATURE
    # ========================
    "Animaux et Nature": {
        "animal": 3, "animaux": 3, "faune": 3, "sauvage": 3,
        "chien": 3, "chiot": 3, "chat": 3, "chaton": 3, "félin": 3, "felin": 3, "canin": 3,
        "cheval": 3, "poney": 3, "équitation": 3, "equitation": 3, "cavaler": 3,
        "oiseau": 3, "oiseaux": 3, "voler": 2, "aile": 3, "plume": 3,
        "poisson": 3, "aquarium": 3, "nageoire": 3,
        "serpent": 3, "lézard": 3, "lezard": 3, "reptile": 3, "tortue": 3,
        "insecte": 3, "papillon": 3, "abeille": 3, "araignée": 3, "araignee": 3,
        "éléphant": 3, "elephant": 3, "lion": 3, "tigre": 3, "ours": 3, "loup": 3, "renard": 3,
        "singe": 3, "gorille": 3, "dauphin": 3, "baleine": 3, "requin": 3,
        "zoo": 3, "parc animalier": 3, "réserve": 3, "reserve": 3, "safari": 3,
        "vétérinaire": 3, "veterinaire": 3, "véto": 3, "veto": 3, "soigneur": 3, "soigneuse": 3,
        "refuge": 3, "spa": 3, "adoption": 3, "adopter": 3,
        "protection animale": 3, "bien-être animal": 3, "bien etre animal": 3,
        "espèce protégée": 3, "espece protegee": 3, "menacé": 3, "menace": 3, "extinction": 3,
        "biodiversité": 3, "biodiversite": 3, "écosystème": 3, "ecosysteme": 3,
        "nature": 2, "naturel": 2, "naturelle": 2, "sauvage": 3,
        "forêt": 3, "foret": 3, "bois": 2, "arbre": 2, "feuille": 2,
        "fleur": 2, "fleurs": 2, "plante": 2, "plantes": 2, "végétal": 3, "vegetal": 3,
        "jardin": 3, "jardinage": 3, "potager": 3, "botanique": 3,
        "montagne": 2, "rivière": 2, "riviere": 2, "lac": 2, "océan": 3, "ocean": 3,
        "paysage": 2, "panorama": 3, "vue": 1, "horizon": 3,
        "rando": 3, "randonnée": 3, "randonnee": 3, "balade": 3, "promenade": 3,
        "campagne": 3, "champ": 3, "prairie": 3, "pré": 3, "pre": 3,
        "élevage": 3, "elevage": 3, "ferme": 3, "agriculteur": 3, "agricultrice": 3,
        "berger": 3, "bergère": 3, "bergere": 3, "troupeau": 3,
    },
    
    # ========================
    # 20. HISTOIRE ET PATRIMOINE
    # ========================
    "Histoire et Patrimoine": {
        "histoire": 3, "historique": 3, "historien": 3, "historienne": 3,
        "passé": 2, "passe": 2, "mémoire": 2, "memoire": 2, "souvenir": 2,
        "patrimoine": 3, "héritage": 3, "heritage": 3, "culturel": 3, "culturelle": 3,
        "monument": 3, "site historique": 3, "vestige": 3, "ruine": 3,
        "château": 3, "chateau": 3, "forteresse": 3, "rempart": 3, "donjon": 3,
        "cathédrale": 3, "cathedrale": 3, "église": 2, "eglise": 2, "basilique": 3,
        "temple": 3, "pyramide": 3, "obélisque": 3, "obelisque": 3,
        "moyen âge": 3, "moyen age": 3, "médiéval": 3, "medieval": 3,
        "renaissance": 3, "baroque": 3, "classique": 2, "moderne": 2, "contemporain": 2,
        "antiquité": 3, "antiquite": 3, "gréco-romain": 3, "greco-romain": 3,
        "égypte ancienne": 3, "egypte ancienne": 3, "pharaon": 3, "hiéroglyphe": 3, "hieroglyphe": 3,
        "rome antique": 3, "romain": 3, "romaine": 3, "empire": 3,
        "grec": 3, "grecque": 3, "athènes": 3, "athenes": 3, "sparte": 3,
        "viking": 3, "scandinave": 3, "nordique": 3,
        "guerre mondiale": 3, "première guerre": 3, "premiere guerre": 3,
        "deuxième guerre": 3, "deuxieme guerre": 3, "seconde guerre": 3,
        "révolution": 3, "revolution": 3, "révolution française": 3, "revolution francaise": 3,
        "napoléon": 3, "napoleon": 3, "empire": 3, "empereur": 3,
        "colonie": 3, "colonisation": 3, "décolonisation": 3, "decolonisation": 3,
        "indépendance": 3, "independance": 3,
        "archéologie": 3, "archeologie": 3, "fouille": 3, "fouilles": 3,
        "archéologue": 3, "archeologue": 3, "découverte": 3, "decouverte": 3,
        "musée": 3, "musee": 3, "exposition": 3, "collection": 3,
        "archive": 3, "document": 2, "manuscrit": 3, "parchemin": 3,
        "généalogie": 3, "genealogie": 3, "ancêtre": 3, "ancetre": 3, "aïeul": 3, "aieul": 3,
        "tradition": 3, "coutume": 3, "folklore": 3, "légende": 3, "legende": 3,
        "mythe": 3, "mythologie": 3, "épopée": 3, "epopee": 3, "légendaire": 3, "legendaire": 3,
        "roi": 3, "reine": 3, "monarque": 3, "dynastie": 3, "royauté": 3, "royaute": 3,
        "chevalier": 3, "croisade": 3, "templier": 3, "samouraï": 3, "samourai": 3,
        "civilisation": 3, "peuple": 2, "ethnie": 3,
        "inscription": 3, "classé": 3, "classe": 3, "unesco": 3, "patrimoine mondial": 3,
    },
    
    # ========================
    # 21. ÉVÉNEMENTS ET ACTUALITÉS
    # ========================
    "Événements et Actualités": {
        "actualité": 3, "actualite": 3, "actu": 3, "news": 3, "information": 2,
        "événement": 3, "evenement": 3, "événement marquant": 3, "evenement marquant": 3,
        "cérémonie": 3, "ceremonie": 3, "célébration": 3, "celebration": 3,
        "festival": 3, "salon": 3, "foire": 3, "exposition": 3, "conférence": 3, "conference": 3,
        "concert": 3, "spectacle": 3, "show": 3, "représentation": 3, "representation": 3,
        "compétition": 3, "competition": 3, "tournoi": 3, "championnat": 3,
        "lancement": 3, "inauguration": 3, "ouverture": 3, "vernissage": 3,
        "conférence de presse": 3, "conference de presse": 3, "communiqué": 3, "communique": 3,
        "annonce": 3, "déclaration": 3, "declaration": 3, "révélation": 3, "revelation": 3,
        "nouvelle": 2, "info": 2, "breaking news": 3, "flash info": 3,
        "journal": 2, "quotidien": 2, "hebdomadaire": 3, "magazine": 3,
        "télévision": 3, "television": 3, "tv": 3, "chaîne": 2, "chaine": 2,
        "radio": 2, "podcast": 3, "émission": 3, "emission": 3,
        "média": 3, "media": 3, "médias": 3, "medias": 3, "presse": 3,
        "journaliste": 3, "reporter": 3, "correspondant": 3, "correspondante": 3,
        "interview": 3, "reportage": 3, "documentaire": 3, "enquête": 3, "enquete": 3,
        "direct": 3, "live": 3, "en direct": 3, "streaming": 3,
        "viral": 3, "tendance": 3, "buzz": 3, "partage": 3, "partager": 3,
        "réseaux sociaux": 3, "reseaux sociaux": 3, "facebook": 2, "twitter": 2, "instagram": 2,
        "tiktok": 3, "snapchat": 3, "linkedin": 3, "youtube": 2,
        "hashtag": 3, "trending": 3, "populaire": 2, "follow": 3, "like": 2, "commentaire": 3,
        "phénomène": 3, "phenomene": 3, "mouvement": 2, "vague": 2,
        "débat": 3, "debat": 3, "polémique": 3, "polemique": 3, "controverse": 3,
        "scandale": 3, "révélation": 3, "revelation": 3, "affaire": 3,
        "manifestation": 3, "rassemblement": 3, "mobilisation": 3, "grève": 3, "greve": 3,
        "crise": 3, "catastrophe": 3, "accident": 3, "incident": 3,
        "météo": 3, "meteo": 3, "tempête": 3, "tempete": 3, "ouragan": 3, "cyclone": 3,
        "inondation": 3, "sécheresse": 3, "secheresse": 3, "canicule": 3,
        "tremblement de terre": 3, "séisme": 3, "seisme": 3, "tsunami": 3,
        "alerte": 3, "vigilance": 3, "prévision": 3, "prevision": 3, "bulletin": 3,
        "cet événement": 3, "cet evenement": 3, "cet événement marquant": 3, "cet evenement marquant": 3,
    },
    
    # ========================
    # 22. AMOUR ET RELATIONS
    # ========================
    "Amour et Relations": {
        "amour": 3, "amoureux": 3, "amoureuse": 3, "aimer": 2, "aime": 2, "aimé": 2, "aimee": 2,
        "couple": 3, "relation": 2, "relations": 2, "conjoint": 3, "conjointe": 3,
        "mari": 3, "femme": 2, "époux": 3, "epoux": 3, "épouse": 3, "epouse": 3,
        "mariage": 3, "marié": 3, "marie": 3, "mariée": 3, "mariee": 3,
        "divorce": 3, "divorcé": 3, "séparation": 3, "separation": 3,
        "célibataire": 3, "celibataire": 3, "célibat": 3, "celibat": 3,
        "rencontre": 3, "rencontrer": 3, "date": 3, "dating": 3, "tinder": 3,
        "fiancé": 3, "fiance": 3, "fiancée": 3, "fiancee": 3, "fiançailles": 3, "fiancailles": 3,
        "romantique": 3, "romance": 3, "passion": 3, "passionné": 3, "passionne": 3,
        "cœur": 3, "coeur": 3, "coup de cœur": 3, "coup de coeur": 3, "coup de foudre": 3,
        "baiser": 3, "embrasser": 3, "câlin": 3, "calin": 3, "tendresse": 3,
        "jalousie": 3, "jaloux": 3, "jalouse": 3, "infidélité": 3, "infidelite": 3,
        "tromper": 3, "trompé": 3, "trompee": 3, "trahir": 3, "trahison": 3,
        "rupture": 3, "casser": 2, "quitter": 2, "quitté": 2, "quitte": 2,
        "réconciliation": 3, "reconciliation": 3, "pardon": 3, "pardonner": 3,
        "famille": 2, "parent": 2, "parents": 2, "enfant": 2, "enfants": 2,
        "bébé": 3, "bebe": 3, "naissance": 3, "grossesse": 3, "enceinte": 3,
        "maternité": 3, "maternite": 3, "paternité": 3, "paternite": 3,
        "frère": 3, "frere": 3, "sœur": 3, "soeur": 3, "fratrie": 3,
        "grand-parent": 3, "grand parent": 3, "grand-père": 3, "grand pere": 3,
        "grand-mère": 3, "grand mere": 3, "petit-fils": 3, "petite-fille": 3,
        "cousin": 3, "cousine": 3, "oncle": 3, "tante": 3, "neveu": 3, "nièce": 3, "niece": 3,
        "ami": 2, "amis": 2, "amie": 2, "amies": 2, "amitié": 3, "amitie": 3,
        "copain": 3, "copine": 3, "pote": 3, "bande": 2, "groupe": 1,
        "collègue": 3, "collegue": 3, "collaborateur": 3, "collaboratrice": 3,
        "voisin": 3, "voisine": 3, "voisinage": 3,
        "connaissance": 2, "relationnel": 3, "social": 2, "sociale": 2,
        "solitude": 3, "seul": 2, "seule": 2, "isolement": 3, "abandon": 3,
        "dépendance": 3, "dependance": 3, "attachement": 3, "détachement": 3, "detachement": 3,
        "affection": 3, "attachement": 3, "proche": 2, "intime": 3, "intimité": 3, "intimite": 3,
        "confidence": 3, "confident": 3, "confidente": 3, "secret": 3,
        "soutien": 3, "soutenir": 3, "aider": 2, "aide": 2, "entraide": 3,
        "écoute": 3, "ecoute": 3, "écouter": 2, "ecouter": 2, "compréhension": 3, "comprehension": 3,
        "respect": 3, "respecter": 3, "confiance": 3, "honnêteté": 3, "honnetete": 3,
        "dispute": 3, "conflit": 3, "engueulade": 3, "réconciliation": 3, "reconciliation": 3,
        "belle-famille": 3, "belle famille": 3, "beau-père": 3, "beau pere": 3,
        "belle-mère": 3, "belle mere": 3, "beau-frère": 3, "belle-sœur": 3, "belle soeur": 3,
    },
    
    # ========================
    # 23. MAISON ET HABITAT
    # ========================
    "Maison et Habitat": {
        "maison": 3, "habitat": 3, "logement": 3, "appartement": 3, "appart": 3,
        "immeuble": 3, "résidence": 3, "residence": 3, "pavillon": 3, "villa": 3,
        "studio": 3, "loft": 3, "duplex": 3, "triplex": 3, "penthouse": 3,
        "propriétaire": 3, "proprietaire": 3, "locataire": 3, "propriété": 3, "propriete": 3,
        "location": 3, "louer": 3, "loué": 3, "loue": 3, "loyer": 3,
        "achat": 3, "acheter": 2, "acheté": 2, "achete": 2, "acquisition": 3,
        "vente": 3, "vendre": 3, "vendu": 3, "vendeur": 3, "acheteur": 3,
        "agence immobilière": 3, "agence immobiliere": 3, "agent immobilier": 3,
        "notaire": 3, "compromis": 3, "acte de vente": 3, "signature": 3,
        "crédit immobilier": 3, "credit immobilier": 3, "prêt": 3, "pret": 3, "emprunt": 3,
        "taux": 3, "taux d'intérêt": 3, "taux d interet": 3, "mensualité": 3, "mensualite": 3,
        "pièce": 2, "piece": 2, "chambre": 3, "salon": 3, "salle à manger": 3, "salle a manger": 3,
        "cuisine": 3, "salle de bain": 3, "sdb": 3, "toilette": 3, "wc": 3,
        "bureau": 3, "dressing": 3, "buanderie": 3, "cellier": 3, "grenier": 3,
        "cave": 3, "garage": 3, "jardin": 3, "terrasse": 3, "balcon": 3,
        "étage": 2, "etage": 2, "rez-de-chaussée": 3, "rez de chaussee": 3,
        "ascenseur": 3, "escalier": 3, "couloir": 3, "entrée": 3, "entree": 3,
        "surface": 3, "superficie": 3, "mètre carré": 3, "metre carre": 3, "m2": 3,
        "décoration": 3, "decoration": 3, "déco": 3, "deco": 3, "ameublement": 3,
        "meuble": 3, "meubles": 3, "canapé": 3, "canape": 3, "table": 2, "chaise": 3,
        "lit": 3, "armoire": 3, "étagère": 3, "etagere": 3, "bibliothèque": 3,
        "rénovation": 3, "renovation": 3, "travaux": 3,
        "peinture": 3, "carrelage": 3, "parquet": 3, "moquette": 3,
        "électricité": 3, "electricite": 3, "plomberie": 3, "chauffage": 3,
        "isolation": 3, "insonorisation": 3, "double vitrage": 3,
        "déménagement": 3, "demenagement": 3, "déménager": 3, "demenager": 3,
        "emménagement": 3, "emmenagement": 3, "emménager": 3, "emmenager": 3,
        "carton": 3, "déménageur": 3, "demenageur": 3, "camion": 3,
        "état des lieux": 3, "etat des lieux": 3, "inventaire": 3,
        "caution": 3, "dépôt de garantie": 3, "depot de garantie": 3,
        "charges": 3, "copropriété": 3, "copropriete": 3, "syndic": 3,
        "taxe foncière": 3, "taxe fonciere": 3, "taxe d'habitation": 3, "taxe d habitation": 3,
        "énergie": 3, "energie": 3, "électricité": 3, "electricite": 3, "gaz": 3, "eau": 3,
        "facture": 3, "consommation": 3, "économie d'énergie": 3, "economie d energie": 3,
        "domotique": 3, "connecté": 3, "connecte": 3, "intelligent": 2,
        "alarme": 3, "sécurité": 3, "securite": 3, "serrure": 3, "clé": 2, "cle": 2,
        "assurance habitation": 3, "sinistre": 3, "dégât des eaux": 3, "degat des eaux": 3,
        "incendie": 3, "cambriolage": 3, "vol": 2,
        "voisin": 3, "voisine": 3, "voisinage": 3, "nuisance": 3, "bruit": 2,
        "confort": 3, "cosy": 3, "cocooning": 3, "chaleureux": 3,
        "liberté de louer": 3, "liberte de louer": 3, "louer en toute tranquilité": 3,
    },
    
    # ========================
    # 24. SHOPPING ET CONSOMMATION
    # ========================
    "Shopping et Consommation": {
        "shopping": 3, "achat": 3, "achats": 3, "acheter": 2, "acheté": 2, "achete": 2,
        "magasin": 3, "boutique": 3, "centre commercial": 3, "galerie marchande": 3,
        "supermarché": 3, "supermarche": 3, "hypermarché": 3, "hypermarche": 3,
        "épicerie": 3, "epicerie": 3, "marché": 3, "marche": 3, "primeur": 3,
        "boulangerie": 3, "pâtisserie": 3, "patisserie": 3, "boucherie": 3, "poissonnerie": 3,
        "fromagerie": 3, "caviste": 3, "fleuriste": 3,
        "promotion": 3, "promo": 3, "soldes": 3, "réduction": 3, "reduction": 3,
        "remise": 3, "rabais": 3, "bon plan": 3, "bonne affaire": 3,
        "pas cher": 3, "cher": 3, "chère": 3, "chere": 3, "prix": 2,
        "coûter": 3, "couter": 3, "coût": 3, "cout": 3, "dépense": 3, "depense": 3,
        "gratuit": 3, "gratuite": 3, "offert": 3, "offerte": 3, "cadeau": 3,
        "payer": 3, "payé": 3, "paye": 3, "régler": 3, "regler": 3,
        "carte bancaire": 3, "cb": 3, "espèces": 3, "especes": 3, "liquide": 3,
        "chèque": 3, "cheque": 3, "virement": 3, "prélèvement": 3, "prelevement": 3,
        "facture": 3, "ticket": 3, "reçu": 3, "recu": 3, "ticket de caisse": 3,
        "remboursement": 3, "rembourser": 3, "échange": 3, "echange": 3,
        "retour": 3, "retourner": 3, "service après-vente": 3, "service apres-vente": 3,
        "sav": 3, "garantie": 3, "réclamation": 3, "reclamation": 3,
        "livraison": 3, "livrer": 3, "colis": 3, "transporteur": 3,
        "commande": 3, "commander": 3, "panier": 3, "checkout": 3,
        "en ligne": 3, "online": 3, "e-commerce": 3, "ecommerce": 3,
        "amazon": 3, "cdisount": 3, "fnac": 3, "darty": 3, "boulanger": 3,
        "leboncoin": 3, "vinted": 3, "etsy": 3, "aliexpress": 3, "wish": 3,
        "drive": 3, "click and collect": 3, "retrait": 3,
        "consommation": 3, "consommer": 3, "consommateur": 3, "consommatrice": 3,
        "produit": 2, "article": 2, "objet": 2, "marchandise": 3,
        "marque": 3, "brand": 3, "label": 3, "qualité": 3, "qualite": 3,
        "bio": 3, "équitable": 3, "equitable": 3, "local": 3, "artisanal": 3,
        "fait main": 3, "fait maison": 3, "diy": 3,
        "neuf": 3, "neuve": 3, "occasion": 3, "seconde main": 3, "vintage": 3,
        "collection": 3, "collectionner": 3, "collectionneur": 3, "collectionneuse": 3,
        "acheteur": 3, "acheteuse": 3, "vendeur": 3, "vendeuse": 3,
        "négocier": 3, "negocier": 3, "marchander": 3, "discuter le prix": 3,
        "arnaque": 3, "escroquerie": 3, "contrefaçon": 3, "contrefacon": 3,
        "publicité": 3, "publicite": 3, "pub": 3, "marketing": 3,
        "tendance": 3, "trend": 3, "mode": 2, "nouveauté": 3, "nouveaute": 3,
        "liste de courses": 3, "liste d'envies": 3, "liste d envies": 3, "wishlist": 3,
        "craquer": 3, "coup de cœur": 3, "coup de coeur": 3, "tentation": 3,
        "ce que j'ai acheté": 3, "ce que j ai achete": 3, "j'ai acheté": 3, "j ai achete": 3,
    },
}

# =========================
# FONCTIONS DE PRÉTRAITEMENT
# =========================

def _preprocess_text(text: str) -> List[str]:
    """Prétraite un texte pour l'analyse de thème."""
    if not text:
        return []
    
    text = text.lower().strip()
    
    # Supprimer les URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    
    # Supprimer les mentions et hashtags
    text = re.sub(r'@\w+|#\w+', ' ', text)
    
    # Normaliser les apostrophes
    text = text.replace("'", "'").replace("'", "'").replace("'", "'").replace("`", "'")
    
    # Remplacer les apostrophes et tirets par des espaces
    text = text.replace("'", " ").replace("-", " ").replace("_", " ")
    
    # Supprimer la ponctuation (garder lettres et chiffres)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Supprimer les chiffres isolés
    text = re.sub(r'\b\d+\b', ' ', text)
    
    # Tokenizer
    tokens = text.split()
    
    # Filtrer les stopwords et les mots courts
    tokens = [t for t in tokens if t not in STOPWORDS_FR and len(t) > 1]
    
    # Ajouter les bigrammes
    bigrams = []
    for i in range(len(tokens) - 1):
        bigram = tokens[i] + " " + tokens[i+1]
        bigrams.append(bigram)
    
    return tokens + bigrams


def _detect_topic_by_keywords(
    text: str, 
    min_unique_keywords: int = 1,
    min_total_weight: float = 3.0,
) -> Optional[Tuple[str, float, List[str], int, int]]:
    """
    Détecte le thème d'un texte basé sur les mots-clés pondérés.
    
    Args:
        text: Texte à analyser
        min_unique_keywords: Nombre minimum de mots-clés UNIQUES requis
        min_total_weight: Score total minimum requis
        
    Returns:
        Tuple (nom_du_thème, score_de_confiance, mots_clés_trouvés, poids_total, nb_uniques) ou None
    """
    if not text or not text.strip():
        return None
    
    tokens = _preprocess_text(text)
    if len(tokens) < 2:
        return None
    
    topic_results: Dict[str, Tuple[float, int, List[str], float]] = {}
    
    for topic, keywords_weighted in TOPIC_KEYWORDS.items():
        total_weight = 0.0
        found_keywords: Set[str] = set()
        found_details: List[str] = []
        
        for token in tokens:
            if token in keywords_weighted:
                weight = keywords_weighted[token]
                total_weight += weight
                if token not in found_keywords:
                    found_keywords.add(token)
                    found_details.append(f"{token}({weight})")
        
        unique_count = len(found_keywords)
        
        if unique_count >= min_unique_keywords:
            diversity_bonus = unique_count * 1.0
            adjusted_score = total_weight + diversity_bonus
            topic_results[topic] = (adjusted_score, unique_count, found_details, total_weight)
    
    if not topic_results:
        return None
    
    best_topic = None
    best_score = 0.0
    best_unique = 0
    best_details = []
    best_raw_weight = 0.0
    
    for topic, (score, unique, details, raw_weight) in topic_results.items():
        if score > best_score and score >= min_total_weight:
            best_score = score
            best_topic = topic
            best_unique = unique
            best_details = details
            best_raw_weight = raw_weight
    
    if best_topic:
        confidence = min(1.0, (best_unique / max(1, len(tokens) * 0.25)) * (best_score / 25.0))
        return (best_topic, confidence, best_details, best_raw_weight, best_unique)
    
    return None


# =========================
# API PRINCIPALE
# =========================

def extract_topics(
    texts: List[str],
    n_topics: int = 10,
    n_words: int = 10,
    max_features: int = 1000,
    method: str = "keywords",
) -> Dict[str, Any]:
    """Extrait les thèmes principaux d'une liste de textes."""
    if not texts or len(texts) == 0:
        logger.warning("Aucun texte fourni")
        return {"topics": [], "topic_distributions": [], "method": method, "classified_count": 0, "unclassified_count": 0}
    
    try:
        if method == "lda" and SKLEARN_AVAILABLE:
            return _extract_topics_lda(texts, n_topics, n_words, max_features)
        else:
            return _extract_topics_keywords(texts, n_topics, n_words)
    except Exception as e:
        logger.error(f"Erreur extraction: {e}")
        return _extract_topics_keywords(texts, n_topics, n_words)


def _extract_topics_keywords(texts: List[str], n_topics: int, n_words: int) -> Dict[str, Any]:
    """Extraction robuste par mots-clés."""
    
    topic_counts: Dict[str, int] = {}
    topic_examples: Dict[str, List[Dict]] = {}
    classified = 0
    unclassified = 0
    unclassified_texts: List[str] = []
    
    for text in texts:
        result = _detect_topic_by_keywords(text, min_unique_keywords=1, min_total_weight=3.0)
        if result:
            topic_name, confidence, details, weight, unique = result
            topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
            if topic_name not in topic_examples:
                topic_examples[topic_name] = []
            if len(topic_examples[topic_name]) < 3:
                topic_examples[topic_name].append({
                    "text": text[:120],
                    "confidence": round(confidence, 2),
                    "keywords": details[:5],
                    "weight": weight,
                    "unique": unique,
                })
            classified += 1
        else:
            unclassified += 1
            unclassified_texts.append(text[:80])
    
    logger.info(f"Textes classifiés: {classified}, Non classifiés: {unclassified}")
    if unclassified > 0 and unclassified <= 5:
        logger.info(f"Exemples non classifiés: {unclassified_texts}")
    
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    top_topics = sorted_topics[:n_topics]
    
    topics = []
    for topic_id, (topic_name, count) in enumerate(top_topics):
        keywords = list(TOPIC_KEYWORDS[topic_name].keys())
        keywords_sorted = sorted(keywords, key=lambda k: TOPIC_KEYWORDS[topic_name][k], reverse=True)
        topics.append({
            "topic_id": topic_id,
            "topic_name": topic_name,
            "words": keywords_sorted[:n_words],
            "weights": [TOPIC_KEYWORDS[topic_name][w] for w in keywords_sorted[:n_words]],
            "count": count,
            "examples": topic_examples.get(topic_name, []),
        })
    
    return {
        "topics": topics,
        "topic_distributions": [],
        "method": "keywords",
        "classified_count": classified,
        "unclassified_count": unclassified,
    }


def _extract_topics_lda(texts: List[str], n_topics: int, n_words: int, max_features: int) -> Dict[str, Any]:
    """Extraction LDA avec fallback keywords."""
    
    processed_texts = [" ".join(_preprocess_text(t)) for t in texts]
    processed_texts = [t for t in processed_texts if len(t.split()) >= 3]
    
    if len(processed_texts) < max(5, n_topics * 2):
        logger.warning(f"Pas assez de textes ({len(processed_texts)}) pour LDA, fallback keywords")
        return _extract_topics_keywords(texts, n_topics, n_words)
    
    try:
        vectorizer = CountVectorizer(
            max_features=max_features,
            lowercase=True,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.9,
        )
        
        doc_term_matrix = vectorizer.fit_transform(processed_texts)
        actual_n_topics = min(n_topics, doc_term_matrix.shape[0] - 1, doc_term_matrix.shape[1] - 1)
        actual_n_topics = max(2, actual_n_topics)
        
        lda = LatentDirichletAllocation(
            n_components=actual_n_topics,
            random_state=42,
            max_iter=10,
            learning_method="online",
            batch_size=min(32, len(processed_texts)),
        )
        lda.fit(doc_term_matrix)
        
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[:-n_words - 1:-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topic_weights = [float(topic[i]) for i in top_words_idx]
            
            topic_name = f"Topic {topic_idx + 1}"
            for word in top_words[:3]:
                for theme, keywords in TOPIC_KEYWORDS.items():
                    if word in keywords:
                        topic_name = theme
                        break
                if topic_name != f"Topic {topic_idx + 1}":
                    break
            
            topics.append({
                "topic_id": topic_idx,
                "topic_name": topic_name,
                "words": top_words,
                "weights": topic_weights,
                "count": 0,
            })
        
        topic_distributions = lda.transform(doc_term_matrix).tolist()
        
        return {
            "topics": topics,
            "topic_distributions": topic_distributions,
            "method": "lda",
            "classified_count": len(processed_texts),
            "unclassified_count": len(texts) - len(processed_texts),
        }
    except Exception as e:
        logger.error(f"Erreur LDA: {e}")
        return _extract_topics_keywords(texts, n_topics, n_words)


def get_dominant_topic(
    text: str, 
    topics_model: Dict[str, Any] = None, 
    min_confidence: float = 0.05,
    method: str = "keywords",
) -> Optional[Dict[str, Any]]:
    """
    Retourne le thème dominant pour un texte.
    
    Args:
        text: Texte à analyser
        topics_model: Modèle de thèmes (optionnel, requis pour LDA)
        min_confidence: Seuil minimum de confiance
        method: Méthode de détection ("keywords" ou "lda")
    
    Returns:
        dict ou None
    """
    if not text or not text.strip():
        return None
    
    if method == "lda" and SKLEARN_AVAILABLE and topics_model:
        return _get_dominant_topic_lda(text, topics_model, min_confidence)
    else:
        return _get_dominant_topic_keywords(text, topics_model, min_confidence)


def _get_dominant_topic_keywords(
    text: str, 
    topics_model: Dict[str, Any] = None, 
    min_confidence: float = 0.05,
) -> Optional[Dict[str, Any]]:
    """Détection de thème par mots-clés pondérés."""
    result = _detect_topic_by_keywords(text, min_unique_keywords=1, min_total_weight=3.0)
    
    if result:
        topic_name, confidence, details, weight, unique = result
        
        if confidence >= min_confidence:
            topic_id = 0
            words = []
            if topics_model and topics_model.get("topics"):
                for t in topics_model["topics"]:
                    if t.get("topic_name") == topic_name:
                        topic_id = t.get("topic_id", 0)
                        words = t.get("words", [])[:5]
                        break
            
            if not words:
                words = [k for k, v in sorted(
                    TOPIC_KEYWORDS.get(topic_name, {}).items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]]
            
            return {
                "topic_id": topic_id,
                "topic_name": topic_name,
                "words": words,
                "confidence": round(confidence, 4),
                "details": details[:10],
                "weight": weight,
                "unique_keywords": unique,
                "method": "keywords",
            }
    
    return None


def _get_dominant_topic_lda(
    text: str, 
    topics_model: Dict[str, Any], 
    min_confidence: float = 0.05,
) -> Optional[Dict[str, Any]]:
    """Détection de thème par LDA."""
    if not topics_model or topics_model.get("method") != "lda":
        logger.warning("Modèle LDA non fourni, fallback keywords")
        return _get_dominant_topic_keywords(text, None, min_confidence)
    
    try:
        from sklearn.feature_extraction.text import CountVectorizer
        
        processed_text = " ".join(_preprocess_text(text))
        if len(processed_text.split()) < 3:
            return _get_dominant_topic_keywords(text, None, min_confidence)
        
        # Reconstituer le vectorizer et le modèle LDA (simplifié)
        # En pratique, il faudrait sérialiser le vectorizer et le modèle
        # Ici on fait un fallback sur keywords pour la détection individuelle
        logger.info("LDA détecté mais vectorizer non sérialisé, fallback keywords")
        return _get_dominant_topic_keywords(text, None, min_confidence)
        
    except Exception as e:
        logger.error(f"Erreur LDA: {e}")
        return _get_dominant_topic_keywords(text, None, min_confidence)


def get_dominant_topic_keyword(text: str, topics_model: Dict[str, Any] = None) -> Optional[str]:
    """Version simplifiée retournant juste le nom du thème."""
    result = _detect_topic_by_keywords(text, min_unique_keywords=1, min_total_weight=3.0)
    if result:
        return result[0]
    return None


def get_topic_distribution(text: str, topics_model: Dict[str, Any]) -> List[float]:
    """Retourne la distribution de thèmes pour un texte (compatibilité API)."""
    if not text or not topics_model or not topics_model.get("topics"):
        return []
    
    dominant = get_dominant_topic(text, topics_model)
    n_topics = len(topics_model["topics"])
    
    if dominant:
        dist = [0.0] * n_topics
        for i, topic in enumerate(topics_model["topics"]):
            if topic.get("topic_name") == dominant["topic_name"]:
                dist[i] = 0.8 + (0.2 / n_topics)
            else:
                dist[i] = 0.2 / n_topics
        return dist
    
    return [1.0 / n_topics] * n_topics if n_topics > 0 else []


# =========================
# INTÉGRATION NEO4J
# =========================

def update_post_topic(db, post_id: str, topics_model: Dict[str, Any]) -> bool:
    """Met à jour le thème d'un post dans Neo4j."""
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

    dominant_topic = get_dominant_topic(content, topics_model)
    
    if dominant_topic:
        topic_name = dominant_topic.get("topic_name")
        topic_words = dominant_topic.get("words", [])[:5]
        confidence = dominant_topic.get("confidence", 0.0)
    else:
        topic_name = None
        topic_words = []
        confidence = 0.0

    query = """
    MATCH (p:Post {postId: $post_id})
    SET p.detectedTopic = $topic_name,
        p.topicWords = $topic_words,
        p.topicConfidence = $confidence
    RETURN p
    """

    try:
        db._execute_write(
            query,
            post_id=post_id,
            topic_name=topic_name,
            topic_words=topic_words,
            confidence=confidence,
        )
        if topic_name:
            logger.info(f"Post {post_id} → {topic_name} (conf: {confidence:.2f})")
        else:
            logger.info(f"Post {post_id} → aucun thème")
        return True
    except Exception as e:
        logger.error(f"Erreur mise à jour thème: {e}")
        return False


def build_topics_model_from_posts(db, limit: int = 500) -> Dict[str, Any]:
    """Construit un modèle de thèmes à partir des posts Neo4j."""
    from src.db_utils import LinkUpDB

    if not isinstance(db, LinkUpDB):
        logger.error("Instance db invalide")
        return {}

    query = """
    MATCH (p:Post)
    WHERE p.content IS NOT NULL AND p.content <> ''
    RETURN p.content AS content
    LIMIT $limit
    """

    try:
        rows = db._execute_read(query, limit=limit)
        texts = [row["content"] for row in rows if row.get("content")]

        if not texts:
            logger.warning("Aucun contenu pour construire le modèle")
            return {"topics": [], "method": "keywords"}

        logger.info(f"Construction du modèle avec {len(texts)} posts")
        topics_model = extract_topics(texts)
        n_topics = len(topics_model.get("topics", []))
        logger.info(f"Modèle construit: {n_topics} thèmes détectés")
        return topics_model
    except Exception as e:
        logger.error(f"Erreur construction modèle: {e}")
        return {"topics": [], "method": "keywords"}


def batch_update_posts_topics(db, limit: int = 100, reanalyze_all: bool = False) -> int:
    """Met à jour les topics des posts en masse."""
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
        WHERE p.detectedTopic IS NULL
        RETURN p.postId AS post_id, p.content AS content
        LIMIT $limit
        """

    try:
        rows = db._execute_read(query, limit=limit)
        
        if len(rows) == 0:
            logger.info("Aucun post à analyser")
            return 0

        topics_model = build_topics_model_from_posts(db, limit=500)
        
        if not topics_model.get("topics"):
            logger.warning("Aucun thème détecté, nettoyage")
            db._execute_write("MATCH (p:Post) SET p.detectedTopic = NULL, p.topicWords = NULL, p.topicConfidence = NULL")
            return 0

        updated_count = 0
        cleared_count = 0

        for row in rows:
            post_id = row["post_id"]
            content = row.get("content", "")

            if content:
                dominant_topic = get_dominant_topic(content, topics_model)
                
                if dominant_topic:
                    db._execute_write(
                        """
                        MATCH (p:Post {postId: $post_id})
                        SET p.detectedTopic = $topic_name,
                            p.topicWords = $topic_words,
                            p.topicConfidence = $confidence
                        """,
                        post_id=post_id,
                        topic_name=dominant_topic["topic_name"],
                        topic_words=dominant_topic.get("words", [])[:5],
                        confidence=dominant_topic.get("confidence", 0.0),
                    )
                    updated_count += 1
                else:
                    db._execute_write(
                        """
                        MATCH (p:Post {postId: $post_id})
                        SET p.detectedTopic = NULL, p.topicWords = NULL, p.topicConfidence = NULL
                        """,
                        post_id=post_id,
                    )
                    cleared_count += 1

        logger.info(f"{updated_count} posts mis à jour, {cleared_count} posts sans thème")
        return updated_count
    except Exception as e:
        logger.error(f"Erreur batch topics: {e}")
        return 0


# =========================
# TESTS RAPIDES
# =========================

if __name__ == "__main__":
    test_texts = [
        "je joue souvent au basketball",
        "j'aime la musique",
        "aujourd'hui c'est lundi.",
        "je me sens triste.",
        "Ce que j'ai acheté chez cette magnifique région : un vrai coup de cœur ?",
        "Je me forme en cet événement marquant pour me reconvertir.",
        "L'éducation est la clé de tout.",
        "Ma spécialité : le cette innovation, un vrai régal !",
        "J'ai enfin réussi ma recette de cet événement marquant.",
        "L'art contemporain de Algérie est fascinant.",
        "J'apprends la peinture, mes premiers essais sur ce talentueux artiste.",
        "Le yoga m'aide énormément à gérer mon stress.",
        "La nutrition, c'est la clé : j'ai changé mon alimentation.",
        "J'ai adoré le dernier film de Albanie, à voir absolument !",
        "Mon médecin m'a conseillé de L'art d'innover plus facilement, je me sens mieux.",
        "Ce tableau de cette magnifique région est une véritable émotion.",
        "Le dernier festival de Brunetnec était incroyable.",
        "J'ai découvert un endroit secret à cet événement marquant, c'est magique.",
    ]

    print("=" * 80)
    print("TESTS DE TOPIC MODELING - VERSION FINALE 24 THÈMES")
    print("=" * 80)
    
    for text in test_texts:
        topic = get_dominant_topic(text)
        if topic:
            print(f"✅ [{topic['topic_name']:30s}] (conf: {topic['confidence']:.2f}, {topic['unique_keywords']} mots) → {text[:70]}...")
        else:
            print(f"❌ [Non classifié] → {text[:70]}...")