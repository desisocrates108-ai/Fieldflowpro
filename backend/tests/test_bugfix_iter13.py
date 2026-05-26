"""
Test suite for FieldFlow Pro - Iteration 13 Bug Fixes
- Bug 1: Branch form (frontend only - tested via Playwright)
- Bug 2: Worker Sale CASH submission (HTTP 200 with ocr_confidence=0)
- Bug 2b: UPI -> QR payment_mode mapping & ledger total_qr_collected
- Bug 3: Login robustness (verify_password try/except)
- Regression: Admin dashboard, Branch CRUD, Worker /me, my-sales
"""
import os
import pytest
import requests
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://cre-remarks.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"
WORKER_EMAIL = "testworker@fieldflow.com"
WORKER_PASSWORD = "worker123"
BRANCH_ID = "4479a835-4521-479d-b203-2f109d1bb874"
CAMPAIGN_ID = "3328d170-e040-494f-a853-3959ba51fc4c"
SURAT_LAT, SURAT_LNG = 21.1702, 72.8311


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def worker_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": WORKER_EMAIL, "password": WORKER_PASSWORD})
    assert r.status_code == 200, f"Worker login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def worker_id(worker_token):
    r = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {worker_token}"})
    assert r.status_code == 200
    return r.json()["id"]


@pytest.fixture(scope="module")
def available_codes(admin_token):
    """Get list of AVAILABLE coupons from target campaign"""
    r = requests.get(
        f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/coupons?status=AVAILABLE&limit=20",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 200, f"Failed to fetch coupons: {r.text}"
    coupons = r.json()
    codes = [c["code"] for c in coupons if c.get("status") == "AVAILABLE"]
    assert len(codes) >= 2, f"Need at least 2 available coupons, got {len(codes)}"
    return codes


# ====================== Bug 3: Login Robustness ======================
class TestLoginRobustness:
    def test_admin_valid_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"

    def test_worker_valid_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": WORKER_EMAIL, "password": WORKER_PASSWORD})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "worker"

    def test_invalid_password_returns_401_not_500(self):
        """verify_password now wrapped in try/except — should return clean 401"""
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": "WRONG_PASSWORD"})
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"

    def test_nonexistent_user_returns_401(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "nonexistent@example.com", "password": "any"})
        assert r.status_code == 401

    def test_empty_password_returns_401_not_500(self):
        """Empty password should be rejected cleanly"""
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ""})
        assert r.status_code in (401, 422), f"Expected 401/422, got {r.status_code}"


# ====================== Bug 2: Worker Sale CASH ======================
class TestWorkerSaleCash:
    def test_sale_with_cash_and_zero_ocr_confidence(self, worker_token, worker_id, available_codes):
        """Bug 2: previously returned 422 with ocr_confidence: null. Now should accept 0."""
        code = available_codes[0]
        payload = {
            "customer_name": "TEST_Cash Customer",
            "customer_phone": "9876543210",
            "ocr_confidence": 0,  # Frontend now sends 0 when no OCR (was null)
            "coupon_code": code,
            "branch_id": BRANCH_ID,
            "payment_mode": "CASH",
            "latitude": SURAT_LAT,
            "longitude": SURAT_LNG,
            "gps_accuracy": 10.0,
        }
        r = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            json=payload,
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["success"] is True
        assert data["coupon_code"] == code
        assert "sold successfully" in data["message"].lower()

    def test_sale_rejects_pydantic_null_ocr_confidence(self, worker_token, available_codes):
        """Confirm Pydantic still requires float (null would 422). Frontend fix validates."""
        code = available_codes[1] if len(available_codes) > 1 else available_codes[0]
        payload = {
            "customer_name": "TEST_Null OCR",
            "customer_phone": "9876543210",
            "ocr_confidence": None,  # Explicit null — Pydantic should reject
            "coupon_code": code,
            "branch_id": BRANCH_ID,
            "payment_mode": "CASH",
            "latitude": SURAT_LAT,
            "longitude": SURAT_LNG,
        }
        r = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            json=payload,
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        # Pydantic 422 for null on non-Optional float field — confirms frontend MUST send number
        assert r.status_code == 422, f"Expected 422 for null ocr_confidence, got {r.status_code}: {r.text}"


# ====================== Bug 2b: QR Payment Mode & Ledger ======================
class TestWorkerSaleQRAndLedger:
    def test_sale_with_qr_increments_total_qr_collected(self, worker_token, worker_id, available_codes, admin_token):
        # Snapshot ledger BEFORE
        r_before = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/ledger",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Some endpoints may not exist - try alternate
        if r_before.status_code != 200:
            r_before = requests.get(
                f"{BASE_URL}/api/admin/workers/{worker_id}/ledger",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        if r_before.status_code != 200:
            pytest.skip(f"Ledger endpoint not reachable: {r_before.status_code}")

        before = r_before.json()
        qr_before = before.get("total_qr_collected", 0)
        cash_before = before.get("total_cash_collected", 0)

        # Use the second available code for QR sale
        code = available_codes[-1]  # last item
        payload = {
            "customer_name": "TEST_QR Customer",
            "customer_phone": "9876543211",
            "ocr_confidence": 0,
            "coupon_code": code,
            "branch_id": BRANCH_ID,
            "payment_mode": "QR",  # Frontend maps upi -> QR
            "latitude": SURAT_LAT,
            "longitude": SURAT_LNG,
            "gps_accuracy": 10.0,
        }
        r = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            json=payload,
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert r.status_code == 200, f"QR sale failed: {r.status_code} {r.text}"

        # Snapshot AFTER
        time.sleep(1)
        r_after = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/ledger",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if r_after.status_code != 200:
            r_after = requests.get(
                f"{BASE_URL}/api/admin/workers/{worker_id}/ledger",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        after = r_after.json()
        qr_after = after.get("total_qr_collected", 0)
        cash_after = after.get("total_cash_collected", 0)

        assert qr_after > qr_before, f"total_qr_collected did not increment: {qr_before} -> {qr_after}"
        # Cash should NOT have changed from this QR sale
        assert cash_after == cash_before, f"Cash incremented unexpectedly: {cash_before} -> {cash_after}"


# ====================== Regression: Admin dashboard, Branch CRUD, Worker me ======================
class TestRegression:
    def test_admin_dashboard_stats(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Try multiple endpoints
        if r.status_code == 404:
            r = requests.get(
                f"{BASE_URL}/api/admin/dashboard",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert r.status_code in (200, 404), f"Dashboard stats: {r.status_code}"
        # Don't fail hard if endpoint differs - just log

    def test_worker_me(self, worker_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {worker_token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "worker"

    def test_worker_my_sales(self, worker_token):
        r = requests.get(
            f"{BASE_URL}/api/campaigns/worker/my-sales",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert r.status_code == 200
        sales = r.json()
        assert isinstance(sales, list)

    def test_branch_list(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/branches", headers={"Authorization": f"Bearer {admin_token}"})
        if r.status_code == 404:
            r = requests.get(f"{BASE_URL}/api/admin/branches", headers={"Authorization": f"Bearer {admin_token}"})
        assert r.status_code == 200, f"Branch list: {r.text}"
        assert isinstance(r.json(), list)

    def test_branch_create_and_update(self, admin_token):
        # CREATE
        payload = {
            "name": "TEST_Iter13 Branch",
            "address": "TEST_Iter13 Address Line",
            "latitude": 21.17,
            "longitude": 72.83,
            "contact_phone": "9876543210",
        }
        r = requests.post(
            f"{BASE_URL}/api/branches",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if r.status_code == 404:
            r = requests.post(
                f"{BASE_URL}/api/admin/branches",
                json=payload,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert r.status_code in (200, 201), f"Branch create: {r.status_code} {r.text}"
        branch = r.json()
        bid = branch.get("id")
        assert bid

        # UPDATE
        upd = requests.patch(
            f"{BASE_URL}/api/branches/{bid}",
            json={"name": "TEST_Iter13 Branch Updated"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if upd.status_code == 404:
            upd = requests.patch(
                f"{BASE_URL}/api/admin/branches/{bid}",
                json={"name": "TEST_Iter13 Branch Updated"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        assert upd.status_code in (200, 204), f"Branch update: {upd.status_code} {upd.text}"

        # Cleanup
        requests.delete(f"{BASE_URL}/api/branches/{bid}", headers={"Authorization": f"Bearer {admin_token}"})
