"""
Field Revenue Intelligence System - Comprehensive Backend Tests
Tests for: Campaigns, Coupon Sales, Worker Ledger, Expenses, Admin Controls, Areas
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"
WORKER_EMAIL = "testworker@fieldflow.com"
WORKER_PASSWORD = "worker123"

# Test data tracking
TEST_PREFIX = f"TEST{uuid.uuid4().hex[:4].upper()}"
created_campaign_id = None
created_area_id = None
created_worker_id = None
test_coupon_code = None


class TestAuthAndSetup:
    """Authentication and initial setup tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        # Try to register if login fails
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Test Admin",
            "role": "admin"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        """Get worker authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        # Try to register if login fails
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD,
            "name": "Test Worker",
            "role": "worker"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Worker authentication failed")
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "3.0.0"
        print(f"✓ Health check passed - Version: {data['version']}")
    
    def test_admin_login(self, admin_token):
        """Test admin login"""
        assert admin_token is not None
        print(f"✓ Admin login successful")
    
    def test_worker_login(self, worker_token):
        """Test worker login"""
        assert worker_token is not None
        print(f"✓ Worker login successful")


class TestAreaManagement:
    """Area creation and listing tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_create_area(self, admin_token):
        """Test area creation"""
        global created_area_id
        response = requests.post(
            f"{BASE_URL}/api/areas",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_Area_{uuid.uuid4().hex[:6]}",
                "city": "Mumbai",
                "state": "Maharashtra",
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["city"] == "Mumbai"
        assert data["state"] == "Maharashtra"
        created_area_id = data["id"]
        print(f"✓ Area created: {data['name']} (ID: {created_area_id})")
    
    def test_list_areas(self, admin_token):
        """Test area listing"""
        response = requests.get(
            f"{BASE_URL}/api/areas",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Areas listed: {len(data)} areas found")
    
    def test_get_states(self, admin_token):
        """Test getting unique states"""
        response = requests.get(
            f"{BASE_URL}/api/areas/states",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ States retrieved: {data}")


class TestCampaignManagement:
    """Campaign CRUD and coupon generation tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_create_campaign(self, admin_token):
        """Test campaign creation with auto-generated coupon codes"""
        global created_campaign_id, test_coupon_code, TEST_PREFIX
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"Test Campaign {TEST_PREFIX}",
                "price": 149.0,
                "total_count": 10,
                "prefix": TEST_PREFIX
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == f"Test Campaign {TEST_PREFIX}"
        assert data["price"] == 149.0
        assert data["total_count"] == 10
        assert data["prefix"] == TEST_PREFIX
        assert data["sold_count"] == 0
        assert data["available_count"] == 10
        assert data["status"] == "ACTIVE"
        created_campaign_id = data["id"]
        test_coupon_code = f"{TEST_PREFIX}001"  # First coupon code
        print(f"✓ Campaign created: {data['name']} with prefix {TEST_PREFIX}")
        print(f"  - Expected coupon codes: {TEST_PREFIX}001 to {TEST_PREFIX}010")
    
    def test_list_campaigns(self, admin_token):
        """Test campaign listing with statistics"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Find our test campaign
        test_campaign = next((c for c in data if c.get("prefix") == TEST_PREFIX), None)
        if test_campaign:
            assert test_campaign["sold_count"] == 0
            assert test_campaign["available_count"] == 10
        print(f"✓ Campaigns listed: {len(data)} campaigns found")
    
    def test_get_campaign_coupons(self, admin_token):
        """Test getting coupons for a campaign"""
        global created_campaign_id
        if not created_campaign_id:
            pytest.skip("No campaign created")
        
        response = requests.get(
            f"{BASE_URL}/api/campaigns/{created_campaign_id}/coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # We created 10 coupons
        # Verify coupon codes are properly formatted
        codes = [c["code"] for c in data]
        assert f"{TEST_PREFIX}001" in codes
        assert f"{TEST_PREFIX}010" in codes
        # All should be AVAILABLE
        for coupon in data:
            assert coupon["status"] == "AVAILABLE"
        print(f"✓ Campaign coupons retrieved: {len(data)} coupons")
        print(f"  - Codes: {codes[:3]}...{codes[-1]}")
    
    def test_duplicate_prefix_rejected(self, admin_token):
        """Test that duplicate campaign prefix is rejected"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Duplicate Campaign",
                "price": 99.0,
                "total_count": 5,
                "prefix": TEST_PREFIX  # Same prefix as before
            }
        )
        assert response.status_code == 400
        print(f"✓ Duplicate prefix correctly rejected")


class TestCouponValidationAndSale:
    """Coupon validation and sale flow tests"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Worker authentication failed")
    
    def test_validate_coupon_code_valid(self, worker_token):
        """Test validating a valid coupon code"""
        global test_coupon_code
        if not test_coupon_code:
            pytest.skip("No test coupon code available")
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"coupon_code": test_coupon_code}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["status"] == "AVAILABLE"
        assert data["campaign_price"] == 149.0
        assert "campaign_name" in data
        print(f"✓ Coupon validation passed: {test_coupon_code} is valid")
        print(f"  - Campaign: {data['campaign_name']}, Price: ₹{data['campaign_price']}")
    
    def test_validate_coupon_code_invalid(self, worker_token):
        """Test validating an invalid coupon code"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"coupon_code": "INVALID999"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        print(f"✓ Invalid coupon correctly rejected")
    
    def test_sell_coupon(self, worker_token):
        """Test selling a coupon"""
        global test_coupon_code
        if not test_coupon_code:
            pytest.skip("No test coupon code available")
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/sell",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "coupon_code": test_coupon_code,
                "customer_name": "Test Customer",
                "customer_phone": "9876543210",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "gps_accuracy": 50.0  # Good accuracy
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["coupon_code"] == test_coupon_code
        assert data["campaign_price"] == 149.0
        assert "ledger" in data["message"].lower()
        print(f"✓ Coupon sold successfully: {test_coupon_code}")
        print(f"  - Customer: {data['customer_name']}, Price: ₹{data['campaign_price']}")
    
    def test_sell_already_sold_coupon(self, worker_token):
        """Test that selling an already sold coupon fails"""
        global test_coupon_code
        if not test_coupon_code:
            pytest.skip("No test coupon code available")
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/sell",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "coupon_code": test_coupon_code,
                "customer_name": "Another Customer",
                "customer_phone": "9876543211",
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        )
        assert response.status_code == 400
        print(f"✓ Already sold coupon correctly rejected")
    
    def test_gps_accuracy_rejection(self, worker_token):
        """Test that low GPS accuracy is rejected"""
        # Use second coupon code
        second_coupon = f"{TEST_PREFIX}002"
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/sell",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "coupon_code": second_coupon,
                "customer_name": "Test Customer 2",
                "customer_phone": "9876543212",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "gps_accuracy": 150.0  # Too low accuracy (>100m)
            }
        )
        assert response.status_code == 400
        assert "accuracy" in response.json().get("detail", "").lower()
        print(f"✓ Low GPS accuracy correctly rejected (150m > 100m threshold)")


class TestWorkerLedger:
    """Worker ledger and transaction tests"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Worker authentication failed")
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def worker_id(self, worker_token):
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        if response.status_code == 200:
            return response.json().get("id")
        pytest.skip("Could not get worker ID")
    
    def test_get_worker_ledger(self, worker_token, worker_id):
        """Test getting worker's ledger"""
        response = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/ledger",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_coupons_sold" in data
        assert "total_revenue" in data
        assert "total_advances" in data
        assert "total_expenses" in data
        assert "net_payable" in data
        # After selling one coupon, should have at least 1 sale
        assert data["total_coupons_sold"] >= 1
        assert data["total_revenue"] >= 149.0  # At least one sale at 149
        print(f"✓ Worker ledger retrieved:")
        print(f"  - Coupons sold: {data['total_coupons_sold']}")
        print(f"  - Total revenue: ₹{data['total_revenue']}")
        print(f"  - Net payable: ₹{data['net_payable']}")
    
    def test_get_worker_transactions(self, worker_token, worker_id):
        """Test getting worker's transaction history"""
        response = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/transactions",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least one SALE transaction
        sale_transactions = [t for t in data if t["type"] == "SALE"]
        assert len(sale_transactions) >= 1
        print(f"✓ Worker transactions retrieved: {len(data)} transactions")
    
    def test_admin_add_advance(self, admin_token, worker_id):
        """Test admin adding advance to worker"""
        response = requests.post(
            f"{BASE_URL}/api/workers/{worker_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "amount": 500.0,
                "description": "Test advance payment"
            }
        )
        assert response.status_code == 200
        print(f"✓ Advance of ₹500 added to worker")
    
    def test_ledger_updated_after_advance(self, worker_token, worker_id):
        """Test that ledger is updated after advance"""
        response = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/ledger",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_advances"] >= 500.0
        print(f"✓ Ledger updated - Total advances: ₹{data['total_advances']}")
    
    def test_admin_view_all_ledgers(self, admin_token):
        """Test admin viewing all worker ledgers"""
        response = requests.get(
            f"{BASE_URL}/api/ledgers/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ All ledgers retrieved: {len(data)} workers")


class TestExpenseModule:
    """Expense submission and approval tests"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Worker authentication failed")
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_submit_small_expense_without_photo(self, worker_token):
        """Test submitting expense under ₹100 without photo"""
        response = requests.post(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "type": "Travel",
                "amount": 50.0,
                "description": "Auto fare",
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50.0
        assert data["type"] == "Travel"
        assert data["status"] == "PENDING"
        print(f"✓ Small expense (₹50) submitted without photo")
    
    def test_large_expense_requires_photo(self, worker_token):
        """Test that expense >₹100 requires photo"""
        response = requests.post(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "type": "Equipment",
                "amount": 150.0,
                "description": "Test equipment",
                "latitude": 19.0760,
                "longitude": 72.8777
                # No photo provided
            }
        )
        assert response.status_code == 400
        assert "photo" in response.json().get("detail", "").lower()
        print(f"✓ Large expense (₹150) correctly requires photo")
    
    def test_get_worker_expenses(self, worker_token):
        """Test getting worker's expenses"""
        response = requests.get(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Worker expenses retrieved: {len(data)} expenses")


class TestAdminWorkerControl:
    """Admin worker management tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_create_worker(self, admin_token):
        """Test admin creating a new worker"""
        global created_worker_id
        test_email = f"test_worker_{uuid.uuid4().hex[:6]}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/workers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": test_email,
                "password": "testpass123",
                "name": "Test Created Worker",
                "phone": "9876543299"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_email
        assert data["role"] == "worker"
        created_worker_id = data["id"]
        print(f"✓ Worker created: {data['name']} (ID: {created_worker_id})")
    
    def test_disable_worker(self, admin_token):
        """Test disabling a worker"""
        global created_worker_id
        if not created_worker_id:
            pytest.skip("No worker created")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/workers/{created_worker_id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Worker disabled successfully")
    
    def test_enable_worker(self, admin_token):
        """Test enabling a worker"""
        global created_worker_id
        if not created_worker_id:
            pytest.skip("No worker created")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/workers/{created_worker_id}/enable",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Worker enabled successfully")
    
    def test_reset_worker_password(self, admin_token):
        """Test resetting worker password"""
        global created_worker_id
        if not created_worker_id:
            pytest.skip("No worker created")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/workers/{created_worker_id}/reset-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_password": "newpassword123"}
        )
        assert response.status_code == 200
        print(f"✓ Worker password reset successfully")
    
    def test_delete_worker_without_sales(self, admin_token):
        """Test deleting a worker without sales"""
        global created_worker_id
        if not created_worker_id:
            pytest.skip("No worker created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/workers/{created_worker_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Worker deleted successfully")


class TestAdminDashboard:
    """Admin dashboard statistics tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_get_admin_dashboard_stats(self, admin_token):
        """Test getting comprehensive admin dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Verify all expected fields
        assert "total_workers" in data
        assert "active_workers_today" in data
        assert "inactive_alerts" in data
        assert "total_sales_today" in data
        assert "total_revenue_today" in data
        assert "total_sales_month" in data
        assert "total_revenue_month" in data
        assert "active_campaigns" in data
        assert "total_coupons_available" in data
        assert "total_areas" in data
        assert "pending_expenses" in data
        assert "net_payable_all_workers" in data
        print(f"✓ Admin dashboard stats retrieved:")
        print(f"  - Total workers: {data['total_workers']}")
        print(f"  - Active campaigns: {data['active_campaigns']}")
        print(f"  - Sales today: {data['total_sales_today']}")
        print(f"  - Revenue today: ₹{data['total_revenue_today']}")
    
    def test_get_inactivity_alerts(self, admin_token):
        """Test getting inactivity alerts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/inactivity-alerts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Inactivity alerts retrieved: {len(data)} alerts")
    
    def test_get_spoofing_alerts(self, admin_token):
        """Test getting location spoofing alerts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/spoofing-alerts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Spoofing alerts retrieved: {len(data)} alerts")


class TestAreaAnalytics:
    """Area analytics tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_get_sales_analytics(self, admin_token):
        """Test getting sales analytics summary"""
        response = requests.get(
            f"{BASE_URL}/api/areas/analytics/summary?days=30",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "total_revenue" in data
        assert "sales_by_campaign" in data
        assert "sales_by_area" in data
        assert "sales_by_worker" in data
        assert "daily_trend" in data
        print(f"✓ Sales analytics retrieved:")
        print(f"  - Total sales: {data['total_sales']}")
        print(f"  - Total revenue: ₹{data['total_revenue']}")


class TestCampaignStatusUpdate:
    """Campaign status update tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_update_campaign_status_to_inactive(self, admin_token):
        """Test updating campaign status to INACTIVE"""
        global created_campaign_id
        if not created_campaign_id:
            pytest.skip("No campaign created")
        
        response = requests.patch(
            f"{BASE_URL}/api/campaigns/{created_campaign_id}?status=INACTIVE",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Campaign status updated to INACTIVE")
    
    def test_validate_coupon_from_inactive_campaign(self):
        """Test that coupons from inactive campaign are rejected"""
        # Login as worker
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": WORKER_EMAIL,
            "password": WORKER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Worker login failed")
        worker_token = response.json().get("access_token")
        
        # Try to validate a coupon from the now-inactive campaign
        third_coupon = f"{TEST_PREFIX}003"
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"coupon_code": third_coupon}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "not active" in data["message"].lower()
        print(f"✓ Coupon from inactive campaign correctly rejected")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
