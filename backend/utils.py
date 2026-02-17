import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Dict
import math

# In-memory OTP storage (for MVP - use Redis in production)
otp_storage: Dict[str, dict] = {}

def generate_coupon_code(area_id: str, worker_id: str) -> str:
    """
    Generate unique coupon code in format: SVL-AREAID-WORKERID-RANDOM6
    Example: SVL-VAL-102-A7K9D2
    """
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"SVL-{area_id[:3].upper()}-{worker_id[:3].upper()}-{random_suffix}"

def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def store_otp(phone: str, coupon_code: str) -> str:
    """Store OTP with expiration (5 minutes)"""
    otp = generate_otp()
    otp_storage[f"{phone}:{coupon_code}"] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "attempts": 0
    }
    return otp

def verify_otp(phone: str, coupon_code: str, otp: str) -> bool:
    """Verify OTP"""
    key = f"{phone}:{coupon_code}"
    stored = otp_storage.get(key)
    
    if not stored:
        return False
    
    # Check expiration
    if datetime.now(timezone.utc) > stored["expires_at"]:
        del otp_storage[key]
        return False
    
    # Check attempts (max 3)
    if stored["attempts"] >= 3:
        del otp_storage[key]
        return False
    
    stored["attempts"] += 1
    
    if stored["otp"] == otp:
        del otp_storage[key]
        return True
    
    return False

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    R = 6371  # Radius of earth in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def find_nearest_branch(branches: list, latitude: float, longitude: float) -> dict:
    """Find the nearest branch based on haversine distance"""
    if not branches:
        return None
    
    nearest = None
    min_distance = float('inf')
    
    for branch in branches:
        distance = calculate_haversine_distance(
            latitude, longitude,
            branch['latitude'], branch['longitude']
        )
        if distance < min_distance:
            min_distance = distance
            nearest = branch
            nearest['distance_km'] = round(distance, 2)
    
    return nearest

def serialize_datetime(obj):
    """Serialize datetime objects to ISO string"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
