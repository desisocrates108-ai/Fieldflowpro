# Field Flow Pro - Product Requirements Document

## Original Problem Statement
Build a full-stack field operations management platform ("Field Flow Pro") for managing workers, campaigns, coupons, branches, CRE (Customer Relations Executive) operations, expenses, attendance, and real-time intelligence dashboards.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver) + JWT Auth + Pydantic
- **Frontend**: React + Tailwind CSS + Shadcn UI + React Router
- **Integrations**: Razorpay (payments), Tesseract.js (OCR), Mapbox (future)

## Architecture
```
/app/backend/ - FastAPI server with modular route files
  server.py - Main app, core endpoints (coupons, auth, etc.)
  routes_admin.py - Admin management + dashboard stats + coupon delete
  routes_campaigns.py - Campaign CRUD + coupon management
  routes_cre_branch.py - CRE & Branch operations + call log delete
  routes_intelligence.py - Analytics & scoring
  routes_ledger.py - Financial ledger
  routes_payments.py - Razorpay integration
  routes_attendance.py - Punch in/out
  routes_areas.py - Area management
  models.py - Pydantic models
  auth.py - JWT auth
  utils.py - Encryption, helpers

/app/frontend/src/ - React SPA
  pages/admin/ - Dashboard, Workers, Campaigns, Coupons, Branches, Ledger, etc.
  pages/worker/ - Worker dashboard, sale coupon, attendance
  pages/cre/ - CRE dashboard
  pages/branch/ - Branch dashboard
  components/ - Shared components (Layout, ForceDeleteModal, PaymentQR, etc.)
  lib/api.js - API client
```

## Credentials
- Admin: testadmin@fieldflow.com / admin123
- Worker: testworker@fieldflow.com / worker123
- CRE: testcre@fieldflow.com / cre123
- Branch: testbranch@fieldflow.com / branch123

## What's Been Implemented

### Core Features (Complete)
- Multi-role authentication (admin, worker, CRE, branch)
- Campaign management (CRUD, coupon generation, worker assignment)
- Coupon lifecycle (issue, verify, redeem, sell)
- Worker management (create, disable, reset password, cash-allowed toggle)
- Branch management with CRE assignment
- Expense submission and approval workflow
- Worker ledger and financial tracking
- Area management
- Attendance Module (punch-in/out + admin dashboard)
- Worker "Cash Allowed" logic
- Admin deletion overhaul (soft/hard/force delete for all entities)
- ForceDeleteModal reusable component

### P0 Fixes (March 2026)
1. **Force Delete Coupon** - Unified `DELETE /api/admin/coupons/{id}?force=true` checks both collections
2. **Admin Dashboard Stats** - Consolidated `GET /api/admin/dashboard-stats` with IST timezone
3. **Worker Photo Gallery + Retake** - SaleCoupon step 2 with Capture/Gallery/Retake/Upload Different
4. **CRE Remarks Deletable** - `DELETE /api/cre/call-log/{log_id}` with RBAC

### Latest Session (March 12, 2026)
1. **Removed "Made with Emergent" badge** - Cleaned index.html, updated page title to "FieldFlow Pro", updated meta description
2. **CRE Remarks Delete in Admin Ledger** - Added Actions column with trash icon, confirmation dialog with remark details, instant row removal, badge count update, success toast
3. **Enhanced Command Center Dashboard** - Added second stats row with 8 additional cards (Revenue Month, Sales Month, Active Campaigns, Coupons Available, Total Workers, Total Branches, Total Areas, Expenses Month). Added IST timestamp display. Backend now returns `total_branches` and includes debug logging.

## Key API Endpoints
- `GET /api/admin/dashboard-stats` - Consolidated IST-aware dashboard stats (19 fields)
- `DELETE /api/admin/coupons/{id}?force=true` - Unified coupon delete (both collections)
- `DELETE /api/cre/call-log/{log_id}` - CRE remark delete with RBAC
- `GET /api/admin/cre-remarks` - Admin view of all CRE remarks
- `POST /api/attendance/punch-in` / `punch-out` - Worker attendance

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Live Map feature (Mapbox)
- WebSocket real-time updates for CRE dashboard
- DB migration: MongoDB → PostgreSQL
- Image storage: Local → AWS S3
- Frontend: React + Vite migration
- Full PWA/offline-first strategy
- Replace mock OTP with real SMS (Twilio)
