"""
Elite v4.0 Intelligence Routes
- Fraud Detection Engine
- Worker Performance Scoring
- Real-time Metrics
- Area Intelligence
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import uuid
from collections import defaultdict

from models import (
    FraudAlert, FraudAlertResponse, FraudAlertType,
    WorkerPerformanceScore, WorkerPerformanceResponse,
    RealTimeMetrics, AreaIntelligence
)
from auth import get_current_user, require_roles

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

db = None
create_audit_log = None

def init_routes(database, audit_func):
    global db, create_audit_log
    db = database
    create_audit_log = audit_func


# ========== FRAUD DETECTION ENGINE ==========

async def detect_duplicate_mobile(mobile_hash: str, exclude_coupon_id: str = None) -> List[dict]:
    """Detect same mobile used across multiple coupons"""
    query = {"customer_phone": mobile_hash, "status": "SOLD"}
    if exclude_coupon_id:
        query["id"] = {"$ne": exclude_coupon_id}
    
    duplicates = await db.campaign_coupons.find(query, {"_id": 0}).to_list(100)
    return duplicates


async def detect_gps_clustering(worker_id: str, lat: float, lng: float, time_window_minutes: int = 20) -> int:
    """Detect multiple sales from same GPS location in short time"""
    time_threshold = (datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)).isoformat()
    
    # Find sales in time window with similar GPS (within ~100 meters)
    # Using approximate degree comparison (0.001 degree ≈ 111 meters)
    tolerance = 0.001
    
    nearby_sales = await db.campaign_coupons.count_documents({
        "sold_by_worker_id": worker_id,
        "sold_at": {"$gte": time_threshold},
        "latitude": {"$gte": lat - tolerance, "$lte": lat + tolerance},
        "longitude": {"$gte": lng - tolerance, "$lte": lng + tolerance}
    })
    
    return nearby_sales


async def check_expense_revenue_ratio(worker_id: str) -> float:
    """Calculate expense to revenue ratio for a worker"""
    ledger = await db.worker_ledgers.find_one({"worker_id": worker_id}, {"_id": 0})
    if not ledger or ledger.get("total_revenue", 0) == 0:
        return 0.0
    
    ratio = ledger.get("total_expenses", 0) / ledger.get("total_revenue", 1)
    return round(ratio, 2)


async def create_fraud_alert(
    alert_type: str,
    worker_id: str,
    severity: str,
    details: dict,
    related_entity_id: str = None
):
    """Create a fraud alert record"""
    alert = FraudAlert(
        alert_type=alert_type,
        worker_id=worker_id,
        severity=severity,
        details=details,
        related_entity_id=related_entity_id
    )
    
    doc = alert.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.fraud_alerts.insert_one(doc)
    
    return alert


@router.get("/fraud-alerts", response_model=List[FraudAlertResponse])
async def get_fraud_alerts(
    status: Optional[str] = "ACTIVE",
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get fraud alerts with filters"""
    query = {}
    if status:
        query["status"] = status
    if alert_type:
        query["alert_type"] = alert_type
    if severity:
        query["severity"] = severity
    
    alerts = await db.fraud_alerts.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    results = []
    for a in alerts:
        if isinstance(a.get("created_at"), str):
            a["created_at"] = datetime.fromisoformat(a["created_at"])
        if isinstance(a.get("resolved_at"), str):
            a["resolved_at"] = datetime.fromisoformat(a["resolved_at"])
        
        # Get worker name
        worker = await db.users.find_one({"id": a["worker_id"]}, {"_id": 0, "name": 1})
        
        results.append(FraudAlertResponse(
            id=a["id"],
            alert_type=a["alert_type"],
            worker_id=a["worker_id"],
            worker_name=worker["name"] if worker else "Unknown",
            severity=a["severity"],
            details=a["details"],
            related_entity_id=a.get("related_entity_id"),
            status=a["status"],
            created_at=a["created_at"],
            resolved_at=a.get("resolved_at"),
            resolved_by=a.get("resolved_by"),
            resolution_notes=a.get("resolution_notes")
        ))
    
    return results


@router.patch("/fraud-alerts/{alert_id}/resolve")
async def resolve_fraud_alert(
    alert_id: str,
    notes: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Resolve a fraud alert"""
    alert = await db.fraud_alerts.find_one({"id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.fraud_alerts.update_one(
        {"id": alert_id},
        {"$set": {
            "status": "RESOLVED",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": current_user["sub"],
            "resolution_notes": notes
        }}
    )
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="FRAUD_ALERT_RESOLVED",
        entity="fraud_alert",
        entity_id=alert_id,
        metadata={"notes": notes},
        request=request
    )
    
    return {"message": "Alert resolved"}


@router.patch("/fraud-alerts/{alert_id}/dismiss")
async def dismiss_fraud_alert(
    alert_id: str,
    notes: Optional[str] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Dismiss a fraud alert as false positive"""
    alert = await db.fraud_alerts.find_one({"id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.fraud_alerts.update_one(
        {"id": alert_id},
        {"$set": {
            "status": "DISMISSED",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": current_user["sub"],
            "resolution_notes": notes
        }}
    )
    
    return {"message": "Alert dismissed"}


@router.post("/scan-fraud")
async def run_fraud_scan(
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually trigger fraud detection scan"""
    alerts_created = 0
    
    # 1. Scan for duplicate mobiles
    pipeline = [
        {"$match": {"status": "SOLD", "customer_phone": {"$exists": True}}},
        {"$group": {"_id": "$customer_phone", "count": {"$sum": 1}, "coupons": {"$push": "$id"}}},
        {"$match": {"count": {"$gt": 2}}}  # Flag if same mobile used 3+ times
    ]
    
    duplicate_mobiles = await db.campaign_coupons.aggregate(pipeline).to_list(100)
    
    for dup in duplicate_mobiles:
        # Check if alert already exists
        existing = await db.fraud_alerts.find_one({
            "alert_type": "DUPLICATE_MOBILE",
            "details.mobile_hash": dup["_id"],
            "status": "ACTIVE"
        })
        
        if not existing:
            # Get worker IDs involved
            coupons = await db.campaign_coupons.find(
                {"id": {"$in": dup["coupons"]}},
                {"_id": 0, "sold_by_worker_id": 1}
            ).to_list(100)
            worker_ids = list(set([c["sold_by_worker_id"] for c in coupons if c.get("sold_by_worker_id")]))
            
            if worker_ids:
                await create_fraud_alert(
                    alert_type="DUPLICATE_MOBILE",
                    worker_id=worker_ids[0],
                    severity="HIGH" if dup["count"] > 5 else "MEDIUM",
                    details={
                        "mobile_hash": dup["_id"],
                        "usage_count": dup["count"],
                        "coupon_ids": dup["coupons"][:10],  # Limit to 10
                        "workers_involved": worker_ids
                    }
                )
                alerts_created += 1
    
    # 2. Scan for high expense-to-revenue ratios
    workers = await db.users.find({"role": "worker", "is_active": True}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    
    for worker in workers:
        ratio = await check_expense_revenue_ratio(worker["id"])
        
        if ratio > 0.5:  # Flag if expenses > 50% of revenue
            existing = await db.fraud_alerts.find_one({
                "alert_type": "HIGH_EXPENSE_RATIO",
                "worker_id": worker["id"],
                "status": "ACTIVE"
            })
            
            if not existing:
                ledger = await db.worker_ledgers.find_one({"worker_id": worker["id"]}, {"_id": 0})
                await create_fraud_alert(
                    alert_type="HIGH_EXPENSE_RATIO",
                    worker_id=worker["id"],
                    severity="HIGH" if ratio > 0.8 else "MEDIUM",
                    details={
                        "expense_ratio": ratio,
                        "total_expenses": ledger.get("total_expenses", 0) if ledger else 0,
                        "total_revenue": ledger.get("total_revenue", 0) if ledger else 0
                    }
                )
                alerts_created += 1
    
    # 3. GPS clustering alerts are created during sale (real-time)
    # Location spoofing alerts are also created during sale
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="FRAUD_SCAN_TRIGGERED",
        entity="system",
        metadata={"alerts_created": alerts_created},
        request=request
    )
    
    return {
        "message": f"Fraud scan complete. {alerts_created} new alerts created.",
        "alerts_created": alerts_created
    }


# ========== WORKER PERFORMANCE SCORING ==========

async def calculate_worker_score(worker_id: str) -> dict:
    """
    Calculate comprehensive worker performance score (0-100)
    
    Components:
    - Conversion Rate (sales vs days active): 25%
    - Avg Sales per Active Day: 25%
    - Revenue per Day: 20%
    - Activity Score (attendance consistency): 15%
    - Inactivity Ratio (inverse): 15%
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_month = (now - month_start).days + 1
    
    # Get worker data
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0})
    if not worker:
        return None
    
    # Total sales this month
    total_sales = await db.campaign_coupons.count_documents({
        "sold_by_worker_id": worker_id,
        "sold_at": {"$gte": month_start.isoformat()}
    })
    
    # Days with attendance this month
    attendance_days = await db.attendance.distinct("timestamp", {
        "worker_id": worker_id,
        "type": "PUNCH_IN",
        "timestamp": {"$gte": month_start.isoformat()}
    })
    active_days = len(set([a[:10] for a in attendance_days]))  # Unique dates
    
    # Revenue this month
    revenue_pipeline = [
        {"$match": {"sold_by_worker_id": worker_id, "sold_at": {"$gte": month_start.isoformat()}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {"_id": None, "total": {"$sum": "$campaign.price"}}}
    ]
    revenue_result = await db.campaign_coupons.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    # Inactivity alerts this month
    inactivity_count = await db.inactivity_logs.count_documents({
        "worker_id": worker_id,
        "alert_time": {"$gte": month_start.isoformat()}
    })
    
    # Calculate component scores (0-100 each)
    
    # 1. Sales per active day score
    avg_sales_per_day = total_sales / max(active_days, 1)
    sales_score = min(100, avg_sales_per_day * 20)  # 5 sales/day = 100
    
    # 2. Revenue score
    avg_revenue_per_day = total_revenue / max(active_days, 1)
    revenue_score = min(100, avg_revenue_per_day / 10)  # ₹1000/day = 100
    
    # 3. Attendance consistency score
    expected_work_days = min(days_in_month, 26)  # Max 26 working days
    attendance_score = min(100, (active_days / expected_work_days) * 100)
    
    # 4. Inactivity ratio (inverse - fewer alerts = better)
    max_acceptable_alerts = 5
    inactivity_score = max(0, 100 - (inactivity_count / max_acceptable_alerts * 100))
    
    # 5. Conversion efficiency (sales per day registered)
    created_at = datetime.fromisoformat(worker["created_at"]) if isinstance(worker.get("created_at"), str) else worker.get("created_at", now)
    days_registered = max(1, (now - created_at).days)
    conversion_rate = total_sales / days_registered
    conversion_score = min(100, conversion_rate * 33.33)  # 3 sales/day avg = 100
    
    # Weighted final score
    final_score = (
        conversion_score * 0.25 +
        sales_score * 0.25 +
        revenue_score * 0.20 +
        attendance_score * 0.15 +
        inactivity_score * 0.15
    )
    
    return {
        "worker_id": worker_id,
        "worker_name": worker["name"],
        "final_score": round(final_score, 1),
        "components": {
            "conversion_score": round(conversion_score, 1),
            "sales_per_day_score": round(sales_score, 1),
            "revenue_score": round(revenue_score, 1),
            "attendance_score": round(attendance_score, 1),
            "inactivity_score": round(inactivity_score, 1)
        },
        "metrics": {
            "total_sales_month": total_sales,
            "active_days": active_days,
            "avg_sales_per_day": round(avg_sales_per_day, 2),
            "total_revenue_month": total_revenue,
            "avg_revenue_per_day": round(avg_revenue_per_day, 2),
            "inactivity_alerts": inactivity_count
        },
        "grade": get_performance_grade(final_score),
        "calculated_at": now.isoformat()
    }


def get_performance_grade(score: float) -> str:
    """Convert numeric score to grade"""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


@router.get("/worker-scores", response_model=List[WorkerPerformanceResponse])
async def get_all_worker_scores(
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get performance scores for all workers"""
    workers = await db.users.find(
        {"role": "worker", "is_active": True},
        {"_id": 0, "id": 1}
    ).to_list(500)
    
    scores = []
    for worker in workers:
        score_data = await calculate_worker_score(worker["id"])
        if score_data:
            scores.append(WorkerPerformanceResponse(**score_data))
    
    # Sort by score descending
    scores.sort(key=lambda x: x.final_score, reverse=True)
    
    # Add rank
    for i, score in enumerate(scores):
        score.rank = i + 1
    
    return scores


@router.get("/worker-scores/{worker_id}", response_model=WorkerPerformanceResponse)
async def get_worker_score(
    worker_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get performance score for a specific worker"""
    # Workers can see their own score
    if current_user["role"] == "worker" and current_user["sub"] != worker_id:
        raise HTTPException(status_code=403, detail="Cannot view other worker's score")
    
    score_data = await calculate_worker_score(worker_id)
    if not score_data:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    return WorkerPerformanceResponse(**score_data)


# ========== REAL-TIME METRICS (WebSocket Support) ==========

@router.get("/realtime-metrics", response_model=RealTimeMetrics)
async def get_realtime_metrics(
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get real-time metrics for dashboard"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # Live sales today
    sales_today = await db.campaign_coupons.count_documents({
        "status": "SOLD",
        "sold_at": {"$gte": today_start}
    })
    
    # Live revenue today
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
    revenue_result = await db.campaign_coupons.aggregate(revenue_pipeline).to_list(1)
    revenue_today = revenue_result[0]["total"] if revenue_result else 0.0
    
    # Active workers (punched in today, not punched out)
    punch_ins_today = await db.attendance.find({
        "type": "PUNCH_IN",
        "timestamp": {"$gte": today_start}
    }, {"_id": 0, "worker_id": 1}).to_list(500)
    
    punched_in_ids = [p["worker_id"] for p in punch_ins_today]
    
    punch_outs_today = await db.attendance.find({
        "type": "PUNCH_OUT",
        "timestamp": {"$gte": today_start}
    }, {"_id": 0, "worker_id": 1}).to_list(500)
    
    punched_out_ids = [p["worker_id"] for p in punch_outs_today]
    
    active_workers = len(set(punched_in_ids) - set(punched_out_ids))
    total_punched_in = len(set(punched_in_ids))
    
    # Inactive workers (active inactivity alerts)
    inactive_alerts = await db.inactivity_logs.count_documents({"status": "ACTIVE"})
    
    # Fraud alerts count
    fraud_alerts_count = await db.fraud_alerts.count_documents({"status": "ACTIVE"})
    
    # Pending expenses
    pending_expenses = await db.expenses.count_documents({"status": "PENDING"})
    
    # Encashments today
    encashments_today = await db.encashments.count_documents({
        "encashed_at": {"$gte": today_start}
    })
    
    return RealTimeMetrics(
        live_sales_today=sales_today,
        live_revenue_today=revenue_today,
        active_workers_now=active_workers,
        total_punched_in_today=total_punched_in,
        inactive_worker_alerts=inactive_alerts,
        fraud_alerts_active=fraud_alerts_count,
        pending_expenses=pending_expenses,
        encashments_today=encashments_today,
        last_updated=now.isoformat()
    )


# ========== AREA INTELLIGENCE ==========

@router.get("/area-intelligence")
async def get_area_intelligence(
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get sales intelligence by area, city, state"""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    # Sales by city
    city_pipeline = [
        {"$match": {"status": "SOLD", "city": {"$exists": True, "$ne": ""}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$city",
            "total_sales": {"$sum": 1},
            "total_revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 20}
    ]
    
    sales_by_city = await db.campaign_coupons.aggregate(city_pipeline).to_list(20)
    
    # Sales by state
    state_pipeline = [
        {"$match": {"status": "SOLD", "state": {"$exists": True, "$ne": ""}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$state",
            "total_sales": {"$sum": 1},
            "total_revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"total_revenue": -1}}
    ]
    
    sales_by_state = await db.campaign_coupons.aggregate(state_pipeline).to_list(50)
    
    # Campaign performance by geography
    campaign_geo_pipeline = [
        {"$match": {"status": "SOLD", "sold_at": {"$gte": month_start}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": {
                "campaign_id": "$campaign_id",
                "campaign_name": "$campaign.name",
                "state": "$state"
            },
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 50}
    ]
    
    campaign_by_geo = await db.campaign_coupons.aggregate(campaign_geo_pipeline).to_list(50)
    
    # Top performing areas (area_name field)
    area_pipeline = [
        {"$match": {"status": "SOLD", "area_name": {"$exists": True, "$ne": ""}}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$area_name",
            "total_sales": {"$sum": 1},
            "total_revenue": {"$sum": "$campaign.price"},
            "city": {"$first": "$city"},
            "state": {"$first": "$state"}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 30}
    ]
    
    sales_by_area = await db.campaign_coupons.aggregate(area_pipeline).to_list(30)
    
    return {
        "sales_by_city": [{"city": s["_id"], "sales": s["total_sales"], "revenue": s["total_revenue"]} for s in sales_by_city],
        "sales_by_state": [{"state": s["_id"], "sales": s["total_sales"], "revenue": s["total_revenue"]} for s in sales_by_state],
        "campaign_by_geography": [
            {
                "campaign_id": s["_id"]["campaign_id"],
                "campaign_name": s["_id"]["campaign_name"],
                "state": s["_id"]["state"],
                "sales": s["sales"],
                "revenue": s["revenue"]
            }
            for s in campaign_by_geo
        ],
        "top_areas": [
            {
                "area": s["_id"],
                "city": s.get("city", ""),
                "state": s.get("state", ""),
                "sales": s["total_sales"],
                "revenue": s["total_revenue"]
            }
            for s in sales_by_area
        ],
        "generated_at": now.isoformat()
    }


# ========== INACTIVE WORKERS PANEL ==========

@router.get("/inactive-workers")
async def get_inactive_workers_panel(
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get detailed inactive workers panel for admin dashboard"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get active inactivity alerts
    alerts = await db.inactivity_logs.find(
        {"status": "ACTIVE"},
        {"_id": 0}
    ).sort("alert_time", -1).to_list(100)
    
    results = []
    for alert in alerts:
        worker_id = alert["worker_id"]
        
        # Get worker details
        worker = await db.users.find_one({"id": worker_id}, {"_id": 0})
        if not worker:
            continue
        
        # Get area info
        area = None
        if worker.get("area_id"):
            area = await db.areas.find_one({"id": worker["area_id"]}, {"_id": 0, "name": 1, "city": 1})
        
        # Get last sale
        last_sale = await db.campaign_coupons.find_one(
            {"sold_by_worker_id": worker_id},
            {"_id": 0, "sold_at": 1, "code": 1},
            sort=[("sold_at", -1)]
        )
        
        # Get latest location
        latest_location = await db.location_logs.find_one(
            {"worker_id": worker_id},
            {"_id": 0},
            sort=[("timestamp", -1)]
        )
        
        results.append({
            "alert_id": alert["id"],
            "worker_id": worker_id,
            "worker_name": worker["name"],
            "worker_phone": worker.get("phone"),
            "area_name": area["name"] if area else "Not Assigned",
            "area_city": area.get("city", "") if area else "",
            "punch_in_time": alert["punch_in_time"],
            "hours_inactive": round(alert.get("hours_inactive", 3.0), 1),
            "last_sale_time": last_sale.get("sold_at") if last_sale else None,
            "last_sale_code": last_sale.get("code") if last_sale else None,
            "current_latitude": latest_location.get("latitude") if latest_location else alert.get("latitude"),
            "current_longitude": latest_location.get("longitude") if latest_location else alert.get("longitude"),
            "location_timestamp": latest_location.get("timestamp") if latest_location else None,
            "alert_time": alert["alert_time"]
        })
    
    return {
        "total_inactive": len(results),
        "workers": results
    }
