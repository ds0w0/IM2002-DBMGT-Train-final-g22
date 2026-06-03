# AI Session Context — TransitFlow

**How to use this file:**
At the start of every AI coding session, paste the full contents of this file as your first message to your AI assistant. This gives the AI the context it needs to produce code that fits your codebase and is consistent with your teammates' work.

**Who maintains this file:**
Whoever makes a schema change or architectural decision updates this file in the same commit. Treat it like a team contract.

---

## Project Overview

TransitFlow is a Python-based AI chat assistant for a fictional transit operator. It queries three databases — PostgreSQL (relational + vector), Neo4j (graph) — and uses an LLM to answer user questions. Our task as students is to design the database schema and implement the query functions in `databases/relational/queries.py` and `databases/graph/queries.py`.

## Tech Stack

- Language: Python 3.11+
- Relational DB: PostgreSQL via `psycopg2` with `RealDictCursor`
- Graph DB: Neo4j via the `neo4j` Python driver
- Vector search: `pgvector` extension (already implemented — do not modify)
- Web UI: Gradio
- LLM: Google Gemini or local Ollama (configured via `.env`)

## Coding Conventions

- **Naming:** `snake_case` for all Python names and SQL identifiers
- **Docstrings:** All functions must have a docstring with `Args:` and `Returns:` sections
- **Return types:** Use type hints. Read-only functions return `list[dict]` or `Optional[dict]`
- **Empty results:** Return `[]` or `None` (as documented), never raise an exception for "not found"
- **SQL:** Use `%s` placeholders for all user inputs — never string-format into SQL
- **Relational pattern:** Use `_connect()` helper + `psycopg2.extras.RealDictCursor`:
  ```python
  with _connect() as conn:
      with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
          cur.execute("SELECT ...", (param,))
          return [dict(row) for row in cur.fetchall()]
  ```
- **Graph pattern:** Use `_driver()` helper + session:
  ```python
  with _driver() as driver:
      with driver.session() as session:
          result = session.run("MATCH ...", station_id=station_id)
          return [dict(record) for record in result]
  ```

## Agreed Relational Schema

<!-- ============================================================
  FILL THIS IN after your team completes the schema design workshop.
  Paste your final CREATE TABLE statements here.
  ============================================================ -->

```sql
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

-- 為 national_rail_bookings 的外鍵加上 HASH/B-TREE 索引
CREATE INDEX IF NOT EXISTS idx_rail_bookings_user_id ON national_rail_bookings(user_id);

-- 為 feedback 的外鍵加上索引
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);

-- 為 metro_travel_history 的外鍵加上索引
CREATE INDEX IF NOT EXISTS idx_metro_history_user_id ON metro_travel_history(user_id);

```

## Agreed Graph Schema

<!-- ============================================================
  FILL THIS IN after your team agrees on Neo4j node labels and
  relationship types.
  ============================================================ -->

```
Node labels:
- `MetroStation`: Represents a physical transit station on the subway network.
- `RailStation`: Represents a physical transit station on the national rail network.

Relationship types:
- `METRO_LINK`: Connects adjacent `MetroStation` nodes with route tracking.
- `RAIL_LINK`: Connects adjacent `RailStation` nodes with route attributes.
- `INTERCHANGE_TO`: Represents a pedestrian transfer gateway link connecting a `MetroStation` and a `RailStation` at co-located transit hubs.

Key properties:
- `station_id` (String, Unique PK on all nodes)
- `name` (String)
- `travel_time_min` (Integer/Float on `METRO_LINK`, `RAIL_LINK`, and `INTERCHANGE_TO` relationships representing edge traversal costs)
```

## Function Signatures We Are Implementing

These are fixed contracts. AI-generated code must match these signatures exactly.

### Relational (`databases/relational/queries.py`)

```python
# Read-only
def query_national_rail_availability(origin_id: str, destination_id: str, travel_date: Optional[str] = None) -> list[dict]: ...
def query_national_rail_fare(schedule_id: str, fare_class: str, stops_travelled: int) -> Optional[dict]: ...
def query_metro_schedules(origin_id: str, destination_id: str) -> list[dict]: ...
def query_metro_fare(schedule_id: str, stops_travelled: int) -> Optional[dict]: ...
def query_available_seats(schedule_id: str, travel_date: str, fare_class: str) -> list[dict]: ...
def query_user_profile(user_email: str) -> Optional[dict]: ...
def query_user_bookings(user_email: str) -> dict: ...  # returns {"national_rail": [...], "metro": [...]}
def query_payment_info(booking_id: str) -> Optional[dict]: ...

# Write operations
def execute_booking(user_id, schedule_id, origin_station_id, destination_station_id, travel_date, fare_class, seat_id, ticket_type="single") -> tuple[bool, dict | str]: ...
def execute_cancellation(booking_id: str, user_id: str) -> tuple[bool, dict | str]: ...

# Auth
def register_user(email, first_name, surname, year_of_birth, password, secret_question, secret_answer) -> tuple[bool, str]: ...
def login_user(email: str, password: str) -> Optional[dict]: ...
def get_user_secret_question(email: str) -> Optional[str]: ...
def verify_secret_answer(email: str, answer: str) -> bool: ...
def update_password(email: str, new_password: str) -> bool: ...
```

### Graph (`databases/graph/queries.py`)

```python
def query_shortest_route(origin_id: str, destination_id: str, network: str = "auto") -> dict: ...
def query_cheapest_route(origin_id: str, destination_id: str, network: str = "auto", fare_class: str = "standard") -> dict: ...
def query_alternative_routes(origin_id, destination_id, avoid_station_id, network="auto", max_routes=3) -> list[list[dict]]: ...
def query_interchange_path(origin_id: str, destination_id: str) -> dict: ...
def query_delay_ripple(delayed_station_id: str, hops: int = 2) -> list[dict]: ...
def query_station_connections(station_id: str) -> list[dict]: ...
```

## Team Decisions Log

<!-- Add entries as you make decisions. Format: "Decision: X. Why: Y." -->

- [x] Schema Design: Split sensitive hashes out into a separate `user_credentials` child table linked via 1:1 foreign keys to achieve Third Normal Form (3NF) and isolate core authentication entities.
- [x] Relational Indexes: Attached non-clustered explicit indexes (`idx_rail_bookings_user_id`, `idx_feedback_user_id`, `idx_metro_history_user_id`) on foreign keys to optimize subquery join bottlenecks.
- [x] Graph schema: TODO — add your node label and relationship type decisions here
- [x] Concurrency Isolation: Deployed pessimistic row-level locking (`FOR UPDATE`) inside `execute_booking` transactional scripts to safeguard against race conditions under heavy parallel loads.
- [x] Module Decoupling: Patched runtime circular imports between langconfig pipelines and query functions via dynamic context modules using `importlib`.

## Prompts That Worked

<!-- Share prompts that produced good output so teammates can reuse them. -->

### Schema design prompt that worked:
```
"Design a highly robust PostgreSQL transactional schema for TransitFlow. Isolate sensitive passenger registration data from credentials by engineering a primary users entity and a detached user_credentials child table linked via an asynchronous ON DELETE CASCADE foreign key relation. Ensure all passenger booking logs, polymorphic payment logs, and metro history tracking tables use standard ISO TIMESTAMPTZ zones, exact decimal classes for monetary variables (NUMERIC(10,2)), and possess performance-oriented secondary lookup index bindings on every foreign key column identifier."
```

### Query implementation prompt that worked:
```
Refactor the `query_travel_policies` function inside `databases/relational/queries.py` to decouple semantic embeddings query patterns. Avoid direct relational hardcoding by importing shared utilities dynamically using `importlib.import_module('skeleton.llm')` to cleanly eliminate Python runtime circular-dependency blocks.
```
