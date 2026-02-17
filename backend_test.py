#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class FieldFlowAPITester:
    def __init__(self, base_url="https://couponsys.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.worker_token = None
        self.branch_manager_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.admin_user_id = None
        self.worker_user_id = None
        self.branch_manager_id = None
        self.coupon_id = None
        self.coupon_code = None
        self.booking_id = None
        self.branch_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}
            
            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.make_request('GET', 'health')
        self.log_test("Health Check", success and "status" in response)
        return success

    def test_user_registration(self):
        """Test user registration for different roles"""
        timestamp = datetime.now().strftime("%H%M%S")
        
        # Test admin registration
        admin_data = {
            "email": f"admin_{timestamp}@fieldflow.com",
            "password": "admin123",
            "name": f"Admin User {timestamp}",
            "phone": "+1234567890",
            "role": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/register', admin_data)
        if success and "access_token" in response:
            self.admin_token = response["access_token"]
            self.admin_user_id = response["user"]["id"]
            self.log_test("Admin Registration", True)
        else:
            self.log_test("Admin Registration", False, str(response))
            return False

        # Test worker registration
        worker_data = {
            "email": f"worker_{timestamp}@fieldflow.com",
            "password": "worker123",
            "name": f"Worker User {timestamp}",
            "phone": "+1234567891",
            "role": "worker"
        }
        
        success, response = self.make_request('POST', 'auth/register', worker_data)
        if success and "access_token" in response:
            self.worker_token = response["access_token"]
            self.worker_user_id = response["user"]["id"]
            self.log_test("Worker Registration", True)
        else:
            self.log_test("Worker Registration", False, str(response))

        # Test branch manager registration
        branch_data = {
            "email": f"branch_{timestamp}@fieldflow.com",
            "password": "branch123",
            "name": f"Branch Manager {timestamp}",
            "phone": "+1234567892",
            "role": "branch_manager"
        }
        
        success, response = self.make_request('POST', 'auth/register', branch_data)
        if success and "access_token" in response:
            self.branch_manager_token = response["access_token"]
            self.branch_manager_id = response["user"]["id"]
            self.log_test("Branch Manager Registration", True)
        else:
            self.log_test("Branch Manager Registration", False, str(response))

        return True

    def test_user_login(self):
        """Test user login"""
        # We'll use the registered admin for login test
        login_data = {
            "email": f"admin_{datetime.now().strftime('%H%M%S')}@fieldflow.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, expected_status=401)  # Should fail for non-existent user
        self.log_test("Login with Invalid Credentials", success)  # Should return 401
        
        return True

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        if not self.admin_token:
            self.log_test("Dashboard Stats", False, "No admin token available")
            return False
            
        success, response = self.make_request('GET', 'dashboard/stats', token=self.admin_token)
        expected_fields = ['total_workers', 'active_workers', 'total_coupons_today', 'redemption_rate']
        
        if success and all(field in response for field in expected_fields):
            self.log_test("Dashboard Stats", True)
        else:
            self.log_test("Dashboard Stats", False, f"Missing fields or error: {response}")
        
        return success

    def test_attendance_flow(self):
        """Test GPS punch-in and punch-out"""
        if not self.worker_token:
            self.log_test("Attendance Flow", False, "No worker token available")
            return False

        # Test punch-in
        punch_in_data = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "accuracy": 10.0
        }
        
        success, response = self.make_request('POST', 'attendance/punch-in', punch_in_data, self.worker_token)
        if success:
            self.log_test("GPS Punch-In", True)
        else:
            self.log_test("GPS Punch-In", False, str(response))
            return False

        # Test getting today's attendance
        success, response = self.make_request('GET', 'attendance/today', token=self.worker_token)
        self.log_test("Get Today's Attendance", success and isinstance(response, list))

        # Test punch-out
        punch_out_data = {
            "latitude": 37.7750,
            "longitude": -122.4195,
            "accuracy": 8.0
        }
        
        success, response = self.make_request('POST', 'attendance/punch-out', punch_out_data, self.worker_token)
        if success:
            self.log_test("GPS Punch-Out", True)
        else:
            self.log_test("GPS Punch-Out", False, str(response))

        return True

    def test_coupon_issuance(self):
        """Test coupon creation with proper format"""
        if not self.worker_token:
            self.log_test("Coupon Issuance", False, "No worker token available")
            return False

        coupon_data = {
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "area_id": "NORTH",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        
        success, response = self.make_request('POST', 'coupons/create', coupon_data, self.worker_token)
        
        if success and "code" in response:
            self.coupon_code = response["code"]
            self.coupon_id = response["id"]
            
            # Verify coupon code format: SVL-AREAID-WORKERID-RANDOM6
            code_parts = self.coupon_code.split('-')
            format_valid = (len(code_parts) == 4 and 
                          code_parts[0] == "SVL" and
                          len(code_parts[3]) == 6)
            
            self.log_test("Coupon Code Format", format_valid, f"Generated: {self.coupon_code}")
            self.log_test("Coupon Issuance", True)
        else:
            self.log_test("Coupon Issuance", False, str(response))
            return False

        return True

    def test_otp_redemption_flow(self):
        """Test OTP request and verification"""
        if not self.coupon_code:
            self.log_test("OTP Redemption Flow", False, "No coupon code available")
            return False

        # Request OTP
        otp_request_data = {
            "coupon_code": self.coupon_code,
            "phone": "+1234567890"
        }
        
        success, response = self.make_request('POST', 'coupons/request-otp', otp_request_data)
        
        if success and "mock_otp" in response:
            mock_otp = response["mock_otp"]
            self.log_test("OTP Request", True, f"Mock OTP: {mock_otp}")
            
            # Verify OTP
            otp_verify_data = {
                "coupon_code": self.coupon_code,
                "phone": "+1234567890",
                "otp": mock_otp
            }
            
            success, response = self.make_request('POST', 'coupons/verify-otp', otp_verify_data)
            if success:
                self.log_test("OTP Verification", True)
            else:
                self.log_test("OTP Verification", False, str(response))
        else:
            self.log_test("OTP Request", False, str(response))
            return False

        return True

    def test_booking_creation(self):
        """Test booking creation after coupon redemption"""
        if not self.coupon_id:
            self.log_test("Booking Creation", False, "No redeemed coupon available")
            return False

        booking_data = {
            "coupon_id": self.coupon_id,
            "service_type": "Installation",
            "address": "123 Main St, San Francisco, CA",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "notes": "Test booking"
        }
        
        success, response = self.make_request('POST', 'bookings', booking_data)
        
        if success and "id" in response:
            self.booking_id = response["id"]
            self.log_test("Booking Creation", True)
        else:
            self.log_test("Booking Creation", False, str(response))
            return False

        return True

    def test_branch_management(self):
        """Test branch creation and assignment"""
        if not self.admin_token:
            self.log_test("Branch Management", False, "No admin token available")
            return False

        # Create branch
        branch_data = {
            "name": "Test Branch",
            "address": "456 Branch St, San Francisco, CA",
            "latitude": 37.7849,
            "longitude": -122.4094,
            "contact_phone": "+1234567893"
        }
        
        success, response = self.make_request('POST', 'branches', branch_data, self.admin_token)
        
        if success and "id" in response:
            self.branch_id = response["id"]
            self.log_test("Branch Creation", True)
            
            # Test branch assignment to booking
            if self.booking_id:
                assign_data = {"branch_id": self.branch_id}
                success, response = self.make_request('PATCH', f'bookings/{self.booking_id}/assign', assign_data, self.admin_token)
                self.log_test("Branch Assignment", success)
            
        else:
            self.log_test("Branch Creation", False, str(response))
            return False

        return True

    def test_booking_status_updates(self):
        """Test booking status lifecycle"""
        if not self.booking_id or not self.admin_token:
            self.log_test("Booking Status Updates", False, "Missing booking ID or admin token")
            return False

        # Update to DISPATCHED
        status_data = {
            "status": "DISPATCHED",
            "notes": "Technician dispatched"
        }
        
        success, response = self.make_request('PATCH', f'bookings/{self.booking_id}/status', status_data, self.admin_token)
        self.log_test("Booking Status - DISPATCHED", success)

        # Update to COMPLETED
        status_data = {
            "status": "COMPLETED",
            "notes": "Service completed successfully"
        }
        
        success, response = self.make_request('PATCH', f'bookings/{self.booking_id}/status', status_data, self.admin_token)
        self.log_test("Booking Status - COMPLETED", success)

        return True

    def test_role_based_access(self):
        """Test role-based access control"""
        # Test worker trying to access admin endpoint
        if self.worker_token:
            success, response = self.make_request('GET', 'dashboard/stats', token=self.worker_token, expected_status=403)
            self.log_test("Role-based Access Control", success)  # Should return 403
        
        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting FieldFlow Pro API Tests")
        print("=" * 50)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Authentication flow
        self.test_user_registration()
        self.test_user_login()
        
        # Core functionality
        self.test_dashboard_stats()
        self.test_attendance_flow()
        self.test_coupon_issuance()
        self.test_otp_redemption_flow()
        self.test_booking_creation()
        self.test_branch_management()
        self.test_booking_status_updates()
        
        # Security
        self.test_role_based_access()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = FieldFlowAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())