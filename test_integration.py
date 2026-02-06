#!/usr/bin/env python3
"""
Test OneWeather integration
"""

import asyncio
import httpx
import sys
from datetime import datetime

async def test_integration():
    """Test the full integration"""
    print("🧪 Testing OneWeather Integration")
    print("=" * 60)
    
    # Test 1: API Health
    print("\n1. Testing API Health...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8000/health/")
            if response.status_code == 200:
                print("   ✅ API is healthy")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ❌ API health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ API not reachable: {e}")
        print("   Start API with: cd /home/ubuntu/OneWeather/api && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    
    # Test 2: Forecast Endpoint
    print("\n2. Testing Forecast Endpoint...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test Ardmore, PA
            response = await client.get(
                "http://localhost:8000/api/v1/forecast/40.0048/-75.2923",
                params={"hours": 6, "include_sources": True}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Forecast endpoint working")
                print(f"   Location: {data['latitude']}, {data['longitude']}")
                print(f"   Points returned: {len(data['points'])}")
                print(f"   Sources used: {data['sources_used']}")
                print(f"   Blending method: {data['blending_method']}")
                
                if data['points']:
                    point = data['points'][0]
                    print(f"   Sample forecast:")
                    print(f"     Time: {point['timestamp']}")
                    print(f"     Temp: {point['temperature_c']}°C")
                    print(f"     Wind: {point['wind_speed_mps']} m/s")
                
                return True
            else:
                print(f"   ❌ Forecast failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Forecast error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Dashboard Connection
    print("\n3. Testing Dashboard Connection...")
    print("   Dashboard running at: http://localhost:8081")
    print("   Open browser to test dashboard")
    return True

async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("OneWeather Integration Test")
    print("=" * 60)
    
    success = await test_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Integration ready.")
        print("\nNext steps:")
        print("1. Dashboard: http://localhost:8081")
        print("2. API Docs: http://localhost:8000/docs")
        print("3. Test Ardmore, PA forecast")
    else:
        print("⚠️  Some tests failed. Check logs above.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())