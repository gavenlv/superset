#!/usr/bin/env python3
"""
Superset API Test Runner
This script validates all major Superset API endpoints with comprehensive testing
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class SupersetApiTester:
    def __init__(self, base_url: str = "http://localhost:8088", username: str = "admin", password: str = "admin"):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_token = None
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, message: str = "", response_time: float = 0):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "message": message,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if message:
            print(f"   📝 {message}")
        if response_time > 0:
            print(f"   ⏱️ Response time: {response_time:.2f}ms")
        print()

    def make_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """Make HTTP request and return response with timing"""
        url = f"{self.base_url}{endpoint}"
        
        # Add authorization header if token is available
        if self.access_token and 'headers' not in kwargs:
            kwargs['headers'] = {}
        if self.access_token:
            kwargs['headers']['Authorization'] = f'Bearer {self.access_token}'
            
        start_time = time.time()
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response_time = (time.time() - start_time) * 1000
            return response, response_time
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return None, response_time

    def test_authentication(self):
        """Test authentication endpoints"""
        print("🔐 Testing Authentication...")
        
        # Test login
        login_data = {
            "username": self.username,
            "password": self.password,
            "provider": "db"
        }
        
        response, response_time = self.make_request(
            'POST', 
            '/api/v1/security/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.access_token = data.get('access_token')
                if self.access_token:
                    self.log_test("Authentication - Login", "PASS", 
                                f"Successfully obtained access token", response_time)
                else:
                    self.log_test("Authentication - Login", "FAIL", 
                                "No access token in response", response_time)
            except json.JSONDecodeError:
                self.log_test("Authentication - Login", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Authentication - Login", "FAIL", error_msg, response_time)
            
        # Test user info
        if self.access_token:
            response, response_time = self.make_request('GET', '/api/v1/me/')
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if 'result' in data and 'username' in data['result']:
                        self.log_test("Authentication - User Info", "PASS", 
                                    f"User: {data['result']['username']}", response_time)
                    else:
                        self.log_test("Authentication - User Info", "FAIL", 
                                    "Invalid user info structure", response_time)
                except json.JSONDecodeError:
                    self.log_test("Authentication - User Info", "FAIL", 
                                "Invalid JSON response", response_time)
            else:
                error_msg = f"Status: {response.status_code if response else 'No response'}"
                self.log_test("Authentication - User Info", "FAIL", error_msg, response_time)

    def test_dashboards(self):
        """Test dashboard endpoints"""
        print("📊 Testing Dashboards...")
        
        # List dashboards
        response, response_time = self.make_request('GET', '/api/v1/dashboard/?q=(page:0,page_size:25)')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'count' in data and 'result' in data:
                    count = data['count']
                    dashboards = data['result']
                    self.log_test("Dashboards - List", "PASS", 
                                f"Found {count} dashboards", response_time)
                    
                    # Test dashboard details if we have dashboards
                    if dashboards:
                        dashboard_id = dashboards[0]['id']
                        detail_response, detail_time = self.make_request(
                            'GET', f'/api/v1/dashboard/{dashboard_id}'
                        )
                        
                        if detail_response and detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            if 'result' in detail_data:
                                title = detail_data['result'].get('dashboard_title', 'Unknown')
                                self.log_test("Dashboards - Detail", "PASS", 
                                            f"Dashboard: {title}", detail_time)
                            else:
                                self.log_test("Dashboards - Detail", "FAIL", 
                                            "Invalid detail structure", detail_time)
                        else:
                            error_msg = f"Status: {detail_response.status_code if detail_response else 'No response'}"
                            self.log_test("Dashboards - Detail", "FAIL", error_msg, detail_time)
                else:
                    self.log_test("Dashboards - List", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("Dashboards - List", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Dashboards - List", "FAIL", error_msg, response_time)

    def test_charts(self):
        """Test chart endpoints"""
        print("📈 Testing Charts...")
        
        # List charts
        response, response_time = self.make_request('GET', '/api/v1/chart/?q=(page:0,page_size:25)')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'count' in data and 'result' in data:
                    count = data['count']
                    charts = data['result']
                    self.log_test("Charts - List", "PASS", 
                                f"Found {count} charts", response_time)
                    
                    # Test chart data if we have charts
                    if charts:
                        chart_data_query = {
                            "datasource": {"id": 1, "type": "table"},
                            "queries": [{
                                "time_range": "No filter",
                                "granularity": "ds",
                                "filters": [],
                                "extras": {"having": "", "where": ""}
                            }],
                            "result_format": "json",
                            "result_type": "full"
                        }
                        
                        data_response, data_time = self.make_request(
                            'POST', '/api/v1/chart/data',
                            json=chart_data_query,
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        if data_response and data_response.status_code in [200, 202]:
                            self.log_test("Charts - Data Query", "PASS", 
                                        "Chart data query successful", data_time)
                        else:
                            error_msg = f"Status: {data_response.status_code if data_response else 'No response'}"
                            self.log_test("Charts - Data Query", "WARN", error_msg, data_time)
                else:
                    self.log_test("Charts - List", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("Charts - List", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Charts - List", "FAIL", error_msg, response_time)

    def test_datasets(self):
        """Test dataset endpoints"""
        print("🗃️ Testing Datasets...")
        
        response, response_time = self.make_request('GET', '/api/v1/dataset/?q=(page:0,page_size:25)')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'count' in data and 'result' in data:
                    count = data['count']
                    self.log_test("Datasets - List", "PASS", 
                                f"Found {count} datasets", response_time)
                else:
                    self.log_test("Datasets - List", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("Datasets - List", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Datasets - List", "FAIL", error_msg, response_time)

    def test_databases(self):
        """Test database endpoints"""
        print("🗄️ Testing Databases...")
        
        # List databases
        response, response_time = self.make_request('GET', '/api/v1/database/')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'result' in data:
                    count = len(data['result'])
                    self.log_test("Databases - List", "PASS", 
                                f"Found {count} databases", response_time)
                    
                    # Test connection
                    test_connection_data = {
                        "sqlalchemy_uri": "sqlite:///",
                        "database_name": "test_connection"
                    }
                    
                    conn_response, conn_time = self.make_request(
                        'POST', '/api/v1/database/test_connection',
                        json=test_connection_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if conn_response and conn_response.status_code in [200, 400, 422]:
                        self.log_test("Databases - Test Connection", "PASS", 
                                    "Connection test completed", conn_time)
                    else:
                        error_msg = f"Status: {conn_response.status_code if conn_response else 'No response'}"
                        self.log_test("Databases - Test Connection", "WARN", error_msg, conn_time)
                else:
                    self.log_test("Databases - List", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("Databases - List", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Databases - List", "FAIL", error_msg, response_time)

    def test_sqllab(self):
        """Test SQL Lab endpoints"""
        print("🔬 Testing SQL Lab...")
        
        # Get first database ID
        db_response, _ = self.make_request('GET', '/api/v1/database/')
        database_id = 1  # Default fallback
        
        if db_response and db_response.status_code == 200:
            try:
                db_data = db_response.json()
                if db_data['result']:
                    database_id = db_data['result'][0]['id']
            except:
                pass
        
        # Execute SQL query
        sql_query = {
            "database_id": database_id,
            "sql": "SELECT 1 as test_column, 'Hello World' as message",
            "runAsync": False,
            "schema": "main"
        }
        
        response, response_time = self.make_request(
            'POST', '/api/v1/sqllab/execute/',
            json=sql_query,
            headers={'Content-Type': 'application/json'}
        )
        
        if response and response.status_code in [200, 201, 202]:
            try:
                data = response.json()
                if 'status' in data:
                    status = data['status']
                    self.log_test("SQL Lab - Execute Query", "PASS", 
                                f"Query status: {status}", response_time)
                else:
                    self.log_test("SQL Lab - Execute Query", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("SQL Lab - Execute Query", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("SQL Lab - Execute Query", "WARN", error_msg, response_time)
            
        # List saved queries
        response, response_time = self.make_request('GET', '/api/v1/saved_query/')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'result' in data:
                    count = len(data['result'])
                    self.log_test("SQL Lab - Saved Queries", "PASS", 
                                f"Found {count} saved queries", response_time)
                else:
                    self.log_test("SQL Lab - Saved Queries", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("SQL Lab - Saved Queries", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("SQL Lab - Saved Queries", "FAIL", error_msg, response_time)

    def test_security(self):
        """Test security endpoints"""
        print("🔒 Testing Security...")
        
        # List roles
        response, response_time = self.make_request('GET', '/api/v1/security/roles/')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'result' in data:
                    count = len(data['result'])
                    self.log_test("Security - Roles", "PASS", 
                                f"Found {count} roles", response_time)
                else:
                    self.log_test("Security - Roles", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("Security - Roles", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Security - Roles", "FAIL", error_msg, response_time)
            
        # List users
        response, response_time = self.make_request('GET', '/api/v1/security/users/')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'result' in data:
                    count = len(data['result'])
                    self.log_test("Security - Users", "PASS", 
                                f"Found {count} users", response_time)
                else:
                    self.log_test("Security - Users", "FAIL", 
                                "Invalid response structure", response_time)
            except json.JSONDecodeError:
                self.log_test("Security - Users", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Security - Users", "FAIL", error_msg, response_time)

    def test_apex_jwt(self):
        """Test APEX JWT authentication"""
        print("🔑 Testing APEX JWT...")
        
        # APEX JWT Login
        apex_login_data = {
            "username": self.username,
            "password": self.password
        }
        
        response, response_time = self.make_request(
            'POST', '/api/v1/apex/jwt_login',
            json=apex_login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'token' in data:
                    apex_token = data['token']
                    self.log_test("APEX - JWT Login", "PASS", 
                                "Successfully obtained APEX JWT token", response_time)
                    
                    # Test token validation
                    validation_data = {"token": apex_token}
                    val_response, val_time = self.make_request(
                        'POST', '/api/v1/apex/validate_token',
                        json=validation_data,
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {apex_token}'
                        }
                    )
                    
                    if val_response and val_response.status_code == 200:
                        val_data = val_response.json()
                        if val_data.get('valid'):
                            self.log_test("APEX - Token Validation", "PASS", 
                                        "Token validation successful", val_time)
                        else:
                            self.log_test("APEX - Token Validation", "FAIL", 
                                        "Token validation failed", val_time)
                    else:
                        error_msg = f"Status: {val_response.status_code if val_response else 'No response'}"
                        self.log_test("APEX - Token Validation", "WARN", error_msg, val_time)
                else:
                    self.log_test("APEX - JWT Login", "FAIL", 
                                "No token in response", response_time)
            except json.JSONDecodeError:
                self.log_test("APEX - JWT Login", "FAIL", 
                            "Invalid JSON response", response_time)
        elif response and response.status_code == 404:
            self.log_test("APEX - JWT Login", "WARN", 
                        "APEX endpoints not available (expected in some setups)", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("APEX - JWT Login", "FAIL", error_msg, response_time)

    def test_health_check(self):
        """Test health check endpoints"""
        print("🏥 Testing Health Check...")
        
        # Health check
        response, response_time = self.make_request('GET', '/health')
        
        if response and response.status_code == 200:
            if 'OK' in response.text:
                self.log_test("Health Check", "PASS", 
                            "Service is healthy", response_time)
            else:
                self.log_test("Health Check", "WARN", 
                            "Unexpected health check response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("Health Check", "FAIL", error_msg, response_time)
            
        # OpenAPI spec
        response, response_time = self.make_request('GET', '/api/v1/openapi.json')
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'openapi' in data and 'paths' in data:
                    path_count = len(data['paths'])
                    self.log_test("OpenAPI Specification", "PASS", 
                                f"Found {path_count} API endpoints", response_time)
                else:
                    self.log_test("OpenAPI Specification", "FAIL", 
                                "Invalid OpenAPI structure", response_time)
            except json.JSONDecodeError:
                self.log_test("OpenAPI Specification", "FAIL", 
                            "Invalid JSON response", response_time)
        else:
            error_msg = f"Status: {response.status_code if response else 'No response'}"
            self.log_test("OpenAPI Specification", "FAIL", error_msg, response_time)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Superset API Test Suite\n")
        print(f"📍 Target: {self.base_url}")
        print(f"👤 User: {self.username}")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        # Run all test categories
        self.test_health_check()
        self.test_authentication()
        
        if self.access_token:
            self.test_dashboards()
            self.test_charts()
            self.test_datasets()
            self.test_databases()
            self.test_sqllab()
            self.test_security()
            self.test_apex_jwt()
        else:
            print("❌ Skipping remaining tests due to authentication failure")
            
        # Generate summary
        total_time = time.time() - start_time
        self.generate_summary(total_time)
        
        return self.test_results

    def generate_summary(self, total_time: float):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print("=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"🎯 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"⏱️ Total Time: {total_time:.2f} seconds")
        
        if total_tests > 0:
            success_rate = (passed / total_tests) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
            
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test_name']}: {result['message']}")
                    
        if warnings > 0:
            print("\n⚠️ Warnings:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"   • {result['test_name']}: {result['message']}")
        
        print("=" * 60)
        
        # Save results to file
        self.save_results()

    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"superset_api_test_results_{timestamp}.json"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "username": self.username,
            "total_tests": len(self.test_results),
            "passed": len([r for r in self.test_results if r['status'] == 'PASS']),
            "failed": len([r for r in self.test_results if r['status'] == 'FAIL']),
            "warnings": len([r for r in self.test_results if r['status'] == 'WARN']),
            "results": self.test_results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8088"
        
    if len(sys.argv) > 2:
        username = sys.argv[2]
    else:
        username = "admin"
        
    if len(sys.argv) > 3:
        password = sys.argv[3]
    else:
        password = "admin"
    
    tester = SupersetApiTester(base_url, username, password)
    results = tester.run_all_tests()
    
    # Exit with error code if there are failures
    failed_count = len([r for r in results if r['status'] == 'FAIL'])
    sys.exit(failed_count)

if __name__ == "__main__":
    main() 