# 🧪 Guide de Test - LinkUpDS API

## 🚀 Démarrer le serveur

```bash
pip install -r requirements.txt
uvicorn api:app --reload
```

L'API sera disponible à : `http://localhost:8000`

---

## 📖 Documentation interactive

- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`
- **Health Check** : `http://localhost:8000/health`

---

## 🧾 Exemples de requêtes

### 1️⃣ **Authentification**

#### Créer un compte
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jean Dupont",
    "email": "jean@example.com",
    "password": "SecurePassword123",
    "username": "jean",
    "bio": "Développeur passionné",
    "city": "Paris"
  }'
```

#### Se connecter
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean@example.com",
    "password": "SecurePassword123"
  }'
```

Réponse :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Récupérer mon profil
```bash
TOKEN="votre_token_ici"
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### 2️⃣ **Utilisateurs**

#### Récupérer un utilisateur
```bash
curl -X GET http://localhost:8000/users/user_xxx
```

#### Mettre à jour mon profil
```bash
TOKEN="votre_token_ici"
curl -X PUT http://localhost:8000/users/user_xxx \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jean Dupont Modifié",
    "bio": "Dev + DevOps",
    "city": "Lyon",
    "interests": ["Python", "Neo4j", "FastAPI"]
  }'
```

#### Supprimer mon compte
```bash
TOKEN="votre_token_ici"
curl -X DELETE http://localhost:8000/users/user_xxx \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3️⃣ **Posts**

#### Créer un post
```bash
TOKEN="votre_token_ici"
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Bonjour LinkUpDS!",
    "topic": "general"
  }'
```

#### Récupérer un post
```bash
curl -X GET http://localhost:8000/posts/post_xxx
```

#### Supprimer un post
```bash
TOKEN="votre_token_ici"
curl -X DELETE http://localhost:8000/posts/post_xxx \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4️⃣ **Follows (Suivre/Ne plus suivre)**

#### Suivre un utilisateur
```bash
TOKEN="votre_token_ici"
curl -X POST http://localhost:8000/follows/user_xxx \
  -H "Authorization: Bearer $TOKEN"
```

#### Arrêter de suivre un utilisateur
```bash
TOKEN="votre_token_ici"
curl -X DELETE http://localhost:8000/follows/user_xxx \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5️⃣ **Likes**

#### Liker un post
```bash
TOKEN="votre_token_ici"
curl -X POST http://localhost:8000/likes/post_xxx \
  -H "Authorization: Bearer $TOKEN"
```

#### Retirer un like
```bash
TOKEN="votre_token_ici"
curl -X DELETE http://localhost:8000/likes/post_xxx \
  -H "Authorization: Bearer $TOKEN"
```

---

### 6️⃣ **Feed**

#### Récupérer mon feed (pagination)
```bash
TOKEN="votre_token_ici"
curl -X GET "http://localhost:8000/feed/user_xxx?skip=0&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

Paramètres :
- `skip` : nombre de posts à sauter (défaut: 0)
- `limit` : nombre de posts à retourner (défaut: 20, max: 100)

---

## 🔒 Points de sécurité implémentés

✅ **Hachage des passwords** : bcrypt avec salt  
✅ **JWT Authentication** : tokens signés et datés  
✅ **Autorisation** : vérification des permissions (ne modifier/supprimer que ses propres données)  
✅ **Pas d'exposition de passwords** : séparation `get_user()` vs `get_user_auth_by_email()`  
✅ **Logging** : toutes les opérations critiques tracées  
✅ **Gestion d'erreurs** : messages d'erreur cohérents sans exposition de détails sensibles  

---

## 📊 Codes HTTP utilisés

| Code | Signification |
|------|---------------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## 🚨 Gestion des erreurs

### Format standard des erreurs
```json
{
  "detail": "Message d'erreur explicite"
}
```

### Exemples

**Token invalide**
```json
{
  "detail": "Token invalide ou expiré"
}
```

**Permission refusée**
```json
{
  "detail": "Vous ne pouvez modifier que votre propre profil"
}
```

**Ressource non trouvée**
```json
{
  "detail": "Utilisateur introuvable"
}
```

---

## 💾 Variables d'environnement

```bash
# JWT
SECRET_KEY=votre_clé_secrète
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=motdepasse123
NEO4J_DATABASE=neo4j

# Logging
LOG_LEVEL=INFO
```

---

## 📝 Notes importantes

1. Les **passwords ne sont jamais exposés** dans les réponses
2. Le **token JWT** expire après 24h par défaut
3. Les **permissions sont vérifiées** pour chaque opération sensible
4. Le **logging enregistre** tous les accès critiques
5. La **pagination du feed** utilise `skip/limit` pour optimiser Neo4j

---

## 🐛 Debugging

Vérifiez les logs :
```bash
# Les logs apparaissent dans le terminal lors du démarrage
# Format: TIMESTAMP - LOGGER - LEVEL - MESSAGE
```

Testez la connexion Neo4j :
```python
from src.db_utils import LinkUpDB
db = LinkUpDB()
print(db.verify_connection())  # True/False
```

---
