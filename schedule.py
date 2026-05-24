import requests
import psycopg2
import time

# script for retrieving bus line & stop data from OSM database
# 2nd to be run


# OVERPASS
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]
HEADERS = {"User-Agent": "TP-App/1.0"}

# Constanta bounding box
BBOX = "44.13,28.56,44.23,28.68"

# DB
conn = psycopg2.connect(
    host="localhost",
    database="tpbd",
    user="nico",
    password="eon"
)
cur = conn.cursor()

# HELPERS
def overpass(query):
    for url in OVERPASS_ENDPOINTS:
        try:
            r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=180)
            r.raise_for_status()
            return r.json()["elements"]
        except Exception:
            time.sleep(5)
    raise RuntimeError("Overpass failed")

# BUS ROUTES
ROUTE_QUERY = f"""
[out:json][timeout:180];
relation["route"="bus"]({BBOX});
out body;
>;
out skel qt;
"""

elements = overpass(ROUTE_QUERY)

# INSERT LINES (ONE PER DIRECTION)
relation_to_line = {}

for el in elements:
    if el["type"] != "relation":
        continue

    ref = el.get("tags", {}).get("ref", "0")
    direction = el.get("tags", {}).get("direction", "A")

    cur.execute("""
        INSERT INTO line(number, direction)
        VALUES (%s, %s)
        RETURNING id
    """, (ref, direction))

    relation_to_line[el["id"]] = cur.fetchone()[0]

conn.commit()

# MAP STATIONS
cur.execute("SELECT osm_id, id FROM station")
osm_to_station = dict(cur.fetchall())

# ASSIGN STOPS WITH ORDER
for el in elements:
    if el["type"] != "relation" or el["id"] not in relation_to_line:
        continue

    line_id = relation_to_line[el["id"]]
    seen = set()
    order = 0

    for m in el.get("members", []):
        if m["type"] == "node" and m["ref"] in osm_to_station:
            sid = osm_to_station[m["ref"]]
            if sid in seen:
                continue
            seen.add(sid)

            cur.execute("""
                INSERT INTO stop(id_s, id_l, stop_order)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (sid, line_id, order))
            order += 1

conn.commit()
cur.close()
conn.close()

print("Constanta bus routes, directions & stops imported successfully")
