# FieldFlow Pro - Product Requirements Document

## Overview
FieldFlow Pro is a production-ready, pan-India field revenue intelligence system designed for field service companies. The application supports multiple user roles (Admin, Worker, Branch Manager, CRE) with comprehensive coupon management, sales tracking, expense handling, and worker management capabilities.

## Current Version: 3.0.0
**Last Updated**: February 18, 2026

---

## Core Architecture

### Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Authentication**: JWT-based with RBAC (Role-Based Access Control)
- **Real-time**: WebSockets for CRE notifications
- **OCR**: Tesseract.js (client-side)
- **Camera**: react-webcam

### User Roles
1. **Admin**: Full system access, campaign management, worker control, analytics
2. **CRE (Customer Relations Executive)**: Coupon verification, limited analytics
3. **Worker**: Field operations, coupon sales, expense submission
4. **Branch**: Booking management with data masking

---

## Implemented Features (v3.0.0)

### 1. Campaign Management (Admin)
- ✅ Create campaigns with name, price, total count, prefix
- ✅ Auto-generate serial coupon codes (e.g., MUM001-MUM050)
- ✅ Dynamic digit padding based on total count
- ✅ View sold/available counts per campaign
- ✅ Activate/Deactivate campaigns
- ✅ Campaign deletion (if no sales)

### 2. New Coupon Sale Flow (Worker)
- ✅ 4-step process: Code Entry → Photo/Details → Confirm → Success
- ✅ Manual coupon code entry with validation
- ✅ Shows campaign name and price before sale
- ✅ Photo capture with OCR auto-extraction
- ✅ GPS location capture with accuracy check
- ✅ Area selection (optional)
- ✅ Rejection if GPS accuracy >100m

### 3. Worker Ledger System
- ✅ Auto-updates on each sale
- ✅ Tracks: total_coupons_sold, total_revenue, total_advances, total_expenses, net_payable
- ✅ Transaction history with type (SALE/ADVANCE/EXPENSE)
- ✅ Admin can view all worker ledgers
- ✅ Admin can add advance payments

### 4. Expense Module
- ✅ Worker expense submission
- ✅ Expense types: Travel, Food, Equipment, Communication, Accommodation, Other
- ✅ Bill photo mandatory for amounts >₹100
- ✅ GPS location captured
- ✅ Admin approval/rejection workflow
- ✅ Auto-deduct from net payable on approval

### 5. Admin Worker Control
- ✅ Create new workers
- ✅ Disable/Enable worker accounts
- ✅ Reset worker passwords
- ✅ Delete workers (if no sales)
- ✅ Add advance payments
- ✅ View comprehensive worker stats

### 6. Area Management & Analytics
- ✅ Create areas with city, state, coordinates
- ✅ Sales analytics by area, campaign, worker
- ✅ Revenue tracking per area
- ✅ Daily trend data

### 7. Inactivity Tracking
- ✅ Background task monitors worker activity
- ✅ Alert after 3 hours of punch-in with no sales
- ✅ Auto-capture last known location
- ✅ Admin can view/resolve/dismiss alerts

### 8. Security Features
- ✅ Unique coupon codes (no reuse)
- ✅ GPS accuracy validation (reject >100m)
- ✅ Location spoofing detection (>50km in <10 mins)
- ✅ Server-side financial calculations
- ✅ Phone number encryption at rest
- ✅ Data masking based on role
- ✅ Comprehensive audit logging

---

## API Endpoints

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/register`

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}` - Get campaign details
- `GET /api/campaigns/{id}/coupons` - Get campaign coupons
- `PATCH /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign
- `POST /api/campaigns/validate-code` - Validate coupon code
- `POST /api/campaigns/sell` - Complete coupon sale

### Areas
- `POST /api/areas` - Create area
- `GET /api/areas` - List areas
- `GET /api/areas/states` - Get unique states
- `GET /api/areas/cities` - Get cities by state
- `GET /api/areas/analytics/summary` - Sales analytics

### Ledger & Expenses
- `GET /api/workers/{id}/ledger` - Get worker ledger
- `GET /api/workers/{id}/transactions` - Transaction history
- `POST /api/workers/{id}/advance` - Add advance (Admin)
- `GET /api/ledgers/all` - All worker ledgers (Admin)
- `POST /api/expenses` - Submit expense (Worker)
- `GET /api/expenses` - List expenses
- `PATCH /api/expenses/{id}/approve` - Approve/Reject (Admin)

### Admin Worker Control
- `POST /api/admin/workers` - Create worker
- `PATCH /api/admin/workers/{id}` - Update worker
- `POST /api/admin/workers/{id}/disable` - Disable worker
- `POST /api/admin/workers/{id}/enable` - Enable worker
- `DELETE /api/admin/workers/{id}` - Delete worker
- `POST /api/admin/workers/{id}/reset-password` - Reset password
- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/inactivity-alerts` - Inactivity alerts
- `GET /api/admin/spoofing-alerts` - Location spoofing alerts

---

## Database Schema

### campaigns
```json
{
  "id": "uuid",
  "name": "string",
  "price": "float",
  "total_count": "int",
  "prefix": "string",
  "digit_padding": "int",
  "status": "ACTIVE|INACTIVE|COMPLETED",
  "sold_count": "int",
  "created_by": "uuid",
  "created_at": "datetime"
}
```

### campaign_coupons
```json
{
  "id": "uuid",
  "campaign_id": "uuid",
  "code": "string",
  "serial_number": "int",
  "status": "AVAILABLE|SOLD|CANCELLED",
  "sold_by_worker_id": "uuid",
  "sold_at": "datetime",
  "customer_name": "string",
  "customer_phone": "encrypted",
  "photo_url": "string",
  "latitude": "float",
  "longitude": "float",
  "area_id": "uuid"
}
```

### worker_ledgers
```json
{
  "id": "uuid",
  "worker_id": "uuid",
  "total_coupons_sold": "int",
  "total_revenue": "float",
  "total_advances": "float",
  "total_expenses": "float",
  "net_payable": "float",
  "last_updated": "datetime"
}
```

### expenses
```json
{
  "id": "uuid",
  "worker_id": "uuid",
  "type": "string",
  "amount": "float",
  "description": "string",
  "latitude": "float",
  "longitude": "float",
  "bill_photo_url": "string",
  "status": "PENDING|APPROVED|REJECTED",
  "approved_by": "uuid",
  "approved_at": "datetime"
}
```

---

## Test Credentials
- **Admin**: testadmin@fieldflow.com / admin123
- **Worker**: testworker@fieldflow.com / worker123
- **Branch**: testbranch@fieldflow.com / branch123
- **CRE**: testcre@fieldflow.com / cre123

---

## Known Limitations / Future Work

### Mocked APIs
- OTP verification is mocked (returns mock OTP in response)

### Deferred Features (P2+)
- Live Map with Mapbox (requires API key)
- PostgreSQL migration
- AWS S3 image storage
- Real SMS integration (Twilio)
- Offline-first PWA with IndexedDB
- React + Vite migration
- Advanced fraud detection
- Worker performance scoring

---

## Changelog

### v3.0.0 (February 18, 2026)
- **Major**: Replaced auto coupon generation with campaign-based system
- **Added**: Campaign Management with prefix-based coupon codes
- **Added**: New 4-step coupon sale flow with manual code entry
- **Added**: Worker Ledger System (sales, advances, expenses, net payable)
- **Added**: Expense Module with photo requirement validation
- **Added**: Inactivity Tracking with 3-hour alerts
- **Added**: Location Spoofing Detection
- **Added**: Admin Worker Control (create/disable/reset/delete/advance)
- **Added**: Area Management with analytics
- **Enhanced**: Admin Dashboard with comprehensive stats

### v2.1.0 (February 17, 2026)
- Added RBAC enhancement with data masking
- Added audit logging
- Started OCR-based coupon issuance

### v1.0.0 (Initial)
- Basic authentication
- Initial coupon and booking flow
