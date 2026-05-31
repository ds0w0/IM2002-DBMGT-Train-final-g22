"""
skeleton/seed_neo4j.py
======================
從 train-mock-data/ 讀取車站 JSON，
在 Neo4j 建立 MetroStation / NationalRailStation 節點
以及 METRO_LINK / RAIL_LINK / INTERCHANGE_TO 關係。

使用方式：
  Windows PowerShell:  python skeleton/seed_neo4j.py
  macOS / Linux:       python3 skeleton/seed_neo4j.py
"""

import json
import os
import sys

sys.path.insert(0, ".")

from neo4j import GraphDatabase
from skeleton.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

NEO4J_USERNAME = NEO4J_USER  # 統一變數名稱

_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "train-mock-data")
)


def _load(filename: str) -> list:
    with open(os.path.join(_DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


def seed_metro_stations(session, metro_stations: list) -> None:
    for s in metro_stations:
        session.run(
            """
            MERGE (n:MetroStation {station_id: $id})
            SET n.name                         = $name,
                n.lines                        = $lines,
                n.is_interchange_metro         = $is_interchange_metro,
                n.interchange_metro_lines      = $interchange_metro_lines,
                n.is_interchange_national_rail = $is_interchange_national_rail
            """,
            id=s["station_id"],
            name=s["name"],
            lines=s["lines"],
            is_interchange_metro=s["is_interchange_metro"],
            interchange_metro_lines=s.get("interchange_metro_lines", []),
            is_interchange_national_rail=s["is_interchange_national_rail"],
        )
    print(f"  ✅ MetroStation 節點：{len(metro_stations)} 個")


def seed_national_rail_stations(session, nr_stations: list) -> None:
    for s in nr_stations:
        session.run(
            """
            MERGE (n:NationalRailStation {station_id: $id})
            SET n.name                            = $name,
                n.lines                           = $lines,
                n.is_interchange_national_rail    = $is_interchange_national_rail,
                n.interchange_national_rail_lines = $interchange_national_rail_lines,
                n.is_interchange_metro            = $is_interchange_metro
            """,
            id=s["station_id"],
            name=s["name"],
            lines=s["lines"],
            is_interchange_national_rail=s["is_interchange_national_rail"],
            interchange_national_rail_lines=s.get("interchange_national_rail_lines", []),
            is_interchange_metro=s["is_interchange_metro"],
        )
    print(f"  ✅ NationalRailStation 節點：{len(nr_stations)} 個")


def seed_metro_links(session, metro_stations: list) -> None:
    count = 0
    for s in metro_stations:
        for adj in s.get("adjacent_stations", []):
            session.run(
                """
                MATCH (a:MetroStation {station_id: $from_id})
                MATCH (b:MetroStation {station_id: $to_id})
                MERGE (a)-[r:METRO_LINK {line: $line}]->(b)
                SET r.travel_time_min = $time
                """,
                from_id=s["station_id"],
                to_id=adj["station_id"],
                line=adj["line"],
                time=adj["travel_time_min"],
            )
            count += 1
    print(f"  ✅ METRO_LINK 關係：{count} 條")


def seed_rail_links(session, nr_stations: list) -> None:
    count = 0
    for s in nr_stations:
        for adj in s.get("adjacent_stations", []):
            session.run(
                """
                MATCH (a:NationalRailStation {station_id: $from_id})
                MATCH (b:NationalRailStation {station_id: $to_id})
                MERGE (a)-[r:RAIL_LINK {line: $line}]->(b)
                SET r.travel_time_min = $time
                """,
                from_id=s["station_id"],
                to_id=adj["station_id"],
                line=adj["line"],
                time=adj["travel_time_min"],
            )
            count += 1
    print(f"  ✅ RAIL_LINK 關係：{count} 條")


def seed_interchange_links(session, metro_stations: list) -> None:
    count = 0
    for s in metro_stations:
        if s["is_interchange_national_rail"] and s.get("interchange_national_rail_station_id"):
            nr_id = s["interchange_national_rail_station_id"]
            session.run(
                """
                MATCH (m:MetroStation {station_id: $ms_id})
                MATCH (n:NationalRailStation {station_id: $nr_id})
                MERGE (m)-[r:INTERCHANGE_TO]->(n)
                SET r.walk_time_min = 5, r.interchange_type = "metro_to_rail"
                """,
                ms_id=s["station_id"],
                nr_id=nr_id,
            )
            session.run(
                """
                MATCH (m:MetroStation {station_id: $ms_id})
                MATCH (n:NationalRailStation {station_id: $nr_id})
                MERGE (n)-[r:INTERCHANGE_TO]->(m)
                SET r.walk_time_min = 5, r.interchange_type = "rail_to_metro"
                """,
                ms_id=s["station_id"],
                nr_id=nr_id,
            )
            count += 2
    print(f"  ✅ INTERCHANGE_TO 關係：{count} 條")


def seed():
    print("\n🚀 開始 Neo4j Graph Seeding...")

    metro_stations = _load("metro_stations.json")
    nr_stations    = _load("national_rail_stations.json")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    with driver.session() as session:

        session.run("MATCH (n) DETACH DELETE n")
        print("  Cleared existing graph data")

        print("\n📍 建立車站節點...")
        seed_metro_stations(session, metro_stations)
        seed_national_rail_stations(session, nr_stations)

        print("\n🔗 建立連線關係...")
        seed_metro_links(session, metro_stations)
        seed_rail_links(session, nr_stations)
        seed_interchange_links(session, metro_stations)

        print("\n🔍 驗證結果...")
        r1 = session.run("MATCH (n:MetroStation) RETURN count(n) AS cnt").single()
        r2 = session.run("MATCH (n:NationalRailStation) RETURN count(n) AS cnt").single()
        r3 = session.run("MATCH ()-[r:METRO_LINK]->() RETURN count(r) AS cnt").single()
        r4 = session.run("MATCH ()-[r:RAIL_LINK]->() RETURN count(r) AS cnt").single()
        r5 = session.run("MATCH ()-[r:INTERCHANGE_TO]->() RETURN count(r) AS cnt").single()
        print(f"   MetroStation：{r1['cnt']} 個")
        print(f"   NationalRailStation：{r2['cnt']} 個")
        print(f"   METRO_LINK：{r3['cnt']} 條")
        print(f"   RAIL_LINK：{r4['cnt']} 條")
        print(f"   INTERCHANGE_TO：{r5['cnt']} 條")

    driver.close()
    print("\n✅ Neo4j Seeding 完成！")
    print("   Open http://localhost:7475 to explore the graph.")


if __name__ == "__main__":
    print("Connecting to Neo4j...")
    seed()