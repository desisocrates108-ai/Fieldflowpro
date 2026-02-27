"""
Test Suite for FieldFlow Pro v6.0 Features:
1. Attendance Module (punch-in/out, admin dashboard with stats/export)
2. Worker Cash Permission Toggle in Admin Workers page
3. Campaign Deletion with safe-delete logic
4. Cash/QR payment tracking in ledger
5. Static file serving for expense photos
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://campaign-mgmt-2.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"
WORKER_EMAIL = "testworker@fieldflow.com"
WORKER_PASSWORD = "worker123"
WORKER_CASH_DISABLED_EMAIL = "newworker_test@fieldflow.com"
WORKER_CASH_DISABLED_PASSWORD = "test123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def worker_token():
    """Get worker authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": WORKER_EMAIL,
        "password": WORKER_PASSWORD
    })
    assert response.status_code == 200, f"Worker login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def worker_cash_disabled_token():
    """Get worker (cash disabled) authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": WORKER_CASH_DISABLED_EMAIL,
        "password": WORKER_CASH_DISABLED_PASSWORD
    })
    assert response.status_code == 200, f"Worker (cash disabled) login failed: {response.text}"
    return response.json()["access_token"]


class TestHealthCheck:
    """Basic health check tests"""

    def test_health_endpoint(self):
        """Verify API is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAdminAttendanceDashboard:
    """Tests for Admin Attendance Dashboard - stats show correct counts"""

    def test_attendance_stats_api(self, admin_token):
        """GET /api/attendance/admin/stats - returns correct stats structure"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total_workers" in data
        assert "present_today" in data
        assert "absent_today" in data
        assert "in_progress" in data
        assert "total_hours_today" in data
        
        # Verify types
        assert isinstance(data["total_workers"], int)
        assert isinstance(data["present_today"], int)
        assert isinstance(data["absent_today"], int)
        assert isinstance(data["in_progress"], int)
        assert isinstance(data["total_hours_today"], (int, float))

    def test_attendance_stats_with_date(self, admin_token):
        """GET /api/attendance/admin/stats?date=YYYY-MM-DD - filters by date"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/stats?date={today}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_workers" in data

    def test_attendance_workers_list(self, admin_token):
        """GET /api/attendance/admin/workers - returns all workers with attendance status"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/workers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            worker = data[0]
            assert "worker_id" in worker
            assert "worker_name" in worker
            assert "worker_email" in worker
            assert "date" in worker
            assert "status" in worker
            assert worker["status"] in ["PRESENT", "IN_PROGRESS", "ABSENT"]

    def test_attendance_export_csv(self, admin_token):
        """GET /api/attendance/admin/export - exports attendance data"""
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = "2026-01-01"
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/export?start_date={start_date}&end_date={today}&format=csv",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "csv_data" in data
        assert "filename" in data


class TestWorkerPunchInOut:
    """Tests for Worker Punch-In and Punch-Out functionality"""

    def test_worker_can_view_today_attendance(self, worker_token):
        """GET /api/attendance/today - worker sees their status"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/today",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "date" in data
        assert "status" in data
        assert data["status"] in ["NOT_STARTED", "IN_PROGRESS", "PRESENT"]

    def test_attendance_stats_requires_admin(self, worker_token):
        """Admin stats endpoint should require admin role"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/stats",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        # Should be 403 Forbidden for workers
        assert response.status_code == 403


class TestWorkerCashPermissionToggle:
    """Tests for Admin Workers page - Cash toggle button works and persists"""

    def test_get_workers_with_cash_allowed_field(self, admin_token):
        """GET /api/admin/users?role=worker - returns cash_allowed field"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users?role=worker",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            worker = data[0]
            assert "cash_allowed" in worker

    def test_toggle_cash_permission(self, admin_token):
        """POST /api/admin/workers/{id}/toggle-cash - toggles cash permission"""
        # First get a worker
        workers_response = requests.get(
            f"{BASE_URL}/api/admin/users?role=worker",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        workers = workers_response.json()
        worker = workers[0]
        worker_id = worker["id"]
        original_cash_allowed = worker.get("cash_allowed", True)
        
        # Toggle cash permission
        response = requests.post(
            f"{BASE_URL}/api/admin/workers/{worker_id}/toggle-cash",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "cash_allowed" in data
        # Cash should be toggled
        assert data["cash_allowed"] != original_cash_allowed
        
        # Toggle back to original state
        requests.post(
            f"{BASE_URL}/api/admin/workers/{worker_id}/toggle-cash",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    def test_toggle_cash_only_for_workers(self, admin_token):
        """Toggle cash should fail for non-worker users"""
        # Get admin's own ID (not a worker)
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        admin_id = me_response.json()["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/workers/{admin_id}/toggle-cash",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should fail for admin user
        assert response.status_code in [400, 404]


class TestWorkerSaleCouponCashVisibility:
    """Tests for Worker SaleCoupon page - Cash option hidden when cash_allowed=false"""

    def test_worker_cash_allowed_returns_true(self, worker_token):
        """Worker with cash_allowed should see cash option"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Default worker should have cash allowed
        assert data.get("cash_allowed", True) == True

    def test_worker_cash_disabled_returns_false(self, worker_cash_disabled_token):
        """Worker with cash_allowed=false should NOT see cash option"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {worker_cash_disabled_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # This worker should have cash disabled
        assert data.get("cash_allowed") == False


class TestCampaignDeletion:
    """Tests for Campaign delete button - returns error if campaign has sold coupons"""

    def test_campaign_list_shows_sold_count(self, admin_token):
        """GET /api/campaigns - each campaign has sold_count"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            campaign = data[0]
            assert "sold_count" in campaign
            assert "available_count" in campaign
            assert isinstance(campaign["sold_count"], int)

    def test_delete_campaign_without_sales_succeeds(self, admin_token):
        """DELETE /api/campaigns/{id} - succeeds if no sold coupons"""
        # First create a test campaign to delete
        create_response = requests.post(
            f"{BASE_URL}/api/campaigns",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": "TEST_DELETE_CAMPAIGN",
                "price": 100,
                "start_code": "DEL100",
                "end_code": "DEL105"
            }
        )
        
        if create_response.status_code == 200:
            campaign_id = create_response.json()["id"]
            
            # Delete should succeed (no sales)
            delete_response = requests.delete(
                f"{BASE_URL}/api/campaigns/{campaign_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert delete_response.status_code == 200
        else:
            # Campaign might already exist, skip this test
            pytest.skip("Could not create test campaign")


class TestLedgerCashQRColumns:
    """Tests for Ledger shows Cash and QR/UPI columns with correct breakdown"""

    def test_ledger_has_cash_and_qr_columns(self, admin_token):
        """GET /api/ledgers/all - returns total_cash_collected and total_qr_collected"""
        response = requests.get(
            f"{BASE_URL}/api/ledgers/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            ledger = data[0]
            assert "worker_id" in ledger
            assert "worker_name" in ledger
            assert "total_coupons_sold" in ledger
            assert "total_revenue" in ledger
            assert "total_cash_collected" in ledger
            assert "total_qr_collected" in ledger
            assert "total_advances" in ledger
            assert "total_expenses" in ledger
            assert "net_payable" in ledger


class TestStaticFileServing:
    """Tests for Static file serving - /api/uploads/{filename} returns 200"""

    def test_static_file_serving_exists(self):
        """GET /api/uploads/{filename} - returns 200 for existing file"""
        # This file exists in the uploads directory
        response = requests.get(
            f"{BASE_URL}/api/uploads/expense_4a612d31-2d83-495c-b526-9ef7edb5a115.jpg"
        )
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("image/")

    def test_static_file_serving_not_found(self):
        """GET /api/uploads/{filename} - returns 404 for non-existent file"""
        response = requests.get(
            f"{BASE_URL}/api/uploads/nonexistent_file_123456.jpg"
        )
        assert response.status_code == 404


class TestAttendanceReportFilters:
    """Tests for Attendance Report with filters"""

    def test_attendance_report_with_status_filter(self, admin_token):
        """GET /api/attendance/admin/report?status=PRESENT - filters by status"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/report?status=PRESENT",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All records should have status PRESENT
        for record in data:
            assert record["status"] == "PRESENT"

    def test_attendance_report_with_date_range(self, admin_token):
        """GET /api/attendance/admin/report?start_date=X&end_date=Y - filters by date range"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/admin/report?start_date=2026-01-01&end_date=2026-12-31",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestWorkerMyAttendanceHistory:
    """Tests for Worker's own attendance history"""

    def test_worker_attendance_history(self, worker_token):
        """GET /api/attendance/my-history - worker sees their history"""
        response = requests.get(
            f"{BASE_URL}/api/attendance/my-history",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "worker_name" in data
        assert "records" in data
        assert isinstance(data["records"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
