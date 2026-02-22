# FieldFlow Pro - Product Requirements Document

## Overview
FieldFlow Pro is a production-ready, pan-India field revenue intelligence system designed for field service companies. The application supports multiple user roles (Admin, Worker, Branch Manager, CRE) with comprehensive coupon management, sales tracking, expense handling, fraud detection, and worker performance analytics.

## Current Version: 4.0.0 (Elite)
**Last Updated**: February 19, 2026
**Status**: ✅ PHASE 1 + ADMIN UPGRADES COMPLETE

---

## Version History

### v4.0.1 - Admin Panel Upgrades (February 19, 2026)
**All features verified:**
- ✅ Campaign Creation with Start/End Code Range
- ✅ Expense Approval System (Approve/Reject with reasons)
- ✅ Bill Photo Viewer Modal
- ✅ Branch Remove/Deactivate with dependency check
- ✅ Worker sees expense status and rejection reason

### v4.0.0 - Elite Edition (February 18, 2026)
**Phase 1 Complete:**
- ✅ Fraud Detection Engine
- ✅ Worker Performance Scoring (0-100)
- ✅ Inactive Worker Alert Dashboard
- ✅ Real-time Metrics
- ✅ Area Intelligence
- ✅ Admin Command Center redesign

### v3.1.0 (February 18, 2026)
- Full end-to-end testing completed (34 tests passed)

---

## Admin Panel Features (v4.0.1)

### 1. Campaign Creation - Start/End Code Range ✅
**New Logic:**
- Input: `start_code` (e.g., "UT100") and `end_code` (e.g., "UT400")
- System extracts prefix automatically
- Validates:
  - Same prefix in both codes
  - End number > Start number
  - No code range overlap with existing campaigns
- Auto-calculates total: `Total = End - Start`
- Example: UT100 to UT400 creates 300 coupons (UT100-UT399)

**API:** `POST /api/campaigns`
```json
{
  "name": "Campaign Name",
  "price": 199,
  "start_code": "UT100",
  "end_code": "UT400"
}
```

### 2. Expense Approval System ✅
**Workflow:**
1. Worker submits expense (status: PENDING)
2. Admin views expenses in Ledger → Worker → Expenses dialog
3. Admin can:
   - **Approve**: Expense added to worker ledger, deducts from net_payable
   - **Reject**: Requires reason, does NOT affect net_payable

**API:** `PATCH /api/expenses/{id}/approve`
```json
// Approve
{"approved": true}

// Reject
{"approved": false, "rejection_reason": "Invalid receipt"}
```

**Business Rule:** Only APPROVED expenses affect financial calculations.

### 3. Bill Photo Viewer ✅
- View button in expense table opens modal
- Displays uploaded bill image
- Handles both relative and absolute URLs
- Error fallback for missing images

### 4. Branch Management - Remove/Deactivate ✅
**Logic:**
- If branch has dependencies (workers, coupons, encashments):
  - **Soft delete** → Deactivate only
- If no dependencies:
  - **Hard delete** → Permanent removal

**APIs:**
- `DELETE /api/branches/{id}` - Remove/Deactivate
- `PATCH /api/branches/{id}/activate` - Re-activate

### 5. Worker Expense Status Display ✅
- Worker sees: PENDING / APPROVED / REJECTED
- If rejected, shows rejection reason
- Stats show approved total only

---

## Phase 1 Features (v4.0.0)

### Fraud Detection Engine ✅
- DUPLICATE_MOBILE: Same mobile 3+ times
- GPS_CLUSTERING: 5+ sales from same GPS in 20 mins
- IMPOSSIBLE_TRAVEL: GPS jump >50km in <10 mins
- HIGH_EXPENSE_RATIO: Expense to revenue >50%

### Worker Performance Scoring ✅
- Score: 0-100 scale
- Components: Conversion (25%), Sales/Day (25%), Revenue (20%), Attendance (15%), Inactivity (15%)
- Grades: A+ to F

### Admin Command Center ✅
- 8 real-time metric cards
- Fraud Alerts panel
- Inactive Workers panel with GPS
- Worker Rankings table

---

## API Endpoints Summary

### Campaign APIs
- `POST /api/campaigns` - Create with start_code/end_code
- `GET /api/campaigns` - List all
- `GET /api/campaigns/{id}/coupons` - Get campaign coupons
- `PATCH /api/campaigns/{id}` - Update status

### Expense APIs
- `POST /api/expenses` - Submit expense
- `GET /api/expenses` - List expenses
- `PATCH /api/expenses/{id}/approve` - Approve/Reject

### Branch APIs
- `POST /api/branches` - Create branch
- `GET /api/branches` - List branches
- `DELETE /api/branches/{id}` - Remove/Deactivate
- `PATCH /api/branches/{id}/activate` - Re-activate

### Intelligence APIs
- `GET /api/intelligence/realtime-metrics`
- `GET /api/intelligence/worker-scores`
- `GET /api/intelligence/fraud-alerts`
- `POST /api/intelligence/scan-fraud`
- `GET /api/intelligence/inactive-workers`
- `GET /api/intelligence/area-intelligence`

---

## Test Credentials
- **Admin**: testadmin@fieldflow.com / admin123
- **Worker**: testworker@fieldflow.com / worker123
- **Branch**: testbranch@fieldflow.com / branch123
- **CRE**: testcre@fieldflow.com / cre123

---

## Testing Summary

### v4.0.1 Admin Panel Tests: ✅ ALL PASSING
- Campaign start/end range validation
- Prefix mismatch detection
- End < Start rejection
- Expense approve/reject workflow
- Ledger updates correctly
- Branch delete/deactivate logic
- Worker expense status display

### v4.0.0 Phase 1 Tests: ✅ 100% PASS (23/23)
- Fraud detection APIs
- Worker scoring APIs
- Real-time metrics
- Area intelligence

---

## Upcoming Tasks (Phase 2)

### P1: CRE Dashboard Overhaul
- [ ] Excel-style grid table
- [ ] Date filters (Today/Yesterday/Custom)
- [ ] Campaign & Branch filters
- [ ] Search & Pagination
- [ ] CSV/Excel export

### P1: WebSocket Real-time Updates
- [ ] Frontend WebSocket connection
- [ ] Live updates for CRE dashboard

---

## Future Tasks (Backlog)

- [ ] Migrate frontend to Vite
- [ ] Migrate to PostgreSQL
- [ ] S3-compatible storage
- [ ] AES-256 encryption upgrade
- [ ] Offline-first PWA
- [ ] Live Map with Mapbox (awaiting API key)
- [ ] Real SMS integration (Twilio)

---

## File Structure
```
/app/
├── backend/
│   ├── server.py             # Main FastAPI (v4.0.0)
│   ├── models.py             # Pydantic models
│   ├── routes_intelligence.py # Fraud, Scores, Metrics
│   ├── routes_campaigns.py   # Campaign with start/end range
│   ├── routes_ledger.py      # Expense approval
│   └── routes_cre_branch.py  # CRE & Branch
└── frontend/
    └── src/pages/admin/
        ├── Campaigns.jsx     # Start/End code UI
        ├── Ledger.jsx        # Expense approval UI
        ├── Branches.jsx      # Remove/Deactivate UI
        └── Dashboard.jsx     # Command Center
```

---

## Mocked APIs
- **OTP Verification**: Returns mock_otp for testing
