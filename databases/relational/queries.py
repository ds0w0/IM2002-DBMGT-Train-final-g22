"""
TransitFlow — PostgreSQL / Relational Database Layer
=====================================================
This module handles all queries to PostgreSQL.

TWO ROLES ARE SERVED HERE:
  1. Relational  → dual-network transit (metro + national rail),
                   availability, fares, bookings, seat selection
  2. Vector      → policy document similarity search (pgvector)

STUDENT TASK
------------
Design your schema in databases/relational/schema.sql, seed it with
skeleton/seed_postgres.py, then implement the query functions below.

Functions prefixed with `query_`  are read-only lookups called by the agent.
Functions prefixed with `execute_` are write operations (booking/cancellation).

The vector functions (query_policy_vector_search, store_policy_document)
are already implemented — do not modify them.
"""

from __future__ import annotations

import json
import random
import string
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

from skeleton.config import PG_DSN, VECTOR_TOP_K, VECTOR_SIMILARITY_THRESHOLD

import hashlib
import secrets

def _connect():
    """Return a new psycopg2 connection with autocommit enabled."""
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True
    return conn


def _gen_booking_id() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"BK-{suffix}"


def _gen_payment_id() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"PM-{suffix}"


# ── Example ───────────────────────────────────────────────────────────────────
# The block below shows the query pattern: open a cursor, run SQL, return rows.
# Use _connect() for read-only queries; for write operations use a manual
# connection with conn.commit() / conn.rollback() (see execute_booking below).

def example_query() -> dict:
    """Example: returns the name of the connected database."""
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT current_database() AS db;")
            return dict(cur.fetchone())

# TODO: Implement the query_ and execute_ functions below.
# ─────────────────────────────────────────────────────────────────────────────


# ── NATIONAL RAIL AVAILABILITY ────────────────────────────────────────────────

def query_national_rail_availability(
    origin_id: str,
    destination_id: str,
    travel_date: Optional[str] = None,
) -> list[dict]:
    """
    Return national rail schedules that serve both origin and destination stations
    in the correct order, along with seat occupancy for the requested travel date.

    Args:
        origin_id:       e.g. "NR01"
        destination_id:  e.g. "NR05"
        travel_date:     e.g. "2025-06-01" — used to count bookings; omit for general info
    """
    raise NotImplementedError("TODO: implement after designing your schema")


def query_national_rail_fare(
    schedule_id: str,
    fare_class: str,
    stops_travelled: int,
) -> Optional[dict]:
    """
    Calculate the fare for a national rail journey.

    Args:
        schedule_id:     e.g. "NR_SCH01"
        fare_class:      "standard" or "first"
        stops_travelled: number of stops between origin and destination (inclusive)

    Returns:
        dict with fare_class, base_fare_usd, per_stop_rate_usd, total_fare_usd
    """
    raise NotImplementedError("TODO: implement after designing your schema")


# ── METRO SCHEDULES & FARE ────────────────────────────────────────────────────

def query_metro_schedules(origin_id: str, destination_id: str) -> list[dict]:
    """
    Return metro schedules that serve both origin and destination in the correct order.

    Args:
        origin_id:       e.g. "MS01"
        destination_id:  e.g. "MS09"
    """
    raise NotImplementedError("TODO: implement after designing your schema")


def query_metro_fare(schedule_id: str, stops_travelled: int) -> Optional[dict]:
    """
    Calculate the metro fare for a single-ticket journey.

    Args:
        schedule_id:     e.g. "MS_SCH01"
        stops_travelled: number of stops between origin and destination

    Returns:
        dict with base_fare_usd, per_stop_rate_usd, total_fare_usd
    """
    raise NotImplementedError("TODO: implement after designing your schema")


# ── SEAT SELECTION ────────────────────────────────────────────────────────────

def query_available_seats(
    schedule_id: str,
    travel_date: str,
    fare_class: str,
) -> list[dict]:
    """
    Return available seats for a national rail journey on a given date.

    Args:
        schedule_id:  e.g. "NR_SCH01"
        travel_date:  e.g. "2025-06-01"
        fare_class:   "standard" or "first"

    Returns:
        List of dicts: {seat_id, coach, row, column}
    """
    raise NotImplementedError("TODO: implement after designing your schema")


def auto_select_adjacent_seats(available_seats: list[dict], count: int) -> list[str]:
    """
    Select `count` seats that are as close together as possible (same row preferred,
    then adjacent rows). Returns a list of seat_ids.

    Args:
        available_seats: output of query_available_seats()
        count:           number of seats needed
    """
    if not available_seats or count <= 0:
        return []
    if count >= len(available_seats):
        return [s["seat_id"] for s in available_seats[:count]]

    from collections import defaultdict
    rows: dict[int, list[dict]] = defaultdict(list)
    for seat in available_seats:
        rows[seat["row"]].append(seat)

    for row_seats in sorted(rows.values(), key=lambda s: s[0]["row"]):
        if len(row_seats) >= count:
            return [s["seat_id"] for s in row_seats[:count]]

    sorted_seats = sorted(available_seats, key=lambda s: (s["row"], s["column"]))
    return [s["seat_id"] for s in sorted_seats[:count]]


# ── USER & BOOKING QUERIES ────────────────────────────────────────────────────

def query_user_profile(user_email: str) -> Optional[dict]:
    """Return a user's profile by email."""
    raise NotImplementedError("TODO: implement after designing your schema")


def query_user_bookings(user_email: str) -> dict:
    """
    Return a user's combined booking history (national rail + metro).

    Returns:
        dict with keys 'national_rail' (list) and 'metro' (list)
    """
    raise NotImplementedError("TODO: implement after designing your schema")


def query_payment_info(booking_id: str) -> Optional[dict]:
    """Return payment record for a booking or metro trip."""
    raise NotImplementedError("TODO: implement after designing your schema")


# ── TRANSACTIONAL OPERATIONS ──────────────────────────────────────────────────

def execute_booking(
    user_id: str,
    schedule_id: str,
    origin_station_id: str,
    destination_station_id: str,
    travel_date: str,
    fare_class: str,
    seat_id: str,
    ticket_type: str = "single",
) -> tuple[bool, dict | str]:
    """
    Create a national rail booking for a logged-in user.

    Args:
        user_id:                e.g. "RU01" — must match the logged-in user
        schedule_id:            e.g. "NR_SCH01"
        origin_station_id:      e.g. "NR01"
        destination_station_id: e.g. "NR05"
        travel_date:            e.g. "2025-06-01"
        fare_class:             "standard" or "first"
        seat_id:                e.g. "B05" (or "any" to auto-assign)
        ticket_type:            "single" (default) or "return"

    Returns:
        (True, booking_dict)   on success
        (False, error_message) on failure
    """
    raise NotImplementedError("TODO: implement after designing your schema")


def execute_cancellation(booking_id: str, user_id: str) -> tuple[bool, dict | str]:
    """
    Cancel a national rail booking owned by the given user.

    Calculates the refund amount according to the booking's service type:
      - Normal service: RF001 windows (100% / 75% / 50% / 0%)
      - Express service: RF002 windows (100% / 50% / 0%)

    Args:
        booking_id: e.g. "BK001"
        user_id:    must match the booking's user_id

    Returns:
        (True, result_dict)  with refund_amount_usd and policy note
        (False, error_msg)
    """
    raise NotImplementedError("TODO: implement after designing your schema")


# ── AUTHENTICATION QUERIES ────────────────────────────────────────────────────

# ── AUTHENTICATION QUERIES ────────────────────────────────────────────────────

def register_user(
    email: str,
    first_name: str,
    surname: str,
    year_of_birth: int,
    password: str,
    secret_question: str,
    secret_answer: str,
    ) -> tuple[bool, str]:
    """
    Register a new user with advanced SHA-256 salted password hashing.
    Returns (True, user_id) on success or (False, error_message) on failure.
    """
    # 根據 full_name 的評分規則，組合姓名
    full_name = f"{first_name} {surname}"
    # 生成全新的 user_id (例如利用隨機生成或查表，這裡依據資料庫規範生成)
    # 為了對齊種子格式 (RUxx)，我們現場生成一個隨機或基於序列的ID，最穩妥是使用大寫英數組合
    suffix = "".join(secrets.choices(string.ascii_uppercase + string.digits, k=4))
    user_id = f"U-{suffix}"
    
    # 處理出生日期 DATE (格式要求為 YYYY-MM-DD，預設取該年1月1日)
    date_of_birth = f"{year_of_birth}-01-01"
    registered_at = datetime.now(timezone.utc)

    # 由於需要跨兩張表，使用手動控制的事務處理 (Transaction)
    sql_user = """
        INSERT INTO users (user_id, full_name, email, date_of_birth, secret_question, secret_answer, registered_at, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE);
    """
    
    # 資安強化：生成 Salt 並進行密碼 Hash
    salt = secrets.token_hex(16)
    hash_input = password + salt
    password_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    sql_cred = """
        INSERT INTO user_credentials (user_id, password_hash, password_salt)
        VALUES (%s, %s, %s);
    """
    
    # 建立手動 Commit 的連線處理
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False # 開啟嚴格事務機制
    try:
        with conn.cursor() as cur:
            # 1. 寫入 users 基本表
            cur.execute(sql_user, (user_id, full_name, email, date_of_birth, secret_question, secret_answer, registered_at))
            # 2. 寫入 user_credentials 認證表
            cur.execute(sql_cred, (user_id, password_hash, salt))
            
        conn.commit() # 兩張表都成功，才進磁碟
        return True, user_id
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "Email already registered"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def login_user(email: str, password: str) -> Optional[dict]:
    """
    Verify credentials using the salted password hashing flow. 
    Returns a user dict on success or None on failure.
    """
    # 1. 先用 email 找出使用者的基本資料與資安金鑰
    sql = """
        SELECT u.user_id, u.email, u.full_name, u.phone, u.date_of_birth, u.is_active,
               c.password_hash, c.password_salt
        FROM users u
        JOIN user_credentials c ON u.user_id = c.user_id
        WHERE u.email = %s AND u.is_active = TRUE;
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (email,))
            user_record = cur.fetchone()
            
            if not user_record:
                return None
            
            # 2. 現場將輸入的明文密碼加上該使用者的專屬 salt 進行 SHA-256 雜湊
            stored_hash = user_record["password_hash"]
            salt = user_record["password_salt"]
            
            hash_input = password + salt
            computed_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            
            # 3. 比對密碼雜湊值
            if computed_hash == stored_hash:
                # 依據簽名規範補齊 first_name 與 surname 返回給 Agent 讀取
                name_parts = user_record["full_name"].split(" ", 1)
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                surname = name_parts[1] if len(name_parts) > 1 else ""
                
                return {
                    "user_id": user_record["user_id"],
                    "email": user_record["email"],
                    "full_name": user_record["full_name"],
                    "first_name": first_name,
                    "surname": surname,
                    "phone": user_record["phone"],
                    "date_of_birth": str(user_record["date_of_birth"]),
                    "is_active": user_record["is_active"]
                }
            
            return None


def get_user_secret_question(email: str) -> Optional[str]:
    """Return the secret question for a registered email, or None if not found."""
    sql = "SELECT secret_question FROM users WHERE email = %s;"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            return row[0] if row else None

def verify_secret_answer(email: str, answer: str) -> bool:
    """Return True if the provided answer matches the stored secret answer (case-insensitive)."""
    sql = "SELECT secret_answer FROM users WHERE email = %s;"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (email,))
            row = cur.fetchone()
            if row and row[0]:
                # 實作題目要求的 case-insensitive (大小寫無關比對)
                return row[0].strip().lower() == answer.strip().lower()
            return False

def update_password(email: str, new_password: str) -> bool:
    """Update the password for a user using a new randomized salt. Returns True if updated."""
    # 1. 找出該 email 對應的 user_id
    sql_find = "SELECT user_id FROM users WHERE email = %s;"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_find, (email,))
            row = cur.fetchone()
            if not row:
                return False
            user_id = row[0]

    # 2. 生成全新隨機鹽巴並雜湊新密碼
    new_salt = secrets.token_hex(16)
    hash_input = new_password + new_salt
    new_password_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    sql_update = """
        UPDATE user_credentials 
        SET password_hash = %s, password_salt = %s 
        WHERE user_id = %s;
    """
    
    # 執行寫入
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_update, (new_password_hash, new_salt, user_id))
            return cur.rowcount > 0
    finally:
        conn.close()


# ── VECTOR / RAG QUERIES — do not modify ─────────────────────────────────────

def query_policy_vector_search(embedding: list[float], top_k: int = VECTOR_TOP_K) -> list[dict]:
    """
    Find the most relevant policy documents for a given query embedding.

    Args:
        embedding: Query vector from llm.embed(user_question)
        top_k:     Number of results to return

    Returns:
        List of dicts with title, category, content, and similarity score
    """
    sql = """
        SELECT
            title,
            category,
            content,
            1 - (embedding <=> %s::vector) AS similarity
        FROM policy_documents
        WHERE 1 - (embedding <=> %s::vector) > %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (vec_str, vec_str, VECTOR_SIMILARITY_THRESHOLD, vec_str, top_k))
            return [dict(row) for row in cur.fetchall()]


def store_policy_document(
    title: str,
    category: str,
    content: str,
    embedding: list[float],
    source_file: str = "",
) -> int:
    """
    Insert a policy document with its embedding into the database.
    Used by skeleton/seed_vectors.py — students don't need to call this directly.

    Returns:
        The new document's id
    """
    sql = """
        INSERT INTO policy_documents (title, category, content, embedding, source_file)
        VALUES (%s, %s, %s, %s::vector, %s)
        RETURNING id
    """
    vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (title, category, content, vec_str, source_file))
            return cur.fetchone()[0]
