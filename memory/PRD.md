# FieldFlow Pro - Product Requirements Document

## Overview
FieldFlow Pro is a production-ready, pan-India field revenue intelligence system designed for field service companies. The application supports multiple user roles (Admin, Worker, Branch Manager, CRE) with comprehensive coupon management, sales tracking, expense handling, and worker management capabilities.

## Current Version: 3.1.0
**Last Updated**: February 18, 2026
**Status**: ✅ VERIFIED & STABLE

---

## Core Architecture

### Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Authentication**: JWT-based with RBAC (Role-Based Access Control)
- **Real-time**: WebSockets for CRE notifications (backend ready)
- **OCR**: Tesseract.js (client-side)
- **Camera**: react-webcam
- **Reverse Geocoding**: aiohttp + OpenStreetMap Nominatim

### User Roles
1. **Admin**: Full system access, campaign management, worker control, analytics
2. **CRE (Customer Relations Executive)**: Customer call management, FULL phone access
3. **Worker**: Field operations, coupon sales, expense submission
4. **Branch**: Coupon encashment, MASKED phone access (last 4 digits only)

---

## Implemented Features (v3.1.0) - ALL VERIFIED ✅

### 1. Campaign Management (Admin)
- ✅ Create campaigns with name, price, total count, prefix
- ✅ Auto-generate serial coupon codes (e.g., MUM001-MUM050)
- ✅ Dynamic digit padding based on total count
- ✅ View sold/available counts per campaign
- ✅ Activate/Deactivate campaigns
- ✅ Campaign deletion (if no sales)

### 2. New Coupon Sale Flow (Worker)
- ✅ Manual coupon code entry with validation
- ✅ Shows campaign name and price before sale
- ✅ Photo capture with OCR auto-extraction
- ✅ GPS location capture with accuracy check (<100m required)
- ✅ Branch selection (mandatory)
- ✅ Reverse geocoding for city/state/area

### 3. Worker Ledger System
- ✅ Auto-updates on each sale
- ✅ Tracks: total_coupons_sold, total_revenue, total_advances, total_expenses, net_payable
- ✅ Transaction history with type (SALE/ADVANCE/EXPENSE)
- ✅ Admin can view all worker ledgers
- ✅ Admin can add advance payments
- ✅ Server-side financial calculations (verified)

### 4. Expense Module
- ✅ Worker expense submission
- ✅ Expense types: Travel, Food, Equipment, Communication, Accommodation, Other
- ✅ Bill photo mandatory for amounts >₹100
- ✅ GPS location captured
- ✅ Admin approval/rejection workflow
- ✅ Auto-deduct from net payable on approval

### 5. CRE Call Management
- ✅ Customer list with FULL phone numbers
- ✅ Log calls via API
- ✅ Mandatory remarks after each call
- ✅ Call history tracking
- ✅ Dashboard stats (today's calls, pending calls)

### 6. Branch Encashment
- ✅ Customer list with MASKED phone (last 4 only)
- ✅ Encash coupon by code
- ✅ Duplicate encashment prevention (verified)
- ✅ Branch assignment required

### 7. Admin Worker Control
- ✅ Create new workers
- ✅ Disable/Enable worker accounts
- ✅ Reset worker passwords
- ✅ Delete workers (if no sales)
- ✅ Add advance payments
- ✅ View comprehensive worker stats
- ✅ Assign branch to branch users

### 8. Security Features (All Verified)
- ✅ Unique coupon codes (no reuse - tested)
- ✅ GPS accuracy validation (reject >100m)
- ✅ Location spoofing detection (>50km in <10 mins)
- ✅ Server-side financial calculations
- ✅ Phone number encryption at rest
- ✅ Data masking based on role
- ✅ Comprehensive audit logging
- ✅ No duplicate encashment

---

## API Endpoints

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/refresh`
- `GET /api/auth/me`

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}` - Get campaign details
- `GET /api/campaigns/{id}/coupons` - Get campaign coupons
- `PATCH /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign
- `POST /api/campaigns/validate-code` - Validate coupon code
- `POST /api/campaigns/sell` - Complete coupon sale
- `POST /api/campaigns/worker-sale` - Worker sale with branch selection

### CRE Routes
- `GET /api/cre/dashboard/stats` - CRE dashboard stats
- `GET /api/cre/customers` - Customer list (full phone)
- `POST /api/cre/calls/{coupon_id}/log` - Log call
- `POST /api/cre/calls/{call_log_id}/remarks` - Add remarks
- `GET /api/cre/calls/history` - Call history

### Branch Routes
- `GET /api/branch/customers` - Customer list (masked phone)
- `POST /api/branch/encash` - Encash coupon

### Ledger & Expenses
- `GET /api/workers/{id}/ledger` - Get worker ledger
- `GET /api/workers/{id}/transactions` - Transaction history
- `POST /api/workers/{id}/advance` - Add advance (Admin)
- `GET /api/ledgers/all` - All worker ledgers (Admin)
- `POST /api/expenses` - Submit expense (Worker)
- `GET /api/expenses` - List expenses
- `PATCH /api/expenses/{id}/approve` - Approve/Reject (Admin)

### Admin Routes
- `POST /api/admin/workers` - Create worker
- `PATCH /api/admin/workers/{id}` - Update worker
- `POST /api/admin/workers/{id}/disable` - Disable worker
- `POST /api/admin/workers/{id}/enable` - Enable worker
- `DELETE /api/admin/workers/{id}` - Delete worker
- `POST /api/admin/workers/{id}/reset-password` - Reset password
- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/cre-remarks` - All CRE remarks
- `GET /api/admin/encashments` - All encashments
- `PATCH /api/users/{user_id}/branch` - Assign branch to user

---

## Test Credentials
- **Admin**: testadmin@fieldflow.com / admin123
- **Worker**: testworker@fieldflow.com / worker123
- **Branch**: testbranch@fieldflow.com / branch123
- **CRE**: testcre@fieldflow.com / cre123

---

## Testing Summary (v3.1.0)

### Test Results: ✅ 100% PASS
- **Backend Tests**: 34/34 passed
- **Frontend Tests**: All 4 role dashboards working
- **Test Report**: `/app/test_reports/iteration_3.json`

### Verified Scenarios
1. ✅ Campaign creation with auto-generated serial codes
2. ✅ Coupon validation returns campaign name/price
3. ✅ Worker sale flow with GPS validation
4. ✅ Ledger auto-update after sale
5. ✅ Expense submission with photo validation
6. ✅ CRE call logging with mandatory remarks
7. ✅ CRE sees FULL phone numbers
8. ✅ Branch sees MASKED phone numbers
9. ✅ Branch encashment with duplicate prevention
10. ✅ Financial calculations (net_payable = revenue - advances - expenses)

---

## Mocked APIs
- **OTP Verification**: `POST /api/coupons/request-otp` returns `mock_otp` in response for testing

---

## Upcoming Tasks (P1)

### 1. Live Map with Mapbox
- Worker locations on real-time map
- **Blocked**: Awaiting Mapbox API key from user

### 2. WebSocket Real-time Updates
- Backend WebSocket infrastructure ready
- Frontend integration needed for CRE dashboard live updates

---

## Future Tasks (P2/Backlog)

- [ ] Offline-first PWA with IndexedDB
- [ ] Migrate frontend to React + Vite
- [ ] Migrate database to PostgreSQL
- [ ] AWS S3 image storage
- [ ] Real SMS integration (Twilio)
- [ ] Advanced fraud detection
- [ ] Worker performance scoring
- [ ] AES-256 encryption upgrade

---

## Changelog

### v3.1.0 (February 18, 2026)
- **VERIFIED**: Full end-to-end testing completed
- **Added**: PATCH /api/users/{user_id}/branch for branch assignment
- **Tested**: 34 backend tests, all 4 frontend dashboards
- **Confirmed**: All security features working (no duplicate sales/encashments)

### v3.0.0 (February 18, 2026)
- **Major**: Replaced auto coupon generation with campaign-based system
- **Added**: Campaign Management with prefix-based coupon codes
- **Added**: New coupon sale flow with manual code entry
- **Added**: Worker Ledger System
- **Added**: Expense Module
- **Added**: CRE Call Management
- **Added**: Branch Encashment
- **Added**: Inactivity Tracking
- **Added**: Location Spoofing Detection
- **Added**: Admin Worker Control

### v2.1.0 (February 17, 2026)
- Added RBAC enhancement with data masking
- Added audit logging
- Started OCR-based coupon issuance

### v1.0.0 (Initial)
- Basic authentication
- Initial coupon and booking flow
