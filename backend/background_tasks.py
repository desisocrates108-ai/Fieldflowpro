"""
Background Tasks for FieldFlow Pro
- Inactivity tracking
- Scheduled jobs
"""
import asyncio
from datetime import datetime, timezone, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

db = None
INACTIVITY_THRESHOLD_HOURS = 3

def init_background_tasks(database):
    global db
    db = database


async def check_worker_inactivity():
    """
    Check for workers who:
    1. Punched in today
    2. Haven't sold any coupon in 3+ hours since punch-in
    3. Don't already have an active alert
    """
    if not db:
        return
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    threshold_time = now - timedelta(hours=INACTIVITY_THRESHOLD_HOURS)
    
    try:
        # Get today's punch-ins
        punch_ins = await db.attendance.find({
            "type": "PUNCH_IN",
            "timestamp": {"$gte": today_start.isoformat()}
        }, {"_id": 0}).to_list(500)
        
        for punch in punch_ins:
            worker_id = punch["worker_id"]
            punch_time = datetime.fromisoformat(punch["timestamp"])
            
            # Skip if punched in less than 3 hours ago
            if punch_time > threshold_time:
                continue
            
            # Check if worker has punched out
            punch_out = await db.attendance.find_one({
                "worker_id": worker_id,
                "type": "PUNCH_OUT",
                "timestamp": {"$gte": today_start.isoformat()}
            })
            if punch_out:
                continue
            
            # Check if worker has made any sale today
            last_sale = await db.campaign_coupons.find_one({
                "sold_by_worker_id": worker_id,
                "sold_at": {"$gte": punch_time.isoformat()}
            })
            if last_sale:
                continue
            
            # Check if alert already exists for today
            existing_alert = await db.inactivity_logs.find_one({
                "worker_id": worker_id,
                "punch_in_time": {"$gte": today_start.isoformat()},
                "status": "ACTIVE"
            })
            if existing_alert:
                continue
            
            # Get latest location
            location = await db.location_logs.find_one(
                {"worker_id": worker_id},
                {"_id": 0},
                sort=[("timestamp", -1)]
            )
            
            # Fetch current location from the worker's device
            # For now, use last known location
            lat = location["latitude"] if location else None
            lng = location["longitude"] if location else None
            
            # Create inactivity alert
            alert = {
                "id": str(uuid.uuid4()),
                "worker_id": worker_id,
                "punch_in_time": punch_time.isoformat(),
                "alert_time": now.isoformat(),
                "latitude": lat,
                "longitude": lng,
                "hours_inactive": (now - punch_time).total_seconds() / 3600,
                "status": "ACTIVE"
            }
            
            await db.inactivity_logs.insert_one(alert)
            logger.info(f"Inactivity alert created for worker {worker_id}")
            
    except Exception as e:
        logger.error(f"Error in inactivity check: {e}")


async def inactivity_checker_loop():
    """Background loop that runs inactivity checks every 5 minutes"""
    while True:
        await check_worker_inactivity()
        await asyncio.sleep(300)  # Check every 5 minutes


def start_background_tasks(app):
    """Start background tasks when app starts"""
    @app.on_event("startup")
    async def startup_background_tasks():
        asyncio.create_task(inactivity_checker_loop())
        logger.info("Background inactivity checker started")
