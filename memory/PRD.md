# FieldFlow Pro - Product Requirements Document

## Overview
FieldFlow Pro is a production-ready, pan-India field revenue intelligence system for field service companies. Supports Admin, Worker, CRE, and Branch roles with comprehensive coupon management, sales tracking, expense handling, and fraud detection.

## Current Version: 4.1.0
**Last Updated**: February 22, 2026
**Status**: ✅ ALL SYSTEM UPDATES COMPLETE

---

## Recent Updates (v4.1.0)

### 1. Campaign Creation - Start/End Code Range ✅
- Input: `start_code` and `end_code`
- Auto-calculates total (end - start)
- **NO hardcoded limits** - tested with 500, 700, 1000 coupons
- Example: UT100 to UT300 creates 200 coupons (UT100-UT299)

### 2. Worker Sale Flow - Simplified ✅
- **Removed OCR from sale submission**
- Flow: Validate coupon → Customer details → Branch select → Submit
- Photo capture is optional
- GPS validation (<100m accuracy required)

### 3. Worker My Sales - Enhanced ✅
- Now includes: **Worker Name**, **Branch Name**, **Campaign Name**
- API: `GET /api/campaigns/worker/my-sales`

### 4. CRE Dashboard - Excel-Style ✅
- **Date Filters**: Today, Yesterday, 7D, Custom Range
- **Sortable columns**: Date, Customer, Mobile, Coupon, Campaign, Branch, Worker, Status, Remarks
- **Search**: By name, phone, or coupon code
- **Campaign/Branch filters**
- **CSV Export** button
- **Quick Call Tab**: Search + scrollable contact list

### 5. Expense Approval System ✅
- Admin can Approve/Reject with reason
- **Only APPROVED expenses affect net_payable**
- Worker sees status and rejection reason

### 6. Branch Management ✅
- **Remove/Deactivate** with dependency check
- If dependencies exist → Soft delete (deactivate)
- If no dependencies → Hard delete

---

## API Endpoints

### Campaign APIs
```
POST /api/campaigns                    # Create with start_code/end_code
GET  /api/campaigns                    # List all
GET  /api/campaigns/{id}/coupons       # Get coupons (limit=1000)
POST /api/campaigns/validate-code      # Validate coupon code
POST /api/campaigns/worker-sale        # Complete sale (no OCR)
GET  /api/campaigns/worker/my-sales    # Worker's sales history
```

### CRE APIs
```
GET  /api/cre/customers                # List customers
     ?from_date=YYYY-MM-DD             # Date filter
     ?to_date=YYYY-MM-DD               # Date filter
     ?pending_only=true                # Only pending calls
GET  /api/cre/dashboard/stats          # Dashboard stats
POST /api/cre/calls/{coupon_id}/log    # Log a call
POST /api/cre/calls/{log_id}/remarks   # Add remarks (mandatory)
```

### Expense APIs
```
POST  /api/expenses                    # Submit expense
GET   /api/expenses                    # List expenses
PATCH /api/expenses/{id}/approve       # Approve/Reject
      {"approved": true}               # Approve
      {"approved": false, "rejection_reason": "..."}  # Reject
```

### Branch APIs
```
POST   /api/branches                   # Create branch
GET    /api/branches                   # List branches
DELETE /api/branches/{id}              # Remove/Deactivate
PATCH  /api/branches/{id}/activate     # Re-activate
```

### Intelligence APIs (Elite v4.0)
```
GET  /api/intelligence/realtime-metrics
GET  /api/intelligence/worker-scores
GET  /api/intelligence/fraud-alerts
POST /api/intelligence/scan-fraud
GET  /api/intelligence/inactive-workers
GET  /api/intelligence/area-intelligence
```

---

## Test Results

### v4.1.0 Tests: ✅ 100% PASS (22/22 backend tests)
- Worker My Sales API with joins
- CRE Date Filter
- Coupon Range Generation (no limits)
- CRE Dashboard Excel Table
- Quick Call Section
- CSV Export

### Verified Campaigns
| Campaign | Prefix | Coupons | Notes |
|----------|--------|---------|-------|
| Range Test 200 | RNG | 200 | RNG100-RNG299 |
| Final Test | FIN | 100 | FIN500-FIN599 |
| Large Test | LRG | 500 | No limit verified |
| Diwali | TT | 700 | No limit verified |
| Ahemdabad | UT100 | 1000 | No limit verified |

---

## Test Credentials
- **Admin**: testadmin@fieldflow.com / admin123
- **Worker**: testworker@fieldflow.com / worker123
- **CRE**: testcre@fieldflow.com / cre123
- **Branch**: testbranch@fieldflow.com / branch123

---

## Business Rules

### Campaign
- Prefix mismatch → Rejected
- End ≤ Start → Rejected
- Overlap with existing → Rejected
- Total = End - Start (end code exclusive)

### Expense
- Amount > ₹100 → Bill photo mandatory
- Only APPROVED expenses deduct from net_payable
- Rejected expenses → Show reason to worker

### Branch
- With workers/coupons/encashments → Soft delete (deactivate)
- No dependencies → Hard delete

### GPS
- Accuracy must be ≤ 100m for sale
- >50km in <10 mins → Fraud alert

---

## File Structure
```
/app/backend/
├── server.py                 # Main app (v4.1.0)
├── routes_campaigns.py       # Campaign + Worker Sale + My Sales
├── routes_cre_branch.py      # CRE with date filter + Branch
├── routes_ledger.py          # Expense approval
├── routes_intelligence.py    # Fraud detection, scoring
└── models.py                 # All models

/app/frontend/src/pages/
├── admin/
│   ├── Dashboard.jsx         # Command Center
│   ├── Campaigns.jsx         # Start/End code UI
│   ├── Ledger.jsx            # Expense approval UI
│   └── Branches.jsx          # Remove/Deactivate UI
├── worker/
│   ├── SaleCoupon.jsx        # Simplified sale + My Sales
│   └── Expenses.jsx          # Status + rejection reason
└── cre/
    └── Dashboard.jsx         # Excel table + Quick Call
```

---

## Upcoming Tasks

### P1
- [ ] Live Map with Mapbox (awaiting API key)
- [ ] WebSocket real-time updates for CRE

### P2/Backlog
- [ ] Migrate to PostgreSQL
- [ ] Migrate frontend to Vite
- [ ] S3 storage
- [ ] Offline-first PWA
- [ ] Real SMS (Twilio)

---

## Mocked APIs
- **OTP**: `POST /api/coupons/request-otp` returns mock_otp
