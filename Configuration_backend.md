# Guide d'utilisation du Backend

## Installation des dépendances

Installez toutes les dépendances du projet avec la commande suivante :

```bash
pip install -r requirements.txt
```

## Configuration de la base de données

Avant de lancer le backend, vous devez configurer votre base de données.

1. Créez une base de données dans neo4j.

2. Ouvrez le fichier `scripts/init_db.py` et renseignez les informations nécessaires à la connexion à votre base de données, notamment :

   * le nom de la base de données ;
   * le mot de passe de la base de données.

3. Exécutez ensuite le script d'initialisation afin de créer les contraintes d'unicité nécessaires sur les identifiants :

```bash
python scripts/init_db.py
```

4. Ouvrez le fichier `.env` et remplacez les valeurs par les paramètres correspondant à votre environnement, notamment :

   * le nom de votre base de données ;
   * l'utilisateur de votre base de données ;
   * le mot de passe votre base de données ;

## Lancement du serveur

Une fois les dépendances installées et la base de données configurée, lancez le serveur avec la commande suivante :

```bash
python -m uvicorn api:app
```

L'API sera alors accessible à l'adresse suivante :

```
http://localhost:8000
```

## Documentation des endpoints

La documentation interactive Swagger est disponible à l'adresse suivante :

```
http://localhost:8000/docs
```
