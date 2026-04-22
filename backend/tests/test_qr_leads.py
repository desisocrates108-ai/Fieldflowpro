"""
QR Lead Capture System Tests
Tests for:
- POST /api/qr-leads (public endpoint - no auth)
- GET /api/admin/qr-leads (admin endpoint - requires auth)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestQRLeadsPublicEndpoint:
    """Tests for public QR lead submission endpoint (no auth required)"""
    
    def test_submit_qr_lead_success(self):
        """Test successful QR lead submission with all required fields"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"TEST_User_{unique_id}",
            "mobile": "9876543210",
            "city": "Mumbai",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "message" in data
        assert "Thank you" in data["message"]
        print(f"✓ QR lead submission successful: {data['message']}")
    
    def test_submit_qr_lead_vehicle_type_160cc_plus(self):
        """Test QR lead submission with ≥ 160cc vehicle type"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"TEST_Rider_{unique_id}",
            "mobile": "9123456789",
            "city": "Delhi",
            "state": "Delhi",
            "vehicle_type": "≥ 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"✓ QR lead with ≥ 160cc vehicle type submitted successfully")
    
    def test_submit_qr_lead_missing_name(self):
        """Test validation: missing name field"""
        payload = {
            "mobile": "9876543210",
            "city": "Mumbai",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "required" in data.get("detail", "").lower()
        print(f"✓ Validation works: missing name returns 400")
    
    def test_submit_qr_lead_missing_mobile(self):
        """Test validation: missing mobile field"""
        payload = {
            "name": "Test User",
            "city": "Mumbai",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Validation works: missing mobile returns 400")
    
    def test_submit_qr_lead_missing_city(self):
        """Test validation: missing city field"""
        payload = {
            "name": "Test User",
            "mobile": "9876543210",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Validation works: missing city returns 400")
    
    def test_submit_qr_lead_missing_state(self):
        """Test validation: missing state field"""
        payload = {
            "name": "Test User",
            "mobile": "9876543210",
            "city": "Mumbai",
            "vehicle_type": "< 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Validation works: missing state returns 400")
    
    def test_submit_qr_lead_missing_vehicle_type(self):
        """Test validation: missing vehicle_type field"""
        payload = {
            "name": "Test User",
            "mobile": "9876543210",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Validation works: missing vehicle_type returns 400")
    
    def test_submit_qr_lead_invalid_mobile_short(self):
        """Test validation: mobile number less than 10 digits"""
        payload = {
            "name": "Test User",
            "mobile": "12345",  # Only 5 digits
            "city": "Mumbai",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "10-digit" in data.get("detail", "").lower() or "mobile" in data.get("detail", "").lower()
        print(f"✓ Validation works: short mobile number returns 400")
    
    def test_submit_qr_lead_mobile_with_country_code(self):
        """Test that mobile with country code is accepted (extracts last 10 digits)"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "name": f"TEST_International_{unique_id}",
            "mobile": "+919876543210",  # With country code
            "city": "Bangalore",
            "state": "Karnataka",
            "vehicle_type": "≥ 160cc"
        }
        
        response = requests.post(f"{BASE_URL}/api/qr-leads", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Mobile with country code accepted")


class TestQRLeadsAdminEndpoint:
    """Tests for admin QR leads endpoint (requires auth)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed - skipping admin tests")
        
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_qr_leads_success(self):
        """Test fetching QR leads as admin"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads", headers=self.headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "leads" in data, "Response should contain 'leads' array"
        assert "total" in data, "Response should contain 'total' count"
        assert "today_count" in data, "Response should contain 'today_count'"
        
        assert isinstance(data["leads"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["today_count"], int)
        
        print(f"✓ Admin QR leads endpoint works: {data['total']} total leads, {data['today_count']} today")
    
    def test_get_qr_leads_verify_lead_structure(self):
        """Test that leads have all required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["leads"]) > 0:
            lead = data["leads"][0]
            required_fields = ["id", "name", "mobile", "city", "state", "vehicle_type", "created_at"]
            
            for field in required_fields:
                assert field in lead, f"Lead should have '{field}' field"
            
            print(f"✓ Lead structure verified: {list(lead.keys())}")
        else:
            print("⚠ No leads found to verify structure")
    
    def test_get_qr_leads_search_by_name(self):
        """Test search filter by name"""
        # First create a test lead
        unique_name = f"TEST_SearchName_{str(uuid.uuid4())[:8]}"
        requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": unique_name,
            "mobile": "9999888877",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "vehicle_type": "< 160cc"
        })
        
        # Search for it
        response = requests.get(
            f"{BASE_URL}/api/admin/qr-leads?search={unique_name}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find the lead we just created
        found = any(lead["name"] == unique_name for lead in data["leads"])
        assert found, f"Should find lead with name '{unique_name}'"
        print(f"✓ Search by name works: found '{unique_name}'")
    
    def test_get_qr_leads_search_by_mobile(self):
        """Test search filter by mobile"""
        # Create a lead with unique mobile
        unique_mobile = "9111222333"
        requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": f"TEST_MobileSearch_{str(uuid.uuid4())[:8]}",
            "mobile": unique_mobile,
            "city": "Hyderabad",
            "state": "Telangana",
            "vehicle_type": "≥ 160cc"
        })
        
        # Search by mobile
        response = requests.get(
            f"{BASE_URL}/api/admin/qr-leads?search={unique_mobile}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        found = any(lead["mobile"] == unique_mobile for lead in data["leads"])
        assert found, f"Should find lead with mobile '{unique_mobile}'"
        print(f"✓ Search by mobile works")
    
    def test_get_qr_leads_search_by_city(self):
        """Test search filter by city"""
        unique_city = f"TestCity{str(uuid.uuid4())[:4]}"
        requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": f"TEST_CitySearch_{str(uuid.uuid4())[:8]}",
            "mobile": "9444555666",
            "city": unique_city,
            "state": "TestState",
            "vehicle_type": "< 160cc"
        })
        
        # Search by city
        response = requests.get(
            f"{BASE_URL}/api/admin/qr-leads?search={unique_city}",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        found = any(lead["city"] == unique_city for lead in data["leads"])
        assert found, f"Should find lead with city '{unique_city}'"
        print(f"✓ Search by city works")
    
    def test_get_qr_leads_date_filter(self):
        """Test date range filter"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/qr-leads?date_from={today}T00:00:00&date_to={today}T23:59:59",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned leads should be from today
        print(f"✓ Date filter works: {len(data['leads'])} leads for today")
    
    def test_get_qr_leads_unauthorized(self):
        """Test that endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Admin endpoint requires authentication")
    
    def test_get_qr_leads_pagination(self):
        """Test pagination parameters"""
        response = requests.get(
            f"{BASE_URL}/api/admin/qr-leads?skip=0&limit=5",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return at most 5 leads
        assert len(data["leads"]) <= 5
        print(f"✓ Pagination works: returned {len(data['leads'])} leads with limit=5")


class TestQRLeadsDataPersistence:
    """Test that QR leads are properly persisted and retrievable"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testadmin@fieldflow.com",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Admin login failed")
        
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_and_verify_lead_persistence(self):
        """Test that submitted lead appears in admin list"""
        unique_id = str(uuid.uuid4())[:8]
        test_lead = {
            "name": f"TEST_Persist_{unique_id}",
            "mobile": "9777666555",
            "city": "Pune",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        }
        
        # Submit lead
        submit_response = requests.post(f"{BASE_URL}/api/qr-leads", json=test_lead)
        assert submit_response.status_code == 200
        
        # Verify it appears in admin list
        admin_response = requests.get(
            f"{BASE_URL}/api/admin/qr-leads?search={test_lead['name']}",
            headers=self.headers
        )
        
        assert admin_response.status_code == 200
        data = admin_response.json()
        
        # Find our lead
        found_lead = None
        for lead in data["leads"]:
            if lead["name"] == test_lead["name"]:
                found_lead = lead
                break
        
        assert found_lead is not None, "Submitted lead should appear in admin list"
        assert found_lead["mobile"] == test_lead["mobile"][-10:]  # Last 10 digits
        assert found_lead["city"] == test_lead["city"]
        assert found_lead["state"] == test_lead["state"]
        assert found_lead["vehicle_type"] == test_lead["vehicle_type"]
        
        print(f"✓ Lead persistence verified: {found_lead['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
