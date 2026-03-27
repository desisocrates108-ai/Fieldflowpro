"""
Test Suite for v9 Features:
1. Admin Coupons - merged view of campaign + legacy coupons with filters
2. Worker Data Entry - create and view own entries
3. Admin Data Entry - view all entries with filters and export
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"
WORKER_EMAIL = "testworker@fieldflow.com"
WORKER_PASSWORD = "worker123"


class TestAuth:
    """Authentication tests for admin and worker"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['name']}")
        return data["access_token"]
    
    def test_worker_login(self):
        """Test worker login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        assert response.status_code == 200, f"Worker login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "worker"
        print(f"✓ Worker login successful: {data['user']['name']}")
        return data["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def worker_token():
    """Get worker auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": WORKER_EMAIL,
        "password": WORKER_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Worker login failed: {response.text}")
    return response.json()["access_token"]


# ========== Admin Coupons Tests ==========

class TestAdminCoupons:
    """Tests for Admin Coupons merged view endpoint"""
    
    def test_get_admin_coupons_no_filter(self, admin_token):
        """GET /api/admin/coupons returns merged campaign + legacy coupons"""
        response = requests.get(
            f"{BASE_URL}/api/admin/coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "coupons" in data
        assert "total" in data
        assert "total_campaign" in data
        assert "total_legacy" in data
        
        print(f"✓ Admin coupons: {len(data['coupons'])} returned, campaign={data['total_campaign']}, legacy={data['total_legacy']}")
        
        # Verify coupon structure if any exist
        if data["coupons"]:
            coupon = data["coupons"][0]
            expected_fields = ["id", "code", "status", "customer_name", "customer_phone", 
                            "campaign_name", "worker_name", "branch_name", "source"]
            for field in expected_fields:
                assert field in coupon, f"Missing field: {field}"
            print(f"✓ Coupon structure verified with all expected fields")
    
    def test_admin_coupons_status_filter(self, admin_token):
        """Test status filter on admin coupons"""
        response = requests.get(
            f"{BASE_URL}/api/admin/coupons?status=AVAILABLE",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned coupons should have AVAILABLE status
        for coupon in data["coupons"]:
            assert coupon["status"] == "AVAILABLE", f"Expected AVAILABLE, got {coupon['status']}"
        
        print(f"✓ Status filter works: {len(data['coupons'])} AVAILABLE coupons")
    
    def test_admin_coupons_source_filter_campaign(self, admin_token):
        """Test source filter for campaign coupons"""
        response = requests.get(
            f"{BASE_URL}/api/admin/coupons?source=campaign",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned coupons should be from campaign source
        for coupon in data["coupons"]:
            assert coupon["source"] == "campaign", f"Expected campaign source, got {coupon['source']}"
        
        print(f"✓ Source filter (campaign) works: {len(data['coupons'])} campaign coupons")
    
    def test_admin_coupons_source_filter_legacy(self, admin_token):
        """Test source filter for legacy coupons"""
        response = requests.get(
            f"{BASE_URL}/api/admin/coupons?source=legacy",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned coupons should be from legacy source
        for coupon in data["coupons"]:
            assert coupon["source"] == "legacy", f"Expected legacy source, got {coupon['source']}"
        
        print(f"✓ Source filter (legacy) works: {len(data['coupons'])} legacy coupons")
    
    def test_admin_coupons_search(self, admin_token):
        """Test search functionality on admin coupons"""
        # First get some coupons to find a search term
        response = requests.get(
            f"{BASE_URL}/api/admin/coupons?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["coupons"]:
            # Search by coupon code
            code = data["coupons"][0]["code"]
            search_response = requests.get(
                f"{BASE_URL}/api/admin/coupons?search={code}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert search_response.status_code == 200
            search_data = search_response.json()
            
            # Should find at least the coupon we searched for
            codes = [c["code"] for c in search_data["coupons"]]
            assert code in codes, f"Search for {code} didn't return expected coupon"
            print(f"✓ Search works: found coupon {code}")
        else:
            print("✓ Search test skipped (no coupons to search)")
    
    def test_admin_coupons_unauthorized(self):
        """Test that unauthorized access is rejected"""
        response = requests.get(f"{BASE_URL}/api/admin/coupons")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Unauthorized access correctly rejected")
    
    def test_admin_coupons_worker_forbidden(self, worker_token):
        """Test that worker cannot access admin coupons"""
        response = requests.get(
            f"{BASE_URL}/api/admin/coupons",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Worker correctly forbidden from admin coupons")


# ========== Worker Data Entry Tests ==========

class TestWorkerDataEntry:
    """Tests for Worker Data Entry feature"""
    
    def test_create_data_entry(self, worker_token):
        """POST /api/worker/data-entry creates a new entry"""
        entry_data = {
            "customer_name": "TEST_John Doe",
            "mobile_number": "9876543210",
            "city": "Mumbai",
            "notes": "Test entry from pytest"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/worker/data-entry",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json=entry_data
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "entry" in data
        assert data["entry"]["customer_name"] == entry_data["customer_name"]
        assert data["entry"]["mobile_number"] == entry_data["mobile_number"]
        assert data["entry"]["city"] == entry_data["city"]
        assert "id" in data["entry"]
        assert "worker_id" in data["entry"]
        assert "worker_name" in data["entry"]
        assert "created_at" in data["entry"]
        
        print(f"✓ Data entry created: {data['entry']['id']}")
        return data["entry"]["id"]
    
    def test_create_data_entry_validation(self, worker_token):
        """Test validation - required fields"""
        # Missing customer_name
        response = requests.post(
            f"{BASE_URL}/api/worker/data-entry",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json={"mobile_number": "1234567890", "city": "Delhi"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Validation works: missing customer_name rejected")
        
        # Missing mobile_number
        response = requests.post(
            f"{BASE_URL}/api/worker/data-entry",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json={"customer_name": "Test", "city": "Delhi"}
        )
        assert response.status_code == 400
        print("✓ Validation works: missing mobile_number rejected")
        
        # Missing city
        response = requests.post(
            f"{BASE_URL}/api/worker/data-entry",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json={"customer_name": "Test", "mobile_number": "1234567890"}
        )
        assert response.status_code == 400
        print("✓ Validation works: missing city rejected")
    
    def test_get_my_data_entries(self, worker_token):
        """GET /api/worker/data-entry/me returns worker's own entries"""
        response = requests.get(
            f"{BASE_URL}/api/worker/data-entry/me",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)
        
        print(f"✓ Worker's entries: {data['total']} total")
        
        # Verify entry structure
        if data["entries"]:
            entry = data["entries"][0]
            expected_fields = ["id", "customer_name", "mobile_number", "city", "worker_id", "created_at"]
            for field in expected_fields:
                assert field in entry, f"Missing field: {field}"
            print("✓ Entry structure verified")
    
    def test_worker_data_entry_unauthorized(self):
        """Test unauthorized access to worker data entry"""
        response = requests.post(
            f"{BASE_URL}/api/worker/data-entry",
            json={"customer_name": "Test", "mobile_number": "123", "city": "Test"}
        )
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Unauthorized POST correctly rejected")
        
        response = requests.get(f"{BASE_URL}/api/worker/data-entry/me")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Unauthorized GET correctly rejected")


# ========== Admin Data Entry Tests ==========

class TestAdminDataEntry:
    """Tests for Admin Data Entry view"""
    
    def test_get_admin_data_entries(self, admin_token):
        """GET /api/admin/data-entry returns all entries"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "entries" in data
        assert "total" in data
        assert "workers" in data  # Worker filter dropdown data
        
        print(f"✓ Admin data entries: {data['total']} total, {len(data['workers'])} unique workers")
        
        # Verify workers list structure
        if data["workers"]:
            worker = data["workers"][0]
            assert "id" in worker
            assert "name" in worker
            print("✓ Workers dropdown data structure verified")
    
    def test_admin_data_entry_search(self, admin_token):
        """Test search functionality"""
        # First get entries to find a search term
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        if data["entries"]:
            # Search by customer name
            name = data["entries"][0]["customer_name"]
            search_response = requests.get(
                f"{BASE_URL}/api/admin/data-entry?search={name}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert search_response.status_code == 200
            search_data = search_response.json()
            
            names = [e["customer_name"] for e in search_data["entries"]]
            assert any(name in n for n in names), f"Search for {name} didn't return expected entry"
            print(f"✓ Search works: found entries matching '{name}'")
        else:
            print("✓ Search test skipped (no entries)")
    
    def test_admin_data_entry_worker_filter(self, admin_token):
        """Test worker filter"""
        # First get entries to find a worker_id
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        if data["entries"]:
            worker_id = data["entries"][0]["worker_id"]
            filter_response = requests.get(
                f"{BASE_URL}/api/admin/data-entry?worker_id={worker_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert filter_response.status_code == 200
            filter_data = filter_response.json()
            
            # All entries should be from the filtered worker
            for entry in filter_data["entries"]:
                assert entry["worker_id"] == worker_id
            
            print(f"✓ Worker filter works: {len(filter_data['entries'])} entries for worker {worker_id}")
        else:
            print("✓ Worker filter test skipped (no entries)")
    
    def test_admin_data_entry_export(self, admin_token):
        """GET /api/admin/data-entry/export returns data for Excel export"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry/export",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "entries" in data
        print(f"✓ Export endpoint works: {len(data['entries'])} entries for export")
    
    def test_admin_data_entry_forbidden_for_worker(self, worker_token):
        """Test that worker cannot access admin data entry"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Worker correctly forbidden from admin data entry")


# ========== Admin Coupon Delete Tests ==========

class TestAdminCouponDelete:
    """Tests for Admin coupon delete functionality"""
    
    def test_delete_nonexistent_coupon(self, admin_token):
        """DELETE /api/admin/coupons/{id} returns 404 for non-existent coupon"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/coupons/nonexistent-id-12345",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Delete non-existent coupon returns 404")
    
    def test_delete_coupon_unauthorized(self):
        """Test unauthorized delete is rejected"""
        response = requests.delete(f"{BASE_URL}/api/admin/coupons/some-id")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Unauthorized delete correctly rejected")


# ========== Health Check ==========

class TestHealthCheck:
    """Basic health check"""
    
    def test_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ API healthy: version {data.get('version', 'unknown')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
