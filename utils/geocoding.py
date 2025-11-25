"""
Google Maps Geocoding Utility for Agricultural Location Management
Handles coordinate extraction and distance calculations for farmers, merchants, and warehouses
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic
from geopy.geocoders import GoogleV3
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for handling Google Maps geocoding and location calculations"""
    
    def __init__(self, api_key: str = None):
        """Initialize geocoding service with Google Maps API key"""
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if self.api_key:
            self.geocoder = GoogleV3(api_key=self.api_key)
        else:
            # Fallback to free geocoding service if no API key
            from geopy.geocoders import Nominatim
            self.geocoder = Nominatim(user_agent="lumbung_digital_app")
    
    def geocode_address(self, address: str, region: str = "ID") -> Optional[Dict[str, float]]:
        """
        Geocode an address to get latitude and longitude coordinates
        
        Args:
            address: Complete address string
            region: Region code (default: "ID" for Indonesia)
            
        Returns:
            Dictionary with 'lat', 'lng', and 'formatted_address' or None if failed
        """
        try:
            # Clean and format address
            address = address.strip()
            if not address:
                return None
            
            # Add region context for Indonesian addresses
            if "indonesia" not in address.lower():
                address += ", Indonesia"
            
            # Geocode the address
            location = self.geocoder.geocode(address)
            
            if location:
                return {
                    'lat': location.latitude,
                    'lng': location.longitude,
                    'formatted_address': location.address,
                    'confidence': getattr(location, 'confidence', 0.8)
                }
            else:
                logger.warning(f"Address not found: {address}")
                return None
                
        except Exception as e:
            logger.error(f"Geocoding error for address '{address}': {e}")
            return None
    
    def geocode_with_fallback(self, address: str, location_name: str = "") -> Optional[Dict[str, float]]:
        """
        Geocode with multiple fallback strategies for Indonesian locations
        
        Args:
            address: Primary address to geocode
            location_name: Additional location context (desa, kecamatan, etc.)
            
        Returns:
            Coordinates dictionary or None
        """
        # Strategy 1: Try full address
        result = self.geocode_address(address)
        if result:
            return result
        
        # Strategy 2: Try with location name + Indonesia
        if location_name:
            fallback_address = f"{location_name}, Indonesia"
            result = self.geocode_address(fallback_address)
            if result:
                return result
        
        # Strategy 3: Try common Indonesian location patterns
        common_patterns = [
            f"{address}, Jawa Barat, Indonesia",
            f"{address}, Jawa Tengah, Indonesia",
            f"{address}, Jawa Timur, Indonesia",
            f"{address}, Sumatera Barat, Indonesia",
            f"Desa {address}, Indonesia",
            f"Kecamatan {address}, Indonesia",
            f"Kabupaten {address}, Indonesia"
        ]
        
        for pattern in common_patterns:
            result = self.geocode_address(pattern)
            if result:
                logger.info(f"Found coordinates using fallback pattern: {pattern}")
                return result
        
        logger.warning(f"All geocoding strategies failed for: {address}")
        return None
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """
        Calculate distance between two coordinates in kilometers
        
        Args:
            coord1: (latitude, longitude) tuple for first location
            coord2: (latitude, longitude) tuple for second location
            
        Returns:
            Distance in kilometers
        """
        try:
            distance = geodesic(coord1, coord2).kilometers
            return round(distance, 2)
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return float('inf')
    
    def find_nearby_locations(self, center_coord: Tuple[float, float], 
                            locations: List[Dict], radius_km: float = 10.0) -> List[Dict]:
        """
        Find locations within specified radius from center coordinate
        
        Args:
            center_coord: (latitude, longitude) center point
            locations: List of location dictionaries with coordinates
            radius_km: Search radius in kilometers
            
        Returns:
            List of nearby locations with distance information
        """
        nearby_locations = []
        
        for location in locations:
            if 'coordinates' in location and location['coordinates']:
                loc_coord = (location['coordinates']['lat'], location['coordinates']['lng'])
                distance = self.calculate_distance(center_coord, loc_coord)
                
                if distance <= radius_km:
                    location_with_distance = location.copy()
                    location_with_distance['distance_km'] = distance
                    nearby_locations.append(location_with_distance)
        
        # Sort by distance
        nearby_locations.sort(key=lambda x: x['distance_km'])
        return nearby_locations
    
    def get_optimal_route(self, start_coord: Tuple[float, float], 
                         destinations: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Generate optimal route using nearest neighbor algorithm
        
        Args:
            start_coord: Starting coordinate
            destinations: List of destination coordinates
            
        Returns:
            Ordered list of coordinates for optimal route
        """
        if not destinations:
            return [start_coord]
        
        route = [start_coord]
        remaining = destinations.copy()
        current = start_coord
        
        while remaining:
            # Find nearest destination
            nearest = min(remaining, key=lambda dest: self.calculate_distance(current, dest))
            route.append(nearest)
            remaining.remove(nearest)
            current = nearest
        
        return route
    
    def validate_coordinates(self, lat: float, lng: float) -> bool:
        """
        Validate if coordinates are within reasonable bounds for Indonesia
        
        Args:
            lat: Latitude value
            lng: Longitude value
            
        Returns:
            True if coordinates are valid for Indonesia
        """
        # Indonesia bounds: approximately 6°N to 11°S, 95°E to 141°E
        if not (-11.0 <= lat <= 6.0):
            return False
        if not (95.0 <= lng <= 141.0):
            return False
        return True
    
    def format_coordinates_display(self, coordinates: Dict[str, float]) -> str:
        """Format coordinates for display"""
        if coordinates and 'lat' in coordinates and 'lng' in coordinates:
            return f"{coordinates['lat']:.6f}, {coordinates['lng']:.6f}"
        return "Koordinat tidak tersedia"
    
    def get_static_map_url(self, coordinates: Dict[str, float], zoom: int = 15, 
                          size: str = "400x300", marker_color: str = "red") -> str:
        """
        Generate Google Static Maps URL for coordinate display
        
        Args:
            coordinates: Dictionary with 'lat' and 'lng'
            zoom: Map zoom level (1-21)
            size: Image size (e.g., "400x300")
            marker_color: Marker color for the location
            
        Returns:
            Static map URL or empty string if API key not available
        """
        if not self.api_key or not coordinates:
            return ""
        
        try:
            lat, lng = coordinates['lat'], coordinates['lng']
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            params = f"center={lat},{lng}&zoom={zoom}&size={size}&markers=color:{marker_color}%7C{lat},{lng}&key={self.api_key}"
            return f"{base_url}?{params}"
        except Exception as e:
            logger.error(f"Error generating static map URL: {e}")
            return ""

# Global geocoding service instance
geocoding_service = GeocodingService()

def get_coordinates_from_address(address: str, location_context: str = "") -> Optional[Dict[str, float]]:
    """
    Convenience function to get coordinates from address
    
    Args:
        address: Address to geocode
        location_context: Additional location context
        
    Returns:
        Coordinates dictionary or None
    """
    return geocoding_service.geocode_with_fallback(address, location_context)

def calculate_distance_between_locations(coord1: Tuple[float, float], 
                                       coord2: Tuple[float, float]) -> float:
    """
    Convenience function to calculate distance between two coordinates
    
    Args:
        coord1: (latitude, longitude) tuple for first location
        coord2: (latitude, longitude) tuple for second location
        
    Returns:
        Distance in kilometers
    """
    return geocoding_service.calculate_distance(coord1, coord2)