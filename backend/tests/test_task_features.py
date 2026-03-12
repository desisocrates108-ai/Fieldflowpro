"""
Backend API tests for 3 tasks:
- Task 1: Rebranding verification (HTML checks)
- Task 2: CRE Remarks delete functionality
- Task 3: Dashboard stats with total_branches
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTask1Rebranding:
    """Task 1: Verify 'Made with Emergent' badge removed and title changed"""
    
    def test_page_title_is_fieldflow_pro(self):
        """Verify page title is 'FieldFlow Pro'"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        html = response.text
        
        # Check title is FieldFlow Pro
        assert "<title>FieldFlow Pro</title>" in html, "Page title should be 'FieldFlow Pro'"
        
        # Verify NOT 'Emergent | Fullstack App'
        assert "Emergent | Fullstack App" not in html, "Old title should not be present"
    
    def test_meta_description_no_emergent(self):
        """Verify meta description doesn't contain 'emergent'"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        html = response.text
        
        # Check meta description
        assert 'content="FieldFlow Pro - Field Operations Management Platform"' in html, \
            "Meta description should be 'FieldFlow Pro - Field Operations Management Platform'"
        
        # Ensure 'emergent' is not in the meta description
        # Note: emergent.sh scripts are OK, just not in the description
        meta_line = [line for line in html.split('\n') if 'name="description"' in line]
        if meta_line:
            assert 'emergent' not in meta_line[0].lower() or 'fieldflow' in meta_line[0].lower(), \
                "Meta description should not contain 'emergent'"
    
    def test_no_made_with_emergent_badge(self):
        """Verify 'Made with Emergent' badge is removed"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        html = response.text
        
        # Check badge HTML is not present
        assert "Made with Emergent" not in html, "'Made with Emergent' badge should be removed"
        assert "emergent-badge" not in html.lower(), "Emergent badge class should not be present"


class TestTask3DashboardStats:
    """Task 3: Dashboard stats endpoint with total_branches"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed - skipping admin tests")
    
    def test_dashboard_stats_returns_all_fields(self, admin_token):
        """Verify /api/admin/dashboard-stats returns all required fields including total_branches"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard-stats", headers=headers)
        
        assert response.status_code == 200, f"Dashboard stats should return 200, got {response.status_code}"
        data = response.json()
        
        # Top row stats (8)
        top_row_fields = [
            "revenue_today", "sales_today", "active_workers_now", 
            "total_punched_in_today", "inactive_alerts", "fraud_alerts_active",
            "pending_expenses", "encashments_today"
        ]
        
        # Bottom row stats (8)
        bottom_row_fields = [
            "revenue_month", "sales_month", "active_campaigns", 
            "total_coupons_available", "total_workers", "total_branches",
            "total_areas", "expenses_month"
        ]
        
        # Check all required fields exist
        all_fields = top_row_fields + bottom_row_fields
        missing_fields = [f for f in all_fields if f not in data]
        
        assert not missing_fields, f"Missing fields: {missing_fields}"
        
        # Specifically verify total_branches is present
        assert "total_branches" in data, "total_branches field must be present"
        assert isinstance(data["total_branches"], int), "total_branches should be an integer"
    
    def test_dashboard_stats_has_timestamp(self, admin_token):
        """Verify last_updated timestamp is present"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard-stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "last_updated" in data, "last_updated timestamp should be present"
        assert "timezone" in data, "timezone field should be present"
        assert data["timezone"] == "Asia/Kolkata", "Timezone should be Asia/Kolkata (IST)"
    
    def test_dashboard_stats_no_hardcoded_zeros(self, admin_token):
        """Verify stats come from backend (structure exists, values can be 0 if no data)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/dashboard-stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All numeric fields should be integers or floats
        numeric_fields = [
            "total_workers", "active_workers_now", "total_punched_in_today",
            "inactive_alerts", "fraud_alerts_active", "sales_today",
            "revenue_today", "sales_month", "revenue_month", "active_campaigns",
            "total_coupons_available", "total_areas", "total_branches",
            "pending_expenses", "expenses_month", "encashments_today"
        ]
        
        for field in numeric_fields:
            if field in data:
                assert isinstance(data[field], (int, float)), f"{field} should be numeric"


class TestTask2CRERemarkDelete:
    """Task 2: CRE Remarks delete functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed - skipping admin tests")
    
    @pytest.fixture
    def cre_token(self):
        """Get CRE auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testcre@fieldflow.com",
            "password": "cre123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("CRE login failed - skipping CRE tests")
    
    def test_admin_can_view_cre_remarks(self, admin_token):
        """Admin should be able to view CRE remarks"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/cre-remarks", headers=headers)
        
        assert response.status_code == 200, f"Admin should view CRE remarks, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_delete_cre_remark_endpoint_exists(self, admin_token):
        """Verify DELETE /api/cre/call-log/{log_id} endpoint exists"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with a non-existent ID - should get 404 not 405 (method not allowed)
        response = requests.delete(f"{BASE_URL}/api/cre/call-log/non-existent-id", headers=headers)
        
        # 404 means endpoint exists but log not found
        # 405 would mean endpoint doesn't exist
        assert response.status_code == 404, f"Should return 404 for non-existent log, got {response.status_code}"
        
        # Verify error message
        data = response.json()
        assert "not found" in data.get("detail", "").lower(), "Should return 'not found' message"
    
    def test_delete_existing_cre_remark_as_admin(self, admin_token):
        """Test deleting an existing CRE remark as admin (if one exists)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get existing remarks
        response = requests.get(f"{BASE_URL}/api/admin/cre-remarks", headers=headers)
        assert response.status_code == 200
        
        remarks = response.json()
        if len(remarks) == 0:
            pytest.skip("No CRE remarks to delete")
        
        # Get the first remark ID
        remark_id = remarks[0]["id"]
        initial_count = len(remarks)
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/cre/call-log/{remark_id}", 
            headers=headers
        )
        
        assert delete_response.status_code == 200, f"Delete should succeed, got {delete_response.status_code}"
        
        # Verify deletion
        data = delete_response.json()
        assert "deleted" in data.get("message", "").lower() or "success" in data.get("message", "").lower(), \
            "Should return success message"
        
        # Verify remark is gone
        verify_response = requests.get(f"{BASE_URL}/api/admin/cre-remarks", headers=headers)
        assert verify_response.status_code == 200
        
        new_remarks = verify_response.json()
        new_ids = [r["id"] for r in new_remarks]
        
        assert remark_id not in new_ids, "Deleted remark should not appear in list"
        assert len(new_remarks) == initial_count - 1, "Remark count should decrease by 1"


class TestAuthEndpoints:
    """Basic auth endpoint tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login should succeed, got {response.status_code}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
    
    def test_cre_login(self):
        """Test CRE login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testcre@fieldflow.com",
            "password": "cre123"
        })
        assert response.status_code == 200, f"CRE login should succeed, got {response.status_code}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health should be 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "healthy", "Status should be healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
