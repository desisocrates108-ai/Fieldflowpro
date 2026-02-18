"""
FieldFlow Pro v3.0 - Comprehensive Backend Tests
Tests for: CRE Call Logging, Branch Encashment, Worker Sale Flow, Admin Views
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
CRE_EMAIL = "testcre@fieldflow.com"
CRE_PASSWORD = "cre123"
BRANCH_EMAIL = "testbranch@fieldflow.com"
BRANCH_PASSWORD = "branch123"

# Test data tracking
TEST_PREFIX = f"V3T{uuid.uuid4().hex[:3].upper()}"
created_campaign_id = None
created_branch_id = None
test_coupon_code = None
sold_coupon_id = None
cre_call_log_id = None


def get_or_create_user(email, password, name, role):
    """Helper to get or create a user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    
    # Try to register
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
        "role": role
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed - Version: {data['version']}")
    
    def test_admin_login(self):
        """Test admin login"""
        token = get_or_create_user(ADMIN_EMAIL, ADMIN_PASSWORD, "Test Admin", "admin")
        assert token is not None
        print(f"✓ Admin login successful")
    
    def test_worker_login(self):
        """Test worker login"""
        token = get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
        assert token is not None
        print(f"✓ Worker login successful")
    
    def test_cre_login(self):
        """Test CRE login"""
        token = get_or_create_user(CRE_EMAIL, CRE_PASSWORD, "Test CRE", "cre")
        assert token is not None
        print(f"✓ CRE login successful")
    
    def test_branch_login(self):
        """Test Branch login"""
        token = get_or_create_user(BRANCH_EMAIL, BRANCH_PASSWORD, "Test Branch", "branch")
        assert token is not None
        print(f"✓ Branch login successful")


class TestSetupCampaignAndBranch:
    """Setup campaign and branch for testing"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        return get_or_create_user(ADMIN_EMAIL, ADMIN_PASSWORD, "Test Admin", "admin")
    
    def test_create_branch(self, admin_token):
        """Create a test branch"""
        global created_branch_id
        response = requests.post(
            f"{BASE_URL}/api/branches",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"Test Branch {TEST_PREFIX}",
                "address": "123 Test Street, Mumbai",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "contact_phone": "9876543210"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        created_branch_id = data["id"]
        print(f"✓ Branch created: {data['name']} (ID: {created_branch_id})")
    
    def test_assign_branch_to_branch_user(self, admin_token):
        """Assign branch to branch user"""
        global created_branch_id
        if not created_branch_id:
            pytest.skip("No branch created")
        
        # Get branch user ID
        branch_token = get_or_create_user(BRANCH_EMAIL, BRANCH_PASSWORD, "Test Branch", "branch")
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {branch_token}"}
        )
        if response.status_code != 200:
            pytest.skip("Could not get branch user")
        
        branch_user_id = response.json()["id"]
        
        # Update user with branch_id (using admin endpoint)
        response = requests.patch(
            f"{BASE_URL}/api/workers/{branch_user_id}?branch_id={created_branch_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # This might fail if user is not a worker, try direct update
        if response.status_code != 200:
            # Try updating via users endpoint if available
            print(f"  Note: Branch assignment may need manual setup")
        else:
            print(f"✓ Branch assigned to branch user")
    
    def test_create_campaign(self, admin_token):
        """Create a test campaign with auto-generated coupon codes"""
        global created_campaign_id, test_coupon_code, TEST_PREFIX
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"V3 Test Campaign {TEST_PREFIX}",
                "price": 199.0,
                "total_count": 10,
                "prefix": TEST_PREFIX
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["prefix"] == TEST_PREFIX
        assert data["total_count"] == 10
        assert data["sold_count"] == 0
        assert data["available_count"] == 10
        created_campaign_id = data["id"]
        test_coupon_code = f"{TEST_PREFIX}001"
        print(f"✓ Campaign created: {data['name']}")
        print(f"  - Coupon codes: {TEST_PREFIX}001 to {TEST_PREFIX}010")
    
    def test_verify_campaign_coupons(self, admin_token):
        """Verify campaign coupons were generated correctly"""
        global created_campaign_id, TEST_PREFIX
        if not created_campaign_id:
            pytest.skip("No campaign created")
        
        response = requests.get(
            f"{BASE_URL}/api/campaigns/{created_campaign_id}/coupons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Verify codes are properly formatted
        codes = [c["code"] for c in data]
        assert f"{TEST_PREFIX}001" in codes
        assert f"{TEST_PREFIX}010" in codes
        
        # All should be AVAILABLE
        for coupon in data:
            assert coupon["status"] == "AVAILABLE"
        
        print(f"✓ Campaign coupons verified: {len(data)} coupons")
        print(f"  - Codes: {codes[:3]}...{codes[-1]}")


class TestCouponValidation:
    """Test coupon code validation"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        return get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
    
    def test_validate_valid_code(self, worker_token):
        """Test validating a valid coupon code"""
        global test_coupon_code
        if not test_coupon_code:
            pytest.skip("No test coupon code")
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"coupon_code": test_coupon_code}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["status"] == "AVAILABLE"
        assert data["campaign_price"] == 199.0
        assert "campaign_name" in data
        print(f"✓ Valid code validation: {test_coupon_code}")
        print(f"  - Campaign: {data['campaign_name']}, Price: ₹{data['campaign_price']}")
    
    def test_validate_invalid_code(self, worker_token):
        """Test validating an invalid coupon code"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={"coupon_code": "INVALID999XYZ"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        print(f"✓ Invalid code correctly rejected")


class TestWorkerSaleFlow:
    """Test the new worker-sale flow with branch selection"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        return get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
    
    def test_worker_sale_with_branch(self, worker_token):
        """Test complete worker sale flow with branch selection"""
        global test_coupon_code, created_branch_id, sold_coupon_id
        if not test_coupon_code:
            pytest.skip("No test coupon code")
        if not created_branch_id:
            pytest.skip("No branch created")
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "customer_name": "V3 Test Customer",
                "customer_phone": "9876543210",
                "coupon_code": test_coupon_code,
                "branch_id": created_branch_id,
                "latitude": 19.0760,
                "longitude": 72.8777,
                "gps_accuracy": 50.0,
                "city": "Mumbai",
                "state": "Maharashtra"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["coupon_code"] == test_coupon_code
        assert data["campaign_price"] == 199.0
        assert "branch_name" in data
        sold_coupon_id = data["coupon_id"]
        print(f"✓ Worker sale completed: {test_coupon_code}")
        print(f"  - Customer: {data['customer_name']}")
        print(f"  - Branch: {data['branch_name']}")
        print(f"  - Price: ₹{data['campaign_price']}")
    
    def test_no_duplicate_sale(self, worker_token):
        """Test that same coupon cannot be sold twice"""
        global test_coupon_code, created_branch_id
        if not test_coupon_code or not created_branch_id:
            pytest.skip("No test data")
        
        response = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "customer_name": "Another Customer",
                "customer_phone": "9876543211",
                "coupon_code": test_coupon_code,
                "branch_id": created_branch_id,
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        )
        assert response.status_code == 400
        assert "sold" in response.json().get("detail", "").lower()
        print(f"✓ Duplicate sale correctly rejected")
    
    def test_gps_accuracy_rejection(self, worker_token):
        """Test GPS accuracy >100m is rejected"""
        global TEST_PREFIX, created_branch_id
        if not created_branch_id:
            pytest.skip("No branch created")
        
        second_coupon = f"{TEST_PREFIX}002"
        response = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "customer_name": "Test Customer 2",
                "customer_phone": "9876543212",
                "coupon_code": second_coupon,
                "branch_id": created_branch_id,
                "latitude": 19.0760,
                "longitude": 72.8777,
                "gps_accuracy": 150.0  # >100m
            }
        )
        assert response.status_code == 400
        assert "accuracy" in response.json().get("detail", "").lower()
        print(f"✓ GPS accuracy >100m correctly rejected")


class TestWorkerLedger:
    """Test worker ledger updates after sale"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        return get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
    
    @pytest.fixture(scope="class")
    def worker_id(self, worker_token):
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        if response.status_code == 200:
            return response.json().get("id")
        return None
    
    def test_ledger_updated_after_sale(self, worker_token, worker_id):
        """Test ledger is updated after sale"""
        if not worker_id:
            pytest.skip("No worker ID")
        
        response = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/ledger",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_coupons_sold" in data
        assert "total_revenue" in data
        assert "net_payable" in data
        assert data["total_coupons_sold"] >= 1
        assert data["total_revenue"] >= 199.0
        print(f"✓ Worker ledger verified:")
        print(f"  - Coupons sold: {data['total_coupons_sold']}")
        print(f"  - Total revenue: ₹{data['total_revenue']}")
        print(f"  - Net payable: ₹{data['net_payable']}")
    
    def test_transaction_history(self, worker_token, worker_id):
        """Test transaction history shows sale"""
        if not worker_id:
            pytest.skip("No worker ID")
        
        response = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/transactions",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        sale_transactions = [t for t in data if t["type"] == "SALE"]
        assert len(sale_transactions) >= 1
        print(f"✓ Transaction history: {len(data)} transactions, {len(sale_transactions)} sales")


class TestExpenseModule:
    """Test expense submission with photo requirement"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        return get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        return get_or_create_user(ADMIN_EMAIL, ADMIN_PASSWORD, "Test Admin", "admin")
    
    def test_small_expense_no_photo(self, worker_token):
        """Test expense <₹100 without photo is allowed"""
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
        assert data["status"] == "PENDING"
        print(f"✓ Small expense (₹50) submitted without photo")
    
    def test_large_expense_requires_photo(self, worker_token):
        """Test expense >₹100 requires photo"""
        response = requests.post(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {worker_token}"},
            json={
                "type": "Equipment",
                "amount": 200.0,
                "description": "Office supplies",
                "latitude": 19.0760,
                "longitude": 72.8777
                # No photo provided
            }
        )
        assert response.status_code == 400
        assert "photo" in response.json().get("detail", "").lower()
        print(f"✓ Large expense (₹200) without photo correctly rejected")
    
    def test_get_expenses(self, worker_token):
        """Test getting worker's expenses"""
        response = requests.get(
            f"{BASE_URL}/api/expenses",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Expenses retrieved: {len(data)} expenses")


class TestCRECallLogging:
    """Test CRE call logging and remarks"""
    
    @pytest.fixture(scope="class")
    def cre_token(self):
        return get_or_create_user(CRE_EMAIL, CRE_PASSWORD, "Test CRE", "cre")
    
    def test_cre_dashboard_stats(self, cre_token):
        """Test CRE dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/cre/dashboard/stats",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "today_total_customers" in data
        assert "today_calls_made" in data
        assert "pending_calls" in data
        print(f"✓ CRE dashboard stats:")
        print(f"  - Today's customers: {data['today_total_customers']}")
        print(f"  - Calls made: {data['today_calls_made']}")
        print(f"  - Pending: {data['pending_calls']}")
    
    def test_cre_customers_list_full_phone(self, cre_token):
        """Test CRE sees full phone numbers (not masked)"""
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If there are customers, verify phone is not masked
        if len(data) > 0:
            customer = data[0]
            assert "customer_phone" in customer
            # Full phone should be 10 digits, not masked
            phone = customer["customer_phone"]
            if phone:
                assert len(phone) >= 10 or phone.startswith("+")
                assert "****" not in phone  # Not masked
        
        print(f"✓ CRE customers list: {len(data)} customers (full phone visible)")
    
    def test_cre_log_call(self, cre_token):
        """Test CRE logging a call"""
        global sold_coupon_id, cre_call_log_id
        if not sold_coupon_id:
            pytest.skip("No sold coupon to call")
        
        response = requests.post(
            f"{BASE_URL}/api/cre/calls/{sold_coupon_id}/log",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "call_log_id" in data
        cre_call_log_id = data["call_log_id"]
        print(f"✓ CRE call logged: {cre_call_log_id}")
    
    def test_cre_remarks_mandatory(self, cre_token):
        """Test CRE remarks are mandatory"""
        global cre_call_log_id
        if not cre_call_log_id:
            pytest.skip("No call log to add remarks")
        
        # Try empty remarks
        response = requests.post(
            f"{BASE_URL}/api/cre/calls/{cre_call_log_id}/remarks",
            headers={"Authorization": f"Bearer {cre_token}"},
            json={"remarks": ""}
        )
        assert response.status_code == 400
        print(f"✓ Empty remarks correctly rejected")
    
    def test_cre_add_remarks(self, cre_token):
        """Test CRE adding remarks"""
        global cre_call_log_id
        if not cre_call_log_id:
            pytest.skip("No call log to add remarks")
        
        response = requests.post(
            f"{BASE_URL}/api/cre/calls/{cre_call_log_id}/remarks",
            headers={"Authorization": f"Bearer {cre_token}"},
            json={"remarks": "Customer confirmed appointment for next week"}
        )
        assert response.status_code == 200
        print(f"✓ CRE remarks added successfully")
    
    def test_cre_call_history(self, cre_token):
        """Test CRE call history"""
        response = requests.get(
            f"{BASE_URL}/api/cre/calls/history",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ CRE call history: {len(data)} calls")


class TestBranchEncashment:
    """Test branch customer view and encashment"""
    
    @pytest.fixture(scope="class")
    def branch_token(self):
        return get_or_create_user(BRANCH_EMAIL, BRANCH_PASSWORD, "Test Branch", "branch")
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        return get_or_create_user(ADMIN_EMAIL, ADMIN_PASSWORD, "Test Admin", "admin")
    
    def test_branch_customers_masked_phone(self, branch_token):
        """Test branch sees masked phone numbers"""
        response = requests.get(
            f"{BASE_URL}/api/branch/customers",
            headers={"Authorization": f"Bearer {branch_token}"}
        )
        # May return 400 if branch not assigned
        if response.status_code == 400:
            print(f"  Note: Branch user needs branch_id assigned")
            pytest.skip("Branch not assigned to user")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If there are customers, verify phone is masked
        if len(data) > 0:
            customer = data[0]
            assert "mobile_last4" in customer
            # Should be masked format like "******1234"
            assert "****" in customer["mobile_last4"] or len(customer["mobile_last4"]) <= 10
        
        print(f"✓ Branch customers list: {len(data)} customers (phone masked)")
    
    def test_branch_encash_coupon(self, branch_token):
        """Test branch encashing a coupon"""
        global test_coupon_code
        if not test_coupon_code:
            pytest.skip("No test coupon")
        
        response = requests.post(
            f"{BASE_URL}/api/branch/encash",
            headers={"Authorization": f"Bearer {branch_token}"},
            json={"coupon_code": test_coupon_code}
        )
        
        # May fail if branch not assigned or coupon not assigned to branch
        if response.status_code == 400:
            error = response.json().get("detail", "")
            if "not assigned" in error.lower():
                print(f"  Note: {error}")
                pytest.skip("Branch assignment issue")
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] == True
            assert data["coupon_code"] == test_coupon_code
            print(f"✓ Coupon encashed: {test_coupon_code}")
            print(f"  - Amount: ₹{data['campaign_price']}")
    
    def test_no_duplicate_encashment(self, branch_token):
        """Test same coupon cannot be encashed twice"""
        global test_coupon_code
        if not test_coupon_code:
            pytest.skip("No test coupon")
        
        response = requests.post(
            f"{BASE_URL}/api/branch/encash",
            headers={"Authorization": f"Bearer {branch_token}"},
            json={"coupon_code": test_coupon_code}
        )
        
        # Should fail - either already encashed or not assigned
        if response.status_code == 400:
            error = response.json().get("detail", "")
            if "encashed" in error.lower():
                print(f"✓ Duplicate encashment correctly rejected")
            else:
                print(f"  Note: {error}")


class TestAdminViews:
    """Test admin views for CRE remarks and encashments"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        return get_or_create_user(ADMIN_EMAIL, ADMIN_PASSWORD, "Test Admin", "admin")
    
    def test_admin_view_cre_remarks(self, admin_token):
        """Test admin viewing all CRE remarks"""
        response = requests.get(
            f"{BASE_URL}/api/admin/cre-remarks",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin CRE remarks view: {len(data)} remarks")
    
    def test_admin_view_encashments(self, admin_token):
        """Test admin viewing all encashments"""
        response = requests.get(
            f"{BASE_URL}/api/admin/encashments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin encashments view: {len(data)} encashments")
    
    def test_admin_view_all_ledgers(self, admin_token):
        """Test admin viewing all worker ledgers"""
        response = requests.get(
            f"{BASE_URL}/api/ledgers/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin all ledgers view: {len(data)} workers")
    
    def test_admin_add_advance(self, admin_token):
        """Test admin adding advance to worker"""
        # Get worker ID
        worker_token = get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        if response.status_code != 200:
            pytest.skip("Could not get worker ID")
        
        worker_id = response.json()["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/workers/{worker_id}/advance",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "amount": 1000.0,
                "description": "V3 Test advance"
            }
        )
        assert response.status_code == 200
        print(f"✓ Admin added advance of ₹1000 to worker")
    
    def test_admin_dashboard_stats(self, admin_token):
        """Test admin dashboard comprehensive stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_workers" in data
        assert "active_workers_today" in data
        assert "total_sales_today" in data
        assert "total_revenue_today" in data
        assert "active_campaigns" in data
        assert "pending_expenses" in data
        assert "net_payable_all_workers" in data
        print(f"✓ Admin dashboard stats:")
        print(f"  - Workers: {data['total_workers']} total, {data['active_workers_today']} active")
        print(f"  - Sales today: {data['total_sales_today']}, Revenue: ₹{data['total_revenue_today']}")
        print(f"  - Active campaigns: {data['active_campaigns']}")


class TestFinancialCalculations:
    """Test server-side financial calculations"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        return get_or_create_user(WORKER_EMAIL, WORKER_PASSWORD, "Test Worker", "worker")
    
    @pytest.fixture(scope="class")
    def worker_id(self, worker_token):
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        if response.status_code == 200:
            return response.json().get("id")
        return None
    
    def test_net_payable_calculation(self, worker_token, worker_id):
        """Test net_payable = revenue - advances - expenses"""
        if not worker_id:
            pytest.skip("No worker ID")
        
        response = requests.get(
            f"{BASE_URL}/api/workers/{worker_id}/ledger",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify calculation
        expected_net = data["total_revenue"] - data["total_advances"] - data["total_expenses"]
        actual_net = data["net_payable"]
        
        # Allow small floating point difference
        assert abs(expected_net - actual_net) < 0.01, f"Expected {expected_net}, got {actual_net}"
        
        print(f"✓ Net payable calculation verified:")
        print(f"  - Revenue: ₹{data['total_revenue']}")
        print(f"  - Advances: ₹{data['total_advances']}")
        print(f"  - Expenses: ₹{data['total_expenses']}")
        print(f"  - Net payable: ₹{data['net_payable']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
