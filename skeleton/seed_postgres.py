"""
Seed PostgreSQL with all TransitFlow mock data from train-mock-data/.

Usage:
    python skeleton/seed_postgres.py

Run AFTER docker-compose up -d.
You must first design and create your tables in databases/relational/schema.sql.
Safe to re-run: implement your inserts with ON CONFLICT DO NOTHING.
"""

import json
import os
import sys

import psycopg2
from psycopg2.extras import execute_values

import hashlib
import secrets

# ── resolve paths ────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR    = os.path.join(PROJECT_DIR, "train-mock-data")

sys.path.insert(0, PROJECT_DIR)
from skeleton import config as cfg


def load(filename):
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


def connect():
    return psycopg2.connect(
        host=cfg.PG_HOST,
        port=cfg.PG_PORT,
        dbname=cfg.PG_DB,
        user=cfg.PG_USER,
        password=cfg.PG_PASSWORD,
    )


def insert_many(cur, table, columns, rows):
    """Bulk insert with ON CONFLICT DO NOTHING. Returns row count inserted."""
    if not rows:
        return 0
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s "
        f"ON CONFLICT DO NOTHING"
    )
    execute_values(cur, sql, rows)
    return cur.rowcount


# ── seeders ──────────────────────────────────────────────────────────────────

def seed_metro_stations(cur):
    data = load("metro_stations.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    # Each item in `data` is a dict — inspect the JSON to see available fields.
    pass


def seed_national_rail_stations(cur):
    data = load("national_rail_stations.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


def seed_metro_schedules(cur):
    data = load("metro_schedules.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


def seed_national_rail_schedules(cur):
    data = load("national_rail_schedules.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


def seed_seat_layouts(cur):
    data = load("national_rail_seat_layouts.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass

def seed_users(cur):
    data = load("registered_users.json")
    
    user_rows = []
    credential_rows = []
    
    for u in data:
        # ---- 1. 準備 users 基本資料 ----
        user_rows.append((
            u["user_id"], u["full_name"], u["email"], u["phone"],
            u["date_of_birth"], u["secret_question"], u["secret_answer"],
            u["registered_at"], u["is_active"]
        ))
        
        # ---- 2. 資安強化：生成 Salt 並進行密碼 Hash ----
        # 隨機生成 16 位元組的十六進位 Salt
        salt = secrets.token_hex(16) 
        plaintext_password = u["password"]
        
        # 將 明碼密碼 + Salt 進行 SHA-256 雜湊
        hash_input = plaintext_password + salt
        password_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        credential_rows.append((
            u["user_id"],
            password_hash,
            salt
        ))
        
    # ---- 3. 寫入第一張表：users ----
    user_columns = [
        "user_id", "full_name", "email", "phone", 
        "date_of_birth", "secret_question", "secret_answer", 
        "registered_at", "is_active"
    ]
    n_users = insert_many(cur, "users", user_columns, user_rows)
    print(f"  users: {n_users} rows inserted")
    
    # ---- 4. 寫入第二張表：user_credentials ----
    cred_columns = ["user_id", "password_hash", "password_salt"]
    n_creds = insert_many(cur, "user_credentials", cred_columns, credential_rows)
    print(f"  user_credentials: {n_creds} rows inserted")

def seed_national_rail_bookings(cur):
    data = load("bookings.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


def seed_metro_travels(cur):
    data = load("metro_travel_history.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


def seed_payments(cur):
    data = load("payments.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


def seed_feedback(cur):
    data = load("feedback.json")
    # TODO: Design your table schema, then implement the INSERT logic here.
    pass


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to PostgreSQL...")
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        print("Seeding tables (dependency order):")
        seed_metro_stations(cur)
        seed_national_rail_stations(cur)
        seed_metro_schedules(cur)
        seed_national_rail_schedules(cur)
        seed_seat_layouts(cur)
        seed_users(cur)
        seed_national_rail_bookings(cur)
        seed_metro_travels(cur)
        seed_payments(cur)
        seed_feedback(cur)
        conn.commit()
        print("\nAll done. Database seeded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
