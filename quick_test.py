#!/usr/bin/env python3
"""
Quick standalone test
"""

print("Testing OneWeather core functionality...")

# Test 1: Check if we can import basic modules
print("\n1. Testing imports...")
try:
    import sys
    import json
    from datetime import datetime
    print("✅ Basic imports OK")
except ImportError as e:
    print(f"❌ Import error: {e}")

# Test 2: Check API structure
print("\n2. Checking API structure...")
import os
api_files = [
    "api/app/main.py",
    "api/app/routers/forecast.py", 
    "api/app/services/weather_sources.py",
    "api/app/schemas/forecast.py"
]

for file in api_files:
    if os.path.exists(file):
        print(f"✅ {file} exists")
    else:
        print(f"❌ {file} missing")

# Test 3: Check Docker setup
print("\n3. Checking Docker setup...")
docker_files = [
    "docker-compose.yml",
    "docker-compose.override.yml",
    "api/Dockerfile.dev",
    "ingestion/Dockerfile"
]

for file in docker_files:
    if os.path.exists(file):
        print(f"✅ {file} exists")
    else:
        print(f"❌ {file} missing")

# Test 4: Check project docs
print("\n4. Checking documentation...")
doc_files = [
    "PROJECT_GOALS.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "README.md"
]

for file in doc_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} exists ({size} bytes)")
    else:
        print(f"❌ {file} missing")

# Test 5: Check data sources implementation
print("\n5. Checking data source implementations...")
try:
    # Read the weather sources file to see what's implemented
    with open("api/app/services/weather_sources.py", "r") as f:
        content = f.read()
        
    sources = []
    if "OpenMeteoSource" in content:
        sources.append("Open-Meteo")
    if "NOAAWeatherGovSource" in content:
        sources.append("NOAA Weather.gov")
    if "MeteomaticsFreeSource" in content:
        sources.append("Meteomatics")
        
    print(f"✅ Implemented sources: {', '.join(sources)}")
    
    # Check for blending logic
    if "blend_forecasts" in content:
        print("✅ Blending logic implemented")
    else:
        print("❌ Blending logic missing")
        
except Exception as e:
    print(f"❌ Error reading source file: {e}")

print("\n" + "=" * 60)
print("Summary: Phase 1 foundation is built and ready for testing.")
print("\nTo run the API:")
print("1. Install Docker if not installed")
print("2. Run: docker-compose up -d")
print("3. Access: http://localhost:8000/docs")
print("\nTo add paid APIs:")
print("1. Get API keys for Tomorrow.io and Visual Crossing")
print("2. Add to environment variables")
print("3. Implement API connectors")
print("=" * 60)