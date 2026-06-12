# Work Allocation Report — Group 22

## 1. Team Members

| Full Name | Student ID | GitHub Username | Email |
| --- | --- | --- | --- |
| 張學睿 (Team Lead) | 113403520 | ds0w0 | <raythesnowman@gmail.com> |
| 陸昱霖 | 112403517 | chocomint408 | <yulinlu866@gmail.com> |
| 王宇崴 | 113403022 | yikes0000 | <weiwei950613@gmail.com> |

---

## 2. Task Ownership

### Code Repository

| Task | Primary Owner | Supporting Member(s) | Notes |
| --- | --- | --- | --- |
| **Task 1** — Relational schema design (`schema.sql`) | **ds0w0** | chocomint408 | Designed table structures for users, salt credentials, bookings, payments, and polymorphic feedback. |
| **Task 2a** — Core availability & fare queries | **ds0w0** | | Authored parameterised SQL handlers for rail lookup occupancy and metro interval calculations. |
| **Task 2b** — Seat & user queries | **ds0w0** | | Authored profile retrieval and joined relational table transaction logs. |
| **Task 2c** — Write operations (`execute_booking`, `execute_cancellation`) | **ds0w0** | | Implemented rigorous multi-table transaction blocks with programmatic ROLLBACK error isolation. |
| **Task 2d** — Authentication queries | **ds0w0** | | Developed cryptographically sound SHA-256 password salting flows to eliminate plain-text vectors. |
| **Task 3** — PostgreSQL seeding (`seed_postgres.py`) | **ds0w0** | **chocomint408**, yikes0000 | Configured dynamic tuple loaders using `execute_values` with complete `ON CONFLICT DO NOTHING` logic. Successfully seeded all 11 core tables (stations, schedules, user credentials, feedback, and metro history). |
| **Task 4** — Neo4j graph design & seeding (`seed_neo4j.py`, `seed.cypher`) | **chocomint408** | | Architected graph database schema containing interchange networks, `METRO_LINK`, and topological costs. |
| **Task 5** — Neo4j query functions (`graph/queries.py`) | **chocomint408** | **ds0w0** | Written initially by chocomint408. **ds0w0 provided refactoring support** during code integration to ensure precise time-weighted output sorting alignment. |
| **Task 6** — Optional extension *(Promo Codes, Trip History & RAG)* | **ds0w0**, **yikes0000** | chocomint408 | ds0w0 engineered a highly concurrent Promo Code relational database subsystem using strict atomic locks. yikes0000 extended the RAG knowledge base with 4 new policy sections and implemented a custom Trip History Panel in the UI. Both co-authored `TASK6.md` to document the full extension scope. |

### Design Document

| Section | Primary Author | Supporting Member(s) | Notes |
| --- | --- | --- | --- |
| Section 1 — ER Diagram | **ds0w0** | | Generated data visualisations using dbdiagram.io formats. |
| Section 2 — Normalisation Justification | **ds0w0** | | Authored logic breakdown logs ensuring strict 3NF database layout compliance. |
| Section 3 — Graph Database Design Rationale | **chocomint408** | | Authored architectural rationale behind graph node relationship topologies. |
| Section 4 — Vector / RAG Design | **yikes0000** | | Documented RAG pipeline stages, embedding dimension choices, cosine similarity rationale, and provider switching consequences. |
| Section 5 — AI Tool Usage Evidence | **ds0w0** | chocomint408, yikes0000 | Consolidated diagnostic chat stubs and repository graph snapshots. |
| Section 6 — Reflection & Trade-offs | **chocomint408** | ds0w0, yikes0000 | Synthesized cross-system analysis comparing ACID relational models vs network graphs. |
| Section 7 — Task 6 Extension | **yikes0000** | | Documented motivation for Trip History Panel, UI design decisions, schema queries used, and testing evidence with screenshots. |

---

## 3. Estimated Contribution Percentages

| Member | Estimated % | Brief justification |
| --- | --- | --- |
| **張學睿 (ds0w0)** | **37.5%** | Designed the entire core relational database management layout, parameterised lookup structures, transaction scopes, and automated python table-seeding configurations. Provided critical module dependency fix. |
| **陸昱霖 (chocomint408)** | **37.5%** | Spearheaded the full graph database network architecture, authoring Cypher link parameters, edge weights, and routing lookups. Conducted exhaustive localized application performance verification checks. |
| **王宇崴 (yikes0000)** | **25%** | Extended RAG knowledge base with 4 new policy sections (`children_and_family`, `passenger_conduct`, `season_tickets_and_passes`, `special_services`) and verified end-to-end vector seeding (21 documents total). Implemented Task 6 Trip History Panel UI extension, enabling users to view past national rail bookings and metro trips in a structured table format queried directly from PostgreSQL. Authored Design Document Section 4 and Section 7. |
| **Total** | **100%** | |

---

## 4. Mid-Project Changes

| Change | Original plan | Revised plan | Reason |
| --- | --- | --- | --- |
| **RAG Runtime Dependency Patch** | yikes0000 embeds hardcoded vector providers. | ds0w0 deployed an `importlib` module dynamic injection bridge. | Static circular dependencies blocked the execution pipeline between language configurations and database query logic during cross-system integration, requiring ds0w0 to deploy a dynamic import patch. |
| **Task 6 Scope Expansion** | yikes0000 handles RAG knowledge base only. | yikes0000 additionally implemented Trip History Panel UI extension. | The panel adds a meaningful new interaction mode (structured booking table) that the chat-only interface cannot replicate, qualifying for full Task 6 database extension marks rather than UI-only cap. |

---

## 5. Team Declaration

We confirm that this work allocation accurately reflects how responsibilities were divided within our team.

| Name | Signature / Typed name | Date |
| --- | --- | --- |
| 張學睿 | 張學睿 | 2026-06-03 |
| 陸昱霖 | 陸昱霖 | 2026-06-03 |
| 王宇崴 | 王宇崴| 2026-06-12 |
