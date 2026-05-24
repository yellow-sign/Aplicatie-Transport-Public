
import sys
import psycopg2
from psycopg2 import sql, extras
from datetime import datetime, time, timedelta
import math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium
from folium import plugins
import json
import hashlib
import secrets
from pathlib import Path
import csv
import heapq

class DatabaseManager:
    """Handles all PostgreSQL database operations"""
    
    def __init__(self, host="localhost", database="transport_db", user="postgres", password="password"):
        self.connection = psycopg2.connect(
            host="localhost",
            database="tpbd",
            user="nico",
            password="pass"
        )
        self.cursor = self.connection.cursor(cursor_factory=extras.DictCursor)
    
    # User/Account methods
    def create_account(self, username, email, password, role="user"):
        """Create new account in the account table"""
        query = """
            INSERT INTO account (username, password, email, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        self.cursor.execute(query, (username, password, email, role))
        self.connection.commit()
        return self.cursor.fetchone()[0]
    
    def authenticate_user(self, username, password):
        """Authenticate user from account table"""
        query = "SELECT id, role FROM account WHERE username = %s AND password = %s"
        self.cursor.execute(query, (username, password))
        result = self.cursor.fetchone()
        
        if result:
            return {'id': result[0], 'role': result[1]}
        return None
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        query = "SELECT * FROM account WHERE id = %s"
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()
    
    def delete_account(self, user_id):
        """Delete user account"""
        query = "DELETE FROM account WHERE id = %s"
        self.cursor.execute(query, (user_id,))
        self.connection.commit()
    
    def update_account(self, user_id, username=None, email=None, password=None):
        """Update user account information"""
        updates = []
        params = []
        
        if username:
            updates.append("username = %s")
            params.append(username)
        if email:
            updates.append("email = %s")
            params.append(email)
        if password:
            updates.append("password = %s")
            params.append(password)
        
        if updates:
            query = f"UPDATE account SET {', '.join(updates)} WHERE id = %s"
            params.append(user_id)
            self.cursor.execute(query, tuple(params))
            self.connection.commit()
    
    # Station methods
    def get_all_stations(self):
        """Get all stations from station table"""
        query = "SELECT * FROM station ORDER BY nume"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_station_by_id(self, station_id):
        """Get station by ID"""
        query = "SELECT * FROM station WHERE id = %s"
        self.cursor.execute(query, (station_id,))
        return self.cursor.fetchone()
    
    def add_station(self, name, lat, lon, osm_id=None):
        """Add new station"""
        query = """
            INSERT INTO station (nume, lat, lon, osm_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        self.cursor.execute(query, (name, lat, lon, osm_id))
        self.connection.commit()
        return self.cursor.fetchone()[0]
    
    def update_station(self, station_id, name=None, lat=None, lon=None):
        """Update station information"""
        updates = []
        params = []
        
        if name:
            updates.append("nume = %s")
            params.append(name)
        if lat is not None:
            updates.append("lat = %s")
            params.append(lat)
        if lon is not None:
            updates.append("lon = %s")
            params.append(lon)
        
        if updates:
            query = f"UPDATE station SET {', '.join(updates)} WHERE id = %s"
            params.append(station_id)
            self.cursor.execute(query, tuple(params))
            self.connection.commit()
    
    def delete_station(self, station_id):
        """Delete station"""
        query = "DELETE FROM station WHERE id = %s"
        self.cursor.execute(query, (station_id,))
        self.connection.commit()
    
    # Line methods
    def get_all_lines(self):
        """Get all lines from line table"""
        query = "SELECT * FROM line ORDER BY number"
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_line_by_id(self, line_id):
        """Get line by ID"""
        query = "SELECT * FROM line WHERE id = %s"
        self.cursor.execute(query, (line_id,))
        return self.cursor.fetchone()
    
    def add_line(self, number, direction):
        """Add new line"""
        query = """
            INSERT INTO line (number, direction)
            VALUES (%s, %s)
            RETURNING id
        """
        self.cursor.execute(query, (number, direction))
        self.connection.commit()
        return self.cursor.fetchone()[0]
    
    def update_line(self, line_id, number=None, direction=None):
        """Update line information"""
        updates = []
        params = []
        
        if number:
            updates.append("number = %s")
            params.append(number)
        if direction:
            updates.append("direction = %s")
            params.append(direction)
        
        if updates:
            query = f"UPDATE line SET {', '.join(updates)} WHERE id = %s"
            params.append(line_id)
            self.cursor.execute(query, tuple(params))
            self.connection.commit()
    
    def delete_line(self, line_id):
        """Delete line"""
        query = "DELETE FROM line WHERE id = %s"
        self.cursor.execute(query, (line_id,))
        self.connection.commit()
    
    # Stop methods (junction table between station and line)
    def get_stops_for_line(self, line_id, direction=None):
        """Get all stops for a specific line with stop_order"""
        if direction:
            query = """
                SELECT s.id as station_id, s.nume, s.lat, s.lon, s.osm_id, st.stop_order
                FROM stop st
                JOIN station s ON st.id_s = s.id
                JOIN line l ON st.id_l = l.id
                WHERE st.id_l = %s AND l.direction = %s
                ORDER BY st.stop_order
            """
            self.cursor.execute(query, (line_id, direction))
        else:
            query = """
                SELECT s.id as station_id, s.nume, s.lat, s.lon, s.osm_id, st.stop_order
                FROM stop st
                JOIN station s ON st.id_s = s.id
                WHERE st.id_l = %s
                ORDER BY st.stop_order
            """
            self.cursor.execute(query, (line_id,))
        return self.cursor.fetchall()
    
    def get_all_stops(self):
        """Get all stops with line and station info"""
        query = """
            SELECT st.id_s, st.id_l, st.stop_order, s.nume as station_name, l.number as line_number
            FROM stop st
            JOIN station s ON st.id_s = s.id
            JOIN line l ON st.id_l = l.id
            ORDER BY l.number, st.stop_order
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def add_stop(self, station_id, line_id, stop_order):
        """Add stop to line"""
        query = """
            INSERT INTO stop (id_s, id_l, stop_order)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (station_id, line_id, stop_order))
        self.connection.commit()
    
    def update_stop_order(self, station_id, line_id, stop_order):
        """Update stop order"""
        query = """
            UPDATE stop 
            SET stop_order = %s
            WHERE id_s = %s AND id_l = %s
        """
        self.cursor.execute(query, (stop_order, station_id, line_id))
        self.connection.commit()
    
    def remove_stop(self, station_id, line_id):
        """Remove stop from line"""
        query = "DELETE FROM stop WHERE id_s = %s AND id_l = %s"
        self.cursor.execute(query, (station_id, line_id))
        self.connection.commit()
    
    # Schedule methods
    def get_schedule_for_line_station(self, line_id, station_id):
        """Get schedule for specific line and station"""
        query = """
            SELECT time FROM schedule
            WHERE id_l = %s AND id_s = %s
        """
        self.cursor.execute(query, (line_id, station_id))
        result = self.cursor.fetchone()
        return result[0] if result else []
    
    def get_all_schedules(self):
        """Get all schedules"""
        query = """
            SELECT s.id_l, s.id_s, s.time, l.number as line_number, st.nume as station_name
            FROM schedule s
            JOIN line l ON s.id_l = l.id
            JOIN station st ON s.id_s = st.id
            ORDER BY l.number, st.nume
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def add_schedule(self, line_id, station_id, times):
        """Add schedule for line and station"""
        query = """
            INSERT INTO schedule (id_l, id_s, time)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (line_id, station_id, times))
        self.connection.commit()
    
    def update_schedule(self, line_id, station_id, times):
        """Update schedule"""
        query = """
            UPDATE schedule 
            SET time = %s
            WHERE id_l = %s AND id_s = %s
        """
        self.cursor.execute(query, (times, line_id, station_id))
        self.connection.commit()
    
    def delete_schedule(self, line_id, station_id):
        """Delete schedule"""
        query = "DELETE FROM schedule WHERE id_l = %s AND id_s = %s"
        self.cursor.execute(query, (line_id, station_id))
        self.connection.commit()
    
    # Ticket and Travel methods
    def create_ticket(self, ticket_type):
        """Create a ticket"""
        query = """
            INSERT INTO ticket (type)
            VALUES (%s)
            RETURNING id
        """
        self.cursor.execute(query, (ticket_type,))
        self.connection.commit()
        return self.cursor.fetchone()[0]
    
    def create_travel(self, account_id, price, travel_date, travel_time):
        """Record a travel purchase"""
        query = """
            INSERT INTO calatorie (account_id, price, date, time)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        self.cursor.execute(query, (account_id, price, travel_date, travel_time))
        self.connection.commit()
        return self.cursor.fetchone()[0]
    
    def get_user_travels(self, account_id):
        """Get all travels for a user"""
        query = """
            SELECT * FROM calatorie 
            WHERE account_id = %s 
            ORDER BY date DESC, time DESC
        """
        self.cursor.execute(query, (account_id,))
        return self.cursor.fetchall()
    
    # Subscription methods
    def create_subscription(self, last_name, first_name, cnp, line_id):
        """Create a subscription"""
        try:
            #  Check NULL for general subscription
            if line_id in (0, -1, None):
                # General subscription (no specific line)
                query = """
                    INSERT INTO abonament (last_name, first_name, cnp, id_l)
                    VALUES (%s, %s, %s, NULL)
                    RETURNING id
                """
                params = (last_name, first_name, cnp)
            else:
                # Subscription for specific line
                query = """
                    INSERT INTO abonament (last_name, first_name, cnp, id_l)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """
                params = (last_name, first_name, cnp, line_id)
            
            self.cursor.execute(query, params)
            self.connection.commit()
            result = self.cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            self.connection.rollback()
            print(f"Error creating subscription: {e}")
            
            # Fallback: try with explicit ID
            try:
                # Get the next ID
                query = "SELECT COALESCE(MAX(id), 0) + 1 FROM abonament"
                self.cursor.execute(query)
                next_id = self.cursor.fetchone()[0]
                
                if line_id in (0, -1, None):
                    query = """
                        INSERT INTO abonament (id, last_name, first_name, cnp, id_l)
                        VALUES (%s, %s, %s, %s, NULL)
                    """
                    params = (next_id, last_name, first_name, cnp)
                else:
                    query = """
                        INSERT INTO abonament (id, last_name, first_name, cnp, id_l)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    params = (next_id, last_name, first_name, cnp, line_id)
                
                self.cursor.execute(query, params)
                self.connection.commit()
                return next_id
            except Exception as e2:
                print(f"Fallback also failed: {e2}")
                return None
        
    def get_subscriptions(self):
        """Get all subscriptions"""
        query = """
            SELECT a.*, l.number as line_number
            FROM abonament a
            LEFT JOIN line l ON a.id_l = l.id
            ORDER BY a.last_name, a.first_name
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    # Navigation and Route Planning
    def build_transport_graph(self):
        """Build weighted graph for navigation based on stops and schedules"""
        graph = {}
        
        # Get all stations to initialize the graph
        all_stations = self.get_all_stations()
        for station in all_stations:
            graph[station['id']] = []
        
        # Get all lines
        lines = self.get_all_lines()
        
        for line in lines:
            # Get stops for this line
            stops = self.get_stops_for_line(line['id'])
            
            # Sort stops by stop_order
            stops_sorted = sorted(stops, key=lambda x: x['stop_order'])
            
            # Build graph edges between consecutive stops
            for i in range(len(stops_sorted) - 1):
                current_stop = stops_sorted[i]
                next_stop = stops_sorted[i + 1]
                
                # Calculate travel time between stops based on schedules
                travel_time = self.calculate_travel_time_between_stops(
                    line['id'], 
                    current_stop['station_id'], 
                    next_stop['station_id']
                )
                
                # Add edge from current to next
                if current_stop['station_id'] not in graph:
                    graph[current_stop['station_id']] = []
                
                graph[current_stop['station_id']].append({
                    'target': next_stop['station_id'],
                    'weight': travel_time,
                    'line_id': line['id'],
                    'line_number': line['number'],
                    'direction': line['direction'],
                    'is_transfer': False
                })
        
        # Add walking connections between nearby stations (within 500m)
        # This helps with transfers but with a high penalty to discourage them
        for i, station1 in enumerate(all_stations):
            for j, station2 in enumerate(all_stations):
                if i >= j:
                    continue
                
                distance = self.haversine_distance(
                    station1['lat'], station1['lon'],
                    station2['lat'], station2['lon']
                )
                
                # If stations are within 500m, add walking connection with high penalty
                if distance <= 0.5:  # 500 meters
                    walking_time = distance * 12  # 12 minutes per km = 5 km/h walking speed
                    transfer_penalty = 10  # Extra penalty for transfers
                    total_weight = walking_time + transfer_penalty
                    
                    graph[station1['id']].append({
                        'target': station2['id'],
                        'weight': total_weight,
                        'line_id': None,
                        'line_number': 'WALK',
                        'direction': 'walk',
                        'is_transfer': True
                    })
                    
                    graph[station2['id']].append({
                        'target': station1['id'],
                        'weight': total_weight,
                        'line_id': None,
                        'line_number': 'WALK',
                        'direction': 'walk',
                        'is_transfer': True
                    })
        
        return graph
    
    def calculate_travel_time_between_stops(self, line_id, from_station_id, to_station_id):
        """Calculate average travel time between two consecutive stops"""
        from_schedule = self.get_schedule_for_line_station(line_id, from_station_id)
        to_schedule = self.get_schedule_for_line_station(line_id, to_station_id)
        
        if from_schedule and to_schedule and len(from_schedule) > 0 and len(to_schedule) > 0:
            # Calculate average time difference between matching schedule entries
            total_diff = 0
            count = 0
            
            # Try to match schedules by index
            for i in range(min(len(from_schedule), len(to_schedule))):
                try:
                    diff = self.time_difference(from_schedule[i], to_schedule[i])
                    if diff > 0:  # Ensure to_station is after from_station
                        total_diff += diff
                        count += 1
                except (ValueError, TypeError):
                    continue
            
            return total_diff / count if count > 0 else 5  # Default 5 minutes
        
        return 5  # Default fallback
    
    def time_difference(self, time1, time2):
        """Calculate time difference in minutes between two time objects"""
        if isinstance(time1, str):
            time1 = datetime.strptime(time1, '%H:%M:%S').time()
        if isinstance(time2, str):
            time2 = datetime.strptime(time2, '%H:%M:%S').time()
        
        dt1 = datetime.combine(datetime.today(), time1)
        dt2 = datetime.combine(datetime.today(), time2)
        
        diff = dt2 - dt1
        return diff.total_seconds() / 60

    def find_station_by_name(self, name):
        """Find station by name (case-insensitive, partial match)"""
        query = """
            SELECT * FROM station 
            WHERE LOWER(nume) LIKE LOWER(%s)
            ORDER BY nume
            LIMIT 1
        """
        self.cursor.execute(query, (f'%{name}%',))
        return self.cursor.fetchone()

    def find_station_by_name_exact(self, name):
        """Find station by exact name match"""
        query = "SELECT * FROM station WHERE nume = %s"
        self.cursor.execute(query, (name,))
        return self.cursor.fetchone()
    
    def find_nearest_stations(self, lat, lon, radius_km=1):
        """Find stations within radius using haversine formula"""
        stations = self.get_all_stations()
        nearby_stations = []
        
        for station in stations:
            distance = self.haversine_distance(lat, lon, station['lat'], station['lon'])
            if distance <= radius_km:
                station_with_distance = dict(station)
                station_with_distance['distance'] = distance
                nearby_stations.append(station_with_distance)
        
        return sorted(nearby_stations, key=lambda x: x['distance'])
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) ** 2) + math.cos(lat1_rad) * math.cos(lat2_rad) * (math.sin(delta_lon/2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def find_route(self, start_lat, start_lon, end_lat, end_lon):
        """Find optimal route between two locations using actual coordinates"""
        # Find nearest stations to start and end points
        start_stations = self.find_nearest_stations(start_lat, start_lon, 0.5)  # 500m radius
        end_stations = self.find_nearest_stations(end_lat, end_lon, 0.5)
        
        if not start_stations:
            # Try larger radius
            start_stations = self.find_nearest_stations(start_lat, start_lon, 1.0)
        if not end_stations:
            end_stations = self.find_nearest_stations(end_lat, end_lon, 1.0)
        
        if not start_stations or not end_stations:
            return None
        
        start_id = start_stations[0]['id']
        end_id = end_stations[0]['id']
        
        if start_id == end_id:
            return {
                'path': [{'station_id': start_id, 'line_id': None, 'line_number': None}],
                'total_time': 0,
                'start_station': self.get_station_by_id(start_id),
                'end_station': self.get_station_by_id(end_id),
                'transfer_count': 0
            }
        
        # Build graph
        graph = self.build_transport_graph()
        
        # Check if stations are in graph
        if start_id not in graph:
            # Find nearest station that is in graph
            for station in start_stations[1:]:
                if station['id'] in graph:
                    start_id = station['id']
                    break
        
        if end_id not in graph:
            # Find nearest station that is in graph
            for station in end_stations[1:]:
                if station['id'] in graph:
                    end_id = station['id']
                    break
        
        if start_id not in graph or end_id not in graph:
            return None
        
        # Initialize Dijkstra's algorithm with transfer tracking
        distances = {}
        previous = {}
        transfers = {}  # Track number of transfers
        lines_used = {}  # Track line used to reach each node
        
        for node in graph:
            distances[node] = float('inf')
            previous[node] = None
            transfers[node] = float('inf')
            lines_used[node] = None
        
        distances[start_id] = 0
        transfers[start_id] = 0
        
        # Priority queue: (total_cost, node, current_line, transfers_count)
        pq = [(0, start_id, None, 0)]
        
        while pq:
            current_cost, current, current_line, current_transfers = heapq.heappop(pq)
            
            # Skip if we found a better path already
            if current_cost > distances[current]:
                continue
            
            # If we reached the destination, we can stop
            if current == end_id:
                break
            
            # Explore neighbors
            for edge in graph.get(current, []):
                neighbor = edge['target']
                weight = edge['weight']
                edge_line = edge['line_id']
                edge_line_number = edge.get('line_number', 'WALK')
                
                # Calculate transfer penalty
                transfer_penalty = 0
                new_transfers = current_transfers
                
                # Check if this is a transfer (changing lines or walking)
                if current_line is not None and edge_line is not None and current_line != edge_line:
                    transfer_penalty = 10  # Penalty for changing bus lines
                    new_transfers += 1
                elif edge_line is None or edge_line_number == 'WALK':
                    # Walking connection
                    transfer_penalty = 5
                    if current_line is not None:  # If coming from a bus
                        new_transfers += 1
                
                total_cost = current_cost + weight + transfer_penalty
                
                # Skip if neighbor not in distances
                if neighbor not in distances:
                    continue
                
                # Update if we found a better path
                if (total_cost < distances[neighbor] or 
                    (total_cost == distances[neighbor] and new_transfers < transfers[neighbor])):
                    
                    distances[neighbor] = total_cost
                    previous[neighbor] = {
                        'node': current,
                        'line_id': edge_line,
                        'line_number': edge_line_number,
                        'direction': edge.get('direction', 'forward'),
                        'is_transfer': edge_line is None or edge_line_number == 'WALK'
                    }
                    transfers[neighbor] = new_transfers
                    lines_used[neighbor] = edge_line
                    
                    heapq.heappush(pq, (total_cost, neighbor, edge_line, new_transfers))
        
        # Check if path exists
        if distances[end_id] == float('inf'):
            return None
        
        # Reconstruct path
        path = []
        current = end_id
        while previous.get(current):
            path.insert(0, {
                'station_id': current,
                'line_id': previous[current]['line_id'],
                'line_number': previous[current]['line_number'],
                'direction': previous[current]['direction'],
                'is_transfer': previous[current]['is_transfer']
            })
            current = previous[current]['node']
        
        path.insert(0, {
            'station_id': start_id,
            'line_id': None,
            'line_number': None,
            'direction': None,
            'is_transfer': False
        })
        
        # Calculate actual travel time without penalties
        actual_time = 0
        for i in range(len(path) - 1):
            for edge in graph.get(path[i]['station_id'], []):
                if edge['target'] == path[i+1]['station_id']:
                    actual_time += edge['weight']
                    break
        
        # Simplify path to show only key stations
        simplified_path = self.simplify_route_path(path)
        
        return {
            'path': simplified_path,
            'full_path': path,
            'total_time': actual_time,
            'transfer_count': transfers[end_id],
            'start_station': self.get_station_by_id(start_id),
            'end_station': self.get_station_by_id(end_id)
        }
    
    def simplify_route_path(self, path):
        """Simplify route path to show only key stations: start, end, and transfer points"""
        if len(path) <= 3:
            return path
        
        simplified = [path[0]]  # Always include start
        
        for i in range(1, len(path) - 1):
            current = path[i]
            prev = simplified[-1]
            next_station = path[i + 1]
            
            # Include station if:
            # 1. It's a transfer point
            # 2. Line changes
            # 3. It's the last station before end
            if (current['is_transfer'] or 
                current['line_id'] != prev['line_id'] or
                i == len(path) - 2):
                simplified.append(current)
        
        simplified.append(path[-1])  # Always include end
        return simplified

class MapWidget(QWidget):
    """Interactive OpenStreetMap widget for Constanta with burger menu for lines"""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.selected_line_id = None
        self.current_route = None
        self.init_ui()
        self.load_map_data()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Top bar with burger menu and route controls
        top_bar = QHBoxLayout()
        
        # Burger menu button for lines
        self.burger_menu_btn = QPushButton("☰ Lines")
        self.burger_menu_btn.setFixedWidth(100)
        self.burger_menu_btn.clicked.connect(self.toggle_lines_menu)
        
        # Route planning controls
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start location")
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("Destination")
        
        self.find_route_btn = QPushButton("Find Route")
        self.find_route_btn.clicked.connect(self.find_route)
        
        self.clear_route_btn = QPushButton("Clear Route")
        self.clear_route_btn.clicked.connect(self.clear_route)
        
        # Toggle buttons
        self.show_stations_btn = QCheckBox("Stations")
        self.show_stations_btn.setChecked(True)
        self.show_stations_btn.stateChanged.connect(self.toggle_stations)
        
        self.show_all_lines_btn = QCheckBox("All Lines")
        self.show_all_lines_btn.setChecked(True)
        self.show_all_lines_btn.stateChanged.connect(self.toggle_all_lines)
        
        top_bar.addWidget(self.burger_menu_btn)
        top_bar.addWidget(QLabel("From:"))
        top_bar.addWidget(self.start_input)
        top_bar.addWidget(QLabel("To:"))
        top_bar.addWidget(self.end_input)
        top_bar.addWidget(self.find_route_btn)
        top_bar.addWidget(self.clear_route_btn)
        top_bar.addWidget(self.show_stations_btn)
        top_bar.addWidget(self.show_all_lines_btn)
        top_bar.addStretch()
        
        # Create side panel for lines menu (hidden by default)
        self.side_panel = QWidget()
        self.side_panel.setFixedWidth(250)
        side_layout = QVBoxLayout()
        
        # Lines list
        side_layout.addWidget(QLabel("Select Bus Line:"))
        self.lines_list = QListWidget()
        self.load_lines_list()
        self.lines_list.itemClicked.connect(self.select_line)
        
        # Show all lines button
        self.show_all_btn = QPushButton("Show All Lines")
        self.show_all_btn.clicked.connect(self.show_all_lines)
        
        # Clear selection button
        self.clear_selection_btn = QPushButton("Clear Selection")
        self.clear_selection_btn.clicked.connect(self.clear_line_selection)
        
        side_layout.addWidget(self.lines_list)
        side_layout.addWidget(self.show_all_btn)
        side_layout.addWidget(self.clear_selection_btn)
        side_layout.addStretch()
        
        self.side_panel.setLayout(side_layout)
        self.side_panel.setVisible(False)
        
        # Main content area (map + side panel)
        content_layout = QHBoxLayout()
        content_layout.addWidget(self.side_panel)
        
        # Create web view for OpenStreetMap
        self.web_view = QWebEngineView()
        self.create_constanta_map()
        content_layout.addWidget(self.web_view, 1)  # 1 = stretch factor
        
        # Route details panel
        self.route_details = QTextEdit()
        self.route_details.setReadOnly(True)
        self.route_details.setMaximumHeight(150)
        
        main_layout.addLayout(top_bar)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.route_details)
        self.setLayout(main_layout)
    
    def create_constanta_map(self):
        """Create OpenStreetMap centered on Constanta"""
        # Constanta coordinates
        constanta_coords = [44.1598, 28.6348]
        
        self.map = folium.Map(
            location=constanta_coords,
            zoom_start=13,
            tiles='OpenStreetMap',
            control_scale=True,
            attr='OpenStreetMap contributors'
        )
        
        # Add plugins
        plugins.Fullscreen().add_to(self.map)
        plugins.MousePosition().add_to(self.map)
        
        # Save and load map
        self.update_map_display()
    
    def load_map_data(self):
        """Load stations and lines from database"""
        self.station_markers = {}
        self.line_layers = {}
        
        # Load stations
        stations = self.db.get_all_stations()
        for station in stations:
            marker = folium.Marker(
                [station['lat'], station['lon']],
                popup=f"<b>{station['nume']}</b>",
                tooltip=station['nume'],
            )
            marker.add_to(self.map)
            self.station_markers[station['id']] = marker
        
        # Load all lines initially
        self.load_all_lines_to_map()
        
        self.update_map_display()
    
    def load_all_lines_to_map(self):
        """Load all bus lines to the map"""
        lines = self.db.get_all_lines()
        colors = ['red', 'green', 'orange', 'purple', 'darkblue', 'darkred', 'darkgreen', 'cadetblue']
        
        for idx, line in enumerate(lines):
            color = colors[idx % len(colors)]
            
            # Get stops for this line
            stops = self.db.get_stops_for_line(line['id'])
            if stops and len(stops) > 1:
                coordinates = [(s['lat'], s['lon']) for s in stops]
                
                # Create tooltip with line info
                line_info = f"Line {line['number']} ({line['direction']})"
                if len(stops) > 0:
                    line_info += f"<br>Stations: {len(stops)}"
                
                polyline = folium.PolyLine(
                    coordinates,
                    color=color,
                    weight=3,
                    opacity=0.7,
                    popup=line_info,
                    tooltip=f"Line {line['number']}"
                )
                polyline.add_to(self.map)
                self.line_layers[line['id']] = {
                    'layer': polyline,
                    'visible': True
                }
    
    def load_lines_list(self):
        """Load all lines into the side menu list"""
        lines = self.db.get_all_lines()
        self.lines_list.clear()
        
        for line in lines:
            item = QListWidgetItem(f"Line {line['number']} ({line['direction']})")
            item.setData(Qt.UserRole, line['id'])
            self.lines_list.addItem(item)
    
    def toggle_lines_menu(self):
        """Toggle the burger menu visibility"""
        self.side_panel.setVisible(not self.side_panel.isVisible())
        if self.side_panel.isVisible():
            self.burger_menu_btn.setText("✕ Close")
        else:
            self.burger_menu_btn.setText("☰ Lines")
    
    def select_line(self, item):
        """Select a specific line to show only its stations"""
        line_id = item.data(Qt.UserRole)
        self.selected_line_id = line_id
        
        # Clear the map and reload
        self.clear_map()
        
        # Get line info
        line = self.db.get_line_by_id(line_id)
        if not line:
            return
        
        # Get stops for this line
        stops = self.db.get_stops_for_line(line_id)
        
        # Create a set of station IDs for this line
        line_station_ids = {stop['station_id'] for stop in stops}
        
        # Add stations ONLY for this line
        for stop in stops:
            station = self.db.get_station_by_id(stop['station_id'])
            if station:
                marker = folium.Marker(
                    [station['lat'], station['lon']],
                    popup=f"<b>{station['nume']}</b>",
                    tooltip=station['nume'],
                )
                marker.add_to(self.map)
                # Don't add to station_markers to avoid conflict
        
        # Draw only this line
        if stops and len(stops) > 1:
            coordinates = [(s['lat'], s['lon']) for s in stops]
            folium.PolyLine(
                coordinates,
                color='red',
                weight=4,
                opacity=0.8,
                popup=f"Line {line['number']} ({line['direction']})",
                tooltip=f"Line {line['number']}"
            ).add_to(self.map)
        
        # Update UI
        self.show_all_lines_btn.setChecked(False)
        self.update_map_display()
        
        # Show info
        self.route_details.setText(f"Showing Line {line['number']} ({line['direction']})\n"
                                f"Stations: {len(stops)}\n"
                                f"Click 'Show All Lines' to return to full view.")
    
    def show_all_lines(self):
        """Show all lines and stations"""
        self.selected_line_id = None
        self.clear_map()
        # Re-add plugins
        plugins.Fullscreen().add_to(self.map)
        plugins.MousePosition().add_to(self.map)
        
        # Reload all data
        self.load_map_data()
        self.show_all_lines_btn.setChecked(True)
        self.route_details.setText("Showing all bus lines and stations.")
    
    def clear_line_selection(self):
        """Clear the line selection"""
        self.selected_line_id = None
        self.lines_list.clearSelection()
        self.show_all_lines()
    
    def clear_map(self):
        """Clear all map elements"""
        # Remove all children from the map
        self.map = folium.Map(
            location=[44.1598, 28.6348],  # Constanta coords
            zoom_start=13,
            tiles='OpenStreetMap',
            control_scale=True,
            attr='OpenStreetMap contributors'
        )
        
        # Clear references
        self.station_markers = {}
        self.line_layers = {}
        
        # Re-add plugins
        plugins.Fullscreen().add_to(self.map)
        plugins.MousePosition().add_to(self.map)
    
    def update_map_display(self):
        """Update the map display in the web view"""
        map_path = Path("constanta_map.html")
        self.map.save(str(map_path))
        self.web_view.setUrl(QUrl.fromLocalFile(str(map_path.absolute())))
    
    def find_route(self):
        """Find and display route between locations using station names"""
        start_text = self.start_input.text().strip()
        end_text = self.end_input.text().strip()
        
        if not start_text or not end_text:
            QMessageBox.warning(self, "Input Required", "Please enter both start and end locations")
            return
        
        # Show loading message
        self.route_details.setText(f"Finding route from '{start_text}' to '{end_text}'...")
        QApplication.processEvents()
        
        try:
            # Try to find stations by name
            start_station = None
            end_station = None
            
            # First try exact match
            start_station = self.db.find_station_by_name_exact(start_text)
            end_station = self.db.find_station_by_name_exact(end_text)
            
            # If not found, try partial match
            if not start_station:
                start_station = self.db.find_station_by_name(start_text)
            if not end_station:
                end_station = self.db.find_station_by_name(end_text)
            
            if not start_station:
                QMessageBox.warning(self, "Station Not Found", 
                    f"Could not find station: '{start_text}'\n"
                    f"Please enter a valid station name.")
                self.route_details.clear()
                return
                
            if not end_station:
                QMessageBox.warning(self, "Station Not Found", 
                    f"Could not find station: '{end_text}'\n"
                    f"Please enter a valid station name.")
                self.route_details.clear()
                return
            
            # Get coordinates from found stations
            start_coords = [start_station['lat'], start_station['lon']]
            end_coords = [end_station['lat'], end_station['lon']]
            
            # Find route using actual station coordinates
            route = self.db.find_route(
                start_coords[0], start_coords[1],
                end_coords[0], end_coords[1]
            )
            
            if route:
                self.current_route = route
                self.display_route(route)
            else:
                QMessageBox.warning(self, "No Route Found", 
                    f"Could not find a route from '{start_station['nume']}' to '{end_station['nume']}'.\n"
                    f"Try selecting different stations.")
                self.route_details.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to find route: {str(e)}")
            self.route_details.clear()
    
    def display_route(self, route):
        """Display the found route on the map"""
        # Clear the entire map first
        self.clear_map()
        
        # Build route instructions
        route_details_text = f"Route from {route['start_station']['nume']} to {route['end_station']['nume']}\n"
        route_details_text += f"Estimated time: {route['total_time']:.0f} minutes\n"
        
        if route['transfer_count'] > 0:
            route_details_text += f"Transfers: {route['transfer_count']}\n\n"
        else:
            route_details_text += f"Direct route (no transfers)\n\n"
        
        route_details_text += "Route Instructions:\n"
        
        # Track current segment
        current_segment = []
        current_line = None
        
        for i, step in enumerate(route['path']):
            station = self.db.get_station_by_id(step['station_id'])
            if not station:
                continue
                
            # Add station to map
            if i == 0:  # Start
                icon_color = 'green'
                icon_text = 'flag'
                status = "Start"
            elif i == len(route['path']) - 1:  # End
                icon_color = 'red'
                icon_text = 'flag-checkered'
                status = "End"
            else:
                icon_color = 'orange'
                icon_text = 'circle'
                status = "Route Stop"
            
            folium.Marker(
                [station['lat'], station['lon']],
                popup=f"<b>{status}: {station['nume']}</b><br>"
                    f"Line: {step.get('line_number', 'Walk')}",
                tooltip=f"{status}: {station['nume']}",
                icon=folium.Icon(color=icon_color, icon=icon_text, prefix='fa')
            ).add_to(self.map)
            
            # Build instructions
            line_number = step.get('line_number')
            
            if line_number and line_number != 'WALK':
                if line_number != current_line:
                    # New bus line segment
                    if current_line:
                        # Finish previous segment
                        if current_segment:
                            route_details_text += f"  • Get off at: {current_segment[-1]}\n\n"
                    
                    current_line = line_number
                    current_segment = []
                    
                    # Get line direction
                    line_info = self.db.get_line_by_id(step['line_id']) if step['line_id'] else None
                    direction = f"({line_info['direction']})" if line_info else ""
                    
                    route_details_text += f"Take Line {current_line} {direction}:\n"
                
                current_segment.append(station['nume'])
                
            elif line_number == 'WALK' or not line_number:
                # Walking segment
                if current_line:
                    # Finish bus segment first
                    if current_segment:
                        route_details_text += f"  • Get off at: {current_segment[-1]}\n\n"
                    current_line = None
                    current_segment = []
                
                route_details_text += f"Walk to: {station['nume']}\n"
        
        # Add final instruction if we ended on a bus
        if current_line and current_segment:
            route_details_text += f"  • Get off at final destination: {current_segment[-1]}\n"
        
        # Draw route lines on map
        route_coords = []
        for step in route['path']:
            station = self.db.get_station_by_id(step['station_id'])
            if station:
                route_coords.append([station['lat'], station['lon']])
        
        # Also draw the actual bus lines
        drawn_lines = set()
        for step in route['path']:
            if step['line_id'] and step['line_id'] not in drawn_lines:
                line = self.db.get_line_by_id(step['line_id'])
                if line:
                    stops = self.db.get_stops_for_line(step['line_id'])
                    if stops and len(stops) > 1:
                        coordinates = [(s['lat'], s['lon']) for s in stops]
                        folium.PolyLine(
                            coordinates,
                            color='blue',
                            weight=2,
                            opacity=0.5,
                            popup=f"Line {line['number']}",
                            tooltip=f"Bus Line {line['number']}"
                        ).add_to(self.map)
                        drawn_lines.add(step['line_id'])
        
        # Draw the actual route path
        if len(route_coords) > 1:
            folium.PolyLine(
                route_coords,
                color='red',
                weight=4,
                opacity=0.8,
                popup=f"Your Route: {route['total_time']:.0f} min",
                tooltip="Your Route"
            ).add_to(self.map)
        
        # Update display
        self.update_map_display()
        self.route_details.setText(route_details_text)
        
        # Center map on route
        if route_coords:
            avg_lat = sum(coord[0] for coord in route_coords) / len(route_coords)
            avg_lon = sum(coord[1] for coord in route_coords) / len(route_coords)
            self.map.location = [avg_lat, avg_lon]
            self.update_map_display()
    
    def clear_route(self):
        """Clear the current route from the map"""
        self.current_route = None
        self.clear_line_selection()
        self.route_details.clear()
        self.start_input.clear()
        self.end_input.clear()
    
    def toggle_stations(self, state):
        """Toggle station markers visibility - only works in 'all lines' mode"""
        if self.selected_line_id is not None or self.current_route is not None:
            # Don't toggle when in single line or route mode
            QMessageBox.information(self, "Info", 
                "Station visibility toggle is only available in 'Show All Lines' mode.\n"
                "Click 'Show All Lines' first to use this feature.")
            self.show_stations_btn.setChecked(True)
            return
        
        for marker in self.station_markers.values():
            if state == Qt.Checked:
                marker.add_to(self.map)
            else:
                if marker._id in self.map._children:
                    del self.map._children[marker._id]
        
        self.update_map_display()
    
    def toggle_all_lines(self, state):
        """Toggle all lines visibility"""
        for line_data in self.line_layers.values():
            line_data['visible'] = state
            if state:
                line_data['layer'].add_to(self.map)
            else:
                if line_data['layer']._id in self.map._children:
                    del self.map._children[line_data['layer']._id]
        
        self.update_map_display()

class AccountWidget(QWidget):
    """User account management widget"""
    
    current_user_changed = pyqtSignal(dict)


    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Login/Register tabs
        self.tabs = QTabWidget()
        
        # Login tab
        login_widget = QWidget()
        login_layout = QVBoxLayout()
        
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Username")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        
        login_layout.addWidget(QLabel("Username:"))
        login_layout.addWidget(self.login_username)
        login_layout.addWidget(QLabel("Password:"))
        login_layout.addWidget(self.login_password)
        login_layout.addWidget(self.login_btn)
        login_widget.setLayout(login_layout)
        
        # Register tab
        register_widget = QWidget()
        register_layout = QVBoxLayout()
        
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Username")
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Password")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setPlaceholderText("Confirm Password")
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        
        self.register_btn = QPushButton("Create Account")
        self.register_btn.clicked.connect(self.register)
        
        register_layout.addWidget(QLabel("Username:"))
        register_layout.addWidget(self.reg_username)
        register_layout.addWidget(QLabel("Email:"))
        register_layout.addWidget(self.reg_email)
        register_layout.addWidget(QLabel("Password:"))
        register_layout.addWidget(self.reg_password)
        register_layout.addWidget(QLabel("Confirm Password:"))
        register_layout.addWidget(self.reg_confirm)
        register_layout.addWidget(self.register_btn)
        register_widget.setLayout(register_layout)
        
        self.tabs.addTab(login_widget, "Login")
        self.tabs.addTab(register_widget, "Register")
        
        layout.addWidget(self.tabs)
        
        # User info panel
        self.user_panel = QGroupBox("My Account")
        user_layout = QVBoxLayout()
        
        self.user_info = QLabel("Not logged in")
        self.user_info.setAlignment(Qt.AlignCenter)
        
        self.travel_history_btn = QPushButton("Travel History")
        self.travel_history_btn.clicked.connect(self.show_travel_history)
        
        self.buy_ticket_btn = QPushButton("Buy Ticket")
        self.buy_ticket_btn.clicked.connect(self.buy_ticket)
        
        self.buy_subscription_btn = QPushButton("Buy Subscription")
        self.buy_subscription_btn.clicked.connect(self.buy_subscription)
        
        self.edit_account_btn = QPushButton("Edit Account")
        self.edit_account_btn.clicked.connect(self.edit_account)
        
        self.delete_account_btn = QPushButton("Delete Account")
        self.delete_account_btn.clicked.connect(self.delete_account)
        self.delete_account_btn.setStyleSheet("background-color: #ff4444; color: white;")
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout)
        
        user_layout.addWidget(self.user_info)
        user_layout.addWidget(self.travel_history_btn)
        user_layout.addWidget(self.buy_ticket_btn)
        user_layout.addWidget(self.buy_subscription_btn)
        user_layout.addWidget(self.edit_account_btn)
        user_layout.addWidget(self.delete_account_btn)
        user_layout.addWidget(self.logout_btn)
        
        self.user_panel.setLayout(user_layout)
        self.user_panel.setVisible(False)
        
        layout.addWidget(self.user_panel)
        self.setLayout(layout)

    def login(self):
        username = self.login_username.text()
        password = self.login_password.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        
        user = self.db.authenticate_user(username, password)
        if user:
            self.current_user = user
            user_details = self.db.get_user_by_id(user['id'])
            self.show_user_panel(user_details)
            
            # Emit signal with user data
            self.current_user_changed.emit(user)
            
            QMessageBox.information(self, "Success", f"Welcome, {username}!")
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")
    
    def logout(self):
        # Emit signal with None to indicate logout
        self.current_user_changed.emit(None)
        
        self.current_user = None
        self.user_panel.setVisible(False)
        self.tabs.setVisible(True)
        self.clear_fields()

    def register(self):
        username = self.reg_username.text()
        email = self.reg_email.text()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        
        if not all([username, email, password, confirm]):
            QMessageBox.warning(self, "Error", "All fields are required")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords don't match")
            return
        
        try:
            user_id = self.db.create_account(username, email, password)
            QMessageBox.information(self, "Success", f"Account created successfully! ID: {user_id}")
            self.tabs.setCurrentIndex(0)
            self.login_username.setText(username)
            self.login_password.setText(password)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Registration failed: {str(e)}")
    
    def show_user_panel(self, user_details):
        role_display = "Administrator" if user_details['role'] == 'admin' else "User"
        self.user_info.setText(f"Logged in as: {user_details['username']}\nRole: {role_display}")
        self.user_panel.setVisible(True)
        self.tabs.setVisible(False)
    
    def show_travel_history(self):
        if not self.current_user:
            return
        
        travels = self.db.get_user_travels(self.current_user['id'])
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Travel History")
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Date", "Time", "Price"])
        
        table.setRowCount(len(travels))
        for row, travel in enumerate(travels):
            table.setItem(row, 1, QTableWidgetItem(str(travel['date'])))
            table.setItem(row, 2, QTableWidgetItem(str(travel['time'])))
            table.setItem(row, 3, QTableWidgetItem(f"{travel['price']:.2f}"))
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def buy_ticket(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Buy Ticket")
        dialog.setGeometry(300, 300, 300, 200)
        
        layout = QVBoxLayout()
        
        ticket_type_combo = QComboBox()
        ticket_type_combo.addItems(["3h", "24h", "72h", "7d"])
        
        price_label = QLabel("Price: 5.00 RON")
        
        buy_btn = QPushButton("Purchase")
        
        def update_price():
            prices = {"3h": 5.00, "24h": 15.00, "72h": 30.00, "7d": 50.00}
            selected = ticket_type_combo.currentText()
            price_label.setText(f"Price: {prices[selected]:.2f} RON")
        
        ticket_type_combo.currentIndexChanged.connect(update_price)
        
        def purchase():
            # Map ticket types to their IDs
            ticket_type_map = {"3h": 1, "24h": 2, "72h": 3, "7d": 4}
            selected_type = ticket_type_combo.currentText()
            ticket_type = ticket_type_map[selected_type]
            
            # Get the price based on ticket type
            prices = {"3h": 5.00, "24h": 15.00, "72h": 30.00, "7d": 50.00}
            price = prices[selected_type]
            
            ticket_id = 999  
            
            # Record travel
            travel_id = self.db.create_travel(
                self.current_user['id'],
                price,
                datetime.now().date(),
                datetime.now().time()
            )
            
            QMessageBox.information(dialog, "Success", 
                f"Ticket purchased successfully!\n"
                f"Ticket Type: {selected_type}\n"
                f"Price: {price:.2f} RON\n")
            dialog.close()
                
        buy_btn.clicked.connect(purchase)
        
        layout.addWidget(QLabel("Select Ticket Type:"))
        layout.addWidget(ticket_type_combo)
        layout.addWidget(price_label)
        layout.addWidget(buy_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def buy_subscription(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Buy Subscription")
        dialog.setGeometry(300, 300, 450, 350)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        first_name_input = QLineEdit()
        last_name_input = QLineEdit()
        cnp_input = QLineEdit()
        
        # Subscription type selection
        sub_type_group = QButtonGroup()
        general_radio = QRadioButton("General Subscription (80 RON/month - all lines)")
        specific_radio = QRadioButton("Line-specific Subscription (20 RON/month)")
        general_radio.setChecked(True)
        
        sub_type_group.addButton(general_radio)
        sub_type_group.addButton(specific_radio)
        
        # Line selection 
        line_combo = QComboBox()
        lines = self.db.get_all_lines()
        line_combo.addItem("Select a line", -1)
        for line in lines:
            line_combo.addItem(f"Line {line['number']} ({line['direction']})", line['id'])
        line_combo.setEnabled(False)
        
        # Price display
        price_label = QLabel("Price: 80 RON/month")
        price_label.setStyleSheet("font-weight: bold; color: green;")
        
        # Enable/disable line selection based on radio button
        def update_subscription_type():
            if specific_radio.isChecked():
                line_combo.setEnabled(True)
                price_label.setText("Price: 20 RON/month")
                price_label.setStyleSheet("font-weight: bold; color: blue;")
            else:
                line_combo.setEnabled(False)
                price_label.setText("Price: 80 RON/month")
                price_label.setStyleSheet("font-weight: bold; color: green;")
        
        general_radio.toggled.connect(update_subscription_type)
        specific_radio.toggled.connect(update_subscription_type)
        
        form_layout.addRow("Subscription Type:", general_radio)
        form_layout.addRow("", specific_radio)
        form_layout.addRow("First Name:", first_name_input)
        form_layout.addRow("Last Name:", last_name_input)
        form_layout.addRow("CNP:", cnp_input)
        form_layout.addRow("Line (if specific):", line_combo)
        form_layout.addRow("", price_label)
        
        buy_btn = QPushButton("Purchase Subscription")
    
        def purchase():
            if not all([first_name_input.text(), last_name_input.text(), cnp_input.text()]):
                QMessageBox.warning(dialog, "Error", "All fields are required")
                return
            
            if len(cnp_input.text()) != 13:
                QMessageBox.warning(dialog, "Error", "CNP must be 13 characters")
                return
            
            if specific_radio.isChecked():
                line_id = line_combo.currentData()
                if line_id == -1:
                    QMessageBox.warning(dialog, "Error", "Please select a line for line-specific subscription")
                    return
                price = 20.00
            else:
                line_id = None
                price = 80.00
            
            try:
                subscription_id = self.db.create_subscription(
                    last_name_input.text(),
                    first_name_input.text(),
                    cnp_input.text(),
                    line_id
                )
                
                if subscription_id is None:
                    raise Exception("Failed to create subscription")
                
                travel_id = self.db.create_travel(
                    self.current_user['id'],
                    price,
                    datetime.now().date(),
                    datetime.now().time()
                )
                
                sub_type = "General" if line_id is None else f"Line-specific (Line {line_combo.currentText().split()[1]})"
                
                QMessageBox.information(dialog, "Success", 
                    f"Subscription purchased successfully!\n\n"
                    f"Subscription ID: {subscription_id}\n"
                    f"Type: {sub_type}\n"
                    f"Price: {price:.2f} RON/month\n"
                    f"Valid for: 30 days\n"
                    f"Purchase recorded as Travel ID: {travel_id}")
                dialog.close()
                
            except Exception as e:
                QMessageBox.critical(dialog, "Error", 
                    f"Failed to purchase subscription: {str(e)}\n"
                    f"Please check database connection and schema.")
        
        buy_btn.clicked.connect(purchase)
        
        layout.addLayout(form_layout)
        layout.addWidget(buy_btn)
        
        dialog.setLayout(layout)        
        dialog.exec_()
    
    def edit_account(self):
        if not self.current_user:
            return
        
        user_details = self.db.get_user_by_id(self.current_user['id'])
        if not user_details:
            QMessageBox.warning(self, "Error", "Could not retrieve user details")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Account")
        dialog.setGeometry(300, 300, 300, 250)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        username_input = QLineEdit(user_details['username'])
        email_input = QLineEdit(user_details['email'])
        password_input = QLineEdit()
        password_input.setPlaceholderText("Leave empty to keep current")
        password_input.setEchoMode(QLineEdit.Password)
        confirm_input = QLineEdit()
        confirm_input.setPlaceholderText("Confirm new password")
        confirm_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", username_input)
        form_layout.addRow("Email:", email_input)
        form_layout.addRow("New Password:", password_input)
        form_layout.addRow("Confirm Password:", confirm_input)
        
        save_btn = QPushButton("Save Changes")
        
        def save_changes():
            if password_input.text() and password_input.text() != confirm_input.text():
                QMessageBox.warning(dialog, "Error", "Passwords don't match")
                return
            
            updates = {}
            if username_input.text() != user_details['username']:
                updates['username'] = username_input.text()
            if email_input.text() != user_details['email']:
                updates['email'] = email_input.text()
            if password_input.text():
                updates['password'] = password_input.text()
            
            if updates:
                self.db.update_account(self.current_user['id'], **updates)
                QMessageBox.information(dialog, "Success", "Account updated successfully!")
                dialog.close()
                updated_details = self.db.get_user_by_id(self.current_user['id'])
                self.show_user_panel(updated_details)
            else:
                QMessageBox.information(dialog, "No Changes", "No changes were made")
                dialog.close()
        
        save_btn.clicked.connect(save_changes)
        
        layout.addLayout(form_layout)
        layout.addWidget(save_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def delete_account(self):
        if not self.current_user:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete your account? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_account(self.current_user['id'])
            self.current_user = None
            self.user_panel.setVisible(False)
            self.tabs.setVisible(True)
            self.clear_fields()
            QMessageBox.information(self, "Account Deleted", "Your account has been deleted successfully.")
    
    def clear_fields(self):
        self.login_username.clear()
        self.login_password.clear()
        self.reg_username.clear()
        self.reg_email.clear()
        self.reg_password.clear()
        self.reg_confirm.clear()


class ScheduleWidget(QWidget):
    """Schedule viewing widget"""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Line selection
        line_layout = QHBoxLayout()
        line_layout.addWidget(QLabel("Select Line:"))
        
        self.line_combo = QComboBox()
        self.load_lines()
        self.line_combo.currentIndexChanged.connect(self.load_line_schedule)
        
        line_layout.addWidget(self.line_combo)
        line_layout.addStretch()
        
        # Schedule table
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(3) 
        self.schedule_table.setHorizontalHeaderLabels(["Station", "Next Arrivals", "Schedule"]) 
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.schedule_table.itemDoubleClicked.connect(self.show_full_schedule)
        
        layout.addLayout(line_layout)
        layout.addWidget(self.schedule_table)
        self.setLayout(layout)
        
        # Load initial data if lines exist
        if self.line_combo.count() > 0:
            QTimer.singleShot(100, self.load_line_schedule)
            
        self.schedule_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 1px 12px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    
    def show_full_schedule(self, item=None):
        """Show full schedule for a station when clicked"""
        if isinstance(item, QTableWidgetItem):
            row = item.row()
        else:
            # Handle button click
            return
        
        line_id = self.line_combo.currentData()
        if not line_id:
            return
        
        # Get station from the clicked row
        station_name_item = self.schedule_table.item(row, 0)
        if not station_name_item:
            return
        
        station_name = station_name_item.text()
        
        # Find station by name
        stations = self.db.get_all_stations()
        station_id = None
        for station in stations:
            if station['nume'] == station_name:
                station_id = station['id']
                break
        
        if not station_id:
            QMessageBox.warning(self, "Error", f"Could not find station: {station_name}")
            return
        
        self.show_full_schedule_for_station(station_id, line_id, station_name)

    def show_full_schedule_for_station(self, station_id, line_id, station_name):
        """Show dialog with full schedule for a specific station"""
        # Get line info
        line = self.db.get_line_by_id(line_id)
        if not line:
            return
        
        # Get full schedule
        schedule_times = self.db.get_schedule_for_line_station(line_id, station_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Full Schedule - {station_name}")
        dialog.setGeometry(300, 300, 400, 500)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<h3>Line {line['number']} ({line['direction']})</h3>"
                    f"<b>Station:</b> {station_name}<br><br>"
                    f"<b>Full Schedule:</b>")
        header.setTextFormat(Qt.RichText)
        layout.addWidget(header)
        
        # Schedule list
        schedule_text = QTextEdit()
        schedule_text.setReadOnly(True)
        schedule_text.setLineWrapMode(QTextEdit.NoWrap)
        
        if schedule_times:
            # Group times by hour for better readability
            times_by_hour = {}
            for t in schedule_times:
                if isinstance(t, str):
                    try:
                        t_time = datetime.strptime(t, '%H:%M:%S').time()
                        hour = t_time.hour
                    except ValueError:
                        continue
                else:
                    t_time = t
                    hour = t_time.hour
                
                if hour not in times_by_hour:
                    times_by_hour[hour] = []
                
                # Format time
                if isinstance(t, str):
                    display_time = t[:5]  # HH:MM
                else:
                    display_time = t.strftime('%H:%M')
                
                times_by_hour[hour].append(display_time)
            
            # Build display text
            text = ""
            for hour in sorted(times_by_hour.keys()):
                text += f"<b>{hour:02d}:00 - {hour:02d}:59</b><br>"
                times = sorted(times_by_hour[hour])
                
                # Group times in columns for better readability
                cols = 4
                for i in range(0, len(times), cols):
                    row_times = times[i:i+cols]
                    text += "&nbsp;&nbsp;" + " &nbsp; ".join(row_times) + "<br>"
                text += "<br>"
            
            schedule_text.setHtml(text)
        else:
            schedule_text.setPlainText("No schedule available for this station.")
        
        layout.addWidget(schedule_text)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def load_lines(self):
        """Load all lines from database"""
        lines = self.db.get_all_lines()
        self.line_combo.clear()
        for line in lines:
            self.line_combo.addItem(f"Line {line['number']} ({line['direction']})", line['id'])
    
    def load_line_schedule(self):
        """Load schedule for selected line - show only next 3 arrivals"""
        if self.line_combo.currentIndex() < 0:
            return
        
        line_id = self.line_combo.currentData()
        if not line_id:
            return
        
        # Get stops for this line
        stops = self.db.get_stops_for_line(line_id)
        
        self.schedule_table.setRowCount(len(stops))
        
        now = datetime.now()
        
        for row, stop in enumerate(stops):
            station_id = stop['station_id']
            station = self.db.get_station_by_id(station_id)
            
            if not station:
                continue
                
            # Station name
            self.schedule_table.setItem(row, 0, QTableWidgetItem(station['nume']))
            
            # Get schedule times
            schedule_times = self.db.get_schedule_for_line_station(line_id, station_id)
            
            if schedule_times:
                # Filter for future arrivals
                future_times = []
                for t in schedule_times:
                    if isinstance(t, str):
                        try:
                            t_time = datetime.strptime(t, '%H:%M:%S').time()
                        except ValueError:
                            continue
                    else:
                        t_time = t
                    
                    arrival_datetime = datetime.combine(now.date(), t_time)
                    if arrival_datetime > now:
                        future_times.append((arrival_datetime, t))
                
                # Sort by time and take next 3
                future_times.sort(key=lambda x: x[0])
                next_arrivals = future_times[:3]
                
                # Format next arrivals
                if next_arrivals:
                    arrivals_text = ""
                    for arrival_datetime, t in next_arrivals:
                        time_until = arrival_datetime - now
                        minutes = int(time_until.total_seconds() / 60)
                        
                        # Format time display
                        if isinstance(t, str):
                            display_time = t[:5]  # Show only HH:MM
                        else:
                            display_time = t.strftime('%H:%M')
                        
                        arrivals_text += f"{display_time} (in {minutes} min)\n"
                    
                    arrivals_text = arrivals_text.strip()  # Remove trailing newline
                    arrivals_item = QTableWidgetItem(arrivals_text)
                    
                    # Color code based on time to next arrival
                    if next_arrivals:
                        minutes_to_first = int((next_arrivals[0][0] - now).total_seconds() / 60)
                        if minutes_to_first < 5:
                            arrivals_item.setForeground(QColor(0, 128, 0))  # Green
                        elif minutes_to_first < 15:
                            arrivals_item.setForeground(QColor(255, 165, 0))  # Orange
                        else:
                            arrivals_item.setForeground(QColor(0, 0, 255))  # Blue
                    
                    self.schedule_table.setItem(row, 1, arrivals_item)
                else:
                    self.schedule_table.setItem(row, 1, QTableWidgetItem("No more today"))
            else:
                self.schedule_table.setItem(row, 1, QTableWidgetItem("No schedule"))
            
            # Create a closure to capture current values
            def create_button_handler(st_id, st_name, ln_id):
                def handler():
                    self.show_full_schedule_for_station(st_id, ln_id, st_name)
                return handler
            
            # Create button with proper closure
            schedule_btn = QPushButton("View Full Schedule")
            schedule_btn.clicked.connect(create_button_handler(station_id, station['nume'], line_id))
            
            # Create a widget to hold the button
            btn_widget = QWidget()
            btn_layout = QHBoxLayout()
            btn_layout.addWidget(schedule_btn)
            btn_layout.setAlignment(Qt.AlignCenter)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_widget.setLayout(btn_layout)
            
            self.schedule_table.setCellWidget(row, 2, btn_widget)
        
        self.schedule_table.resizeColumnsToContents()

class AdminWidget(QWidget):
    """Administrator panel for managing transit data"""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        tabs = QTabWidget()
        
        # Stations tab
        stations_tab = self.create_stations_tab()
        tabs.addTab(stations_tab, "Stations")
        
        # Lines tab
        lines_tab = self.create_lines_tab()
        tabs.addTab(lines_tab, "Lines")
        
        # Schedules tab
        schedules_tab = self.create_schedules_tab()
        tabs.addTab(schedules_tab, "Schedules")
        
        # Subscriptions tab
        subscriptions_tab = self.create_subscriptions_tab()
        tabs.addTab(subscriptions_tab, "Subscriptions")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    def create_stations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Table
        self.stations_table = QTableWidget()
        self.stations_table.setColumnCount(5)
        self.stations_table.setHorizontalHeaderLabels(["ID", "Name", "Latitude", "Longitude", "OSM ID"])
        self.stations_table.horizontalHeader().setStretchLastSection(True)
        self.stations_table.itemDoubleClicked.connect(self.edit_station)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Station")
        add_btn.clicked.connect(self.add_station)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_stations)
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_stations)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        
        layout.addWidget(self.stations_table)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        self.refresh_stations()
        return widget
    
    def create_lines_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Table
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(4)
        self.lines_table.setHorizontalHeaderLabels(["ID", "Number", "Direction", "Stops Count"])
        self.lines_table.horizontalHeader().setStretchLastSection(True)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Line")
        add_btn.clicked.connect(self.add_line)
        edit_btn = QPushButton("Edit Line")
        edit_btn.clicked.connect(self.edit_line)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_lines)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        
        layout.addWidget(self.lines_table)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        self.refresh_lines()
        return widget
    
    def create_schedules_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Line:"))
        
        self.schedule_line_combo = QComboBox()
        self.load_lines_combo()
        
        selection_layout.addWidget(self.schedule_line_combo)
        selection_layout.addWidget(QLabel("Station:"))
        
        self.schedule_station_combo = QComboBox()
        self.load_stations_combo()
        
        selection_layout.addWidget(self.schedule_station_combo)
        selection_layout.addStretch()
        
        # Schedule editor
        self.schedule_editor = QTextEdit()
        self.schedule_editor.setPlaceholderText("Enter times in HH:MM:SS format, one per line")
        
        # Buttons
        btn_layout = QHBoxLayout()
        load_btn = QPushButton("Load Schedule")
        load_btn.clicked.connect(self.load_schedule)
        save_btn = QPushButton("Save Schedule")
        save_btn.clicked.connect(self.save_schedule)
        
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        
        layout.addLayout(selection_layout)
        layout.addWidget(QLabel("Schedule Times:"))
        layout.addWidget(self.schedule_editor)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_subscriptions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Table
        self.subscriptions_table = QTableWidget()
        self.subscriptions_table.setColumnCount(6)
        self.subscriptions_table.setHorizontalHeaderLabels(["ID", "Last Name", "First Name", "CNP", "Line ID", "Line Number"])
        self.subscriptions_table.horizontalHeader().setStretchLastSection(True)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_subscriptions)
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_subscriptions)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        
        layout.addWidget(self.subscriptions_table)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        self.refresh_subscriptions()
        return widget
    
    # Station methods
    def refresh_stations(self):
        stations = self.db.get_all_stations()
        self.stations_table.setRowCount(len(stations))
        
        for row, station in enumerate(stations):
            self.stations_table.setItem(row, 0, QTableWidgetItem(str(station['id'])))
            self.stations_table.setItem(row, 1, QTableWidgetItem(station['nume']))
            self.stations_table.setItem(row, 2, QTableWidgetItem(str(station['lat'])))
            self.stations_table.setItem(row, 3, QTableWidgetItem(str(station['lon'])))
            self.stations_table.setItem(row, 4, QTableWidgetItem(str(station.get('osm_id', ''))))
        
        self.stations_table.resizeColumnsToContents()
    
    def add_station(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Station")
        dialog.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        name_input = QLineEdit()
        lat_input = QLineEdit()
        lon_input = QLineEdit()
        osm_input = QLineEdit()
        
        form.addRow("Station Name:", name_input)
        form.addRow("Latitude:", lat_input)
        form.addRow("Longitude:", lon_input)
        form.addRow("OSM ID (optional):", osm_input)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        def accept():
            try:
                station_id = self.db.add_station(
                    name_input.text(),
                    float(lat_input.text()),
                    float(lon_input.text()),
                    int(osm_input.text()) if osm_input.text() else None
                )
                QMessageBox.information(dialog, "Success", f"Station added with ID: {station_id}")
                self.refresh_stations()
                self.load_stations_combo()
                dialog.accept()
            except ValueError as e:
                QMessageBox.warning(dialog, "Error", f"Invalid input: {str(e)}")
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"Failed to add station: {str(e)}")
        
        btn_box.accepted.connect(accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def edit_station(self, item):
        row = item.row()
        station_id = int(self.stations_table.item(row, 0).text())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Station")
        dialog.setGeometry(300, 300, 400, 300)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        name_input = QLineEdit(self.stations_table.item(row, 1).text())
        lat_input = QLineEdit(self.stations_table.item(row, 2).text())
        lon_input = QLineEdit(self.stations_table.item(row, 3).text())
        osm_input = QLineEdit(self.stations_table.item(row, 4).text())
        
        form.addRow("Station Name:", name_input)
        form.addRow("Latitude:", lat_input)
        form.addRow("Longitude:", lon_input)
        form.addRow("OSM ID:", osm_input)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        def save():
            try:
                self.db.update_station(
                    station_id,
                    name=name_input.text(),
                    lat=float(lat_input.text()) if lat_input.text() else None,
                    lon=float(lon_input.text()) if lon_input.text() else None
                )
                QMessageBox.information(dialog, "Success", "Station updated")
                self.refresh_stations()
                self.load_stations_combo()
                dialog.accept()
            except ValueError as e:
                QMessageBox.warning(dialog, "Error", f"Invalid input: {str(e)}")
        
        btn_box.accepted.connect(save)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def export_stations(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Stations", "", "CSV Files (*.csv)"
        )
        
        if filename:
            stations = self.db.get_all_stations()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Latitude', 'Longitude', 'OSM ID'])
                for station in stations:
                    writer.writerow([
                        station['id'],
                        station['nume'],
                        station['lat'],
                        station['lon'],
                        station.get('osm_id', '')
                    ])
            QMessageBox.information(self, "Export Complete", f"Stations exported to {filename}")
    
    # Line methods
    def refresh_lines(self):
        lines = self.db.get_all_lines()
        self.lines_table.setRowCount(len(lines))
        
        for row, line in enumerate(lines):
            self.lines_table.setItem(row, 0, QTableWidgetItem(str(line['id'])))
            self.lines_table.setItem(row, 1, QTableWidgetItem(line['number']))
            self.lines_table.setItem(row, 2, QTableWidgetItem(line['direction']))
            
            # Count stops for this line
            stops = self.db.get_stops_for_line(line['id'])
            self.lines_table.setItem(row, 3, QTableWidgetItem(str(len(stops))))
        
        self.lines_table.resizeColumnsToContents()
    
    def add_line(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Line")
        dialog.setGeometry(300, 300, 300, 200)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        number_input = QLineEdit()
        direction_combo = QComboBox()
        direction_combo.addItems(["forward", "backward"])
        
        form.addRow("Line Number:", number_input)
        form.addRow("Direction:", direction_combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        def accept():
            try:
                line_id = self.db.add_line(
                    number_input.text(),
                    direction_combo.currentText()
                )
                QMessageBox.information(dialog, "Success", f"Line added with ID: {line_id}")
                self.refresh_lines()
                self.load_lines_combo()  # Refresh combo in schedules tab
                dialog.accept()
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"Failed to add line: {str(e)}")
        
        btn_box.accepted.connect(accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def edit_line(self):
        current_row = self.lines_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a line to edit")
            return
        
        line_id = int(self.lines_table.item(current_row, 0).text())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Line")
        dialog.setGeometry(300, 300, 300, 200)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        number_input = QLineEdit(self.lines_table.item(current_row, 1).text())
        direction_combo = QComboBox()
        direction_combo.addItems(["forward", "backward"])
        direction_combo.setCurrentText(self.lines_table.item(current_row, 2).text())
        
        form.addRow("Line Number:", number_input)
        form.addRow("Direction:", direction_combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        def save():
            try:
                self.db.update_line(
                    line_id,
                    number=number_input.text(),
                    direction=direction_combo.currentText()
                )
                QMessageBox.information(dialog, "Success", "Line updated")
                self.refresh_lines()
                self.load_lines_combo()
                dialog.accept()
            except Exception as e:
                QMessageBox.warning(dialog, "Error", f"Failed to update line: {str(e)}")
        
        btn_box.accepted.connect(save)
        btn_box.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    # Schedule methods
    def load_lines_combo(self):
        self.schedule_line_combo.clear()
        lines = self.db.get_all_lines()
        for line in lines:
            self.schedule_line_combo.addItem(f"Line {line['number']} ({line['direction']})", line['id'])
    
    def load_stations_combo(self):
        self.schedule_station_combo.clear()
        stations = self.db.get_all_stations()
        for station in stations:
            self.schedule_station_combo.addItem(station['nume'], station['id'])
    
    def load_schedule(self):
        line_id = self.schedule_line_combo.currentData()
        station_id = self.schedule_station_combo.currentData()
        
        if not line_id or not station_id:
            QMessageBox.warning(self, "Selection Required", "Please select both line and station")
            return
        
        schedule_times = self.db.get_schedule_for_line_station(line_id, station_id)
        
        if schedule_times:
            times_text = "\n".join([str(t) for t in schedule_times])
            self.schedule_editor.setText(times_text)
        else:
            self.schedule_editor.clear()
    
    def save_schedule(self):
        line_id = self.schedule_line_combo.currentData()
        station_id = self.schedule_station_combo.currentData()
        
        if not line_id or not station_id:
            QMessageBox.warning(self, "Selection Required", "Please select both line and station")
            return
        
        times_text = self.schedule_editor.toPlainText().strip()
        if not times_text:
            QMessageBox.warning(self, "No Schedule", "Please enter schedule times")
            return
        
        # Parse times
        times = []
        for line in times_text.split('\n'):
            line = line.strip()
            if line:
                try:
                    # Validate time format
                    datetime.strptime(line, '%H:%M:%S')
                    times.append(line)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Time", f"Invalid time format: {line}\nUse HH:MM:SS format")
                    return
        
        try:
            # Check if schedule exists
            existing = self.db.get_schedule_for_line_station(line_id, station_id)
            if existing:
                self.db.update_schedule(line_id, station_id, times)
                QMessageBox.information(self, "Success", "Schedule updated")
            else:
                self.db.add_schedule(line_id, station_id, times)
                QMessageBox.information(self, "Success", "Schedule added")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save schedule: {str(e)}")
    
    # Subscription methods
    def refresh_subscriptions(self):
        subscriptions = self.db.get_subscriptions()
        self.subscriptions_table.setRowCount(len(subscriptions))
        
        for row, sub in enumerate(subscriptions):
            self.subscriptions_table.setItem(row, 0, QTableWidgetItem(str(sub['id'])))
            self.subscriptions_table.setItem(row, 1, QTableWidgetItem(sub['last_name']))
            self.subscriptions_table.setItem(row, 2, QTableWidgetItem(sub['first_name']))
            self.subscriptions_table.setItem(row, 3, QTableWidgetItem(sub['cnp']))
            self.subscriptions_table.setItem(row, 4, QTableWidgetItem(str(sub['id_l'])))
            self.subscriptions_table.setItem(row, 5, QTableWidgetItem(sub.get('line_number', '')))
        
        self.subscriptions_table.resizeColumnsToContents()
    
    def export_subscriptions(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Subscriptions", "", "CSV Files (*.csv)"
        )
        
        if filename:
            subscriptions = self.db.get_subscriptions()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Last Name', 'First Name', 'CNP', 'Line ID', 'Line Number'])
                for sub in subscriptions:
                    writer.writerow([
                        sub['id'],
                        sub['last_name'],
                        sub['first_name'],
                        sub['cnp'],
                        sub['id_l'],
                        sub.get('line_number', '')
                    ])
            QMessageBox.information(self, "Export Complete", f"Subscriptions exported to {filename}")

class MainWindow(QMainWindow):
    """Main application window UI"""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Constanta Public Transport System")
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Map & Navigation tab with burger menu
        self.map_widget = MapWidget(self.db)
        self.tab_widget.addTab(self.map_widget, "Map & Navigation")
        
        # Schedules tab
        self.schedule_widget = ScheduleWidget(self.db)
        self.tab_widget.addTab(self.schedule_widget, "Schedules")
        
        # Account & Tickets tab
        self.account_widget = AccountWidget(self.db)
        self.tab_widget.addTab(self.account_widget, "Account & Tickets")
        
        # Connect account widget to main window
        self.account_widget.current_user_changed.connect(self.on_user_changed)
        
        # Admin panel
        self.admin_widget = AdminWidget(self.db)
        
        main_layout.addWidget(self.tab_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_label = QLabel("Ready - Use burger menu to select specific bus lines")
        self.statusBar().addWidget(self.status_label)
        
        # Apply stylesheet
        self.apply_stylesheet()

        # Connect the signal
        self.account_widget.current_user_changed.connect(self.on_user_changed)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        refresh_action = QAction('Refresh Data', self)
        refresh_action.triggered.connect(self.refresh_all)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        admin_action = QAction('Admin Panel', self)
        admin_action.triggered.connect(self.toggle_admin_panel)
        view_menu.addAction(admin_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        import_action = QAction('Import Data', self)
        import_action.triggered.connect(self.import_data)
        tools_menu.addAction(import_action)
        
        export_action = QAction('Export Data', self)
        export_action.triggered.connect(self.export_data)
        tools_menu.addAction(export_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def on_user_changed(self, user_data):
        """Handle user change from AccountWidget signal"""
        if user_data is None:
            self.on_user_logout()
        else:
            self.on_user_login(user_data)

    def refresh_all(self):
        """Refresh all data in the application"""
        self.map_widget.load_map_data()
        self.map_widget.load_lines_list()
        self.schedule_widget.load_lines()
        if hasattr(self, 'admin_widget'):
            self.admin_widget.refresh_stations()
            self.admin_widget.refresh_lines()
            self.admin_widget.refresh_subscriptions()
        
        self.status_label.setText("Data refreshed")
        QMessageBox.information(self, "Refresh Complete", "All data has been refreshed")
    
    def on_user_login(self, user_data):
        """Handle user login event from AccountWidget"""
        self.current_user = user_data
        user_details = self.db.get_user_by_id(user_data['id'])
        
        # Update status bar with user info
        role_display = "Administrator" if user_details['role'] == 'admin' else "User"
        self.status_label.setText(f"Logged in as: {user_details['username']} ({role_display})")
        
        # Enable admin features if user is admin
        if user_details['role'] == 'admin':
            # Find and enable admin action in menu
            for action in self.menuBar().actions():
                if action.text() == 'View':
                    for subaction in action.menu().actions():
                        if subaction.text() == 'Admin Panel':
                            subaction.setEnabled(True)
                            break
                    break

    def toggle_admin_panel(self):
        """Show or hide admin panel tab"""
        # Check if user is logged in and is admin
        if not self.current_user:
            QMessageBox.warning(self, "Login Required", 
                "Please log in first to access admin features.")
            # Switch to account tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "👤 Account & Tickets":
                    self.tab_widget.setCurrentIndex(i)
                    break
            return
        
        # Get user details to check role
        user_details = self.db.get_user_by_id(self.current_user['id'])
        if not user_details or user_details.get('role') != 'admin':
            QMessageBox.warning(self, "Access Denied", 
                "Administrator access required.\n"
                "Current user role: " + (user_details.get('role', 'unknown') if user_details else 'not found'))
            return
        
        # Check if admin tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Admin Panel":
                self.tab_widget.removeTab(i)
                self.status_label.setText("Admin panel closed")
                return
        
        # Add admin tab
        self.tab_widget.addTab(self.admin_widget, "Admin Panel")
        self.tab_widget.setCurrentWidget(self.admin_widget)
        self.status_label.setText("Admin panel opened - Administrator mode")
    
    def on_user_logout(self):
        """Handle user logout event"""
        self.current_user = None
        self.status_label.setText("Ready - Use burger menu to select specific bus lines")
        
        # Disable admin features
        for action in self.menuBar().actions():
            if action.text() == 'View':
                for subaction in action.menu().actions():
                    if subaction.text() == 'Admin Panel':
                        subaction.setEnabled(False)
                        break
                break

    def import_data(self):
        """Import data from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if filename:
            QMessageBox.information(self, "Import", f"Import from {filename} would be implemented here")
    
    def export_data(self):
        """Export data to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if filename:
            QMessageBox.information(self, "Export", f"Export to {filename} would be implemented here")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Constanta Public Transport",
            "Constanta Public Transport System v2.0\n\n"
            "A comprehensive desktop application for managing and navigating\n"
            "public transportation in Constanta, Romania.\n\n"
            "New Features:\n"
            "• Burger menu for bus line selection\n"
            "• Route planning that minimizes transfers\n"
            "• Simplified route display showing only necessary stations\n"
            "• Interactive map with OpenStreetMap integration\n\n"
            "Database: PostgreSQL\n"
            "Map: OpenStreetMap\n"
            "UI: PyQt5\n\n"
            "© 2024 Constanta Transport Authority"
        )
    
    def apply_stylesheet(self):
        """Apply stylesheet to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #d0d0d0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton[style*="background-color: #ff4444"] {
                background-color: #ff4444;
            }
            QPushButton[style*="background-color: #ff4444"]:hover {
                background-color: #ff3333;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
            QTableWidget {
                gridline-color: #dddddd;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #dddddd;
                font-weight: bold;
            }
            QGroupBox {
                border: 2px solid #4CAF50;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #333333;
            }
            QStatusBar {
                background-color: #e0e0e0;
                color: #666666;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            /* Side panel styling */
            QWidget#side_panel {
                background-color: #f8f9fa;
                border-right: 2px solid #dee2e6;
            }
        """)

def main():
    app = QApplication(sys.argv)
    
    # Set application icon and style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
