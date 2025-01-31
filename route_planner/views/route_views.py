# route_planner/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..utils import RoutePlanner

class RouteAPIView(APIView):
    def post(self, request):
        try:
            # Expect coordinates in the request
            start_lat = float(request.data.get('start_lat'))
            start_lon = float(request.data.get('start_lon'))
            end_lat = float(request.data.get('end_lat'))
            end_lon = float(request.data.get('end_lon'))
            
            # switched the order to lon&lat as open route expects them that way
            start_coords = (start_lon, start_lat)
            end_coords = (end_lon, end_lat)
            planner = RoutePlanner()

            # Get route
            print(start_coords,end_coords)
            route = planner.get_route(start_coords, end_coords)
            # print('error')

            # Find optimal fuel stops
            # print(route)
            optimal_stops = planner.find_optimal_fuel_stops(route)
            print(optimal_stops)
            # Calculate total cost
            total_cost = planner.calculate_total_cost(route, optimal_stops) #CHANGE ME
            
            return Response({
                'route': route,
                'fuel_stops': optimal_stops,
                'total_cost': total_cost
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )