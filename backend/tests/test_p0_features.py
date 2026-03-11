"""
P0 Features Tests - Field Flow Pro
- P0-4: Force Delete Coupon (both legacy 'coupons' and 'campaign_coupons')
- P0-2: Admin Dashboard Stats (IST timezone)
- P0-3: CRE Remark Delete (RBAC)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
ADMIN_CREDS = {"email": "testadmin@fieldflow.com", "password": "admin123"}
CRE_CREDS = {"email": "testcre@fieldflow.com", "password": "cre123"}
WORKER_CREDS = {"email": "testworker@fieldflow.com", "password": "worker123"}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code} {response.text}")


@pytest.fixture(scope="module")
def cre_token():
    """Get CRE auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=CRE_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"CRE login failed: {response.status_code} {response.text}")


@pytest.fixture(scope="module")
def worker_token():
    """Get worker auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=WORKER_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Worker login failed: {response.status_code} {response.text}")


class TestAdminDashboardStats:
    """P0-2: GET /api/admin/dashboard-stats - consolidated IST-aware stats"""
    
    def test_dashboard_stats_returns_200(self, admin_token):
        """Dashboard stats endpoint returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
    def test_dashboard_stats_has_required_fields(self, admin_token):
        """Dashboard stats has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = [
            "total_workers",
            "active_workers_now",
            "total_punched_in_today",
            "inactive_alerts",
            "fraud_alerts_active",
            "sales_today",
            "revenue_today",
            "sales_month",
            "revenue_month",
            "active_campaigns",
            "total_coupons_available",
            "total_areas",
            "pending_expenses",
            "expenses_month",
            "encashments_today",
            "net_payable",
            "timezone",
            "last_updated"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            
    def test_dashboard_stats_data_types(self, admin_token):
        """Dashboard stats has correct data types"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Integer fields
        int_fields = ["total_workers", "active_workers_now", "total_punched_in_today",
                      "inactive_alerts", "fraud_alerts_active", "sales_today", "sales_month",
                      "active_campaigns", "total_coupons_available", "total_areas", 
                      "pending_expenses", "encashments_today"]
        
        for field in int_fields:
            assert isinstance(data[field], int), f"{field} should be int, got {type(data[field])}"
        
        # Float fields (revenue/money)
        float_fields = ["revenue_today", "revenue_month", "expenses_month", "net_payable"]
        for field in float_fields:
            assert isinstance(data[field], (int, float)), f"{field} should be numeric, got {type(data[field])}"
            
    def test_dashboard_stats_accessible_by_cre(self, cre_token):
        """Dashboard stats is accessible by CRE role"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        # CRE should be able to access dashboard stats based on require_roles("admin", "cre")
        assert response.status_code == 200, f"CRE should access dashboard-stats, got {response.status_code}"

    def test_dashboard_stats_not_accessible_by_worker(self, worker_token):
        """Dashboard stats is NOT accessible by worker role"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        # Worker should NOT be able to access admin endpoints
        assert response.status_code in [401, 403], f"Worker should not access dashboard-stats, got {response.status_code}"


class TestForceDeleteCoupon:
    """P0-4: DELETE /api/admin/coupons/{coupon_id}?force=true"""
    
    def test_delete_legacy_coupon_endpoint_exists(self, admin_token):
        """Admin coupon delete endpoint exists"""
        # Use a fake ID to test endpoint existence
        response = requests.delete(
            f"{BASE_URL}/api/admin/coupons/FAKE_ID_12345?force=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 404 = endpoint exists but coupon not found (expected)
        # 405 = method not allowed (endpoint doesn't exist)
        assert response.status_code == 404, f"Expected 404 for non-existent coupon, got {response.status_code}"
        
    def test_delete_coupon_not_found_message(self, admin_token):
        """Delete coupon returns proper error message for non-existent coupon"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/coupons/NON_EXISTENT_COUPON?force=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        
    def test_delete_coupon_requires_admin(self, worker_token):
        """Delete coupon requires admin role"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/coupons/ANY_COUPON?force=true",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        # Worker should NOT be able to delete coupons
        assert response.status_code in [401, 403], f"Worker should not delete coupons, got {response.status_code}"
        
    def test_list_legacy_coupons_for_deletion(self, admin_token):
        """Get legacy coupons list to verify endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to list coupons: {response.status_code}"
        coupons = response.json()
        print(f"Found {len(coupons)} legacy coupons")


class TestCRERemarkDelete:
    """P0-3: DELETE /api/cre/call-log/{log_id} with RBAC"""
    
    def test_delete_call_log_endpoint_exists(self, admin_token):
        """CRE call log delete endpoint exists"""
        response = requests.delete(
            f"{BASE_URL}/api/cre/call-log/FAKE_LOG_ID",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 404 = endpoint exists but log not found (expected)
        # 405 = method not allowed (endpoint doesn't exist)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        
    def test_delete_call_log_not_found_message(self, admin_token):
        """Delete call log returns proper error for non-existent log"""
        response = requests.delete(
            f"{BASE_URL}/api/cre/call-log/NON_EXISTENT_LOG",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        
    def test_delete_call_log_accessible_by_cre(self, cre_token):
        """CRE can access delete call log endpoint"""
        response = requests.delete(
            f"{BASE_URL}/api/cre/call-log/FAKE_LOG_ID",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        # CRE should have access to the endpoint (404 = log not found, but endpoint works)
        assert response.status_code == 404, f"CRE should access call-log delete, got {response.status_code}"
        
    def test_delete_call_log_not_accessible_by_worker(self, worker_token):
        """Worker cannot delete call logs"""
        response = requests.delete(
            f"{BASE_URL}/api/cre/call-log/ANY_LOG",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        # Worker should NOT be able to delete call logs
        assert response.status_code in [401, 403], f"Worker should not delete call logs, got {response.status_code}"


class TestIntegrationFlows:
    """Integration tests for the full flows"""
    
    def test_admin_login_works(self):
        """Admin can log in successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        
    def test_cre_login_works(self):
        """CRE can log in successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=CRE_CREDS)
        assert response.status_code == 200, f"CRE login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "cre"
        
    def test_worker_login_works(self):
        """Worker can log in successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=WORKER_CREDS)
        if response.status_code != 200:
            pytest.skip(f"Worker account may not exist: {response.status_code} {response.text}")
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "worker"
        
    def test_branches_list(self, admin_token):
        """Branches API returns list"""
        response = requests.get(
            f"{BASE_URL}/api/branches",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        branches = response.json()
        assert isinstance(branches, list)
        print(f"Found {len(branches)} branches")
        
    def test_campaigns_list(self, admin_token):
        """Campaigns API returns list"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        campaigns = response.json()
        assert isinstance(campaigns, list)
        print(f"Found {len(campaigns)} campaigns")
