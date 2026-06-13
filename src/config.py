"""
Configuration de LinkUpDS API.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret_key_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

# API Configuration
API_TITLE = "LinkUpDS API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Backend du réseau social LinkUpDS basé sur Neo4j"

# Pagination
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
DEFAULT_SKIP = 0

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
