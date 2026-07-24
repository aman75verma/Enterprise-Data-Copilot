import os
from functools import lru_cache
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://copilot:copilot_pass@localhost:5433/copilot_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def vector_literal(embedding: Any) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


def search_docs(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("Search query cannot be empty")

    safe_top_k = max(1, min(top_k, 10))
    model = get_embedding_model()
    embedding = vector_literal(model.encode(query))

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT title, source_file, url, product, section, chunk_index, content
                FROM doc_chunks
                ORDER BY embedding <-> %s
                LIMIT %s
                """,
                (embedding, safe_top_k),
            )
            return [dict(row) for row in cur.fetchall()]
