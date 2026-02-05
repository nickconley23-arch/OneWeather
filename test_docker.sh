#!/bin/bash
# Test script for OneWeather Docker setup

set -e

echo "🔧 Testing OneWeather Docker setup..."
echo "======================================"

# Test 1: Check Docker is available
echo "1. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker is available"
else
    echo "   ❌ Docker not found. Please install Docker first."
    exit 1
fi

# Test 2: Check Docker Compose
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "   ✅ Docker Compose is available"
else
    echo "   ❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Test 3: Build ingestion image
echo "3. Building ingestion Docker image..."
cd ingestion
docker build -t oneweather-ingestion:test -f Dockerfile .
if [ $? -eq 0 ]; then
    echo "   ✅ Ingestion image built successfully"
else
    echo "   ❌ Failed to build ingestion image"
    exit 1
fi
cd ..

# Test 4: Test wgrib2 in container
echo "4. Testing wgrib2 in container..."
docker run --rm oneweather-ingestion:test which wgrib2
if [ $? -eq 0 ]; then
    echo "   ✅ wgrib2 available in container"
else
    echo "   ❌ wgrib2 not found in container"
    exit 1
fi

# Test 5: Test Python dependencies
echo "5. Testing Python dependencies..."
docker run --rm oneweather-ingestion:test python3 -c "import requests, cfgrib, h3; print('✅ All Python imports successful')"
if [ $? -eq 0 ]; then
    echo "   ✅ Python dependencies installed"
else
    echo "   ❌ Python dependency check failed"
    exit 1
fi

# Test 6: Test GFS POC script
echo "6. Testing GFS POC script..."
docker run --rm oneweather-ingestion:test python3 gfs_poc.py --help
if [ $? -eq 0 ]; then
    echo "   ✅ GFS POC script works"
else
    echo "   ❌ GFS POC script failed"
    exit 1
fi

echo ""
echo "======================================"
echo "🎉 All Docker tests passed!"
echo ""
echo "Next steps:"
echo "1. Run 'make dev' to start development environment"
echo "2. Run 'make monitor' to see dashboard URLs"
echo "3. Run 'make ingest-gfs-test' to test GFS ingestion"
echo ""
echo "For production deployment to Railway/Vercel:"
echo "- The Dockerfile is production-ready"
echo "- Use docker-compose.yml for multi-service deployment"
echo "- Environment variables in .env.example"