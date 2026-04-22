# Field Flow Pro - Product Requirements Document

## Original Problem Statement
Build a full-stack field operations management platform ("Field Flow Pro") for managing workers, campaigns, coupons, branches, CRE operations, expenses, attendance, and real-time intelligence dashboards.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver) + JWT Auth + Pydantic
- **Frontend**: React + Tailwind CSS + Shadcn UI + React Router
- **Integrations**: Razorpay (payments), Tesseract.js (OCR), xlsx (Excel export), qrcode.react (QR code generation)

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
- Today's Entry Count: Green card showing IST-aware count

### Sold Coupons Page
- Full sold coupon history with enriched data
- Decrypted customer phone, worker/branch/campaign names
- Photo thumbnails, executive summary badges
- Filters: worker, campaign, branch, date range, Today, search
- Excel export, stats cards

### QR Lead Capture System (April 22, 2026)
- **Public Form** at `/qr-lead-form`: Mobile-friendly, FieldFlow Pro branding
  - Fields: Name, Mobile (10-digit validated), City, State, Vehicle Type (< 160cc / ≥ 160cc)
  - No login required, success message after submit
- **Admin QR Leads** at `/admin/qr-leads`:
  - Stats cards: Total Leads, Today's Leads, Source
  - Table with all columns, search/date filters
  - Excel export, Refresh button
  - Show QR Code dialog with downloadable QR code (PNG)
- **Backend**: `POST /api/qr-leads` (public), `GET /api/admin/qr-leads` (admin)
- **DB**: `qr_leads` collection with IST timestamps

### Command Center Dashboard
- IST-aware stats: revenue_today, sales_today, active_workers_now, punched_in, etc.
- Single consolidated endpoint: GET /api/admin/dashboard-stats
- Auto-refresh + manual Refresh button

## Key API Endpoints
- `POST /api/qr-leads` — Public, customer lead from QR scan
- `GET /api/admin/qr-leads` — Admin view with search/date filters
- `GET /api/admin/dashboard-stats` — IST-aware stats
- `GET /api/admin/sold-coupons` — Sold coupons with filters
- `GET /api/admin/coupons` — Merged coupons with decrypted phone
- `GET /api/admin/data-entry` — Worker data entries (with today_count)
- `POST /api/campaigns/worker-sale` — Worker sale submission
- `PATCH /api/branches/{branch_id}` — Update branch details

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Live Map (Mapbox), WebSocket real-time updates
- DB migration (PostgreSQL), Image storage (S3)
- Vite migration, PWA, Real SMS (Twilio)
