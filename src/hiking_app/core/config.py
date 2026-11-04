import os
from dotenv import load_dotenv

load_dotenv()


def build_db_url(user: str, password: str, host: str, port: int, name: str) -> str:
    return f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=disable"

PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
PG_USER = os.getenv("POSTGRES_USER")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD")
PG_NAME = os.getenv("POSTGRES_DB", "doorbell_db")
PG_DB_URL = build_db_url(PG_USER, PG_PASSWORD, PG_HOST, PG_PORT, PG_NAME)