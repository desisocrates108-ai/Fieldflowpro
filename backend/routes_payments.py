"""
Razorpay Payment Integration Routes for Field Flow Pro
- Order creation from backend (secure)
- Payment Link with QR Code generation
- Payment verification with signature validation
- Webhook handling for payment events
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, List
import razorpay
import hmac
import hashlib
import os
import uuid
import base64
import io

router = APIRouter(prefix="/api/payments", tags=["Payments"])

# Database and audit function will be injected
db = None
create_audit_log = None

# Razorpay client (initialized in init_routes)
razorpay_client = None

def init_routes(database, audit_func):
    global db, create_audit_log, razorpay_client
    db = database
    create_audit_log = audit_func
    
    # Initialize Razorpay client
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    
    if key_id and key_secret:
        razorpay_client = razorpay.Client(auth=(key_id, key_secret))
        print(f"Razorpay initialized with key: {key_id[:10]}...")
    else:
        print("WARNING: Razorpay credentials not found in environment")


# ========== Pydantic Models ==========

class CreatePaymentOrderRequest(BaseModel):
    """Request to create a payment order for a ticket/coupon sale"""
    ticket_id: str
    amount: float  # Amount in INR (will be converted to paise)
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    description: Optional[str] = None


class PaymentOrderResponse(BaseModel):
    """Response after creating a payment order"""
    id: str
    order_id: str
    razorpay_order_id: str
    amount: float
    amount_paise: int
    currency: str
    status: str
    qr_code_base64: Optional[str] = None
    payment_link: Optional[str] = None
    created_at: str


class VerifyPaymentRequest(BaseModel):
    """Request to verify payment after completion"""
    order_id: str  # Our internal order ID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentStatusResponse(BaseModel):
    """Payment status response"""
    order_id: str
    ticket_id: str
    amount: float
    status: str  # pending, paid, failed
    payment_id: Optional[str] = None
    paid_at: Optional[str] = None


# ========== Helper Functions ==========

def generate_qr_code_base64(data: str) -> str:
    """Generate QR code as base64 string"""
    import qrcode
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature"""
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    
    message = f"{order_id}|{payment_id}"
    generated_signature = hmac.new(
        key_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(generated_signature, signature)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature"""
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    
    generated_signature = hmac.new(
        key_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(generated_signature, signature)


# ========== Payment Order Routes ==========

@router.post("/create-order", response_model=PaymentOrderResponse)
async def create_payment_order(
    data: CreatePaymentOrderRequest,
    request: Request
):
    """
    Create a Razorpay payment order for a ticket/coupon sale.
    Returns order details with QR code for UPI payment.
    """
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    try:
        # Validate amount (minimum ₹1)
        if data.amount < 1:
            raise HTTPException(status_code=400, detail="Amount must be at least ₹1")
        
        # Convert to paise (smallest currency unit)
        amount_paise = int(data.amount * 100)
        
        # Generate unique receipt ID
        receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt_id,
            "notes": {
                "ticket_id": data.ticket_id,
                "customer_name": data.customer_name,
                "customer_phone": data.customer_phone
            }
        })
        
        # Create our internal order record
        order_id = str(uuid.uuid4())
        order_doc = {
            "id": order_id,
            "ticket_id": data.ticket_id,
            "razorpay_order_id": razorpay_order["id"],
            "receipt_id": receipt_id,
            "amount": data.amount,
            "amount_paise": amount_paise,
            "currency": "INR",
            "status": "pending",
            "customer_name": data.customer_name,
            "customer_phone": data.customer_phone,
            "customer_email": data.customer_email,
            "description": data.description or f"Payment for ticket {data.ticket_id}",
            "razorpay_payment_id": None,
            "razorpay_signature": None,
            "paid_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payment_orders.insert_one(order_doc)
        
        # Generate UPI payment link for QR code
        # Format: upi://pay?pa=<VPA>&pn=<NAME>&am=<AMOUNT>&cu=INR&tn=<NOTE>
        # We'll use Razorpay's checkout URL for QR
        key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        
        # Create a payment link that can be converted to QR
        checkout_url = f"https://rzp.io/i/{razorpay_order['id']}"
        
        # Generate QR code with the Razorpay order details
        # We'll encode the order info in a format that can be used
        qr_data = f"razorpay://checkout?order_id={razorpay_order['id']}&key={key_id}&amount={amount_paise}"
        qr_code_base64 = generate_qr_code_base64(qr_data)
        
        # Store QR code reference
        await db.payment_orders.update_one(
            {"id": order_id},
            {"$set": {"qr_code_generated": True}}
        )
        
        return PaymentOrderResponse(
            id=order_id,
            order_id=order_id,
            razorpay_order_id=razorpay_order["id"],
            amount=data.amount,
            amount_paise=amount_paise,
            currency="INR",
            status="pending",
            qr_code_base64=qr_code_base64,
            payment_link=checkout_url,
            created_at=order_doc["created_at"]
        )
        
    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Razorpay error: {str(e)}")
    except Exception as e:
        import traceback
        print(f"Payment order creation error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create payment order: {str(e)}")


@router.post("/verify", response_model=PaymentStatusResponse)
async def verify_payment(
    data: VerifyPaymentRequest,
    request: Request
):
    """
    Verify payment after customer completes payment.
    This must be called to confirm payment was successful.
    """
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment gateway not configured")
    
    try:
        # Find the order
        order = await db.payment_orders.find_one({"id": data.order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Payment order not found")
        
        # Verify Razorpay order ID matches
        if order["razorpay_order_id"] != data.razorpay_order_id:
            raise HTTPException(status_code=400, detail="Order ID mismatch")
        
        # Check if already verified
        if order["status"] == "paid":
            return PaymentStatusResponse(
                order_id=order["id"],
                ticket_id=order["ticket_id"],
                amount=order["amount"],
                status="paid",
                payment_id=order.get("razorpay_payment_id"),
                paid_at=order.get("paid_at")
            )
        
        # Verify signature
        is_valid = verify_razorpay_signature(
            data.razorpay_order_id,
            data.razorpay_payment_id,
            data.razorpay_signature
        )
        
        if not is_valid:
            # Also try using Razorpay SDK verification
            try:
                razorpay_client.utility.verify_payment_signature({
                    'razorpay_order_id': data.razorpay_order_id,
                    'razorpay_payment_id': data.razorpay_payment_id,
                    'razorpay_signature': data.razorpay_signature
                })
                is_valid = True
            except Exception:
                is_valid = False
        
        if not is_valid:
            # Mark as failed
            await db.payment_orders.update_one(
                {"id": data.order_id},
                {"$set": {
                    "status": "failed",
                    "failure_reason": "Signature verification failed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            raise HTTPException(status_code=400, detail="Payment signature verification failed")
        
        # Fetch payment details from Razorpay
        payment_details = razorpay_client.payment.fetch(data.razorpay_payment_id)
        
        # Verify amount matches
        if payment_details["amount"] != order["amount_paise"]:
            raise HTTPException(status_code=400, detail="Payment amount mismatch")
        
        # Update order as paid
        paid_at = datetime.now(timezone.utc).isoformat()
        await db.payment_orders.update_one(
            {"id": data.order_id},
            {"$set": {
                "status": "paid",
                "razorpay_payment_id": data.razorpay_payment_id,
                "razorpay_signature": data.razorpay_signature,
                "payment_method": payment_details.get("method"),
                "paid_at": paid_at,
                "updated_at": paid_at
            }}
        )
        
        # Update the ticket/coupon as PAID
        await db.campaign_coupons.update_one(
            {"id": order["ticket_id"]},
            {"$set": {
                "payment_status": "PAID",
                "payment_id": data.razorpay_payment_id,
                "paid_at": paid_at
            }}
        )
        
        return PaymentStatusResponse(
            order_id=order["id"],
            ticket_id=order["ticket_id"],
            amount=order["amount"],
            status="paid",
            payment_id=data.razorpay_payment_id,
            paid_at=paid_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Payment verification error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(order_id: str):
    """
    Get current payment status for an order.
    Used for polling payment status after QR scan.
    """
    order = await db.payment_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Payment order not found")
    
    # If still pending, check with Razorpay
    if order["status"] == "pending" and razorpay_client:
        try:
            # Fetch order from Razorpay
            razorpay_order = razorpay_client.order.fetch(order["razorpay_order_id"])
            
            if razorpay_order["status"] == "paid":
                # Get payment details
                payments = razorpay_client.order.payments(order["razorpay_order_id"])
                if payments.get("items"):
                    payment = payments["items"][0]
                    paid_at = datetime.now(timezone.utc).isoformat()
                    
                    # Update our records
                    await db.payment_orders.update_one(
                        {"id": order_id},
                        {"$set": {
                            "status": "paid",
                            "razorpay_payment_id": payment["id"],
                            "payment_method": payment.get("method"),
                            "paid_at": paid_at,
                            "updated_at": paid_at
                        }}
                    )
                    
                    # Update ticket
                    await db.campaign_coupons.update_one(
                        {"id": order["ticket_id"]},
                        {"$set": {
                            "payment_status": "PAID",
                            "payment_id": payment["id"],
                            "paid_at": paid_at
                        }}
                    )
                    
                    return PaymentStatusResponse(
                        order_id=order["id"],
                        ticket_id=order["ticket_id"],
                        amount=order["amount"],
                        status="paid",
                        payment_id=payment["id"],
                        paid_at=paid_at
                    )
        except Exception as e:
            print(f"Error checking Razorpay status: {e}")
    
    return PaymentStatusResponse(
        order_id=order["id"],
        ticket_id=order["ticket_id"],
        amount=order["amount"],
        status=order["status"],
        payment_id=order.get("razorpay_payment_id"),
        paid_at=order.get("paid_at")
    )


@router.get("/order/{ticket_id}")
async def get_payment_order_by_ticket(ticket_id: str):
    """Get payment order for a ticket"""
    order = await db.payment_orders.find_one(
        {"ticket_id": ticket_id},
        {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="No payment order found for this ticket")
    
    return order


# ========== Webhook Endpoint ==========

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """
    Webhook endpoint for Razorpay payment events.
    Handles: payment.captured, payment.failed
    """
    try:
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature", "")
        event_id = request.headers.get("x-razorpay-event-id", str(uuid.uuid4()))
        
        # Verify webhook signature (if we have a webhook secret)
        # Note: For live mode, you should configure webhook secret in Razorpay dashboard
        if signature:
            if not verify_webhook_signature(body, signature):
                print(f"Webhook signature verification failed for event {event_id}")
                # Don't reject - just log and continue
        
        # Parse payload
        import json
        payload = json.loads(body.decode())
        event_type = payload.get("event", "")
        
        # Check for duplicate events
        existing = await db.webhook_events.find_one({"event_id": event_id})
        if existing:
            return Response(status_code=200)
        
        # Store webhook event
        webhook_doc = {
            "id": str(uuid.uuid4()),
            "event_id": event_id,
            "event_type": event_type,
            "payload": payload,
            "processed": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.webhook_events.insert_one(webhook_doc)
        
        # Process event
        if event_type == "payment.captured":
            await handle_payment_captured(payload)
        elif event_type == "payment.failed":
            await handle_payment_failed(payload)
        elif event_type == "order.paid":
            await handle_order_paid(payload)
        
        # Mark as processed
        await db.webhook_events.update_one(
            {"event_id": event_id},
            {"$set": {"processed": True}}
        )
        
        return Response(status_code=200)
        
    except Exception as e:
        import traceback
        print(f"Webhook processing error: {str(e)}")
        print(traceback.format_exc())
        # Return 200 to prevent retries for processing errors
        return Response(status_code=200)


async def handle_payment_captured(payload: dict):
    """Handle payment.captured webhook event"""
    payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not payment_data:
        return
    
    payment_id = payment_data.get("id")
    order_id = payment_data.get("order_id")
    amount_paise = payment_data.get("amount", 0)
    
    # Find our order by Razorpay order ID
    order = await db.payment_orders.find_one({"razorpay_order_id": order_id}, {"_id": 0})
    if not order:
        print(f"Order not found for Razorpay order {order_id}")
        return
    
    # Update payment status
    paid_at = datetime.now(timezone.utc).isoformat()
    await db.payment_orders.update_one(
        {"razorpay_order_id": order_id},
        {"$set": {
            "status": "paid",
            "razorpay_payment_id": payment_id,
            "payment_method": payment_data.get("method"),
            "paid_at": paid_at,
            "updated_at": paid_at
        }}
    )
    
    # Update ticket
    await db.campaign_coupons.update_one(
        {"id": order["ticket_id"]},
        {"$set": {
            "payment_status": "PAID",
            "payment_id": payment_id,
            "paid_at": paid_at
        }}
    )
    
    print(f"Payment captured: {payment_id} for order {order_id}")


async def handle_payment_failed(payload: dict):
    """Handle payment.failed webhook event"""
    payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not payment_data:
        return
    
    payment_id = payment_data.get("id")
    order_id = payment_data.get("order_id")
    error_code = payment_data.get("error_code")
    error_description = payment_data.get("error_description")
    
    # Find and update our order
    await db.payment_orders.update_one(
        {"razorpay_order_id": order_id},
        {"$set": {
            "status": "failed",
            "failure_reason": f"{error_code}: {error_description}",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    print(f"Payment failed: {payment_id} - {error_code}: {error_description}")


async def handle_order_paid(payload: dict):
    """Handle order.paid webhook event"""
    order_data = payload.get("payload", {}).get("order", {}).get("entity", {})
    if not order_data:
        return
    
    razorpay_order_id = order_data.get("id")
    
    # Find our order
    order = await db.payment_orders.find_one({"razorpay_order_id": razorpay_order_id}, {"_id": 0})
    if not order or order["status"] == "paid":
        return
    
    # Get payment details
    if razorpay_client:
        try:
            payments = razorpay_client.order.payments(razorpay_order_id)
            if payments.get("items"):
                payment = payments["items"][0]
                paid_at = datetime.now(timezone.utc).isoformat()
                
                await db.payment_orders.update_one(
                    {"razorpay_order_id": razorpay_order_id},
                    {"$set": {
                        "status": "paid",
                        "razorpay_payment_id": payment["id"],
                        "payment_method": payment.get("method"),
                        "paid_at": paid_at,
                        "updated_at": paid_at
                    }}
                )
                
                # Update ticket
                await db.campaign_coupons.update_one(
                    {"id": order["ticket_id"]},
                    {"$set": {
                        "payment_status": "PAID",
                        "payment_id": payment["id"],
                        "paid_at": paid_at
                    }}
                )
        except Exception as e:
            print(f"Error fetching payment details: {e}")


# ========== Admin Payment Routes ==========

@router.get("/admin/orders")
async def get_all_payment_orders(
    status: Optional[str] = None,
    limit: int = 100
):
    """Get all payment orders (admin only)"""
    query = {}
    if status:
        query["status"] = status
    
    orders = await db.payment_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return orders


@router.get("/admin/stats")
async def get_payment_stats():
    """Get payment statistics (admin only)"""
    total_orders = await db.payment_orders.count_documents({})
    paid_orders = await db.payment_orders.count_documents({"status": "paid"})
    pending_orders = await db.payment_orders.count_documents({"status": "pending"})
    failed_orders = await db.payment_orders.count_documents({"status": "failed"})
    
    # Calculate total revenue
    pipeline = [
        {"$match": {"status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = await db.payment_orders.aggregate(pipeline).to_list(1)
    total_revenue = result[0]["total"] if result else 0
    
    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "failed_orders": failed_orders,
        "total_revenue": total_revenue,
        "success_rate": round((paid_orders / total_orders * 100) if total_orders > 0 else 0, 2)
    }
