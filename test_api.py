#!/usr/bin/env python3
"""
Quick test of OneWeather API
"""

import asyncio
import httpx
import sys

async def test_api():
    """Test the forecast API"""
    print("Testing OneWeather API...")
    
    # Test demo endpoint (NYC)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, check if API is running
            health_response = await client.get("http://localhost:8000/health")
            print(f"✅ Health check: {health_response.status_code}")
            print(f"   Response: {health_response.json()}")
            
            # Test demo forecast
            print("\nTesting demo forecast (NYC)...")
            demo_response = await client.get("http://localhost:8000/api/v1/forecast/test/demo")
            print(f"✅ Demo forecast: {demo_response.status_code}")
            
            if demo_response.status_code == 200:
                data = demo_response.json()
                print(f"   Location: {data['latitude']}, {data['longitude']}")
                print(f"   Points: {len(data['points'])}")
                print(f"   Sources used: {data['sources_used']}")
                print(f"   Blending method: {data['blending_method']}")
                
                if data['points']:
                    first_point = data['points'][0]
                    print(f"\nFirst forecast point:")
                    print(f"   Time: {first_point['timestamp']}")
                    print(f"   Temp: {first_point['temperature_c']}°C")
                    print(f"   Precip: {first_point['precipitation_mm']}mm")
                    print(f"   Wind: {first_point['wind_speed_mps']} m/s")
                    
                return True
            else:
                print(f"❌ Demo failed: {demo_response.text}")
                return False
                
    except httpx.ConnectError:
        print("❌ API not running. Start with: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_direct_sources():
    """Test weather sources directly"""
    print("\nTesting weather sources directly...")
    
    # Add current directory to path
    import sys
    sys.path.append('/home/ubuntu/OneWeather/api')
    
    try:
        from app.services.weather_sources import weather_manager
        
        # Test NYC
        forecasts = await weather_manager.get_all_forecasts(40.7128, -74.0060)
        print(f"✅ Direct source test:")
        print(f"   Sources: {list(forecasts.keys())}")
        
        for source, points in forecasts.items():
            print(f"   {source}: {len(points)} points")
            if points:
                print(f"     First: {points[0].timestamp}, Temp: {points[0].temperature_c}°C")
        
        # Test blending
        blended = weather_manager.blend_forecasts(forecasts)
        print(f"   Blended: {len(blended)} points")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Install dependencies: pip install httpx")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("OneWeather Phase 1 Test")
    print("=" * 60)
    
    # Test 1: Direct sources
    print("\n[Test 1] Direct source integration")
    source_ok = await test_direct_sources()
    
    # Test 2: API
    print("\n[Test 2] API endpoint")
    api_ok = await test_api()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Sources: {'✅' if source_ok else '❌'}")
    print(f"  API: {'✅' if api_ok else '❌'}")
    
    if source_ok and api_ok:
        print("\n🎉 Phase 1 foundation is working!")
        print("\nNext steps:")
        print("1. Start API: docker-compose up -d")
        print("2. Access: http://localhost:8000/docs")
        print("3. Demo: http://localhost:8000/api/v1/forecast/test/demo")
    else:
        print("\n⚠️  Some tests failed. Check dependencies and API.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())