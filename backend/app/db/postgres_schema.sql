CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS semantic_cache_entries (

    id BIGSERIAL PRIMARY KEY,

    application_id INTEGER NOT NULL,

    cache_key TEXT NOT NULL,

    model TEXT NOT NULL,

    prompt_text TEXT NOT NULL,

    response_json JSONB NOT NULL,

    embedding vector(384) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    expires_at TIMESTAMPTZ,

    hit_count INTEGER NOT NULL DEFAULT 0
);


CREATE INDEX IF NOT EXISTS
semantic_cache_entries_application_idx
ON semantic_cache_entries(application_id);


CREATE INDEX IF NOT EXISTS
semantic_cache_entries_model_idx
ON semantic_cache_entries(
    application_id,
    model
);


CREATE INDEX IF NOT EXISTS
semantic_cache_entries_embedding_hnsw_idx
ON semantic_cache_entries
USING hnsw (
    embedding vector_cosine_ops
);