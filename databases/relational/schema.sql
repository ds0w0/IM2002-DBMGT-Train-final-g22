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

-- 3. 國家鐵路訂票紀錄表
CREATE TABLE IF NOT EXISTS national_rail_bookings (
    booking_id             VARCHAR(20)   PRIMARY KEY,
    user_id                VARCHAR(10)   NOT NULL REFERENCES users(user_id),
    schedule_id            VARCHAR(20)   NOT NULL, 
    origin_station_id      VARCHAR(10)   NOT NULL, 
    destination_station_id VARCHAR(10)   NOT NULL, 
    travel_date            DATE          NOT NULL,
    departure_time         VARCHAR(10)   NOT NULL,
    ticket_type            VARCHAR(20)   NOT NULL, 
    fare_class             VARCHAR(20)   NOT NULL, 
    coach                  CHAR(2)       NOT NULL,
    seat_id                VARCHAR(10)   NOT NULL,
    stops_travelled        INT           NOT NULL,
    amount_usd             NUMERIC(10,2) NOT NULL,
    status                 VARCHAR(20)   NOT NULL, 
    booked_at              TIMESTAMPTZ   NOT NULL,
    travelled_at           TIMESTAMPTZ   
);

-- 4. 付款紀錄表
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(20)   PRIMARY KEY,
    booking_id VARCHAR(20)   NOT NULL, 
    amount_usd NUMERIC(10,2) NOT NULL, 
    method     VARCHAR(50)   NOT NULL, 
    status     VARCHAR(20)   NOT NULL, 
    paid_at    TIMESTAMPTZ   NOT NULL  
);

-- 5. 乘客滿度回饋與評論表
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id  VARCHAR(20) PRIMARY KEY,
    booking_id   VARCHAR(20) NOT NULL, 
    user_id      VARCHAR(10) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    rating       INT         NOT NULL CHECK (rating >= 1 AND rating <= 5), 
    comment      TEXT,                 
    submitted_at TIMESTAMPTZ NOT NULL
);

-- 6. 捷運搭乘歷史紀錄表 (對齊 Task 2b query_user_bookings)
CREATE TABLE IF NOT EXISTS metro_travel_history (
    trip_id                VARCHAR(20)   PRIMARY KEY,
    user_id                VARCHAR(10)   NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    schedule_id            VARCHAR(20)   NOT NULL, -- 對齊捷運班表 ID
    origin_station_id      VARCHAR(10)   NOT NULL, -- 進站捷運站 ID
    destination_station_id VARCHAR(10),            -- 出站捷運站 ID (允許為空以防尚未刷出)
    tap_in_at              TIMESTAMPTZ   NOT NULL, -- 進站刷卡時間
    tap_out_at             TIMESTAMPTZ,            -- 出站刷卡時間
    fare_usd               NUMERIC(10,2) NOT NULL, -- 精準捷運票價
    status                 VARCHAR(20)   NOT NULL  -- 'completed', 'active' 等狀態
);

-- 7. 捷運站點表
CREATE TABLE IF NOT EXISTS metro_stations (
    station_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lines JSONB NOT NULL,
    zone INT,
    has_interchange BOOLEAN DEFAULT FALSE
);

-- 8. 國家鐵路站點表
CREATE TABLE IF NOT EXISTS national_rail_stations (
    station_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    has_interchange BOOLEAN DEFAULT FALSE
);

-- 9. 捷運班表 (包含 JSONB 以支援複雜陣列查詢)
CREATE TABLE IF NOT EXISTS metro_schedules (
    schedule_id VARCHAR(20) PRIMARY KEY,
    line VARCHAR(10) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    origin_station_id VARCHAR(10) NOT NULL,
    destination_station_id VARCHAR(10) NOT NULL,
    stops_in_order JSONB NOT NULL,
    first_train_time VARCHAR(10),
    last_train_time VARCHAR(10),
    travel_time_from_origin_min JSONB,
    base_fare_usd NUMERIC(10,2),
    per_stop_rate_usd NUMERIC(10,2),
    frequency_min INT
);

-- 10. 國家鐵路班表
CREATE TABLE IF NOT EXISTS national_rail_schedules (
    schedule_id VARCHAR(20) PRIMARY KEY,
    train_number VARCHAR(20),
    route_name VARCHAR(100),
    origin_station_id VARCHAR(10) NOT NULL,
    destination_station_id VARCHAR(10) NOT NULL,
    departure_time VARCHAR(10),
    arrival_time VARCHAR(10),
    route_stations VARCHAR[] NOT NULL, -- 支援 ARRAY[%s, %s] 查詢
    travel_time_from_origin_min JSONB,
    base_fare_usd NUMERIC(10,2),
    per_stop_rate_usd NUMERIC(10,2),
    total_seats INT DEFAULT 40
);

-- 11. 國家鐵路座位佈局表
CREATE TABLE IF NOT EXISTS seat_layouts (
    id SERIAL PRIMARY KEY,
    coach VARCHAR(2) NOT NULL,
    seat_id VARCHAR(10) NOT NULL,
    seat_row INT NOT NULL,
    seat_column VARCHAR(2) NOT NULL,
    fare_class VARCHAR(20) NOT NULL
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
CREATE INDEX IF NOT EXISTS idx_policy_documents_embedding ON policy_documents USING hnsw (embedding vector_cosine_ops);
