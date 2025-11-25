"""
Distribution Optimization Algorithm for Agricultural Products
Implements efficient routing and distribution planning using geographic coordinates
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class DistributionOptimizer:
    """Advanced distribution optimization for agricultural products"""
    
    def __init__(self):
        """Initialize distribution optimizer"""
        self.vehicle_capacity = 1000  # kg - default capacity
        self.max_distance = 100  # km - maximum single route distance
        self.fuel_efficiency = 8  # km per liter
        self.fuel_cost_per_liter = 15000  # IDR per liter
    
    def calculate_distribution_cost(self, route: List[Dict], warehouse_coord: Tuple[float, float]) -> Dict:
        """
        Calculate total cost for a distribution route
        
        Args:
            route: List of destinations with coordinates and weights
            warehouse_coord: Starting warehouse coordinates
            
        Returns:
            Cost breakdown dictionary
        """
        total_distance = 0
        total_weight = 0
        current_coord = warehouse_coord
        
        for destination in route:
            dest_coord = (destination['coordinates']['lat'], destination['coordinates']['lng'])
            distance = geodesic(current_coord, dest_coord).kilometers
            total_distance += distance
            total_weight += destination.get('weight_kg', 0)
            current_coord = dest_coord
        
        # Return to warehouse
        return_distance = geodesic(current_coord, warehouse_coord).kilometers
        total_distance += return_distance
        
        # Calculate fuel cost
        fuel_needed = total_distance / self.fuel_efficiency
        fuel_cost = fuel_needed * self.fuel_cost_per_liter
        
        # Calculate driver cost (estimated)
        estimated_time = total_distance / 30  # 30 km/h average speed
        driver_cost = estimated_time * 50000  # IDR 50k per hour
        
        return {
            'total_distance_km': round(total_distance, 2),
            'total_weight_kg': total_weight,
            'fuel_cost_idr': round(fuel_cost, 0),
            'driver_cost_idr': round(driver_cost, 0),
            'total_cost_idr': round(fuel_cost + driver_cost, 0),
            'estimated_time_hours': round(estimated_time, 2),
            'fuel_needed_liters': round(fuel_needed, 2)
        }
    
    def optimize_delivery_route(self, destinations: List[Dict], 
                              warehouse_coord: Tuple[float, float],
                              optimization_type: str = "distance") -> Dict:
        """
        Optimize delivery route using various algorithms
        
        Args:
            destinations: List of destinations with coordinates and demands
            warehouse_coord: Starting warehouse coordinates
            optimization_type: "distance", "time", "cost", or "capacity"
            
        Returns:
            Optimized route with cost analysis
        """
        if not destinations:
            return {'route': [], 'cost': {}, 'efficiency': 0}
        
        # Remove destinations without coordinates
        valid_destinations = [
            dest for dest in destinations 
            if 'coordinates' in dest and dest['coordinates'] and 
            'lat' in dest['coordinates'] and 'lng' in dest['coordinates']
        ]
        
        if not valid_destinations:
            return {'route': [], 'cost': {}, 'efficiency': 0, 'error': 'No valid destinations with coordinates'}
        
        # Choose optimization algorithm based on type
        if optimization_type == "distance":
            optimized_route = self._nearest_neighbor_tsp(valid_destinations, warehouse_coord)
        elif optimization_type == "capacity":
            optimized_route = self._capacity_constrained_routing(valid_destinations, warehouse_coord)
        else:
            optimized_route = self._nearest_neighbor_tsp(valid_destinations, warehouse_coord)
        
        # Calculate costs
        cost_analysis = self.calculate_distribution_cost(optimized_route, warehouse_coord)
        
        # Calculate efficiency metrics
        original_distance = self._calculate_total_distance(valid_destinations, warehouse_coord)
        optimized_distance = cost_analysis['total_distance_km']
        efficiency = ((original_distance - optimized_distance) / original_distance * 100) if original_distance > 0 else 0
        
        return {
            'route': optimized_route,
            'cost': cost_analysis,
            'efficiency': round(efficiency, 2),
            'destinations_count': len(valid_destinations),
            'optimization_type': optimization_type
        }
    
    def _nearest_neighbor_tsp(self, destinations: List[Dict], 
                               start_coord: Tuple[float, float]) -> List[Dict]:
        """
        Solve TSP using nearest neighbor heuristic
        
        Args:
            destinations: List of destinations
            start_coord: Starting coordinates
            
        Returns:
            Optimized route order
        """
        if not destinations:
            return []
        
        unvisited = destinations.copy()
        route = []
        current_coord = start_coord
        
        while unvisited:
            # Find nearest unvisited destination
            nearest = min(unvisited, key=lambda dest: 
                         geodesic(current_coord, (dest['coordinates']['lat'], dest['coordinates']['lng'])).kilometers)
            
            route.append(nearest)
            unvisited.remove(nearest)
            current_coord = (nearest['coordinates']['lat'], nearest['coordinates']['lng'])
        
        return route
    
    def _capacity_constrained_routing(self, destinations: List[Dict], 
                                     warehouse_coord: Tuple[float, float]) -> List[Dict]:
        """
        Route optimization considering vehicle capacity constraints
        
        Args:
            destinations: Destinations with weight demands
            warehouse_coord: Warehouse coordinates
            
        Returns:
            Route considering capacity limits
        """
        # Sort by distance from warehouse (nearest first)
        sorted_destinations = sorted(destinations, key=lambda dest:
            geodesic(warehouse_coord, (dest['coordinates']['lat'], dest['coordinates']['lng'])).kilometers)
        
        route = []
        current_weight = 0
        
        for destination in sorted_destinations:
            dest_weight = destination.get('weight_kg', 0)
            
            # Check if adding this destination exceeds capacity
            if current_weight + dest_weight <= self.vehicle_capacity:
                route.append(destination)
                current_weight += dest_weight
            else:
                # Would exceed capacity - skip for now
                # In full implementation, this would create multiple routes
                continue
        
        return route
    
    def _calculate_total_distance(self, destinations: List[Dict], 
                                 warehouse_coord: Tuple[float, float]) -> float:
        """Calculate total distance for unoptimized route"""
        total_distance = 0
        current_coord = warehouse_coord
        
        for destination in destinations:
            dest_coord = (destination['coordinates']['lat'], destination['coordinates']['lng'])
            distance = geodesic(current_coord, dest_coord).kilometers
            total_distance += distance
            current_coord = dest_coord
        
        # Return to warehouse
        return_distance = geodesic(current_coord, warehouse_coord).kilometers
        total_distance += return_distance
        
        return total_distance
    
    def find_optimal_warehouse(self, warehouses: List[Dict], 
                               destinations: List[Dict]) -> Dict:
        """
        Find the most optimal warehouse for serving given destinations
        
        Args:
            warehouses: List of available warehouses
            destinations: List of destinations to serve
            
        Returns:
            Optimal warehouse with efficiency analysis
        """
        if not warehouses or not destinations:
            return {'warehouse': None, 'efficiency': 0, 'total_distance': 0}
        
        best_warehouse = None
        best_efficiency = float('inf')
        best_analysis = None
        
        for warehouse in warehouses:
            if 'coordinates' not in warehouse or not warehouse['coordinates']:
                continue
            
            warehouse_coord = (warehouse['coordinates']['lat'], warehouse['coordinates']['lng'])
            
            # Calculate route from this warehouse
            route_analysis = self.optimize_delivery_route(destinations, warehouse_coord)
            
            if route_analysis['cost']['total_distance_km'] < best_efficiency:
                best_efficiency = route_analysis['cost']['total_distance_km']
                best_warehouse = warehouse
                best_analysis = route_analysis
        
        return {
            'warehouse': best_warehouse,
            'efficiency': best_efficiency,
            'route_analysis': best_analysis,
            'total_distance': best_efficiency
        }
    
    def optimize_distribution_routes(self, warehouses: List[Dict], 
                                   merchants: List[Dict]) -> List[Dict]:
        """
        Optimize distribution routes for multiple warehouses serving multiple merchants
        
        Args:
            warehouses: List of warehouses with coordinates and capacity
            merchants: List of merchants with coordinates and demand
            
        Returns:
            List of optimized routes with cost analysis
        """
        optimized_routes = []
        
        if not warehouses or not merchants:
            return optimized_routes
        
        # Filter valid merchants with coordinates
        valid_merchants = [
            merchant for merchant in merchants
            if 'coordinates' in merchant and merchant['coordinates'] and
            'lat' in merchant['coordinates'] and 'lng' in merchant['coordinates']
        ]
        
        if not valid_merchants:
            return optimized_routes
        
        # For each warehouse, find optimal routes to merchants
        for warehouse in warehouses:
            if 'coordinates' not in warehouse or not warehouse['coordinates']:
                continue
            
            warehouse_coord = (warehouse['coordinates']['lat'], warehouse['coordinates']['lng'])
            
            # Optimize delivery route from this warehouse to all merchants
            route_analysis = self.optimize_delivery_route(
                valid_merchants, warehouse_coord, "balanced"
            )
            
            if route_analysis['route']:
                optimized_routes.append({
                    'warehouse': warehouse,
                    'route': route_analysis['route'],
                    'total_distance': route_analysis['cost']['total_distance_km'],
                    'total_cost': route_analysis['cost']['total_cost_idr'],
                    'efficiency': route_analysis['efficiency'],
                    'destinations_count': route_analysis['destinations_count']
                })
        
        return optimized_routes
    
    def generate_distribution_recommendations(self, warehouse_inventory: Dict,
                                            pending_requests: List[Dict],
                                            warehouses: List[Dict]) -> Dict:
        """
        Generate smart distribution recommendations based on inventory and location
        
        Args:
            warehouse_inventory: Current inventory by warehouse
            pending_requests: Pending distribution requests
            warehouses: Available warehouses
            
        Returns:
            Distribution recommendations with efficiency scores
        """
        recommendations = {
            'recommendations': [],
            'total_efficiency': 0,
            'total_cost_savings': 0,
            'unfulfilled_requests': []
        }
        
        # Group requests by location proximity
        location_groups = self._group_requests_by_proximity(pending_requests)
        
        for group in location_groups:
            # Find optimal warehouse for this group
            optimal_warehouse = self.find_optimal_warehouse(warehouses, group['requests'])
            
            if optimal_warehouse['warehouse']:
                # Calculate route
                route_analysis = self.optimize_delivery_route(
                    group['requests'], 
                    (optimal_warehouse['warehouse']['coordinates']['lat'], 
                     optimal_warehouse['warehouse']['coordinates']['lng'])
                )
                
                recommendation = {
                    'warehouse': optimal_warehouse['warehouse'],
                    'destinations': group['requests'],
                    'route_analysis': route_analysis,
                    'priority_score': group.get('priority_score', 0),
                    'estimated_savings': route_analysis['efficiency'] * 1000  # IDR estimation
                }
                
                recommendations['recommendations'].append(recommendation)
        
        # Calculate totals
        total_efficiency = sum(r['route_analysis']['efficiency'] for r in recommendations['recommendations'])
        total_savings = sum(r['estimated_savings'] for r in recommendations['recommendations'])
        
        recommendations['total_efficiency'] = round(total_efficiency / len(recommendations['recommendations']), 2) if recommendations['recommendations'] else 0
        recommendations['total_cost_savings'] = round(total_savings, 0)
        
        return recommendations
    
    def _group_requests_by_proximity(self, requests: List[Dict]) -> List[Dict]:
        """Group requests by geographic proximity for efficient routing"""
        # Simple clustering based on distance threshold
        groups = []
        distance_threshold = 5.0  # km
        
        for request in requests:
            if 'coordinates' not in request or not request['coordinates']:
                continue
            
            placed = False
            request_coord = (request['coordinates']['lat'], request['coordinates']['lng'])
            
            for group in groups:
                if group['requests']:
                    # Check if close to any existing request in group
                    for existing_request in group['requests']:
                        existing_coord = (existing_request['coordinates']['lat'], 
                                        existing_request['coordinates']['lng'])
                        distance = geodesic(request_coord, existing_coord).kilometers
                        
                        if distance <= distance_threshold:
                            group['requests'].append(request)
                            placed = True
                            break
                    
                    if placed:
                        break
            
            if not placed:
                # Create new group
                groups.append({
                    'requests': [request],
                    'center_coord': request_coord,
                    'priority_score': request.get('priority', 0)
                })
        
        return groups

# Global optimizer instance
distribution_optimizer = DistributionOptimizer()

def optimize_distribution_route(destinations: List[Dict], 
                               warehouse_coord: Tuple[float, float],
                               optimization_type: str = "distance") -> Dict:
    """
    Convenience function for route optimization
    
    Args:
        destinations: List of destinations with coordinates
        warehouse_coord: Starting warehouse coordinates
        optimization_type: Type of optimization
        
    Returns:
        Optimized route analysis
    """
    return distribution_optimizer.optimize_delivery_route(
        destinations, warehouse_coord, optimization_type
    )

def find_optimal_warehouse_for_distribution(warehouses: List[Dict], 
                                           destinations: List[Dict]) -> Dict:
    """
    Find optimal warehouse for distribution
    
    Args:
        warehouses: Available warehouses
        destinations: Destinations to serve
        
    Returns:
        Optimal warehouse selection
    """
    return distribution_optimizer.find_optimal_warehouse(warehouses, destinations)