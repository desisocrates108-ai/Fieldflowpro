from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fieldflow-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against stored hash.
    Returns False (instead of raising) if hash is malformed or bcrypt is broken.
    This prevents a corrupted bcrypt installation from causing 500s that block ALL logins.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"verify_password failed: {type(e).__name__}: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    return payload

def require_roles(*allowed_roles):
    """
    Role-based access control decorator.
    
    Roles hierarchy:
    - admin: Full access to everything
    - cre: Same as admin but cannot manage users/settings
    - worker: Can only access own data (coupons, attendance)
    - branch: Limited access, masked mobile numbers
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker

# Role permission definitions
ROLE_PERMISSIONS = {
    "admin": {
        "can_view_full_mobile": True,
        "can_manage_users": True,
        "can_manage_settings": True,
        "can_export_data": True,
        "can_view_all_coupons": True,
        "can_view_audit_logs": True,
        "can_assign_branches": True,
    },
    "cre": {
        "can_view_full_mobile": True,
        "can_manage_users": False,
        "can_manage_settings": False,
        "can_export_data": True,
        "can_view_all_coupons": True,
        "can_view_audit_logs": True,
        "can_assign_branches": False,
    },
    "worker": {
        "can_view_full_mobile": True,  # Only own coupons
        "can_manage_users": False,
        "can_manage_settings": False,
        "can_export_data": False,
        "can_view_all_coupons": False,  # Only own
        "can_view_audit_logs": False,
        "can_assign_branches": False,
    },
    "branch": {
        "can_view_full_mobile": False,  # Only last 4 digits
        "can_manage_users": False,
        "can_manage_settings": False,
        "can_export_data": False,
        "can_view_all_coupons": False,  # Only assigned
        "can_view_audit_logs": False,
        "can_assign_branches": False,
    },
}

def get_role_permissions(role: str) -> dict:
    """Get permissions for a specific role"""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["worker"])

def can_view_full_mobile(role: str) -> bool:
    """Check if role can view full mobile numbers"""
    return ROLE_PERMISSIONS.get(role, {}).get("can_view_full_mobile", False)

def mask_mobile(phone: str) -> str:
    """
    Mask mobile number showing only last 4 digits.
    Example: 1234567890 -> XXXXXX7890
    """
    if not phone or len(phone) < 4:
        return "XXXX"
    return "X" * (len(phone) - 4) + phone[-4:]

def get_last4_digits(phone: str) -> str:
    """Extract last 4 digits of phone number"""
    if not phone or len(phone) < 4:
        return phone or ""
    # Remove any non-digit characters first
    digits = ''.join(filter(str.isdigit, phone))
    return digits[-4:] if len(digits) >= 4 else digits
