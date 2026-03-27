# Field Flow Pro - Product Requirements Document

## Original Problem Statement
Build a full-stack field operations management platform ("Field Flow Pro") for managing workers, campaigns, coupons, branches, CRE operations, expenses, attendance, and real-time intelligence dashboards.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver) + JWT Auth + Pydantic
- **Frontend**: React + Tailwind CSS + Shadcn UI + React Router
- **Integrations**: Razorpay (payments), Tesseract.js (OCR), xlsx (Excel export)

## Architecture
```
/app/backend/
  server.py - Main app, core endpoints, worker data entry
  routes_admin.py - Admin management, dashboard stats, admin coupons, admin data entry
  routes_campaigns.py - Campaign CRUD + coupon management
  routes_cre_branch.py - CRE & Branch operations + call log delete
  routes_intelligence.py - Analytics & scoring
  routes_ledger.py - Financial ledger
  routes_payments.py - Razorpay integration
  routes_attendance.py - Punch in/out
  routes_areas.py - Area management
  models.py - Pydantic models
  auth.py - JWT auth, utils.py - Encryption/helpers

/app/frontend/src/
  pages/admin/ - Dashboard, Workers, Campaigns, Coupons, Branches, Ledger, DataEntry, etc.
  pages/worker/ - Dashboard, SaleCoupon, Attendance, Expenses, DataEntry
  pages/cre/ - CRE Dashboard
  pages/branch/ - Branch Dashboard
  components/ - Layout, ForceDeleteModal, PaymentQR, etc.
  lib/api.js - API client
```

## Credentials
- Admin: testadmin@fieldflow.com / admin123
- Worker: testworker@fieldflow.com / worker123
- CRE: testcre@fieldflow.com / cre123
- Branch: testbranch@fieldflow.com / branch123

## What's Been Implemented

### Core Features (Complete)
- Multi-role auth (admin, worker, CRE, branch)
- Campaign management (CRUD, coupon generation, worker assignment)
- Coupon lifecycle (issue, verify, redeem, sell)
- Worker management (create, disable, reset password, cash-allowed)
- Branch management with CRE assignment
- Expense submission and approval workflow
- Worker ledger and financial tracking
- Area management, Attendance Module
- Admin deletion overhaul (soft/hard/force delete)

### P0 Fixes (March 2026)
1. Force Delete Coupon — unified endpoint checks both collections
2. Admin Dashboard Stats — IST-aware consolidated endpoint
3. Worker Photo Gallery + Retake
4. CRE Remarks Deletable

### Session: March 12, 2026
1. Removed "Made with Emergent" badge, rebranded to FieldFlow Pro
2. CRE Remarks delete in Admin Ledger (Actions column, confirmation dialog)
3. Enhanced Command Center Dashboard (16 stat cards, IST timestamp)

### Session: March 27, 2026
1. **Admin Coupons Page Rewrite** — Merged campaign_coupons + legacy coupons into unified view with full customer details (name, mobile, coupon code, campaign, worker, branch, sold date, photo, status, source). Search, status/source filters, photo preview modal, Excel export, delete with confirmation.
2. **Worker Data Entry** — New page replacing "My Sales" in sidebar. Form: Customer Name, Mobile Number, City, Notes. Worker sees own entries table. Backend: POST /api/worker/data-entry, GET /api/worker/data-entry/me. Collection: manual_customer_entries.
3. **Admin Data Entry** — New page showing all worker entries. Search by name/mobile/city, filter by worker/date range. Excel export (admin only). Backend: GET /api/admin/data-entry, GET /api/admin/data-entry/export.

## Key API Endpoints
- `GET /api/admin/dashboard-stats` - IST-aware dashboard stats (19 fields)
- `GET /api/admin/coupons` - Merged coupon view with filters
- `DELETE /api/admin/coupons/{id}?force=true` - Unified coupon delete
- `GET /api/admin/data-entry` - All worker data entries
- `GET /api/admin/data-entry/export` - Export data entries
- `POST /api/worker/data-entry` - Worker creates data entry
- `GET /api/worker/data-entry/me` - Worker's own entries
- `DELETE /api/cre/call-log/{log_id}` - CRE remark delete with RBAC

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Live Map feature (Mapbox)
- WebSocket real-time updates for CRE dashboard
- DB migration: MongoDB → PostgreSQL
- Image storage: Local → AWS S3
- Frontend: React + Vite migration
- Full PWA/offline-first, Replace mock OTP with real SMS (Twilio)
