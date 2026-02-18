"""
Area Management & Analytics Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from models import (
    AreaCreate, Area, AreaResponse,
    SalesAnalytics, AreaAnalytics, WorkerAnalytics
)
from auth import get_current_user, require_roles

router = APIRouter(prefix="/api/areas", tags=["Areas"])

db = None
create_audit_log = None

def init_routes(database, audit_func):
    global db, create_audit_log
    db = database
    create_audit_log = audit_func


@router.post("", response_model=AreaResponse)
async def create_area(
    data: AreaCreate,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new area"""
    # Check for duplicate
    existing = await db.areas.find_one({
        "name": data.name,
        "city": data.city,
        "state": data.state
    })
    if existing:
        raise HTTPException(status_code=400, detail="Area already exists")
    
    area = Area(
        name=data.name,
        city=data.city,
        state=data.state,
        latitude=data.latitude,
        longitude=data.longitude
    )
    
    doc = area.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.areas.insert_one(doc)
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="AREA_CREATED",
        entity="area",
        entity_id=area.id,
        metadata={"name": data.name, "city": data.city, "state": data.state},
        request=request
    )
    
    return AreaResponse(
        id=area.id,
        name=area.name,
        city=area.city,
        state=area.state,
        latitude=area.latitude,
        longitude=area.longitude,
        is_active=area.is_active,
        total_sales=0,
        total_revenue=0.0
    )


@router.get("", response_model=List[AreaResponse])
async def get_areas(
    state: Optional[str] = None,
    city: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "cre", "worker"))
):
    """Get all areas with sales stats"""
    query = {"is_active": True}
    if state:
        query["state"] = state
    if city:
        query["city"] = city
    
    areas = await db.areas.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    
    results = []
    for a in areas:
        # Get sales for this area
        sales = await db.campaign_coupons.count_documents({
            "area_id": a["id"],
            "status": "SOLD"
        })
        
        # Get revenue
        pipeline = [
            {"$match": {"area_id": a["id"], "status": "SOLD"}},
            {"$lookup": {
                "from": "campaigns",
                "localField": "campaign_id",
                "foreignField": "id",
                "as": "campaign"
            }},
            {"$unwind": "$campaign"},
            {"$group": {"_id": None, "total": {"$sum": "$campaign.price"}}}
        ]
        revenue_result = await db.campaign_coupons.aggregate(pipeline).to_list(1)
        revenue = revenue_result[0]["total"] if revenue_result else 0.0
        
        results.append(AreaResponse(
            id=a["id"],
            name=a["name"],
            city=a["city"],
            state=a["state"],
            latitude=a.get("latitude"),
            longitude=a.get("longitude"),
            is_active=a["is_active"],
            total_sales=sales,
            total_revenue=revenue
        ))
    
    return results


@router.get("/states")
async def get_states(current_user: dict = Depends(require_roles("admin", "cre"))):
    """Get unique states"""
    states = await db.areas.distinct("state", {"is_active": True})
    return sorted(states)


@router.get("/cities")
async def get_cities(
    state: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get unique cities"""
    query = {"is_active": True}
    if state:
        query["state"] = state
    cities = await db.areas.distinct("city", query)
    return sorted(cities)


@router.patch("/{area_id}")
async def update_area(
    area_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    request: Request = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update area"""
    area = await db.areas.find_one({"id": area_id}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if is_active is not None:
        update_data["is_active"] = is_active
    if latitude is not None:
        update_data["latitude"] = latitude
    if longitude is not None:
        update_data["longitude"] = longitude
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    await db.areas.update_one({"id": area_id}, {"$set": update_data})
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="AREA_UPDATED",
        entity="area",
        entity_id=area_id,
        metadata=update_data,
        request=request
    )
    
    return {"message": "Area updated successfully"}


# ========== Analytics ==========

@router.get("/analytics/summary", response_model=SalesAnalytics)
async def get_sales_analytics(
    days: int = 30,
    state: Optional[str] = None,
    city: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get comprehensive sales analytics"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # Base match for sold coupons
    match_query = {
        "status": "SOLD",
        "sold_at": {"$gte": start_date}
    }
    
    # Filter by area if state/city specified
    if state or city:
        area_query = {"is_active": True}
        if state:
            area_query["state"] = state
        if city:
            area_query["city"] = city
        area_ids = await db.areas.distinct("id", area_query)
        match_query["area_id"] = {"$in": area_ids}
    
    # Total sales & revenue
    total_pipeline = [
        {"$match": match_query},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": None,
            "total_sales": {"$sum": 1},
            "total_revenue": {"$sum": "$campaign.price"}
        }}
    ]
    totals = await db.campaign_coupons.aggregate(total_pipeline).to_list(1)
    
    # Sales by campaign
    campaign_pipeline = [
        {"$match": match_query},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$campaign_id",
            "campaign_name": {"$first": "$campaign.name"},
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 10}
    ]
    by_campaign = await db.campaign_coupons.aggregate(campaign_pipeline).to_list(10)
    
    # Sales by area
    area_pipeline = [
        {"$match": match_query},
        {"$lookup": {
            "from": "areas",
            "localField": "area_id",
            "foreignField": "id",
            "as": "area"
        }},
        {"$unwind": {"path": "$area", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$area_id",
            "area_name": {"$first": {"$ifNull": ["$area.name", "Unknown"]}},
            "city": {"$first": {"$ifNull": ["$area.city", "Unknown"]}},
            "state": {"$first": {"$ifNull": ["$area.state", "Unknown"]}},
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 10}
    ]
    by_area = await db.campaign_coupons.aggregate(area_pipeline).to_list(10)
    
    # Sales by worker
    worker_pipeline = [
        {"$match": match_query},
        {"$lookup": {
            "from": "users",
            "localField": "sold_by_worker_id",
            "foreignField": "id",
            "as": "worker"
        }},
        {"$unwind": {"path": "$worker", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$sold_by_worker_id",
            "worker_name": {"$first": {"$ifNull": ["$worker.name", "Unknown"]}},
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"revenue": -1}},
        {"$limit": 10}
    ]
    by_worker = await db.campaign_coupons.aggregate(worker_pipeline).to_list(10)
    
    # Daily trend
    daily_pipeline = [
        {"$match": match_query},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$addFields": {
            "sold_date": {"$substr": ["$sold_at", 0, 10]}
        }},
        {"$group": {
            "_id": "$sold_date",
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily = await db.campaign_coupons.aggregate(daily_pipeline).to_list(days)
    
    return SalesAnalytics(
        total_sales=totals[0]["total_sales"] if totals else 0,
        total_revenue=totals[0]["total_revenue"] if totals else 0.0,
        sales_by_campaign=[{
            "campaign_id": c["_id"],
            "campaign_name": c["campaign_name"],
            "sales": c["sales"],
            "revenue": c["revenue"]
        } for c in by_campaign],
        sales_by_area=[{
            "area_id": a["_id"],
            "area_name": a["area_name"],
            "city": a["city"],
            "state": a["state"],
            "sales": a["sales"],
            "revenue": a["revenue"]
        } for a in by_area],
        sales_by_worker=[{
            "worker_id": w["_id"],
            "worker_name": w["worker_name"],
            "sales": w["sales"],
            "revenue": w["revenue"]
        } for w in by_worker],
        daily_trend=[{
            "date": d["_id"],
            "sales": d["sales"],
            "revenue": d["revenue"]
        } for d in daily]
    )


@router.get("/analytics/area/{area_id}", response_model=AreaAnalytics)
async def get_area_analytics(
    area_id: str,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get detailed analytics for a specific area"""
    area = await db.areas.find_one({"id": area_id}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    # Get sales stats
    sales_count = await db.campaign_coupons.count_documents({
        "area_id": area_id,
        "status": "SOLD"
    })
    
    # Get revenue
    revenue_pipeline = [
        {"$match": {"area_id": area_id, "status": "SOLD"}},
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
    revenue = revenue_result[0]["total"] if revenue_result else 0.0
    
    # Get active workers in area
    active_workers = await db.users.count_documents({
        "area_id": area_id,
        "role": "worker",
        "is_active": True
    })
    
    # Top campaigns in area
    campaign_pipeline = [
        {"$match": {"area_id": area_id, "status": "SOLD"}},
        {"$lookup": {
            "from": "campaigns",
            "localField": "campaign_id",
            "foreignField": "id",
            "as": "campaign"
        }},
        {"$unwind": "$campaign"},
        {"$group": {
            "_id": "$campaign_id",
            "name": {"$first": "$campaign.name"},
            "sales": {"$sum": 1},
            "revenue": {"$sum": "$campaign.price"}
        }},
        {"$sort": {"sales": -1}},
        {"$limit": 5}
    ]
    top_campaigns = await db.campaign_coupons.aggregate(campaign_pipeline).to_list(5)
    
    return AreaAnalytics(
        area_id=area_id,
        area_name=area["name"],
        city=area["city"],
        state=area["state"],
        total_sales=sales_count,
        total_revenue=revenue,
        active_workers=active_workers,
        top_campaigns=[{
            "campaign_id": c["_id"],
            "name": c["name"],
            "sales": c["sales"],
            "revenue": c["revenue"]
        } for c in top_campaigns]
    )
