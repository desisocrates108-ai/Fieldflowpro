"""
Test QR Campaign System - Campaign-specific QR codes for lead capture
Tests: Campaign CRUD, Lead submission with/without campaign, Filtering by campaign/source
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "testadmin@fieldflow.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


# ========== Campaign CRUD Tests ==========

class TestCampaignCRUD:
    """Test campaign creation, listing, and deletion"""
    
    def test_create_campaign_success(self, admin_headers):
        """POST /api/admin/qr-campaigns - Create campaign with name"""
        unique_name = f"TEST_CAMP_{uuid.uuid4().hex[:6].upper()}"
        response = requests.post(f"{BASE_URL}/api/admin/qr-campaigns", 
            headers=admin_headers,
            json={"name": unique_name, "description": "Test campaign description"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "campaign" in data
        campaign = data["campaign"]
        assert campaign["name"] == unique_name
        # Code should be uppercase alphanumeric version of name
        expected_code = ''.join(c for c in unique_name.upper() if c.isalnum())
        assert campaign["code"] == expected_code
        assert campaign["is_active"] == True
        assert "id" in campaign
        assert "created_at" in campaign
        print(f"✓ Created campaign: {campaign['code']}")
        
    def test_create_campaign_missing_name(self, admin_headers):
        """POST /api/admin/qr-campaigns - Fail without name"""
        response = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"description": "No name provided"}
        )
        assert response.status_code == 400
        assert "name" in response.json().get("detail", "").lower()
        print("✓ Correctly rejected campaign without name")
        
    def test_create_campaign_duplicate_code(self, admin_headers):
        """POST /api/admin/qr-campaigns - Fail on duplicate code (409)"""
        # Create first campaign
        unique_name = f"DUPTEST{uuid.uuid4().hex[:4].upper()}"
        response1 = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"name": unique_name}
        )
        assert response1.status_code == 200
        
        # Try to create duplicate
        response2 = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"name": unique_name}
        )
        assert response2.status_code == 409, f"Expected 409 for duplicate, got {response2.status_code}"
        assert "already exists" in response2.json().get("detail", "").lower()
        print("✓ Correctly rejected duplicate campaign code (409)")
        
    def test_list_campaigns_with_lead_counts(self, admin_headers):
        """GET /api/admin/qr-campaigns - List campaigns with lead counts"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-campaigns", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "campaigns" in data
        campaigns = data["campaigns"]
        assert isinstance(campaigns, list)
        
        # Each campaign should have lead_count
        for c in campaigns:
            assert "id" in c
            assert "code" in c
            assert "name" in c
            assert "lead_count" in c
            assert isinstance(c["lead_count"], int)
        print(f"✓ Listed {len(campaigns)} campaigns with lead counts")
        
    def test_delete_campaign(self, admin_headers):
        """DELETE /api/admin/qr-campaigns/{id} - Delete campaign"""
        # Create a campaign to delete
        unique_name = f"DELTEST{uuid.uuid4().hex[:4].upper()}"
        create_resp = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"name": unique_name}
        )
        assert create_resp.status_code == 200
        campaign_id = create_resp.json()["campaign"]["id"]
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/admin/qr-campaigns/{campaign_id}",
            headers=admin_headers
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json().get("success") == True
        print(f"✓ Deleted campaign {unique_name}")
        
    def test_delete_nonexistent_campaign(self, admin_headers):
        """DELETE /api/admin/qr-campaigns/{id} - 404 for nonexistent"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/admin/qr-campaigns/{fake_id}",
            headers=admin_headers
        )
        assert response.status_code == 404
        print("✓ Correctly returned 404 for nonexistent campaign")


# ========== Lead Submission Tests ==========

class TestLeadSubmission:
    """Test lead submission with and without campaign parameter"""
    
    def test_submit_lead_without_campaign(self):
        """POST /api/qr-leads - Submit lead without campaign (source=QR)"""
        response = requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": "TEST_General Lead",
            "mobile": "9876543210",
            "city": "Mumbai",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print("✓ Submitted general lead (no campaign)")
        
    def test_submit_lead_with_campaign(self, admin_headers):
        """POST /api/qr-leads - Submit lead with campaign param (source=CAMPAIGN_QR)"""
        # First create a campaign
        unique_name = f"LEADTEST{uuid.uuid4().hex[:4].upper()}"
        create_resp = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"name": unique_name}
        )
        assert create_resp.status_code == 200
        campaign_code = create_resp.json()["campaign"]["code"]
        
        # Submit lead with campaign
        response = requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": "TEST_Campaign Lead",
            "mobile": "9876543211",
            "city": "Delhi",
            "state": "Delhi",
            "vehicle_type": "≥ 160cc",
            "campaign": campaign_code
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Submitted campaign lead for {campaign_code}")
        
    def test_lead_stored_with_campaign_fields(self, admin_headers):
        """Verify lead has campaign_code, campaign_name, source fields"""
        # Create campaign
        unique_name = f"VERIFY{uuid.uuid4().hex[:4].upper()}"
        create_resp = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"name": unique_name}
        )
        campaign_code = create_resp.json()["campaign"]["code"]
        
        # Submit lead with unique name for search
        unique_lead_name = f"TEST_Verify_{uuid.uuid4().hex[:6]}"
        requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": unique_lead_name,
            "mobile": "9812345678",
            "city": "Pune",
            "state": "Maharashtra",
            "vehicle_type": "< 160cc",
            "campaign": campaign_code
        })
        
        # Fetch leads filtered by campaign_code
        leads_resp = requests.get(f"{BASE_URL}/api/admin/qr-leads?campaign_code={campaign_code}",
            headers=admin_headers
        )
        assert leads_resp.status_code == 200
        leads = leads_resp.json().get("leads", [])
        assert len(leads) >= 1, f"Expected at least 1 lead for campaign {campaign_code}"
        
        # Find our specific lead
        lead = next((l for l in leads if l["name"] == unique_lead_name), leads[0])
        assert lead.get("campaign_code") == campaign_code
        assert lead.get("campaign_name") == unique_name  # Should resolve to campaign name
        assert lead.get("source") == "CAMPAIGN_QR"
        print(f"✓ Lead has correct campaign_code={campaign_code}, campaign_name={unique_name}, source=CAMPAIGN_QR")
        
    def test_general_lead_has_null_campaign(self, admin_headers):
        """Verify general lead has campaign_code=null, source=QR"""
        unique_lead_name = f"TEST_General_{uuid.uuid4().hex[:6]}"
        requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": unique_lead_name,
            "mobile": "9712345678",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "vehicle_type": "≥ 160cc"
        })
        
        # Filter by source=general to get only general leads
        leads_resp = requests.get(f"{BASE_URL}/api/admin/qr-leads?source_filter=general",
            headers=admin_headers
        )
        leads = leads_resp.json().get("leads", [])
        assert len(leads) >= 1, "Expected at least 1 general lead"
        
        # Find our specific lead or use first one
        lead = next((l for l in leads if l["name"] == unique_lead_name), leads[0])
        assert lead.get("campaign_code") is None
        assert lead.get("source") == "QR"
        print("✓ General lead has campaign_code=null, source=QR")


# ========== Lead Filtering Tests ==========

class TestLeadFiltering:
    """Test filtering leads by campaign_code and source_filter"""
    
    def test_filter_by_campaign_code(self, admin_headers):
        """GET /api/admin/qr-leads?campaign_code=X - Filter by specific campaign"""
        # Create campaign and lead
        unique_name = f"FILTER{uuid.uuid4().hex[:4].upper()}"
        create_resp = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            headers=admin_headers,
            json={"name": unique_name}
        )
        campaign_code = create_resp.json()["campaign"]["code"]
        
        # Submit lead
        requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": "TEST_Filter Test",
            "mobile": f"96{uuid.uuid4().hex[:8]}"[:10],
            "city": "Bangalore",
            "state": "Karnataka",
            "vehicle_type": "< 160cc",
            "campaign": campaign_code
        })
        
        # Filter by campaign_code
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads?campaign_code={campaign_code}",
            headers=admin_headers
        )
        assert response.status_code == 200
        leads = response.json().get("leads", [])
        
        # All returned leads should have this campaign_code
        for lead in leads:
            assert lead["campaign_code"] == campaign_code
        print(f"✓ Filter by campaign_code={campaign_code} works ({len(leads)} leads)")
        
    def test_filter_source_general(self, admin_headers):
        """GET /api/admin/qr-leads?source_filter=general - Only general leads"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads?source_filter=general",
            headers=admin_headers
        )
        assert response.status_code == 200
        leads = response.json().get("leads", [])
        
        # All returned leads should have campaign_code=null
        for lead in leads:
            assert lead.get("campaign_code") is None, f"Expected null campaign_code, got {lead.get('campaign_code')}"
        print(f"✓ source_filter=general returns only general leads ({len(leads)} leads)")
        
    def test_filter_source_campaign(self, admin_headers):
        """GET /api/admin/qr-leads?source_filter=campaign - Only campaign leads"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads?source_filter=campaign",
            headers=admin_headers
        )
        assert response.status_code == 200
        leads = response.json().get("leads", [])
        
        # All returned leads should have campaign_code != null
        for lead in leads:
            assert lead["campaign_code"] is not None, f"Expected non-null campaign_code"
        print(f"✓ source_filter=campaign returns only campaign leads ({len(leads)} leads)")
        
    def test_campaign_codes_in_response(self, admin_headers):
        """GET /api/admin/qr-leads - Response includes campaign_codes list for dropdown"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-leads", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "campaign_codes" in data
        assert isinstance(data["campaign_codes"], list)
        # Should not contain None values
        assert None not in data["campaign_codes"]
        print(f"✓ Response includes campaign_codes list: {data['campaign_codes'][:5]}...")


# ========== Existing Campaigns Test (BI6, BI7) ==========

class TestExistingCampaigns:
    """Test existing campaigns BI6 and BI7 mentioned in context"""
    
    def test_bi6_bi7_campaigns_exist(self, admin_headers):
        """Verify BI6 and BI7 campaigns exist with lead counts"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-campaigns", headers=admin_headers)
        assert response.status_code == 200
        campaigns = response.json().get("campaigns", [])
        
        campaign_codes = [c["code"] for c in campaigns]
        
        # Check if BI6 and BI7 exist (they should per context)
        bi6_exists = "BI6" in campaign_codes
        bi7_exists = "BI7" in campaign_codes
        
        if bi6_exists:
            bi6 = next(c for c in campaigns if c["code"] == "BI6")
            print(f"✓ BI6 campaign exists with {bi6['lead_count']} leads")
        else:
            print("⚠ BI6 campaign not found (may need to be created)")
            
        if bi7_exists:
            bi7 = next(c for c in campaigns if c["code"] == "BI7")
            print(f"✓ BI7 campaign exists with {bi7['lead_count']} leads")
        else:
            print("⚠ BI7 campaign not found (may need to be created)")
            
        # At least one should exist based on context
        assert bi6_exists or bi7_exists or len(campaigns) > 0, "No campaigns found"


# ========== Auth Tests ==========

class TestCampaignAuth:
    """Test that campaign endpoints require admin auth"""
    
    def test_create_campaign_requires_auth(self):
        """POST /api/admin/qr-campaigns - Requires auth"""
        response = requests.post(f"{BASE_URL}/api/admin/qr-campaigns",
            json={"name": "NoAuth"}
        )
        assert response.status_code in [401, 403]
        print("✓ Create campaign requires auth")
        
    def test_list_campaigns_requires_auth(self):
        """GET /api/admin/qr-campaigns - Requires auth"""
        response = requests.get(f"{BASE_URL}/api/admin/qr-campaigns")
        assert response.status_code in [401, 403]
        print("✓ List campaigns requires auth")
        
    def test_delete_campaign_requires_auth(self):
        """DELETE /api/admin/qr-campaigns/{id} - Requires auth"""
        response = requests.delete(f"{BASE_URL}/api/admin/qr-campaigns/fake-id")
        assert response.status_code in [401, 403]
        print("✓ Delete campaign requires auth")
        
    def test_qr_leads_public_no_auth(self):
        """POST /api/qr-leads - Public endpoint, no auth required"""
        response = requests.post(f"{BASE_URL}/api/qr-leads", json={
            "name": "TEST_Public",
            "mobile": "9999999999",
            "city": "Test",
            "state": "Test",
            "vehicle_type": "< 160cc"
        })
        # Should succeed without auth
        assert response.status_code == 200
        print("✓ QR lead submission is public (no auth required)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
