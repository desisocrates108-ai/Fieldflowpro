# FieldFlow Pro - Product Requirements Document

## Overview
FieldFlow Pro is a production-ready, pan-India field revenue intelligence system designed for field service companies. The application supports multiple user roles (Admin, Worker, Branch Manager, CRE) with comprehensive coupon management, sales tracking, expense handling, fraud detection, and worker performance analytics.

## Current Version: 4.0.0 (Elite)
**Last Updated**: February 18, 2026
**Status**: ✅ PHASE 1 COMPLETE & VERIFIED

---

## Version History

### v4.0.0 - Elite Edition (February 18, 2026)
**Phase 1 Complete: Fraud Detection & Performance Scoring**
- ✅ Fraud Detection Engine
- ✅ Worker Performance Scoring (0-100)
- ✅ Inactive Worker Alert Dashboard
- ✅ Real-time Metrics
- ✅ Area Intelligence
- ✅ Admin Command Center redesign

### v3.1.0 (February 18, 2026)
- Full end-to-end testing completed
- All core features verified (34 tests passed)

### v3.0.0 (February 18, 2026)
- Campaign-based coupon system
- Worker Ledger System
- CRE Call Management
- Branch Encashment

---

## Core Architecture

### Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Authentication**: JWT-based with RBAC
- **Real-time**: WebSockets (backend ready)
- **OCR**: Tesseract.js (client-side)
- **Camera**: react-webcam
- **Reverse Geocoding**: aiohttp + OpenStreetMap

### User Roles
1. **Admin**: Full system access, campaign management, fraud monitoring, worker analytics
2. **CRE**: Customer call management, FULL phone access
3. **Worker**: Field operations, coupon sales, expense submission
4. **Branch**: Coupon encashment, MASKED phone access

---

## Phase 1 Features (v4.0.0) - ALL VERIFIED ✅

### 1. Fraud Detection Engine
- ✅ **DUPLICATE_MOBILE**: Detects same mobile used 3+ times
- ✅ **GPS_CLUSTERING**: Detects 5+ sales from same location in 20 mins
- ✅ **IMPOSSIBLE_TRAVEL**: Detects GPS jump >50km in <10 mins
- ✅ **HIGH_EXPENSE_RATIO**: Detects expense to revenue ratio >50%
- ✅ Manual fraud scan trigger for admin
- ✅ Resolve/Dismiss fraud alerts

### 2. Worker Performance Scoring
- ✅ Score calculation (0-100 scale)
- ✅ Five weighted components:
  - Conversion Score (25%)
  - Sales per Day Score (25%)
  - Revenue Score (20%)
  - Attendance Score (15%)
  - Inactivity Score (15%)
- ✅ Grade assignment (A+ to F)
- ✅ Worker rankings leaderboard

### 3. Inactive Worker Alert Dashboard
- ✅ Worker name and area displayed
- ✅ Hours inactive shown
- ✅ Map-ready GPS coordinates
- ✅ Last sale information
- ✅ Resolve button for alerts

### 4. Real-Time Metrics
- ✅ Live sales today
- ✅ Live revenue today
- ✅ Active workers now
- ✅ Total punched in today
- ✅ Inactive worker alerts count
- ✅ Fraud alerts count
- ✅ Pending expenses count
- ✅ Encashments today

### 5. Area Intelligence
- ✅ Sales by city
- ✅ Sales by state
- ✅ Campaign performance by geography
- ✅ Top performing areas

### 6. Admin Command Center (Redesigned)
- ✅ 8 real-time metric cards
- ✅ Fraud Alerts panel with resolve/dismiss
- ✅ Inactive Workers panel with GPS
- ✅ Worker Performance Rankings table
- ✅ Quick action buttons (Refresh, Fraud Scan)

---

## Existing Features (v3.x) - ALL VERIFIED ✅

### Campaign Management
- Create campaigns with auto-generated codes
- Dynamic zero padding for coupon codes
- Sold/available counts per campaign
- Archive campaigns with sales

### Worker Sale Flow
- Manual coupon code entry with validation
- Photo capture with OCR
- GPS location capture (<100m accuracy)
- Branch selection (mandatory)
- Reverse geocoding

### Worker Ledger
- Total Revenue tracking
- Total Expenses tracking
- Total Advances tracking
- Net Payable calculation
- Server-side calculations only

### CRE Dashboard
- Customer list with full phone
- Call logging
- Mandatory remarks
- Call history

### Branch Dashboard
- Customer list (last 4 digits)
- Coupon encashment
- Duplicate prevention

---

## API Endpoints

### Intelligence APIs (v4.0 - NEW)
- `GET /api/intelligence/realtime-metrics` - Real-time dashboard metrics
- `GET /api/intelligence/worker-scores` - All worker performance scores
- `GET /api/intelligence/worker-scores/{id}` - Individual worker score
- `GET /api/intelligence/fraud-alerts` - Fraud alerts list
- `POST /api/intelligence/scan-fraud` - Trigger fraud scan
- `PATCH /api/intelligence/fraud-alerts/{id}/resolve` - Resolve alert
- `PATCH /api/intelligence/fraud-alerts/{id}/dismiss` - Dismiss alert
- `GET /api/intelligence/inactive-workers` - Inactive workers panel
- `GET /api/intelligence/area-intelligence` - Area sales data

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/auth/me`

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns/validate-code` - Validate code
- `POST /api/campaigns/worker-sale` - Complete sale

### Ledger & Expenses
- `GET /api/workers/{id}/ledger` - Worker ledger
- `POST /api/expenses` - Submit expense
- `PATCH /api/expenses/{id}/approve` - Approve/Reject

### CRE & Branch
- `GET /api/cre/customers` - Full phone access
- `POST /api/cre/calls/{id}/log` - Log call
- `GET /api/branch/customers` - Masked phone
- `POST /api/branch/encash` - Encash coupon

---

## Test Credentials
- **Admin**: testadmin@fieldflow.com / admin123
- **Worker**: testworker@fieldflow.com / worker123
- **Branch**: testbranch@fieldflow.com / branch123
- **CRE**: testcre@fieldflow.com / cre123

---

## Testing Summary

### v4.0.0 Phase 1 Test Results: ✅ 100% PASS
- **Backend Tests**: 23/23 passed
- **Frontend Tests**: All Phase 1 UI elements working
- **Test Report**: `/app/test_reports/iteration_4.json`

### v3.1.0 Test Results: ✅ 100% PASS
- **Backend Tests**: 34/34 passed
- **Test Report**: `/app/test_reports/iteration_3.json`

---

## Upcoming Tasks (Phase 2)

### P1: CRE Dashboard Overhaul
- [ ] Excel-style grid table
- [ ] Date filters (Today/Yesterday/Custom Range)
- [ ] Campaign & Branch filters
- [ ] Search & Pagination
- [ ] CSV/Excel export

### P1: WebSocket Real-time Updates
- [ ] Frontend WebSocket connection
- [ ] Live updates for CRE dashboard

---

## Future Tasks (Backlog)

### P2: Infrastructure
- [ ] Migrate frontend to Vite
- [ ] Migrate to PostgreSQL
- [ ] S3-compatible storage
- [ ] AES-256 encryption upgrade

### P2: Features
- [ ] Offline-first PWA
- [ ] Live Map with Mapbox (awaiting API key)
- [ ] Real SMS integration (Twilio)
- [ ] Advanced fraud detection

---

## File Structure
```
/app/
├── backend/
│   ├── server.py             # Main FastAPI app (v4.0.0)
│   ├── models.py             # All Pydantic models
│   ├── routes_intelligence.py # Fraud, Scores, Metrics (NEW)
│   ├── routes_campaigns.py   # Campaign & Sale routes
│   ├── routes_ledger.py      # Ledger & Expense routes
│   ├── routes_cre_branch.py  # CRE & Branch routes
│   ├── routes_admin.py       # Admin routes
│   └── background_tasks.py   # Inactivity checker
└── frontend/
    ├── src/
    │   ├── lib/api.js        # intelligenceAPI added
    │   └── pages/
    │       └── admin/
    │           └── Dashboard.jsx  # Command Center (Redesigned)
    └── memory/
        └── PRD.md
```

---

## Mocked APIs
- **OTP Verification**: `POST /api/coupons/request-otp` returns `mock_otp` in response for testing

---

## 3rd Party Integrations
- **Mapbox**: Selected but deferred (awaiting API key)
- **Tesseract.js**: Client-side OCR
- **aiohttp**: Reverse geocoding
