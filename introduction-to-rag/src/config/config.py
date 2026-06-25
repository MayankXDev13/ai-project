import os
from dotenv import load_dotenv

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "changeme-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
