# Field Flow Pro - Product Requirements Document

## Original Problem Statement
Build a full-stack field operations management platform ("Field Flow Pro") for managing workers, campaigns, coupons, branches, CRE operations, expenses, attendance, and real-time intelligence dashboards.

## Tech Stack
- **Backend**: FastAPI + MongoDB (Motor async driver) + JWT Auth + Pydantic
- **Frontend**: React + Tailwind CSS + Shadcn UI + React Router + PWA
- **Android**: TWA (Trusted Web Activity) wrapper for Play Store
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
- Sold Coupons Page with filters + Excel export
- Data Entry System with today's count

### QR Lead Capture System (Campaign-Based)
- General QR + Campaign-specific QR codes
- Admin campaign management with create/delete/view QR
- Public mobile-friendly form with campaign detection
- Leads table with campaign/source filters + Excel export

### PWA + Android App (April 22, 2026)
- **manifest.json**: Standalone display, theme color, app icons
- **Service Worker**: Network-first for API, cache-first for static assets, offline fallback
- **Meta Tags**: apple-mobile-web-app-capable, theme-color, viewport-fit=cover
- **Android TWA Project** (`/app/android-twa/`):
  - Complete Gradle project ready for Android Studio
  - AndroidManifest.xml with camera/GPS/internet permissions
  - Splash screen with FieldFlow Pro branding
  - Digital Asset Links support (assetlinks.json)
  - README with step-by-step APK build instructions

## Key API Endpoints
- `POST /api/qr-leads` — Public lead capture
- `GET /api/admin/qr-leads` — Admin leads with campaign filter
- `POST /api/admin/qr-campaigns` — Create campaign QR
- `GET /api/admin/qr-campaigns` — List campaigns with lead counts
- `GET /api/admin/dashboard-stats` — IST-aware stats
- `GET /api/admin/sold-coupons` — Sold coupons with filters
- `POST /api/campaigns/worker-sale` — Worker sale submission

## How to Build APK
1. Download project from GitHub ("Save to GitHub" in Emergent)
2. Open `/android-twa` folder in Android Studio
3. Build → Generate Signed APK
4. Upload to Google Play Console
(See `/app/android-twa/README.md` for full guide)

## Upcoming Tasks (P1)
- CRE Dashboard Overhaul (Excel-style grid, advanced filters)

## Future Tasks (P2+)
- Custom domain setup (fieldflow.servall.in)
- Live Map (Mapbox), WebSocket real-time updates
- iOS App Store submission (WKWebView wrapper)
- DB migration (PostgreSQL), Image storage (S3)
- Vite migration, Real SMS (Twilio)
