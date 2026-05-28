# TransitFlow: Data Modeling & Schema Design Report

## 1. Executive Summary
The TransitFlow mock data represents a dual-network public transit system (City Metro and National Rail). To build an optimal, high-performance database layer, we must apply **Polyglot Persistence**, routing data to the database engine best suited for its structure and access patterns.

*   **PostgreSQL (Relational):** Master system of record. Handles users, stations, schedules, seats, bookings, payments, and feedback.
*   **Neo4j (Graph):** Routing and topological data. Handles stations (nodes) and the physical tracks/travel times between them (edges).
*   **PostgreSQL + pgvector (Vector):** Knowledge base. Handles policy documents.

---

## 2. PostgreSQL Relational Data Model

### 2.1 Infrastructure & Timetables
The infrastructure data contains stations and the scheduled trains running through them.

**Table: `metro_stations`**
*   `station_id` (VARCHAR PK)
*   `name` (VARCHAR)
*   `lines` (TEXT ARRAY)
*   `is_interchange_metro`, `is_interchange_national_rail` (BOOLEAN)
*   `interchange_metro_lines` (TEXT ARRAY)
*   `interchange_national_rail_station_id` (VARCHAR FK)

**Table: `national_rail_stations`**
*   *Same structure as metro_stations, but tracking metro interchange IDs.*

**Table: `metro_schedules` & `national_rail_schedules`**
*   *Best Practice Applied:* **JSONB for Ordered Arrays & Maps.** The `stops_in_order` and `travel_time_from_origin_min` fields should be stored as `JSONB`. Relational databases struggle with ordered arrays in standard tables without complex sequence columns. PostgreSQL's `JSONB` combined with `jsonb_array_elements_text()` allows for flawless origin/destination sequence checking.
*   *Key Columns:* `schedule_id` (PK), `line`, `direction`, `origin_station_id` (FK), `destination_station_id` (FK), `stops_in_order` (JSONB), `travel_time_from_origin_min` (JSONB), `base_fare_usd`, `per_stop_rate_usd`.
*   *National Rail specific:* `fare_classes` (JSONB), `service_type` (VARCHAR).

### 2.2 Physical Train Layouts
**Table: `national_rail_seats`**
*   *Best Practice Applied:* **Flattening Nested JSON.** The `national_rail_seat_layouts.json` file is heavily nested (Schedule -> Coaches -> Seats). Instead of storing massive JSON blobs, we flatten this into a `national_rail_seats` table to make availability queries (`query_available_seats`) incredibly fast.
*   *Key Columns:* `seat_id` (VARCHAR), `schedule_id` (VARCHAR FK), `coach` (VARCHAR), `fare_class` (VARCHAR), `seat_row` (INT), `seat_column` (VARCHAR).
*   *Composite PK:* `(schedule_id, seat_id)`

### 2.3 Identity & Access
**Table: `users`**
*   *Key Columns:* `user_id` (VARCHAR PK), `full_name`, `email` (UNIQUE), `password`, `phone`, `date_of_birth`, `secret_question`, `secret_answer`, `registered_at`, `is_active`.

### 2.4 Transactions (Bookings & Trips)
Because Metro trips ("MT001") and National Rail bookings ("BK001") have different lifecycles and business rules, they belong in separate tables rather than a forced overarching table.

**Table: `national_rail_bookings`**
*   *Key Columns:* `booking_id` (PK), `user_id` (FK), `schedule_id` (FK), `origin_station_id` (FK), `destination_station_id` (FK), `travel_date`, `departure_time`, `ticket_type`, `fare_class`, `coach`, `seat_id`, `stops_travelled`, `amount_usd`, `status`, `booked_at`, `travelled_at`.

**Table: `metro_trips`**
*   *Key Columns:* `trip_id` (PK), `user_id` (FK), `schedule_id` (FK), `origin_station_id` (FK), `destination_station_id` (FK), `travel_date`, `ticket_type`, `day_pass_ref` (VARCHAR, self-referencing FK), `stops_travelled`, `amount_usd`, `status`, `purchased_at`, `travelled_at`.

### 2.5 Payments & Feedback (Polymorphic Associations)
*   *Best Practice Applied:* **Handling Polymorphism.** The `payments.json` and `feedback.json` files reference a `booking_id` which could belong to *either* a National Rail Booking or a Metro Trip. 
*   Since strict Foreign Keys cannot point to "Table A OR Table B", we use a generic `transaction_ref` VARCHAR column. In the application layer, we know "BK%" refers to national rail and "MT%" refers to metro.

**Table: `payments`**
*   `payment_id` (PK), `transaction_ref` (VARCHAR Index), `amount_usd`, `method`, `status`, `paid_at`.

**Table: `feedback`**
*   `feedback_id` (PK), `transaction_ref` (VARCHAR Index), `user_id` (FK), `rating`, `comment`, `submitted_at`.

---

## 3. Neo4j Graph Data Model

While PostgreSQL handles the business data, Neo4j handles routing logic. We extract the `adjacent_stations` arrays from the JSON data to build the graph.

### Nodes
*   **`(:MetroStation)`**: Properties `station_id`, `name`, `lines`.
*   **`(:NationalRailStation)`**: Properties `station_id`, `name`, `lines`.

### Relationships (Edges)
*   **`[:METRO_LINK]`**: Connects MetroStations. Properties: `line`, `travel_time_min`.
*   **`[:RAIL_LINK]`**: Connects NationalRailStations. Properties: `line`, `travel_time_min`.
*   **`[:INTERCHANGE_TO]`**: Connects a MetroStation to a NationalRailStation (and vice-versa).

*Why this matters:* By keeping graph properties lightweight (just time and line info), Dijkstra's shortest-path algorithms run in milliseconds, completely bypassing complex SQL recursive CTEs.

---

## 4. Summary of Data Anomalies & Normalization Rules

1.  **Day Passes:** In `metro_travel_history.json`, day passes contain `stops_travelled: null` and subsequent trips use a `day_pass_ref`. The `metro_trips` schema allows NULLs on these columns to support this.
2.  **Seat Layouts:** A layout (`SL01`) maps 1:1 to a schedule (`NR_SCH01`). Therefore, we can bypass the `layout_id` entirely in the normalized tables and map seats directly to the `schedule_id`.
3.  **Password Security:** The mock data uses plain-text passwords. The schema will store them as strings, but a note should be left for future production updates to use `argon2` hashes.
4.  **Vector documents:** The four policy JSON files (`refund_policy`, `travel_policies`, `booking_rules`, `ticket_types`) do not need to be modeled into standard relational tables; they belong strictly in the `policy_documents` table provided in `schema.sql` via pgvector embeddings.