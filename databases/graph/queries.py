"""
TransitFlow — Neo4j Graph Database Layer
=========================================
This module handles all queries to Neo4j.
"""

from __future__ import annotations
from typing import Optional
from neo4j import GraphDatabase
from skeleton.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def _driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def example_count_nodes() -> int:
    with _driver() as driver:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS total")
            return result.single()["total"]


# ── FASTEST ROUTE ─────────────────────────────────────────────────────────────

def query_shortest_route(
    origin_id: str,
    destination_id: str,
    network: str = "auto",
) -> dict:
    """
    Find the fastest path between two stations using shortestPath().
    Works on metro-only, rail-only, or cross-network journeys.
    """
    from_label = "MetroStation" if origin_id.startswith("MS") else "NationalRailStation"
    to_label   = "MetroStation" if destination_id.startswith("MS") else "NationalRailStation"

    with _driver() as driver:
        with driver.session() as session:
            result = session.run(
                f"""
                MATCH (start:{from_label} {{station_id: $from_id}}),
                      (end:{to_label}   {{station_id: $to_id}}),
                      p = shortestPath(
                            (start)-[:METRO_LINK|RAIL_LINK|INTERCHANGE_TO*]-(end)
                          )
                RETURN [n IN nodes(p) | {{
                            station_id: n.station_id,
                            name: n.name,
                            type: CASE WHEN n:MetroStation THEN 'metro' ELSE 'national_rail' END
                       }}] AS stations,
                       [r IN relationships(p) | {{
                            type: type(r),
                            line: r.line,
                            travel_time_min: r.travel_time_min,
                            walk_time_min: r.walk_time_min
                       }}] AS links,
                       reduce(t = 0, r IN relationships(p) |
                            t + coalesce(r.travel_time_min, r.walk_time_min, 0)
                       ) AS total_time
                """,
                from_id=origin_id,
                to_id=destination_id,
            )
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
        stop = {"order": i + 1, "station_id": s["station_id"],
                "name": s["name"], "network": s["type"]}
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
        "total_time_min": total,
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
    Find the fastest path that avoids a specific closed/delayed station.
    """
    from_label  = "MetroStation" if origin_id.startswith("MS") else "NationalRailStation"
    to_label    = "MetroStation" if destination_id.startswith("MS") else "NationalRailStation"

    with _driver() as driver:
        with driver.session() as session:
            avoid_info = session.run(
                "MATCH (n {station_id: $id}) RETURN n.name AS name",
                id=avoid_station_id,
            ).single()
            avoid_name = avoid_info["name"] if avoid_info else avoid_station_id

            result = session.run(
                f"""
                MATCH (start:{from_label} {{station_id: $from_id}}),
                      (end:{to_label}   {{station_id: $to_id}})
                MATCH p = shortestPath(
                            (start)-[:METRO_LINK|RAIL_LINK|INTERCHANGE_TO*]-(end)
                          )
                WHERE NONE(n IN nodes(p) WHERE n.station_id = $avoid_id)
                RETURN [n IN nodes(p) | {{
                            station_id: n.station_id,
                            name: n.name,
                            type: CASE WHEN n:MetroStation THEN 'metro' ELSE 'national_rail' END
                       }}] AS stations,
                       [r IN relationships(p) | {{
                            type: type(r),
                            line: r.line,
                            travel_time_min: r.travel_time_min,
                            walk_time_min: r.walk_time_min
                       }}] AS links,
                       reduce(t = 0, r IN relationships(p) |
                            t + coalesce(r.travel_time_min, r.walk_time_min, 0)
                       ) AS total_time
                ORDER BY total_time ASC
                LIMIT 1
                """,
                from_id=origin_id,
                to_id=destination_id,
                avoid_id=avoid_station_id,
            )
            record = result.single()

    if not record:
        return {
            "found": False,
            "avoided_station": avoid_name,
            "message": f"⚠️ {avoid_name} 封閉中，且找不到替代路線。建議改搭公車或聯繫客服。",
        }

    stations = record["stations"]
    links    = record["links"]
    total    = record["total_time"]

    stops = []
    for i, s in enumerate(stations):
        stop = {"order": i + 1, "station_id": s["station_id"],
                "name": s["name"], "network": s["type"]}
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
        "total_time_min":  total,
        "note": f"⚠️ {avoid_name} 目前封閉，此為繞道替代路線。",
    }


# ── CROSS-NETWORK INTERCHANGE PATH ───────────────────────────────────────────

def query_interchange_path(origin_id: str, destination_id: str) -> dict:
    """跨網路路徑，等同於 query_shortest_route 的跨網路版本。"""
    return query_shortest_route(origin_id, destination_id, network="auto")


# ── DELAY RIPPLE ANALYSIS ─────────────────────────────────────────────────────

def query_delay_ripple(delayed_station_id: str, hops: int = 2) -> list[dict]:
    """
    Find all stations within N hops of a disrupted station.
    """
    with _driver() as driver:
        with driver.session() as session:
            result = session.run(
                """
                MATCH (start {station_id: $station_id})
                MATCH (start)-[:METRO_LINK|RAIL_LINK*1..$hops]-(affected)
                WHERE affected.station_id <> $station_id
                RETURN DISTINCT
                    affected.station_id AS station_id,
                    affected.name       AS name,
                    affected.lines      AS lines_affected,
                    min(length(shortestPath(
                        (start)-[:METRO_LINK|RAIL_LINK*]-(affected)
                    ))) AS hops_away
                ORDER BY hops_away
                """,
                station_id=delayed_station_id,
                hops=hops,
            )
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