"""
Fonctions d'acces aux donnees Neo4j pour LinkUpDS.

Fichier : src/db_utils.py
Classe principale : LinkUpDB

Methodes : create_user, create_post, follow, unfollow, like_post, get_feed, etc.
"""

import uuid
from neo4j import GraphDatabase, exceptions

# Meme configuration que scripts/init_db.py
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "motdepasse123"


def _node_to_dict(node):
    """Transforme un noeud Neo4j en dictionnaire."""
    if node is None:
        return {}
    data = dict(node)
    for key, value in data.items():
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
        elif hasattr(value, "to_native"):
            data[key] = value.to_native()
    return data


class LinkUpDB:
    """Classe pour gerer les operations sur la base Neo4j."""

    def __init__(self, uri=URI, user=USER, password=PASSWORD):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self.driver is not None:
            self.driver.close()
            self.driver = None

    def verify_connectivity(self):
        try:
            self.driver.verify_connectivity()
            return True
        except exceptions.ServiceUnavailable:
            return False

    def _execute(self, query, params=None, single=False):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            if single:
                return result.single()
            return list(result)

    def create_user(self, name, email, password, user_id=None, role="user"):
        user_id = user_id or str(uuid.uuid4())
        query = """
        CREATE (u:User {
            userId: $user_id,
            name: $name,
            email: $email,
            password: $password,
            role: $role,
            createdAt: datetime()
        })
        RETURN u
        """
        record = self._execute(query, {
            "user_id": user_id,
            "name": name,
            "email": email,
            "password": password,
            "role": role,
        }, single=True)
        return _node_to_dict(record["u"])

    def get_user(self, user_id):
        query = "MATCH (u:User {userId: $user_id}) RETURN u"
        record = self._execute(query, {"user_id": user_id}, single=True)
        return _node_to_dict(record["u"]) if record else None

    def get_user_by_email(self, email):
        query = "MATCH (u:User {email: $email}) RETURN u"
        record = self._execute(query, {"email": email}, single=True)
        return _node_to_dict(record["u"]) if record else None

    def get_all_users(self, limit=100):
        query = """
        MATCH (u:User)
        RETURN u
        ORDER BY u.createdAt DESC
        LIMIT $limit
        """
        return [_node_to_dict(r["u"]) for r in self._execute(query, {"limit": limit})]

    def create_post(self, user_id, content, post_id=None, sentiment=None, category_id=None):
        post_id = post_id or str(uuid.uuid4())
        query = """
        MATCH (u:User {userId: $user_id})
        CREATE (p:Post {
            postId: $post_id,
            content: $content,
            timestamp: datetime(),
            sentiment: $sentiment
        })
        CREATE (u)-[:POSTED]->(p)
        WITH u, p
        OPTIONAL MATCH (c:Category {categoryId: $category_id})
        FOREACH (_ IN CASE WHEN c IS NULL THEN [] ELSE [1] END |
            CREATE (p)-[:IN_CATEGORY]->(c)
        )
        RETURN p, u.userId AS authorId, u.name AS authorName
        """
        record = self._execute(query, {
            "user_id": user_id,
            "post_id": post_id,
            "content": content,
            "sentiment": sentiment,
            "category_id": category_id,
        }, single=True)

        if record is None:
            raise ValueError("Utilisateur introuvable : " + user_id)

        post = _node_to_dict(record["p"])
        post["authorId"] = record["authorId"]
        post["authorName"] = record["authorName"]
        return post

    def get_post(self, post_id):
        query = """
        MATCH (u:User)-[:POSTED]->(p:Post {postId: $post_id})
        OPTIONAL MATCH (liker:User)-[:LIKES]->(p)
        RETURN p, u.userId AS authorId, u.name AS authorName, count(liker) AS likeCount
        """
        record = self._execute(query, {"post_id": post_id}, single=True)
        if record is None:
            return None

        post = _node_to_dict(record["p"])
        post["authorId"] = record["authorId"]
        post["authorName"] = record["authorName"]
        post["likeCount"] = record["likeCount"]
        return post

    def get_user_posts(self, user_id, limit=50):
        query = """
        MATCH (u:User {userId: $user_id})-[:POSTED]->(p:Post)
        OPTIONAL MATCH (liker:User)-[:LIKES]->(p)
        RETURN p, u.userId AS authorId, u.name AS authorName, count(liker) AS likeCount
        ORDER BY p.timestamp DESC
        LIMIT $limit
        """
        posts = []
        for record in self._execute(query, {"user_id": user_id, "limit": limit}):
            post = _node_to_dict(record["p"])
            post["authorId"] = record["authorId"]
            post["authorName"] = record["authorName"]
            post["likeCount"] = record["likeCount"]
            posts.append(post)
        return posts

    def follow(self, follower_id, followed_id):
        if follower_id == followed_id:
            raise ValueError("Un utilisateur ne peut pas se suivre lui-meme.")

        query = """
        MATCH (follower:User {userId: $follower_id})
        MATCH (followed:User {userId: $followed_id})
        MERGE (follower)-[:FOLLOWS]->(followed)
        RETURN follower
        """
        record = self._execute(query, {
            "follower_id": follower_id,
            "followed_id": followed_id,
        }, single=True)
        return record is not None

    def unfollow(self, follower_id, followed_id):
        query = """
        MATCH (follower:User {userId: $follower_id})-[r:FOLLOWS]->(followed:User {userId: $followed_id})
        DELETE r
        RETURN count(r) AS deleted
        """
        record = self._execute(query, {
            "follower_id": follower_id,
            "followed_id": followed_id,
        }, single=True)
        return record is not None and record["deleted"] > 0

    def get_following(self, user_id):
        query = """
        MATCH (u:User {userId: $user_id})-[:FOLLOWS]->(followed:User)
        RETURN followed
        ORDER BY followed.name
        """
        return [_node_to_dict(r["followed"]) for r in self._execute(query, {"user_id": user_id})]

    def get_followers(self, user_id):
        query = """
        MATCH (follower:User)-[:FOLLOWS]->(u:User {userId: $user_id})
        RETURN follower
        ORDER BY follower.name
        """
        return [_node_to_dict(r["follower"]) for r in self._execute(query, {"user_id": user_id})]

    def like_post(self, user_id, post_id):
        query = """
        MATCH (u:User {userId: $user_id}), (p:Post {postId: $post_id})
        MERGE (u)-[:LIKES]->(p)
        RETURN u
        """
        record = self._execute(query, {"user_id": user_id, "post_id": post_id}, single=True)
        return record is not None

    def unlike_post(self, user_id, post_id):
        query = """
        MATCH (u:User {userId: $user_id})-[r:LIKES]->(p:Post {postId: $post_id})
        DELETE r
        RETURN count(r) AS deleted
        """
        record = self._execute(query, {"user_id": user_id, "post_id": post_id}, single=True)
        return record is not None and record["deleted"] > 0

    def get_post_likes(self, post_id):
        query = """
        MATCH (u:User)-[:LIKES]->(p:Post {postId: $post_id})
        RETURN u
        ORDER BY u.name
        """
        return [_node_to_dict(r["u"]) for r in self._execute(query, {"post_id": post_id})]

    def get_feed(self, user_id, limit=20):
        """Retourne les posts des personnes suivies + les posts de l'utilisateur."""
        query = """
        MATCH (me:User {userId: $user_id})
        MATCH (author:User)-[:POSTED]->(p:Post)
        WHERE author = me OR EXISTS { (me)-[:FOLLOWS]->(author) }
        OPTIONAL MATCH (liker:User)-[:LIKES]->(p)
        OPTIONAL MATCH (me)-[myLike:LIKES]->(p)
        RETURN p,
               author.userId AS authorId,
               author.name AS authorName,
               count(liker) AS likeCount,
               myLike IS NOT NULL AS likedByMe
        ORDER BY p.timestamp DESC
        LIMIT $limit
        """
        feed = []
        for record in self._execute(query, {"user_id": user_id, "limit": limit}):
            post = _node_to_dict(record["p"])
            post["authorId"] = record["authorId"]
            post["authorName"] = record["authorName"]
            post["likeCount"] = record["likeCount"]
            post["likedByMe"] = record["likedByMe"]
            feed.append(post)
        return feed
