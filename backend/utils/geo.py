"""
backend/utils/geo.py
---------------------
Geolocation utility for attendance check-in radius validation.
Uses the Haversine formula to calculate distance between two coordinates.
"""

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance (in metres) between two points
    on Earth using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1 (decimal degrees).
        lat2, lon2: Latitude and longitude of point 2 (decimal degrees).

    Returns:
        Distance in metres.
    """
    R = 6_371_000  # Earth radius in metres

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_within_office_radius(
    employee_lat: float,
    employee_lon: float,
    office_lat: float,
    office_lon: float,
    radius_meters: float,
) -> bool:
    """
    Returns True if the employee's location is within the allowed office radius.

    Args:
        employee_lat / employee_lon: Coordinates from browser geolocation.
        office_lat / office_lon: Configured office coordinates (from config.py).
        radius_meters: Allowed check-in radius in metres.
    """
    distance = haversine_distance(employee_lat, employee_lon, office_lat, office_lon)
    return distance <= radius_meters
