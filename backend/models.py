from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Literal
from datetime import datetime, timezone
import uuid

# ========== Enums as Literals ==========
UserRole = Literal["admin", "worker", "branch_manager", "customer"]
CouponStatus = Literal["ISSUED", "REDEEMED", "EXPIRED", "CANCELLED", "UTILIZED"]
BookingStatus = Literal["PENDING", "ASSIGNED", "DISPATCHED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
TaskStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "OVERDUE"]
AttendanceType = Literal["PUNCH_IN", "PUNCH_OUT"]

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
    role: UserRole = "customer"

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
    area_id: Optional[str] = None  # For workers
    branch_id: Optional[str] = None  # For branch managers

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    phone: Optional[str]
    role: str
    is_active: bool
    area_id: Optional[str] = None
    branch_id: Optional[str] = None

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

# ========== Coupon Models ==========
class CouponCreate(BaseModel):
    customer_name: str
    customer_phone: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    area_id: Optional[str] = None

class Coupon(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    code: str  # SVL-AREAID-WORKERID-RANDOM6
    worker_id: str
    customer_name: str
    customer_phone: str
    status: CouponStatus = "ISSUED"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    area_id: Optional[str] = None
    booking_id: Optional[str] = None
    issued_at: datetime = Field(default_factory=current_utc)
    redeemed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class CouponResponse(BaseModel):
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
    issued_at: datetime
    redeemed_at: Optional[datetime]
    expires_at: Optional[datetime]

class CouponRedeem(BaseModel):
    coupon_code: str
    otp: str

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

# ========== Dashboard Stats ==========
class DashboardStats(BaseModel):
    total_workers: int
    active_workers: int
    total_coupons_today: int
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
