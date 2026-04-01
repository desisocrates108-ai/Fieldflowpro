# Field Flow Pro - Product Requirements Document

## Original Problem Statement
Build a full-stack field operations management platform ("Field Flow Pro") for managing workers, campaigns, coupons, branches, CRE operations, expenses, attendance, and real-time intelligence dashboards.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver) + JWT Auth + Pydantic
- **Frontend**: React + Tailwind CSS + Shadcn UI + React Router
- **Integrations**: Razorpay (payments), Tesseract.js (OCR), xlsx (Excel export)

## Credentials
- Admin: testadmin@fieldflow.com / admin123
- Worker: testworker@fieldflow.com / worker123
- CRE: testcre@fieldflow.com / cre123
- Branch: testbranch@fieldflow.com / branch123

## What's Been Implemented

### Core Features
- Multi-role auth, Campaign management, Coupon lifecycle
- Worker management, Branch management (CRUD + Edit), Expense workflow
- Worker ledger, Area management, Attendance Module
- Admin deletion overhaul (soft/hard/force delete)
- Admin Dashboard with 16 IST-aware stat cards
- CRE Remarks deletable (Admin + CRE RBAC)
- Worker Photo Gallery + Retake in Sale Coupon

### Admin Coupons (Full View)
- Merged campaign_coupons + legacy coupons
- Decrypted phone numbers for admin view
- Photo thumbnail + full-size modal preview
- Status/Source filters, Search, Excel export, Delete

### Data Entry System
- Worker Data Entry: form (name, mobile, city, notes) + own entries table
- Admin Data Entry: all entries, search/filter by worker/date, Excel export

### Branch Management (Latest - April 1, 2026)
- **PATCH /api/branches/{branch_id}**: Update branch name, address, lat/lng, phone
- **Edit Modal**: Prefilled form with all branch fields
- **Reusable BranchForm** component for create + edit
- Actions column: Edit (pencil), Activate (power), Delete (trash)

## Key API Endpoints
- `GET /api/admin/dashboard-stats` - IST-aware stats
- `GET /api/admin/coupons` - Merged coupons with decrypted phone + photo
- `DELETE /api/admin/coupons/{id}?force=true` - Unified delete
- `GET /api/admin/data-entry` - All worker data entries
- `POST /api/worker/data-entry` - Worker creates entry
- `GET /api/worker/data-entry/me` - Worker's own entries
- `PATCH /api/branches/{branch_id}` - Update branch details
- `DELETE /api/cre/call-log/{log_id}` - CRE remark delete

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Live Map (Mapbox), WebSocket real-time updates
- DB migration (PostgreSQL), Image storage (S3)
- Vite migration, PWA, Real SMS (Twilio)
