from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Literal
from datetime import datetime, timezone
import uuid

# ========== Enums as Literals ==========
UserRole = Literal["admin", "worker", "branch", "cre"]
CouponStatus = Literal["PENDING", "VERIFIED", "ACTIVE", "REDEEMED", "EXPIRED", "CANCELLED", "UTILIZED"]
BookingStatus = Literal["PENDING", "ASSIGNED", "DISPATCHED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
TaskStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "OVERDUE"]
AttendanceType = Literal["PUNCH_IN", "PUNCH_OUT"]
AuditAction = Literal[
    "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT",
    "COUPON_CREATED", "COUPON_REDEEMED", "COUPON_CANCELLED", "COUPON_VERIFIED",
    "PHOTO_UPLOADED", "BOOKING_CREATED", "BOOKING_UPDATED",
    "USER_CREATED", "USER_UPDATED", "SEARCH_QUERY",
    "PUNCH_IN", "PUNCH_OUT", "DATA_EXPORT",
    "COUPON_ACCESSED", "POSSESSION_UPDATED"
]

def generate_uuid():
    return str(uuid.uuid4())

def current_utc():
    return datetime.now(timezone.utc)

# ========== User Models ==========
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    role: UserRole = "worker"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    email: EmailStr
    name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=current_utc)
    area_id: Optional[str] = None
    branch_id: Optional[str] = None
    coupon_possession_count: int = 0  # Number of physical coupons worker has

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str]
    role: str
    is_active: bool
    area_id: Optional[str] = None
    branch_id: Optional[str] = None
    coupon_possession_count: int = 0

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

# ========== Attendance Models ==========
class AttendanceCreate(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

class Attendance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    type: AttendanceType
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: datetime = Field(default_factory=current_utc)
    is_valid: bool = True
    remarks: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: str
    worker_id: str
    type: str
    latitude: float
    longitude: float
    timestamp: datetime
    is_valid: bool
    remarks: Optional[str] = None

# ========== Photo Extraction Result ==========
class PhotoExtractionResult(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    confidence: float = 0.0

# ========== Coupon Models ==========
class CouponCreate(BaseModel):
    customer_name: str
    customer_phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    area_id: Optional[str] = None

class CouponIssue(BaseModel):
    """New coupon issuance from photo capture"""
    image_base64: Optional[str] = None  # Base64 encoded image
    extracted_name: str
    extracted_mobile: str
    location: dict  # {"lat": float, "lng": float}
    ocr_confidence: float = 0.0
    photo_url: Optional[str] = None  # URL if uploaded separately

class Coupon(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    code: str
    worker_id: str
    customer_name: str
    customer_phone: str  # Full phone (encrypted in DB)
    customer_phone_last4: str
    status: CouponStatus = "PENDING"  # Starts as PENDING, CRE verifies
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    area_id: Optional[str] = None
    booking_id: Optional[str] = None
    assigned_to_cre: Optional[str] = None  # CRE user ID
    ocr_confidence: float = 0.0
    issued_at: datetime = Field(default_factory=current_utc)
    verified_at: Optional[datetime] = None
    redeemed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

# Response models with role-based masking
class CouponResponseFull(BaseModel):
    """Full response for Admin/CRE - includes full mobile and location"""
    id: str
    code: str
    worker_id: str
    customer_name: str
    customer_phone: str
    status: str
    latitude: Optional[float]
    longitude: Optional[float]
    photo_url: Optional[str]
    area_id: Optional[str]
    booking_id: Optional[str]
    assigned_to_cre: Optional[str]
    ocr_confidence: float
    issued_at: datetime
    verified_at: Optional[datetime]
    redeemed_at: Optional[datetime]
    expires_at: Optional[datetime]

class CouponResponseMasked(BaseModel):
    """Masked response for Branch - only last 4 digits, no location"""
    id: str
    code: str
    customer_name: str
    mobile_last4: str
    status: str
    issued_at: datetime
    redeemed_at: Optional[datetime]

class CouponResponseWorker(BaseModel):
    """Response for Worker - own coupons only"""
    id: str
    code: str
    customer_name: str
    customer_phone: str
    status: str
    latitude: Optional[float]
    longitude: Optional[float]
    photo_url: Optional[str]
    area_id: Optional[str]
    ocr_confidence: float
    issued_at: datetime
    redeemed_at: Optional[datetime]

class CouponRedeem(BaseModel):
    coupon_code: str
    otp: str

class CouponVerify(BaseModel):
    """CRE verifies coupon data"""
    verified: bool
    corrected_name: Optional[str] = None
    corrected_mobile: Optional[str] = None
    notes: Optional[str] = None

# ========== Coupon Summary (Worker Dashboard) ==========
class CouponSummary(BaseModel):
    worker_id: str
    coupon_possession_count: int
    coupons_issued: int
    coupons_pending: int
    coupons_verified: int

class UpdatePossessionCount(BaseModel):
    coupon_possession_count: int

# ========== Issuance Log ==========
class IssuanceLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    coupon_id: str
    accessed_by: str  # User ID
    role: str
    fields_accessed: List[str]  # ["customerMobile", "location"]
    timestamp: datetime = Field(default_factory=current_utc)

class IssuanceLogResponse(BaseModel):
    id: str
    coupon_id: str
    accessed_by: str
    role: str
    fields_accessed: List[str]
    timestamp: datetime

# ========== Booking Models ==========
class BookingCreate(BaseModel):
    coupon_id: str
    service_type: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    coupon_id: str
    customer_name: str
    customer_phone: str
    service_type: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: BookingStatus = "PENDING"
    branch_id: Optional[str] = None
    assigned_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_photo_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=current_utc)

class BookingResponse(BaseModel):
    id: str
    coupon_id: str
    customer_name: str
    customer_phone: str
    service_type: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    branch_id: Optional[str]
    assigned_at: Optional[datetime]
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]
    completion_photo_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

class BookingResponseMasked(BaseModel):
    """Masked response for Branch"""
    id: str
    coupon_id: str
    customer_name: str
    mobile_last4: str
    service_type: str
    address: str
    status: str
    branch_id: Optional[str]
    assigned_at: Optional[datetime]
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    notes: Optional[str] = None
    completion_photo_url: Optional[str] = None

# ========== Branch Models ==========
class BranchCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    contact_phone: Optional[str] = None

class Branch(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    name: str
    address: str
    latitude: float
    longitude: float
    contact_phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=current_utc)

class BranchResponse(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    contact_phone: Optional[str]
    is_active: bool
    created_at: datetime

class BranchAssign(BaseModel):
    branch_id: str

# ========== Task Models ==========
class TaskCreate(BaseModel):
    worker_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = "PENDING"
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    remarks: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=current_utc)

class TaskResponse(BaseModel):
    id: str
    worker_id: str
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    remarks: Optional[str]
    photo_url: Optional[str]
    created_at: datetime

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    remarks: Optional[str] = None
    photo_url: Optional[str] = None

# ========== Location Log Models ==========
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

class LocationLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: datetime = Field(default_factory=current_utc)

# ========== Audit Log Models ==========
class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    user_id: str
    user_role: str
    action: AuditAction
    entity: str
    entity_id: Optional[str] = None
    metadata: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=current_utc)

class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    user_role: str
    action: str
    entity: str
    entity_id: Optional[str]
    metadata: Optional[dict]
    timestamp: datetime

# ========== Dashboard Stats ==========
class DashboardStats(BaseModel):
    total_workers: int
    active_workers: int
    total_coupons_today: int
    coupons_pending_verification: int
    redemption_rate: float
    attendance_rate: float
    pending_bookings: int
    completed_bookings: int
    total_branches: int

# ========== OTP Models ==========
class OTPRequest(BaseModel):
    coupon_code: str
    phone: str

class OTPVerify(BaseModel):
    coupon_code: str
    phone: str
    otp: str

# ========== WebSocket Message ==========
class WSMessage(BaseModel):
    type: str  # "new_coupon", "coupon_verified", etc.
    data: dict
    timestamp: datetime = Field(default_factory=current_utc)
