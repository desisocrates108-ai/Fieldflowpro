"""
FieldFlow Pro Elite v4.0 - Phase 1 Intelligence APIs Test Suite
Tests for:
- Real-time Metrics API
- Worker Performance Scoring
- Fraud Detection Engine
- Inactive Workers Panel
- Area Intelligence
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


class TestHealthCheck:
    """Health check and version verification"""
    
    def test_health_check_returns_v4(self):
        """Verify health check shows version 4.0.0"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "4.0.0", f"Expected version 4.0.0, got {data['version']}"


class TestRealtimeMetrics:
    """Real-time Metrics API tests"""
    
    def test_get_realtime_metrics_success(self, admin_headers):
        """GET /api/intelligence/realtime-metrics returns all expected fields"""
        response = requests.get(f"{BASE_URL}/api/intelligence/realtime-metrics", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields exist
        required_fields = [
            "live_sales_today", "live_revenue_today", "active_workers_now",
            "total_punched_in_today", "inactive_worker_alerts", "fraud_alerts_active",
            "pending_expenses", "encashments_today", "last_updated"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["live_sales_today"], int)
        assert isinstance(data["live_revenue_today"], (int, float))
        assert isinstance(data["active_workers_now"], int)
        assert isinstance(data["total_punched_in_today"], int)
        assert isinstance(data["inactive_worker_alerts"], int)
        assert isinstance(data["fraud_alerts_active"], int)
        assert isinstance(data["pending_expenses"], int)
        assert isinstance(data["encashments_today"], int)
    
    def test_realtime_metrics_requires_admin_role(self, worker_headers):
        """Workers cannot access realtime metrics"""
        response = requests.get(f"{BASE_URL}/api/intelligence/realtime-metrics", headers=worker_headers)
        assert response.status_code == 403
    
    def test_realtime_metrics_requires_auth(self):
        """Unauthenticated requests are rejected"""
        response = requests.get(f"{BASE_URL}/api/intelligence/realtime-metrics")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"


class TestWorkerPerformanceScoring:
    """Worker Performance Scoring API tests"""
    
    def test_get_all_worker_scores(self, admin_headers):
        """GET /api/intelligence/worker-scores returns list of workers with scores"""
        response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        if len(data) > 0:
            worker = data[0]
            # Verify score structure
            assert "worker_id" in worker
            assert "worker_name" in worker
            assert "final_score" in worker
            assert "components" in worker
            assert "metrics" in worker
            assert "grade" in worker
            assert "rank" in worker
            
            # Verify score range (0-100)
            assert 0 <= worker["final_score"] <= 100
            
            # Verify grade is valid
            valid_grades = ["A+", "A", "B+", "B", "C", "D", "F"]
            assert worker["grade"] in valid_grades
            
            # Verify components structure
            components = worker["components"]
            assert "conversion_score" in components
            assert "sales_per_day_score" in components
            assert "revenue_score" in components
            assert "attendance_score" in components
            assert "inactivity_score" in components
            
            # Verify metrics structure
            metrics = worker["metrics"]
            assert "total_sales_month" in metrics
            assert "active_days" in metrics
            assert "avg_sales_per_day" in metrics
            assert "total_revenue_month" in metrics
            assert "inactivity_alerts" in metrics
    
    def test_worker_scores_sorted_by_score_descending(self, admin_headers):
        """Worker scores should be sorted by final_score descending"""
        response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 1:
            scores = [w["final_score"] for w in data]
            assert scores == sorted(scores, reverse=True), "Scores not sorted descending"
    
    def test_get_individual_worker_score(self, admin_headers):
        """GET /api/intelligence/worker-scores/{worker_id} returns specific worker score"""
        # First get list to find a worker_id
        list_response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores", headers=admin_headers)
        assert list_response.status_code == 200
        workers = list_response.json()
        
        if len(workers) > 0:
            worker_id = workers[0]["worker_id"]
            response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores/{worker_id}", headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            
            assert data["worker_id"] == worker_id
            assert "final_score" in data
            assert "grade" in data
    
    def test_worker_can_view_own_score(self, worker_headers):
        """Workers can view their own performance score"""
        # Get worker's own ID from /auth/me
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=worker_headers)
        assert me_response.status_code == 200
        worker_id = me_response.json()["id"]
        
        response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores/{worker_id}", headers=worker_headers)
        assert response.status_code == 200
    
    def test_worker_cannot_view_other_worker_score(self, worker_headers, admin_headers):
        """Workers cannot view other workers' scores"""
        # Get a different worker's ID
        list_response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores", headers=admin_headers)
        workers = list_response.json()
        
        # Get current worker's ID
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=worker_headers)
        current_worker_id = me_response.json()["id"]
        
        # Find a different worker
        other_worker = next((w for w in workers if w["worker_id"] != current_worker_id), None)
        
        if other_worker:
            response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores/{other_worker['worker_id']}", headers=worker_headers)
            assert response.status_code == 403
    
    def test_invalid_worker_id_returns_404(self, admin_headers):
        """Invalid worker ID returns 404"""
        response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores/invalid-id-12345", headers=admin_headers)
        assert response.status_code == 404


class TestFraudDetection:
    """Fraud Detection Engine API tests"""
    
    def test_get_fraud_alerts_active(self, admin_headers):
        """GET /api/intelligence/fraud-alerts returns active alerts"""
        response = requests.get(f"{BASE_URL}/api/intelligence/fraud-alerts?status=ACTIVE", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        for alert in data:
            assert alert["status"] == "ACTIVE"
            assert "id" in alert
            assert "alert_type" in alert
            assert "worker_id" in alert
            assert "worker_name" in alert
            assert "severity" in alert
            assert "details" in alert
            assert "created_at" in alert
    
    def test_get_fraud_alerts_resolved(self, admin_headers):
        """GET /api/intelligence/fraud-alerts?status=RESOLVED returns resolved alerts"""
        response = requests.get(f"{BASE_URL}/api/intelligence/fraud-alerts?status=RESOLVED", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        for alert in data:
            assert alert["status"] == "RESOLVED"
    
    def test_fraud_scan_trigger(self, admin_headers):
        """POST /api/intelligence/scan-fraud triggers fraud scan"""
        response = requests.post(f"{BASE_URL}/api/intelligence/scan-fraud", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "alerts_created" in data
        assert isinstance(data["alerts_created"], int)
    
    def test_fraud_alerts_require_admin(self, worker_headers):
        """Workers cannot access fraud alerts"""
        response = requests.get(f"{BASE_URL}/api/intelligence/fraud-alerts", headers=worker_headers)
        assert response.status_code == 403
    
    def test_fraud_scan_requires_admin(self, worker_headers):
        """Workers cannot trigger fraud scan"""
        response = requests.post(f"{BASE_URL}/api/intelligence/scan-fraud", headers=worker_headers)
        assert response.status_code == 403
    
    def test_fraud_alert_severity_values(self, admin_headers):
        """Fraud alerts have valid severity values"""
        response = requests.get(f"{BASE_URL}/api/intelligence/fraud-alerts", headers=admin_headers)
        assert response.status_code == 200
        
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        for alert in response.json():
            assert alert["severity"] in valid_severities


class TestInactiveWorkers:
    """Inactive Workers Panel API tests"""
    
    def test_get_inactive_workers(self, admin_headers):
        """GET /api/intelligence/inactive-workers returns inactive workers panel data"""
        response = requests.get(f"{BASE_URL}/api/intelligence/inactive-workers", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_inactive" in data
        assert "workers" in data
        assert isinstance(data["total_inactive"], int)
        assert isinstance(data["workers"], list)
        
        for worker in data["workers"]:
            assert "alert_id" in worker
            assert "worker_id" in worker
            assert "worker_name" in worker
            assert "punch_in_time" in worker
            assert "hours_inactive" in worker
    
    def test_inactive_workers_requires_admin(self, worker_headers):
        """Workers cannot access inactive workers panel"""
        response = requests.get(f"{BASE_URL}/api/intelligence/inactive-workers", headers=worker_headers)
        assert response.status_code == 403


class TestAreaIntelligence:
    """Area Intelligence API tests"""
    
    def test_get_area_intelligence(self, admin_headers):
        """GET /api/intelligence/area-intelligence returns geographic sales data"""
        response = requests.get(f"{BASE_URL}/api/intelligence/area-intelligence", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "sales_by_city" in data
        assert "sales_by_state" in data
        assert "campaign_by_geography" in data
        assert "top_areas" in data
        assert "generated_at" in data
        
        # Verify sales_by_city structure
        for city_data in data["sales_by_city"]:
            assert "city" in city_data
            assert "sales" in city_data
            assert "revenue" in city_data
        
        # Verify sales_by_state structure
        for state_data in data["sales_by_state"]:
            assert "state" in state_data
            assert "sales" in state_data
            assert "revenue" in state_data
        
        # Verify campaign_by_geography structure
        for geo_data in data["campaign_by_geography"]:
            assert "campaign_id" in geo_data
            assert "campaign_name" in geo_data
            assert "state" in geo_data
            assert "sales" in geo_data
            assert "revenue" in geo_data
    
    def test_area_intelligence_requires_admin(self, worker_headers):
        """Workers cannot access area intelligence"""
        response = requests.get(f"{BASE_URL}/api/intelligence/area-intelligence", headers=worker_headers)
        assert response.status_code == 403


class TestFraudAlertActions:
    """Fraud Alert Resolve/Dismiss actions tests"""
    
    def test_resolve_nonexistent_alert_returns_404(self, admin_headers):
        """Resolving non-existent alert returns 404"""
        response = requests.patch(
            f"{BASE_URL}/api/intelligence/fraud-alerts/nonexistent-id/resolve",
            headers=admin_headers
        )
        assert response.status_code == 404
    
    def test_dismiss_nonexistent_alert_returns_404(self, admin_headers):
        """Dismissing non-existent alert returns 404"""
        response = requests.patch(
            f"{BASE_URL}/api/intelligence/fraud-alerts/nonexistent-id/dismiss",
            headers=admin_headers
        )
        assert response.status_code == 404


class TestGradeCalculation:
    """Test grade calculation logic"""
    
    def test_grade_boundaries(self, admin_headers):
        """Verify grade boundaries are correct"""
        response = requests.get(f"{BASE_URL}/api/intelligence/worker-scores", headers=admin_headers)
        assert response.status_code == 200
        
        for worker in response.json():
            score = worker["final_score"]
            grade = worker["grade"]
            
            if score >= 90:
                assert grade == "A+", f"Score {score} should be A+, got {grade}"
            elif score >= 80:
                assert grade == "A", f"Score {score} should be A, got {grade}"
            elif score >= 70:
                assert grade == "B+", f"Score {score} should be B+, got {grade}"
            elif score >= 60:
                assert grade == "B", f"Score {score} should be B, got {grade}"
            elif score >= 50:
                assert grade == "C", f"Score {score} should be C, got {grade}"
            elif score >= 40:
                assert grade == "D", f"Score {score} should be D, got {grade}"
            else:
                assert grade == "F", f"Score {score} should be F, got {grade}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
