import folium
from folium import plugins
from typing import List, Dict
# import branca.colormap as cm

def create_route_map(real_route_coordinates: List[List[float]], fuel_stops: List[Dict]) -> folium.Map:
    """
    Create a basic route map with markers
    """
    route_coordinates= list(map(lambda x: list(reversed(x)), real_route_coordinates))
    # Calculate center of the route
    center_lat = sum(coord[0] for coord in route_coordinates) / len(route_coordinates)
    center_lon = sum(coord[1] for coord in route_coordinates) / len(route_coordinates)
    
    # Create base map with proper attribution
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5,
        tiles='CartoDB positron',
        attr='CartoDB'
    )
    
    # Add the route line
    route_line = folium.PolyLine(
        route_coordinates,
        weight=3,
        color='blue',
        opacity=0.8
    )
    route_line.add_to(m)
    
    # Add start marker
    folium.Marker(
        route_coordinates[0], #CHANGE ME
        # route_coordinates[0].reverse(),
        popup='Start',
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)
    
    # Add end marker
    folium.Marker(
        route_coordinates[-1], #CHANGE ME
        # route_coordinates[-1].reverse(),
        popup='End',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add fuel stop markers
    for stop in fuel_stops:
        folium.Marker(
            location=[stop['latitude'], stop['longitude']],
            popup=folium.Popup(
                f"""
                <div style="width: 200px">
                    <h4>{stop['name']}</h4>
                    <p><b>Price:</b> ${stop['price']:.2f}/gal</p>
                    <p><b>Distance:</b> {stop.get('distance_from_start',0):.1f} miles</p>
                </div>
                """,
                max_width=300
            ),
            icon=folium.Icon(color='orange', icon='info-sign')
        ).add_to(m)
    
    # Add measure control
    plugins.MeasureControl().add_to(m)
    
    return m

def create_detailed_route_map(
    route_coordinates: List[List[float]],
    fuel_stops: List[Dict],
    route_segments: List[Dict] = None
) -> folium.Map:
    """
    Create a detailed route map with additional features
    """
    # Calculate center of the route
    center_lat = sum(coord[0] for coord in route_coordinates) / len(route_coordinates)
    center_lon = sum(coord[1] for coord in route_coordinates) / len(route_coordinates)
    
    # Create base map with proper attribution
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5,
        tiles='CartoDB positron',
        attr='CartoDB'
    )
    
    # Add different tile layers with proper attribution
    folium.TileLayer(
        'OpenStreetMap',
        attr='© OpenStreetMap contributors'
    ).add_to(m)
    
    folium.TileLayer(
        'CartoDB positron',
        attr='© CartoDB'
    ).add_to(m)
    
    folium.TileLayer(
        'Stamen Terrain',
        attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
    ).add_to(m)
    
    # Create layer control
    folium.LayerControl().add_to(m)
    
    # Add route segments with fuel level indicators
    if route_segments:
        for segment in route_segments:
            color = get_color_for_fuel_level(segment['fuel_level'])
            folium.PolyLine(
                segment['coordinates'],
                weight=4,
                color=color,
                opacity=0.8,
                popup=folium.Popup(
                    f"Fuel Level: {segment['fuel_level']:.1f} gallons",
                    max_width=200
                )
            ).add_to(m)
    else:
        # If no segments provided, show complete route
        folium.PolyLine(
            route_coordinates,
            weight=3,
            color='blue',
            opacity=0.8
        ).add_to(m)
    
    # Add fuel stops with detailed information
    for i, stop in enumerate(fuel_stops, 1):
        folium.CircleMarker(
            location=[stop['latitude'], stop['longitude']],
            radius=8,
            color='orange',
            fill=True,
            popup=folium.Popup(
                f"""
                <div style="width: 250px">
                    <h4>Stop #{i}: {stop['name']}</h4>
                    <table style="width: 100%">
                        <tr>
                            <td><b>Price:</b></td>
                            <td>${stop.get('price',0):.2f}/gal</td>
                        </tr>
                        <tr>
                            <td><b>Distance:</b></td>
                            <td>{stop.get('distance',0):.1f} miles</td>
                        </tr>
                        <tr>
                            <td><b>Fuel Added:</b></td>
                            <td>{stop.get('amount', 0):.1f} gal</td>
                        </tr>
                        <tr>
                            <td><b>Cost:</b></td>
                            <td>${stop.get('cost', 0):.2f}</td>
                        </tr>
                    </table>
                </div>
                """,
                max_width=300
            )
        ).add_to(m)
    
    # Add start and end markers
    folium.Marker(
        route_coordinates[0],
        popup='Start',
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)
    
    folium.Marker(
        route_coordinates[-1],
        popup='End',
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(m)
    
    # Add legend
    legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; 
                    left: 50px; 
                    z-index: 1000;
                    background-color: white;
                    padding: 10px;
                    border: 2px solid grey;
                    border-radius: 5px">
            <h4>Legend</h4>
            <p><i class="fa fa-play" style="color: green"></i> Start</p>
            <p><i class="fa fa-stop" style="color: red"></i> End</p>
            <p><i class="fa fa-circle" style="color: orange"></i> Fuel Stop</p>
            <p>Fuel Level:</p>
            <p style="color: green">■ High (>70%)</p>
            <p style="color: yellow">■ Medium (30-70%)</p>
            <p style="color: red">■ Low (<30%)</p>
        </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add plugins
    plugins.MeasureControl().add_to(m)
    plugins.MiniMap().add_to(m)
    plugins.Fullscreen().add_to(m)
    plugins.MousePosition().add_to(m)
    
    return m

def get_color_for_fuel_level(fuel_level: float, max_fuel: float = 50.0) -> str:
    """Return color based on fuel level percentage"""
    ratio = fuel_level / max_fuel
    if ratio > 0.7:
        return 'green'
    elif ratio > 0.3:
        return 'yellow'
    else:
        return 'red'

def save_map(map_obj: folium.Map, filename: str = 'route_map.html') -> str:
    """Save map to HTML file"""
    map_obj.save(filename)
    return filename

# Example usage:
if __name__ == "__main__":
    # Example data
    example_route = [
        [40.7128, -74.0060],  # New York
        [39.9526, -75.1652],  # Philadelphia
        [38.9072, -77.0369],  # Washington DC
    ]
    
    example_stops = [
        {
            "name": "AM ENERGY",
            "latitude": 40.740447,
            "longitude": -99.53681,
            "price": 2.899,
            "distance": 9.061192170949194
        },
        {
            "name": "PWI #535",
            "latitude": 39.109476,
            "longitude": -108.358051,
            "price": 3.379,
            "distance": 44.063054960216164
        },
        {
            "name": "MOAPA PAIUTE TRAVEL CENTER",
            "latitude": 36.770009,
            "longitude": -114.647283,
            "price": 3.33233333,
            "distance": 19.571760466149783
        },
        {
            "name": "TA LAPLACE",
            "latitude": 34.05513,
            "longitude": -118.25703,
            "price": 3.22733333,
            "distance": 39.36759052939697
        }
    ]
    
    example_segments = [
        {
            'coordinates': [[40.7128, -74.0060], [39.9526, -75.1652]],
            'fuel_level': 45.0
        }
    ]
    
    # Create basic map
    basic_map = create_route_map(example_route, example_stops)
    save_map(basic_map, 'basic_route_map.html')
    
    # Create detailed map
    detailed_map = create_detailed_route_map(example_route, example_stops, example_segments)
    save_map(detailed_map, 'detailed_route_map.html')