// ============================================================
// TransitFlow — Neo4j Graph Seed File
// databases/graph/seed.cypher
//
// 說明：本檔案由 skeleton/seed_neo4j.py 執行時自動載入。
//       所有節點與關係均使用 MERGE，可安全重複執行。
//
// 節點類型：
//   MetroStation       — 捷運站 (MS01–MS20)
//   NationalRailStation — 國鐵站 (NR01–NR10)
//
// 關係類型：
//   METRO_LINK          — 捷運站之間的相鄰連線
//   RAIL_LINK           — 國鐵站之間的相鄰連線
//   INTERCHANGE_TO      — 捷運站 ↔ 國鐵站的轉乘連線
// ============================================================

// ─────────────────────────────────────────────────────────────
// SECTION 1 — 清除舊資料（重新 seed 時使用）
// ─────────────────────────────────────────────────────────────
MATCH (n) DETACH DELETE n;

// ─────────────────────────────────────────────────────────────
// SECTION 2 — 建立捷運站節點 (MetroStation)
// ─────────────────────────────────────────────────────────────

MERGE (s:MetroStation {station_id: "MS01"})
SET s.name = "Central Square",
    s.lines = ["M1", "M2"],
    s.is_interchange_metro = true,
    s.interchange_metro_lines = ["M1", "M2"],
    s.is_interchange_national_rail = true;

MERGE (s:MetroStation {station_id: "MS02"})
SET s.name = "Riverside",
    s.lines = ["M1"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS03"})
SET s.name = "Northgate",
    s.lines = ["M1"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS04"})
SET s.name = "Elm Park",
    s.lines = ["M1", "M3"],
    s.is_interchange_metro = true,
    s.interchange_metro_lines = ["M1", "M3"],
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS05"})
SET s.name = "Westfield",
    s.lines = ["M1"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS06"})
SET s.name = "Harbour View",
    s.lines = ["M2"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS07"})
SET s.name = "Old Town",
    s.lines = ["M2"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = true;

MERGE (s:MetroStation {station_id: "MS08"})
SET s.name = "University",
    s.lines = ["M2", "M4"],
    s.is_interchange_metro = true,
    s.interchange_metro_lines = ["M2", "M4"],
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS09"})
SET s.name = "Queensbridge",
    s.lines = ["M2"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS10"})
SET s.name = "Parkside",
    s.lines = ["M3"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS11"})
SET s.name = "Greenhill",
    s.lines = ["M3"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS12"})
SET s.name = "Lakeshore",
    s.lines = ["M3", "M4"],
    s.is_interchange_metro = true,
    s.interchange_metro_lines = ["M3", "M4"],
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS13"})
SET s.name = "Clifton",
    s.lines = ["M3"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS14"})
SET s.name = "Eastwick",
    s.lines = ["M4"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS15"})
SET s.name = "Ferndale",
    s.lines = ["M4"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = true;

MERGE (s:MetroStation {station_id: "MS16"})
SET s.name = "Hilltop",
    s.lines = ["M4"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS17"})
SET s.name = "Broadmoor",
    s.lines = ["M1", "M4"],
    s.is_interchange_metro = true,
    s.interchange_metro_lines = ["M1", "M4"],
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS18"})
SET s.name = "Sunnyvale",
    s.lines = ["M2"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS19"})
SET s.name = "Redwood",
    s.lines = ["M3"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

MERGE (s:MetroStation {station_id: "MS20"})
SET s.name = "Thornton",
    s.lines = ["M1"],
    s.is_interchange_metro = false,
    s.is_interchange_national_rail = false;

// ─────────────────────────────────────────────────────────────
// SECTION 3 — 建立國鐵站節點 (NationalRailStation)
// ─────────────────────────────────────────────────────────────

MERGE (s:NationalRailStation {station_id: "NR01"})
SET s.name = "Central Station",
    s.lines = ["NR1", "NR2"],
    s.is_interchange_national_rail = true,
    s.interchange_national_rail_lines = ["NR1", "NR2"],
    s.is_interchange_metro = true;

MERGE (s:NationalRailStation {station_id: "NR02"})
SET s.name = "Maplewood",
    s.lines = ["NR1"],
    s.is_interchange_metro = false;

MERGE (s:NationalRailStation {station_id: "NR03"})
SET s.name = "Old Town Junction",
    s.lines = ["NR1"],
    s.is_interchange_metro = true;

MERGE (s:NationalRailStation {station_id: "NR04"})
SET s.name = "Ashford",
    s.lines = ["NR1"],
    s.is_interchange_metro = false;

MERGE (s:NationalRailStation {station_id: "NR05"})
SET s.name = "Stonehaven",
    s.lines = ["NR1"],
    s.is_interchange_metro = false;

MERGE (s:NationalRailStation {station_id: "NR06"})
SET s.name = "Bridgeport",
    s.lines = ["NR2"],
    s.is_interchange_metro = false;

MERGE (s:NationalRailStation {station_id: "NR07"})
SET s.name = "Ferndale Halt",
    s.lines = ["NR2"],
    s.is_interchange_metro = true;

MERGE (s:NationalRailStation {station_id: "NR08"})
SET s.name = "Coalport",
    s.lines = ["NR2"],
    s.is_interchange_metro = false;

MERGE (s:NationalRailStation {station_id: "NR09"})
SET s.name = "Dunmore",
    s.lines = ["NR2"],
    s.is_interchange_metro = false;

MERGE (s:NationalRailStation {station_id: "NR10"})
SET s.name = "Langford End",
    s.lines = ["NR2"],
    s.is_interchange_metro = false;

// ─────────────────────────────────────────────────────────────
// SECTION 4 — 建立捷運站之間的 METRO_LINK 關係
// ─────────────────────────────────────────────────────────────

// MS01 Central Square
MATCH (a:MetroStation {station_id: "MS01"}), (b:MetroStation {station_id: "MS05"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS01"}), (b:MetroStation {station_id: "MS02"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS01"}), (b:MetroStation {station_id: "MS06"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS01"}), (b:MetroStation {station_id: "MS07"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 2;

// MS02 Riverside
MATCH (a:MetroStation {station_id: "MS02"}), (b:MetroStation {station_id: "MS01"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS02"}), (b:MetroStation {station_id: "MS03"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 2;

// MS03 Northgate
MATCH (a:MetroStation {station_id: "MS03"}), (b:MetroStation {station_id: "MS02"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS03"}), (b:MetroStation {station_id: "MS04"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 4;

// MS04 Elm Park
MATCH (a:MetroStation {station_id: "MS04"}), (b:MetroStation {station_id: "MS03"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 4;
MATCH (a:MetroStation {station_id: "MS04"}), (b:MetroStation {station_id: "MS17"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS04"}), (b:MetroStation {station_id: "MS12"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 3;

// MS05 Westfield
MATCH (a:MetroStation {station_id: "MS05"}), (b:MetroStation {station_id: "MS20"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS05"}), (b:MetroStation {station_id: "MS01"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 3;

// MS06 Harbour View
MATCH (a:MetroStation {station_id: "MS06"}), (b:MetroStation {station_id: "MS01"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 3;

// MS07 Old Town
MATCH (a:MetroStation {station_id: "MS07"}), (b:MetroStation {station_id: "MS01"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS07"}), (b:MetroStation {station_id: "MS18"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 2;

// MS08 University
MATCH (a:MetroStation {station_id: "MS08"}), (b:MetroStation {station_id: "MS18"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 4;
MATCH (a:MetroStation {station_id: "MS08"}), (b:MetroStation {station_id: "MS09"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS08"}), (b:MetroStation {station_id: "MS17"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 4;
MATCH (a:MetroStation {station_id: "MS08"}), (b:MetroStation {station_id: "MS12"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 4;

// MS09 Queensbridge
MATCH (a:MetroStation {station_id: "MS09"}), (b:MetroStation {station_id: "MS08"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 3;

// MS10 Parkside
MATCH (a:MetroStation {station_id: "MS10"}), (b:MetroStation {station_id: "MS11"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS10"}), (b:MetroStation {station_id: "MS12"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 4;

// MS11 Greenhill
MATCH (a:MetroStation {station_id: "MS11"}), (b:MetroStation {station_id: "MS10"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS11"}), (b:MetroStation {station_id: "MS19"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 3;

// MS12 Lakeshore
MATCH (a:MetroStation {station_id: "MS12"}), (b:MetroStation {station_id: "MS04"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS12"}), (b:MetroStation {station_id: "MS10"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 4;
MATCH (a:MetroStation {station_id: "MS12"}), (b:MetroStation {station_id: "MS08"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 4;
MATCH (a:MetroStation {station_id: "MS12"}), (b:MetroStation {station_id: "MS14"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 4;

// MS13 Clifton
MATCH (a:MetroStation {station_id: "MS13"}), (b:MetroStation {station_id: "MS19"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 2;

// MS14 Eastwick
MATCH (a:MetroStation {station_id: "MS14"}), (b:MetroStation {station_id: "MS12"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 4;
MATCH (a:MetroStation {station_id: "MS14"}), (b:MetroStation {station_id: "MS15"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 2;

// MS15 Ferndale
MATCH (a:MetroStation {station_id: "MS15"}), (b:MetroStation {station_id: "MS14"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS15"}), (b:MetroStation {station_id: "MS16"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 3;

// MS16 Hilltop
MATCH (a:MetroStation {station_id: "MS16"}), (b:MetroStation {station_id: "MS15"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 3;

// MS17 Broadmoor
MATCH (a:MetroStation {station_id: "MS17"}), (b:MetroStation {station_id: "MS04"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 3;
MATCH (a:MetroStation {station_id: "MS17"}), (b:MetroStation {station_id: "MS08"})
MERGE (a)-[r:METRO_LINK {line: "M4"}]->(b) SET r.travel_time_min = 4;

// MS18 Sunnyvale
MATCH (a:MetroStation {station_id: "MS18"}), (b:MetroStation {station_id: "MS07"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS18"}), (b:MetroStation {station_id: "MS08"})
MERGE (a)-[r:METRO_LINK {line: "M2"}]->(b) SET r.travel_time_min = 4;

// MS19 Redwood
MATCH (a:MetroStation {station_id: "MS19"}), (b:MetroStation {station_id: "MS13"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 2;
MATCH (a:MetroStation {station_id: "MS19"}), (b:MetroStation {station_id: "MS11"})
MERGE (a)-[r:METRO_LINK {line: "M3"}]->(b) SET r.travel_time_min = 3;

// MS20 Thornton
MATCH (a:MetroStation {station_id: "MS20"}), (b:MetroStation {station_id: "MS05"})
MERGE (a)-[r:METRO_LINK {line: "M1"}]->(b) SET r.travel_time_min = 2;

// ─────────────────────────────────────────────────────────────
// SECTION 5 — 建立國鐵站之間的 RAIL_LINK 關係
// ─────────────────────────────────────────────────────────────

// NR01 Central Station
MATCH (a:NationalRailStation {station_id: "NR01"}), (b:NationalRailStation {station_id: "NR02"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 12;
MATCH (a:NationalRailStation {station_id: "NR01"}), (b:NationalRailStation {station_id: "NR06"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 14;

// NR02 Maplewood
MATCH (a:NationalRailStation {station_id: "NR02"}), (b:NationalRailStation {station_id: "NR01"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 12;
MATCH (a:NationalRailStation {station_id: "NR02"}), (b:NationalRailStation {station_id: "NR03"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 18;

// NR03 Old Town Junction
MATCH (a:NationalRailStation {station_id: "NR03"}), (b:NationalRailStation {station_id: "NR02"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 18;
MATCH (a:NationalRailStation {station_id: "NR03"}), (b:NationalRailStation {station_id: "NR04"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 15;

// NR04 Ashford
MATCH (a:NationalRailStation {station_id: "NR04"}), (b:NationalRailStation {station_id: "NR03"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 15;
MATCH (a:NationalRailStation {station_id: "NR04"}), (b:NationalRailStation {station_id: "NR05"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 20;

// NR05 Stonehaven
MATCH (a:NationalRailStation {station_id: "NR05"}), (b:NationalRailStation {station_id: "NR04"})
MERGE (a)-[r:RAIL_LINK {line: "NR1"}]->(b) SET r.travel_time_min = 20;

// NR06 Bridgeport
MATCH (a:NationalRailStation {station_id: "NR06"}), (b:NationalRailStation {station_id: "NR01"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 14;
MATCH (a:NationalRailStation {station_id: "NR06"}), (b:NationalRailStation {station_id: "NR07"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 16;

// NR07 Ferndale Halt
MATCH (a:NationalRailStation {station_id: "NR07"}), (b:NationalRailStation {station_id: "NR06"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 16;
MATCH (a:NationalRailStation {station_id: "NR07"}), (b:NationalRailStation {station_id: "NR08"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 22;

// NR08 Coalport
MATCH (a:NationalRailStation {station_id: "NR08"}), (b:NationalRailStation {station_id: "NR07"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 22;
MATCH (a:NationalRailStation {station_id: "NR08"}), (b:NationalRailStation {station_id: "NR09"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 21;

// NR09 Dunmore
MATCH (a:NationalRailStation {station_id: "NR09"}), (b:NationalRailStation {station_id: "NR08"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 21;
MATCH (a:NationalRailStation {station_id: "NR09"}), (b:NationalRailStation {station_id: "NR10"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 19;

// NR10 Langford End
MATCH (a:NationalRailStation {station_id: "NR10"}), (b:NationalRailStation {station_id: "NR09"})
MERGE (a)-[r:RAIL_LINK {line: "NR2"}]->(b) SET r.travel_time_min = 19;

// ─────────────────────────────────────────────────────────────
// SECTION 6 — 建立捷運 ↔ 國鐵轉乘關係 (INTERCHANGE_TO)
// ─────────────────────────────────────────────────────────────

// MS01 (Central Square) ↔ NR01 (Central Station)
MATCH (m:MetroStation {station_id: "MS01"}), (n:NationalRailStation {station_id: "NR01"})
MERGE (m)-[r:INTERCHANGE_TO]->(n) SET r.walk_time_min = 5, r.interchange_type = "metro_to_rail";
MATCH (m:MetroStation {station_id: "MS01"}), (n:NationalRailStation {station_id: "NR01"})
MERGE (n)-[r:INTERCHANGE_TO]->(m) SET r.walk_time_min = 5, r.interchange_type = "rail_to_metro";

// MS07 (Old Town) ↔ NR03 (Old Town Junction)
MATCH (m:MetroStation {station_id: "MS07"}), (n:NationalRailStation {station_id: "NR03"})
MERGE (m)-[r:INTERCHANGE_TO]->(n) SET r.walk_time_min = 5, r.interchange_type = "metro_to_rail";
MATCH (m:MetroStation {station_id: "MS07"}), (n:NationalRailStation {station_id: "NR03"})
MERGE (n)-[r:INTERCHANGE_TO]->(m) SET r.walk_time_min = 5, r.interchange_type = "rail_to_metro";

// MS15 (Ferndale) ↔ NR07 (Ferndale Halt)
MATCH (m:MetroStation {station_id: "MS15"}), (n:NationalRailStation {station_id: "NR07"})
MERGE (m)-[r:INTERCHANGE_TO]->(n) SET r.walk_time_min = 5, r.interchange_type = "metro_to_rail";
MATCH (m:MetroStation {station_id: "MS15"}), (n:NationalRailStation {station_id: "NR07"})
MERGE (n)-[r:INTERCHANGE_TO]->(m) SET r.walk_time_min = 5, r.interchange_type = "rail_to_metro";