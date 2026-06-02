"""
TransitFlow — Neo4j Graph Database Layer
=========================================
This module handles all queries to Neo4j.
"""

from __future__ import annotations
from typing import Optional, Any, cast
from neo4j import GraphDatabase
from skeleton.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def _driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def example_count_nodes() -> int:
    with _driver() as driver:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS total")
            record = result.single()
            return record["total"] if record is not None else 0


# ── FASTEST ROUTE ─────────────────────────────────────────────────────────────

def query_shortest_route(
    origin_id: str,
    destination_id: str,
    network: str = "auto",
) -> dict:
    """
    Find the absolute fastest path between two stations based on real travel time,
    not just the fewer station hops. Supports cross-network transfers.
    """
    # 根據前綴動態決定標籤，精準鎖定節點起點與終點
    from_label = "MetroStation" if origin_id.startswith("MS") else "NationalRailStation"
    to_label   = "MetroStation" if destination_id.startswith("MS") else "NationalRailStation"

    # 💡 核心優化：拋棄盲目的 shortestPath()，改用路徑權重加總(REDUCE)並依時間正序排列，找出真正的「最快路徑」
    cypher_sql = f"""
        MATCH (start:{from_label} {{station_id: $from_id}}),
              (end:{to_label} {{station_id: $to_id}})
        MATCH p = (start)-[:METRO_LINK|RAIL_LINK|INTERCHANGE_TO*1..15]-(end)
        WITH p, 
             nodes(p) AS ns, 
             relationships(p) AS rels,
             reduce(t = 0, r IN relationships(p) | t + coalesce(r.travel_time_min, r.walk_time_min, 0)) AS total_time
        RETURN 
            [n IN ns | {{
                station_id: n.station_id,
                name: n.name,
                type: CASE WHEN n:MetroStation THEN 'metro' ELSE 'national_rail' END
            }}] AS stations,
            [r IN rels | {{
                type: type(r),
                line: coalesce(r.line, ''),
                travel_time_min: r.travel_time_min,
                walk_time_min: r.walk_time_min
            }}] AS links,
            total_time AS total_time
        ORDER BY total_time ASC
        LIMIT 1
    """

    with _driver() as driver:
        with driver.session() as session:
            result = session.run(cypher_sql, from_id=origin_id, to_id=destination_id)
            record = result.single()

    if not record:
        return {
            "found": False,
            "origin_id": origin_id,
            "destination_id": destination_id,
            "message": f"找不到從 {origin_id} 到 {destination_id} 的路線。",
        }

    stations = record["stations"]
    links    = record["links"]
    total    = record["total_time"]

    stops = []
    for i, s in enumerate(stations):
        stop = {
            "order": i + 1, 
            "station_id": s["station_id"],
            "name": s["name"], 
            "network": s["type"]
        }
        if i < len(links):
            lk = links[i]
            stop["connection_type"] = lk["type"]
            if lk["type"] == "INTERCHANGE_TO":
                stop["action"] = f"步行轉乘（約 {lk.get('walk_time_min', 5)} 分鐘）"
            else:
                stop["line"] = lk.get("line", "")
                stop["time_to_next_min"] = lk.get("travel_time_min", 0)
        stops.append(stop)

    lines_used = [lk["line"] for lk in links if lk.get("line")]
    transfers  = sum(1 for lk in links if lk["type"] == "INTERCHANGE_TO")

    return {
        "found": True,
        "from_station": stations[0]["name"],
        "to_station":   stations[-1]["name"],
        "stops": stops,
        "total_time_min": int(total),
        "transfers": transfers,
        "lines_used": list(dict.fromkeys(lines_used)),
    }


# ── ALTERNATIVE ROUTES (avoiding a station) ───────────────────────────────────

def query_alternative_routes(
    origin_id: str,
    destination_id: str,
    avoid_station_id: str,
    network: str = "auto",
    max_routes: int = 3,
) -> dict:
    """
    Find the fastest alternative path that completely circumvents a closed/delayed station.
    """
    from_label  = "MetroStation" if origin_id.startswith("MS") else "NationalRailStation"
    to_label    = "MetroStation" if destination_id.startswith("MS") else "NationalRailStation"

    with _driver() as driver:
        with driver.session() as session:
            # 安全查詢被封閉車站的名稱
            avoid_info = session.run(
                "MATCH (n) WHERE n.station_id = $id RETURN n.name AS name",
                id=avoid_station_id,
            ).single()
            avoid_name = avoid_info["name"] if avoid_info else avoid_station_id

            # 💡 核心優化：利用 NONE 關鍵字在全路徑生成時就排除該站，並依據時間代價排序
            cypher_sql = f"""
                MATCH (start:{from_label} {{station_id: $from_id}}),
                      (end:{to_label} {{station_id: $to_id}})
                MATCH p = (start)-[:METRO_LINK|RAIL_LINK|INTERCHANGE_TO*1..15]-(end)
                WHERE NONE(n IN nodes(p) WHERE n.station_id = $avoid_id)
                WITH p, 
                     reduce(t = 0, r IN relationships(p) | t + coalesce(r.travel_time_min, r.walk_time_min, 0)) AS total_time
                RETURN 
                    [n IN nodes(p) | {{
                        station_id: n.station_id,
                        name: n.name,
                        type: CASE WHEN n:MetroStation THEN 'metro' ELSE 'national_rail' END
                    }}] AS stations,
                    [r IN relationships(p) | {{
                        type: type(r),
                        line: coalesce(r.line, ''),
                        travel_time_min: r.travel_time_min,
                        walk_time_min: r.walk_time_min
                    }}] AS links,
                    total_time AS total_time
                ORDER BY total_time ASC
                LIMIT 1
            """
            
            result = session.run(cypher_sql, from_id=origin_id, to_id=destination_id, avoid_id=avoid_station_id)
            record = result.single()

    if not record:
        return {
            "found": False,
            "avoided_station": avoid_name,
            "message": f"⚠️ {avoid_name} 封閉中，且找不到替代繞道波段。建議改搭公車或聯繫客服。",
        }

    stations = record["stations"]
    links    = record["links"]
    total    = record["total_time"]

    stops = []
    for i, s in enumerate(stations):
        stop = {
            "order": i + 1, 
            "station_id": s["station_id"],
            "name": s["name"], 
            "network": s["type"]
        }
        if i < len(links):
            lk = links[i]
            stop["connection_type"] = lk["type"]
            if lk["type"] == "INTERCHANGE_TO":
                stop["action"] = f"步行轉乘（約 {lk.get('walk_time_min', 5)} 分鐘）"
            else:
                stop["line"] = lk.get("line", "")
                stop["time_to_next_min"] = lk.get("travel_time_min", 0)
        stops.append(stop)

    return {
        "found": True,
        "from_station":    stations[0]["name"],
        "to_station":      stations[-1]["name"],
        "avoided_station": avoid_name,
        "stops":           stops,
        "total_time_min":  int(total),
        "note": f"⚠️ {avoid_name} 目前封閉，此為繞道替代最快路徑。",
    }


# ── CROSS-NETWORK INTERCHANGE PATH ───────────────────────────────────────────

def query_interchange_path(origin_id: str, destination_id: str) -> dict:
    """跨網路路徑，等同於 query_shortest_route 的跨網路版本。"""
    return query_shortest_route(origin_id, destination_id, network="auto")


# ── DELAY RIPPLE ANALYSIS ─────────────────────────────────────────────────────

def query_delay_ripple(delayed_station_id: str, hops: int = 2) -> list[dict]:
    """
    Find all downstream stations within N拓撲步數(hops) of a disrupted station.
    Useful for proactive passenger alerting.
    """
    # 💡 核心優化：將 hops 強制轉化為安全正整數防範注入，並使用穩固的拓撲路徑深度限制語法
    safe_hops = max(1, min(int(hops), 5))
    
    cypher_sql = f"""
        MATCH (start {{station_id: $station_id}})
        MATCH (start)-[:METRO_LINK|RAIL_LINK*1..{safe_hops}]-(affected)
        WHERE affected.station_id <> $station_id
        WITH DISTINCT affected, start
        MATCH p = shortestPath((start)-[:METRO_LINK|RAIL_LINK*]-(affected))
        RETURN 
            affected.station_id AS station_id,
            affected.name       AS name,
            affected.lines      AS lines_affected,
            length(p)           AS hops_away
        ORDER BY hops_away ASC
    """
    with _driver() as driver:
        with driver.session() as session:
            # cast to Any to satisfy driver typing (LiteralString | Query) in type-checkers
            result = session.run(cast(Any, cypher_sql), station_id=delayed_station_id)
            return [dict(r) for r in result]


# ── STATION CONNECTIONS ───────────────────────────────────────────────────────

def query_station_connections(station_id: str) -> list[dict]:
    """List all direct connections from a given station."""
    with _driver() as driver:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (a {station_id: $station_id})-[r]->(b)
                RETURN b.station_id AS connected_station_id,
                       b.name       AS connected_station_name,
                       type(r)      AS relationship_type,
                       r.line       AS line,
                       coalesce(r.travel_time_min, r.walk_time_min) AS time_min
                ORDER BY time_min
                """,
                station_id=station_id,
            )
            return [dict(r) for r in result]
# ── CHEAPEST ROUTE ────────────────────────────────────────────────────────────

def query_cheapest_route(
    origin_id: str,
    destination_id: str,
    network: str = "auto",
    fare_class: str = "standard",
) -> dict:
    """
    Cheapest route — approximated by shortest travel time
    (fare data lives in PostgreSQL, not the graph).
    """
    return query_shortest_route(origin_id, destination_id, network)