import psycopg2
from datetime import time

# script for generating timed bus schedules
# 3rd to be run

conn = psycopg2.connect(
    host="localhost",
    database="tpbd",
    user="nico",
    password="eon"
)
cur = conn.cursor()

# table:
# schedule(id_s INT, id_l INT, times TIME[])

# PARAMETERS
START_TIME = 5 * 60      # 05:00
END_TIME   = 23 * 60     # 23:00
FREQUENCY  = 10          # minutes between buses

# GENERATE TIME VECTOR
def generate_times():
    times = []
    t = START_TIME
    while t <= END_TIME:
        times.append(time(t // 60, t % 60))
        t += FREQUENCY
    return times

arrival_times = generate_times()

# FILL SCHEDULES
cur.execute("""
    SELECT id_s, id_l
    FROM stop
""")

rows = cur.fetchall()

for id_s, id_l in rows:
    cur.execute("""
        INSERT INTO schedule(id_s, id_l, time)
        VALUES (%s, %s, %s)
    """, (id_s, id_l, arrival_times))

conn.commit()
cur.close()
conn.close()

print("Bus schedules populated")
