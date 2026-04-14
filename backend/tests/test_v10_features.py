"""
Test Suite v10: Testing 5 major fixes
1. Command Center dashboard stats (revenue_today, sales_today, active_now, punched_in, pending_expenses)
2. Data Entry page today's entry count
3. Sold Coupons admin page with filters
4. Ledger expense bill images
5. Worker sale submission (backend only - GPS required for full e2e)
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"
WORKER_EMAIL = "testworker@fieldflow.com"
WORKER_PASSWORD = "worker123"


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_worker_login(self):
        """Test worker login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        assert response.status_code == 200, f"Worker login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "worker"
        print(f"✓ Worker login successful: {data['user']['name']}")


@pytest.fixture
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json()["access_token"]


@pytest.fixture
def worker_token():
    """Get worker auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": WORKER_EMAIL,
        "password": WORKER_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Worker login failed")
    return response.json()["access_token"]


class TestDashboardStats:
    """Test Command Center dashboard stats endpoint"""
    
    def test_dashboard_stats_returns_all_fields(self, admin_token):
        """Dashboard stats should return all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Check all required fields exist
        required_fields = [
            "total_workers", "active_workers_now", "total_punched_in_today",
            "inactive_alerts", "fraud_alerts_active", "sales_today", "revenue_today",
            "sales_month", "revenue_month", "active_campaigns", "total_coupons_available",
            "total_areas", "total_branches", "pending_expenses", "expenses_month",
            "encashments_today", "net_payable", "timezone", "last_updated"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify timezone is IST
        assert data["timezone"] == "Asia/Kolkata", f"Expected IST timezone, got {data['timezone']}"
        
        # Verify numeric fields are numbers
        assert isinstance(data["revenue_today"], (int, float))
        assert isinstance(data["sales_today"], int)
        assert isinstance(data["pending_expenses"], int)
        
        print(f"✓ Dashboard stats: revenue_today=₹{data['revenue_today']}, sales_today={data['sales_today']}, pending_expenses={data['pending_expenses']}")
    
    def test_dashboard_stats_refresh(self, admin_token):
        """Dashboard stats should be refreshable"""
        # Call twice to verify consistency
        response1 = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        response2 = requests.get(
            f"{BASE_URL}/api/admin/dashboard-stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Core stats should be consistent
        assert data1["total_workers"] == data2["total_workers"]
        assert data1["active_campaigns"] == data2["active_campaigns"]
        print("✓ Dashboard stats refresh works correctly")


class TestSoldCoupons:
    """Test Sold Coupons admin endpoint"""
    
    def test_sold_coupons_endpoint_exists(self, admin_token):
        """Sold coupons endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/sold-coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Sold coupons failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "coupons" in data
        assert "total" in data
        assert "today_sold" in data
        assert "worker_summary" in data
        assert "filters" in data
        
        print(f"✓ Sold coupons: total={data['total']}, today_sold={data['today_sold']}")
    
    def test_sold_coupons_filters_structure(self, admin_token):
        """Sold coupons should have filter dropdowns"""
        response = requests.get(
            f"{BASE_URL}/api/admin/sold-coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        filters = data["filters"]
        assert "workers" in filters
        assert "campaigns" in filters
        assert "branches" in filters
        
        # Each filter should be a list of {id, name}
        if filters["workers"]:
            assert "id" in filters["workers"][0]
            assert "name" in filters["workers"][0]
        
        print(f"✓ Sold coupons filters: {len(filters['workers'])} workers, {len(filters['campaigns'])} campaigns, {len(filters['branches'])} branches")
    
    def test_sold_coupons_worker_filter(self, admin_token):
        """Sold coupons should filter by worker_id"""
        # First get all to find a worker
        response = requests.get(
            f"{BASE_URL}/api/admin/sold-coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        if data["coupons"]:
            worker_id = data["coupons"][0].get("worker_id")
            if worker_id:
                # Filter by this worker
                filtered_response = requests.get(
                    f"{BASE_URL}/api/admin/sold-coupons?worker_id={worker_id}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert filtered_response.status_code == 200
                filtered_data = filtered_response.json()
                
                # All results should be from this worker
                for coupon in filtered_data["coupons"]:
                    assert coupon["worker_id"] == worker_id
                
                print(f"✓ Worker filter works: {len(filtered_data['coupons'])} coupons for worker {worker_id}")
        else:
            print("✓ No sold coupons to filter (empty data)")
    
    def test_sold_coupons_coupon_details(self, admin_token):
        """Sold coupons should include all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/sold-coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        if data["coupons"]:
            coupon = data["coupons"][0]
            required_fields = [
                "id", "code", "customer_name", "worker_name", 
                "campaign_name", "campaign_price", "sold_at", "payment_mode"
            ]
            for field in required_fields:
                assert field in coupon, f"Missing field in coupon: {field}"
            
            print(f"✓ Coupon details complete: {coupon['code']} - {coupon['customer_name']} - ₹{coupon['campaign_price']}")
        else:
            print("✓ No sold coupons to verify (empty data)")


class TestDataEntry:
    """Test Data Entry endpoint with today_count"""
    
    def test_admin_data_entry_returns_today_count(self, admin_token):
        """Admin data entry should return today_count"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Data entry failed: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "entries" in data
        assert "total" in data
        assert "today_count" in data, "Missing today_count field"
        assert "workers" in data
        
        assert isinstance(data["today_count"], int)
        
        print(f"✓ Data entry: total={data['total']}, today_count={data['today_count']}")
    
    def test_data_entry_workers_dropdown(self, admin_token):
        """Data entry should return workers for filter dropdown"""
        response = requests.get(
            f"{BASE_URL}/api/admin/data-entry",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        assert "workers" in data
        assert isinstance(data["workers"], list)
        
        if data["workers"]:
            worker = data["workers"][0]
            assert "id" in worker
            assert "name" in worker
        
        print(f"✓ Data entry workers dropdown: {len(data['workers'])} workers")


class TestLedgerExpenses:
    """Test Ledger and Expenses endpoints"""
    
    def test_ledgers_all_endpoint(self, admin_token):
        """Ledgers all endpoint should return worker ledgers"""
        response = requests.get(
            f"{BASE_URL}/api/ledgers/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Ledgers failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        
        if data:
            ledger = data[0]
            required_fields = [
                "worker_id", "worker_name", "total_coupons_sold", 
                "total_revenue", "total_expenses", "net_payable"
            ]
            for field in required_fields:
                assert field in ledger, f"Missing field: {field}"
        
        print(f"✓ Ledgers: {len(data)} workers")
    
    def test_expenses_endpoint(self, admin_token):
        """Expenses endpoint should return expenses list"""
        response = requests.get(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expenses failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        
        if data:
            expense = data[0]
            required_fields = ["id", "worker_id", "type", "amount", "status"]
            for field in required_fields:
                assert field in expense, f"Missing field: {field}"
            
            # Check bill_photo_url field exists (can be null)
            assert "bill_photo_url" in expense
            
            if expense.get("bill_photo_url"):
                print(f"✓ Expense with bill photo: {expense['bill_photo_url']}")
        
        print(f"✓ Expenses: {len(data)} records")
    
    def test_expense_bill_image_accessible(self, admin_token):
        """Expense bill images should be accessible"""
        # Get expenses with photos
        response = requests.get(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        data = response.json()
        
        expenses_with_photos = [e for e in data if e.get("bill_photo_url")]
        
        if expenses_with_photos:
            expense = expenses_with_photos[0]
            photo_url = expense["bill_photo_url"]
            
            # Convert relative URL to full URL
            if photo_url.startswith("/uploads/"):
                full_url = f"{BASE_URL}/api/uploads/{photo_url.replace('/uploads/', '')}"
            else:
                full_url = f"{BASE_URL}{photo_url}"
            
            # Check image is accessible (HEAD request)
            img_response = requests.head(full_url)
            assert img_response.status_code == 200, f"Bill image not accessible: {full_url} - {img_response.status_code}"
            
            print(f"✓ Bill image accessible: {full_url}")
        else:
            print("✓ No expenses with bill photos to test")


class TestWorkerSale:
    """Test Worker Sale endpoint (backend validation only)"""
    
    def test_coupon_validation_endpoint(self, worker_token):
        """Coupon validation endpoint should work"""
        # Try to validate a coupon code
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"coupon_code": "UT001"}
        )
        assert response.status_code == 200, f"Validation failed: {response.text}"
        data = response.json()
        
        assert "valid" in data
        assert "message" in data
        
        print(f"✓ Coupon validation: valid={data['valid']}, message={data['message']}")
    
    def test_branches_endpoint_for_sale(self, worker_token):
        """Branches endpoint should be accessible for worker sale flow"""
        response = requests.get(
            f"{BASE_URL}/api/branches",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200, f"Branches failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        
        if data:
            branch = data[0]
            assert "id" in branch
            assert "name" in branch
        
        print(f"✓ Branches for sale: {len(data)} branches available")
    
    def test_worker_sale_requires_gps(self, worker_token):
        """Worker sale should require GPS coordinates"""
        # Try to make a sale without GPS - should fail
        response = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "coupon_code": "UT001",
                "customer_name": "Test Customer",
                "customer_phone": "9876543210",
                "branch_id": "test-branch-id"
                # Missing latitude, longitude
            }
        )
        # Should fail with validation error (422) or bad request (400)
        assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"
        print("✓ Worker sale correctly requires GPS coordinates")


class TestSidebarNavigation:
    """Test that Sold Coupons route exists"""
    
    def test_sold_coupons_route_accessible(self, admin_token):
        """Sold coupons page should be accessible"""
        response = requests.get(
            f"{BASE_URL}/api/admin/sold-coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("✓ Sold coupons route is accessible")


class TestCRERemarks:
    """Test CRE remarks endpoint"""
    
    def test_cre_remarks_endpoint(self, admin_token):
        """CRE remarks endpoint should work"""
        response = requests.get(
            f"{BASE_URL}/api/admin/cre-remarks",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"CRE remarks failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ CRE remarks: {len(data)} records")


class TestEncashments:
    """Test encashments endpoint"""
    
    def test_encashments_endpoint(self, admin_token):
        """Encashments endpoint should work"""
        response = requests.get(
            f"{BASE_URL}/api/admin/encashments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Encashments failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"✓ Encashments: {len(data)} records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
