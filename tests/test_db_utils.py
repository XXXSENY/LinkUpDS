"""
Tests manuels pour src/db_utils.py

Execution : python Tests/test_db_utils.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db_utils import LinkUpDB


def main():
    print("Verification de LinkUpDB...")
    db = LinkUpDB()

    if not db.verify_connectivity():
        print("Erreur : Neo4j n'est pas accessible.")
        print("Lancez Docker puis : python scripts/init_db.py")
        return 1

    suffix = datetime.now().strftime("%H%M%S")
    user1 = db.create_user(
        name="Khadija",
        email="khadija." + suffix + "@linkupds.local",
        password="test123",
    )
    user2 = db.create_user(
        name="Moussa",
        email="moussa." + suffix + "@linkupds.local",
        password="test123",
    )

    db.follow(user1["userId"], user2["userId"])
    post = db.create_post(
        user_id=user2["userId"],
        content="Premier post de test LinkUpDS",
        sentiment="neutre",
    )
    db.like_post(user1["userId"], post["postId"])

    feed = db.get_feed(user1["userId"])
    print("Utilisateur cree :", user1["name"])
    print("Nombre de posts dans le fil :", len(feed))
    if feed:
        print("Contenu du dernier post :", feed[0]["content"])

    db.close()
    print("Test OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
