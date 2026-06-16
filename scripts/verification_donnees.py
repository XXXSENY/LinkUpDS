"""
Script de vérification des données - Adama Kané
J1 : Vérification que la base contient bien des relations FOLLOWS et des intérêts exploitables
"""
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))          
from src.db_utils import LinkUpDB
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verifier_donnees():
    """Vérifie l'intégrité des données générées"""
    
    logger.info("=" * 60)
    logger.info("🔍 VÉRIFICATION DES DONNÉES - JOUR 1")
    logger.info(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    logger.info("=" * 60)
    
    db = LinkUpDB()
    resultats = {}
    
    try:
        with db.driver.session() as session:
            
            # 1. COMPTER LES UTILISATEURS
            result = session.run("MATCH (u:User) RETURN COUNT(u) AS count")
            nb_users = result.single()["count"]
            resultats['utilisateurs'] = nb_users
            logger.info(f"👤 Utilisateurs : {nb_users}")
            
            # 2. COMPTER LES POSTS
            result = session.run("MATCH (p:Post) RETURN COUNT(p) AS count")
            nb_posts = result.single()["count"]
            resultats['posts'] = nb_posts
            logger.info(f"📝 Posts : {nb_posts}")
            
            # 3. COMPTER LES RELATIONS FOLLOWS
            result = session.run("MATCH ()-[:FOLLOWS]->() RETURN COUNT(*) AS count")
            nb_follows = result.single()["count"]
            resultats['follows'] = nb_follows
            logger.info(f"🔗 Relations FOLLOWS : {nb_follows}")
            
            # 4. COMPTER LES LIKES
            result = session.run("MATCH ()-[:LIKES]->() RETURN COUNT(*) AS count")
            nb_likes = result.single()["count"]
            resultats['likes'] = nb_likes
            logger.info(f"❤️ Likes : {nb_likes}")
            
            # 5. POSTS AVEC CONTENU (pour NLP)
            result = session.run("""
                MATCH (p:Post) 
                WHERE p.content IS NOT NULL AND p.content <> ""
                RETURN COUNT(p) AS count
            """)
            nb_contenu = result.single()["count"]
            resultats['posts_contenu'] = nb_contenu
            logger.info(f"📄 Posts avec contenu : {nb_contenu}")
            
            # 6. UTILISATEURS AVEC INTÉRÊTS
            result = session.run("""
                MATCH (u:User)
                WHERE u.interests IS NOT NULL AND SIZE(u.interests) > 0
                RETURN COUNT(u) AS count
            """)
            nb_interets = result.single()["count"]
            resultats['users_interets'] = nb_interets
            if nb_interets > 0:
                logger.info(f"🎯 Utilisateurs avec intérêts : {nb_interets}")
            else:
                logger.warning("⚠️ Aucun utilisateur avec des intérêts trouvé")
            
            # 7. EXEMPLES DE RELATIONS FOLLOWS
            logger.info("\n📊 EXEMPLES DE RELATIONS FOLLOWS :")
            result = session.run("""
                MATCH (a:User)-[:FOLLOWS]->(b:User) 
                RETURN a.username AS follower, b.username AS followed
                LIMIT 5
            """)
            for record in result:
                logger.info(f"  • {record['follower']} suit {record['followed']}")
            
            # 8. EXEMPLES DE POSTS
            logger.info("\n📝 EXEMPLES DE POSTS :")
            result = session.run("""
                MATCH (p:Post) 
                RETURN p.content AS content
                LIMIT 3
            """)
            for record in result:
                content = record['content'][:100] + "..." if len(record['content']) > 100 else record['content']
                logger.info(f"  • {content}")
            
            # 9. EXEMPLES D'INTÉRÊTS
            if nb_interets > 0:
                logger.info("\n🎯 EXEMPLES D'INTÉRÊTS :")
                result = session.run("""
                    MATCH (u:User)
                    WHERE u.interests IS NOT NULL AND SIZE(u.interests) > 0
                    RETURN u.username AS username, u.interests AS interests
                    LIMIT 3
                """)
                for record in result:
                    logger.info(f"  • {record['username']} : {record['interests']}")
            
            # 10. STRUCTURE DU GRAPHE
            logger.info("\n📊 STATISTIQUES DU GRAPHE :")
            
            # Degré moyen
            result = session.run("""
                MATCH (u:User)
                OPTIONAL MATCH (u)-[:FOLLOWS]->(f)
                WITH u, COUNT(f) AS following
                RETURN AVG(following) AS avg_degree
            """)
            avg_degree = result.single()["avg_degree"]
            logger.info(f"  • Degré moyen (following) : {avg_degree:.2f}")
            
            # Utilisateur avec le plus de followers
            result = session.run("""
                MATCH (u:User)<-[:FOLLOWS]-(f)
                RETURN u.username AS username, COUNT(f) AS followers
                ORDER BY followers DESC
                LIMIT 1
            """)
            record = result.single()
            if record:
                logger.info(f"  • Plus influent : {record['username']} ({record['followers']} followers)")
            
            # 11. VÉRIFICATION POUR OUMOU (Common Neighbors, Jaccard)
            logger.info("\n🔬 VÉRIFICATION POUR OUMOU (Équipe 2) :")
            
            # Vérifier qu'il y a assez de relations pour les calculs
            if nb_follows >= 10:
                logger.info("  ✅ Suffisamment de relations FOLLOWS pour les calculs")
            else:
                logger.warning("  ⚠️ Peu de relations FOLLOWS - les calculs seront limités")
            
            # Vérifier les intérêts pour la similarité
            if nb_interets >= 5:
                logger.info("  ✅ Suffisamment d'utilisateurs avec intérêts")
            else:
                logger.warning("  ⚠️ Peu d'utilisateurs avec intérêts")
            
            # 12. VÉRIFICATION POUR IBRAHIMA (Recommandations)
            logger.info("\n🔬 VÉRIFICATION POUR IBRAHIMA (Équipe 3) :")
            
            # Utilisateurs avec au moins 2 follows (pour avoir des recommandations)
            result = session.run("""
                MATCH (u:User)-[:FOLLOWS]->(f)
                WITH u, COUNT(f) AS following
                WHERE following >= 2
                RETURN COUNT(u) AS count
            """)
            nb_actifs = result.single()["count"]
            logger.info(f"  • Utilisateurs avec >= 2 follows : {nb_actifs}")
            
            # Vérifier les posts pour l'analyse de sentiment
            if nb_contenu >= 10:
                logger.info("  ✅ Suffisamment de posts pour l'analyse NLP")
            else:
                logger.warning("  ⚠️ Peu de posts pour l'analyse NLP")
            
            # CONCLUSION
            logger.info("\n" + "=" * 60)
            logger.info("📋 RÉSUMÉ DE LA VÉRIFICATION")
            logger.info("=" * 60)
            
            # Vérifier les critères
            criteres = {
                "Utilisateurs > 0": nb_users > 0,
                "Posts > 0": nb_posts > 0,
                "Relations FOLLOWS > 0": nb_follows > 0,
                "Posts avec contenu > 0": nb_contenu > 0
            }
            
            for critere, ok in criteres.items():
                if ok:
                    logger.info(f"  ✅ {critere}")
                else:
                    logger.error(f"  ❌ {critere}")
            
            # Bilan
            tous_ok = all(criteres.values())
            if tous_ok:
                logger.info("\n🎉 TOUTES LES VÉRIFICATIONS SONT OK")
                logger.info("✅ Les données sont exploitables pour les équipes 2 et 3")
            else:
                logger.warning("\n⚠️ CERTAINS CRITÈRES NE SONT PAS REMPLIS")
                logger.warning("Veuillez vérifier les données générées")
            
            logger.info("=" * 60)
            
            # Retourner les résultats pour le rapport
            return resultats
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification : {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    resultats = verifier_donnees()
    
    # Enregistrer les résultats dans un fichier
    with open("verification_j1.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("RAPPORT DE VÉRIFICATION - JOUR 1\n")
        f.write(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write("=" * 60 + "\n")
        if resultats:
            for key, value in resultats.items():
                f.write(f"{key}: {value}\n")