import math
from typing import List, Dict, Tuple, Any
from geopy.distance import geodesic
import logging
import numpy as np

# Try to import OR-Tools
try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logging.warning("OR-Tools not available. VRP optimization will be disabled.")

logger = logging.getLogger(__name__)

class DistributionOptimizer:
    def __init__(self):
        pass
        
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in km"""
        return geodesic(coord1, coord2).kilometers
        
    def optimize_delivery_route(self, destinations: List[Dict], warehouse_coord: Tuple[float, float], 
                              optimization_type: str = "distance", num_vehicles: int = 1,
                              vehicle_capacity: float = 1000.0) -> Dict[str, Any]:
        """
        Optimize delivery route using specified method
        
        Args:
            destinations: List of dictionaries containing destination info
            warehouse_coord: Tuple of (lat, lng) for the warehouse
            optimization_type: "distance", "cost", or "vrp"
            num_vehicles: Number of vehicles for VRP
            vehicle_capacity: Capacity per vehicle in kg
        """
        # Filter valid destinations
        valid_destinations = [
            d for d in destinations 
            if d.get('coordinates') and 
            isinstance(d['coordinates'], dict) and
            d['coordinates'].get('lat') is not None and 
            d['coordinates'].get('lng') is not None
        ]
        
        if not valid_destinations:
            logger.warning("No valid destinations with coordinates found for optimization")
            return {
                'route': [], 
                'cost': {}, 
                'efficiency': 0, 
                'error': 'No valid destinations with coordinates found. Please ensure merchants have valid location data.'
            }
        
        # Choose optimization algorithm
        if optimization_type == "vrp" and ORTOOLS_AVAILABLE:
            return self._solve_vrp_with_ortools(valid_destinations, warehouse_coord, num_vehicles, vehicle_capacity)
        elif optimization_type == "distance":
            # Use TSP with 2-opt improvement
            route = self._solve_tsp_nearest_neighbor(valid_destinations, warehouse_coord)
            route = self._two_opt_improvement(route, warehouse_coord)
        else:
            # Default to simple TSP
            route = self._solve_tsp_nearest_neighbor(valid_destinations, warehouse_coord)
            
        # Calculate metrics
        total_distance = self._calculate_route_distance(route, warehouse_coord)
        total_weight = sum(d.get('weight_kg', 0) for d in route)
        
        # Estimate cost (simplified model)
        base_cost = 50000  # Base cost per trip
        cost_per_km = 2000
        total_cost = base_cost + (total_distance * cost_per_km)
        
        return {
            'route': route,
            'cost': {
                'total_distance_km': round(total_distance, 2),
                'total_cost_rp': round(total_cost, 0),
                'cost_per_kg': round(total_cost / total_weight, 0) if total_weight > 0 else 0
            },
            'efficiency': round(total_weight / total_distance, 2) if total_distance > 0 else 0
        }

    def _solve_tsp_nearest_neighbor(self, destinations: List[Dict], start_coord: Tuple[float, float]) -> List[Dict]:
        """Solve TSP using Nearest Neighbor algorithm"""
        unvisited = destinations.copy()
        current_coord = start_coord
        route = []
        
        while unvisited:
            # Find nearest neighbor
            nearest = min(unvisited, key=lambda x: self.calculate_distance(
                current_coord, 
                (x['coordinates']['lat'], x['coordinates']['lng'])
            ))
            
            route.append(nearest)
            unvisited.remove(nearest)
            current_coord = (nearest['coordinates']['lat'], nearest['coordinates']['lng'])
            
        return route

    def _two_opt_improvement(self, route: List[Dict], warehouse_coord: Tuple) -> List[Dict]:
        """
        Improve TSP solution using 2-opt algorithm
        """
        if len(route) < 3:
            return route
            
        improved = True
        best_route = route.copy()
        
        # Limit iterations for performance
        max_iterations = 50
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for i in range(len(best_route) - 1):
                for j in range(i + 2, len(best_route)):
                    # Create new route with swapped edges
                    new_route = best_route[:i+1] + best_route[i+1:j+1][::-1] + best_route[j+1:]
                    
                    # Calculate distances
                    current_dist = self._calculate_route_distance(best_route, warehouse_coord)
                    new_dist = self._calculate_route_distance(new_route, warehouse_coord)
                    
                    if new_dist < current_dist:
                        best_route = new_route
                        improved = True
                        break # Restart inner loop
                if improved:
                    break # Restart outer loop
                    
        return best_route

    def _solve_vrp_with_ortools(self, destinations: List[Dict], warehouse_coord: Tuple, 
                                num_vehicles: int, vehicle_capacity: float) -> Dict:
        """Solve VRP using Google OR-Tools"""
        # Create data model
        data = {}
        
        # Locations: Warehouse + Destinations
        locations = [warehouse_coord] + [
            (d['coordinates']['lat'], d['coordinates']['lng']) for d in destinations
        ]
        
        # Distance matrix
        size = len(locations)
        dist_matrix = np.zeros((size, size))
        for i in range(size):
            for j in range(size):
                if i != j:
                    dist_matrix[i][j] = self.calculate_distance(locations[i], locations[j]) * 1000 # meters
        
        data['distance_matrix'] = dist_matrix
        data['demands'] = [0] + [d.get('weight_kg', 0) for d in destinations]
        data['vehicle_capacities'] = [vehicle_capacity] * num_vehicles
        data['num_vehicles'] = num_vehicles
        data['depot'] = 0
        
        # Create routing index manager
        manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                              data['num_vehicles'], data['depot'])

        # Create Routing Model
        routing = pywrapcp.RoutingModel(manager)

        # Create and register a transit callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Capacity constraint
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity')

        # Setting first solution heuristic
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.seconds = 5

        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            routes = []
            total_distance = 0
            total_load = 0
            
            for vehicle_id in range(data['num_vehicles']):
                index = routing.Start(vehicle_id)
                route_nodes = []
                route_distance = 0
                route_load = 0
                
                while not routing.IsEnd(index):
                    node_index = manager.IndexToNode(index)
                    if node_index != 0: # Skip depot
                        dest = destinations[node_index - 1]
                        route_nodes.append(dest)
                        route_load += data['demands'][node_index]
                    
                    previous_index = index
                    index = solution.Value(routing.NextVar(index))
                    route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                
                if route_nodes:
                    routes.append({
                        'vehicle_id': vehicle_id + 1,
                        'route': route_nodes,
                        'distance_km': route_distance / 1000,
                        'load_kg': route_load
                    })
                    total_distance += route_distance
                    total_load += route_load
            
            # Estimate cost
            base_cost = 50000 * len(routes)
            cost_per_km = 2000
            total_cost = base_cost + (total_distance / 1000 * cost_per_km)
            
            return {
                'routes': routes, # List of routes per vehicle
                'route': routes[0]['route'] if routes else [], # Backward compatibility (first route)
                'cost': {
                    'total_distance_km': round(total_distance / 1000, 2),
                    'total_cost_rp': round(total_cost, 0),
                    'cost_per_kg': round(total_cost / total_load, 0) if total_load > 0 else 0
                },
                'efficiency': round(total_load / (total_distance / 1000), 2) if total_distance > 0 else 0
            }
        else:
            return {
                'route': [], 
                'cost': {}, 
                'efficiency': 0, 
                'error': 'Solution not found'
            }

    def _calculate_route_distance(self, route: List[Dict], start_coord: Tuple[float, float]) -> float:
        """Calculate total distance of a route"""
        if not route:
            return 0
            
        total_dist = 0
        current_coord = start_coord
        
        for stop in route:
            stop_coord = (stop['coordinates']['lat'], stop['coordinates']['lng'])
            total_dist += self.calculate_distance(current_coord, stop_coord)
            current_coord = stop_coord
            
        # Return to warehouse (optional, usually VRP assumes return)
        # total_dist += self.calculate_distance(current_coord, start_coord)
        
        return total_dist