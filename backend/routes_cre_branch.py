"""
CRE Routes - Customer call management and remarks
Branch Routes - Coupon encashment
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from models import (
    CRECallLog, CRECallLogCreate, CRECallLogRemarks, CRECallLogResponse,
    CRECustomerView, CREDashboardStats,
    EncashmentRequest, EncashmentResponse, EncashmentRecord,
    BranchCustomerView, AdminCRERemarkView, AdminEncashmentView
)
from auth import get_current_user, require_roles, mask_mobile

router = APIRouter(prefix="/api", tags=["CRE & Branch"])

db = None
create_audit_log = None

def init_routes(database, audit_func):
    global db, create_audit_log
    db = database
    create_audit_log = audit_func


# ========== CRE Dashboard Stats ==========
@router.get("/cre/dashboard/stats", response_model=CREDashboardStats)
async def get_cre_dashboard_stats(
    current_user: dict = Depends(require_roles("cre"))
):
    """Get CRE dashboard statistics"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # Total customers assigned today (sold coupons)
    total_customers = await db.campaign_coupons.count_documents({
        "status": "SOLD",
        "sold_at": {"$gte": today_start}
    })
    
    # Calls made today by this CRE
    calls_made = await db.cre_call_logs.count_documents({
        "cre_id": current_user["sub"],
        "call_timestamp": {"$gte": today_start}
    })
    
    # Pending calls (sold coupons without any call log)
    all_sold_ids = await db.campaign_coupons.distinct("id", {"status": "SOLD"})
    called_ids = await db.cre_call_logs.distinct("coupon_id")
    pending_calls = len(set(all_sold_ids) - set(called_ids))
    
    return CREDashboardStats(
        today_total_customers=total_customers,
        today_calls_made=calls_made,
        pending_calls=pending_calls
    )


# ========== CRE Customer List ==========
@router.get("/cre/customers", response_model=List[CRECustomerView])
async def get_cre_customers(
    pending_only: bool = False,
    limit: int = 100,
    current_user: dict = Depends(require_roles("cre"))
):
    """Get customers for CRE to call - Full mobile visible"""
    from utils import decrypt_mobile
    
    query = {"status": "SOLD"}
    coupons = await db.campaign_coupons.find(query, {"_id": 0}).sort("sold_at", -1).to_list(limit)
    
    results = []
    for coupon in coupons:
        # Get campaign info
        campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0})
        campaign_name = campaign["name"] if campaign else "Unknown"
        
        # Get branch info
        branch = await db.branches.find_one({"id": coupon.get("branch_id")}, {"_id": 0})
        branch_name = branch["name"] if branch else "Not Assigned"
        
        # Get last call log
        last_call = await db.cre_call_logs.find_one(
            {"coupon_id": coupon["id"]},
            {"_id": 0},
            sort=[("call_timestamp", -1)]
        )
        
        # Skip if pending_only and already called
        if pending_only and last_call:
            continue
        
        # Decrypt phone for CRE (full access)
        full_phone = decrypt_mobile(coupon.get("customer_phone", ""))
        
        if isinstance(coupon.get("sold_at"), str):
            coupon["sold_at"] = datetime.fromisoformat(coupon["sold_at"])
        
        results.append(CRECustomerView(
            coupon_id=coupon["id"],
            coupon_code=coupon["code"],
            customer_name=coupon["customer_name"],
            customer_phone=full_phone,
            campaign_name=campaign_name,
            branch_id=coupon.get("branch_id", ""),
            branch_name=branch_name,
            sold_at=coupon["sold_at"],
            call_status=last_call["call_status"] if last_call else "PENDING",
            last_call_timestamp=datetime.fromisoformat(last_call["call_timestamp"]) if last_call and isinstance(last_call.get("call_timestamp"), str) else last_call.get("call_timestamp") if last_call else None,
            last_remarks=last_call.get("remarks") if last_call else None
        ))
    
    return results


# ========== CRE Log Call ==========
@router.post("/cre/calls/{coupon_id}/log")
async def log_cre_call(
    coupon_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("cre"))
):
    """Log a call made by CRE"""
    from utils import decrypt_mobile
    
    # Get coupon
    coupon = await db.campaign_coupons.find_one({"id": coupon_id}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    # Create call log
    call_log = CRECallLog(
        coupon_id=coupon_id,
        cre_id=current_user["sub"],
        customer_name=coupon["customer_name"],
        customer_phone=decrypt_mobile(coupon.get("customer_phone", "")),
        call_status="CALLED"
    )
    
    doc = call_log.model_dump()
    doc["call_timestamp"] = doc["call_timestamp"].isoformat()
    await db.cre_call_logs.insert_one(doc)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="CRE_CALL_MADE",
        entity="cre_call_log",
        entity_id=call_log.id,
        metadata={"coupon_id": coupon_id, "customer_name": coupon["customer_name"]},
        request=request
    )
    
    return {
        "call_log_id": call_log.id,
        "message": "Call logged successfully. Please add remarks."
    }


# ========== CRE Add Remarks (Mandatory) ==========
@router.post("/cre/calls/{call_log_id}/remarks")
async def add_cre_remarks(
    call_log_id: str,
    data: CRECallLogRemarks,
    request: Request,
    current_user: dict = Depends(require_roles("cre"))
):
    """Add remarks after call - MANDATORY"""
    if not data.remarks or len(data.remarks.strip()) < 3:
        raise HTTPException(status_code=400, detail="Remarks are mandatory and must be at least 3 characters")
    
    # Get call log
    call_log = await db.cre_call_logs.find_one({"id": call_log_id}, {"_id": 0})
    if not call_log:
        raise HTTPException(status_code=404, detail="Call log not found")
    
    if call_log["cre_id"] != current_user["sub"]:
        raise HTTPException(status_code=403, detail="You can only add remarks to your own calls")
    
    # Update with remarks
    now = datetime.now(timezone.utc)
    await db.cre_call_logs.update_one(
        {"id": call_log_id},
        {"$set": {
            "remarks": data.remarks.strip(),
            "remarks_timestamp": now.isoformat()
        }}
    )
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="CRE_REMARKS_ADDED",
        entity="cre_call_log",
        entity_id=call_log_id,
        metadata={"remarks": data.remarks.strip()},
        request=request
    )
    
    return {"message": "Remarks added successfully"}


# ========== CRE Call History ==========
@router.get("/cre/calls/history", response_model=List[CRECallLogResponse])
async def get_cre_call_history(
    limit: int = 50,
    current_user: dict = Depends(require_roles("cre"))
):
    """Get CRE's call history"""
    calls = await db.cre_call_logs.find(
        {"cre_id": current_user["sub"]},
        {"_id": 0}
    ).sort("call_timestamp", -1).to_list(limit)
    
    results = []
    for call in calls:
        if isinstance(call.get("call_timestamp"), str):
            call["call_timestamp"] = datetime.fromisoformat(call["call_timestamp"])
        if isinstance(call.get("remarks_timestamp"), str):
            call["remarks_timestamp"] = datetime.fromisoformat(call["remarks_timestamp"])
        
        # Get coupon code
        coupon = await db.campaign_coupons.find_one({"id": call["coupon_id"]}, {"_id": 0, "code": 1})
        
        # Get CRE name
        cre = await db.users.find_one({"id": call["cre_id"]}, {"_id": 0, "name": 1})
        
        results.append(CRECallLogResponse(
            id=call["id"],
            coupon_id=call["coupon_id"],
            coupon_code=coupon["code"] if coupon else "Unknown",
            cre_id=call["cre_id"],
            cre_name=cre["name"] if cre else "Unknown",
            customer_name=call["customer_name"],
            customer_phone=call["customer_phone"],
            call_timestamp=call["call_timestamp"],
            call_status=call["call_status"],
            remarks=call.get("remarks"),
            remarks_timestamp=call.get("remarks_timestamp")
        ))
    
    return results


# ========== Branch Customer List ==========
@router.get("/branch/customers", response_model=List[BranchCustomerView])
async def get_branch_customers(
    current_user: dict = Depends(require_roles("branch"))
):
    """Get customers assigned to this branch - Masked mobile"""
    # Get user's branch_id
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
    if not user or not user.get("branch_id"):
        raise HTTPException(status_code=400, detail="Branch not assigned to user")
    
    branch_id = user["branch_id"]
    
    # Get coupons assigned to this branch
    coupons = await db.campaign_coupons.find(
        {"branch_id": branch_id, "status": {"$in": ["SOLD", "ENCASHED"]}},
        {"_id": 0}
    ).sort("sold_at", -1).to_list(200)
    
    results = []
    for coupon in coupons:
        # Get campaign info
        campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0})
        campaign_name = campaign["name"] if campaign else "Unknown"
        
        if isinstance(coupon.get("sold_at"), str):
            coupon["sold_at"] = datetime.fromisoformat(coupon["sold_at"])
        
        # Masked mobile - last 4 digits only
        last4 = coupon.get("customer_phone_last4", "XXXX")
        
        results.append(BranchCustomerView(
            coupon_id=coupon["id"],
            coupon_code=coupon["code"],
            customer_name=coupon["customer_name"],
            mobile_last4=f"******{last4}",
            campaign_name=campaign_name,
            sold_at=coupon["sold_at"],
            status=coupon["status"]
        ))
    
    return results


# ========== Branch Encash Coupon ==========
@router.post("/branch/encash", response_model=EncashmentResponse)
async def encash_coupon(
    data: EncashmentRequest,
    request: Request,
    current_user: dict = Depends(require_roles("branch"))
):
    """Encash a coupon - Branch only"""
    code = data.coupon_code.upper().strip()
    
    # Get user's branch
    user = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
    if not user or not user.get("branch_id"):
        raise HTTPException(status_code=400, detail="Branch not assigned to user")
    
    branch_id = user["branch_id"]
    
    # Find coupon
    coupon = await db.campaign_coupons.find_one({"code": code}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon '{code}' not found")
    
    # Validate branch assignment
    if coupon.get("branch_id") != branch_id:
        raise HTTPException(status_code=403, detail="This coupon is not assigned to your branch")
    
    # Validate status
    if coupon["status"] == "AVAILABLE":
        raise HTTPException(status_code=400, detail="This coupon has not been sold yet")
    
    if coupon["status"] == "ENCASHED":
        raise HTTPException(status_code=400, detail="This coupon has already been encashed")
    
    if coupon["status"] not in ["SOLD"]:
        raise HTTPException(status_code=400, detail=f"Cannot encash coupon with status '{coupon['status']}'")
    
    # Get campaign for price
    campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=400, detail="Campaign not found")
    
    now = datetime.now(timezone.utc)
    
    # Update coupon status
    await db.campaign_coupons.update_one(
        {"id": coupon["id"]},
        {"$set": {
            "status": "ENCASHED",
            "encashed_at": now.isoformat(),
            "encashed_by": current_user["sub"]
        }}
    )
    
    # Create encashment record
    encashment = EncashmentRecord(
        coupon_id=coupon["id"],
        branch_id=branch_id,
        encashed_by=current_user["sub"],
        campaign_price=campaign["price"]
    )
    
    enc_doc = encashment.model_dump()
    enc_doc["encashed_at"] = enc_doc["encashed_at"].isoformat()
    await db.encashments.insert_one(enc_doc)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="COUPON_ENCASHED",
        entity="campaign_coupon",
        entity_id=coupon["id"],
        metadata={
            "code": code,
            "branch_id": branch_id,
            "campaign_price": campaign["price"]
        },
        request=request
    )
    
    return EncashmentResponse(
        success=True,
        coupon_id=coupon["id"],
        coupon_code=code,
        campaign_name=campaign["name"],
        campaign_price=campaign["price"],
        customer_name=coupon["customer_name"],
        encashed_at=now,
        message=f"Coupon {code} encashed successfully! Amount: ₹{campaign['price']}"
    )


# ========== Admin: View All CRE Remarks ==========
@router.get("/admin/cre-remarks", response_model=List[AdminCRERemarkView])
async def get_all_cre_remarks(
    limit: int = 100,
    current_user: dict = Depends(require_roles("admin"))
):
    """Admin view of all CRE call remarks"""
    calls = await db.cre_call_logs.find(
        {"remarks": {"$exists": True, "$ne": None}},
        {"_id": 0}
    ).sort("remarks_timestamp", -1).to_list(limit)
    
    results = []
    for call in calls:
        if isinstance(call.get("call_timestamp"), str):
            call["call_timestamp"] = datetime.fromisoformat(call["call_timestamp"])
        if isinstance(call.get("remarks_timestamp"), str):
            call["remarks_timestamp"] = datetime.fromisoformat(call["remarks_timestamp"])
        
        # Get CRE name
        cre = await db.users.find_one({"id": call["cre_id"]}, {"_id": 0, "name": 1})
        
        # Get coupon code
        coupon = await db.campaign_coupons.find_one({"id": call["coupon_id"]}, {"_id": 0, "code": 1})
        
        results.append(AdminCRERemarkView(
            id=call["id"],
            cre_id=call["cre_id"],
            cre_name=cre["name"] if cre else "Unknown",
            coupon_code=coupon["code"] if coupon else "Unknown",
            customer_name=call["customer_name"],
            customer_phone=call["customer_phone"],
            call_timestamp=call["call_timestamp"],
            remarks=call["remarks"],
            remarks_timestamp=call["remarks_timestamp"]
        ))
    
    return results


# ========== Admin: View All Encashments ==========
@router.get("/admin/encashments", response_model=List[AdminEncashmentView])
async def get_all_encashments(
    limit: int = 100,
    current_user: dict = Depends(require_roles("admin"))
):
    """Admin view of all branch encashments"""
    encashments = await db.encashments.find({}, {"_id": 0}).sort("encashed_at", -1).to_list(limit)
    
    results = []
    for enc in encashments:
        if isinstance(enc.get("encashed_at"), str):
            enc["encashed_at"] = datetime.fromisoformat(enc["encashed_at"])
        
        # Get coupon details
        coupon = await db.campaign_coupons.find_one({"id": enc["coupon_id"]}, {"_id": 0})
        
        # Get campaign
        campaign = await db.campaigns.find_one({"id": coupon["campaign_id"]}, {"_id": 0}) if coupon else None
        
        # Get branch
        branch = await db.branches.find_one({"id": enc["branch_id"]}, {"_id": 0})
        
        # Get encashed by user
        enc_user = await db.users.find_one({"id": enc["encashed_by"]}, {"_id": 0, "name": 1})
        
        results.append(AdminEncashmentView(
            id=enc["id"],
            coupon_id=enc["coupon_id"],
            coupon_code=coupon["code"] if coupon else "Unknown",
            campaign_name=campaign["name"] if campaign else "Unknown",
            campaign_price=enc["campaign_price"],
            customer_name=coupon["customer_name"] if coupon else "Unknown",
            branch_id=enc["branch_id"],
            branch_name=branch["name"] if branch else "Unknown",
            encashed_by_name=enc_user["name"] if enc_user else "Unknown",
            encashed_at=enc["encashed_at"]
        ))
    
    return results
