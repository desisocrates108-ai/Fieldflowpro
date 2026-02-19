"""
FieldFlow Pro Elite v4.0 - Admin Panel Upgrades Test Suite
Tests for:
1. Campaign Creation with Start/End Code Range
2. Expense Approval System (approve/reject)
3. Branch Management (delete/deactivate/activate)
4. Worker Expense Status and Rejection Reason
"""
import pytest
import requests
import os
from datetime import datetime
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"
WORKER_EMAIL = "testworker@fieldflow.com"
WORKER_PASSWORD = "worker123"


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
def admin_headers(admin_token):
    """Admin auth headers"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def worker_headers(worker_token):
    """Worker auth headers"""
    return {"Authorization": f"Bearer {worker_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def worker_id(worker_token):
    """Get worker's ID"""
    response = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {worker_token}"
    })
    assert response.status_code == 200
    return response.json()["id"]


# ========== Campaign Creation with Start/End Code Range ==========
class TestCampaignCreationRange:
    """Test campaign creation with start_code and end_code range"""
    
    def test_create_campaign_with_valid_range(self, admin_headers):
        """POST /api/campaigns with valid start_code/end_code creates campaign"""
        unique_prefix = f"T{uuid.uuid4().hex[:4].upper()}"
        response = requests.post(f"{BASE_URL}/api/campaigns", headers=admin_headers, json={
            "name": f"Test Campaign {unique_prefix}",
            "price": 149.0,
            "start_code": f"{unique_prefix}100",
            "end_code": f"{unique_prefix}200"
        })
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data["name"] == f"Test Campaign {unique_prefix}"
        assert data["price"] == 149.0
        assert data["prefix"] == unique_prefix
        assert data["total_count"] == 100  # 200 - 100 = 100 coupons
        assert data["available_count"] == 100
        assert data["sold_count"] == 0
        assert data["status"] == "ACTIVE"
    
    def test_campaign_prefix_extraction(self, admin_headers):
        """Verify prefix is correctly extracted from coupon codes"""
        unique_prefix = f"UT{uuid.uuid4().hex[:3].upper()}"
        response = requests.post(f"{BASE_URL}/api/campaigns", headers=admin_headers, json={
            "name": f"Prefix Test {unique_prefix}",
            "price": 99.0,
            "start_code": f"{unique_prefix}001",
            "end_code": f"{unique_prefix}051"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["prefix"] == unique_prefix
        assert data["total_count"] == 50  # 051 - 001 = 50
    
    def test_campaign_total_calculation(self, admin_headers):
        """Verify total coupons = end_number - start_number"""
        unique_prefix = f"TC{uuid.uuid4().hex[:3].upper()}"
        response = requests.post(f"{BASE_URL}/api/campaigns", headers=admin_headers, json={
            "name": f"Total Calc Test {unique_prefix}",
            "price": 199.0,
            "start_code": f"{unique_prefix}100",
            "end_code": f"{unique_prefix}400"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 300  # 400 - 100 = 300 coupons
    
    def test_campaign_prefix_mismatch_error(self, admin_headers):
        """Prefix mismatch should return 400 error"""
        response = requests.post(f"{BASE_URL}/api/campaigns", headers=admin_headers, json={
            "name": "Prefix Mismatch Test",
            "price": 99.0,
            "start_code": "UT100",
            "end_code": "ABC200"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "prefix" in data["detail"].lower() or "mismatch" in data["detail"].lower()
    
    def test_campaign_end_less_than_start_error(self, admin_headers):
        """End number <= start number should return 400 error"""
        unique_prefix = f"EL{uuid.uuid4().hex[:3].upper()}"
        response = requests.post(f"{BASE_URL}/api/campaigns", headers=admin_headers, json={
            "name": "End Less Than Start Test",
            "price": 99.0,
            "start_code": f"{unique_prefix}200",
            "end_code": f"{unique_prefix}100"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "greater" in data["detail"].lower() or "end" in data["detail"].lower()
    
    def test_campaign_invalid_code_format(self, admin_headers):
        """Invalid code format should return 400 error"""
        response = requests.post(f"{BASE_URL}/api/campaigns", headers=admin_headers, json={
            "name": "Invalid Format Test",
            "price": 99.0,
            "start_code": "123ABC",  # Numbers before letters - invalid
            "end_code": "456DEF"
        })
        
        assert response.status_code == 400
    
    def test_get_campaigns_list(self, admin_headers):
        """GET /api/campaigns returns list of campaigns"""
        response = requests.get(f"{BASE_URL}/api/campaigns", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            campaign = data[0]
            assert "id" in campaign
            assert "name" in campaign
            assert "price" in campaign
            assert "prefix" in campaign
            assert "total_count" in campaign
            assert "sold_count" in campaign
            assert "available_count" in campaign
            assert "status" in campaign


# ========== Expense Approval System ==========
class TestExpenseApprovalSystem:
    """Test expense approval/rejection workflow"""
    
    @pytest.fixture
    def test_expense(self, worker_headers, worker_id):
        """Create a test expense for approval testing"""
        response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Travel",
            "amount": 50.0,  # Under 100, no bill required
            "description": f"Test expense for approval {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def test_submit_expense_as_worker(self, worker_headers):
        """Worker can submit expense claim"""
        response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Food",
            "amount": 75.0,
            "description": f"Test food expense {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["type"] == "Food"
        assert data["amount"] == 75.0
    
    def test_approve_expense_updates_ledger(self, admin_headers, worker_headers, worker_id):
        """Approving expense should add to worker's ledger"""
        # First create an expense
        create_response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Equipment",
            "amount": 80.0,
            "description": f"Test equipment expense {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test expense")
        
        expense_id = create_response.json()["id"]
        
        # Get ledger before approval
        ledger_before = requests.get(f"{BASE_URL}/api/workers/{worker_id}/ledger", headers=admin_headers)
        expenses_before = ledger_before.json().get("total_expenses", 0) if ledger_before.status_code == 200 else 0
        
        # Approve the expense
        approve_response = requests.patch(
            f"{BASE_URL}/api/expenses/{expense_id}/approve",
            headers=admin_headers,
            json={"approved": True}
        )
        
        assert approve_response.status_code == 200
        
        # Verify expense status changed
        expenses_response = requests.get(f"{BASE_URL}/api/expenses?worker_id={worker_id}", headers=admin_headers)
        if expenses_response.status_code == 200:
            expenses = expenses_response.json()
            approved_expense = next((e for e in expenses if e["id"] == expense_id), None)
            if approved_expense:
                assert approved_expense["status"] == "APPROVED"
    
    def test_reject_expense_with_reason(self, admin_headers, worker_headers):
        """Rejecting expense should store rejection reason"""
        # Create an expense
        create_response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Communication",
            "amount": 60.0,
            "description": f"Test comm expense {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test expense")
        
        expense_id = create_response.json()["id"]
        rejection_reason = "Invalid receipt - please resubmit with proper documentation"
        
        # Reject the expense
        reject_response = requests.patch(
            f"{BASE_URL}/api/expenses/{expense_id}/approve",
            headers=admin_headers,
            json={"approved": False, "rejection_reason": rejection_reason}
        )
        
        assert reject_response.status_code == 200
        
        # Verify expense status and rejection reason
        expenses_response = requests.get(f"{BASE_URL}/api/expenses", headers=worker_headers)
        if expenses_response.status_code == 200:
            expenses = expenses_response.json()
            rejected_expense = next((e for e in expenses if e["id"] == expense_id), None)
            if rejected_expense:
                assert rejected_expense["status"] == "REJECTED"
                assert rejected_expense["rejection_reason"] == rejection_reason
    
    def test_rejected_expense_does_not_affect_ledger(self, admin_headers, worker_headers, worker_id):
        """Rejected expense should NOT deduct from net_payable"""
        # Get ledger before
        ledger_before = requests.get(f"{BASE_URL}/api/workers/{worker_id}/ledger", headers=admin_headers)
        expenses_before = ledger_before.json().get("total_expenses", 0) if ledger_before.status_code == 200 else 0
        
        # Create and reject an expense
        create_response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Other",
            "amount": 45.0,
            "description": f"Test reject expense {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test expense")
        
        expense_id = create_response.json()["id"]
        
        # Reject it
        requests.patch(
            f"{BASE_URL}/api/expenses/{expense_id}/approve",
            headers=admin_headers,
            json={"approved": False, "rejection_reason": "Test rejection"}
        )
        
        # Get ledger after
        ledger_after = requests.get(f"{BASE_URL}/api/workers/{worker_id}/ledger", headers=admin_headers)
        expenses_after = ledger_after.json().get("total_expenses", 0) if ledger_after.status_code == 200 else 0
        
        # Expenses should not have increased
        assert expenses_after == expenses_before, "Rejected expense should not affect ledger"
    
    def test_expense_requires_bill_over_100(self, worker_headers):
        """Expense over ₹100 requires bill photo"""
        response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Equipment",
            "amount": 150.0,  # Over 100
            "description": "Test expensive item without bill",
            "latitude": 19.0760,
            "longitude": 72.8777
            # No bill_photo_url or image_base64
        })
        
        assert response.status_code == 400
        assert "bill" in response.json()["detail"].lower() or "photo" in response.json()["detail"].lower()
    
    def test_cannot_approve_already_approved(self, admin_headers, worker_headers):
        """Cannot approve an already approved expense"""
        # Create and approve an expense
        create_response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Travel",
            "amount": 30.0,
            "description": f"Test double approve {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test expense")
        
        expense_id = create_response.json()["id"]
        
        # First approval
        requests.patch(
            f"{BASE_URL}/api/expenses/{expense_id}/approve",
            headers=admin_headers,
            json={"approved": True}
        )
        
        # Try to approve again
        second_response = requests.patch(
            f"{BASE_URL}/api/expenses/{expense_id}/approve",
            headers=admin_headers,
            json={"approved": True}
        )
        
        assert second_response.status_code == 400
        assert "pending" in second_response.json()["detail"].lower()


# ========== Branch Management ==========
class TestBranchManagement:
    """Test branch delete/deactivate/activate functionality"""
    
    def test_create_branch(self, admin_headers):
        """Admin can create a new branch"""
        unique_name = f"Test Branch {uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/branches", headers=admin_headers, json={
            "name": unique_name,
            "address": "123 Test Street, Test City",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "contact_phone": "+91 9876543210"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == unique_name
        assert data["is_active"] == True
        return data["id"]
    
    def test_delete_branch_without_dependencies(self, admin_headers):
        """Branch without dependencies can be permanently deleted"""
        # Create a new branch
        unique_name = f"Delete Test Branch {uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/branches", headers=admin_headers, json={
            "name": unique_name,
            "address": "456 Delete Street",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        assert create_response.status_code == 200
        branch_id = create_response.json()["id"]
        
        # Delete the branch
        delete_response = requests.delete(f"{BASE_URL}/api/branches/{branch_id}", headers=admin_headers)
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["action"] == "DELETED"
        assert "deleted" in data["message"].lower()
    
    def test_activate_deactivated_branch(self, admin_headers):
        """Can re-activate a deactivated branch"""
        # Create a branch
        unique_name = f"Activate Test Branch {uuid.uuid4().hex[:6]}"
        create_response = requests.post(f"{BASE_URL}/api/branches", headers=admin_headers, json={
            "name": unique_name,
            "address": "789 Activate Street",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        assert create_response.status_code == 200
        branch_id = create_response.json()["id"]
        
        # Activate the branch (even if already active, should work)
        activate_response = requests.patch(
            f"{BASE_URL}/api/branches/{branch_id}/activate",
            headers=admin_headers
        )
        
        assert activate_response.status_code == 200
        assert "activated" in activate_response.json()["message"].lower()
        
        # Verify branch is active
        branches_response = requests.get(f"{BASE_URL}/api/branches", headers=admin_headers)
        if branches_response.status_code == 200:
            branches = branches_response.json()
            branch = next((b for b in branches if b["id"] == branch_id), None)
            if branch:
                assert branch["is_active"] == True
    
    def test_get_branches_list(self, admin_headers):
        """GET /api/branches returns list of branches"""
        response = requests.get(f"{BASE_URL}/api/branches", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            branch = data[0]
            assert "id" in branch
            assert "name" in branch
            assert "address" in branch
            assert "is_active" in branch
    
    def test_delete_nonexistent_branch_returns_404(self, admin_headers):
        """Deleting non-existent branch returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/branches/nonexistent-branch-id-12345",
            headers=admin_headers
        )
        
        assert response.status_code == 404


# ========== Worker Expense Status View ==========
class TestWorkerExpenseStatusView:
    """Test worker can see expense status and rejection reason"""
    
    def test_worker_sees_expense_status(self, worker_headers):
        """Worker can see status of their expenses"""
        response = requests.get(f"{BASE_URL}/api/expenses", headers=worker_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for expense in data:
            assert "status" in expense
            assert expense["status"] in ["PENDING", "APPROVED", "REJECTED"]
    
    def test_worker_sees_rejection_reason(self, worker_headers, admin_headers):
        """Worker can see rejection reason for rejected expenses"""
        # Create an expense
        create_response = requests.post(f"{BASE_URL}/api/expenses", headers=worker_headers, json={
            "type": "Travel",
            "amount": 55.0,
            "description": f"Test rejection view {uuid.uuid4().hex[:6]}",
            "latitude": 19.0760,
            "longitude": 72.8777
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test expense")
        
        expense_id = create_response.json()["id"]
        rejection_reason = "Missing receipt details"
        
        # Reject it
        requests.patch(
            f"{BASE_URL}/api/expenses/{expense_id}/approve",
            headers=admin_headers,
            json={"approved": False, "rejection_reason": rejection_reason}
        )
        
        # Worker views their expenses
        expenses_response = requests.get(f"{BASE_URL}/api/expenses", headers=worker_headers)
        
        assert expenses_response.status_code == 200
        expenses = expenses_response.json()
        
        rejected_expense = next((e for e in expenses if e["id"] == expense_id), None)
        assert rejected_expense is not None
        assert rejected_expense["status"] == "REJECTED"
        assert rejected_expense["rejection_reason"] == rejection_reason


# ========== Admin Ledger View with Expenses ==========
class TestAdminLedgerExpenseView:
    """Test admin can view worker expenses from ledger"""
    
    def test_admin_can_view_all_ledgers(self, admin_headers):
        """Admin can view all worker ledgers"""
        response = requests.get(f"{BASE_URL}/api/ledgers/all", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            ledger = data[0]
            assert "worker_id" in ledger
            assert "worker_name" in ledger
            assert "total_revenue" in ledger
            assert "total_expenses" in ledger
            assert "total_advances" in ledger
            assert "net_payable" in ledger
    
    def test_admin_can_view_worker_expenses(self, admin_headers, worker_id):
        """Admin can view specific worker's expenses"""
        response = requests.get(f"{BASE_URL}/api/expenses?worker_id={worker_id}", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        for expense in data:
            assert expense["worker_id"] == worker_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
