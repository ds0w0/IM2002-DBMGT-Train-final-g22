-- ============================================================
--  TransitFlow PostgreSQL Schema
--  Seed data is loaded separately by: python skeleton/seed_postgres.py
--
--  TWO ROLES:
--    1. Relational  → dual-network transit data you design below
--    2. Vector      → policy documents for RAG (provided — do not modify)
-- ============================================================

-- ============================================================
--  STUDENT TASK — Design and create your relational tables here
--
--  Start from the mock data in train-mock-data/:
--    metro_stations.json, national_rail_stations.json
--    metro_schedules.json, national_rail_schedules.json
--    national_rail_seat_layouts.json
--    registered_users.json
--    bookings.json, metro_travel_history.json
--    payments.json, feedback.json
--
--  Think about:
--    - What tables do you need?
--    - What columns and data types?
--    - Which fields are primary keys? Which are foreign keys?
--    - What constraints make sense?
--
--  Apply your schema with:
--    docker-compose down -v && docker-compose up -d
-- ============================================================

-- 1. 使用者基本資料表 (不含密碼)
CREATE TABLE IF NOT EXISTS users (
    user_id         VARCHAR(10)  PRIMARY KEY,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    phone           VARCHAR(20),
    date_of_birth   DATE,
    secret_question TEXT,
    secret_answer   TEXT,
    registered_at   TIMESTAMPTZ  NOT NULL,
    is_active       BOOLEAN      DEFAULT TRUE
);

-- 2. 獨立的密碼與安全認證表 (分開儲存，使用 salt)
CREATE TABLE IF NOT EXISTS user_credentials (
    user_id       VARCHAR(10)  PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    password_hash VARCHAR(128) NOT NULL,
    password_salt VARCHAR(64)  NOT NULL
);



-- ============================================================
--  VECTOR SCHEMA  (RAG / Help Desk) — do not modify
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS policy_documents (
    id          SERIAL       PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    category    VARCHAR(50)  NOT NULL,  -- 'refund', 'booking', 'conduct'
    content     TEXT         NOT NULL,
    -- 768-dim  → Ollama nomic-embed-text (default)
    -- 3072-dim → Gemini gemini-embedding-001
    -- If you switch LLM_PROVIDER to gemini, change to vector(3072) and reset the database.
    embedding   vector(768),
    source_file VARCHAR(200),
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- Index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS ON policy_documents USING hnsw (embedding vector_cosine_ops);
