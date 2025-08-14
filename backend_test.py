import requests
import sys
import json
import base64
from datetime import datetime
import time

class DigitalStoreAPITester:
    def __init__(self, base_url="https://coin-market-shop.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.user_token = None
        self.admin_token = None
        self.user_data = None
        self.admin_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_product_id = None
        self.created_topup_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = int(time.time())
        success, response = self.run_test(
            "User Registration",
            "POST",
            "register",
            200,
            data={
                "email": f"user{timestamp}@test.com",
                "username": f"testuser{timestamp}",
                "password": "password123",
                "is_admin": False
            }
        )
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            self.user_data = response['user']
            print(f"   User ID: {self.user_data['id']}")
            print(f"   Wallet Balance: {self.user_data['wallet_balance']}")
            return True
        return False

    def test_admin_registration(self):
        """Test admin registration"""
        timestamp = int(time.time())
        success, response = self.run_test(
            "Admin Registration",
            "POST",
            "register",
            200,
            data={
                "email": f"admin{timestamp}@test.com",
                "username": f"testadmin{timestamp}",
                "password": "admin123",
                "is_admin": True
            }
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_data = response['user']
            print(f"   Admin ID: {self.admin_data['id']}")
            print(f"   Is Admin: {self.admin_data['is_admin']}")
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        if not self.user_data:
            return False
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "login",
            200,
            data={
                "email": self.user_data['email'],
                "password": "password123"
            }
        )
        return success and 'access_token' in response

    def test_get_user_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "me",
            200,
            token=self.user_token
        )
        return success and 'email' in response

    def test_get_products(self):
        """Test getting products list"""
        success, response = self.run_test(
            "Get Products",
            "GET",
            "products",
            200
        )
        return success

    def test_create_product_admin(self):
        """Test creating product as admin"""
        success, response = self.run_test(
            "Create Product (Admin)",
            "POST",
            "products",
            200,
            data={
                "name": "Test Digital Product",
                "description": "A test digital product for testing purposes",
                "price": 10.99,
                "image_url": "https://via.placeholder.com/300x200",
                "category": "Digital"
            },
            token=self.admin_token
        )
        if success and 'id' in response:
            self.created_product_id = response['id']
            print(f"   Created Product ID: {self.created_product_id}")
            return True
        return False

    def test_create_product_user_forbidden(self):
        """Test creating product as regular user (should fail)"""
        success, response = self.run_test(
            "Create Product (User - Should Fail)",
            "POST",
            "products",
            403,  # Expecting forbidden
            data={
                "name": "Test Product",
                "description": "Should not be created",
                "price": 5.99,
                "image_url": "",
                "category": "Test"
            },
            token=self.user_token
        )
        return success  # Success means we got the expected 403

    def test_topup_request(self):
        """Test creating a top-up request"""
        # Create a dummy base64 image
        dummy_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        success, response = self.run_test(
            "Create Top-up Request",
            "POST",
            "topup",
            200,
            data={
                "amount": 50.0,
                "receipt_data": dummy_image
            },
            token=self.user_token
        )
        if success and 'request_id' in response:
            self.created_topup_id = response['request_id']
            print(f"   Created Top-up ID: {self.created_topup_id}")
            return True
        return False

    def test_get_user_topup_requests(self):
        """Test getting user's top-up requests"""
        success, response = self.run_test(
            "Get User Top-up Requests",
            "GET",
            "topup-requests",
            200,
            token=self.user_token
        )
        return success

    def test_get_admin_topup_requests(self):
        """Test getting all top-up requests as admin"""
        success, response = self.run_test(
            "Get Admin Top-up Requests",
            "GET",
            "admin/topup-requests",
            200,
            token=self.admin_token
        )
        return success

    def test_get_admin_topup_requests_user_forbidden(self):
        """Test getting admin top-up requests as user (should fail)"""
        success, response = self.run_test(
            "Get Admin Top-up Requests (User - Should Fail)",
            "GET",
            "admin/topup-requests",
            403,  # Expecting forbidden
            token=self.user_token
        )
        return success  # Success means we got the expected 403

    def test_approve_topup_request(self):
        """Test approving a top-up request"""
        if not self.created_topup_id:
            print("   No top-up request to approve")
            return False
            
        success, response = self.run_test(
            "Approve Top-up Request",
            "POST",
            f"admin/topup-requests/{self.created_topup_id}/approve",
            200,
            token=self.admin_token
        )
        return success

    def test_user_balance_after_approval(self):
        """Test that user balance increased after approval"""
        success, response = self.run_test(
            "Check User Balance After Approval",
            "GET",
            "me",
            200,
            token=self.user_token
        )
        if success and 'wallet_balance' in response:
            new_balance = response['wallet_balance']
            print(f"   New wallet balance: {new_balance}")
            # Should be 50.0 (initial 0.0 + 50.0 from top-up)
            return new_balance > 0
        return False

    def test_purchase_product(self):
        """Test purchasing a product"""
        if not self.created_product_id:
            print("   No product to purchase")
            return False
            
        success, response = self.run_test(
            "Purchase Product",
            "POST",
            f"purchase/{self.created_product_id}",
            200,
            token=self.user_token
        )
        return success

    def test_get_user_purchases(self):
        """Test getting user's purchase history"""
        success, response = self.run_test(
            "Get User Purchases",
            "GET",
            "purchases",
            200,
            token=self.user_token
        )
        return success

    def test_insufficient_balance_purchase(self):
        """Test purchasing when insufficient balance"""
        # First, let's create an expensive product
        success, response = self.run_test(
            "Create Expensive Product",
            "POST",
            "products",
            200,
            data={
                "name": "Expensive Product",
                "description": "Too expensive for current balance",
                "price": 1000.0,
                "image_url": "",
                "category": "Premium"
            },
            token=self.admin_token
        )
        
        if success and 'id' in response:
            expensive_product_id = response['id']
            
            # Try to purchase it (should fail)
            success, response = self.run_test(
                "Purchase Expensive Product (Should Fail)",
                "POST",
                f"purchase/{expensive_product_id}",
                400,  # Expecting bad request due to insufficient balance
                token=self.user_token
            )
            return success  # Success means we got the expected 400
        return False

def main():
    print("🚀 Starting Digital Store API Tests")
    print("=" * 50)
    
    tester = DigitalStoreAPITester()
    
    # Test sequence
    test_sequence = [
        ("User Registration", tester.test_user_registration),
        ("Admin Registration", tester.test_admin_registration),
        ("User Login", tester.test_user_login),
        ("Get User Profile", tester.test_get_user_profile),
        ("Get Products", tester.test_get_products),
        ("Create Product (Admin)", tester.test_create_product_admin),
        ("Create Product (User - Forbidden)", tester.test_create_product_user_forbidden),
        ("Create Top-up Request", tester.test_topup_request),
        ("Get User Top-up Requests", tester.test_get_user_topup_requests),
        ("Get Admin Top-up Requests", tester.test_get_admin_topup_requests),
        ("Get Admin Top-up (User - Forbidden)", tester.test_get_admin_topup_requests_user_forbidden),
        ("Approve Top-up Request", tester.test_approve_topup_request),
        ("Check Balance After Approval", tester.test_user_balance_after_approval),
        ("Purchase Product", tester.test_purchase_product),
        ("Get User Purchases", tester.test_get_user_purchases),
        ("Insufficient Balance Purchase", tester.test_insufficient_balance_purchase),
    ]
    
    # Run all tests
    for test_name, test_func in test_sequence:
        try:
            result = test_func()
            if not result:
                print(f"⚠️  Test '{test_name}' failed but continuing...")
        except Exception as e:
            print(f"💥 Test '{test_name}' crashed: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS")
    print("=" * 50)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())