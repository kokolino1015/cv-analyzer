CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS listings (
    id      SERIAL PRIMARY KEY,
    company TEXT,
    title   TEXT,
    text    TEXT NOT NULL,
    UNIQUE (company, title)
);

CREATE TABLE IF NOT EXISTS chunks (
    id           SERIAL PRIMARY KEY,
    listing_id   INTEGER REFERENCES listings(id) ON DELETE CASCADE,
    chunk_index  INTEGER,
    text         TEXT NOT NULL,
    embedding    vector(768)
);