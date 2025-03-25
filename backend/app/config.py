import os

POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
DB_POOL_SIZE = os.environ.get("DB_POOL_SIZE", 20)  # Number of connections in the pool

REDIS_HOST = os.environ.get("REDIS_HOST", "redis://localhost:6379")

BACKEND_ROOT_PATH = os.environ.get("BACKEND_ROOT_PATH", "")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Quotas
DEFAULT_EXPERIMENTS_QUOTA = int(os.environ.get("DEFAULT_CONTENT_QUOTA", 3))
DEFAULT_API_QUOTA = int(os.environ.get("DEFAULT_API_QUOTA", 100))
CHECK_API_LIMIT = os.environ.get("CHECK_API_LIMIT", True)
CHECK_EXPERIMENTS_LIMIT = os.environ.get("CHECK_EXPERIMENTS_LIMIT", True)
