import os
import httpx
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cv:cv@localhost:5432/cvanalyzer")
EMBED_MODEL = "nomic-embed-text"


def embed_text(text: str) -> list[float]:
    response = httpx.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["embedding"]


def chunk_text(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def insert_listings(listings: list[dict]) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for item in listings:
                cur.execute(
                    "INSERT INTO listings (company, title, text) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (company, title) DO UPDATE "
                    "SET text = EXCLUDED.text "
                    "RETURNING id",
                    (item["company"], item["title"], item["text"]),
                )
                listing_id = cur.fetchone()[0]

                cur.execute("DELETE FROM chunks WHERE listing_id = %s", (listing_id,))

                for index, chunk in enumerate(chunk_text(item["text"])):
                    cur.execute(
                        "INSERT INTO chunks (listing_id, chunk_index, text, embedding) "
                        "VALUES (%s, %s, %s, %s)",
                        (listing_id, index, chunk, embed_text(chunk)),
                    )


def search(query: str, top_k: int = 5) -> list[tuple]:
    query_embedding = Vector(embed_text(query))
    with psycopg.connect(DATABASE_URL) as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM (SELECT DISTINCT
                      ON (l.id) l.company, l.title, l.text,
                          c.embedding <=> %s::vector AS distance
                      FROM chunks c JOIN listings l
                      ON l.id = c.listing_id
                      ORDER BY l.id, distance) best
                ORDER BY distance
                    LIMIT %s
                """,
                (query_embedding, top_k),
            )
            return cur.fetchall()