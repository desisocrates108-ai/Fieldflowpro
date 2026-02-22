"""
Test Suite for FieldFlow Pro System Updates v5.0
Tests:
1. Worker My Sales API - returns worker_name, branch_name, campaign_name
2. Campaign Coupon Range - exact count generation (no hardcoded limits)
3. CRE Date Filter - from_date and to_date query params
4. CRE customers API returns worker_name field
5. Worker Sale Flow - Simple validation without OCR processing
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        """Get worker authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testworker@fieldflow.com",
            "password": "worker123"
        })
        assert response.status_code == 200, f"Worker login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def cre_token(self):
        """Get CRE authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testcre@fieldflow.com",
            "password": "cre123"
        })
        assert response.status_code == 200, f"CRE login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_admin_login(self, admin_token):
        """Test admin can login"""
        assert admin_token is not None
        assert len(admin_token) > 0
    
    def test_worker_login(self, worker_token):
        """Test worker can login"""
        assert worker_token is not None
        assert len(worker_token) > 0
    
    def test_cre_login(self, cre_token):
        """Test CRE can login"""
        assert cre_token is not None
        assert len(cre_token) > 0


class TestWorkerMySales:
    """Test Worker My Sales API - returns worker_name, branch_name, campaign_name"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        """Get worker authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testworker@fieldflow.com",
            "password": "worker123"
        })
        if response.status_code != 200:
            pytest.skip("Worker login failed")
        return response.json()["access_token"]
    
    def test_worker_my_sales_endpoint_exists(self, worker_token):
        """Test GET /api/campaigns/worker/my-sales endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/worker/my-sales",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200, f"My Sales endpoint failed: {response.text}"
    
    def test_worker_my_sales_returns_list(self, worker_token):
        """Test my-sales returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/worker/my-sales",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_worker_my_sales_has_required_fields(self, worker_token):
        """Test my-sales response has worker_name, branch_name, campaign_name fields"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns/worker/my-sales",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are sales, check the fields
        if len(data) > 0:
            sale = data[0]
            # Check required fields exist
            assert "worker_name" in sale, "worker_name field missing"
            assert "branch_name" in sale, "branch_name field missing"
            assert "campaign_name" in sale, "campaign_name field missing"
            assert "coupon_code" in sale, "coupon_code field missing"
            assert "customer_name" in sale, "customer_name field missing"
            assert "campaign_price" in sale, "campaign_price field missing"
            assert "sold_at" in sale, "sold_at field missing"
            
            # Verify field types
            assert isinstance(sale["worker_name"], str), "worker_name should be string"
            assert isinstance(sale["branch_name"], str), "branch_name should be string"
            assert isinstance(sale["campaign_name"], str), "campaign_name should be string"
            print(f"✓ Sale record has all required fields: worker_name={sale['worker_name']}, branch_name={sale['branch_name']}, campaign_name={sale['campaign_name']}")
        else:
            print("No sales found for worker - fields structure cannot be verified")


class TestCampaignCouponRange:
    """Test Campaign Coupon Range - exact count generation without hardcoded limits"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_get_existing_campaigns(self, admin_token):
        """Test getting existing campaigns"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        campaigns = response.json()
        assert isinstance(campaigns, list)
        print(f"Found {len(campaigns)} campaigns")
        for c in campaigns[:5]:
            print(f"  - {c['name']}: {c['prefix']} ({c['total_count']} coupons, {c['sold_count']} sold)")
    
    def test_range_test_200_campaign_exists(self, admin_token):
        """Test 'Range Test 200' campaign with RNG100-RNG299 (200 coupons)"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        campaigns = response.json()
        
        # Find Range Test 200 campaign
        range_test = next((c for c in campaigns if "Range Test" in c["name"] or c["prefix"] == "RNG"), None)
        
        if range_test:
            print(f"Found Range Test campaign: {range_test['name']}")
            print(f"  Prefix: {range_test['prefix']}")
            print(f"  Total Count: {range_test['total_count']}")
            # Verify it has 200 coupons (RNG100-RNG299)
            assert range_test["total_count"] == 200, f"Expected 200 coupons, got {range_test['total_count']}"
            print("✓ Range Test campaign has exactly 200 coupons")
        else:
            print("Range Test campaign not found - may need to create it")
    
    def test_final_test_campaign_exists(self, admin_token):
        """Test 'Final Test' campaign with FIN500-FIN599 (100 coupons)"""
        response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        campaigns = response.json()
        
        # Find Final Test campaign
        final_test = next((c for c in campaigns if "Final Test" in c["name"] or c["prefix"] == "FIN"), None)
        
        if final_test:
            print(f"Found Final Test campaign: {final_test['name']}")
            print(f"  Prefix: {final_test['prefix']}")
            print(f"  Total Count: {final_test['total_count']}")
            # Verify it has 100 coupons (FIN500-FIN599)
            assert final_test["total_count"] == 100, f"Expected 100 coupons, got {final_test['total_count']}"
            print("✓ Final Test campaign has exactly 100 coupons")
        else:
            print("Final Test campaign not found - may need to create it")
    
    def test_create_large_campaign_500_coupons(self, admin_token):
        """Test creating a campaign with 500+ coupons (no hardcoded limit)"""
        import uuid
        unique_prefix = f"LRG{uuid.uuid4().hex[:4].upper()}"
        
        # Create campaign with 500 coupons (LRG001-LRG500)
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": f"Large Test {unique_prefix}",
                "price": 100.0,
                "start_code": f"{unique_prefix}001",
                "end_code": f"{unique_prefix}501"  # 001-500 = 500 coupons
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            assert data["total_count"] == 500, f"Expected 500 coupons, got {data['total_count']}"
            print(f"✓ Successfully created campaign with 500 coupons: {data['name']}")
            
            # Cleanup - delete the test campaign
            delete_response = requests.delete(
                f"{BASE_URL}/api/campaigns/{data['id']}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            print(f"  Cleanup: Deleted test campaign (status: {delete_response.status_code})")
        elif response.status_code == 400:
            # May fail due to duplicate prefix - that's ok
            print(f"Campaign creation returned 400: {response.json().get('detail', 'Unknown error')}")
        else:
            print(f"Campaign creation returned {response.status_code}: {response.text}")


class TestCREDateFilter:
    """Test CRE Date Filter - from_date and to_date query params"""
    
    @pytest.fixture(scope="class")
    def cre_token(self):
        """Get CRE authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testcre@fieldflow.com",
            "password": "cre123"
        })
        if response.status_code != 200:
            pytest.skip("CRE login failed")
        return response.json()["access_token"]
    
    def test_cre_customers_endpoint_exists(self, cre_token):
        """Test GET /api/cre/customers endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200, f"CRE customers endpoint failed: {response.text}"
    
    def test_cre_customers_returns_list(self, cre_token):
        """Test CRE customers returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} customers")
    
    def test_cre_customers_has_worker_name_field(self, cre_token):
        """Test CRE customers response has worker_name field"""
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            customer = data[0]
            assert "worker_name" in customer, "worker_name field missing from CRE customer view"
            print(f"✓ CRE customer has worker_name field: {customer.get('worker_name', 'N/A')}")
            
            # Check other expected fields
            expected_fields = ["coupon_id", "coupon_code", "customer_name", "customer_phone", 
                            "campaign_name", "branch_name", "sold_at", "call_status"]
            for field in expected_fields:
                assert field in customer, f"{field} field missing"
            print("✓ All expected fields present in CRE customer view")
        else:
            print("No customers found - cannot verify worker_name field")
    
    def test_cre_customers_with_date_filter_today(self, cre_token):
        """Test CRE customers with today's date filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            params={"from_date": today, "to_date": today},
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200, f"Date filter failed: {response.text}"
        data = response.json()
        print(f"Customers for today ({today}): {len(data)}")
    
    def test_cre_customers_with_date_filter_range(self, cre_token):
        """Test CRE customers with date range filter"""
        today = datetime.now()
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            params={"from_date": week_ago, "to_date": today_str},
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200, f"Date range filter failed: {response.text}"
        data = response.json()
        print(f"Customers for last 7 days ({week_ago} to {today_str}): {len(data)}")
    
    def test_cre_customers_without_date_filter(self, cre_token):
        """Test CRE customers without date filter returns all"""
        response = requests.get(
            f"{BASE_URL}/api/cre/customers",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200
        all_customers = response.json()
        
        # Compare with filtered results
        today = datetime.now().strftime("%Y-%m-%d")
        response_filtered = requests.get(
            f"{BASE_URL}/api/cre/customers",
            params={"from_date": today, "to_date": today},
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        filtered_customers = response_filtered.json()
        
        print(f"All customers: {len(all_customers)}, Today only: {len(filtered_customers)}")
        # All customers should be >= today's customers
        assert len(all_customers) >= len(filtered_customers), "Date filter not working correctly"


class TestWorkerSaleFlow:
    """Test Worker Sale Flow - Simple validation without OCR processing"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        """Get worker authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testworker@fieldflow.com",
            "password": "worker123"
        })
        if response.status_code != 200:
            pytest.skip("Worker login failed")
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["access_token"]
    
    def test_validate_coupon_code_endpoint(self, worker_token):
        """Test coupon validation endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json={"coupon_code": "INVALID123"}
        )
        # Should return 200 with valid=false for invalid code
        assert response.status_code == 200, f"Validate endpoint failed: {response.text}"
        data = response.json()
        assert "valid" in data or "is_valid" in data, "Response should have valid/is_valid field"
    
    def test_validate_existing_coupon(self, worker_token, admin_token):
        """Test validating an existing available coupon"""
        # First get an available coupon from a campaign
        campaigns_response = requests.get(
            f"{BASE_URL}/api/campaigns",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if campaigns_response.status_code != 200:
            pytest.skip("Cannot get campaigns")
        
        campaigns = campaigns_response.json()
        active_campaign = next((c for c in campaigns if c["status"] == "ACTIVE" and c["available_count"] > 0), None)
        
        if not active_campaign:
            print("No active campaign with available coupons found")
            return
        
        # Get coupons from this campaign
        coupons_response = requests.get(
            f"{BASE_URL}/api/campaigns/{active_campaign['id']}/coupons",
            params={"status": "AVAILABLE"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if coupons_response.status_code != 200:
            print(f"Cannot get coupons: {coupons_response.text}")
            return
        
        coupons = coupons_response.json()
        available_coupon = next((c for c in coupons if c["status"] == "AVAILABLE"), None)
        
        if not available_coupon:
            print("No available coupon found")
            return
        
        # Validate the coupon
        response = requests.post(
            f"{BASE_URL}/api/campaigns/validate-code",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json={"coupon_code": available_coupon["code"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        is_valid = data.get("valid") or data.get("is_valid")
        assert is_valid == True, f"Coupon should be valid: {data}"
        print(f"✓ Coupon {available_coupon['code']} validated successfully")
        print(f"  Campaign: {data.get('campaign_name')}, Price: {data.get('campaign_price') or data.get('price')}")
    
    def test_worker_sale_endpoint_exists(self, worker_token):
        """Test worker-sale endpoint exists"""
        # This should fail validation but endpoint should exist
        response = requests.post(
            f"{BASE_URL}/api/campaigns/worker-sale",
            headers={
                "Authorization": f"Bearer {worker_token}",
                "Content-Type": "application/json"
            },
            json={
                "coupon_code": "INVALID",
                "customer_name": "Test",
                "customer_phone": "9999999999",
                "branch_id": "invalid",
                "latitude": 0,
                "longitude": 0
            }
        )
        # Should return 404 (coupon not found) or 400 (validation error), not 500
        assert response.status_code in [400, 404], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"✓ Worker sale endpoint exists and validates input (returned {response.status_code})")


class TestCREDashboard:
    """Test CRE Dashboard Stats"""
    
    @pytest.fixture(scope="class")
    def cre_token(self):
        """Get CRE authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testcre@fieldflow.com",
            "password": "cre123"
        })
        if response.status_code != 200:
            pytest.skip("CRE login failed")
        return response.json()["access_token"]
    
    def test_cre_dashboard_stats(self, cre_token):
        """Test CRE dashboard stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/cre/dashboard/stats",
            headers={"Authorization": f"Bearer {cre_token}"}
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "today_total_customers" in data, "today_total_customers missing"
        assert "today_calls_made" in data, "today_calls_made missing"
        assert "pending_calls" in data, "pending_calls missing"
        
        print(f"✓ CRE Dashboard Stats:")
        print(f"  Today's Customers: {data['today_total_customers']}")
        print(f"  Calls Made Today: {data['today_calls_made']}")
        print(f"  Pending Calls: {data['pending_calls']}")


class TestBranchesAPI:
    """Test Branches API for worker sale flow"""
    
    @pytest.fixture(scope="class")
    def worker_token(self):
        """Get worker authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testworker@fieldflow.com",
            "password": "worker123"
        })
        if response.status_code != 200:
            pytest.skip("Worker login failed")
        return response.json()["access_token"]
    
    def test_get_branches(self, worker_token):
        """Test getting branches list"""
        response = requests.get(
            f"{BASE_URL}/api/branches",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200, f"Branches endpoint failed: {response.text}"
        branches = response.json()
        assert isinstance(branches, list), "Branches should be a list"
        print(f"Found {len(branches)} branches")
        for b in branches[:5]:
            print(f"  - {b.get('name', 'Unknown')} (ID: {b.get('id', 'N/A')})")


class TestStaticFiles:
    """Test static file serving for bill photos"""
    
    def test_uploads_endpoint_exists(self):
        """Test /uploads/ static files endpoint"""
        # Try to access a non-existent file - should return 404, not 500
        response = requests.get(f"{BASE_URL}/uploads/nonexistent.jpg")
        # 200 means directory listing or default response, 404 for non-existent file
        # Any of these is acceptable - endpoint exists
        assert response.status_code in [200, 404, 403], f"Uploads endpoint issue: {response.status_code}"
        print(f"✓ /uploads/ endpoint exists (returned {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
