import requests
import psycopg2
import time

# script for retrieving bus station data from OSM database
# 1st to be run

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
            r = requests.post(
                url,
                data={"data": query},
                headers=HEADERS,
                timeout=180
            )
            r.raise_for_status()
            return r.json()["elements"]
        except Exception:
            time.sleep(5)
    raise RuntimeError("Overpass failed")

# STOP QUERY
STOP_QUERY = f"""
[out:json][timeout:180];
(
  node["highway"="bus_stop"]({BBOX});
  node["public_transport"="platform"]({BBOX});
);
out body;
"""

elements = overpass(STOP_QUERY)

# INSERT STATIONS
count = 0

for el in elements:
    if el["type"] != "node":
        continue

    name = el.get("tags", {}).get("name", "Unnamed stop")
    lat = el["lat"]
    lon = el["lon"]
    osm_id = el["id"]

    cur.execute("""
        INSERT INTO station(nume, lat, lon, osm_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (osm_id) DO NOTHING
    """, (name, lat, lon, osm_id))

    count += 1

conn.commit()
cur.close()
conn.close()

print(f"Imported {count} Constanta bus stops")
