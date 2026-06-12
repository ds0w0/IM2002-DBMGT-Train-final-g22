# TASK 6 EXTENSION — Trip History Panel

## Overview

This extension adds a **My Bookings** tab to the TransitFlow Gradio UI.
It surfaces the logged-in user's past national rail bookings and metro trips
in a persistent, scannable table format — an interaction that the existing
chat interface cannot provide.

---

## Files Modified or Added

| File | Type | What changed |
|------|------|--------------|
| `skeleton/ui.py` | Modified | Added `load_trip_history()` function and a new `🎫 My Bookings` tab with two `gr.Dataframe` tables |
| `train-mock-data/travel_policies.json` | Modified | Extended with 4 new top-level policy sections: `children_and_family`, `passenger_conduct`, `season_tickets_and_passes`, `special_services` |

---

## New Functions

### `load_trip_history(current_user: str)` — `skeleton/ui.py`

Queries `query_user_bookings()` from `databases/relational/queries.py` and
formats the results into two table-ready lists for display in the UI.

- Returns national rail bookings with columns: Booking ID, From, To, Date, Departure, Class, Seat, Status, Amount
- Returns metro trips with columns: Trip ID, From, To, Tapped In, Tapped Out, Status, Fare
- Returns a status message showing booking counts
- Handles unauthenticated users gracefully (shows a login prompt)

---

## Tables Queried

| Table | Database | Purpose |
|-------|----------|---------|
| `national_rail_bookings` | PostgreSQL | Fetch user's rail booking history |
| `metro_travel_history` | PostgreSQL | Fetch user's metro trip history |

---

## How to Test the Extension

1. Start the Docker stack: `docker-compose up -d`
2. Seed the databases: `python skeleton/seed_postgres.py` and `python skeleton/seed_vectors.py`
3. Launch the UI: `python skeleton/ui.py`
4. Open `http://localhost:7860`
5. Register or log in with an existing account
6. Click the **🎫 My Bookings** tab
7. Click **🔄 Refresh Bookings** to load booking history from PostgreSQL
8. National rail bookings appear in the first table; metro trips in the second

---

## Why This Qualifies as a Substantial UI Improvement

The existing UI is chat-only — all data is returned as plain text in the
conversation window. The My Bookings panel adds a genuinely new interaction
mode: a structured, persistent, tabular view of the user's booking history
that is impossible to replicate in a chat reply. It bypasses the LLM entirely
for a specific, well-defined query and surfaces data directly from PostgreSQL.
