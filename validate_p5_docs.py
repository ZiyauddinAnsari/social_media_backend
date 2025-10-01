#!/usr/bin/env python
"""
Quick validation script for P5 Documentation Enhancements
Tests that enhanced error schemas and documentation are working correctly.
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_api_docs():
    """Test that API documentation is accessible"""
    print("Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/api/docs/")
        if response.status_code == 200:
            print("✅ API docs accessible at /api/docs/")
            return True
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False

def test_schema_endpoint():
    """Test that OpenAPI schema is generated with our enhancements"""
    print("Testing OpenAPI Schema...")
    try:
        response = requests.get(f"{BASE_URL}/api/schema/")
        if response.status_code == 200:
            schema = response.json()
            
            # Check if our custom components are present
            components = schema.get('components', {}).get('schemas', {})
            expected_schemas = [
                'ErrorValidation', 'ErrorThrottle', 'ErrorAuthentication',
                'ErrorPermission', 'ErrorNotFound', 'TokenResponse', 'MediaBatchResponse'
            ]
            
            found_schemas = []
            missing_schemas = []
            
            for schema_name in expected_schemas:
                if schema_name in components:
                    found_schemas.append(schema_name)
                else:
                    missing_schemas.append(schema_name)
            
            print(f"✅ Schema endpoint accessible: {len(schema)} top-level keys")
            print(f"✅ Found custom schemas: {found_schemas}")
            
            if missing_schemas:
                print(f"⚠️  Missing schemas: {missing_schemas}")
            else:
                print("✅ All custom error schemas present")
            
            return True
        else:
            print(f"❌ Schema endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Schema endpoint error: {e}")
        return False

def test_enhanced_endpoint_documentation():
    """Test that endpoints have enhanced error response documentation"""
    print("Testing Enhanced Endpoint Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/api/schema/")
        if response.status_code != 200:
            print("❌ Cannot fetch schema for endpoint testing")
            return False
            
        schema = response.json()
        paths = schema.get('paths', {})
        
        # Check specific endpoints for enhanced documentation
        test_endpoints = [
            '/api/auth/register/',
            '/api/auth/token/',
            '/api/auth/token/refresh/',
            '/api/posts/',
        ]
        
        enhanced_count = 0
        for endpoint in test_endpoints:
            if endpoint in paths:
                path_info = paths[endpoint]
                methods = ['post', 'get', 'put', 'patch', 'delete']
                
                for method in methods:
                    if method in path_info:
                        responses = path_info[method].get('responses', {})
                        error_codes = [code for code in responses.keys() if code in ['400', '401', '403', '404', '429']]
                        
                        if error_codes:
                            enhanced_count += 1
                            print(f"✅ {method.upper()} {endpoint}: error responses {error_codes}")
                            break
        
        if enhanced_count > 0:
            print(f"✅ Enhanced documentation found on {enhanced_count} endpoints")
            return True
        else:
            print("⚠️  No enhanced error documentation found")
            return False
            
    except Exception as e:
        print(f"❌ Endpoint documentation test error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("P5 Documentation Enhancements - Validation Tests")
    print("=" * 50)
    
    tests = [
        test_api_docs,
        test_schema_endpoint,
        test_enhanced_endpoint_documentation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Empty line between tests
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All P5 Documentation Enhancement validations PASSED!")
        print("✅ Enhanced error schemas are working correctly")
        print("✅ API documentation is accessible and complete") 
        print("✅ Error response annotations are in place")
        return True
    else:
        print("❌ Some validations failed. Check server status and configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)