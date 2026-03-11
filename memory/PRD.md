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
  routes_admin.py - Admin management endpoints
  routes_campaigns.py - Campaign CRUD + coupon management
  routes_cre_branch.py - CRE & Branch operations
  routes_intelligence.py - Analytics & scoring
  routes_ledger.py - Financial ledger
  routes_payments.py - Razorpay integration
  routes_attendance.py - Punch in/out
  routes_areas.py - Area management
  models.py - Pydantic models
  auth.py - JWT auth
  utils.py - Encryption, helpers

/app/frontend/src/ - React SPA
  pages/admin/ - Admin dashboard, workers, campaigns, coupons, branches, etc.
  pages/worker/ - Worker dashboard, sale coupon, attendance
  pages/cre/ - CRE dashboard
  pages/branch/ - Branch dashboard
  components/ - Shared components (Layout, ForceDeleteModal, PaymentQR, etc.)
  lib/api.js - API client
```

## Key DB Collections
- users, campaigns, campaign_coupons, coupons (legacy), cre_call_logs
- attendance, daily_attendance, expenses, encashments
- worker_ledgers, ledger_transactions, areas, bookings
- audit_logs, inactivity_logs, fraud_alerts

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

### Recent Completions (March 2026)
- Attendance Module (punch-in/out + admin dashboard)
- Worker "Cash Allowed" logic
- Admin deletion overhaul (soft/hard/force delete for all entities)
- ForceDeleteModal reusable component
- Expense bill image preview fix

### P0 Fixes Completed (March 11, 2026)
1. **P0-4: Force Delete Coupon** - FIXED. New unified `DELETE /api/admin/coupons/{id}?force=true` checks both `coupons` and `campaign_coupons` collections. Root cause was frontend calling wrong collection's endpoint.
2. **P0-2: Admin Dashboard Stats** - FIXED. New consolidated `GET /api/admin/dashboard-stats` with IST timezone (Asia/Kolkata). Returns 18 real stats fields. Frontend updated to use `adminAPI.getDashboardStats()`.
3. **P0-1: Worker Photo Gallery + Retake** - DONE. SaleCoupon step 2 now has Capture, Gallery Upload, Retake, and Upload Different buttons with proper source tracking.
4. **P0-3: CRE Remarks Deletable** - DONE. `DELETE /api/cre/call-log/{log_id}` with admin/CRE RBAC. Delete icon in CRE Dashboard remarks column. Audit logged.

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
