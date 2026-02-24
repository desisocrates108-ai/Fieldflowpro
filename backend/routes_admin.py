"""
Admin User Management, Worker Control & Inactivity Tracking Routes
- All user creation is handled by Admin (no public signup)
- Supports Worker, Branch, CRE roles
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Literal
import asyncio

from models import (
    AdminWorkerCreate, AdminWorkerUpdate, PasswordResetRequest,
    User, UserResponse,
    InactivityLog, InactivityLogResponse,
    AdminDashboardStats
)
from auth import get_current_user, require_roles, get_password_hash

router = APIRouter(prefix="/api/admin", tags=["Admin"])

db = None
create_audit_log = None

def init_routes(database, audit_func):
    global db, create_audit_log
    db = database
    create_audit_log = audit_func


# ========== User Creation Models ==========
class AdminUserCreate(BaseModel):
    """Admin creates any user type"""
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    role: Literal["worker", "branch", "cre"]
    area_id: Optional[str] = None
    branch_id: Optional[str] = None


class AdminUserUpdate(BaseModel):
    """Admin updates any user"""
    name: Optional[str] = None
    phone: Optional[str] = None
    area_id: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: Optional[bool] = None


# ========== Login Management - All User Types ==========

@router.post("/users", response_model=UserResponse)
async def create_user(
    data: AdminUserCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Admin creates a new user (Worker, Branch, or CRE).
    This is the ONLY way to create users - no public signup.
    """
    # Check email exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Create user
    user = User(
        email=data.email,
        name=data.name,
        phone=data.phone,
        role=data.role,
        area_id=data.area_id,
        branch_id=data.branch_id
    )
    
    user_dict = user.model_dump()
    user_dict["password_hash"] = get_password_hash(data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_CREATED",
        entity="user",
        entity_id=user.id,
        metadata={"email": data.email, "name": data.name, "role": data.role},
        request=request
    )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        area_id=user.area_id,
        branch_id=user.branch_id,
        coupon_possession_count=user.coupon_possession_count
    )


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get all users, optionally filtered by role and status"""
    query = {"role": {"$ne": "admin"}}  # Don't list admin users
    
    if role:
        query["role"] = role
    if is_active is not None:
        query["is_active"] = is_active
    
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get single user details"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: AdminUserUpdate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update any user's details"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent modifying admin users
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot modify admin users")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.phone is not None:
        update_data["phone"] = data.phone
    if data.area_id is not None:
        update_data["area_id"] = data.area_id
    if data.branch_id is not None:
        update_data["branch_id"] = data.branch_id
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_UPDATED",
        entity="user",
        entity_id=user_id,
        metadata=update_data,
        request=request
    )
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return updated


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    data: PasswordResetRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Reset any user's password"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent modifying admin users
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot modify admin users")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    new_hash = get_password_hash(data.new_password)
    await db.users.update_one({"id": user_id}, {"$set": {"password_hash": new_hash}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="PASSWORD_RESET",
        entity="user",
        entity_id=user_id,
        metadata={"email": user["email"], "role": user["role"]},
        request=request
    )
    
    return {"message": "Password reset successfully"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Activate a user account"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": True}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_UPDATED",
        entity="user",
        entity_id=user_id,
        metadata={"action": "activated", "email": user["email"]},
        request=request
    )
    
    return {"message": "User activated successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Deactivate a user account"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating admin users
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot deactivate admin users")
    
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_DISABLED",
        entity="user",
        entity_id=user_id,
        metadata={"email": user["email"], "role": user["role"]},
        request=request
    )
    
    return {"message": "User deactivated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a user (only if no dependencies)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting admin users
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin users")
    
    # Check dependencies based on role
    role = user.get("role")
    
    if role == "worker":
        sales_count = await db.campaign_coupons.count_documents({"sold_by_worker_id": user_id})
        if sales_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete worker with {sales_count} sales. Deactivate instead."
            )
    elif role == "branch":
        encash_count = await db.encashments.count_documents({"encashed_by": user_id})
        if encash_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete branch user with {encash_count} encashments. Deactivate instead."
            )
    elif role == "cre":
        call_count = await db.cre_call_logs.count_documents({"cre_id": user_id})
        if call_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete CRE with {call_count} call logs. Deactivate instead."
            )
    
    await db.users.delete_one({"id": user_id})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_DELETED",
        entity="user",
        entity_id=user_id,
        metadata={"email": user["email"], "role": role},
        request=request
    )
    
    return {"message": "User deleted successfully"}


# ========== Legacy Worker Management (kept for backward compatibility) ==========

@router.post("/workers", response_model=UserResponse)
async def create_worker(
    data: AdminWorkerCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Admin creates a new worker (legacy endpoint - use /api/admin/users instead)"""
    # Check email exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=data.email,
        name=data.name,
        phone=data.phone,
        role="worker",
        area_id=data.area_id
    )
    
    user_dict = user.model_dump()
    user_dict["password_hash"] = get_password_hash(data.password)
    user_dict["created_at"] = user_dict["created_at"].isoformat()
    
    await db.users.insert_one(user_dict)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_CREATED",
        entity="user",
        entity_id=user.id,
        metadata={"email": data.email, "name": data.name},
        request=request
    )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        role=user.role,
        is_active=user.is_active,
        area_id=user.area_id,
        branch_id=user.branch_id,
        coupon_possession_count=user.coupon_possession_count
    )


@router.patch("/workers/{worker_id}")
async def update_worker(
    worker_id: str,
    data: AdminWorkerUpdate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update worker details"""
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.phone is not None:
        update_data["phone"] = data.phone
    if data.area_id is not None:
        update_data["area_id"] = data.area_id
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    await db.users.update_one({"id": worker_id}, {"$set": update_data})
    
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


@router.post("/workers/{worker_id}/disable")
async def disable_worker(
    worker_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Disable a worker account"""
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await db.users.update_one({"id": worker_id}, {"$set": {"is_active": False}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_DISABLED",
        entity="user",
        entity_id=worker_id,
        metadata={"email": worker["email"]},
        request=request
    )
    
    return {"message": "Worker disabled successfully"}


@router.post("/workers/{worker_id}/enable")
async def enable_worker(
    worker_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Enable a worker account"""
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await db.users.update_one({"id": worker_id}, {"$set": {"is_active": True}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_UPDATED",
        entity="user",
        entity_id=worker_id,
        metadata={"is_active": True},
        request=request
    )
    
    return {"message": "Worker enabled successfully"}


@router.delete("/workers/{worker_id}")
async def delete_worker(
    worker_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a worker (soft delete - marks as deleted)"""
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Check for sales
    sales_count = await db.campaign_coupons.count_documents({"sold_by_worker_id": worker_id})
    if sales_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete worker with {sales_count} sales. Disable instead."
        )
    
    await db.users.delete_one({"id": worker_id})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="USER_DELETED",
        entity="user",
        entity_id=worker_id,
        metadata={"email": worker["email"]},
        request=request
    )
    
    return {"message": "Worker deleted successfully"}


@router.post("/workers/{worker_id}/reset-password")
async def reset_worker_password(
    worker_id: str,
    data: PasswordResetRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Reset worker's password"""
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    new_hash = get_password_hash(data.new_password)
    await db.users.update_one({"id": worker_id}, {"$set": {"password_hash": new_hash}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="PASSWORD_RESET",
        entity="user",
        entity_id=worker_id,
        metadata={"email": worker["email"]},
        request=request
    )
    
    return {"message": "Password reset successfully"}


# ========== Inactivity Tracking ==========

@router.get("/inactivity-alerts", response_model=List[InactivityLogResponse])
async def get_inactivity_alerts(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get inactivity alerts"""
    query = {}
    if status:
        query["status"] = status
    else:
        query["status"] = "ACTIVE"  # Default to active alerts
    
    alerts = await db.inactivity_logs.find(query, {"_id": 0}).sort("alert_time", -1).to_list(limit)
    
    results = []
    for a in alerts:
        if isinstance(a.get("punch_in_time"), str):
            a["punch_in_time"] = datetime.fromisoformat(a["punch_in_time"])
        if isinstance(a.get("alert_time"), str):
            a["alert_time"] = datetime.fromisoformat(a["alert_time"])
        if isinstance(a.get("resolved_at"), str):
            a["resolved_at"] = datetime.fromisoformat(a["resolved_at"])
        
        # Get worker name
        worker = await db.users.find_one({"id": a["worker_id"]}, {"_id": 0, "name": 1})
        
        results.append(InactivityLogResponse(
            id=a["id"],
            worker_id=a["worker_id"],
            worker_name=worker["name"] if worker else "Unknown",
            punch_in_time=a["punch_in_time"],
            alert_time=a["alert_time"],
            latitude=a.get("latitude"),
            longitude=a.get("longitude"),
            hours_inactive=a.get("hours_inactive", 3.0),
            status=a["status"],
            resolved_at=a.get("resolved_at"),
            notes=a.get("notes")
        ))
    
    return results


@router.patch("/inactivity-alerts/{alert_id}/resolve")
async def resolve_inactivity_alert(
    alert_id: str,
    notes: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Resolve an inactivity alert"""
    alert = await db.inactivity_logs.find_one({"id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.inactivity_logs.update_one(
        {"id": alert_id},
        {"$set": {
            "status": "RESOLVED",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": current_user["sub"],
            "notes": notes
        }}
    )
    
    return {"message": "Alert resolved"}


@router.patch("/inactivity-alerts/{alert_id}/dismiss")
async def dismiss_inactivity_alert(
    alert_id: str,
    notes: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Dismiss an inactivity alert"""
    alert = await db.inactivity_logs.find_one({"id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.inactivity_logs.update_one(
        {"id": alert_id},
        {"$set": {
            "status": "DISMISSED",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": current_user["sub"],
            "notes": notes
        }}
    )
    
    return {"message": "Alert dismissed"}


# ========== Enhanced Dashboard Stats ==========

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_admin_dashboard_stats(
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get comprehensive admin dashboard statistics"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # Workers
    total_workers = await db.users.count_documents({"role": "worker", "is_active": True})
    
    active_today = await db.attendance.count_documents({
        "type": "PUNCH_IN",
        "timestamp": {"$gte": today_start}
    })
    
    inactive_alerts = await db.inactivity_logs.count_documents({"status": "ACTIVE"})
    
    # Sales today
    sales_today = await db.campaign_coupons.count_documents({
        "status": "SOLD",
        "sold_at": {"$gte": today_start}
    })
    
    # Revenue today
    revenue_pipeline = [
        {"$match": {"status": "SOLD", "sold_at": {"$gte": today_start}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {"_id": None, "total": {"$sum": "$campaign.price"}}}
    ]
    revenue_today_result = await db.campaign_coupons.aggregate(revenue_pipeline).to_list(1)
    revenue_today = revenue_today_result[0]["total"] if revenue_today_result else 0.0
    
    # Sales & Revenue this month
    sales_month = await db.campaign_coupons.count_documents({
        "status": "SOLD",
        "sold_at": {"$gte": month_start}
    })
    
    month_pipeline = [
        {"$match": {"status": "SOLD", "sold_at": {"$gte": month_start}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {"_id": None, "total": {"$sum": "$campaign.price"}}}
    ]
    revenue_month_result = await db.campaign_coupons.aggregate(month_pipeline).to_list(1)
    revenue_month = revenue_month_result[0]["total"] if revenue_month_result else 0.0
    
    # Campaigns
    active_campaigns = await db.campaigns.count_documents({"status": "ACTIVE"})
    total_available = await db.campaign_coupons.count_documents({"status": "AVAILABLE"})
    
    # Areas
    total_areas = await db.areas.count_documents({"is_active": True})
    
    # Top area
    top_area_pipeline = [
        {"$match": {"status": "SOLD", "sold_at": {"$gte": month_start}}},
        {"$group": {"_id": "$area_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    top_area_result = await db.campaign_coupons.aggregate(top_area_pipeline).to_list(1)
    top_area_name = None
    if top_area_result and top_area_result[0]["_id"]:
        area = await db.areas.find_one({"id": top_area_result[0]["_id"]}, {"_id": 0, "name": 1})
        top_area_name = area["name"] if area else None
    
    # Expenses
    pending_expenses = await db.expenses.count_documents({"status": "PENDING"})
    
    expense_pipeline = [
        {"$match": {"status": "APPROVED", "approved_at": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    expenses_month_result = await db.expenses.aggregate(expense_pipeline).to_list(1)
    expenses_month = expenses_month_result[0]["total"] if expenses_month_result else 0.0
    
    # Advances this month
    advance_pipeline = [
        {"$match": {"type": "ADVANCE", "created_at": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    advances_month_result = await db.ledger_transactions.aggregate(advance_pipeline).to_list(1)
    advances_month = advances_month_result[0]["total"] if advances_month_result else 0.0
    
    # Net payable
    net_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$net_payable"}}}
    ]
    net_result = await db.worker_ledgers.aggregate(net_pipeline).to_list(1)
    net_payable = net_result[0]["total"] if net_result else 0.0
    
    return AdminDashboardStats(
        total_workers=total_workers,
        active_workers_today=active_today,
        inactive_alerts=inactive_alerts,
        total_sales_today=sales_today,
        total_revenue_today=revenue_today,
        total_sales_month=sales_month,
        total_revenue_month=revenue_month,
        active_campaigns=active_campaigns,
        total_coupons_available=total_available,
        total_areas=total_areas,
        top_performing_area=top_area_name,
        pending_expenses=pending_expenses,
        total_expenses_month=expenses_month,
        total_advances_month=advances_month,
        net_payable_all_workers=net_payable
    )


# ========== Location Spoofing Alerts ==========

@router.get("/spoofing-alerts")
async def get_spoofing_alerts(
    limit: int = 50,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get location spoofing alerts"""
    alerts = await db.location_spoofing_alerts.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    results = []
    for a in alerts:
        if isinstance(a.get("created_at"), str):
            a["created_at"] = datetime.fromisoformat(a["created_at"])
        
        worker = await db.users.find_one({"id": a["worker_id"]}, {"_id": 0, "name": 1})
        a["worker_name"] = worker["name"] if worker else "Unknown"
        results.append(a)
    
    return results


# ========== API Key Management ==========

import secrets
import hashlib
from pydantic import BaseModel

class ApiKeyCreate(BaseModel):
    service_name: str
    description: Optional[str] = None


class ApiKeyResponse(BaseModel):
    id: str
    service_name: str
    description: Optional[str]
    key_prefix: str
    is_active: bool
    created_at: str
    last_used_at: Optional[str]


@router.post("/api-keys")
async def create_api_key(
    data: ApiKeyCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Generate a new API key for external integrations"""
    import uuid
    
    # Generate a secure API key
    raw_key = f"ffp_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]
    
    key_doc = {
        "id": str(uuid.uuid4()),
        "service_name": data.service_name,
        "description": data.description,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used_at": None,
        "created_by": current_user["sub"]
    }
    
    await db.api_keys.insert_one(key_doc)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="API_KEY_CREATED",
        entity="api_key",
        entity_id=key_doc["id"],
        metadata={"service_name": data.service_name},
        request=request
    )
    
    # Return the raw key ONLY ONCE
    return {
        "id": key_doc["id"],
        "service_name": key_doc["service_name"],
        "api_key": raw_key,
        "message": "Store this key securely. It cannot be retrieved later."
    }


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get all API keys (without the actual key values)"""
    keys = await db.api_keys.find({}, {"_id": 0, "key_hash": 0}).sort("created_at", -1).to_list(100)
    return keys


@router.post("/api-keys/{key_id}/toggle")
async def toggle_api_key(
    key_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Activate or deactivate an API key"""
    key = await db.api_keys.find_one({"id": key_id}, {"_id": 0})
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    new_status = not key.get("is_active", True)
    await db.api_keys.update_one({"id": key_id}, {"$set": {"is_active": new_status}})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="API_KEY_TOGGLED",
        entity="api_key",
        entity_id=key_id,
        metadata={"service_name": key["service_name"], "is_active": new_status},
        request=request
    )
    
    return {"message": f"API key {'activated' if new_status else 'deactivated'}"}


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Permanently delete an API key"""
    key = await db.api_keys.find_one({"id": key_id}, {"_id": 0})
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    await db.api_keys.delete_one({"id": key_id})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="API_KEY_DELETED",
        entity="api_key",
        entity_id=key_id,
        metadata={"service_name": key["service_name"]},
        request=request
    )
    
    return {"message": "API key deleted"}


# ========== Data Cleanup ==========

@router.post("/cleanup-dummy-data")
async def cleanup_dummy_data(
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """
    Remove all dummy/test data from the database.
    KEEPS: users collection (all user accounts)
    REMOVES: campaigns, coupons, sales, ledgers, expenses, fraud alerts, etc.
    """
    collections_to_clear = [
        "campaigns",
        "campaign_coupons",
        "encashments",
        "worker_ledgers",
        "ledger_transactions",
        "expenses",
        "fraud_alerts",
        "worker_performance_scores",
        "inactivity_logs",
        "location_spoofing_alerts",
        "cre_call_logs",
        "attendance_records",
    ]
    
    results = {}
    for collection in collections_to_clear:
        try:
            count = await db[collection].count_documents({})
            if count > 0:
                await db[collection].delete_many({})
                results[collection] = f"Deleted {count} documents"
            else:
                results[collection] = "Already empty"
        except Exception as e:
            results[collection] = f"Error: {str(e)}"
    
    # Keep users, branches, areas, and api_keys
    kept = {
        "users": await db.users.count_documents({}),
        "branches": await db.branches.count_documents({}),
        "areas": await db.areas.count_documents({}),
        "api_keys": await db.api_keys.count_documents({})
    }
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="DUMMY_DATA_CLEANUP",
        entity="system",
        entity_id="cleanup",
        metadata={"cleared": results, "kept": kept},
        request=request
    )
    
    return {
        "message": "Dummy data cleanup completed",
        "cleared": results,
        "kept": kept
    }


@router.get("/database-stats")
async def get_database_stats(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get counts of all collections in the database"""
    collections = [
        "users", "campaigns", "campaign_coupons", "branches", "areas",
        "encashments", "worker_ledgers", "ledger_transactions", "expenses",
        "fraud_alerts", "worker_performance_scores", "inactivity_logs",
        "api_keys", "audit_logs", "cre_call_logs", "attendance_records"
    ]
    
    stats = {}
    for collection in collections:
        try:
            count = await db[collection].count_documents({})
            stats[collection] = count
        except:
            stats[collection] = 0
    
    return stats
