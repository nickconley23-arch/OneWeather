#!/bin/bash
echo "🔍 Quick Docker verification..."
echo "=============================="

echo "1. Docker version:"
sudo docker --version

echo ""
echo "2. Docker Compose version:"
sudo docker-compose --version

echo ""
echo "3. Test simple container:"
sudo docker run --rm hello-world 2>&1 | grep -A2 "Hello from Docker"

echo ""
echo "4. Check if we can build ingestion image (this may take a minute)..."
cd ingestion
sudo docker build -t oneweather-test -f Dockerfile . > /tmp/docker-build.log 2>&1 &
BUILD_PID=$!

# Show progress
for i in {1..30}; do
    if ps -p $BUILD_PID > /dev/null; then
        echo -n "."
        sleep 2
    else
        break
    fi
done
echo ""

wait $BUILD_PID
BUILD_RESULT=$?

if [ $BUILD_RESULT -eq 0 ]; then
    echo "✅ Docker build successful!"
    
    echo ""
    echo "5. Test wgrib2 in container:"
    sudo docker run --rm oneweather-test which wgrib2
    
    echo ""
    echo "6. Test Python imports:"
    sudo docker run --rm oneweather-test python3 -c "import requests; import cfgrib; import h3; print('✅ All imports work')"
else
    echo "❌ Docker build failed. Check /tmp/docker-build.log"
    tail -20 /tmp/docker-build.log
fi

echo ""
echo "=============================="
echo "Note: Run 'newgrp docker' or log out/in to use Docker without sudo"