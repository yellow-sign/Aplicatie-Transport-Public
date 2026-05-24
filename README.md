# Aplicatie-Transport-Public
Aplicație desktop dezvoltată în Python + PyQt5, conectată la PostgreSQL, pentru gestionarea și vizualizarea transportului public din Constanța folosind OpenStreetMap.

- Frontend: PyQt5 pentru interfața grafică  
- Mapping: OpenStreetMap + Folium pentru vizualizare hărți  
- Backend: Python 3.x  
- Bază de Date: PostgreSQL cu psycopg2  
- Algoritmi: Dijkstra pentru găsirea rutelor optime  

Script pentru popularea bazei de date (utilizand API-ul OSM): 
1. data.py -> locațiile stațțiilor de autobuz
2. schedule.py -> liniile și opririle lor în stații
3. sch.py -> generează programele liniilor (nu există date în OSM)

Aplicatie:
main.py + Baza de date
