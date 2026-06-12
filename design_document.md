# Database Design Document — Group 22

## Section 1 — Entity-Relationship Diagram

### 1.1 Conceptual ERD Topology

Our hybrid data engineering strategy balances relational constraints, graph topological traversal speed, and dense vector similarity search requirements. The cross-system persistent layout is organized around 12 core tables and entity structures, interconnected across PostgreSQL, Neo4j, and pgvector layers.

```text
========================================================================================
1. RELATIONAL COMPONENT (PostgreSQL Schema Ledger)
========================================================================================
   +-----------------------+              +-----------------------+
   |         users         |1            1|   user_credentials    |
   |-----------------------|--------------|-----------------------|
   | PK | user_id          |              | PK,FK | user_id       |
   +-----------------------+              +-----------------------+
        |
        | 1
        +-----------------------------------------+
        | N                                       | N
   +-----------------------+1           N +-----------------------+
   | national_rail_bookings|--------------|       payments        |
   |-----------------------|              |-----------------------|
   | PK | booking_id       |              | PK | payment_id       |
   | FK | user_id          |              +-----------------------+
   +-----------------------+
        |
        | 1
        +----------------------------+
        | N                          | N
   +-----------------------+    +-----------------------+
   |       feedback        |    | metro_travel_history  |
   |-----------------------|    |-----------------------|
   | PK | feedback_id      |    | PK | trip_id          |
   | FK | user_id          |    | FK | user_id          |
   +-----------------------+    +-----------------------+

   +-----------------------+    +-----------------------+
   |    metro_stations     |    | national_rail_stations|
   |-----------------------|    |-----------------------|
   | PK | station_id       |    | PK | station_id       |
   +-----------------------+    +-----------------------+

   +-----------------------+    +-----------------------+
   |    metro_schedules    |    |national_rail_schedules|
   |-----------------------|    |-----------------------|
   | PK | schedule_id      |    | PK | schedule_id      |
   +-----------------------+    +-----------------------+

   +-----------------------+    +-----------------------+
   |     seat_layouts      |    |      promo_codes      | (TASK 6 EXTENSION)
   |-----------------------|    |-----------------------|
   | PK | id               |    | PK | code             |
   +-----------------------+    +-----------------------+

========================================================================================
2. VECTOR & GRAPH ENTITIES (pgvector RAG Corpus & Neo4j Topological Clusters)
========================================================================================
   +-------------------------+          (MetroStation) ====[:METRO_LINK]====> (MetroStation)
   |    policy_documents     |                 ||                                 ||
   |-------------------------|          [:INTERCHANGE_TO]                  [:INTERCHANGE_TO]
   | PK | id                 |                 ||                                 ||
   |    embedding: vector(768|          (RailStation)  ====[:RAIL_LINK]=====> (RailStation)
   +-------------------------+

```

### 1.2 Data Dictionary and Column Specification

#### 1.2.1 Core Identity and Security Entities

* **`users` Table:** Stores demographic profiles and verification contexts.
* `user_id` (VARCHAR(10), Primary Key): Unique alphanumeric cluster sequence identifier.
* `full_name` (VARCHAR(100), Required): Combined passenger denomination string.
* `email` (VARCHAR(150), Unique Constraint): Indexed communication routing string.
* `phone` (VARCHAR(20)): Contact vector.
* `date_of_birth` (DATE): Required constraint parameter for youth/senior fare evaluation.
* `secret_question` / `secret_answer` (TEXT): Fallback out-of-band account reset payload.
* `registered_at` (TIMESTAMPTZ): Strict temporal capture log.
* `is_active` (BOOLEAN): Logical record evaluation toggle flag.

* **`user_credentials` Table:** Highly decoupled storage entity isolating cryptographic secrets.
* `user_id` (VARCHAR(10), Primary Key): Foreign key binder mapping to `users(user_id) ON DELETE CASCADE`.
* `password_hash` (VARCHAR(128)): Secure cryptographic SHA-256 string representation.
* `password_salt` (VARCHAR(64)): High-entropy randomized hex block to thwart rainbow-table mapping.

#### 1.2.2 Transactional and Ledger Entities

* **`national_rail_bookings` Table:** Maintains state records for cross-country journeys.
* `booking_id` (VARCHAR(20), Primary Key): Structured identifier (e.g., `BK-XXXXXX`).
* `user_id` (VARCHAR(10), Foreign Key referencing `users(user_id)`): Passenger record owner.
* `schedule_id` (VARCHAR(20), Required): Link trace to the assigned rail service profile.
* `origin_station_id` / `destination_station_id` (VARCHAR(10)): Spatial point bounds.
* `travel_date` (DATE): Targeted departure date window.
* `departure_time` (VARCHAR(10)): ISO standard formatted departure time.
* `ticket_type` / `fare_class` (VARCHAR(20)): Commercial variables driving tariff rules.
* `coach` / `seat_id` (VARCHAR(10)): Allocated carriage bounds and physical row matrix key.
* `stops_travelled` (INT): Calculated distance scalar driving fare generation formulae.
* `amount_usd` (NUMERIC(10,2)): Exact dynamic cost decimal tracking passenger charge metrics.
* `status` (VARCHAR(20)): Reservation lifecycle enum state (`confirmed`, `cancelled`).
* `booked_at` (TIMESTAMPTZ): Record insertion time log tracking transactional latency.
* `travelled_at` (TIMESTAMPTZ, Nullable): Dynamic timestamp recorded upon track sensor gate trigger.

* **`payments` Table:** Financial ledger log auditing transaction streams.
* `payment_id` (VARCHAR(20), Primary Key): Unique ledger balance reference token (e.g., `PM-XXXXXX`).
* `booking_id` (VARCHAR(20), Required): Relational reference linking to the source invoice identifier.
* `amount_usd` (NUMERIC(10,2)): Monitored transaction value field preventing rounding degradation.
* `method` (VARCHAR(50)): Transaction platform mechanism tracker (`credit_card`, `promo_credit_card`).
* `status` (VARCHAR(20)): Status verification enum string (`paid`, `refunded`).
* `paid_at` (TIMESTAMPTZ): Financial transaction close timestamp.

* **`feedback` Table:** Polymorphic review store monitoring service quality vectors.
* `feedback_id` (VARCHAR(20), Primary Key): Sentiment tracking node reference string.
* `booking_id` (VARCHAR(20), Required): Maps feedback context back to an verified trip lifecycle instance.
* `user_id` (VARCHAR(10), Foreign Key referencing `users(user_id) ON DELETE CASCADE`): Reviewer reference.
* `rating` (INT): Numeric limit constraint forcing evaluation bound metrics between 1 and 5.
* `comment` (TEXT, Nullable): Unstructured text context capturing user qualitative notes.
* `submitted_at` (TIMESTAMPTZ): Date-time registry mapping when the review was sent.

* **`metro_travel_history` Table:** High-throughput transactional ledger recording sub-surface segment tracking.
* `trip_id` (VARCHAR(20), Primary Key): Tap-in record reference.
* `user_id` (VARCHAR(10), Foreign Key referencing `users(user_id) ON DELETE CASCADE`): Commuter reference.
* `schedule_id` (VARCHAR(20)): Maps the physical line configuration engine.
* `origin_station_id` (VARCHAR(10)): Gate entry point tracking token.
* `destination_station_id` (VARCHAR(10), Nullable): Gate exit point identifier (remains null if active).
* `tap_in_at` (TIMESTAMPTZ): Entry timestamp monitoring transit initiation.
* `tap_out_at` (TIMESTAMPTZ, Nullable): Exit timestamp monitoring journey closure.
* `fare_usd` (NUMERIC(10,2)): Variable calculation tracking final tap-out balance subtractions.
* `status` (VARCHAR(20)): Commute lifecycle parameter state (`active`, `completed`).

#### 1.2.3 Operational Static Configuration Entities

* **`metro_stations` Table:** Relational registry for mass transit stations.
* `station_id` (VARCHAR(10), Primary Key): Station lookup node string.
* `name` (VARCHAR(100)): Localized geographical station string designation.
* `lines` (JSONB): Semi-structured format documenting complex dynamic array values for line mappings.
* `zone` (INT): Topological tariff sector categorization integer.
* `has_interchange` (BOOLEAN): Relational indicator flag for co-located multimodal transfer hubs.

* **`national_rail_stations` Table:** Relational dictionary tracking heavy mainline train stations.
* `station_id` (VARCHAR(10), Primary Key): Mainline station dictionary lookup code.
* `name` / `city` (VARCHAR(100)): Regional localization character data.
* `has_interchange` (BOOLEAN): Tracks infrastructure affinity for multimodal links.

* **`metro_schedules` Table:** Service operational baselines for subway scheduling.
* `schedule_id` (VARCHAR(20), Primary Key): Subway line operations reference token.
* `line` / `direction` (VARCHAR(10 / 20)): Network identifiers routing agent requests.
* `origin_station_id` / `destination_station_id` (VARCHAR(10)): Route trajectory termination constraints.
* `stops_in_order` (JSONB): Ordered sequence documenting chronological station stop vectors.
* `first_train_time` / `last_train_time` (VARCHAR(10)): Baseline operating window limits.
* `travel_time_from_origin_min` (JSONB): Multi-value key-value map documenting segment weight costs.
* `base_fare_usd` / `per_stop_rate_usd` (NUMERIC(10,2)): Financial parameters driving dynamic fare calculation.
* `frequency_min` (INT): Interval tracking integer mapping off-peak/peak train arrivals.

* **`national_rail_schedules` Table:** MAINLINE operational baseline tracking structures.
* `schedule_id` (VARCHAR(20), Primary Key): Mainline operational profile lookup key.
* `train_number` / `route_name` (VARCHAR(20 / 100)): Character fields for user-facing agent display logs.
* `origin_station_id` / `destination_station_id` (VARCHAR(10)): Route anchor identifiers.
* `departure_time` / `arrival_time` (VARCHAR(10)): Operating scheduling targets.
* `route_stations` (VARCHAR[]): Native PostgreSQL array list tracking absolute intermediate stops.
* `travel_time_from_origin_min` (JSONB): JSON configuration tracking compound travel durations.
* `base_fare_usd` / `per_stop_rate_usd` (NUMERIC(10,2)): Mainline financial calculation attributes.
* `total_seats` (INT): Seat allocation ceiling parameter defining train capacity limits.

* **`seat_layouts` Table:** Relational spatial matrix defining rolling stock seat mapping.
* `id` (SERIAL, Primary Key): Autoincrement sequence key tracking spatial seat nodes.
* `coach` (VARCHAR(2)): Physical train car block layout reference string.
* `seat_id` (VARCHAR(10)): Specific chair label code mapping user selections.
* `seat_row` (INT) / `seat_column` (VARCHAR(2)): Spatial row and array parameters.
* `fare_class` (VARCHAR(20)): Class segmentation property (`first`, `standard`).

* **`promo_codes` Table (TASK 6 EXTENSION):** Added table tracking marketing campaign entities.
* `code` (VARCHAR(20), Primary Key): Dynamic promotional lookup identifier.
* `discount_percent` (NUMERIC(5,2)): Value percent bounds constraint forcing discount ranges between 0.01 and 100.00.
* `max_uses` (INT): Volume activation constraint tracking voucher lifecycle limits.
* `current_uses` (INT): Atomic transaction counter tracking utilized redemptions.
* `expiry_date` (DATE): Temporal cutoff validation constraint checking campaign expiration windows.
* `is_active` (BOOLEAN): Global validation flag toggle.

#### 1.2.4 Unstructured Vector Search Entities

* **`policy_documents` Table:** Managed text chunk embedding engine.
* `id` (SERIAL, Primary Key): Token record identifier.
* `title` / `category` (VARCHAR(200 / 50)): Text parameters matching metadata pre-filtering hooks.
* `content` (TEXT): Full unstructured textual guidelines (e.g., luggage, pet policies).
* `embedding` (VECTOR(768)): Dense vector layer storing floating-point spatial semantic weights for cosine distance calculation.
* `source_file` (VARCHAR(200)): Lineage tracer tracing back to the origin markdown text block source.

#### 1.2.5 No4j Network Graph Schema Specification

* **`MetroStation` / `RailStation` Nodes:** Network vertex components tracking coordinates.
* `station_id` (String, Node Unique Primary Key): Matching foreign lookup codes matching the SQL table.
* `name` (String): Geographical descriptor string.

* **`METRO_LINK` / `RAIL_LINK` / `INTERCHANGE_TO` Edges:** Network trajectory link relationships.
* `line` (String, Nullable): Track identifiers routing specific path arrays.
* `travel_time_min` (Integer/Float): Edge weight mapping cost metrics between station nodes.
* `walk_time_min` (Integer/Float, Interchange Only): Cross-system transfer walking latency cost metric.

---

## Section 2 — Normalisation Justification

Our application relational schema model achieves strict **Third Normal Form (3NF)** compliance by systematically eradicating structural update anomalies, data redundancies, and partial or transitive operational dependencies.

### 2.1 Elimination of Transitive Dependencies (Achieving 3NF)

A relational layout breaches 3NF if a non-prime column attribute transitively depends on the primary key identifier via another intermediate non-prime attribute ($A \rightarrow B \rightarrow C$).

During our initial architecture workshops, we identified and neutralized several crucial 3NF risks:

1. **The Cryptographic Credential Violation:** If sensitive attributes like `password_hash` and `password_salt` coexisted inside the main flat demographic `users` ledger table, the table would suffer from structural transitive dependencies. The hash values do not map directly to individual user identities; instead, they depend on an entity's login context. By decoupling the architecture and isolating fields into a dedicated `user_credentials` table, we established a strict 1:1 foreign key binding relation (`REFERENCES users(user_id) ON DELETE CASCADE`). This choice satisfies 3NF rules, ensures absolute row isolation, and removes systemic risks of update anomalies during profile alterations.
2. **The Payment Ledger Split:** If payment method types and processing date logs resided directly within the `national_rail_bookings` table, a classic 3NF violation would emerge. The processing parameters depend on the payment execution sequence ($booking\_id \rightarrow payment\_id \rightarrow method$), rather than the structural trip reservation itself. Isolating this sub-system into an independent `payments` transaction ledger satisfies 3NF conditions and shields accounting rows from modifications made to passenger booking parameters.

### 2.2 First Normal Form (1NF) Compliance via Advanced Array and Document Store Handling

First Normal Form requires that all data table cells hold only atomic, indivisible values, firmly prohibiting multi-valued array sets or repeating structural columns.

To map complex multi-stop transit trajectories, we deployed advanced architectural choices to maintain strict 1NF compliance without resorting to endless junction rows:

1. **Mainline Train Tracks (`route_stations` VARCHAR[]):** For national rail lines, multi-value station stop grouping dependencies are mapped utilizing PostgreSQL's native `VARCHAR[]` vector arrays. Because these represent unchanging physical paths rather than transactional row entries, this representation preserves scalar records while enabling fast, index-driven checks with array containment operators (`@>`).
2. **Mass Transit Subway Paths (`stops_in_order` JSONB):** Metro line operations involve complex station sequences. To maintain 1NF atomicity while ensuring clean serialization, we implemented a semi-structured document approach using binary JSON columns (`JSONB`). This decision preserves the atomicity of the base record and enables high-speed, index-friendly validation routines using Postgres GIN structures.

### 2.3 Comprehensive Poly-Database Structural Synergy

Because our data layout is spread across three specialized engines, normalisation rules are carefully aligned with the strengths of each platform:

* **The Relational Storage (PostgreSQL):** Enforces strict mathematical transactional boundaries (3NF) over financial ledgers, ticketing states, and salted user credentials to eliminate anomalies.
* **The Network Topology Engine (Neo4j):** Replaces complex, multi-join SQL queries with indexed graph nodes and directional relationships (`-[:METRO_LINK]->`). This graph structure shifts the cost of path-finding from expensive runtime relational table scans to fast index-driven pointer traversals.
* **The Semantic Store Layer (pgvector):** Decouples unstructured corporate customer service policy documents from structured database records. By storing dense mathematical text vectors (`vector(768)`), it enables semantic intent matching that works independently from formal relational primary keys.

## Section 3 — Graph Database Design Rationale

### 3.1 Why Neo4j for the Transit Network?

While PostgreSQL excels at ACID-compliant financial ledgers and strict schema validation, mapping a deeply interconnected transit topology utilizing SQL requires expensive and recursive Common Table Expressions (`WITH RECURSIVE`). As the network scales, relational joins for pathfinding become a severe performance bottleneck.

Neo4j was selected because it treats relationships as first-class citizens. By adopting a **Graph (Network) Model**, we shift the computational cost from read-time recursive scans to index-driven pointer traversals. This architecture allows our AI routing agent to effortlessly compute time-weighted shortest paths and alternative detour routes (e.g., bypassing closed stations) in milliseconds.

### 3.2 Node and Relationship Specifications

We modeled the dual-network system with distinct operational boundaries but unified transfer capabilities:

* **Nodes (Vertices):**
  * `(m:MetroStation)`: Represents local subway stops. Properties include `station_id` (PK) and `name`.
  * `(r:RailStation)`: Represents cross-country mainline hubs.
* **Relationships (Edges):**
  * `[:METRO_LINK]`: Connects adjacent Metro stations. Contains the `travel_time_min` weight.
  * `[:RAIL_LINK]`: Connects adjacent Rail stations. Contains the `travel_time_min` weight.
  * `[:INTERCHANGE_TO]`: The crucial pedestrian transfer gateway connecting co-located Metro and Rail stations, utilizing a `walk_time_min` property to penalize complex system transfers during routing calculations.

### 3.3 Pathfinding Optimization

Initially, our routing algorithms relied on basic Neo4j `shortestPath()` functions, which only evaluated "node hops" rather than actual commute time. We refined our Cypher implementation to utilize **time-weighted Dijkstra algorithms**, aggregating the `travel_time_min` across all edges to ensure the AI assistant always suggests the genuinely fastest route, not just the one with the fewest stops.

---

## Section 4 — Vector / RAG Design

### 4.1 Limitations of Keyword Search

Traditional relational queries (`SELECT * WHERE content ILIKE '%bicycle%'`) fail when users input semantic variations (e.g., "Can I bring my bike?" or "Rules for two-wheelers"). To enable a highly intelligent Help Desk agent, we required a system capable of understanding the *intent* and *meaning* of user prompts.

### 4.2 pgvector Implementation and Configuration

We extended PostgreSQL with the `pgvector` extension to serve as our Retrieval-Augmented Generation (RAG) knowledge base.

* **Storage**: The `policy_documents` table stores unstructured text (e.g., lost property guidelines, penalty fare regulations expanded by our team) alongside their dense spatial representation in the `embedding` column (`VECTOR(768)`).
* **Retrieval Metric**: We utilize the Cosine Distance operator (`<=>`) supported by a Hierarchical Navigable Small World (`HNSW`) index to rapidly retrieve the top 3 (`VECTOR_TOP_K=3`) most semantically similar documents based on a strict `VECTOR_SIMILARITY_THRESHOLD`.

### 4.3 Architectural Decoupling

To ensure backend Gradio UI stability and prevent Python runtime circular-dependency blocks between the language configuration pipelines and the query logic, we deployed a dynamic module loader (`importlib.import_module("skeleton.llm")`) within `query_travel_policies`. This ensures the semantic embedding functions are initialized securely at runtime.

---

## Section 5 — AI Tool Usage Evidence

Our team utilized AI assistants (Gemini, Copilot, and Cursor) intensively for rapid prototyping, architecture brainstorming, and debugging.

### 5.1 The `AI_SESSION_CONTEXT.md` Team Contract

To prevent AI "hallucinations" (where different AI agents invent conflicting table names or columns), we strictly maintained the `AI_SESSION_CONTEXT.md` file. Before generating any SQL or Python logic, every member primed their AI with the agreed-upon 11 relational schemas and Neo4j node labels. This guaranteed perfectly synchronized syntax across all team branches.

### 5.2 Specific AI Contributions

* **DDL Generation**: We prompted the AI to generate our foundational `schema.sql` with specific instructions to split credentials from user profiles to achieve 3NF compliance and enforce `NUMERIC(10,2)` types for all financial columns.
* **Complex Bug Resolution**: When facing race conditions during high-concurrency ticket booking (`execute_booking`), we utilized AI to refactor our Python `psycopg2` logic, injecting pessimistic `FOR UPDATE` row-level locks and explicit `conn.autocommit = False` transaction boundaries.

---

## Section 6 — Reflection & Trade-offs

Building a Polyglot Persistence architecture (Relational + Graph + Vector) exposed our team to real-world system engineering trade-offs.

### 6.1 The Power of Specialized Engines

Using the right tool for the job provided immense benefits. Neo4j made recursive pathfinding trivial, `pgvector` made our chatbot highly conversational, and PostgreSQL provided ironclad ACID guarantees for payments and bookings.

### 6.2 The Cost of Distributed Complexity

The primary trade-off was **synchronization overhead**. If a physical train station is added to the system, it must be inserted into PostgreSQL (for billing and schedules) and concurrently seeded into Neo4j (for routing). Managing distributed transactions across multiple database paradigms is inherently complex. We mitigated this by keeping all financial and state-changing write operations strictly confined to PostgreSQL, treating Neo4j strictly as a read-optimized routing engine.

## Section 7 — Promo Code Subsystem (Task 6 Bonus)

### Motivation

Adding a promotional code subsystem provides significant commercial value to TransitFlow. It enables the operator to run targeted marketing campaigns and seasonal discounts while safely enforcing strict redemption limits (maximum uses and expiry dates) under high-concurrency booking environments.

### Database Changes

We introduced a new `promo_codes` table to track discount configurations alongside an atomic usage counter, complemented by a specific B-Tree index for active codes.

```sql
CREATE TABLE IF NOT EXISTS promo_codes (
    code VARCHAR(20) PRIMARY KEY,
    discount_percent NUMERIC(5,2) NOT NULL CHECK (discount_percent > 0 AND discount_percent <= 100),
    max_uses INT NOT NULL,
    current_uses INT DEFAULT 0,
    expiry_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_promo_codes_lookup ON promo_codes(code) WHERE is_active = TRUE;

```

### Example Queries

To validate a code during booking, we use a pessimistic lock (`FOR UPDATE`) to prevent race conditions when multiple users try to claim the last available voucher:

```sql
SELECT code, discount_percent, max_uses, current_uses, expiry_date 
FROM promo_codes 
WHERE code = 'TRANSIT10' AND is_active = TRUE 
FOR UPDATE;

```

**Expected Output:**
`[{"code": "TRANSIT10", "discount_percent": 10.00, "max_uses": 100, "current_uses": 0, "expiry_date": "2027-12-31"}]`

### Testing Evidence

* **Promo Code Validation**: Executing `query_validate_promo_code('TRANSIT10')` returns a JSON record containing `discount_percent: 10.00` and `is_active: True`.
* **Concurrency Locking Test**: Multiple simulated booking requests targeting the same promotion bucket (`current_uses < max_uses`) successfully locked the row for update, ensuring `current_uses` increments linearly without race condition overwrites (verified via transaction trace logs).

```markdown

---
