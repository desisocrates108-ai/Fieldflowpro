"""
Worker Ledger & Expense Routes
- Real-time ledger tracking
- Expense submission with photo validation
- Advance management
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import List, Optional
import base64
import uuid
from pathlib import Path

from models import (
    WorkerLedger, WorkerLedgerResponse, LedgerTransaction, LedgerTransactionResponse,
    AddAdvanceRequest, ExpenseCreate, Expense, ExpenseResponse, ExpenseApproval
)
from auth import get_current_user, require_roles

router = APIRouter(prefix="/api", tags=["Ledger & Expenses"])

db = None
create_audit_log = None
UPLOAD_DIR = None

def init_routes(database, audit_func, upload_dir):
    global db, create_audit_log, UPLOAD_DIR
    db = database
    create_audit_log = audit_func
    UPLOAD_DIR = upload_dir


async def get_or_create_ledger(worker_id: str) -> dict:
    """Get or create worker ledger"""
    ledger = await db.worker_ledgers.find_one({"worker_id": worker_id}, {"_id": 0})
    
    if not ledger:
        new_ledger = WorkerLedger(worker_id=worker_id)
        doc = new_ledger.model_dump()
        doc["last_updated"] = doc["last_updated"].isoformat()
        await db.worker_ledgers.insert_one(doc)
        ledger = doc
    
    return ledger


async def update_worker_ledger(
    worker_id: str,
    transaction_type: str,
    amount: float,
    description: str,
    reference_id: Optional[str] = None,
    created_by: Optional[str] = None,
    payment_mode: Optional[str] = None  # CASH or QR
):
    """Update worker ledger and create transaction record"""
    ledger = await get_or_create_ledger(worker_id)
    
    # Calculate new values based on transaction type
    update_data = {"last_updated": datetime.now(timezone.utc).isoformat()}
    
    if transaction_type == "SALE":
        update_data["total_coupons_sold"] = ledger.get("total_coupons_sold", 0) + 1
        update_data["total_revenue"] = ledger.get("total_revenue", 0) + amount
        # Track payment mode
        if payment_mode == "CASH":
            update_data["total_cash_collected"] = ledger.get("total_cash_collected", 0) + amount
        elif payment_mode == "QR":
            update_data["total_qr_collected"] = ledger.get("total_qr_collected", 0) + amount
    elif transaction_type == "ADVANCE":
        update_data["total_advances"] = ledger.get("total_advances", 0) + amount
    elif transaction_type == "EXPENSE":
        update_data["total_expenses"] = ledger.get("total_expenses", 0) + amount
    
    # Calculate net payable
    total_revenue = update_data.get("total_revenue", ledger.get("total_revenue", 0))
    total_advances = update_data.get("total_advances", ledger.get("total_advances", 0))
    total_expenses = update_data.get("total_expenses", ledger.get("total_expenses", 0))
    update_data["net_payable"] = total_revenue - total_advances - total_expenses
    
    await db.worker_ledgers.update_one(
        {"worker_id": worker_id},
        {"$set": update_data}
    )
    
    # Create transaction record
    transaction = LedgerTransaction(
        worker_id=worker_id,
        type=transaction_type,
        amount=amount,
        description=description,
        reference_id=reference_id,
        created_by=created_by
    )
    
    trans_doc = transaction.model_dump()
    trans_doc["created_at"] = trans_doc["created_at"].isoformat()
    if payment_mode:
        trans_doc["payment_mode"] = payment_mode
    await db.ledger_transactions.insert_one(trans_doc)
    
    return update_data


# ========== Ledger Routes ==========

@router.get("/workers/{worker_id}/ledger", response_model=WorkerLedgerResponse)
async def get_worker_ledger(
    worker_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get worker's ledger summary"""
    # Workers can only view their own ledger
    if current_user["role"] == "worker" and current_user["sub"] != worker_id:
        raise HTTPException(status_code=403, detail="Cannot view other worker's ledger")
    
    ledger = await get_or_create_ledger(worker_id)
    
    # Get worker name
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0, "name": 1})
    worker_name = worker["name"] if worker else "Unknown"
    
    if isinstance(ledger.get("last_updated"), str):
        ledger["last_updated"] = datetime.fromisoformat(ledger["last_updated"])
    
    return WorkerLedgerResponse(
        worker_id=worker_id,
        worker_name=worker_name,
        total_coupons_sold=ledger.get("total_coupons_sold", 0),
        total_revenue=ledger.get("total_revenue", 0),
        total_advances=ledger.get("total_advances", 0),
        total_expenses=ledger.get("total_expenses", 0),
        net_payable=ledger.get("net_payable", 0),
        last_updated=ledger.get("last_updated", datetime.now(timezone.utc))
    )


@router.get("/workers/{worker_id}/transactions", response_model=List[LedgerTransactionResponse])
async def get_worker_transactions(
    worker_id: str,
    type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get worker's transaction history"""
    if current_user["role"] == "worker" and current_user["sub"] != worker_id:
        raise HTTPException(status_code=403, detail="Cannot view other worker's transactions")
    
    query = {"worker_id": worker_id}
    if type:
        query["type"] = type
    
    transactions = await db.ledger_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    results = []
    for t in transactions:
        if isinstance(t.get("created_at"), str):
            t["created_at"] = datetime.fromisoformat(t["created_at"])
        results.append(LedgerTransactionResponse(**t))
    
    return results


@router.post("/workers/{worker_id}/advance")
async def add_advance(
    worker_id: str,
    data: AddAdvanceRequest,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Add advance payment to worker (Admin only)"""
    # Verify worker exists
    worker = await db.users.find_one({"id": worker_id, "role": "worker"}, {"_id": 0})
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    await update_worker_ledger(
        worker_id=worker_id,
        transaction_type="ADVANCE",
        amount=data.amount,
        description=data.description or "Advance payment",
        created_by=current_user["sub"]
    )
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action="ADVANCE_ADDED",
        entity="ledger",
        entity_id=worker_id,
        metadata={"amount": data.amount, "description": data.description},
        request=request
    )
    
    return {"message": f"Advance of ₹{data.amount} added successfully"}


@router.get("/ledgers/all", response_model=List[WorkerLedgerResponse])
async def get_all_ledgers(
    current_user: dict = Depends(require_roles("admin", "cre"))
):
    """Get all workers' ledger summaries"""
    # Get all workers
    workers = await db.users.find({"role": "worker"}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
    
    results = []
    for worker in workers:
        ledger = await get_or_create_ledger(worker["id"])
        
        if isinstance(ledger.get("last_updated"), str):
            ledger["last_updated"] = datetime.fromisoformat(ledger["last_updated"])
        
        results.append(WorkerLedgerResponse(
            worker_id=worker["id"],
            worker_name=worker["name"],
            total_coupons_sold=ledger.get("total_coupons_sold", 0),
            total_revenue=ledger.get("total_revenue", 0),
            total_advances=ledger.get("total_advances", 0),
            total_expenses=ledger.get("total_expenses", 0),
            net_payable=ledger.get("net_payable", 0),
            last_updated=ledger.get("last_updated", datetime.now(timezone.utc))
        ))
    
    # Sort by revenue
    results.sort(key=lambda x: x.total_revenue, reverse=True)
    return results


# ========== Expense Routes ==========

@router.post("/expenses", response_model=ExpenseResponse)
async def submit_expense(
    data: ExpenseCreate,
    request: Request,
    current_user: dict = Depends(require_roles("worker"))
):
    """Submit expense claim"""
    worker_id = current_user["sub"]
    
    # Validate: bill photo mandatory if amount > 100
    if data.amount > 100 and not data.bill_photo_url and not data.image_base64:
        raise HTTPException(
            status_code=400,
            detail="Bill photo is mandatory for expenses above ₹100"
        )
    
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Save photo if provided
    photo_url = data.bill_photo_url
    if data.image_base64 and not photo_url:
        try:
            img_data = base64.b64decode(
                data.image_base64.split(',')[-1] if ',' in data.image_base64 else data.image_base64
            )
            filename = f"expense_{uuid.uuid4()}.jpg"
            filepath = UPLOAD_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(img_data)
            photo_url = f"/uploads/{filename}"
        except Exception as e:
            if data.amount > 100:
                raise HTTPException(status_code=400, detail="Failed to save bill photo")
    
    expense = Expense(
        worker_id=worker_id,
        type=data.type,
        amount=data.amount,
        description=data.description,
        latitude=data.latitude,
        longitude=data.longitude,
        bill_photo_url=photo_url
    )
    
    doc = expense.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.expenses.insert_one(doc)
    
    await create_audit_log(
        user_id=worker_id,
        user_role=current_user["role"],
        action="EXPENSE_SUBMITTED",
        entity="expense",
        entity_id=expense.id,
        metadata={"type": data.type, "amount": data.amount},
        request=request
    )
    
    # Get worker name
    worker = await db.users.find_one({"id": worker_id}, {"_id": 0, "name": 1})
    
    return ExpenseResponse(
        id=expense.id,
        worker_id=worker_id,
        worker_name=worker["name"] if worker else None,
        type=expense.type,
        amount=expense.amount,
        description=expense.description,
        latitude=expense.latitude,
        longitude=expense.longitude,
        bill_photo_url=photo_url,
        status=expense.status,
        approved_by=None,
        approved_at=None,
        rejection_reason=None,
        created_at=expense.created_at
    )


@router.get("/expenses", response_model=List[ExpenseResponse])
async def get_expenses(
    status: Optional[str] = None,
    worker_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get expenses"""
    query = {}
    
    # Workers can only see their own
    if current_user["role"] == "worker":
        query["worker_id"] = current_user["sub"]
    elif worker_id:
        query["worker_id"] = worker_id
    
    if status:
        query["status"] = status
    
    expenses = await db.expenses.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    results = []
    for e in expenses:
        if isinstance(e.get("created_at"), str):
            e["created_at"] = datetime.fromisoformat(e["created_at"])
        if isinstance(e.get("approved_at"), str):
            e["approved_at"] = datetime.fromisoformat(e["approved_at"])
        
        # Get worker name
        worker = await db.users.find_one({"id": e["worker_id"]}, {"_id": 0, "name": 1})
        
        results.append(ExpenseResponse(
            id=e["id"],
            worker_id=e["worker_id"],
            worker_name=worker["name"] if worker else None,
            type=e["type"],
            amount=e["amount"],
            description=e.get("description"),
            latitude=e["latitude"],
            longitude=e["longitude"],
            bill_photo_url=e.get("bill_photo_url"),
            status=e["status"],
            approved_by=e.get("approved_by"),
            approved_at=e.get("approved_at"),
            rejection_reason=e.get("rejection_reason"),
            created_at=e["created_at"]
        ))
    
    return results


@router.patch("/expenses/{expense_id}/approve")
async def approve_expense(
    expense_id: str,
    data: ExpenseApproval,
    request: Request,
    current_user: dict = Depends(require_roles("admin"))
):
    """Approve or reject expense"""
    expense = await db.expenses.find_one({"id": expense_id}, {"_id": 0})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if expense["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Expense is not pending")
    
    now = datetime.now(timezone.utc)
    
    if data.approved:
        # Approve and add to ledger
        await db.expenses.update_one(
            {"id": expense_id},
            {"$set": {
                "status": "APPROVED",
                "approved_by": current_user["sub"],
                "approved_at": now.isoformat()
            }}
        )
        
        # Update ledger
        await update_worker_ledger(
            worker_id=expense["worker_id"],
            transaction_type="EXPENSE",
            amount=expense["amount"],
            description=f"Expense: {expense['type']}",
            reference_id=expense_id,
            created_by=current_user["sub"]
        )
        
        action = "EXPENSE_APPROVED"
        message = "Expense approved and added to ledger"
    else:
        # Reject
        await db.expenses.update_one(
            {"id": expense_id},
            {"$set": {
                "status": "REJECTED",
                "approved_by": current_user["sub"],
                "approved_at": now.isoformat(),
                "rejection_reason": data.rejection_reason
            }}
        )
        action = "EXPENSE_REJECTED"
        message = "Expense rejected"
    
    await create_audit_log(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        action=action,
        entity="expense",
        entity_id=expense_id,
        metadata={"approved": data.approved, "reason": data.rejection_reason},
        request=request
    )
    
    return {"message": message}


# Export the update function for use by other modules
def get_update_ledger_func():
    return update_worker_ledger
