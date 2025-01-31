# routing/views/route_views.py
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..utils import RoutePlanner
from ..map_visualizer import create_route_map

class MapAPIView(APIView):
    def get(self, request):
        '''make this endpoint parse the coords from the link so we can use it on the browser easier'''
        try:
            start_lat = float(request.query_params.get('start_lat'))
            start_lon = float(request.query_params.get('start_lon'))
            end_lat = float(request.query_params.get('end_lat'))
            end_lon = float(request.query_params.get('end_lon'))
            
            # switched the order to lon&lat as open route expects them that way
            start_coords = (start_lon, start_lat)
            end_coords = (end_lon, end_lat)
            planner = RoutePlanner()

            route = planner.get_route(start_coords, end_coords)

            # Find optimal fuel stops
            optimal_stops = planner.find_optimal_fuel_stops(route)

            # total_cost = planner.calculate_total_cost(route, optimal_stops) #CHANGE ME
            map_obj = create_route_map(route['routes'][0]['geometry']['coordinates'], optimal_stops)

            return HttpResponse(map_obj._repr_html_())

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
