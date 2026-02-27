# Field Flow Pro - Product Requirements Document
## Pan-India Field Revenue Intelligence System v5.0.0

---

## Original Problem Statement

Build a production-ready, offline-first Progressive Web App (PWA) for a field service company called "Field Flow Pro". The application has evolved from a simple coupon app to a comprehensive "pan-India field revenue intelligence system" (Elite v4.0).

### Core Requirements
- Multi-role system: Admin, Worker, Branch Manager, CRE
- Campaign and coupon management with range-based generation
- Worker financial ledgers and expense tracking
- GPS-based sales tracking with fraud detection
- Real-time admin dashboard with intelligence features

---

## User Personas

1. **Admin**: Full system control, user management, campaign creation, analytics
2. **Worker**: Field sales, coupon distribution, expense submission, attendance
3. **Branch Manager**: Coupon encashment, local oversight
4. **CRE (Customer Relations Executive)**: Customer follow-up, call logging

---

## What's Been Implemented

### v5.0.0 - Attendance & Cash Management (February 27, 2026)

#### P0 - Attendance Module (Completed)
- [x] **Worker Punch-In/Out**: Field workers can punch in/out via GPS
  - No fixed shift times (fieldwork flexibility)
  - Status tracking: NOT_STARTED → IN_PROGRESS → PRESENT
  - Location capture on punch-in/out
  - Duration calculation in hours/minutes
- [x] **Admin Attendance Dashboard**: Real-time attendance monitoring
  - Stats: Total Workers, Present, Working, Absent, Total Hours
  - Date picker for historical data
  - Search and filter by status
  - Export to CSV functionality
  - Worker-by-worker breakdown

#### P0 - Worker Cash Permission (Completed)
- [x] **Cash Toggle in Admin Workers**: ON/OFF toggle for each worker
  - Controls whether worker can accept cash payments
  - Persists to `cash_allowed` field in user record
- [x] **Sale Flow Cash Visibility**: 
  - Workers with cash_allowed=true see both Cash and QR/UPI options
  - Workers with cash_allowed=false see ONLY QR/UPI
  - Warning message shown when cash is disabled

#### P0 - Cash/QR Payment Tracking (Completed)
- [x] **Payment Mode in Sales**: `payment_mode` field (CASH/QR) stored per sale
- [x] **Ledger Cash/QR Breakdown**:
  - Stats cards: Cash Collected, QR/UPI Collected
  - Table columns: Cash, QR/UPI per worker
  - API returns `total_cash_collected`, `total_qr_collected`

#### P0 - Campaign Deletion (Completed)
- [x] **Safe Delete Logic**:
  - Campaign with sold/issued coupons → Error, suggest deactivation
  - Campaign with no activity → Allow permanent delete
  - Delete icon added to campaign list

#### P0 - Bug Fix: Bill Preview (Completed)
- [x] **Static File Serving**: /api/uploads/* serves uploaded files
- [x] **URL Construction**: Frontend correctly builds full URL for bill photos

#### P1 - Admin UI Refactor (Completed)
- [x] **Remove Create Worker**: Centralized in Login Management panel
- [x] **Cash Column**: Added to Workers table
- [x] **Theme #ED1C24**: Applied globally

### v4.2.0 - Production Ready (February 24, 2026)

#### P0 - Critical (Completed)
- [x] **Coupon Range Generation Fix**: No artificial limits - tested with 100, 300+ coupons successfully
- [x] **Public Signup Removed**: `/api/auth/register` route removed - returns 404
- [x] **Login Management Panel**: Admin can create/manage Workers, Branch, CRE users
  - Create users with role assignment
  - Password reset functionality
  - Activate/Deactivate accounts
  - Delete users (with dependency checks)
- [x] **4-Step Worker Sale Flow**: 
  1. Enter & Validate Coupon Code
  2. Capture Photo (Optional - enables OCR)
  3. Enter Customer Details
  4. Select Branch & Confirm
- [x] **OCR is Optional**: Non-blocking, auto-fills if available

#### P1 - High Priority (Completed)
- [x] **API Key Management Panel**: Generate, view, toggle, delete API keys
- [x] **My Sales Enhanced**: Returns `worker_name`, `branch_name`, `city`, `state`
- [x] **Dummy Data Cleanup**: Endpoint to clear test data while keeping users

#### P2 - UI & Security (Completed)
- [x] **Global Theme Color #ED1C24**: Applied to all primary elements
- [x] **JWT & RBAC**: Verified and working
- [x] **Input Validation**: Server-side validation on all endpoints
- [x] **Audit Logging**: All admin actions logged

### v4.0.0 - Elite Features (Previously Completed)
- [x] Worker Performance Scoring Engine
- [x] Fraud Detection Engine (Duplicate Mobile, GPS Clustering)
- [x] Inactive Worker Alerts Panel
- [x] Real-time Admin Dashboard with WebSockets
- [x] Expense Approval System (Approve/Reject)
- [x] Branch Management with safe delete/deactivate

### v3.0.0 - Core System (Previously Completed)
- [x] Multi-role authentication system
- [x] Campaign CRUD with range-based coupon generation
- [x] Worker sales with GPS tracking
- [x] Branch coupon encashment
- [x] CRE customer dashboard
- [x] Financial ledgers and transactions

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh token
- ~~`POST /api/auth/register`~~ - REMOVED (Admin-only user creation)

### Admin - User Management
- `POST /api/admin/users` - Create user (Worker/Branch/CRE)
- `GET /api/admin/users` - List all users
- `GET /api/admin/users/{id}` - Get user details
- `PATCH /api/admin/users/{id}` - Update user
- `POST /api/admin/users/{id}/reset-password` - Reset password
- `POST /api/admin/users/{id}/activate` - Activate user
- `POST /api/admin/users/{id}/deactivate` - Deactivate user
- `DELETE /api/admin/users/{id}` - Delete user
- `POST /api/admin/workers/{id}/toggle-cash` - Toggle cash permission

### Attendance
- `POST /api/attendance/punch-in` - Worker punch in (with GPS)
- `POST /api/attendance/punch-out` - Worker punch out (with GPS)
- `GET /api/attendance/today` - Worker's today attendance status
- `GET /api/attendance/my-history` - Worker's attendance history
- `GET /api/attendance/admin/stats` - Admin: attendance statistics
- `GET /api/attendance/admin/workers` - Admin: all workers attendance
- `GET /api/attendance/admin/report` - Admin: filtered attendance report
- `GET /api/attendance/admin/export` - Admin: export to CSV

### Admin - API Keys
- `POST /api/admin/api-keys` - Generate new API key
- `GET /api/admin/api-keys` - List all API keys
- `POST /api/admin/api-keys/{id}/toggle` - Toggle key status
- `DELETE /api/admin/api-keys/{id}` - Delete API key

### Admin - System
- `GET /api/admin/database-stats` - Database collection counts
- `POST /api/admin/cleanup-dummy-data` - Clear test data

### Campaigns
- `POST /api/campaigns` - Create campaign with coupon range
- `GET /api/campaigns` - List all campaigns
- `PATCH /api/campaigns/{id}` - Update campaign status
- `DELETE /api/campaigns/{id}` - Delete campaign (safe-delete)
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}/coupons` - Get campaign coupons
- `POST /api/campaigns/validate-code` - Validate coupon code
- `POST /api/campaigns/worker-sale` - Record worker sale

---

## Database Schema

### Core Collections
- `users` - All user accounts (admin, worker, branch, cre)
- `campaigns` - Campaign definitions with pricing
- `campaign_coupons` - Individual coupon records
- `branches` - Branch/location data
- `areas` - Geographic areas

### Financial Collections
- `worker_ledgers` - Worker financial summary
- `ledger_transactions` - Individual transactions
- `expenses` - Worker expense submissions
- `encashments` - Branch encashment records

### Intelligence Collections
- `fraud_alerts` - Detected fraud indicators
- `worker_performance_scores` - Performance metrics
- `inactivity_logs` - Worker inactivity tracking
- `api_keys` - External integration keys
- `audit_logs` - System audit trail

---

## Tech Stack

### Backend
- FastAPI (Python 3.11)
- MongoDB with Motor (async driver)
- JWT authentication with bcrypt
- WebSockets for real-time updates
- APScheduler for background tasks

### Frontend
- React 18 with React Router
- Tailwind CSS + Shadcn/UI components
- Tesseract.js for optional OCR
- react-webcam for photo capture

---

## Remaining Backlog

### P1 - Future Enhancements
- [ ] CRE Dashboard Overhaul (Excel-style grid, advanced filters)
- [ ] Live Map feature using Mapbox
- [ ] WebSocket real-time updates for CRE dashboard

### P2 - Infrastructure
- [ ] Migrate database to PostgreSQL
- [ ] Migrate image storage to AWS S3
- [ ] Migrate frontend to Vite build system
- [ ] Full PWA offline-first strategy
- [ ] Replace mock OTP with Twilio SMS

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | testadmin@fieldflow.com | admin123 |
| Worker | testworker@fieldflow.com | worker123 |
| Branch | testbranch@fieldflow.com | branch123 |
| CRE | testcre@fieldflow.com | cre123 |

---

## Changelog

### February 27, 2026 - v5.0.0 - Attendance & Cash Management
- Implemented comprehensive Attendance Module
  - Worker punch-in/out with GPS tracking
  - Admin dashboard with stats, search, filters, export
  - Status tracking: NOT_STARTED → IN_PROGRESS → PRESENT
- Added Worker Cash Permission Toggle
  - Admin can enable/disable cash payments per worker
  - Sale flow respects cash_allowed setting
- Cash/QR Payment Tracking
  - payment_mode field on sales (CASH/QR)
  - Ledger shows Cash and QR/UPI columns with breakdowns
- Campaign Deletion with safe-delete logic
- Fixed expense bill preview (static file serving)
- Removed Create Worker from Workers page (centralized in Login Management)

### February 26, 2026 - v4.3.0 - Razorpay Integration
- Integrated Razorpay Payment Gateway for UPI/QR payments
- Added 5-step worker sale flow (Coupon → Photo → Details → Branch → Payment)
- Payment mode selection: Cash or UPI/QR
- Real-time payment status checking with auto-refresh
- Webhook integration for payment.captured and payment.failed events
- Admin payment statistics dashboard
- Signature verification for secure payments

### February 24, 2026 - v4.2.0
- Implemented COMPLETE MASTER PRODUCTION PROMPT
- Removed public signup routes
- Added Login Management panel
- Added API Key Management panel
- Implemented 4-step worker sale flow
- Applied global theme color #ED1C24
- Added dummy data cleanup endpoint
- Verified coupon range generation (no limits)

### February 23, 2026 - v4.1.0
- Made OCR optional and non-blocking
- Added worker_name, branch_name to My Sales
- Enhanced CRE dashboard with date filters

### February 22, 2026 - v4.0.0
- Elite features: Fraud detection, performance scoring
- Admin command center with real-time metrics
- Expense approval system
- Branch safe delete/deactivate
