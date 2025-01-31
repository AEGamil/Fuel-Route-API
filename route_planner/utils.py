# route_planner/utils.py
import requests
import pandas as pd
import math
import os
from typing import List, Dict, Tuple

class RoutePlanner:
    def __init__(self):
        # self.OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY")
        self.BASE_URL = 'https://api.openrouteservice.org/v2/directions/driving-car'
        self.fuel_stations = self.load_fuel_stations()

    def load_fuel_stations(self) -> pd.DataFrame:
        # Load and process the CSV file
        df = pd.read_csv('route_planner/checkpoint(4).csv')
        return df

    def calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in miles
        """
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        R = 3959.87433  # Earth's radius in miles

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

    # def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict:
    #     """
    #     Get route using OpenRouteService API
    #     Coordinates should be in [longitude, latitude] format
    #     """
    #     headers = {
    #         'Authorization': self.OPENROUTE_API_KEY,
    #         'Content-Type': 'application/json; charset=utf-8'
    #     }
        
    #     body = {
    #         "coordinates": [
    #             list(start_coords),
    #             list(end_coords)
    #         ]
    #     }
        
    #     response = requests.post(self.BASE_URL, json=body, headers=headers)
    #     return response.json()


    def get_route(self, start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Dict:
        """
        Get route using OSRM API
        Coordinates should be in [longitude, latitude] format
        """
        # OSRM public server base URL
        base_url = "http://router.project-osrm.org"

        # Profile can be 'driving', 'walking', or 'cycling'
        profile = 'driving'

        # Construct the coordinates string
        start_lon, start_lat = start_coords
        end_lon, end_lat = end_coords
        coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"

        # Build the full URL for the route request
        url = f"{base_url}/route/v1/{profile}/{coords}"

        # Set query parameters to mimic OpenRouteService as closely as possible
        params = {
            'overview': 'full', 
            'geometries': 'geojson',  
            'steps': 'true',     
            'annotations': 'true',
            'alternatives': 'false'
        }

        # Make the GET request to the OSRM API
        response = requests.get(url, params=params)

        # Parse the JSON response
        data = response.json()

        # Map OSRM's response structure to match OpenRouteService's output
        if 'routes' in data:
            routes = []
            for route in data['routes']:
                # Each route has 'legs', which correspond to 'segments' in OpenRouteService
                segments = []
                for leg in route['legs']:
                    # Each leg contains 'steps'
                    steps = []
                    for step in leg.get('steps', []):
                        step_info = {
                            'distance': step.get('distance'),
                            'duration': step.get('duration'),
                            'instruction': step.get('maneuver', {}).get('instruction'),
                            'name': step.get('name'),
                            'type': step.get('maneuver', {}).get('type'),
                            'modifier': step.get('maneuver', {}).get('modifier'),
                            'geometry': step.get('geometry')
                        }
                        steps.append(step_info)
                    segment = {
                        'distance': leg.get('distance'),
                        'duration': leg.get('duration'),
                        'steps': steps
                    }
                    segments.append(segment)
                mapped_route = {
                    'summary': {
                        'distance': route.get('distance'),
                        'duration': route.get('duration')
                    },
                    'geometry': route.get('geometry'),   # GeoJSON format
                    'segments': segments
                }
                routes.append(mapped_route)

            result = {
                'routes': routes,
                'waypoints': data.get('waypoints'),
                'code': data.get('code')
            }
        else:
            result = {
                'error': data.get('message', 'An error occurred while fetching the route.'),
                'code': data.get('code', 'Error')
            }
        return result

    def find_nearby_stations(self, position: Tuple[float, float], max_range: float = 50) -> List[Dict]:
        """Find fuel stations within range (miles) of current position"""
        nearby = []
        current_lat, current_lon = position
        
        for _, station in self.fuel_stations.iterrows():
            distance = self.calculate_distance(
                (current_lat, current_lon),
                (station['Latitude'], station['Longitude'])
            )
            if distance <= max_range:
                nearby.append({
                    'name': station['Truckstop Name'],
                    'latitude': station['Latitude'],
                    'longitude': station['Longitude'],
                    'price': station['Retail Price'],
                    'distance': distance
                })
        return nearby

    def find_optimal_fuel_stops(self, route: Dict) -> List[Dict]:
        coordinates = route['routes'][0]['geometry']['coordinates']
        optimal_stops = []
        cumulative_distance = 0.0
        next_refuel_distance = 500.0 
        last_lat, last_lon = None, None

        for i in range(len(coordinates)):
            current_lon, current_lat= coordinates[i]
            if last_lat is not None and last_lon is not None:
                segment_distance = self.calculate_distance(
                    (last_lat, last_lon),
                    (current_lat, current_lon)
                )
                cumulative_distance += segment_distance

                # Check if we need to refuel or if we're at the last coordinate
                if cumulative_distance >= next_refuel_distance:
                    nearby_stations = self.find_nearby_stations((current_lat, current_lon))        
                    if nearby_stations:
                        # Get the cheapest station
                        cheapest_station = min(
                            nearby_stations,
                            key=lambda x: x['price']
                        )
                        optimal_stops.append(cheapest_station)
                        next_refuel_distance += 500.0  # Set the next refuel point
                    else:
                        # If no stations found within the default range, expand search radius
                        wider_search = self.find_nearby_stations(
                            (current_lat, current_lon),
                            max_range=100  # Increase search radius to 100 miles
                        )
                        if wider_search:
                            cheapest_station = min(
                                wider_search,
                                key=lambda x: x['price']
                            )
                            optimal_stops.append(cheapest_station)
                            next_refuel_distance += 500.0
                        else:
                            raise Exception("Could not find any suitable fuel stops along the route")
            else:
                pass
            last_lat, last_lon = current_lat, current_lon

        return optimal_stops

    def calculate_total_cost(self, route: Dict, stops: List[Dict]) -> float:
        total_distance = route['routes'][0]['summary']['distance'] / 1609.34  # Convert to miles
        gallons_needed = total_distance / 10  # 10 mpg
        
        total_cost = 0.0
        remaining_gallons = gallons_needed
        
        for stop in stops:
            gallons_at_stop = min(50, remaining_gallons)  # 500 miles / 10 mpg = 50 gallons
            total_cost += stop['price'] * gallons_at_stop
            remaining_gallons -= gallons_at_stop
            if remaining_gallons <= 0:
                break  # No more fuel needed
                
        return round(total_cost, 2)