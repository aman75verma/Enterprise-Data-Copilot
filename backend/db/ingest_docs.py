import os
import re
import yaml
import psycopg2
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://copilot:copilot_pass@localhost:5433/copilot_db")
DOCS_DIR = os.getenv(
    "DOCS_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "supabase", "apps", "docs", "content")),
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def parse_frontmatter(content):
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
                if not isinstance(metadata, dict):
                    metadata = {}
                return metadata, parts[2].strip()
            except yaml.YAMLError:
                pass
    return {}, content


def strip_mdx(content):
    content = re.sub(r"^\s*import\s.+?$", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*export\s.+?$", "", content, flags=re.MULTILINE)
    content = re.sub(r"</?[A-Z][^>\n]*(?:>|$)", "", content)
    content = re.sub(r"\{\/\*.*?\*\/\}", "", content, flags=re.DOTALL)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def vector_literal(embedding):
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


def ensure_doc_chunks_table(cur):
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS doc_chunks (
            id SERIAL PRIMARY KEY,
            source_file TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(384),
            title TEXT,
            product TEXT,
            section TEXT,
            url TEXT,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            last_updated TIMESTAMP NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx
        ON doc_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
        """
    )


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata, body = parse_frontmatter(content)
    body = strip_mdx(body)
    title = metadata.get("title") or metadata.get("sidebar_label") or os.path.basename(filepath)
    
    # Infer product from path
    rel_path = os.path.relpath(filepath, DOCS_DIR)
    parts = rel_path.split(os.sep)
    section = parts[0] if parts else "docs"
    product = parts[1] if len(parts) > 1 and parts[0] in {"guides", "reference"} else section
    product = product.replace("-", " ").title()
    
    # url mapping
    url = "/" + rel_path.replace("\\", "/").replace(".mdx", "").replace(".md", "")
    if url.endswith("/index"):
        url = url[:-6]

    return rel_path, title, product, section, url, body

def main():
    if not os.path.isdir(DOCS_DIR):
        raise FileNotFoundError(f"Docs directory not found: {DOCS_DIR}")

    print(f"Loading embedding model ({EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    print("Connecting to Database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    ensure_doc_chunks_table(cur)
    
    print("Clearing existing doc_chunks...")
    cur.execute("TRUNCATE doc_chunks RESTART IDENTITY")
    conn.commit()

    chunk_size = min(500, model.get_max_seq_length() or 500)
    chunk_overlap = min(50, max(0, chunk_size // 5))
    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        model.tokenizer,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    
    print(f"Walking documentation directory: {DOCS_DIR}")
    chunk_count = 0
    file_count = 0
    
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                filepath = os.path.join(root, file)
                rel_path, title, product, section, url, body = process_file(filepath)
                
                chunks = splitter.split_text(body)
                if not chunks:
                    continue
                
                embeddings = model.encode(chunks)
                
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    cur.execute(
                        """
                        INSERT INTO doc_chunks (source_file, content, embedding, title, product, section, url, chunk_index)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (rel_path, chunk, vector_literal(embedding), title, product, section, url, i)
                    )
                    chunk_count += 1
                
                file_count += 1
                if file_count % 50 == 0:
                    print(f"  Processed {file_count} files, {chunk_count} chunks...")
                    conn.commit()
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Success! Inserted {chunk_count} chunks from {file_count} files.")

if __name__ == "__main__":
    main()
