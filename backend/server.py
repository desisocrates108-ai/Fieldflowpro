from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union
import shutil
import uuid

from models import (
    UserCreate, UserLogin, User, UserResponse, TokenResponse,
    AttendanceCreate, Attendance, AttendanceResponse,
    CouponCreate, Coupon, CouponResponseFull, CouponResponseMasked, CouponResponseWorker,
    BookingCreate, Booking, BookingResponse, BookingResponseMasked, BookingStatusUpdate,
    BranchCreate, Branch, BranchResponse, BranchAssign,
    TaskCreate, Task, TaskResponse, TaskUpdate,
    LocationUpdate, LocationLog,
    DashboardStats, OTPRequest, OTPVerify,
    AuditLog, AuditLogResponse, CouponSearchQuery
)
from auth import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, decode_token, get_current_user, require_roles,
    can_view_full_mobile, mask_mobile, get_last4_digits, get_role_permissions
)
from utils import (
    generate_coupon_code, store_otp, verify_otp, 
    find_nearest_branch, serialize_datetime,
    encrypt_mobile, decrypt_mobile, normalize_phone, validate_phone, validate_customer_name
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="FieldFlow Pro API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Audit Logging Helper ==========
async def create_audit_log(
    user_id: str,
    user_role: str,
    action: str,
    entity: str,
    entity_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    request: Optional[Request] = None
):
    """Create an audit log entry"""
    audit = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        entity=entity,
        entity_id=entity_id,
        metadata=metadata,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    doc = audit.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.audit_logs.insert_one(doc)
    
    logger.info(f"AUDIT: {action} by {user_role}:{user_id} on {entity}:{entity_id}")

# ========== Auth Routes ==========
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate, request: Request):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        role=user_data.role
    )
    user_dict = user.model_dump()
    user_dict["password_hash"] = get_password_hash(user_data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Audit log
    await create_audit_log(
        user_id=user.id,
        user_role=user.role,
        action="USER_CREATED",
        entity="user",
        entity_id=user.id,
        metadata={"email": user.email, "role": user.role},
        request=request
    )
    
    # Generate tokens
    token_data = {"sub": user.id, "email": user.email, "role": user.role, "name": user.name}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            area_id=user.area_id,
            branch_id=user.branch_id
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        # Audit failed login
        await create_audit_log(
            user_id="unknown",
            user_role="unknown",
            action="LOGIN_FAILED",
            entity="auth",
            metadata={"email": credentials.email},
            request=request
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Audit successful login
    await create_audit_log(
        user_id=user["id"],
        user_role=user["role"],
        action="LOGIN_SUCCESS",
        entity="auth",
        entity_id=user["id"],
        request=request
    )
    
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"], "name": user["name"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            role=user["role"],
            is_active=user.get("is_active", True),
            area_id=user.get("area_id"),
            branch_id=user.get("branch_id")
        )
    )

@api_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"], "name": user["name"]}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            role=user["role"],
            is_active=user.get("is_active", True),
            area_id=user.get("area_id"),
            branch_id=user.get("branch_id")
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        phone=user.get("phone"),
        role=user["role"],
        is_active=user.get("is_active", True),
        area_id=user.get("area_id"),
        branch_id=user.get("branch_id")
    )

# ========== Attendance Routes ==========
@api_router.post("/attendance/punch-in", response_model=AttendanceResponse)
async def punch_in(data: AttendanceCreate, request: Request, current_user: dict = Depends(require_roles("worker", "admin"))):
    worker_id = current_user["sub"]
    
    # Check if already punched in today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    existing_punch = await db.attendance.find_one({
        "worker_id": worker_id,
        "type": "PUNCH_IN",
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    if existing_punch:
        raise HTTPException(status_code=400, detail="Already punched in today")
    
    attendance = Attendance(
        worker_id=worker_id,
        type="PUNCH_IN",
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy
    )
    
    doc = attendance.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.attendance.insert_one(doc)
    
    # Audit log
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="PUNCH_IN",
        entity="attendance",
        entity_id=attendance.id,
        metadata={"latitude": data.latitude, "longitude": data.longitude},
        request=request
    )
    
    return AttendanceResponse(
        id=attendance.id,
        worker_id=attendance.worker_id,
        type=attendance.type,
        latitude=attendance.latitude,
        longitude=attendance.longitude,
        timestamp=attendance.timestamp,
        is_valid=attendance.is_valid,
        remarks=attendance.remarks
    )

@api_router.post("/attendance/punch-out", response_model=AttendanceResponse)
async def punch_out(data: AttendanceCreate, request: Request, current_user: dict = Depends(require_roles("worker", "admin"))):
    worker_id = current_user["sub"]
    
    # Check if punched in today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    punch_in = await db.attendance.find_one({
        "worker_id": worker_id,
        "type": "PUNCH_IN",
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    if not punch_in:
        raise HTTPException(status_code=400, detail="Must punch in first")
    
    # Check if already punched out
    punch_out_exists = await db.attendance.find_one({
        "worker_id": worker_id,
        "type": "PUNCH_OUT",
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    if punch_out_exists:
        raise HTTPException(status_code=400, detail="Already punched out today")
    
    attendance = Attendance(
        worker_id=worker_id,
        type="PUNCH_OUT",
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy
    )
    
    doc = attendance.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.attendance.insert_one(doc)
    
    # Audit log
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="PUNCH_OUT",
        entity="attendance",
        entity_id=attendance.id,
        metadata={"latitude": data.latitude, "longitude": data.longitude},
        request=request
    )
    
    return AttendanceResponse(
        id=attendance.id,
        worker_id=attendance.worker_id,
        type=attendance.type,
        latitude=attendance.latitude,
        longitude=attendance.longitude,
        timestamp=attendance.timestamp,
        is_valid=attendance.is_valid,
        remarks=attendance.remarks
    )

@api_router.get("/attendance/today")
async def get_today_attendance(current_user: dict = Depends(require_roles("worker", "admin"))):
    worker_id = current_user["sub"]
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    records = await db.attendance.find({
        "worker_id": worker_id,
        "timestamp": {"$gte": today_start.isoformat()}
    }, {"_id": 0}).to_list(10)
    
    return records

# ========== Coupon Routes with RBAC ==========
@api_router.post("/coupons/create")
async def create_coupon(data: CouponCreate, request: Request, current_user: dict = Depends(require_roles("worker", "admin"))):
    worker_id = current_user["sub"]
    area_id = data.area_id or "DEF"
    
    # Validate customer name
    if not validate_customer_name(data.customer_name):
        raise HTTPException(status_code=400, detail="Invalid customer name. Only letters, spaces, dots, and hyphens allowed.")
    
    # Validate and normalize phone
    if not validate_phone(data.customer_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    normalized_phone = normalize_phone(data.customer_phone)
    last4 = get_last4_digits(normalized_phone)
    
    # Encrypt phone for storage
    encrypted_phone = encrypt_mobile(normalized_phone)
    
    # Generate unique coupon code
    code = generate_coupon_code(area_id, worker_id)
    
    # Ensure uniqueness
    while await db.coupons.find_one({"code": code}):
        code = generate_coupon_code(area_id, worker_id)
    
    coupon = Coupon(
        code=code,
        worker_id=worker_id,
        customer_name=data.customer_name,
        customer_phone=encrypted_phone,  # Store encrypted
        customer_phone_last4=last4,
        latitude=data.latitude,
        longitude=data.longitude,
        photo_url=data.photo_url,
        area_id=area_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    
    doc = coupon.model_dump()
    doc["issued_at"] = doc["issued_at"].isoformat()
    doc["expires_at"] = doc["expires_at"].isoformat() if doc["expires_at"] else None
    
    await db.coupons.insert_one(doc)
    
    # Audit log
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="COUPON_CREATED",
        entity="coupon",
        entity_id=coupon.id,
        metadata={"code": code, "customer_name": data.customer_name},
        request=request
    )
    
    # Return response based on role (worker sees full phone for own coupons)
    return CouponResponseWorker(
        id=coupon.id,
        code=coupon.code,
        customer_name=coupon.customer_name,
        customer_phone=normalized_phone,  # Return unencrypted for creator
        status=coupon.status,
        latitude=coupon.latitude,
        longitude=coupon.longitude,
        photo_url=coupon.photo_url,
        area_id=coupon.area_id,
        issued_at=coupon.issued_at,
        redeemed_at=coupon.redeemed_at
    )

@api_router.get("/coupons")
async def get_coupons(
    status: Optional[str] = None,
    search: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get coupons with role-based data visibility:
    - Admin/CRE: See all coupons with full mobile numbers
    - Worker: See only own coupons with full mobile
    - Branch: See assigned coupons with masked mobile (last 4 digits only)
    """
    query = {}
    role = current_user["role"]
    
    # Role-based query filtering
    if role == "worker":
        query["worker_id"] = current_user["sub"]
    elif role == "branch":
        # Branch sees only coupons linked to their bookings
        user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
        if user and user.get("branch_id"):
            # Get booking IDs for this branch
            bookings = await db.bookings.find({"branch_id": user["branch_id"]}, {"coupon_id": 1}).to_list(1000)
            coupon_ids = [b["coupon_id"] for b in bookings if b.get("coupon_id")]
            query["id"] = {"$in": coupon_ids}
    # Admin/CRE see all
    
    if status:
        query["status"] = status
    
    # Search functionality
    if search:
        # Audit search query
        await create_audit_log(
            user_id=current_user["sub"],
            user_role=role,
            action="SEARCH_QUERY",
            entity="coupon",
            metadata={"search_term": search},
            request=request
        )
        
        # Search by name, code, or last 4 digits
        query["$or"] = [
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"customer_phone_last4": {"$regex": search}}
        ]
    
    coupons = await db.coupons.find(query, {"_id": 0}).sort("issued_at", -1).to_list(100)
    
    # Format response based on role
    results = []
    for c in coupons:
        if isinstance(c.get("issued_at"), str):
            c["issued_at"] = datetime.fromisoformat(c["issued_at"])
        if isinstance(c.get("redeemed_at"), str):
            c["redeemed_at"] = datetime.fromisoformat(c["redeemed_at"])
        if isinstance(c.get("expires_at"), str):
            c["expires_at"] = datetime.fromisoformat(c["expires_at"])
        
        if role in ["admin", "cre"]:
            # Full access - decrypt mobile
            decrypted_phone = decrypt_mobile(c.get("customer_phone", ""))
            results.append(CouponResponseFull(
                id=c["id"],
                code=c["code"],
                worker_id=c["worker_id"],
                customer_name=c["customer_name"],
                customer_phone=decrypted_phone,
                status=c["status"],
                latitude=c.get("latitude"),
                longitude=c.get("longitude"),
                photo_url=c.get("photo_url"),
                area_id=c.get("area_id"),
                booking_id=c.get("booking_id"),
                issued_at=c["issued_at"],
                redeemed_at=c.get("redeemed_at"),
                expires_at=c.get("expires_at")
            ))
        elif role == "branch":
            # Masked access - only last 4 digits
            results.append(CouponResponseMasked(
                id=c["id"],
                code=c["code"],
                customer_name=c["customer_name"],
                mobile_last4=mask_mobile(c.get("customer_phone_last4", "")),
                status=c["status"],
                issued_at=c["issued_at"],
                redeemed_at=c.get("redeemed_at")
            ))
        else:  # Worker
            decrypted_phone = decrypt_mobile(c.get("customer_phone", ""))
            results.append(CouponResponseWorker(
                id=c["id"],
                code=c["code"],
                customer_name=c["customer_name"],
                customer_phone=decrypted_phone,
                status=c["status"],
                latitude=c.get("latitude"),
                longitude=c.get("longitude"),
                photo_url=c.get("photo_url"),
                area_id=c.get("area_id"),
                issued_at=c["issued_at"],
                redeemed_at=c.get("redeemed_at")
            ))
    
    return results

@api_router.get("/coupons/{coupon_id}")
async def get_coupon(coupon_id: str, current_user: dict = Depends(get_current_user)):
    coupon = await db.coupons.find_one({"id": coupon_id}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    role = current_user["role"]
    
    # Permission check
    if role == "worker" and coupon["worker_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied to this coupon")
    
    if isinstance(coupon.get("issued_at"), str):
        coupon["issued_at"] = datetime.fromisoformat(coupon["issued_at"])
    if isinstance(coupon.get("redeemed_at"), str):
        coupon["redeemed_at"] = datetime.fromisoformat(coupon["redeemed_at"])
    if isinstance(coupon.get("expires_at"), str):
        coupon["expires_at"] = datetime.fromisoformat(coupon["expires_at"])
    
    decrypted_phone = decrypt_mobile(coupon.get("customer_phone", ""))
    
    if role in ["admin", "cre"]:
        return CouponResponseFull(
            id=coupon["id"],
            code=coupon["code"],
            worker_id=coupon["worker_id"],
            customer_name=coupon["customer_name"],
            customer_phone=decrypted_phone,
            status=coupon["status"],
            latitude=coupon.get("latitude"),
            longitude=coupon.get("longitude"),
            photo_url=coupon.get("photo_url"),
            area_id=coupon.get("area_id"),
            booking_id=coupon.get("booking_id"),
            issued_at=coupon["issued_at"],
            redeemed_at=coupon.get("redeemed_at"),
            expires_at=coupon.get("expires_at")
        )
    elif role == "branch":
        return CouponResponseMasked(
            id=coupon["id"],
            code=coupon["code"],
            customer_name=coupon["customer_name"],
            mobile_last4=mask_mobile(coupon.get("customer_phone_last4", "")),
            status=coupon["status"],
            issued_at=coupon["issued_at"],
            redeemed_at=coupon.get("redeemed_at")
        )
    else:
        return CouponResponseWorker(
            id=coupon["id"],
            code=coupon["code"],
            customer_name=coupon["customer_name"],
            customer_phone=decrypted_phone,
            status=coupon["status"],
            latitude=coupon.get("latitude"),
            longitude=coupon.get("longitude"),
            photo_url=coupon.get("photo_url"),
            area_id=coupon.get("area_id"),
            issued_at=coupon["issued_at"],
            redeemed_at=coupon.get("redeemed_at")
        )

@api_router.post("/coupons/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    # Find coupon by code
    coupon = await db.coupons.find_one({"code": data.coupon_code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    if coupon["status"] != "ACTIVE":
        raise HTTPException(status_code=400, detail=f"Coupon is {coupon['status']}, cannot redeem")
    
    # Verify phone matches (compare with decrypted)
    decrypted_phone = decrypt_mobile(coupon.get("customer_phone", ""))
    normalized_input = normalize_phone(data.phone)
    
    if decrypted_phone != normalized_input:
        raise HTTPException(status_code=400, detail="Phone number does not match")
    
    # Generate and store OTP
    otp = store_otp(data.phone, data.coupon_code)
    
    # In MVP, we log the OTP (in production, send via SMS)
    logger.info(f"[MOCK OTP] Coupon: {data.coupon_code}, Phone: {data.phone}, OTP: {otp}")
    
    return {"message": "OTP sent successfully", "mock_otp": otp}  # Remove mock_otp in production

@api_router.post("/coupons/verify-otp")
async def verify_otp_route(data: OTPVerify, request: Request):
    # Find coupon
    coupon = await db.coupons.find_one({"code": data.coupon_code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    if coupon["status"] != "ACTIVE":
        raise HTTPException(status_code=400, detail=f"Coupon is {coupon['status']}, cannot redeem")
    
    # Verify OTP
    if not verify_otp(data.phone, data.coupon_code, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Update coupon status
    await db.coupons.update_one(
        {"code": data.coupon_code},
        {"$set": {
            "status": "REDEEMED",
            "redeemed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Audit log
    await create_audit_log(
        user_id="customer",
        user_role="customer",
        action="COUPON_REDEEMED",
        entity="coupon",
        entity_id=coupon["id"],
        metadata={"code": data.coupon_code},
        request=request
    )
    
    return {"message": "Coupon redeemed successfully", "coupon_id": coupon["id"]}

# ========== Booking Routes with RBAC ==========
@api_router.post("/bookings", response_model=BookingResponse)
async def create_booking(data: BookingCreate, request: Request):
    # Get coupon info
    coupon = await db.coupons.find_one({"id": data.coupon_id}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    if coupon["status"] != "REDEEMED":
        raise HTTPException(status_code=400, detail="Coupon must be redeemed first")
    
    decrypted_phone = decrypt_mobile(coupon.get("customer_phone", ""))
    
    booking = Booking(
        coupon_id=data.coupon_id,
        customer_name=coupon["customer_name"],
        customer_phone=decrypted_phone,
        service_type=data.service_type,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        notes=data.notes
    )
    
    doc = booking.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    
    await db.bookings.insert_one(doc)
    
    # Update coupon with booking_id
    await db.coupons.update_one(
        {"id": data.coupon_id},
        {"$set": {"booking_id": booking.id}}
    )
    
    # Audit log
    await create_audit_log(
        user_id="customer",
        user_role="customer",
        action="BOOKING_CREATED",
        entity="booking",
        entity_id=booking.id,
        metadata={"coupon_id": data.coupon_id, "service_type": data.service_type},
        request=request
    )
    
    return BookingResponse(**booking.model_dump())

@api_router.get("/bookings")
async def get_bookings(
    status: Optional[str] = None,
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    role = current_user["role"]
    
    # Branch managers see only their branch bookings
    if role == "branch":
        user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
        if user and user.get("branch_id"):
            query["branch_id"] = user["branch_id"]
    elif branch_id:
        query["branch_id"] = branch_id
    
    if status:
        query["status"] = status
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    results = []
    for b in bookings:
        if isinstance(b.get("created_at"), str):
            b["created_at"] = datetime.fromisoformat(b["created_at"])
        for field in ["assigned_at", "dispatched_at", "completed_at"]:
            if isinstance(b.get(field), str):
                b[field] = datetime.fromisoformat(b[field])
        
        if role == "branch":
            # Masked response for branch
            results.append(BookingResponseMasked(
                id=b["id"],
                coupon_id=b["coupon_id"],
                customer_name=b["customer_name"],
                mobile_last4=mask_mobile(b.get("customer_phone", "")[-4:] if b.get("customer_phone") else ""),
                service_type=b["service_type"],
                address=b["address"],
                status=b["status"],
                branch_id=b.get("branch_id"),
                assigned_at=b.get("assigned_at"),
                dispatched_at=b.get("dispatched_at"),
                completed_at=b.get("completed_at"),
                notes=b.get("notes"),
                created_at=b["created_at"]
            ))
        else:
            results.append(BookingResponse(**b))
    
    return results

@api_router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str, current_user: dict = Depends(get_current_user)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    role = current_user["role"]
    
    if isinstance(booking.get("created_at"), str):
        booking["created_at"] = datetime.fromisoformat(booking["created_at"])
    for field in ["assigned_at", "dispatched_at", "completed_at"]:
        if isinstance(booking.get(field), str):
            booking[field] = datetime.fromisoformat(booking[field])
    
    if role == "branch":
        return BookingResponseMasked(
            id=booking["id"],
            coupon_id=booking["coupon_id"],
            customer_name=booking["customer_name"],
            mobile_last4=mask_mobile(booking.get("customer_phone", "")[-4:] if booking.get("customer_phone") else ""),
            service_type=booking["service_type"],
            address=booking["address"],
            status=booking["status"],
            branch_id=booking.get("branch_id"),
            assigned_at=booking.get("assigned_at"),
            dispatched_at=booking.get("dispatched_at"),
            completed_at=booking.get("completed_at"),
            notes=booking.get("notes"),
            created_at=booking["created_at"]
        )
    
    return BookingResponse(**booking)

@api_router.patch("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    data: BookingStatusUpdate,
    request: Request,
    current_user: dict = Depends(require_roles("admin", "cre", "branch"))
):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = {"status": data.status}
    
    if data.notes:
        update_data["notes"] = data.notes
    if data.completion_photo_url:
        update_data["completion_photo_url"] = data.completion_photo_url
    
    # Set timestamps based on status
    now = datetime.now(timezone.utc).isoformat()
    if data.status == "DISPATCHED":
        update_data["dispatched_at"] = now
    elif data.status == "COMPLETED":
        update_data["completed_at"] = now
        # Mark coupon as utilized
        await db.coupons.update_one(
            {"id": booking["coupon_id"]},
            {"$set": {"status": "UTILIZED"}}
        )
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
    # Audit log
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="BOOKING_UPDATED",
        entity="booking",
        entity_id=booking_id,
        metadata={"new_status": data.status},
        request=request
    )
    
    updated = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if isinstance(updated.get("created_at"), str):
        updated["created_at"] = datetime.fromisoformat(updated["created_at"])
    for field in ["assigned_at", "dispatched_at", "completed_at"]:
        if isinstance(updated.get(field), str):
            updated[field] = datetime.fromisoformat(updated[field])
    
    return BookingResponse(**updated)

@api_router.patch("/bookings/{booking_id}/assign")
async def assign_branch(
    booking_id: str,
    data: BranchAssign,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))  # Only admin can assign
):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    branch = await db.branches.find_one({"id": data.branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "branch_id": data.branch_id,
            "status": "ASSIGNED",
            "assigned_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Audit log
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="BOOKING_UPDATED",
        entity="booking",
        entity_id=booking_id,
        metadata={"branch_id": data.branch_id, "action": "branch_assigned"},
        request=request
    )
    
    updated = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if isinstance(updated.get("created_at"), str):
        updated["created_at"] = datetime.fromisoformat(updated["created_at"])
    for field in ["assigned_at", "dispatched_at", "completed_at"]:
        if isinstance(updated.get(field), str):
            updated[field] = datetime.fromisoformat(updated[field])
    
    return BookingResponse(**updated)

# ========== Branch Routes ==========
@api_router.post("/branches", response_model=BranchResponse)
async def create_branch(data: BranchCreate, request: Request, current_user: dict = Depends(require_roles("admin"))):
    branch = Branch(**data.model_dump())
    
    doc = branch.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    
    await db.branches.insert_one(doc)
    
    # Audit log
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_CREATED",
        entity="branch",
        entity_id=branch.id,
        metadata={"name": branch.name},
        request=request
    )
    
    return BranchResponse(**branch.model_dump())

@api_router.get("/branches", response_model=List[BranchResponse])
async def get_branches(current_user: dict = Depends(get_current_user)):
    branches = await db.branches.find({}, {"_id": 0}).to_list(100)
    
    for b in branches:
        if isinstance(b.get("created_at"), str):
            b["created_at"] = datetime.fromisoformat(b["created_at"])
    
    return branches

@api_router.get("/branches/nearest")
async def get_nearest_branch(latitude: float, longitude: float, current_user: dict = Depends(get_current_user)):
    branches = await db.branches.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    if not branches:
        raise HTTPException(status_code=404, detail="No branches found")
    
    nearest = find_nearest_branch(branches, latitude, longitude)
    return nearest

# ========== Task Routes ==========
@api_router.post("/tasks", response_model=TaskResponse)
async def create_task(data: TaskCreate, current_user: dict = Depends(require_roles("admin"))):
    task = Task(**data.model_dump())
    
    doc = task.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    if doc["due_date"]:
        doc["due_date"] = doc["due_date"].isoformat()
    
    await db.tasks.insert_one(doc)
    
    return TaskResponse(**task.model_dump())

@api_router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(current_user: dict = Depends(get_current_user)):
    query = {}
    
    if current_user["role"] == "worker":
        query["worker_id"] = current_user["sub"]
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for t in tasks:
        if isinstance(t.get("created_at"), str):
            t["created_at"] = datetime.fromisoformat(t["created_at"])
        if isinstance(t.get("due_date"), str):
            t["due_date"] = datetime.fromisoformat(t["due_date"])
        if isinstance(t.get("completed_at"), str):
            t["completed_at"] = datetime.fromisoformat(t["completed_at"])
    
    return tasks

@api_router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user: dict = Depends(require_roles("worker", "admin"))
):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {}
    if data.status:
        update_data["status"] = data.status
        if data.status == "COMPLETED":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    if data.remarks:
        update_data["remarks"] = data.remarks
    if data.photo_url:
        update_data["photo_url"] = data.photo_url
    
    await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if isinstance(updated.get("created_at"), str):
        updated["created_at"] = datetime.fromisoformat(updated["created_at"])
    if isinstance(updated.get("due_date"), str):
        updated["due_date"] = datetime.fromisoformat(updated["due_date"])
    if isinstance(updated.get("completed_at"), str):
        updated["completed_at"] = datetime.fromisoformat(updated["completed_at"])
    
    return updated

# ========== Location Routes ==========
@api_router.post("/location/update")
async def update_location(data: LocationUpdate, current_user: dict = Depends(require_roles("worker"))):
    log = LocationLog(
        worker_id=current_user["sub"],
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy
    )
    
    doc = log.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    
    await db.location_logs.insert_one(doc)
    
    return {"message": "Location updated"}

@api_router.get("/location/workers")
async def get_worker_locations(current_user: dict = Depends(require_roles("admin", "cre", "branch"))):
    # Get latest location for each worker
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": "$worker_id",
            "latitude": {"$first": "$latitude"},
            "longitude": {"$first": "$longitude"},
            "timestamp": {"$first": "$timestamp"}
        }},
        {"$project": {"_id": 0, "worker_id": "$_id", "latitude": 1, "longitude": 1, "timestamp": 1}}
    ]
    
    locations = await db.location_logs.aggregate(pipeline).to_list(100)
    
    # Get worker names
    for loc in locations:
        worker = await db.users.find_one({"id": loc["worker_id"]}, {"_id": 0, "name": 1})
        loc["name"] = worker["name"] if worker else "Unknown"
    
    return locations

# ========== Dashboard Routes ==========
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(require_roles("admin", "cre"))):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total workers
    total_workers = await db.users.count_documents({"role": "worker"})
    
    # Active workers (punched in today)
    active_workers = await db.attendance.count_documents({
        "type": "PUNCH_IN",
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    # Total coupons today
    total_coupons_today = await db.coupons.count_documents({
        "issued_at": {"$gte": today_start.isoformat()}
    })
    
    # Redeemed coupons today
    redeemed_today = await db.coupons.count_documents({
        "issued_at": {"$gte": today_start.isoformat()},
        "status": {"$in": ["REDEEMED", "UTILIZED"]}
    })
    
    redemption_rate = (redeemed_today / total_coupons_today * 100) if total_coupons_today > 0 else 0
    attendance_rate = (active_workers / total_workers * 100) if total_workers > 0 else 0
    
    # Bookings
    pending_bookings = await db.bookings.count_documents({"status": {"$in": ["PENDING", "ASSIGNED"]}})
    completed_bookings = await db.bookings.count_documents({"status": "COMPLETED"})
    
    # Branches
    total_branches = await db.branches.count_documents({})
    
    return DashboardStats(
        total_workers=total_workers,
        active_workers=active_workers,
        total_coupons_today=total_coupons_today,
        redemption_rate=round(redemption_rate, 1),
        attendance_rate=round(attendance_rate, 1),
        pending_bookings=pending_bookings,
        completed_bookings=completed_bookings,
        total_branches=total_branches
    )

# ========== Audit Log Routes (Admin/CRE only) ==========
@api_router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = None,
    entity: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    query = {}
    if action:
        query["action"] = action
    if entity:
        query["entity"] = entity
    if user_id:
        query["user_id"] = user_id
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    
    for log in logs:
        if isinstance(log.get("timestamp"), str):
            log["timestamp"] = datetime.fromisoformat(log["timestamp"])
    
    return logs

# ========== Worker Management Routes ==========
@api_router.get("/workers", response_model=List[UserResponse])
async def get_workers(current_user: dict = Depends(require_roles("admin", "cre"))):
    workers = await db.users.find({"role": "worker"}, {"_id": 0, "password_hash": 0}).to_list(100)
    return workers

@api_router.patch("/workers/{worker_id}")
async def update_worker(
    worker_id: str,
    area_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))  # Only admin can manage users
):
    update_data = {}
    if area_id is not None:
        update_data["area_id"] = area_id
    if branch_id is not None:
        update_data["branch_id"] = branch_id
    if is_active is not None:
        update_data["is_active"] = is_active
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    result = await db.users.update_one({"id": worker_id, "role": "worker"}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Audit log
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_UPDATED",
        entity="user",
        entity_id=worker_id,
        metadata=update_data,
        request=request
    )
    
    return {"message": "Worker updated successfully"}

# ========== User Management (Admin only) ==========
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(require_roles("admin"))):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    return users

# ========== File Upload ==========
@api_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    # Generate unique filename
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    
    # Save file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Audit log
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="PHOTO_UPLOADED",
        entity="file",
        entity_id=filename,
        request=request
    )
    
    # Return URL
    return {"url": f"/uploads/{filename}"}

# ========== Health Check ==========
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "2.0.0"}

# Include the router
app.include_router(api_router)

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
