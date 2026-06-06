# backend/app/services/distance_service.py
from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two points"""
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    except:
        return 999  # Return large distance if error

def filter_nearby_donors(donors, hospital_lat, hospital_lon, max_distance_km=5):
    """Filter donors within max_distance_km of hospital"""
    nearby = []
    for donor in donors:
        donor_lat = donor.get('latitude')
        donor_lon = donor.get('longitude')
        
        if donor_lat and donor_lon:
            distance = calculate_distance(donor_lat, donor_lon, hospital_lat, hospital_lon)
            donor['distance_km'] = round(distance, 2)
            
            if distance <= max_distance_km:
                nearby.append(donor)
    
    return nearby