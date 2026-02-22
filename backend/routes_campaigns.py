"""
Campaign Management Routes
- Admin can create campaigns with auto-generated coupon codes
- Workers can validate and sell coupons
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import math
import base64
import uuid
import re
from pathlib import Path
import aiohttp

from models import (
    CampaignCreate, CampaignCreateLegacy, Campaign, CampaignResponse, CampaignCoupon, CampaignCouponResponse,
    CouponValidateRequest, CouponValidateResponse,
    CouponSaleRequest, CouponSaleResponse,
    WorkerSaleRequest, WorkerSaleResponse,
    AuditAction
)
from auth import get_current_user, require_roles, get_last4_digits
from utils import encrypt_mobile, normalize_phone, validate_phone, calculate_haversine_distance

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])

# Import db from server (will be set during app initialization)
db = None
create_audit_log = None
update_worker_ledger = None
UPLOAD_DIR = None

def init_routes(database, audit_func, ledger_func, upload_dir):
    """Initialize routes with database and helpers"""
    global db, create_audit_log, update_worker_ledger, UPLOAD_DIR
    db = database
    create_audit_log = audit_func
    update_worker_ledger = ledger_func
    UPLOAD_DIR = upload_dir


def calculate_digit_padding(total_count: int) -> int:
    """Calculate required digit padding based on total count"""
    if total_count <= 0:
        return 3
    return max(3, len(str(total_count)))


def generate_coupon_code(prefix: str, serial: int, digit_padding: int) -> str:
    """Generate coupon code with proper padding"""
    return f"{prefix}{str(serial).zfill(digit_padding)}"


def parse_coupon_code(code: str) -> tuple:
    """
    Parse coupon code into prefix and number.
    Returns (prefix, number) or (None, None) if invalid.
    Example: "UT100" -> ("UT", 100)
    """
    match = re.match(r'^([A-Za-z]+)(\d+)$', code.strip())
    if match:
        return match.group(1).upper(), int(match.group(2))
    return None, None


# ========== Campaign CRUD ==========

@router.post("", response_model=CampaignResponse)
async def create_campaign(
    data: CampaignCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Create a new campaign with start-end coupon code range.
    Example: start_code="UT100", end_code="UT400" generates UT100-UT399 (300 coupons)
    """
    # Parse start and end codes
    start_prefix, start_num = parse_coupon_code(data.start_code)
    end_prefix, end_num = parse_coupon_code(data.end_code)
    
    # Validate parsing
    if start_prefix is None or end_prefix is None:
        raise HTTPException(status_code=400, detail="Invalid coupon code format. Use format like 'UT100'")
    
    # Validate same prefix
    if start_prefix != end_prefix:
        raise HTTPException(
            status_code=400, 
            detail=f"Prefix mismatch: start='{start_prefix}' vs end='{end_prefix}'. Both codes must have the same prefix."
        )
    
    # Validate end > start
    if end_num <= start_num:
        raise HTTPException(
            status_code=400, 
            detail=f"End number ({end_num}) must be greater than start number ({start_num})"
        )
    
    prefix = start_prefix
    total_count = end_num - start_num  # UT100-UT400 = 300 coupons (100,101,...,399)
    
    if total_count <= 0:
        raise HTTPException(status_code=400, detail="Total count must be positive")
    
    if total_count > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10,000 coupons per campaign allowed")
    
    # Check for duplicate prefix in active campaigns
    existing = await db.campaigns.find_one({"prefix": prefix, "status": {"$ne": "COMPLETED"}})
    if existing:
        raise HTTPException(status_code=400, detail=f"Campaign with prefix '{prefix}' already exists")
    
    # Check for overlapping coupon codes
    first_code = f"{prefix}{str(start_num).zfill(len(str(end_num)))}"
    last_code = f"{prefix}{str(end_num - 1).zfill(len(str(end_num)))}"
    
    # Check if any code in range already exists
    overlap_check = await db.campaign_coupons.find_one({
        "code": {"$regex": f"^{prefix}\\d+$"},
        "$expr": {
            "$and": [
                {"$gte": [{"$toInt": {"$substr": ["$code", len(prefix), -1]}}, start_num]},
                {"$lt": [{"$toInt": {"$substr": ["$code", len(prefix), -1]}}, end_num]}
            ]
        }
    })
    
    # Simpler overlap check - check first and last codes
    existing_first = await db.campaign_coupons.find_one({"code": first_code})
    existing_last = await db.campaign_coupons.find_one({"code": last_code})
    if existing_first or existing_last:
        raise HTTPException(
            status_code=400, 
            detail=f"Code range overlaps with existing campaign. '{first_code}' or '{last_code}' already exists."
        )
    
    digit_padding = len(str(end_num - 1))  # Use the max number's length
    
    # Create campaign
    campaign = Campaign(
        name=data.name,
        price=data.price,
        total_count=total_count,
        prefix=prefix,
        digit_padding=digit_padding,
        created_by=current_user["sub"]
    )
    
    campaign_doc = campaign.model_dump()
    campaign_doc["created_at"] = campaign_doc["created_at"].isoformat()
    campaign_doc["start_code"] = data.start_code.upper()
    campaign_doc["end_code"] = data.end_code.upper()
    campaign_doc["start_number"] = start_num
    campaign_doc["end_number"] = end_num
    await db.campaigns.insert_one(campaign_doc)
    
    # Generate all coupon codes (start to end-1, since total = end - start)
    coupon_docs = []
    for serial in range(start_num, end_num):  # end_num is exclusive
        code = generate_coupon_code(prefix, serial, digit_padding)
        coupon = CampaignCoupon(
            campaign_id=campaign.id,
            code=code,
            serial_number=serial
        )
        doc = coupon.model_dump()
        doc["created_at"] = doc["created_at"].isoformat()
        coupon_docs.append(doc)
    
    # Bulk insert coupons
    if coupon_docs:
        await db.campaign_coupons.insert_many(coupon_docs)
    
    # Audit log
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="CAMPAIGN_CREATED",
        entity="campaign",
        entity_id=campaign.id,
        metadata={
            "name": data.name,
            "prefix": prefix,
            "start_code": data.start_code.upper(),
            "end_code": data.end_code.upper(),
            "total_count": total_count,
            "price": data.price
        },
        request=request
    )
    
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        price=campaign.price,
        total_count=campaign.total_count,
        prefix=campaign.prefix,
        digit_padding=campaign.digit_padding,
        status=campaign.status,
        sold_count=0,
        available_count=total_count,
        created_by=campaign.created_by,
        created_at=campaign.created_at
    )


@router.get("", response_model=List[CampaignResponse])
async def get_campaigns(
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get all campaigns with statistics"""
    query = {}
    if status:
        query["status"] = status
    
    campaigns = await db.campaigns.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    results = []
    for c in campaigns:
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
        
        # Get sold count
        sold_count = await db.campaign_coupons.count_documents({
            "campaign_id": c["id"],
            "status": "SOLD"
        })
        
        results.append(CampaignResponse(
            id=c["id"],
            name=c["name"],
            price=c["price"],
            total_count=c["total_count"],
            prefix=c["prefix"],
            digit_padding=c["digit_padding"],
            status=c["status"],
            sold_count=sold_count,
            available_count=c["total_count"] - sold_count,
            created_by=c["created_by"],
            created_at=c["created_at"]
        ))
    
    return results


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get campaign details"""
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if isinstance(campaign.get("created_at"), str):
        campaign["created_at"] = datetime.fromisoformat(campaign["created_at"])
    
    sold_count = await db.campaign_coupons.count_documents({
        "campaign_id": campaign_id,
        "status": "SOLD"
    })
    
    return CampaignResponse(
        id=campaign["id"],
        name=campaign["name"],
        price=campaign["price"],
        total_count=campaign["total_count"],
        prefix=campaign["prefix"],
        digit_padding=campaign["digit_padding"],
        status=campaign["status"],
        sold_count=sold_count,
        available_count=campaign["total_count"] - sold_count,
        created_by=campaign["created_by"],
        created_at=campaign["created_at"]
    )


@router.get("/{campaign_id}/coupons")
async def get_campaign_coupons(
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = 1000,  # Increased from 100 to 1000 for larger campaigns
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get coupons for a campaign (NO hardcoded limit on generation)"""
    query = {"campaign_id": campaign_id}
    if status:
        query["status"] = status
    
    coupons = await db.campaign_coupons.find(query, {"_id": 0}).sort("serial_number", 1).to_list(limit)
    
    # Get campaign info
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    results = []
    for c in coupons:
        results.append({
            "id": c["id"],
            "code": c["code"],
            "serial_number": c["serial_number"],
            "status": c["status"],
            "campaign_name": campaign["name"],
            "campaign_price": campaign["price"],
            "sold_by_worker_id": c.get("sold_by_worker_id"),
            "sold_at": c.get("sold_at"),
            "customer_name": c.get("customer_name"),
            "customer_phone": c.get("customer_phone"),
            "area_id": c.get("area_id")
        })
    
    return results


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update campaign (name, status only)"""
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    update_data = {}
    if name:
        update_data["name"] = name
    if status:
        update_data["status"] = status
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    await db.campaigns.update_one({"id": campaign_id}, {"$set": update_data})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="CAMPAIGN_UPDATED",
        entity="campaign",
        entity_id=campaign_id,
        metadata=update_data,
        request=request
    )
    
    return {"message": "Campaign updated successfully"}


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete campaign (only if no sales)"""
    campaign = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check for sales
    sold_count = await db.campaign_coupons.count_documents({
        "campaign_id": campaign_id,
        "status": "SOLD"
    })
    
    if sold_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete campaign with {sold_count} sold coupons. Mark as INACTIVE instead."
        )
    
    # Delete coupons and campaign
    await db.campaign_coupons.delete_many({"campaign_id": campaign_id})
    await db.campaigns.delete_one({"id": campaign_id})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="CAMPAIGN_DELETED",
        entity="campaign",
        entity_id=campaign_id,
        metadata={"name": campaign["name"]},
        request=request
    )
    
    return {"message": "Campaign deleted successfully"}


# ========== Coupon Validation & Sale ==========

@router.post("/validate-code", response_model=CouponValidateResponse)
async def validate_coupon_code(
    data: CouponValidateRequest,
    current_user: dict = Depends(require_roles("worker", "admin"))
):
    """
    Validate if a coupon code exists and is available for sale.
    Worker enters code manually, system validates.
    """
    code = data.coupon_code.upper().strip()
    
    # Find coupon
    coupon = await db.campaign_coupons.find_one({"code": code}, {"_id": 0})
    
    if not coupon:
        return CouponValidateResponse(
            valid=False,
            message=f"Coupon code '{code}' not found in system"
        )
    
    if coupon["status"] == "SOLD":
        return CouponValidateResponse(
            valid=False,
            coupon_id=coupon["id"],
            status="SOLD",
            message=f"Coupon '{code}' has already been sold"
        )
    
    if coupon["status"] == "CANCELLED":
        return CouponValidateResponse(
            valid=False,
            coupon_id=coupon["id"],
            status="CANCELLED",
            message=f"Coupon '{code}' has been cancelled"
        )
    
    # Get campaign details
    campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0})
    if not campaign:
        return CouponValidateResponse(
            valid=False,
            message="Campaign not found for this coupon"
        )
    
    if campaign["status"] != "ACTIVE":
        return CouponValidateResponse(
            valid=False,
            campaign_id=campaign["id"],
            campaign_name=campaign["name"],
            status=campaign["status"],
            message=f"Campaign '{campaign['name']}' is not active"
        )
    
    return CouponValidateResponse(
        valid=True,
        coupon_id=coupon["id"],
        campaign_id=campaign["id"],
        campaign_name=campaign["name"],
        campaign_price=campaign["price"],
        status="AVAILABLE",
        message=f"Coupon valid! Campaign: {campaign['name']} - ₹{campaign['price']}"
    )


@router.post("/sell", response_model=CouponSaleResponse)
async def sell_coupon(
    data: CouponSaleRequest,
    request: Request,
    current_user: dict = Depends(require_roles("worker", "admin"))
):
    """
    Complete a coupon sale.
    Worker confirms: code, customer details, GPS location.
    System marks coupon as sold and updates worker ledger.
    """
    worker_id = current_user["sub"]
    code = data.coupon_code.upper().strip()
    
    # Validate GPS accuracy
    if data.gps_accuracy and data.gps_accuracy > 100:
        raise HTTPException(
            status_code=400,
            detail="GPS accuracy too low. Please move to an area with better signal."
        )
    
    # Find and validate coupon
    coupon = await db.campaign_coupons.find_one({"code": code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon code '{code}' not found")
    
    if coupon["status"] == "SOLD":
        raise HTTPException(status_code=400, detail=f"Coupon '{code}' has already been sold")
    
    if coupon["status"] == "CANCELLED":
        raise HTTPException(status_code=400, detail=f"Coupon '{code}' has been cancelled")
    
    # Get campaign
    campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0})
    if not campaign or campaign["status"] != "ACTIVE":
        raise HTTPException(status_code=400, detail="Campaign is not active")
    
    # Validate phone
    if not validate_phone(data.customer_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    normalized_phone = normalize_phone(data.customer_phone)
    encrypted_phone = encrypt_mobile(normalized_phone)
    last4 = get_last4_digits(normalized_phone)
    
    # Check location spoofing (if worker has previous location)
    last_location = await db.location_logs.find_one(
        {"worker_id": worker_id},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    
    if last_location:
        distance = calculate_haversine_distance(
            last_location["latitude"], last_location["longitude"],
            data.latitude, data.longitude
        )
        
        time_diff = (datetime.now(timezone.utc) - datetime.fromisoformat(last_location["timestamp"])).total_seconds() / 60
        
        # Flag if >50km in <10 minutes
        if distance > 50 and time_diff < 10:
            # Log spoofing alert
            spoofing_alert = {
                "id": str(uuid.uuid4()),
                "worker_id": worker_id,
                "previous_lat": last_location["latitude"],
                "previous_lng": last_location["longitude"],
                "current_lat": data.latitude,
                "current_lng": data.longitude,
                "distance_km": round(distance, 2),
                "time_diff_minutes": round(time_diff, 2),
                "alert_type": "IMPOSSIBLE_TRAVEL",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.location_spoofing_alerts.insert_one(spoofing_alert)
            
            await create_audit_log(
                user_id=worker_id,
                user_role=current_user["role"],
                action="LOCATION_SPOOFING_DETECTED",
                entity="location",
                metadata=spoofing_alert,
                request=request
            )
            
            raise HTTPException(
                status_code=400,
                detail=f"Location verification failed. Detected {round(distance, 1)}km movement in {round(time_diff, 1)} minutes."
            )
    
    # Save photo if provided
    photo_url = data.photo_url
    if data.image_base64 and not photo_url:
        try:
            img_data = base64.b64decode(
                data.image_base64.split(',')[-1] if ',' in data.image_base64 else data.image_base64
            )
            filename = f"{uuid.uuid4()}.jpg"
            filepath = UPLOAD_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(img_data)
            photo_url = f"/uploads/{filename}"
        except Exception:
            pass  # Continue without photo
    
    # Update coupon as sold
    now = datetime.now(timezone.utc)
    await db.campaign_coupons.update_one(
        {"id": coupon["id"]},
        {"$set": {
            "status": "SOLD",
            "sold_by_worker_id": worker_id,
            "sold_at": now.isoformat(),
            "customer_name": data.customer_name.strip(),
            "customer_phone": encrypted_phone,
            "customer_phone_last4": last4,
            "photo_url": photo_url,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "area_id": data.area_id,
            "ocr_confidence": data.ocr_confidence
        }}
    )
    
    # Update campaign sold count
    await db.campaigns.update_one(
        {"id": campaign["id"]},
        {"$inc": {"sold_count": 1}}
    )
    
    # Update worker ledger
    await update_worker_ledger(
        worker_id=worker_id,
        transaction_type="SALE",
        amount=campaign["price"],
        description=f"Sale: {code} - {campaign['name']}",
        reference_id=coupon["id"]
    )
    
    # Log location
    location_log = {
        "id": str(uuid.uuid4()),
        "worker_id": worker_id,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.gps_accuracy,
        "timestamp": now.isoformat()
    }
    await db.location_logs.insert_one(location_log)
    
    # Audit log
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="COUPON_SOLD",
        entity="campaign_coupon",
        entity_id=coupon["id"],
        metadata={
            "code": code,
            "campaign_name": campaign["name"],
            "campaign_price": campaign["price"],
            "customer_name": data.customer_name,
            "area_id": data.area_id
        },
        request=request
    )
    
    return CouponSaleResponse(
        success=True,
        coupon_id=coupon["id"],
        coupon_code=code,
        campaign_name=campaign["name"],
        campaign_price=campaign["price"],
        customer_name=data.customer_name.strip(),
        message=f"Coupon sold successfully! ₹{campaign['price']} added to your ledger."
    )



# ========== NEW WORKER SALE FLOW (with Branch) ==========

async def reverse_geocode(lat: float, lng: float) -> dict:
    """Use OpenStreetMap Nominatim for reverse geocoding"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&addressdetails=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "FieldFlowPro/3.0"}) as response:
                if response.status == 200:
                    data = await response.json()
                    address = data.get("address", {})
                    return {
                        "city": address.get("city") or address.get("town") or address.get("village") or address.get("county", ""),
                        "state": address.get("state", ""),
                        "area": address.get("suburb") or address.get("neighbourhood") or address.get("locality", ""),
                        "full_address": data.get("display_name", "")
                    }
    except Exception:
        pass
    return {"city": "", "state": "", "area": "", "full_address": ""}


@router.post("/worker-sale", response_model=WorkerSaleResponse)
async def worker_sale_coupon(
    data: WorkerSaleRequest,
    request: Request,
    current_user: dict = Depends(require_roles("worker"))
):
    """
    NEW Worker Sale Flow:
    1. Manual customer entry (name, phone)
    2. Photo with OCR detection
    3. Enter coupon code (validated)
    4. Select branch (mandatory)
    5. Submit
    """
    worker_id = current_user["sub"]
    code = data.coupon_code.upper().strip()
    
    # ===== VALIDATION PHASE =====
    
    # GPS accuracy check
    if data.gps_accuracy and data.gps_accuracy > 100:
        raise HTTPException(
            status_code=400,
            detail="GPS accuracy too low (>100m). Please move to an area with better signal."
        )
    
    # Validate coupon code
    coupon = await db.campaign_coupons.find_one({"code": code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon code '{code}' not found in system")
    
    if coupon["status"] == "SOLD":
        raise HTTPException(status_code=400, detail=f"Coupon '{code}' has already been sold")
    
    if coupon["status"] == "ENCASHED":
        raise HTTPException(status_code=400, detail=f"Coupon '{code}' has already been encashed")
    
    if coupon["status"] not in ["AVAILABLE"]:
        raise HTTPException(status_code=400, detail=f"Coupon '{code}' is not available for sale")
    
    # Validate campaign
    campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=400, detail="Campaign not found")
    
    if campaign["status"] != "ACTIVE":
        raise HTTPException(status_code=400, detail=f"Campaign '{campaign['name']}' is not active")
    
    # Validate branch
    branch = await db.branches.find_one({"id": data.branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=400, detail="Selected branch not found")
    
    # Validate phone
    if not validate_phone(data.customer_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    normalized_phone = normalize_phone(data.customer_phone)
    encrypted_phone = encrypt_mobile(normalized_phone)
    last4 = get_last4_digits(normalized_phone)
    
    # ===== LOCATION SPOOFING CHECK =====
    last_location = await db.location_logs.find_one(
        {"worker_id": worker_id},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    
    if last_location:
        distance = calculate_haversine_distance(
            last_location["latitude"], last_location["longitude"],
            data.latitude, data.longitude
        )
        time_diff = (datetime.now(timezone.utc) - datetime.fromisoformat(last_location["timestamp"])).total_seconds() / 60
        
        if distance > 50 and time_diff < 10:
            spoofing_alert = {
                "id": str(uuid.uuid4()),
                "worker_id": worker_id,
                "previous_lat": last_location["latitude"],
                "previous_lng": last_location["longitude"],
                "current_lat": data.latitude,
                "current_lng": data.longitude,
                "distance_km": round(distance, 2),
                "time_diff_minutes": round(time_diff, 2),
                "alert_type": "IMPOSSIBLE_TRAVEL",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.location_spoofing_alerts.insert_one(spoofing_alert)
            
            # Also create fraud alert
            fraud_alert = {
                "id": str(uuid.uuid4()),
                "alert_type": "IMPOSSIBLE_TRAVEL",
                "worker_id": worker_id,
                "severity": "HIGH",
                "details": {
                    "distance_km": round(distance, 2),
                    "time_diff_minutes": round(time_diff, 2),
                    "from_location": f"{last_location['latitude']},{last_location['longitude']}",
                    "to_location": f"{data.latitude},{data.longitude}"
                },
                "status": "ACTIVE",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.fraud_alerts.insert_one(fraud_alert)
            
            raise HTTPException(
                status_code=400,
                detail=f"Location verification failed. Detected {round(distance, 1)}km movement in {round(time_diff, 1)} minutes."
            )
    
    # ===== GPS CLUSTERING CHECK (Multiple sales from same location in 20 mins) =====
    time_threshold = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    tolerance = 0.001  # ~111 meters
    
    nearby_sales_count = await db.campaign_coupons.count_documents({
        "sold_by_worker_id": worker_id,
        "sold_at": {"$gte": time_threshold},
        "latitude": {"$gte": data.latitude - tolerance, "$lte": data.latitude + tolerance},
        "longitude": {"$gte": data.longitude - tolerance, "$lte": data.longitude + tolerance}
    })
    
    if nearby_sales_count >= 5:  # 5+ sales from same spot in 20 mins is suspicious
        fraud_alert = {
            "id": str(uuid.uuid4()),
            "alert_type": "GPS_CLUSTERING",
            "worker_id": worker_id,
            "severity": "HIGH" if nearby_sales_count >= 10 else "MEDIUM",
            "details": {
                "sales_count": nearby_sales_count,
                "time_window_minutes": 20,
                "latitude": data.latitude,
                "longitude": data.longitude
            },
            "status": "ACTIVE",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.fraud_alerts.insert_one(fraud_alert)
        # Don't block the sale, just create the alert
    
    # ===== REVERSE GEOCODING =====
    city = data.city
    state = data.state
    area_name = data.area_name
    
    if not city or not state:
        geo_data = await reverse_geocode(data.latitude, data.longitude)
        city = city or geo_data.get("city", "")
        state = state or geo_data.get("state", "")
        area_name = area_name or geo_data.get("area", "")
    
    # ===== SAVE PHOTO =====
    photo_url = None
    if data.image_base64:
        try:
            img_data = base64.b64decode(
                data.image_base64.split(',')[-1] if ',' in data.image_base64 else data.image_base64
            )
            filename = f"sale_{uuid.uuid4()}.jpg"
            filepath = UPLOAD_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(img_data)
            photo_url = f"/uploads/{filename}"
        except Exception:
            pass
    
    # ===== CHECK OCR MISMATCH =====
    ocr_warning = None
    if data.ocr_detected_name and data.ocr_detected_phone:
        name_match = data.customer_name.lower().strip() == data.ocr_detected_name.lower().strip()
        phone_match = data.customer_phone.replace(" ", "") == data.ocr_detected_phone.replace(" ", "")
        
        if not name_match or not phone_match:
            mismatches = []
            if not name_match:
                mismatches.append(f"Name: Manual='{data.customer_name}', OCR='{data.ocr_detected_name}'")
            if not phone_match:
                mismatches.append(f"Phone: Manual='{data.customer_phone}', OCR='{data.ocr_detected_phone}'")
            ocr_warning = "OCR mismatch detected: " + "; ".join(mismatches)
    
    # ===== UPDATE COUPON =====
    now = datetime.now(timezone.utc)
    
    await db.campaign_coupons.update_one(
        {"id": coupon["id"]},
        {"$set": {
            "status": "SOLD",
            "sold_by_worker_id": worker_id,
            "sold_at": now.isoformat(),
            "customer_name": data.customer_name.strip(),
            "customer_phone": encrypted_phone,
            "customer_phone_last4": last4,
            "photo_url": photo_url,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "city": city,
            "state": state,
            "area_name": area_name,
            "branch_id": data.branch_id,
            "ocr_confidence": data.ocr_confidence,
            "ocr_detected_name": data.ocr_detected_name,
            "ocr_detected_phone": data.ocr_detected_phone
        }}
    )
    
    # Update campaign sold count
    await db.campaigns.update_one(
        {"id": campaign["id"]},
        {"$inc": {"sold_count": 1}}
    )
    
    # ===== UPDATE WORKER LEDGER =====
    await update_worker_ledger(
        worker_id=worker_id,
        transaction_type="SALE",
        amount=campaign["price"],
        description=f"Sale: {code} - {campaign['name']} @ {branch['name']}",
        reference_id=coupon["id"]
    )
    
    # Log location
    location_log = {
        "id": str(uuid.uuid4()),
        "worker_id": worker_id,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "accuracy": data.gps_accuracy,
        "city": city,
        "state": state,
        "area_name": area_name,
        "timestamp": now.isoformat()
    }
    await db.location_logs.insert_one(location_log)
    
    # Audit log
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="COUPON_SOLD",
        entity="campaign_coupon",
        entity_id=coupon["id"],
        metadata={
            "code": code,
            "campaign_name": campaign["name"],
            "campaign_price": campaign["price"],
            "customer_name": data.customer_name,
            "branch_id": data.branch_id,
            "branch_name": branch["name"],
            "city": city,
            "state": state,
            "ocr_mismatch": ocr_warning is not None
        },
        request=request
    )
    
    return WorkerSaleResponse(
        success=True,
        coupon_id=coupon["id"],
        coupon_code=code,
        campaign_name=campaign["name"],
        campaign_price=campaign["price"],
        customer_name=data.customer_name.strip(),
        branch_name=branch["name"],
        message=f"Coupon sold successfully! ₹{campaign['price']} added to your ledger.",
        ocr_mismatch_warning=ocr_warning
    )



# ========== WORKER MY SALES ==========

@router.get("/worker/my-sales")
async def get_worker_sales(
    limit: int = 100,
    current_user: dict = Depends(require_roles("worker"))
):
    """
    Get all sales made by the current worker.
    Returns with Worker Name, Branch Name, Campaign Name.
    """
    worker_id = current_user["sub"]
    
    # Get worker info
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0, "name": 1})
    worker_name = worker["name"] if worker else "Unknown"
    
    # Get all sold coupons by this worker
    coupons = await db.campaign_coupons.find(
        {"sold_by_worker_id": worker_id, "status": "SOLD"},
        {"_id": 0}
    ).sort("sold_at", -1).to_list(limit)
    
    results = []
    for coupon in coupons:
        # Get campaign info
        campaign = await db.campaigns.find_one(
            {"id": coupon["campaign_id"]},
            {"_id": 0, "name": 1, "price": 1}
        )
        
        # Get branch info
        branch = None
        if coupon.get("branch_id"):
            branch = await db.branches.find_one(
                {"id": coupon["branch_id"]},
                {"_id": 0, "name": 1}
            )
        
        results.append({
            "coupon_id": coupon["id"],
            "coupon_code": coupon["code"],
            "customer_name": coupon.get("customer_name", ""),
            "customer_phone_last4": coupon.get("customer_phone_last4", ""),
            "worker_id": worker_id,
            "worker_name": worker_name,
            "branch_id": coupon.get("branch_id"),
            "branch_name": branch["name"] if branch else "N/A",
            "campaign_id": coupon["campaign_id"],
            "campaign_name": campaign["name"] if campaign else "Unknown",
            "campaign_price": campaign["price"] if campaign else 0,
            "sold_at": coupon.get("sold_at"),
            "city": coupon.get("city", ""),
            "state": coupon.get("state", "")
        })
    
    return results
