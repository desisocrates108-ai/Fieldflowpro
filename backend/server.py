from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set
import shutil
import uuid
import asyncio

from models import (
    UserCreate, UserLogin, User, UserResponse, TokenResponse,
    AttendanceCreate, Attendance, AttendanceResponse,
    CouponCreate, CouponIssue, Coupon, CouponResponseFull, CouponResponseMasked, CouponResponseWorker,
    CouponSummary, UpdatePossessionCount, CouponVerify,
    BookingCreate, Booking, BookingResponse, BookingResponseMasked, BookingStatusUpdate,
    BranchCreate, Branch, BranchResponse, BranchAssign,
    TaskCreate, Task, TaskResponse, TaskUpdate,
    LocationUpdate, LocationLog,
    DashboardStats, OTPRequest, OTPVerify,
    AuditLog, AuditLogResponse, IssuanceLog, IssuanceLogResponse
)
from auth import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, decode_token, get_current_user, require_roles,
    can_view_full_mobile, mask_mobile, get_last4_digits, get_role_permissions
)
from utils import (
    generate_coupon_code, store_otp, verify_otp, 
    find_nearest_branch, serialize_datetime,
    encrypt_mobile, decrypt_mobile, normalize_phone, validate_phone, validate_customer_name,
    calculate_haversine_distance
)

# Import new route modules
import routes_campaigns
import routes_areas
import routes_ledger
import routes_admin
import routes_cre_branch
import routes_intelligence
import routes_payments
import routes_attendance
import background_tasks

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
app = FastAPI(title="FieldFlow Pro API", version="3.1.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== WebSocket Connection Manager ==========
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, Set[WebSocket]] = {
            "admin": set(),
            "cre": set(),
            "branch": set(),
            "worker": set()
        }
    
    async def connect(self, websocket: WebSocket, role: str, user_id: str):
        await websocket.accept()
        if role not in self.active_connections:
            self.active_connections[role] = set()
        self.active_connections[role].add(websocket)
        websocket.user_id = user_id
        websocket.role = role
        logger.info(f"WebSocket connected: {role}:{user_id}")
    
    def disconnect(self, websocket: WebSocket, role: str):
        if role in self.active_connections:
            self.active_connections[role].discard(websocket)
        logger.info(f"WebSocket disconnected: {role}")
    
    async def broadcast_to_roles(self, roles: List[str], message: dict):
        """Broadcast message to specific roles"""
        for role in roles:
            if role in self.active_connections:
                disconnected = set()
                for connection in self.active_connections[role]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"WebSocket send error: {e}")
                        disconnected.add(connection)
                # Clean up disconnected
                self.active_connections[role] -= disconnected
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        for role_connections in self.active_connections.values():
            for connection in role_connections:
                if hasattr(connection, 'user_id') and connection.user_id == user_id:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        pass

manager = ConnectionManager()

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

# ========== Issuance Log Helper ==========
async def create_issuance_log(coupon_id: str, accessed_by: str, role: str, fields_accessed: List[str]):
    """Log when coupon data is accessed"""
    log = IssuanceLog(
        coupon_id=coupon_id,
        accessed_by=accessed_by,
        role=role,
        fields_accessed=fields_accessed
    )
    doc = log.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.issuance_logs.insert_one(doc)

# ========== WebSocket Endpoint ==========
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        # Verify token
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
        
        await manager.connect(websocket, role, user_id)
        
        try:
            while True:
                # Keep connection alive, handle incoming messages
                data = await websocket.receive_text()
                # Handle ping/pong for keepalive
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            manager.disconnect(websocket, role)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1008)

# ========== Auth Routes ==========
# PUBLIC SIGNUP REMOVED - Only Admin can create users via /api/admin/users endpoint

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
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
            branch_id=user.get("branch_id"),
            coupon_possession_count=user.get("coupon_possession_count", 0)
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
            branch_id=user.get("branch_id"),
            coupon_possession_count=user.get("coupon_possession_count", 0)
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
        branch_id=user.get("branch_id"),
        coupon_possession_count=user.get("coupon_possession_count", 0),
        cash_allowed=user.get("cash_allowed", True)
    )

# ========== OLD Attendance Routes (DISABLED - moved to routes_attendance.py) ==========
# The new attendance system in routes_attendance.py provides:
# - DailyAttendance model with punch-in/out times and duration tracking
# - Admin dashboard with attendance stats and reports
# - Export functionality
# - Better "IN_PROGRESS" status tracking for workers currently working

# Old routes have been commented out - use /api/attendance/* from routes_attendance.py instead

# ========== NEW: Coupon Issue Endpoint (Photo Capture) ==========
@api_router.post("/coupons/issue")
async def issue_coupon(data: CouponIssue, request: Request, current_user: dict = Depends(require_roles("worker", "admin"))):
    """
    New coupon issuance from photo capture with OCR.
    Worker clicks photo → OCR extracts name/mobile → GPS captured → Coupon created
    """
    worker_id = current_user["sub"]
    
    # Get worker info
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Check possession count
    possession_count = worker.get("coupon_possession_count", 0)
    if possession_count <= 0:
        raise HTTPException(status_code=400, detail="No coupons in possession. Please update your coupon count.")
    
    # Validate extracted data
    if not data.extracted_name or len(data.extracted_name) < 2:
        raise HTTPException(status_code=400, detail="Invalid or missing customer name")
    
    if not data.extracted_mobile or len(data.extracted_mobile) < 10:
        raise HTTPException(status_code=400, detail="Invalid or missing mobile number")
    
    # Normalize and validate phone
    normalized_phone = normalize_phone(data.extracted_mobile)
    if not validate_phone(normalized_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    last4 = get_last4_digits(normalized_phone)
    encrypted_phone = encrypt_mobile(normalized_phone)
    
    # Save image if provided
    photo_url = data.photo_url
    if data.image_base64 and not photo_url:
        try:
            # Decode and save image
            img_data = base64.b64decode(data.image_base64.split(',')[-1] if ',' in data.image_base64 else data.image_base64)
            filename = f"{uuid.uuid4()}.jpg"
            filepath = UPLOAD_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(img_data)
            photo_url = f"/uploads/{filename}"
        except Exception as e:
            logger.error(f"Image save error: {e}")
    
    # Generate unique coupon code
    area_id = worker.get("area_id", "DEF")
    code = generate_coupon_code(area_id, worker_id)
    while await db.coupons.find_one({"code": code}):
        code = generate_coupon_code(area_id, worker_id)
    
    # Get first available CRE for assignment
    cre_user = await db.users.find_one({"role": "cre", "is_active": True}, {"_id": 0, "id": 1})
    assigned_cre = cre_user["id"] if cre_user else None
    
    # Create coupon
    coupon = Coupon(
        code=code,
        worker_id=worker_id,
        customer_name=data.extracted_name.strip(),
        customer_phone=encrypted_phone,
        customer_phone_last4=last4,
        status="PENDING",  # Needs CRE verification
        latitude=data.location.get("lat"),
        longitude=data.location.get("lng"),
        photo_url=photo_url,
        area_id=area_id,
        assigned_to_cre=assigned_cre,
        ocr_confidence=data.ocr_confidence,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    
    doc = coupon.model_dump()
    doc["issued_at"] = doc["issued_at"].isoformat()
    doc["expires_at"] = doc["expires_at"].isoformat() if doc["expires_at"] else None
    
    await db.coupons.insert_one(doc)
    
    # Decrease worker's possession count
    await db.users.update_one(
        {"id": worker_id},
        {"$inc": {"coupon_possession_count": -1}}
    )
    
    # Audit log
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="COUPON_CREATED",
        entity="coupon",
        entity_id=coupon.id,
        metadata={
            "code": code,
            "customer_name": data.extracted_name,
            "ocr_confidence": data.ocr_confidence,
            "assigned_cre": assigned_cre
        },
        request=request
    )
    
    # Broadcast to CRE via WebSocket
    ws_message = {
        "type": "new_coupon",
        "data": {
            "coupon_id": coupon.id,
            "code": coupon.code,
            "customer_name": coupon.customer_name,
            "customer_phone": normalized_phone,
            "photo_url": photo_url,
            "location": {"lat": coupon.latitude, "lng": coupon.longitude},
            "ocr_confidence": coupon.ocr_confidence,
            "worker_id": worker_id,
            "issued_at": coupon.issued_at.isoformat()
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_roles(["admin", "cre"], ws_message)
    
    return {
        "coupon_id": coupon.id,
        "code": coupon.code,
        "customer_name": coupon.customer_name,
        "status": coupon.status,
        "message": "Coupon issued successfully. Pending CRE verification."
    }

# ========== Legacy Coupon Create (for backward compatibility) ==========
@api_router.post("/coupons/create")
async def create_coupon(data: CouponCreate, request: Request, current_user: dict = Depends(require_roles("worker", "admin"))):
    worker_id = current_user["sub"]
    area_id = data.area_id or "DEF"
    
    if not validate_customer_name(data.customer_name):
        raise HTTPException(status_code=400, detail="Invalid customer name")
    
    if not validate_phone(data.customer_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    normalized_phone = normalize_phone(data.customer_phone)
    last4 = get_last4_digits(normalized_phone)
    encrypted_phone = encrypt_mobile(normalized_phone)
    
    code = generate_coupon_code(area_id, worker_id)
    while await db.coupons.find_one({"code": code}):
        code = generate_coupon_code(area_id, worker_id)
    
    coupon = Coupon(
        code=code,
        worker_id=worker_id,
        customer_name=data.customer_name,
        customer_phone=encrypted_phone,
        customer_phone_last4=last4,
        status="ACTIVE",
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
    
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="COUPON_CREATED",
        entity="coupon",
        entity_id=coupon.id,
        metadata={"code": code, "customer_name": data.customer_name},
        request=request
    )
    
    return CouponResponseWorker(
        id=coupon.id,
        code=coupon.code,
        customer_name=coupon.customer_name,
        customer_phone=normalized_phone,
        status=coupon.status,
        latitude=coupon.latitude,
        longitude=coupon.longitude,
        photo_url=coupon.photo_url,
        area_id=coupon.area_id,
        ocr_confidence=coupon.ocr_confidence,
        issued_at=coupon.issued_at,
        redeemed_at=coupon.redeemed_at
    )

# ========== Coupon Summary (Worker Dashboard) ==========
@api_router.get("/coupons/summary", response_model=CouponSummary)
async def get_coupon_summary(current_user: dict = Depends(require_roles("worker", "admin"))):
    """Get worker's coupon summary for dashboard"""
    worker_id = current_user["sub"]
    
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    coupons_issued = await db.coupons.count_documents({"worker_id": worker_id})
    coupons_pending = await db.coupons.count_documents({"worker_id": worker_id, "status": "PENDING"})
    coupons_verified = await db.coupons.count_documents({"worker_id": worker_id, "status": {"$in": ["VERIFIED", "ACTIVE"]}})
    
    return CouponSummary(
        worker_id=worker_id,
        coupon_possession_count=worker.get("coupon_possession_count", 0),
        coupons_issued=coupons_issued,
        coupons_pending=coupons_pending,
        coupons_verified=coupons_verified
    )

# ========== Update Possession Count ==========
@api_router.patch("/workers/{worker_id}/coupons", response_model=dict)
async def update_possession_count(
    worker_id: str,
    data: UpdatePossessionCount,
    request: Request,
    current_user: dict = Depends(require_roles("worker", "admin"))
):
    """Worker updates their coupon possession count"""
    # Workers can only update their own count
    if current_user["role"] == "worker" and current_user["sub"] != worker_id:
        raise HTTPException(status_code=403, detail="Can only update own possession count")
    
    if data.coupon_possession_count < 0:
        raise HTTPException(status_code=400, detail="Possession count cannot be negative")
    
    result = await db.users.update_one(
        {"id": worker_id, "role": "worker"},
        {"$set": {"coupon_possession_count": data.coupon_possession_count}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="POSSESSION_UPDATED",
        entity="user",
        entity_id=worker_id,
        metadata={"new_count": data.coupon_possession_count},
        request=request
    )
    
    return {"message": "Updated successfully", "coupon_possession_count": data.coupon_possession_count}

# ========== CRE Verify Coupon ==========
@api_router.patch("/coupons/{coupon_id}/verify")
async def verify_coupon(
    coupon_id: str,
    data: CouponVerify,
    request: Request,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """CRE verifies coupon data extracted from photo"""
    coupon = await db.coupons.find_one({"id": coupon_id}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    if coupon["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Coupon is not pending verification")
    
    update_data = {
        "status": "VERIFIED" if data.verified else "CANCELLED",
        "verified_at": datetime.now(timezone.utc).isoformat()
    }
    
    if data.corrected_name:
        update_data["customer_name"] = data.corrected_name
    if data.corrected_mobile:
        normalized = normalize_phone(data.corrected_mobile)
        update_data["customer_phone"] = encrypt_mobile(normalized)
        update_data["customer_phone_last4"] = get_last4_digits(normalized)
    
    await db.coupons.update_one({"id": coupon_id}, {"$set": update_data})
    
    # If verified, make it active
    if data.verified:
        await db.coupons.update_one({"id": coupon_id}, {"$set": {"status": "ACTIVE"}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="COUPON_VERIFIED",
        entity="coupon",
        entity_id=coupon_id,
        metadata={"verified": data.verified, "notes": data.notes},
        request=request
    )
    
    # Notify via WebSocket
    ws_message = {
        "type": "coupon_verified",
        "data": {
            "coupon_id": coupon_id,
            "verified": data.verified,
            "verified_by": current_user["sub"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_roles(["admin", "cre"], ws_message)
    
    return {"message": "Coupon verified successfully" if data.verified else "Coupon cancelled", "status": update_data["status"]}

# ========== Get Coupons with Role-Based Access ==========
@api_router.get("/coupons")
async def get_coupons(
    status: Optional[str] = None,
    search: Optional[str] = None,
    pending_only: bool = False,
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    role = current_user["role"]
    
    if role == "worker":
        query["worker_id"] = current_user["sub"]
    elif role == "branch":
        user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
        if user and user.get("branch_id"):
            bookings = await db.bookings.find({"branch_id": user["branch_id"]}, {"coupon_id": 1}).to_list(1000)
            coupon_ids = [b["coupon_id"] for b in bookings if b.get("coupon_id")]
            query["id"] = {"$in": coupon_ids}
    
    if status:
        query["status"] = status
    
    if pending_only and role in ["admin", "cre"]:
        query["status"] = "PENDING"
    
    if search:
        await create_audit_log(
            user_id=current_user["sub"],
            user_role=role,
            action="SEARCH_QUERY",
            entity="coupon",
            metadata={"search_term": search},
            request=request
        )
        query["$or"] = [
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"customer_phone_last4": {"$regex": search}}
        ]
    
    coupons = await db.coupons.find(query, {"_id": 0}).sort("issued_at", -1).to_list(100)
    
    results = []
    for c in coupons:
        if isinstance(c.get("issued_at"), str):
            c["issued_at"] = datetime.fromisoformat(c["issued_at"])
        if isinstance(c.get("redeemed_at"), str):
            c["redeemed_at"] = datetime.fromisoformat(c["redeemed_at"])
        if isinstance(c.get("verified_at"), str):
            c["verified_at"] = datetime.fromisoformat(c["verified_at"])
        if isinstance(c.get("expires_at"), str):
            c["expires_at"] = datetime.fromisoformat(c["expires_at"])
        
        # Log access for sensitive data
        if role in ["admin", "cre"]:
            await create_issuance_log(
                coupon_id=c["id"],
                accessed_by=current_user["sub"],
                role=role,
                fields_accessed=["customerMobile", "location"]
            )
        
        if role in ["admin", "cre"]:
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
                assigned_to_cre=c.get("assigned_to_cre"),
                ocr_confidence=c.get("ocr_confidence", 0),
                issued_at=c["issued_at"],
                verified_at=c.get("verified_at"),
                redeemed_at=c.get("redeemed_at"),
                expires_at=c.get("expires_at")
            ))
        elif role == "branch":
            results.append(CouponResponseMasked(
                id=c["id"],
                code=c["code"],
                customer_name=c["customer_name"],
                mobile_last4=mask_mobile(c.get("customer_phone_last4", "")),
                status=c["status"],
                issued_at=c["issued_at"],
                redeemed_at=c.get("redeemed_at")
            ))
        else:
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
                ocr_confidence=c.get("ocr_confidence", 0),
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
    
    if role == "worker" and coupon["worker_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if isinstance(coupon.get("issued_at"), str):
        coupon["issued_at"] = datetime.fromisoformat(coupon["issued_at"])
    if isinstance(coupon.get("redeemed_at"), str):
        coupon["redeemed_at"] = datetime.fromisoformat(coupon["redeemed_at"])
    if isinstance(coupon.get("verified_at"), str):
        coupon["verified_at"] = datetime.fromisoformat(coupon["verified_at"])
    if isinstance(coupon.get("expires_at"), str):
        coupon["expires_at"] = datetime.fromisoformat(coupon["expires_at"])
    
    decrypted_phone = decrypt_mobile(coupon.get("customer_phone", ""))
    
    if role in ["admin", "cre"]:
        await create_issuance_log(coupon_id, current_user["sub"], role, ["customerMobile", "location"])
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
            assigned_to_cre=coupon.get("assigned_to_cre"),
            ocr_confidence=coupon.get("ocr_confidence", 0),
            issued_at=coupon["issued_at"],
            verified_at=coupon.get("verified_at"),
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
            ocr_confidence=coupon.get("ocr_confidence", 0),
            issued_at=coupon["issued_at"],
            redeemed_at=coupon.get("redeemed_at")
        )

@api_router.post("/coupons/request-otp")
async def request_otp(data: OTPRequest, request: Request):
    coupon = await db.coupons.find_one({"code": data.coupon_code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    if coupon["status"] not in ["ACTIVE", "VERIFIED"]:
        raise HTTPException(status_code=400, detail=f"Coupon is {coupon['status']}, cannot redeem")
    
    decrypted_phone = decrypt_mobile(coupon.get("customer_phone", ""))
    normalized_input = normalize_phone(data.phone)
    
    if decrypted_phone != normalized_input:
        raise HTTPException(status_code=400, detail="Phone number does not match")
    
    otp = store_otp(data.phone, data.coupon_code)
    logger.info(f"[MOCK OTP] Coupon: {data.coupon_code}, Phone: {data.phone}, OTP: {otp}")
    
    return {"message": "OTP sent successfully", "mock_otp": otp}

@api_router.post("/coupons/verify-otp")
async def verify_otp_route(data: OTPVerify, request: Request):
    coupon = await db.coupons.find_one({"code": data.coupon_code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    if coupon["status"] not in ["ACTIVE", "VERIFIED"]:
        raise HTTPException(status_code=400, detail=f"Coupon is {coupon['status']}, cannot redeem")
    
    if not verify_otp(data.phone, data.coupon_code, data.otp):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    await db.coupons.update_one(
        {"code": data.coupon_code},
        {"$set": {
            "status": "REDEEMED",
            "redeemed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
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

# ========== Booking Routes ==========
@api_router.post("/bookings", response_model=BookingResponse)
async def create_booking(data: BookingCreate, request: Request):
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
    await db.coupons.update_one({"id": data.coupon_id}, {"$set": {"booking_id": booking.id}})
    
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
    
    now = datetime.now(timezone.utc).isoformat()
    if data.status == "DISPATCHED":
        update_data["dispatched_at"] = now
    elif data.status == "COMPLETED":
        update_data["completed_at"] = now
        await db.coupons.update_one(
            {"id": booking["coupon_id"]},
            {"$set": {"status": "UTILIZED"}}
        )
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
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
    current_user: dict = Depends(require_roles("admin"))
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


@api_router.delete("/branches/{branch_id}")
async def delete_branch(
    branch_id: str,
    request: Request,
    force: bool = False,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Delete a branch.
    - Normal delete: Deactivates if has dependencies, deletes if no dependencies
    - Force delete (force=true): Deletes branch + ALL dependencies (coupons, encashments, unassigns workers)
    """
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Check dependencies
    assigned_workers = await db.users.count_documents({"branch_id": branch_id})
    sold_coupons = await db.campaign_coupons.count_documents({"branch_id": branch_id})
    encashments = await db.encashments.count_documents({"branch_id": branch_id})
    
    has_dependencies = assigned_workers > 0 or sold_coupons > 0 or encashments > 0
    deleted_data = {"branch": branch["name"]}
    
    if force and has_dependencies:
        # FORCE DELETE - remove all dependencies
        # Unassign workers from this branch
        await db.users.update_many({"branch_id": branch_id}, {"$unset": {"branch_id": ""}})
        deleted_data["workers_unassigned"] = assigned_workers
        
        # Delete coupons sold at this branch
        coupon_result = await db.campaign_coupons.delete_many({"branch_id": branch_id})
        deleted_data["coupons_deleted"] = coupon_result.deleted_count
        
        # Delete encashments at this branch
        encash_result = await db.encashments.delete_many({"branch_id": branch_id})
        deleted_data["encashments_deleted"] = encash_result.deleted_count
        
        # Delete the branch
        await db.branches.delete_one({"id": branch_id})
        
        await create_audit_log(
            user_id=current_user["sub"],
            user_role=current_user["role"],
            action="USER_DELETED",
            entity="branch",
            entity_id=branch_id,
            metadata={
                "action": "force_deleted",
                "name": branch["name"],
                "deleted_data": deleted_data
            },
            request=request
        )
        
        return {
            "message": f"Branch '{branch['name']}' FORCE DELETED with all dependencies",
            "action": "FORCE_DELETED",
            "deleted_data": deleted_data
        }
    
    if has_dependencies and not force:
        # Soft delete - deactivate only
        await db.branches.update_one(
            {"id": branch_id},
            {"$set": {"is_active": False}}
        )
        
        await create_audit_log(
            user_id=current_user["sub"],
            user_role=current_user["role"],
            action="USER_UPDATED",
            entity="branch",
            entity_id=branch_id,
            metadata={
                "action": "deactivated",
                "reason": "has_dependencies",
                "assigned_workers": assigned_workers,
                "sold_coupons": sold_coupons,
                "encashments": encashments
            },
            request=request
        )
        
        return {
            "message": "Branch deactivated (has dependencies). Use force=true to delete anyway.",
            "action": "DEACTIVATED",
            "dependencies": {
                "assigned_workers": assigned_workers,
                "sold_coupons": sold_coupons,
                "encashments": encashments
            }
        }
    else:
        # Hard delete - no dependencies
        await db.branches.delete_one({"id": branch_id})
        
        await create_audit_log(
            user_id=current_user["sub"],
            user_role=current_user["role"],
            action="USER_DELETED",
            entity="branch",
            entity_id=branch_id,
            metadata={"action": "deleted", "name": branch["name"]},
            request=request
        )
        
        return {
            "message": f"Branch '{branch['name']}' deleted permanently",
            "action": "DELETED"
        }


@api_router.get("/branches/{branch_id}/dependencies")
async def get_branch_dependencies(
    branch_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get dependencies count for a branch before deletion"""
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    assigned_workers = await db.users.count_documents({"branch_id": branch_id})
    sold_coupons = await db.campaign_coupons.count_documents({"branch_id": branch_id})
    encashments = await db.encashments.count_documents({"branch_id": branch_id})
    
    return {
        "branch_id": branch_id,
        "branch_name": branch["name"],
        "has_dependencies": assigned_workers > 0 or sold_coupons > 0 or encashments > 0,
        "dependencies": {
            "assigned_workers": assigned_workers,
            "sold_coupons": sold_coupons,
            "encashments": encashments
        }
    }


@api_router.patch("/branches/{branch_id}/activate")
async def activate_branch(
    branch_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Re-activate a deactivated branch"""
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    await db.branches.update_one(
        {"id": branch_id},
        {"$set": {"is_active": True}}
    )
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_UPDATED",
        entity="branch",
        entity_id=branch_id,
        metadata={"action": "activated"},
        request=request
    )
    
    return {"message": "Branch activated"}


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
    
    for loc in locations:
        worker = await db.users.find_one({"id": loc["worker_id"]}, {"_id": 0, "name": 1})
        loc["name"] = worker["name"] if worker else "Unknown"
    
    return locations

# ========== Dashboard Routes ==========
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: dict = Depends(require_roles("admin", "cre"))):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_workers = await db.users.count_documents({"role": "worker"})
    active_workers = await db.attendance.count_documents({
        "type": "PUNCH_IN",
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    total_coupons_today = await db.coupons.count_documents({
        "issued_at": {"$gte": today_start.isoformat()}
    })
    
    coupons_pending = await db.coupons.count_documents({"status": "PENDING"})
    
    redeemed_today = await db.coupons.count_documents({
        "issued_at": {"$gte": today_start.isoformat()},
        "status": {"$in": ["REDEEMED", "UTILIZED"]}
    })
    
    redemption_rate = (redeemed_today / total_coupons_today * 100) if total_coupons_today > 0 else 0
    attendance_rate = (active_workers / total_workers * 100) if total_workers > 0 else 0
    
    pending_bookings = await db.bookings.count_documents({"status": {"$in": ["PENDING", "ASSIGNED"]}})
    completed_bookings = await db.bookings.count_documents({"status": "COMPLETED"})
    total_branches = await db.branches.count_documents({})
    
    return DashboardStats(
        total_workers=total_workers,
        active_workers=active_workers,
        total_coupons_today=total_coupons_today,
        coupons_pending_verification=coupons_pending,
        redemption_rate=round(redemption_rate, 1),
        attendance_rate=round(attendance_rate, 1),
        pending_bookings=pending_bookings,
        completed_bookings=completed_bookings,
        total_branches=total_branches
    )

# ========== Audit Log Routes ==========
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

# ========== Issuance Logs ==========
@api_router.get("/issuance-logs", response_model=List[IssuanceLogResponse])
async def get_issuance_logs(
    coupon_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    query = {}
    if coupon_id:
        query["coupon_id"] = coupon_id
    
    logs = await db.issuance_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    
    for log in logs:
        if isinstance(log.get("timestamp"), str):
            log["timestamp"] = datetime.fromisoformat(log["timestamp"])
    
    return logs

# ========== Worker Management ==========
@api_router.get("/workers", response_model=List[UserResponse])
async def get_workers(current_user: dict = Depends(require_roles("admin", "cre"))):
    workers = await db.users.find({"role": "worker"}, {"_id": 0, "password_hash": 0}).to_list(100)
    return workers

@api_router.get("/workers/{worker_id}", response_model=UserResponse)
async def get_worker(worker_id: str, current_user: dict = Depends(get_current_user)):
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0, "password_hash": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Mask mobile for branch users
    if current_user["role"] == "branch":
        worker["phone"] = mask_mobile(worker.get("phone", ""))
    
    return worker

@api_router.patch("/workers/{worker_id}")
async def update_worker(
    worker_id: str,
    area_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
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

# ========== User Management ==========
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(require_roles("admin"))):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    return users

@api_router.patch("/users/{user_id}/branch")
async def assign_user_branch(
    user_id: str,
    branch_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Admin assigns a branch to any user (typically branch role users)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    branch = await db.branches.find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    await db.users.update_one({"id": user_id}, {"$set": {"branch_id": branch_id}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_UPDATED",
        entity="user",
        entity_id=user_id,
        metadata={"branch_id": branch_id, "branch_name": branch["name"]},
        request=request
    )
    
    return {"message": f"User assigned to branch '{branch['name']}'"}

# ========== File Upload ==========
@api_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    current_user: dict = Depends(get_current_user)
):
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="PHOTO_UPLOADED",
        entity="file",
        entity_id=filename,
        request=request
    )
    
    return {"url": f"/uploads/{filename}"}

# ========== Health Check ==========
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "version": "4.0.0"}

# ========== Initialize New Routes ==========
async def get_update_ledger_func():
    """Get the ledger update function from routes_ledger"""
    return routes_ledger.update_worker_ledger

# Initialize route modules with database and helper functions
routes_campaigns.init_routes(db, create_audit_log, routes_ledger.update_worker_ledger, UPLOAD_DIR)
routes_areas.init_routes(db, create_audit_log)
routes_ledger.init_routes(db, create_audit_log, UPLOAD_DIR)
routes_admin.init_routes(db, create_audit_log)
routes_cre_branch.init_routes(db, create_audit_log)
routes_intelligence.init_routes(db, create_audit_log)
routes_payments.init_routes(db, create_audit_log)
routes_attendance.init_routes(db, create_audit_log)
background_tasks.init_background_tasks(db)

# Include the router
app.include_router(api_router)

# Include new route routers
app.include_router(routes_campaigns.router)
app.include_router(routes_areas.router)
app.include_router(routes_ledger.router)
app.include_router(routes_admin.router)
app.include_router(routes_cre_branch.router)
app.include_router(routes_intelligence.router)
app.include_router(routes_payments.router)
app.include_router(routes_attendance.router)

# Mount uploads directory - MUST be mounted BEFORE /api routes for correct priority
# This serves static files from /uploads/* for expense bill photos, etc.
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="api_uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start background tasks
background_tasks.start_background_tasks(app)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
