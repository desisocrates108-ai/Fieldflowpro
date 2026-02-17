# FieldFlow Pro - Product Requirements Document

## Original Problem Statement
Build a production-ready, offline-first Progressive Web App (PWA) for a field service company that combines workforce management, GPS attendance tracking, coupon issuance, customer redemption, booking lifecycle management, branch assignment, and service completion tracking.

## User Personas

### 1. Worker (Field Service Technician)
- Uses mobile phone in field
- Needs GPS attendance tracking
- Issues coupons to customers
- Tracks assigned tasks
- Requires offline capability

### 2. Admin (Operations Manager)
- Monitors workforce on desktop/tablet
- Assigns branches to bookings
- Views analytics dashboard
- Manages workers and branches

### 3. Branch Manager
- Views assigned bookings
- Updates service status
- Dispatches service team
- Confirms completion

### 4. Customer
- Redeems coupon via link/code
- Receives booking confirmation
- Gets service updates

## Core Requirements (Static)

### Authentication
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Secure password hashing (bcrypt)

### GPS Attendance
- GPS punch-in/out with location capture
- Prevent double punch per day
- Accuracy indicators

### Coupon Management
- Format: SVL-AREAID-WORKERID-RANDOM6
- Unique constraint enforcement
- Status lifecycle: ISSUED → REDEEMED → UTILIZED

### Booking Lifecycle
- Status flow: PENDING → ASSIGNED → DISPATCHED → IN_PROGRESS → COMPLETED
- Branch assignment
- Service tracking

## What's Been Implemented (Phase 1 MVP)

### Date: February 17, 2026

#### Backend (FastAPI + MongoDB)
- [x] User Authentication (Register/Login/Refresh/Me)
- [x] GPS Attendance (Punch-In/Punch-Out)
- [x] Coupon Creation with SVL-XXX-XXX-XXXXXX format
- [x] OTP Request & Verification (Mock for MVP)
- [x] Booking Creation after Redemption
- [x] Branch Management (CRUD)
- [x] Branch Assignment to Bookings
- [x] Booking Status Updates
- [x] Dashboard Statistics API
- [x] Location Logging
- [x] File Upload (Local Storage)
- [x] Task Management

#### Frontend (React + Tailwind + Shadcn)
- [x] Login & Registration Pages
- [x] Admin Dashboard with Stats
- [x] Worker Dashboard with Quick Actions
- [x] Attendance Page (Punch In/Out)
- [x] Issue Coupon Page
- [x] My Coupons List
- [x] Tasks List
- [x] Admin: Workers Management
- [x] Admin: Coupons Management
- [x] Admin: Bookings Management
- [x] Admin: Branches Management
- [x] Admin: Live Map (Placeholder)
- [x] Branch: Bookings Management
- [x] Customer: Coupon Redemption Flow

## Prioritized Backlog (P0/P1/P2)

### P0 (Critical - Not Yet Implemented)
- Real-time location tracking with WebSockets
- Offline sync with IndexedDB
- Service Worker for PWA

### P1 (High Priority)
- Mapbox integration for live map
- Photo capture in coupon issuance
- Push notifications
- Geofencing alerts

### P2 (Medium Priority)
- Analytics charts and graphs
- Export to Excel/CSV
- Performance scoring
- Audit logs UI
- Email/SMS OTP integration

### P3 (Nice to Have)
- Fraud detection
- Heatmaps
- Route optimization
- Customer feedback system

## Tech Stack
- Frontend: React + Tailwind CSS + Shadcn UI
- Backend: FastAPI + Motor (MongoDB)
- Database: MongoDB
- Auth: JWT + bcrypt
- Maps: Mapbox (placeholder ready)
- Storage: Local file storage (MVP)
- OTP: Mock (MVP)

## Next Tasks
1. Integrate Mapbox for live worker tracking
2. Implement IndexedDB offline sync
3. Add Service Worker for PWA features
4. Connect real SMS/Email for OTP
5. Add photo capture functionality
6. Implement real-time WebSocket updates

---

## Update: February 17, 2026 (Phase 1.1 - Security Enhancement)

### New Features Implemented:

#### 1. Enhanced RBAC System
- **4 Roles**: admin, cre (Customer Relations Executive), worker, branch
- Strict permission boundaries enforced at API level
- Role-based data visibility

#### 2. Data Masking for Branch Role
- Branch users only see last 4 digits of mobile numbers
- Format: `XXXXXX3210`
- Cannot access full customer phone data

#### 3. Mobile Number Encryption
- All phone numbers encrypted at rest (basic encryption for MVP)
- Decrypted only when serving to authorized roles

#### 4. Audit Logging
- All critical actions logged to audit_logs collection
- Tracks: LOGIN, COUPON_CREATED, BOOKING_UPDATED, SEARCH_QUERY, etc.
- Includes user_id, role, IP address, timestamp

#### 5. Role Permissions Matrix

| Permission | Admin | CRE | Worker | Branch |
|------------|-------|-----|--------|--------|
| View full mobile | ✅ | ✅ | Own only | ❌ |
| Manage users | ✅ | ❌ | ❌ | ❌ |
| View all coupons | ✅ | ✅ | Own only | Assigned |
| Export data | ✅ | ✅ | ❌ | ❌ |
| View audit logs | ✅ | ✅ | ❌ | ❌ |
| Assign branches | ✅ | ❌ | ❌ | ❌ |
| Dashboard stats | ✅ | ✅ | ❌ | ❌ |

### Security Improvements:
- ✅ Phone validation and normalization
- ✅ Customer name validation (letters only)
- ✅ Audit trail for all sensitive operations
- ✅ Role middleware prevents unauthorized access

### Next Tasks (Phase 2):
1. Upgrade to AES-256 encryption for mobile numbers
2. Add rate limiting on API endpoints
3. Implement search indexing for performance
4. Add data export functionality (Excel/CSV) for Admin/CRE
5. Vite migration for frontend
