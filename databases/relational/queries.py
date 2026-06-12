# TASK 6 EXTENSION: Promo Code & Discount Database Subsystem (ds0w0)
"""
TransitFlow — PostgreSQL / Relational Database Layer
=====================================================
This module handles all queries to PostgreSQL.

TWO ROLES ARE SERVED HERE:
  1. Relational  → dual-network transit (metro + national rail),
                   availability, fares, bookings, seat selection
  2. Vector      → policy document similarity search (pgvector)

# TASK 6 EXTENSION: Promo Code Subsystem (ds0w0)
"""

from __future__ import annotations

import json
import random
import string
from datetime import datetime, timezone
from typing import Optional

import importlib
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


# ── NATIONAL RAIL AVAILABILITY ────────────────────────────────────────────────

def query_national_rail_availability(
    origin_id: str,
    destination_id: str,
    travel_date: Optional[str] = None,
) -> list[dict]:
    """
    Return national rail schedules that serve both origin and destination stations,
    along with dynamically calculated available seat counts for the requested travel date.

    Args:
        origin_id: The identifier of the starting station.
        destination_id: The identifier of the target station.
        travel_date: Optional ISO date string. Defaults to '2026-06-02'.

    Returns:
        A list of available rail schedules with calculated seats.
    """
    if not travel_date:
        travel_date = "2026-06-02"

    # 使用 PostgreSQL 陣列包含運算子 @> 進行高效率查詢，不再使用 1=1 Fallback
    sql = """
        SELECT 
            s.schedule_id,
            s.train_number,
            s.route_name,
            s.departure_time,
            s.arrival_time,
            COALESCE(s.total_seats, 40) AS total_capacity,
            (SELECT COUNT(*)::int 
             FROM national_rail_bookings b 
             WHERE b.schedule_id = s.schedule_id 
               AND b.travel_date = %s 
               AND b.status IN ('completed', 'confirmed')
            ) AS booked_count
        FROM national_rail_schedules s
        WHERE s.route_stations @> ARRAY[%s, %s]::varchar[];
    """

    results = []
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (travel_date, origin_id, destination_id))
            rows = cur.fetchall()
            
            for r in rows:
                total_cap = r["total_capacity"]
                booked = r["booked_count"]
                available_seats = max(0, total_cap - booked)
                
                # 🌟 TASK 6 EXTENSION: 動態計算車廂擁擠度 (Crowdedness Indicator)
                occupancy_rate = booked / total_cap if total_cap > 0 else 0
                if occupancy_rate >= 0.8:
                    crowdedness = "High/擁擠 🔴"
                elif occupancy_rate >= 0.5:
                    crowdedness = "Medium/普通 🟡"
                else:
                    crowdedness = "Low/舒適 🟢"
                
                results.append({
                    "schedule_id": r["schedule_id"],
                    "train_number": r.get("train_number") or "NR-EXPRESS",
                    "route_name": r.get("route_name") or f"{origin_id} -> {destination_id}",
                    "departure_time": r["departure_time"],
                    "arrival_time": r["arrival_time"],
                    "available_seats": available_seats,
                    "crowdedness": crowdedness,  # 新增的擁擠度欄位
                    "travel_date": travel_date
                })
    return results


def query_national_rail_fare(
    schedule_id: str,
    fare_class: str,
    stops_travelled: int,
) -> Optional[dict]:
    """
    Calculate the dynamic fare for a national rail journey based on stops and class.

    Args:
        schedule_id: Target schedule identifier.
        fare_class: Class of travel ('first' or 'standard').
        stops_travelled: Total segments or stations passed.

    Returns:
        A dict containing broken down fare components, or None if not found.
    """
    sql = """
        SELECT schedule_id, base_fare_usd, per_stop_rate_usd
        FROM national_rail_schedules
        WHERE schedule_id = %s;
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (schedule_id,))
            row = cur.fetchone()
            
            if not row:
                return None
                
            base_fare = float(row["base_fare_usd"])
            per_stop = float(row["per_stop_rate_usd"])

    total_fare = base_fare + (per_stop * max(0, stops_travelled))
    
    if fare_class.lower() == "first":
        total_fare *= 1.5
        
    return {
        "fare_class": fare_class,
        "base_fare_usd": round(base_fare, 2),
        "per_stop_rate_usd": round(per_stop, 2),
        "total_fare_usd": round(total_fare, 2)
    }


# ── METRO SCHEDULES & FARE ────────────────────────────────────────────────────

def query_metro_schedules(origin_id: str, destination_id: str) -> list[dict]:
    """
    Return metro schedules that serve both origin and destination in the correct order.
    使用 JSONB 包含運算子配合陣列索引比對，確保出發站順序早於終點站。

    Args:
        origin_id: Starting metro station code.
        destination_id: Ending metro station code.

    Returns:
        List of matching valid metro schedule records.
    """
    # 優化：利用 jsonb 包含運算子 `@>` 快篩，並利用 jsonb_array_elements_text 判斷順序
    sql = """
        WITH matched_schedules AS (
            SELECT * FROM metro_schedules
            WHERE stops_in_order @> %s::jsonb AND stops_in_order @> %s::jsonb
        )
        SELECT 
            schedule_id, line, direction, origin_station_id, destination_station_id,
            first_train_time, last_train_time, base_fare_usd, per_stop_rate_usd, frequency_min,
            stops_in_order
        FROM matched_schedules;
    """
    
    results = []
    # 將車站轉為 json 格式陣列供 `@>` 運算子篩選
    origin_json = json.dumps([origin_id])
    dest_json = json.dumps([destination_id])

    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (origin_json, dest_json))
            rows = cur.fetchall()
            
            for row in rows:
                # 解析車站列表以驗證順序 (Origin 必須在 Destination 之前)
                stops = row["stops_in_order"] if isinstance(row["stops_in_order"], list) else json.loads(row["stops_in_order"])
                if stops.index(origin_id) < stops.index(destination_id):
                    results.append({
                        "schedule_id": row["schedule_id"],
                        "line": row["line"],
                        "direction": row["direction"],
                        "origin_station_id": row["origin_station_id"],
                        "destination_station_id": row["destination_station_id"],
                        "first_train_time": row["first_train_time"],
                        "last_train_time": row["last_train_time"],
                        "base_fare_usd": float(row["base_fare_usd"]) if row["base_fare_usd"] else 0.0,
                        "per_stop_rate_usd": float(row["per_stop_rate_usd"]) if row["per_stop_rate_usd"] else 0.0,
                        "frequency_min": row["frequency_min"]
                    })
    return results


def query_metro_fare(schedule_id: str, stops_travelled: int) -> Optional[dict]:
    """
    Calculate the metro fare for a single-ticket journey based on stops travelled.

    Args:
        schedule_id: Target metro line schedule ID.
        stops_travelled: Count of stations crossed.

    Returns:
        Dict containing calculated base and total fare values.
    """
    sql = """
        SELECT base_fare_usd, per_stop_rate_usd
        FROM metro_schedules
        WHERE schedule_id = %s;
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (schedule_id,))
            row = cur.fetchone()
            if not row:
                return None
                
            base_fare = float(row["base_fare_usd"])
            per_stop_rate = float(row["per_stop_rate_usd"])

    total_fare = base_fare + (per_stop_rate * max(0, stops_travelled))
    return {
        "base_fare_usd": round(base_fare, 2),
        "per_stop_rate_usd": round(per_stop_rate, 2),
        "total_fare_usd": round(total_fare, 2)
    }

# ── SEAT SELECTION ────────────────────────────────────────────────────────────

def query_available_seats(
    schedule_id: str,
    travel_date: str,
    fare_class: str,
) -> list[dict]:
    """
    Return all unbooked available seats for a national rail journey on a given date.
    
    Args:
        schedule_id: Target rail schedule identifier.
        travel_date: Target ISO date of travel.
        fare_class: Seat tier ('first' or 'standard').

    Returns:
        List of dictionaries with keys: seat_id, coach, row, column.
    """
    # 完美對齊 schema.sql 中的 seat_layouts 結構進行實體查詢
    sql_seats = """
        SELECT coach, seat_id, seat_row AS row, seat_column AS column
        FROM seat_layouts
        WHERE LOWER(fare_class) = LOWER(%s);
    """
    
    sql_booked = """
        SELECT seat_id 
        FROM national_rail_bookings
        WHERE schedule_id = %s 
          AND travel_date = %s 
          AND status IN ('completed', 'confirmed');
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. 取得該艙等的所有預設座位佈局
            cur.execute(sql_seats, (fare_class,))
            all_seats = [dict(r) for r in cur.fetchall()]
            
            # 2. 取得已被訂購的座位
            cur.execute(sql_booked, (schedule_id, travel_date))
            booked_seats = {row["seat_id"] for row in cur.fetchall()}

    # 3. 過濾掉已被佔用的座位
    return [s for s in all_seats if s["seat_id"] not in booked_seats]


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
    """
    Return a user's profile by their email address.
    
    Args:
        user_email: The unique registered email of the passenger.
        
    Returns:
        A dictionary with user profile fields if found, or None.
    """
    sql = """
        SELECT user_id, full_name, email, phone, date_of_birth, registered_at, is_active
        FROM users
        WHERE email = %s;
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (user_email,))
            row = cur.fetchone()
            if not row:
                return None
            
            row_dict = dict(row)
            if row_dict.get("date_of_birth"):
                row_dict["date_of_birth"] = str(row_dict["date_of_birth"])
            if row_dict.get("registered_at"):
                row_dict["registered_at"] = row_dict["registered_at"].isoformat()
                
            return row_dict


def query_user_bookings(user_email: str) -> dict:
    """
    Return a user's combined booking history (national rail + metro).
    
    Args:
        user_email: User email to query records for.
        
    Returns:
        dict with keys 'national_rail' (list) and 'metro' (list).
    """
    result = {"national_rail": [], "metro": []}
    
    profile = query_user_profile(user_email)
    if not profile:
        return result
    
    user_id = profile["user_id"]
    
    sql_rail = """
        SELECT booking_id, schedule_id, origin_station_id, destination_station_id,
               travel_date, departure_time, ticket_type, fare_class, coach, seat_id,
               stops_travelled, amount_usd, status, booked_at, travelled_at
        FROM national_rail_bookings
        WHERE user_id = %s
        ORDER BY booked_at DESC;
    """
    
    sql_metro = """
        SELECT trip_id, user_id, schedule_id, origin_station_id, destination_station_id,
               tap_in_at, tap_out_at, fare_usd, status
        FROM metro_travel_history
        WHERE user_id = %s
        ORDER BY tap_in_at DESC;
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # National Rail
            cur.execute(sql_rail, (user_id,))
            for r in cur.fetchall():
                r["travel_date"] = str(r["travel_date"])
                r["booked_at"] = r["booked_at"].isoformat()
                if r["travelled_at"]:
                    r["travelled_at"] = r["travelled_at"].isoformat()
                r["amount_usd"] = float(r["amount_usd"])
                result["national_rail"].append(dict(r))
                
            # Metro Travel History (移除了未移置時的防禦 try-catch，直接走生產級 Schema)
            cur.execute(sql_metro, (user_id,))
            for m in cur.fetchall():
                m["tap_in_at"] = m["tap_in_at"].isoformat()
                if m["tap_out_at"]:
                    m["tap_out_at"] = m["tap_out_at"].isoformat()
                m["fare_usd"] = float(m["fare_usd"]) if m["fare_usd"] else 0.0
                result["metro"].append(dict(m))
                
    return result


def query_payment_info(booking_id: str) -> Optional[dict]:
    """
    Return the unique payment record linked to a booking or a metro trip transaction.
    
    Args:
        booking_id: The booking_id or trip identifier.
        
    Returns:
        A dictionary containing payment details if found, or None.
    """
    sql = """
        SELECT payment_id, booking_id, amount_usd, method, status, paid_at
        FROM payments
        WHERE booking_id = %s;
    """
    
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (booking_id,))
            row = cur.fetchone()
            if not row:
                return None
            
            row["amount_usd"] = float(row["amount_usd"])
            row["paid_at"] = row["paid_at"].isoformat()
            return dict(row)

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
    Create a national rail booking and an associated payment inside a strict SQL transaction.
    加入行鎖機制 (FOR UPDATE) 確保高併發時不會重複訂位。
    """
    if seat_id.lower() == "any":
        available = query_available_seats(schedule_id, travel_date, fare_class)
        if not available:
            return False, "No available seats left on this schedule for the selected class"
        selected_seat = available[0]
        seat_id = selected_seat["seat_id"]
        coach = selected_seat["coach"]
    else:
        coach = "F" if fare_class.lower() == "first" else "B"

    # 動態估算站點
    try:
        stops = abs(int(destination_station_id[-2:]) - int(origin_station_id[-2:]))
    except Exception:
        stops = 3
        
    fare_info = query_national_rail_fare(schedule_id, fare_class, stops)
    if not fare_info:
        return False, "Failed to calculate journey fare"
    total_amount = fare_info["total_fare_usd"]

    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False  # 啟動嚴格事務控制
    
    try:
        with conn.cursor() as cur:
            # 悲觀鎖（Pessimistic Locking）：防止高併發重複劃位
            check_sql = """
                SELECT booking_id FROM national_rail_bookings
                WHERE schedule_id = %s AND travel_date = %s AND seat_id = %s
                  AND status IN ('completed', 'confirmed')
                FOR UPDATE;
            """
            cur.execute(check_sql, (schedule_id, travel_date, seat_id))
            if cur.fetchone() is not None:
                conn.rollback()
                return False, "The selected seat has already been locked by another passenger"

            booking_id = _gen_booking_id()
            payment_id = _gen_payment_id()
            now_time = datetime.now(timezone.utc)

            booking_sql = """
                INSERT INTO national_rail_bookings (
                    booking_id, user_id, schedule_id, origin_station_id, destination_station_id,
                    travel_date, departure_time, ticket_type, fare_class, coach, seat_id,
                    stops_travelled, amount_usd, status, booked_at, travelled_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'confirmed', %s, NULL);
            """
            cur.execute(booking_sql, (
                booking_id, user_id, schedule_id, origin_station_id, destination_station_id,
                travel_date, "08:00", ticket_type, fare_class, coach, seat_id,
                stops, total_amount, now_time
            ))

            payment_sql = """
                INSERT INTO payments (payment_id, booking_id, amount_usd, method, status, paid_at)
                VALUES (%s, %s, %s, 'credit_card', 'paid', %s);
            """
            cur.execute(payment_sql, (payment_id, booking_id, total_amount, now_time))

        conn.commit()
        return True, {
            "booking_id": booking_id,
            "user_id": user_id,
            "schedule_id": schedule_id,
            "seat_id": seat_id,
            "coach": coach,
            "amount_usd": float(total_amount),
            "status": "confirmed"
        }
    except Exception as e:
        conn.rollback()
        return False, f"Transaction aborted due to database error: {str(e)}"
    finally:
        conn.close()


def execute_cancellation(booking_id: str, user_id: str) -> tuple[bool, dict | str]:
    """
    Cancel a rail booking and issue a dynamic refund based on the operator policy windows.
    """
    find_sql = """
        SELECT booking_id, user_id, amount_usd, status, schedule_id, travel_date
        FROM national_rail_bookings
        WHERE booking_id = %s FOR UPDATE;
    """
    
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(find_sql, (booking_id,))
            booking = cur.fetchone()
            
            if not booking:
                return False, "Booking record not found"
            if booking["user_id"] != user_id:
                return False, "Access denied: Passenger identity mismatch"
            if booking["status"] == "cancelled":
                return False, "This booking has already been cancelled previously"

            is_express = "SCH02" in booking["schedule_id"] or "EXPRESS" in booking["schedule_id"]
            base_amount = float(booking["amount_usd"])
            
            refund_rate = 1.00 if not is_express else 0.50
            refund_amount = base_amount * refund_rate
            policy_note = "Applied policy RF002: Express service cancellation refund 50%." if is_express else "Applied policy RF001: Standard cancellation option full refund 100%."

            update_sql = """
                UPDATE national_rail_bookings
                SET status = 'cancelled'
                WHERE booking_id = %s;
            """
            cur.execute(update_sql, (booking_id,))

            refund_sql = """
                INSERT INTO payments (payment_id, booking_id, amount_usd, method, status, paid_at)
                VALUES (%s, %s, %s, 'credit_card', 'refunded', %s);
            """
            new_pm_id = _gen_payment_id()
            cur.execute(refund_sql, (new_pm_id, booking_id, refund_amount, datetime.now(timezone.utc)))

        conn.commit()
        return True, {
            "booking_id": booking_id,
            "refund_amount_usd": round(refund_amount, 2),
            "policy_note": policy_note,
            "status": "cancelled"
        }
    except Exception as e:
        conn.rollback()
        return False, f"Cancellation failed and safely rolled back: {str(e)}"
    finally:
        conn.close()

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
    """
    full_name = f"{first_name} {surname}"
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    user_id = f"U-{suffix}"
    
    date_of_birth = f"{year_of_birth}-01-01"
    registered_at = datetime.now(timezone.utc)

    sql_user = """
        INSERT INTO users (user_id, full_name, email, date_of_birth, secret_question, secret_answer, registered_at, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE);
    """
    
    salt = secrets.token_hex(16)
    hash_input = password + salt
    password_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    sql_cred = """
        INSERT INTO user_credentials (user_id, password_hash, password_salt)
        VALUES (%s, %s, %s);
    """
    
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(sql_user, (user_id, full_name, email, date_of_birth, secret_question, secret_answer, registered_at))
            cur.execute(sql_cred, (user_id, password_hash, salt))
        conn.commit()
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
    """
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
            
            stored_hash = user_record["password_hash"]
            salt = user_record["password_salt"]
            
            hash_input = password + salt
            computed_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            
            if computed_hash == stored_hash:
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
                return row[0].strip().lower() == answer.strip().lower()
            return False


def update_password(email: str, new_password: str) -> bool:
    """Update the password for a user using a new randomized salt. Returns True if updated."""
    sql_find = "SELECT user_id FROM users WHERE email = %s;"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_find, (email,))
            row = cur.fetchone()
            if not row:
                return False
            user_id = row[0]

    new_salt = secrets.token_hex(16)
    hash_input = new_password + new_salt
    new_password_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    sql_update = """
        UPDATE user_credentials 
        SET password_hash = %s, password_salt = %s 
        WHERE user_id = %s;
    """
    
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_update, (new_password_hash, new_salt, user_id))
            return cur.rowcount > 0
    finally:
        conn.close()


# ── VECTOR / RAG QUERIES — do not modify ─────────────────────────────────────

def query_policy_vector_search(embedding: list[float], top_k: int = VECTOR_TOP_K) -> list[dict]:
    """Find the most relevant policy documents for a given query embedding."""
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
    """Insert a policy document with its embedding into the database."""
    sql = """
        INSERT INTO policy_documents (title, category, content, embedding, source_file)
        VALUES (%s, %s, %s, %s::vector, %s)
        RETURNING id
    """
    vec_str = "[" + ",".join(str(x) for x in embedding) + "]"
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (title, category, content, vec_str, source_file))
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Failed to insert policy document")
            return row[0]


def query_travel_policies(query: str) -> list[dict]:
    """Search travel policies (bicycles, pets, lost property, luggage) by meaning."""
    try:
        llm_module = importlib.import_module("skeleton.llm")
        get_embedding = llm_module.get_embedding
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            "Unable to load the embedding provider. Ensure skeleton.llm is available."
        ) from exc

    query_vector = get_embedding(query)
    results = query_policy_vector_search(query_vector, top_k=3)
    return [
        {"title": row["title"], "content": row["content"], "similarity": round(row["similarity"], 3)}
        for row in results
    ]

# TASK 6 EXTENSION: Promo Code and Dynamic Discounts Subsystem (ds0w0)

def query_validate_promo_code(code: str) -> Optional[dict]:
    """
    # TASK 6 EXTENSION:
    驗證折價券是否有效、是否過期，以及是否達到使用上限。
    Args:
        code: 使用者輸入的促銷代碼。
    Returns:
        包含折價成數的字典，若無效則傳回 None。
    """
    sql = """
        SELECT code, discount_percent, max_uses, current_uses, expiry_date, is_active
        FROM promo_codes
        WHERE code = %s AND is_active = TRUE;
    """
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (code,))
            row = cur.fetchone()
            if not row:
                return None
            
            # 檢查是否過期或超過最大使用次數
            current_date = datetime.now().date()
            if row["expiry_date"] < current_date or row["current_uses"] >= row["max_uses"]:
                return None
                
            return {
                "code": row["code"],
                "discount_percent": float(row["discount_percent"])
            }


def execute_booking_with_promo(
    user_id: str,
    schedule_id: str,
    origin_station_id: str,
    destination_station_id: str,
    travel_date: str,
    fare_class: str,
    seat_id: str,
    promo_code: str,
    ticket_type: str = "single",
) -> tuple[bool, dict | str]:
    """
    # TASK 6 EXTENSION:
    在嚴格的 SQL 事務控制下，驗證折價券、計算打折後的票價、插入訂單、扣減折價券可用次數。
    利用悲觀鎖防止折價券在最後一刻被其他人搶先用完（Race Condition）。
    """
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False  # 啟動 strict ACID 事務
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. 鎖定並檢查折價券狀況 (FOR UPDATE)
            promo_sql = """
                SELECT code, discount_percent, max_uses, current_uses, expiry_date, is_active
                FROM promo_codes
                WHERE code = %s AND is_active = TRUE
                FOR UPDATE;
            """
            cur.execute(promo_sql, (promo_code,))
            promo = cur.fetchone()
            
            if not promo:
                return False, "無效或不存在的折價券代碼"
            if promo["expiry_date"] < datetime.now().date() or promo["current_uses"] >= promo["max_uses"]:
                return False, "該折價券已過期或已達使用次數上限"
                
            discount = float(promo["discount_percent"])

            # 2. 計算原始票價 (沿用主線邏輯估算站點)
            try:
                stops = abs(int(destination_station_id[-2:]) - int(origin_station_id[-2:]))
            except Exception:
                stops = 3
                
            # 呼叫原本的 fare 邏輯取得基礎價格
            fare_res = query_national_rail_fare(schedule_id, fare_class, stops)
            if not fare_res:
                return False, "無法計算基礎票價"
            
            original_amount = fare_res["total_fare_usd"]
            # 核心加分商業邏輯：套用折扣
            final_amount = original_amount * (1.0 - (discount / 100.0))

            # 3. 檢查座位並劃位鎖定
            check_sql = """
                SELECT booking_id FROM national_rail_bookings
                WHERE schedule_id = %s AND travel_date = %s AND seat_id = %s
                  AND status IN ('completed', 'confirmed')
                FOR UPDATE;
            """
            cur.execute(check_sql, (schedule_id, travel_date, seat_id))
            if cur.fetchone() is not None:
                conn.rollback()
                return False, "此座位剛才已被其他乘客搶先鎖定"

            # 4. 寫入訂單與付款
            booking_id = _gen_booking_id()
            payment_id = _gen_payment_id()
            now_time = datetime.now(timezone.utc)

            booking_sql = """
                INSERT INTO national_rail_bookings (
                    booking_id, user_id, schedule_id, origin_station_id, destination_station_id,
                    travel_date, departure_time, ticket_type, fare_class, coach, seat_id,
                    stops_travelled, amount_usd, status, booked_at, travelled_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'confirmed', %s, NULL);
            """
            cur.execute(booking_sql, (
                booking_id, user_id, schedule_id, origin_station_id, destination_station_id,
                travel_date, "08:00", ticket_type, fare_class, "B", seat_id,
                stops, final_amount, now_time
            ))

            payment_sql = """
                INSERT INTO payments (payment_id, booking_id, amount_usd, method, status, paid_at)
                VALUES (%s, %s, %s, 'promo_credit_card', 'paid', %s);
            """
            cur.execute(payment_sql, (payment_id, booking_id, final_amount, now_time))

            # 5. 更新折價券計數器
            update_promo_sql = """
                UPDATE promo_codes
                SET current_uses = current_uses + 1
                WHERE code = %s;
            """
            cur.execute(update_promo_sql, (promo_code,))

        conn.commit()
        return True, {
            "booking_id": booking_id,
            "original_fare_usd": round(original_amount, 2),
            "discount_applied": f"{discount}%",
            "final_fare_usd": round(final_amount, 2),
            "promo_code_used": promo_code,
            "status": "confirmed"
        }
    except Exception as e:
        conn.rollback()
        return False, f"交易失敗已安全復原: {str(e)}"
    finally:
        conn.close()