import requests
import sys
from datetime import datetime, timedelta
import json

class FOXBackendTester:
    def __init__(self, base_url="https://fox-bin-tracker.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_ids = {
            'client_id': None,
            'dumpster_id': None,
            'order_id': None,
            'payable_id': None,
            'receivable_id': None
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_auth_login(self):
        """Test login with provided credentials"""
        success, response = self.run_test(
            "Login with admin credentials",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@fox.com", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_create_client(self):
        """Create a test client"""
        client_data = {
            "name": "Maria Santos",
            "email": "maria@email.com",
            "phone": "(21) 99999-8888",
            "address": "Av. Brasil, 500",
            "document": "987.654.321-00",
            "document_type": "cpf"
        }
        success, response = self.run_test(
            "Create Client",
            "POST",
            "clients",
            200,
            data=client_data
        )
        if success and 'id' in response:
            self.created_ids['client_id'] = response['id']
            print(f"   Client ID: {response['id']}")
            return True
        return False

    def test_get_clients(self):
        """Get all clients"""
        success, response = self.run_test(
            "Get All Clients",
            "GET",
            "clients",
            200
        )
        if success:
            print(f"   Found {len(response)} clients")
        return success

    def test_get_client_by_id(self):
        """Get specific client by ID"""
        if not self.created_ids['client_id']:
            print("❌ No client ID available for testing")
            return False
        
        success, response = self.run_test(
            "Get Client by ID",
            "GET",
            f"clients/{self.created_ids['client_id']}",
            200
        )
        if success:
            print(f"   Client name: {response.get('name', 'N/A')}")
        return success

    def test_update_client(self):
        """Update client information"""
        if not self.created_ids['client_id']:
            print("❌ No client ID available for testing")
            return False
        
        update_data = {
            "name": "Maria Santos Silva",
            "email": "maria.silva@email.com",
            "phone": "(21) 99999-8888",
            "address": "Av. Brasil, 500 - Apt 101",
            "document": "987.654.321-00",
            "document_type": "cpf"
        }
        success, response = self.run_test(
            "Update Client",
            "PUT",
            f"clients/{self.created_ids['client_id']}",
            200,
            data=update_data
        )
        return success

    def test_create_dumpster(self):
        """Create a test dumpster"""
        dumpster_data = {
            "identifier": "CAC-002",
            "size": "7m³",
            "capacity": "5 toneladas",
            "description": "Caçamba grande"
        }
        success, response = self.run_test(
            "Create Dumpster",
            "POST",
            "dumpsters",
            200,
            data=dumpster_data
        )
        if success and 'id' in response:
            self.created_ids['dumpster_id'] = response['id']
            print(f"   Dumpster ID: {response['id']}")
            return True
        return False

    def test_get_dumpsters(self):
        """Get all dumpsters"""
        success, response = self.run_test(
            "Get All Dumpsters",
            "GET",
            "dumpsters",
            200
        )
        if success:
            print(f"   Found {len(response)} dumpsters")
        return success

    def test_update_dumpster_status(self):
        """Update dumpster status"""
        if not self.created_ids['dumpster_id']:
            print("❌ No dumpster ID available for testing")
            return False
        
        success, response = self.run_test(
            "Update Dumpster Status",
            "PATCH",
            f"dumpsters/{self.created_ids['dumpster_id']}/status?status=maintenance&location=Oficina Central",
            200
        )
        return success

    def test_create_order(self):
        """Create a test order"""
        if not self.created_ids['client_id'] or not self.created_ids['dumpster_id']:
            print("❌ Missing client or dumpster ID for order creation")
            return False
        
        # First set dumpster back to available
        self.run_test(
            "Set Dumpster Available",
            "PATCH",
            f"dumpsters/{self.created_ids['dumpster_id']}/status?status=available",
            200
        )
        
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        order_data = {
            "client_id": self.created_ids['client_id'],
            "dumpster_id": self.created_ids['dumpster_id'],
            "order_type": "placement",
            "delivery_address": "Rua das Flores, 123",
            "rental_value": 350.00,
            "payment_method": "cash",
            "scheduled_date": future_date,
            "notes": "Entrega pela manhã"
        }
        success, response = self.run_test(
            "Create Order",
            "POST",
            "orders",
            200,
            data=order_data
        )
        if success and 'id' in response:
            self.created_ids['order_id'] = response['id']
            print(f"   Order ID: {response['id']}")
            return True
        return False

    def test_get_orders(self):
        """Get all orders"""
        success, response = self.run_test(
            "Get All Orders",
            "GET",
            "orders",
            200
        )
        if success:
            print(f"   Found {len(response)} orders")
        return success

    def test_update_order_status(self):
        """Update order status"""
        if not self.created_ids['order_id']:
            print("❌ No order ID available for testing")
            return False
        
        success, response = self.run_test(
            "Update Order Status",
            "PATCH",
            f"orders/{self.created_ids['order_id']}/status?status=in_progress",
            200
        )
        return success

    def test_create_accounts_payable(self):
        """Create accounts payable"""
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        payable_data = {
            "description": "Manutenção de veículo",
            "amount": 500.00,
            "due_date": future_date,
            "category": "Manutenção",
            "notes": "Revisão mensal do caminhão"
        }
        success, response = self.run_test(
            "Create Accounts Payable",
            "POST",
            "finance/accounts-payable",
            200,
            data=payable_data
        )
        if success and 'id' in response:
            self.created_ids['payable_id'] = response['id']
            print(f"   Payable ID: {response['id']}")
            return True
        return False

    def test_get_accounts_payable(self):
        """Get all accounts payable"""
        success, response = self.run_test(
            "Get Accounts Payable",
            "GET",
            "finance/accounts-payable",
            200
        )
        if success:
            print(f"   Found {len(response)} payable accounts")
        return success

    def test_pay_account(self):
        """Mark account as paid"""
        if not self.created_ids['payable_id']:
            print("❌ No payable ID available for testing")
            return False
        
        success, response = self.run_test(
            "Pay Account",
            "PATCH",
            f"finance/accounts-payable/{self.created_ids['payable_id']}/pay",
            200
        )
        return success

    def test_get_accounts_receivable(self):
        """Get all accounts receivable (should be auto-created from order)"""
        success, response = self.run_test(
            "Get Accounts Receivable",
            "GET",
            "finance/accounts-receivable",
            200
        )
        if success:
            print(f"   Found {len(response)} receivable accounts")
            if response and len(response) > 0:
                self.created_ids['receivable_id'] = response[0]['id']
                print(f"   First receivable ID: {response[0]['id']}")
        return success

    def test_receive_payment(self):
        """Mark payment as received"""
        if not self.created_ids['receivable_id']:
            print("❌ No receivable ID available for testing")
            return False
        
        success, response = self.run_test(
            "Receive Payment",
            "PATCH",
            f"finance/accounts-receivable/{self.created_ids['receivable_id']}/receive",
            200
        )
        return success

    def test_dashboard_stats(self):
        """Get dashboard statistics"""
        success, response = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        if success:
            print(f"   Total dumpsters: {response.get('total_dumpsters', 0)}")
            print(f"   Active orders: {response.get('active_orders', 0)}")
            print(f"   Cash balance: R$ {response.get('cash_balance', 0):.2f}")
        return success

    def test_client_orders(self):
        """Get client order history"""
        if not self.created_ids['client_id']:
            print("❌ No client ID available for testing")
            return False
        
        success, response = self.run_test(
            "Get Client Orders",
            "GET",
            f"clients/{self.created_ids['client_id']}/orders",
            200
        )
        if success:
            print(f"   Found {len(response)} orders for client")
        return success

def main():
    print("🚀 Starting FOX Backend API Tests")
    print("=" * 50)
    
    tester = FOXBackendTester()
    
    # Test sequence
    tests = [
        # Authentication
        tester.test_auth_login,
        
        # Client management
        tester.test_create_client,
        tester.test_get_clients,
        tester.test_get_client_by_id,
        tester.test_update_client,
        
        # Dumpster management
        tester.test_create_dumpster,
        tester.test_get_dumpsters,
        tester.test_update_dumpster_status,
        
        # Order management
        tester.test_create_order,
        tester.test_get_orders,
        tester.test_update_order_status,
        
        # Financial management
        tester.test_create_accounts_payable,
        tester.test_get_accounts_payable,
        tester.test_pay_account,
        tester.test_get_accounts_receivable,
        tester.test_receive_payment,
        
        # Dashboard and reports
        tester.test_dashboard_stats,
        tester.test_client_orders,
    ]
    
    # Run all tests
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())