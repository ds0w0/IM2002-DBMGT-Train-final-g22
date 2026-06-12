# Task 6 Extension Report — Group 22

Our team implemented a comprehensive Task 6 extension that touches relational database concurrency, dynamic query computation, persistent UI enhancements, and RAG knowledge base expansion.

All modified Python and SQL files have been marked with the `# TASK 6 EXTENSION:` comment near the top, as per the assessment requirements.

---

## 1. Promo Code Subsystem & Crowdedness Indicator (ds0w0)

This extension implements a production-grade Promotional Voucher system with strict atomic concurrency control, alongside a dynamic train crowdedness calculator inspired by real-world transit apps.

### Files Modified
- `databases/relational/schema.sql`
- `databases/relational/queries.py`

### Tables Added
- `promo_codes`: Stores registered active discount vouchers, discount percentages, expiry policies, and numeric atomic usage counters (`max_uses`, `current_uses`). Includes a specific B-Tree index for fast active-code lookups.

### Functions Added / Modified
- `query_validate_promo_code(code)`: Read-only endpoint to verify code existence, validity, expiry, and capacity limits.
- `execute_booking_with_promo(...)`: Atomic write operation wrapping code verification, dynamic price reduction, seat protection, and voucher increment tracking in a single database transaction using pessimistic row-locking (`FOR UPDATE`) for concurrent safety.
- `query_national_rail_availability(...)` **(Modified)**: Added a dynamic **Crowdedness Indicator** (High 🔴 / Medium 🟡 / Low 🟢) computed on-the-fly based on `booked_count` versus `total_capacity`.

---

## 2. Trip History Panel & RAG Policy Expansion (yikes0000)

This extension adds a **"🎫 My Bookings"** tab to the Gradio UI, providing a structured, persistent tabular view of the user's booking history (bypassing the LLM), and significantly expands the vector search corpus.

### Files Modified
- `skeleton/ui.py`
- `train-mock-data/travel_policies.json`

### Functions Added / Modified
- `load_trip_history(current_user: str)`: Queries `query_user_bookings()` directly from PostgreSQL and formats the structured outputs into two `gr.Dataframe` tables (National Rail & Metro). Handles unauthenticated users gracefully.

### Data Expanded
- `train-mock-data/travel_policies.json`: Extended the unstructured dataset with 4 new top-level policy sections (`children_and_family`, `passenger_conduct`, `season_tickets_and_passes`, `special_services`). Verified that all 21 resulting policy documents embed correctly into `pgvector` via `seed_vectors.py`.

---

## Testing Evidence & Motivation
Please refer to **Section 7** of our submitted `Design Document` (PDF) for detailed motivations, example Cypher/SQL queries, and testing evidence (including concurrency lock verification and Gradio UI integration logic).