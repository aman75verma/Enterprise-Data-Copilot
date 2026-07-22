import os
import sys

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from ingest_docs import vector_literal

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://copilot:copilot_pass@localhost:5433/copilot_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        raise SystemExit('Usage: python backend/db/search_docs.py "how do I set up row level security"')

    model = SentenceTransformer(EMBEDDING_MODEL)
    embedding = vector_literal(model.encode(query))

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT title, source_file, url, content
                FROM doc_chunks
                ORDER BY embedding <-> %s
                LIMIT 5
                """,
                (embedding,),
            )
            for index, (title, source_file, url, content) in enumerate(cur.fetchall(), start=1):
                snippet = " ".join(content.split())[:300]
                print(f"\n{index}. {title}\n   {source_file}\n   {url}\n   {snippet}...")


if __name__ == "__main__":
    main()
