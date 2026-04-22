# Field Flow Pro - Product Requirements Document

## Original Problem Statement
Build a full-stack field operations management platform ("Field Flow Pro") for managing workers, campaigns, coupons, branches, CRE operations, expenses, attendance, and real-time intelligence dashboards.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver) + JWT Auth + Pydantic
- **Frontend**: React + Tailwind CSS + Shadcn UI + React Router
- **Integrations**: Razorpay (payments), Tesseract.js (OCR), xlsx (Excel export), qrcode.react (QR generation)

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

### Sold Coupons Page
- Full sold coupon history with enriched data, filters, Excel export

### Data Entry System
- Worker Data Entry + Admin view with today's count + Excel export

### QR Lead Capture System (Campaign-Based)
- **General QR**: `/qr-lead-form` — captures leads without campaign
- **Campaign QR**: `/qr-lead-form?campaign=CODE` — captures leads under specific campaign
- **Admin Campaign Management** (`/admin/qr-leads` → Campaigns tab):
  - Create campaigns (name + optional description → auto-generates code)
  - Campaign cards with QR code preview, download, copy URL, lead count, delete
- **Admin Leads Data** (`/admin/qr-leads` → Leads tab):
  - Table with Campaign and Source columns (Campaign/General badges)
  - Filters: search, campaign dropdown, source filter (General/Campaign), date range
  - Excel export includes Campaign Name column
- **Public Form**: Mobile-friendly, FieldFlow Pro branding, shows "Campaign: CODE" badge when applicable
- **Backend**: `qr_leads` collection (campaign_code, campaign_name, source), `qr_campaigns` collection
- **Endpoints**:
  - `POST /api/qr-leads` (public)
  - `GET /api/admin/qr-leads` (admin, with campaign_code + source_filter params)
  - `POST /api/admin/qr-campaigns` (admin)
  - `GET /api/admin/qr-campaigns` (admin, with lead counts)
  - `DELETE /api/admin/qr-campaigns/{id}` (admin)

### Command Center Dashboard
- IST-aware stats with auto-refresh + bcrypt fix

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Live Map (Mapbox), WebSocket real-time updates
- DB migration (PostgreSQL), Image storage (S3)
- Vite migration, PWA, Real SMS (Twilio)
