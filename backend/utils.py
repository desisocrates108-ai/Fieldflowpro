import secrets
import string
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import math
import re

# In-memory OTP storage (for MVP - use Redis in production)
otp_storage: Dict[str, dict] = {}

def generate_coupon_code(area_id: str, worker_id: str) -> str:
    """
    Generate unique coupon code in format: SVL-AREAID-WORKERID-RANDOM6
    Example: SVL-VAL-102-A7K9D2
    """
    # Clean and format area_id (take first 3 chars, uppercase)
    # Handle None or empty area_id
    area_part = "DEF"
    if area_id:
        cleaned = re.sub(r'[^A-Za-z0-9]', '', area_id)[:3].upper()
        if cleaned:
            area_part = cleaned
    
    # Take last 3 chars of worker_id for uniqueness
    worker_part = worker_id[-3:].upper()
    
    # Generate random 6 character alphanumeric
    random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    return f"SVL-{area_part}-{worker_part}-{random_suffix}"

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

# ========== Basic Encryption for Mobile Numbers (MVP) ==========
# Note: For production, use proper AES-256 encryption with secure key management

ENCRYPTION_KEY = "fieldflow-mobile-key-2024"  # Change in production

def _get_encryption_key() -> bytes:
    """Get encryption key as bytes"""
    return hashlib.sha256(ENCRYPTION_KEY.encode()).digest()

def encrypt_mobile(phone: str) -> str:
    """
    Basic encryption for mobile numbers.
    For MVP: Uses simple XOR + base64 encoding
    For Production: Use AES-256 with proper key management
    """
    if not phone:
        return ""
    
    key = _get_encryption_key()
    encrypted = bytes([ord(c) ^ key[i % len(key)] for i, c in enumerate(phone)])
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_mobile(encrypted_phone: str) -> str:
    """
    Decrypt mobile number.
    """
    if not encrypted_phone:
        return ""
    
    try:
        key = _get_encryption_key()
        encrypted = base64.b64decode(encrypted_phone.encode('utf-8'))
        decrypted = ''.join([chr(b ^ key[i % len(key)]) for i, b in enumerate(encrypted)])
        return decrypted
    except Exception:
        # If decryption fails, return original (might be unencrypted)
        return encrypted_phone

def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to standard format.
    Removes spaces, dashes, and ensures +91 prefix for Indian numbers.
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If starts with +, keep it
    if cleaned.startswith('+'):
        return cleaned
    
    # If 10 digits, assume Indian number
    if len(cleaned) == 10:
        return f"+91{cleaned}"
    
    return cleaned

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    normalized = normalize_phone(phone)
    # Check if it's a valid format (10-15 digits with optional +)
    if normalized.startswith('+'):
        return 10 <= len(normalized[1:]) <= 15
    return 10 <= len(normalized) <= 15

def validate_customer_name(name: str) -> bool:
    """Validate customer name - only letters, spaces, and basic punctuation"""
    if not name or len(name) < 2:
        return False
    # Allow letters, spaces, dots, and hyphens
    return bool(re.match(r'^[A-Za-z\s.\-]+$', name))
