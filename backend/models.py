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
    "COUPON_CREATED", "COUPON_REDEEMED", "COUPON_CANCELLED", "COUPON_VERIFIED", "COUPON_DELETED",
    "PHOTO_UPLOADED", "BOOKING_CREATED", "BOOKING_UPDATED",
    "USER_CREATED", "USER_UPDATED", "USER_DELETED", "USER_DISABLED", "PASSWORD_RESET",
    "SEARCH_QUERY", "PUNCH_IN", "PUNCH_OUT", "DATA_EXPORT",
    "COUPON_ACCESSED", "POSSESSION_UPDATED", "COUPON_SOLD", "COUPON_ENCASHED",
    "CAMPAIGN_CREATED", "CAMPAIGN_UPDATED", "CAMPAIGN_DELETED",
    "AREA_CREATED", "AREA_UPDATED",
    "ADVANCE_ADDED", "EXPENSE_SUBMITTED", "EXPENSE_APPROVED", "EXPENSE_REJECTED",
    "INACTIVITY_ALERT", "LOCATION_SPOOFING_DETECTED",
    "CRE_CALL_MADE", "CRE_REMARKS_ADDED", "CRE_CALL_LOG_DELETED",
    "FRAUD_ALERT_CREATED", "FRAUD_ALERT_RESOLVED", "FRAUD_SCAN_TRIGGERED",
    "BRANCH_DELETED", "FORCE_DELETE"
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
    cash_allowed: bool = True  # Whether worker can accept cash payments

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
    cash_allowed: bool = True

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

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
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
    start_code: str  # e.g., "UT100"
    end_code: str    # e.g., "UT400"

class CampaignCreateLegacy(BaseModel):
    """Legacy format - still supported"""
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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
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
    total_cash_collected: float = 0.0  # Cash payments
    total_qr_collected: float = 0.0    # QR/UPI payments
    total_advances: float = 0.0
    total_expenses: float = 0.0
    net_payable: float = 0.0  # revenue - advances - expenses
    last_updated: datetime = Field(default_factory=current_utc)

class WorkerLedgerResponse(BaseModel):
    worker_id: str
    worker_name: str
    total_coupons_sold: int
    total_revenue: float
    total_cash_collected: float = 0.0
    total_qr_collected: float = 0.0
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


# ========== CRE Call Log Models ==========
class CRECallLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    coupon_id: str
    cre_id: str
    customer_name: str
    customer_phone: str
    call_timestamp: datetime = Field(default_factory=current_utc)
    call_duration: Optional[int] = None  # seconds
    call_status: str = "CALLED"
    remarks: Optional[str] = None
    remarks_timestamp: Optional[datetime] = None

class CRECallLogCreate(BaseModel):
    coupon_id: str

class CRECallLogRemarks(BaseModel):
    remarks: str

class CRECallLogResponse(BaseModel):
    id: str
    coupon_id: str
    coupon_code: str
    cre_id: str
    cre_name: str
    customer_name: str
    customer_phone: str
    call_timestamp: datetime
    call_status: str
    remarks: Optional[str]
    remarks_timestamp: Optional[datetime]

# ========== Branch Encashment Models ==========
class EncashmentRequest(BaseModel):
    coupon_code: str

class EncashmentResponse(BaseModel):
    success: bool
    coupon_id: str
    coupon_code: str
    campaign_name: str
    campaign_price: float
    customer_name: str
    encashed_at: datetime
    message: str

class EncashmentRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    coupon_id: str
    branch_id: str
    encashed_by: str
    campaign_price: float
    encashed_at: datetime = Field(default_factory=current_utc)

# ========== Enhanced Sale Request (Worker) ==========
class WorkerSaleRequest(BaseModel):
    # Manual entry
    customer_name: str
    customer_phone: str
    
    # OCR detected (for comparison)
    ocr_detected_name: Optional[str] = None
    ocr_detected_phone: Optional[str] = None
    ocr_confidence: float = 0.0
    
    # Coupon code (mandatory)
    coupon_code: str
    
    # Branch selection (mandatory)
    branch_id: str
    
    # Payment mode (CASH or QR)
    payment_mode: str = "CASH"  # CASH or QR
    
    # Location (OPTIONAL - sale should not be blocked by GPS)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    area_name: Optional[str] = None
    
    # Photo
    image_base64: Optional[str] = None

class WorkerSaleResponse(BaseModel):
    success: bool
    coupon_id: str
    coupon_code: str
    campaign_name: str
    campaign_price: float
    customer_name: str
    branch_name: str
    message: str
    ocr_mismatch_warning: Optional[str] = None

# ========== CRE Customer View ==========
class CRECustomerView(BaseModel):
    coupon_id: str
    coupon_code: str
    customer_name: str
    customer_phone: str  # Full phone for CRE
    campaign_name: str
    branch_id: str
    branch_name: str
    worker_name: Optional[str] = None
    sold_at: datetime
    call_status: str
    last_call_timestamp: Optional[datetime]
    last_remarks: Optional[str]
    last_call_log_id: Optional[str] = None

# ========== CRE Dashboard Stats ==========
class CREDashboardStats(BaseModel):
    today_total_customers: int
    today_calls_made: int
    pending_calls: int

# ========== Branch Customer View ==========
class BranchCustomerView(BaseModel):
    coupon_id: str
    coupon_code: str
    customer_name: str
    mobile_last4: str  # Masked for branch
    campaign_name: str
    sold_at: datetime
    status: str  # SOLD or ENCASHED

# ========== Admin Ledger View ==========
class AdminLedgerView(BaseModel):
    worker_id: str
    worker_name: str
    worker_email: str
    worker_phone: Optional[str]
    total_coupons_sold: int
    total_revenue: float
    total_expenses: float
    total_advances: float
    net_payable: float
    last_sale_date: Optional[datetime]
    expenses_list: List[dict]  # With bill photos

# ========== Admin CRE Remarks View ==========
class AdminCRERemarkView(BaseModel):
    id: str
    cre_id: str
    cre_name: str
    coupon_code: str
    customer_name: str
    customer_phone: str
    call_timestamp: datetime
    remarks: str
    remarks_timestamp: datetime

# ========== Admin Encashment View ==========
class AdminEncashmentView(BaseModel):
    id: str
    coupon_id: str
    coupon_code: str
    campaign_name: str
    campaign_price: float
    customer_name: str
    branch_id: str
    branch_name: str
    encashed_by_name: str
    encashed_at: datetime



# ========== Elite v4.0 - Fraud Detection Models ==========
FraudAlertType = Literal[
    "DUPLICATE_MOBILE",      # Same mobile used multiple times
    "GPS_CLUSTERING",        # Multiple sales from same GPS in short time
    "IMPOSSIBLE_TRAVEL",     # GPS jump >50km in <10 mins
    "HIGH_EXPENSE_RATIO",    # Expense to revenue ratio too high
    "PATTERN_MANIPULATION",  # Coupon code pattern manipulation
    "GPS_ACCURACY_LOW"       # Consistently low GPS accuracy
]

FraudAlertStatus = Literal["ACTIVE", "RESOLVED", "DISMISSED"]
FraudSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

class FraudAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    alert_type: str
    worker_id: str
    severity: str = "MEDIUM"
    details: dict = {}
    related_entity_id: Optional[str] = None
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=current_utc)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None

class FraudAlertResponse(BaseModel):
    id: str
    alert_type: str
    worker_id: str
    worker_name: str
    severity: str
    details: dict
    related_entity_id: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]

# ========== Elite v4.0 - Worker Performance Scoring ==========
class WorkerPerformanceScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    final_score: float
    components: dict  # Individual component scores
    metrics: dict     # Raw metrics used
    grade: str
    calculated_at: datetime = Field(default_factory=current_utc)

class WorkerPerformanceResponse(BaseModel):
    worker_id: str
    worker_name: str
    final_score: float
    components: dict
    metrics: dict
    grade: str
    calculated_at: str
    rank: Optional[int] = None

# ========== Elite v4.0 - Real-Time Metrics ==========
class RealTimeMetrics(BaseModel):
    live_sales_today: int
    live_revenue_today: float
    active_workers_now: int
    total_punched_in_today: int
    inactive_worker_alerts: int
    fraud_alerts_active: int
    pending_expenses: int
    encashments_today: int
    last_updated: str

# ========== Elite v4.0 - Area Intelligence ==========
class AreaIntelligence(BaseModel):
    sales_by_city: List[dict]
    sales_by_state: List[dict]
    campaign_by_geography: List[dict]
    top_areas: List[dict]
    generated_at: str



# ========== Daily Attendance Models ==========
class DailyAttendance(BaseModel):
    """Tracks daily attendance with punch-in/out times and duration"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    worker_id: str
    date: str  # YYYY-MM-DD format
    punch_in_time: Optional[datetime] = None
    punch_in_location: Optional[dict] = None  # {latitude, longitude}
    punch_out_time: Optional[datetime] = None
    punch_out_location: Optional[dict] = None
    duration_minutes: Optional[int] = None  # Total working minutes
    status: str = "ABSENT"  # PRESENT, ABSENT, IN_PROGRESS

class DailyAttendanceResponse(BaseModel):
    id: str
    worker_id: str
    worker_name: str
    date: str
    punch_in_time: Optional[datetime]
    punch_out_time: Optional[datetime]
    duration_minutes: Optional[int]
    duration_formatted: Optional[str] = None  # e.g., "8h 30m"
    status: str

class AttendanceReportFilters(BaseModel):
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None
    worker_id: Optional[str] = None
    status: Optional[str] = None  # PRESENT, ABSENT, IN_PROGRESS

class AttendanceStats(BaseModel):
    total_workers: int
    present_today: int
    absent_today: int
    in_progress: int
    total_hours_today: float
