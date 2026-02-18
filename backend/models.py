from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Literal
from datetime import datetime, timezone
import uuid

# ========== Enums as Literals ==========
UserRole = Literal["admin", "worker", "branch", "cre"]
CouponStatus = Literal["PENDING", "VERIFIED", "ACTIVE", "REDEEMED", "EXPIRED", "CANCELLED", "UTILIZED", "AVAILABLE", "SOLD", "ENCASHED"]
BookingStatus = Literal["PENDING", "ASSIGNED", "DISPATCHED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
TaskStatus = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "OVERDUE"]
AttendanceType = Literal["PUNCH_IN", "PUNCH_OUT"]
CampaignStatus = Literal["ACTIVE", "INACTIVE", "COMPLETED"]
LedgerTransactionType = Literal["SALE", "ADVANCE", "EXPENSE", "ADJUSTMENT"]
ExpenseStatus = Literal["PENDING", "APPROVED", "REJECTED"]
InactivityStatus = Literal["ACTIVE", "RESOLVED", "DISMISSED"]
CallStatus = Literal["PENDING", "CALLED", "NO_ANSWER", "CALLBACK"]
AuditAction = Literal[
    "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT",
    "COUPON_CREATED", "COUPON_REDEEMED", "COUPON_CANCELLED", "COUPON_VERIFIED",
    "PHOTO_UPLOADED", "BOOKING_CREATED", "BOOKING_UPDATED",
    "USER_CREATED", "USER_UPDATED", "USER_DELETED", "USER_DISABLED", "PASSWORD_RESET",
    "SEARCH_QUERY", "PUNCH_IN", "PUNCH_OUT", "DATA_EXPORT",
    "COUPON_ACCESSED", "POSSESSION_UPDATED", "COUPON_SOLD", "COUPON_ENCASHED",
    "CAMPAIGN_CREATED", "CAMPAIGN_UPDATED", "CAMPAIGN_DELETED",
    "AREA_CREATED", "AREA_UPDATED",
    "ADVANCE_ADDED", "EXPENSE_SUBMITTED", "EXPENSE_APPROVED", "EXPENSE_REJECTED",
    "INACTIVITY_ALERT", "LOCATION_SPOOFING_DETECTED",
    "CRE_CALL_MADE", "CRE_REMARKS_ADDED"
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


# ========== Campaign Models ==========
class CampaignCreate(BaseModel):
    name: str
    price: float
    total_count: int
    prefix: str  # e.g., "SA", "MUM01"

class Campaign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    name: str
    price: float
    total_count: int
    prefix: str
    digit_padding: int  # Calculated based on total_count
    status: CampaignStatus = "ACTIVE"
    sold_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=current_utc)

class CampaignResponse(BaseModel):
    id: str
    name: str
    price: float
    total_count: int
    prefix: str
    digit_padding: int
    status: str
    sold_count: int
    available_count: int
    created_by: str
    created_at: datetime

class CampaignCoupon(BaseModel):
    """Individual coupon within a campaign"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    campaign_id: str
    code: str  # e.g., "SA001"
    serial_number: int
    status: str = "AVAILABLE"  # AVAILABLE, SOLD, CANCELLED
    sold_by_worker_id: Optional[str] = None
    sold_at: Optional[datetime] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_phone_last4: Optional[str] = None
    photo_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_id: Optional[str] = None
    ocr_confidence: float = 0.0
    created_at: datetime = Field(default_factory=current_utc)

class CampaignCouponResponse(BaseModel):
    id: str
    campaign_id: str
    campaign_name: str
    campaign_price: float
    code: str
    serial_number: int
    status: str
    sold_by_worker_id: Optional[str]
    sold_at: Optional[datetime]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    area_id: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

# ========== Coupon Sale (New Flow) ==========
class CouponValidateRequest(BaseModel):
    coupon_code: str

class CouponValidateResponse(BaseModel):
    valid: bool
    coupon_id: Optional[str] = None
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    campaign_price: Optional[float] = None
    status: Optional[str] = None
    message: str

class CouponSaleRequest(BaseModel):
    coupon_code: str
    customer_name: str
    customer_phone: str
    latitude: float
    longitude: float
    gps_accuracy: Optional[float] = None
    area_id: Optional[str] = None
    photo_url: Optional[str] = None
    image_base64: Optional[str] = None
    ocr_confidence: float = 0.0

class CouponSaleResponse(BaseModel):
    success: bool
    coupon_id: str
    coupon_code: str
    campaign_name: str
    campaign_price: float
    customer_name: str
    message: str

# ========== Area Models ==========
class AreaCreate(BaseModel):
    name: str
    city: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Area(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    name: str
    city: str
    state: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=current_utc)

class AreaResponse(BaseModel):
    id: str
    name: str
    city: str
    state: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_active: bool
    total_sales: int = 0
    total_revenue: float = 0.0

# ========== Worker Ledger Models ==========
class WorkerLedger(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    total_coupons_sold: int = 0
    total_revenue: float = 0.0
    total_advances: float = 0.0
    total_expenses: float = 0.0
    net_payable: float = 0.0  # revenue - advances - expenses
    last_updated: datetime = Field(default_factory=current_utc)

class WorkerLedgerResponse(BaseModel):
    worker_id: str
    worker_name: str
    total_coupons_sold: int
    total_revenue: float
    total_advances: float
    total_expenses: float
    net_payable: float
    last_updated: datetime

class LedgerTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    type: LedgerTransactionType
    amount: float
    description: str
    reference_id: Optional[str] = None  # coupon_id, expense_id, etc.
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=current_utc)

class LedgerTransactionResponse(BaseModel):
    id: str
    worker_id: str
    type: str
    amount: float
    description: str
    reference_id: Optional[str]
    created_at: datetime

class AddAdvanceRequest(BaseModel):
    amount: float
    description: Optional[str] = "Advance payment"

# ========== Expense Models ==========
class ExpenseCreate(BaseModel):
    type: str  # e.g., "Travel", "Food", "Equipment"
    amount: float
    description: Optional[str] = None
    latitude: float
    longitude: float
    bill_photo_url: Optional[str] = None
    image_base64: Optional[str] = None

class Expense(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    type: str
    amount: float
    description: Optional[str] = None
    latitude: float
    longitude: float
    bill_photo_url: Optional[str] = None
    status: ExpenseStatus = "PENDING"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=current_utc)

class ExpenseResponse(BaseModel):
    id: str
    worker_id: str
    worker_name: Optional[str] = None
    type: str
    amount: float
    description: Optional[str]
    latitude: float
    longitude: float
    bill_photo_url: Optional[str]
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime

class ExpenseApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None

# ========== Inactivity Tracking ==========
class InactivityLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    punch_in_time: datetime
    alert_time: datetime = Field(default_factory=current_utc)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hours_inactive: float = 3.0
    status: InactivityStatus = "ACTIVE"
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    notes: Optional[str] = None

class InactivityLogResponse(BaseModel):
    id: str
    worker_id: str
    worker_name: str
    punch_in_time: datetime
    alert_time: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    hours_inactive: float
    status: str
    resolved_at: Optional[datetime]
    notes: Optional[str]

# ========== Admin Worker Control ==========
class AdminWorkerCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    area_id: Optional[str] = None

class AdminWorkerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    area_id: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordResetRequest(BaseModel):
    new_password: str

# ========== Analytics Models ==========
class SalesAnalytics(BaseModel):
    total_sales: int
    total_revenue: float
    sales_by_campaign: List[dict]
    sales_by_area: List[dict]
    sales_by_worker: List[dict]
    daily_trend: List[dict]

class AreaAnalytics(BaseModel):
    area_id: str
    area_name: str
    city: str
    state: str
    total_sales: int
    total_revenue: float
    active_workers: int
    top_campaigns: List[dict]

class WorkerAnalytics(BaseModel):
    worker_id: str
    worker_name: str
    total_sales: int
    total_revenue: float
    area_name: Optional[str]
    campaigns_sold: List[dict]

# ========== Location Spoofing Detection ==========
class LocationCheck(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: datetime = Field(default_factory=current_utc)

class LocationSpoofingAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    previous_lat: float
    previous_lng: float
    current_lat: float
    current_lng: float
    distance_km: float
    time_diff_minutes: float
    alert_type: str  # "GPS_ACCURACY", "IMPOSSIBLE_TRAVEL"
    created_at: datetime = Field(default_factory=current_utc)

# ========== Enhanced Dashboard Stats ==========
class AdminDashboardStats(BaseModel):
    # Workers
    total_workers: int
    active_workers_today: int
    inactive_alerts: int
    
    # Sales
    total_sales_today: int
    total_revenue_today: float
    total_sales_month: int
    total_revenue_month: float
    
    # Campaigns
    active_campaigns: int
    total_coupons_available: int
    
    # Areas
    total_areas: int
    top_performing_area: Optional[str]
    
    # Expenses
    pending_expenses: int
    total_expenses_month: float
    
    # Financial
    total_advances_month: float
    net_payable_all_workers: float
