#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime, date, timedelta

def test_endpoint(base_url, endpoint, method='GET', data=None):
    """Test a specific API endpoint"""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    print(f"{'='*60}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=30)
        elif method.upper() == 'POST':
            headers = {'Content-Type': 'application/json'} if data else {}
            response = requests.post(url, json=data, headers=headers, timeout=300)  # 5 min timeout for historical sync
        else:
            print(f"Unsupported method: {method}")
            return False
        
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print("\nResponse Body:")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(response.text)
        
        return response.status_code < 400
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_historical_api.py <base_url>")
        print("Example: python test_historical_api.py http://localhost:8080")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    print("Lengolf Sales API - Historical Sync Testing")
    print(f"Base URL: {base_url}")
    print("=" * 60)
    
    # Test basic endpoints first
    print("\n🏥 Testing Health Check...")
    test_endpoint(base_url, "/health", "GET")
    
    print("\n📋 Testing Info Endpoint...")
    test_endpoint(base_url, "/info", "GET")
    
    print("\n📊 Testing Data Coverage Report...")
    test_endpoint(base_url, "/data/coverage", "GET")
    
    # Test historical sync with a small recent range (last 3 days)
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=2)    # 3 days ago
    
    historical_data = {
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d')
    }
    
    print(f"\n📅 Testing Historical Sync (Small Range: {start_date} to {end_date})...")
    test_endpoint(base_url, "/sync/historical", "POST", historical_data)
    
    # Test historical sync with invalid data
    print(f"\n❌ Testing Historical Sync with Invalid Date Format...")
    invalid_data = {
        "start_date": "invalid-date",
        "end_date": "2025-01-10"
    }
    test_endpoint(base_url, "/sync/historical", "POST", invalid_data)
    
    print(f"\n❌ Testing Historical Sync with Missing Fields...")
    incomplete_data = {
        "start_date": "2025-01-07"
        # Missing end_date
    }
    test_endpoint(base_url, "/sync/historical", "POST", incomplete_data)
    
    print(f"\n❌ Testing Historical Sync with Invalid Date Range...")
    invalid_range_data = {
        "start_date": "2025-01-10",
        "end_date": "2025-01-07"  # End before start
    }
    test_endpoint(base_url, "/sync/historical", "POST", invalid_range_data)
    
    # Test missing historical data sync (this might take a while)
    print(f"\n🔄 Testing Missing Historical Data Sync...")
    print("⚠️  Warning: This might take several minutes if there are large gaps!")
    user_input = input("Do you want to proceed with missing data sync? (y/N): ")
    
    if user_input.lower() == 'y':
        test_endpoint(base_url, "/sync/missing", "POST")
    else:
        print("Skipping missing data sync test.")
    
    # Test daily sync for comparison
    print(f"\n📅 Testing Daily Sync...")
    test_endpoint(base_url, "/sync/daily", "POST")
    
    print("\n" + "="*60)
    print("🎉 Testing Complete!")
    print("="*60)

if __name__ == "__main__":
    main() 