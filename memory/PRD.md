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
  routes_admin.py - Admin management, dashboard stats, admin coupons (decrypted), admin data entry
  routes_campaigns.py - Campaign CRUD + coupon management
  routes_cre_branch.py - CRE & Branch operations + call log delete
  routes_intelligence.py - Analytics & scoring
  routes_ledger.py, routes_payments.py, routes_attendance.py, routes_areas.py
  models.py, auth.py, utils.py (encrypt/decrypt mobile)

/app/frontend/src/
  pages/admin/ - Dashboard, Workers, Campaigns, Coupons, Branches, Ledger, DataEntry
  pages/worker/ - Dashboard, SaleCoupon, Attendance, Expenses, DataEntry
  pages/cre/ - CRE Dashboard
  pages/branch/ - Branch Dashboard
  components/ - Layout, ForceDeleteModal, PaymentQR
  lib/api.js - API client
```

## Credentials
- Admin: testadmin@fieldflow.com / admin123
- Worker: testworker@fieldflow.com / worker123
- CRE: testcre@fieldflow.com / cre123
- Branch: testbranch@fieldflow.com / branch123

## What's Been Implemented

### Core Features (Complete)
- Multi-role auth, Campaign management, Coupon lifecycle
- Worker management, Branch management, Expense workflow
- Worker ledger, Area management, Attendance Module
- Admin deletion overhaul (soft/hard/force delete)

### P0 Fixes (March 2026)
1. Force Delete Coupon — unified endpoint checks both collections
2. Admin Dashboard Stats — IST-aware consolidated endpoint (16 stat cards)
3. Worker Photo Gallery + Retake
4. CRE Remarks Deletable + Admin Ledger delete UI

### Admin Coupons (March 27, 2026)
- **Merged View**: campaign_coupons + legacy coupons in one table
- **Decrypted Phone**: Admin sees real mobile numbers (decrypt_mobile from utils.py)
- **Photo Preview**: Thumbnail + full-size modal preview
- **Filters**: Status (SOLD/AVAILABLE/etc.), Source (Campaign/Legacy/All), Search
- **Excel Export**: Download Excel with customer details
- **Delete**: Force delete with confirmation dialog

### Worker & Admin Data Entry (March 27, 2026)
- Worker Data Entry page (form + own entries table)
- Admin Data Entry page (all entries, search/filter/Excel export)
- Sidebar: Worker has "Data Entry" (replaced My Sales), Admin has "Data Entry"

## Key API Endpoints
- `GET /api/admin/dashboard-stats` - IST-aware stats
- `GET /api/admin/coupons` - Merged coupons with decrypted phone + photo
- `DELETE /api/admin/coupons/{id}?force=true` - Unified delete
- `GET /api/admin/data-entry` - All worker data entries
- `POST /api/worker/data-entry` - Worker creates entry
- `GET /api/worker/data-entry/me` - Worker's own entries
- `DELETE /api/cre/call-log/{log_id}` - CRE remark delete

## Important Technical Notes
- **Phone Encryption**: Customer phones stored encrypted via `encrypt_mobile()` in utils.py. Admin coupons endpoint uses `decrypt_mobile()` to show readable numbers. Other roles see last4 only.
- **Photo URLs**: Stored as relative paths. Backend constructs `/api/uploads/{filename}`. Frontend prepends `REACT_APP_BACKEND_URL` for absolute URLs.

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Live Map (Mapbox), WebSocket real-time updates
- DB migration (PostgreSQL), Image storage (S3)
- Vite migration, PWA, Real SMS (Twilio)
