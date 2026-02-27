"""
Attendance Routes - Worker Punch-In/Out System
- No fixed shift times (fieldwork)
- Track punch-in/out times and total working hours
- Admin dashboard for attendance reports
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from models import (
    AttendanceCreate, DailyAttendance, DailyAttendanceResponse,
    AttendanceStats
)
from auth import get_current_user, require_roles

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

db = None
create_audit_log = None

def init_routes(database, audit_func):
    global db, create_audit_log
    db = database
    create_audit_log = audit_func


def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def format_duration(minutes: int) -> str:
    """Convert minutes to 'Xh Ym' format"""
    if minutes is None:
        return None
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"


# ========== Worker Punch Routes ==========

@router.post("/punch-in")
async def punch_in(
    data: AttendanceCreate,
    request: Request,
    current_user: dict = Depends(require_roles("worker"))
):
    """Worker punches in for the day"""
    worker_id = current_user["sub"]
    today = get_today_date()
    
    # Check if already punched in today
    existing = await db.daily_attendance.find_one({
        "worker_id": worker_id,
        "date": today
    }, {"_id": 0})
    
    if existing:
        if existing.get("punch_in_time") and not existing.get("punch_out_time"):
            raise HTTPException(
                status_code=400,
                detail="Already punched in. Please punch out first."
            )
        if existing.get("punch_out_time"):
            raise HTTPException(
                status_code=400,
                detail="Already completed attendance for today. Cannot punch in again."
            )
    
    now = datetime.now(timezone.utc)
    
    attendance = DailyAttendance(
        worker_id=worker_id,
        date=today,
        punch_in_time=now,
        punch_in_location={
            "latitude": data.latitude,
            "longitude": data.longitude,
            "accuracy": data.accuracy
        },
        status="IN_PROGRESS"
    )
    
    doc = attendance.model_dump()
    doc["punch_in_time"] = doc["punch_in_time"].isoformat()
    
    await db.daily_attendance.insert_one(doc)
    
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="PUNCH_IN",
        entity="attendance",
        entity_id=attendance.id,
        metadata={
            "date": today,
            "latitude": data.latitude,
            "longitude": data.longitude
        },
        request=request
    )
    
    return {
        "success": True,
        "message": "Punched in successfully",
        "punch_in_time": now.isoformat(),
        "status": "IN_PROGRESS"
    }


@router.post("/punch-out")
async def punch_out(
    data: AttendanceCreate,
    request: Request,
    current_user: dict = Depends(require_roles("worker"))
):
    """Worker punches out for the day"""
    worker_id = current_user["sub"]
    today = get_today_date()
    
    # Find today's punch-in record
    existing = await db.daily_attendance.find_one({
        "worker_id": worker_id,
        "date": today,
        "punch_in_time": {"$ne": None},
        "punch_out_time": None
    }, {"_id": 0})
    
    if not existing:
        raise HTTPException(
            status_code=400,
            detail="No active punch-in found. Please punch in first."
        )
    
    now = datetime.now(timezone.utc)
    punch_in_time = datetime.fromisoformat(existing["punch_in_time"])
    
    # Calculate duration in minutes
    duration = int((now - punch_in_time).total_seconds() / 60)
    
    await db.daily_attendance.update_one(
        {"id": existing["id"]},
        {"$set": {
            "punch_out_time": now.isoformat(),
            "punch_out_location": {
                "latitude": data.latitude,
                "longitude": data.longitude,
                "accuracy": data.accuracy
            },
            "duration_minutes": duration,
            "status": "PRESENT"
        }}
    )
    
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="PUNCH_OUT",
        entity="attendance",
        entity_id=existing["id"],
        metadata={
            "date": today,
            "duration_minutes": duration,
            "latitude": data.latitude,
            "longitude": data.longitude
        },
        request=request
    )
    
    return {
        "success": True,
        "message": "Punched out successfully",
        "punch_out_time": now.isoformat(),
        "duration_minutes": duration,
        "duration_formatted": format_duration(duration),
        "status": "PRESENT"
    }


@router.get("/today")
async def get_today_attendance(
    current_user: dict = Depends(require_roles("worker"))
):
    """Get worker's today attendance status"""
    worker_id = current_user["sub"]
    today = get_today_date()
    
    record = await db.daily_attendance.find_one({
        "worker_id": worker_id,
        "date": today
    }, {"_id": 0})
    
    if not record:
        return {
            "date": today,
            "status": "NOT_STARTED",
            "punch_in_time": None,
            "punch_out_time": None,
            "duration_minutes": None,
            "duration_formatted": None
        }
    
    # Calculate in-progress duration
    duration_minutes = record.get("duration_minutes")
    if record.get("punch_in_time") and not record.get("punch_out_time"):
        punch_in = datetime.fromisoformat(record["punch_in_time"])
        duration_minutes = int((datetime.now(timezone.utc) - punch_in).total_seconds() / 60)
    
    return {
        "date": today,
        "status": record.get("status", "ABSENT"),
        "punch_in_time": record.get("punch_in_time"),
        "punch_out_time": record.get("punch_out_time"),
        "duration_minutes": duration_minutes,
        "duration_formatted": format_duration(duration_minutes) if duration_minutes else None
    }


@router.get("/my-history")
async def get_my_attendance_history(
    days: int = 30,
    current_user: dict = Depends(require_roles("worker"))
):
    """Get worker's attendance history"""
    worker_id = current_user["sub"]
    
    # Get last N days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    records = await db.daily_attendance.find({
        "worker_id": worker_id,
        "date": {
            "$gte": start_date.strftime("%Y-%m-%d"),
            "$lte": end_date.strftime("%Y-%m-%d")
        }
    }, {"_id": 0}).sort("date", -1).to_list(100)
    
    # Get worker name
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0, "name": 1})
    worker_name = worker["name"] if worker else "Unknown"
    
    results = []
    for r in records:
        duration_minutes = r.get("duration_minutes")
        if r.get("punch_in_time") and not r.get("punch_out_time"):
            punch_in = datetime.fromisoformat(r["punch_in_time"])
            duration_minutes = int((datetime.now(timezone.utc) - punch_in).total_seconds() / 60)
        
        results.append({
            "id": r["id"],
            "date": r["date"],
            "punch_in_time": r.get("punch_in_time"),
            "punch_out_time": r.get("punch_out_time"),
            "duration_minutes": duration_minutes,
            "duration_formatted": format_duration(duration_minutes) if duration_minutes else None,
            "status": r.get("status", "ABSENT")
        })
    
    return {
        "worker_name": worker_name,
        "records": results
    }


# ========== Admin Attendance Routes ==========

@router.get("/admin/stats")
async def get_attendance_stats(
    date: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get attendance statistics for a date (default: today)"""
    target_date = date or get_today_date()
    
    # Total workers
    total_workers = await db.users.count_documents({"role": "worker", "is_active": True})
    
    # Today's attendance breakdown
    present = await db.daily_attendance.count_documents({
        "date": target_date,
        "status": "PRESENT"
    })
    
    in_progress = await db.daily_attendance.count_documents({
        "date": target_date,
        "status": "IN_PROGRESS"
    })
    
    absent = total_workers - present - in_progress
    
    # Total hours worked today
    pipeline = [
        {"$match": {"date": target_date, "duration_minutes": {"$ne": None}}},
        {"$group": {"_id": None, "total_minutes": {"$sum": "$duration_minutes"}}}
    ]
    agg_result = await db.daily_attendance.aggregate(pipeline).to_list(1)
    total_minutes = agg_result[0]["total_minutes"] if agg_result else 0
    total_hours = round(total_minutes / 60, 1)
    
    return AttendanceStats(
        total_workers=total_workers,
        present_today=present,
        absent_today=absent,
        in_progress=in_progress,
        total_hours_today=total_hours
    )


@router.get("/admin/report")
async def get_attendance_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    worker_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 500,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get attendance report with filters"""
    # Default to last 7 days if no dates provided
    if not end_date:
        end_date = get_today_date()
    if not start_date:
        start_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)
        start_date = start_dt.strftime("%Y-%m-%d")
    
    query = {
        "date": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    if worker_id:
        query["worker_id"] = worker_id
    
    if status:
        query["status"] = status
    
    records = await db.daily_attendance.find(query, {"_id": 0}).sort("date", -1).to_list(limit)
    
    # Get all worker names
    worker_ids = list(set([r["worker_id"] for r in records]))
    workers = await db.users.find(
        {"id": {"$in": worker_ids}},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(500)
    worker_map = {w["id"]: w["name"] for w in workers}
    
    results = []
    for r in records:
        duration_minutes = r.get("duration_minutes")
        if r.get("punch_in_time") and not r.get("punch_out_time"):
            punch_in = datetime.fromisoformat(r["punch_in_time"])
            duration_minutes = int((datetime.now(timezone.utc) - punch_in).total_seconds() / 60)
        
        results.append(DailyAttendanceResponse(
            id=r["id"],
            worker_id=r["worker_id"],
            worker_name=worker_map.get(r["worker_id"], "Unknown"),
            date=r["date"],
            punch_in_time=datetime.fromisoformat(r["punch_in_time"]) if r.get("punch_in_time") else None,
            punch_out_time=datetime.fromisoformat(r["punch_out_time"]) if r.get("punch_out_time") else None,
            duration_minutes=duration_minutes,
            duration_formatted=format_duration(duration_minutes) if duration_minutes else None,
            status=r.get("status", "ABSENT")
        ))
    
    return results


@router.get("/admin/workers")
async def get_all_workers_attendance_today(
    date: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get all workers with their attendance status for a date"""
    target_date = date or get_today_date()
    
    # Get all active workers
    workers = await db.users.find(
        {"role": "worker", "is_active": True},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    ).to_list(500)
    
    # Get attendance records for the date
    attendance_records = await db.daily_attendance.find(
        {"date": target_date},
        {"_id": 0}
    ).to_list(500)
    
    attendance_map = {r["worker_id"]: r for r in attendance_records}
    
    results = []
    for worker in workers:
        record = attendance_map.get(worker["id"])
        
        if record:
            duration_minutes = record.get("duration_minutes")
            if record.get("punch_in_time") and not record.get("punch_out_time"):
                punch_in = datetime.fromisoformat(record["punch_in_time"])
                duration_minutes = int((datetime.now(timezone.utc) - punch_in).total_seconds() / 60)
            
            results.append({
                "worker_id": worker["id"],
                "worker_name": worker["name"],
                "worker_email": worker["email"],
                "date": target_date,
                "punch_in_time": record.get("punch_in_time"),
                "punch_out_time": record.get("punch_out_time"),
                "duration_minutes": duration_minutes,
                "duration_formatted": format_duration(duration_minutes) if duration_minutes else None,
                "status": record.get("status", "ABSENT")
            })
        else:
            results.append({
                "worker_id": worker["id"],
                "worker_name": worker["name"],
                "worker_email": worker["email"],
                "date": target_date,
                "punch_in_time": None,
                "punch_out_time": None,
                "duration_minutes": None,
                "duration_formatted": None,
                "status": "ABSENT"
            })
    
    # Sort: IN_PROGRESS first, then PRESENT, then ABSENT
    status_order = {"IN_PROGRESS": 0, "PRESENT": 1, "ABSENT": 2}
    results.sort(key=lambda x: (status_order.get(x["status"], 3), x["worker_name"]))
    
    return results


@router.get("/admin/export")
async def export_attendance(
    start_date: str,
    end_date: str,
    format: str = "json",
    current_user: dict = Depends(require_roles("admin"))
):
    """Export attendance data"""
    records = await db.daily_attendance.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).sort("date", -1).to_list(5000)
    
    # Get worker names
    worker_ids = list(set([r["worker_id"] for r in records]))
    workers = await db.users.find(
        {"id": {"$in": worker_ids}},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    ).to_list(500)
    worker_map = {w["id"]: {"name": w["name"], "email": w["email"]} for w in workers}
    
    export_data = []
    for r in records:
        worker_info = worker_map.get(r["worker_id"], {"name": "Unknown", "email": ""})
        duration_minutes = r.get("duration_minutes")
        
        export_data.append({
            "date": r["date"],
            "worker_name": worker_info["name"],
            "worker_email": worker_info["email"],
            "punch_in_time": r.get("punch_in_time"),
            "punch_out_time": r.get("punch_out_time"),
            "duration_hours": round(duration_minutes / 60, 2) if duration_minutes else 0,
            "status": r.get("status", "ABSENT")
        })
    
    if format == "csv":
        # Return CSV formatted string
        import csv
        import io
        output = io.StringIO()
        if export_data:
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
        return {"csv_data": output.getvalue(), "filename": f"attendance_{start_date}_to_{end_date}.csv"}
    
    return export_data
