# FieldFlow Pro - Android APK Build Guide

## Overview
This is a TWA (Trusted Web Activity) Android project that wraps your FieldFlow Pro web app into a native Android APK for Play Store distribution.

## Prerequisites
- Android Studio (latest stable)
- JDK 17+
- Google Play Developer Account ($25 one-time) - https://play.google.com/console

---

## 🚀 Quick Build (3 Steps)

### Step 1: Open in Android Studio
1. Download this project from GitHub (use "Save to GitHub" in Emergent)
2. Open Android Studio → File → Open → Select `/android-twa` folder
3. Wait for Gradle sync to complete

### Step 2: Generate Signed APK
1. Build → Generate Signed Bundle/APK
2. Select "APK"
3. Create new keystore (SAVE THIS FILE - you'll need it for updates):
   - Key store path: `fieldflow-release.jks`
   - Password: (choose a strong password)
   - Key alias: `fieldflow`
   - Key password: (choose a strong password)
   - Fill organization details
4. Select "release" build type
5. Click "Finish"

### Step 3: Upload to Play Store
1. Go to https://play.google.com/console
2. Create new app → "FieldFlow Pro"
3. Upload APK from: `app/build/outputs/apk/release/app-release.apk`
4. Fill store listing (description, screenshots, etc.)
5. Submit for review

---

## 🔐 Digital Asset Links (Required for no-browser-bar)

After generating your signing key, get the SHA256 fingerprint:
```bash
keytool -list -v -keystore fieldflow-release.jks -alias fieldflow
```

Copy the SHA-256 fingerprint and update:
- File: `frontend/public/.well-known/assetlinks.json`
- Replace: `__YOUR_APP_SIGNING_KEY_SHA256_FINGERPRINT__`

This removes the browser address bar, making it look 100% native.

---

## 📱 What Users See
- Native app icon on home screen
- Full-screen experience (no browser bar when Digital Asset Links verified)
- Splash screen with FieldFlow Pro logo
- Red status bar matching brand
- Camera & GPS permissions auto-requested

---

## ⚙️ Configuration

### Change Domain (when custom domain ready)
Edit `app/build.gradle`:
```gradle
manifestPlaceholders = [
    hostName: "fieldflow.servall.in",
    defaultUrl: "https://fieldflow.servall.in",
    ...
]
```

### App Version (for updates)
Edit `app/build.gradle`:
```gradle
versionCode 2  // Increment for each update
versionName "1.1.0"
```

---

## 🍎 iOS App Store

For iOS, you have two options:

### Option A: PWA (Recommended - No App Store needed)
Users can "Add to Home Screen" from Safari. It already works as a standalone app.

### Option B: App Store via WKWebView
Requires:
- Apple Developer Account ($99/year)
- Xcode on macOS
- Create iOS project with WKWebView pointing to your URL
- Submit to App Store

---

## 📋 Play Store Listing Requirements
- App icon: 512x512px (use icon.svg from public folder, export as PNG)
- Feature graphic: 1024x500px
- Screenshots: Phone (min 2), Tablet (optional)
- Short description: "Field operations management - workers, campaigns, leads & analytics"
- Full description: (Write 300+ words about features)
- Privacy Policy URL: (Required - host a simple policy page)
- Category: Business
- Content rating: Everyone

---

## 🐛 Troubleshooting

**Browser bar showing?**
→ Digital Asset Links not verified. Check assetlinks.json is accessible at:
`https://your-domain.com/.well-known/assetlinks.json`

**App crashes on open?**
→ Check internet connection. TWA requires network for first load.

**Camera/GPS not working?**
→ Permissions are declared in AndroidManifest.xml. User must grant them.
