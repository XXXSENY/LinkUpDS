"""
Script de vérification et d'auto‑rangement de la structure du projet.
Exécution : python scripts/check_and_fix_structure.py
"""

import os
import sys

# Dossiers obligatoires
REQUIRED_DIRS = [
    "scripts",
    "src",
    "src/utils",
    "src/routers",
    "src/models",
    "src/dependencies",
    "docs"
]

# Fichiers obligatoires (contenu par défaut minimal)
REQUIRED_FILES = {
    "scripts/__init__.py": "",
    "scripts/init_db.py": "# Script d'initialisation Neo4j\n",
    "scripts/data_generator.py": "# Générateur de données fictives\n",
    "src/__init__.py": "",
    "src/config.py": "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n",
    "src/db_utils.py": "from neo4j import GraphDatabase\n\nclass LinkUpDB:\n    pass\n",
    "src/exceptions.py": "",
    "src/utils/__init__.py": "",
    "src/utils/security.py": "# Hachage et JWT\n",
    "src/routers/__init__.py": "",
    "src/models/__init__.py": "",
    "src/dependencies/__init__.py": "",
    "app.py": "import streamlit as st\nst.title('LinkUpDS')\n",
    "api.py": "from fastapi import FastAPI\napp = FastAPI()\n",
    "requirements.txt": "streamlit\nneo4j\nfaker\npython-dotenv\nfastapi\nuvicorn\n",
    ".env.example": "NEO4J_URI=bolt://localhost:7687\nNEO4J_USER=neo4j\nNEO4J_PASSWORD=motdepasse123\nSECRET_KEY=ma_super_cle\n",
    "GUIDE.md": "# LinkUpDS - Guide utilisateur\n",
    "README.md": "# LinkUpDS\nRéseau social intelligent\n"
}

def check_and_fix():
    print("=" * 60)
    print("🔍 VÉRIFICATION DE LA STRUCTURE DU PROJET")
    print("=" * 60)
    
    # 1. Création des dossiers manquants
    print("\n📁 Vérification des dossiers...")
    for d in REQUIRED_DIRS:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"   ✅ Dossier créé : {d}")
        else:
            print(f"   ✓ Dossier existant : {d}")
    
    # 2. Création des fichiers manquants
    print("\n📄 Vérification des fichiers...")
    for filepath, default_content in REQUIRED_FILES.items():
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(default_content)
            print(f"   ✅ Fichier créé : {filepath}")
        else:
            print(f"   ✓ Fichier existant : {filepath}")
    
    # 3. Vérification spécifique : fichier .env
    if not os.path.exists(".env"):
        print("\n⚠️  Le fichier .env est manquant. Copie depuis .env.example :")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("   ✅ .env créé à partir de .env.example")
        else:
            print("   ❌ .env.example manque aussi → créez le .env manuellement")
    else:
        print("\n   ✓ .env existant")
    
    # 4. Vérification des imports critiques
    print("\n🧪 Vérification des imports Python...")
    try:
        from src.db_utils import LinkUpDB
        print("   ✅ src.db_utils importable")
    except Exception as e:
        print(f"   ❌ Erreur dans src.db_utils : {e}")
    
    try:
        import streamlit
        print("   ✅ streamlit trouvé")
    except ImportError:
        print("   ❌ streamlit non installé → pip install streamlit")
    
    try:
        import neo4j
        print("   ✅ neo4j trouvé")
    except ImportError:
        print("   ❌ neo4j non installé → pip install neo4j")
    
    # 5. Rapport final
    print("\n" + "=" * 60)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 60)
    print("\n💡 Si des fichiers étaient manquants, ils ont été créés avec un contenu minimal.")
    print("   Pensez à les compléter avec le vrai code.")

if __name__ == "__main__":
    check_and_fix()
