#!/bin/bash
# Check if the new Docker image with TOS fix is ready on ghcr.io

echo "🔍 Checking if new XTTS Docker image is available..."
echo ""

# Try to pull the latest image info
docker manifest inspect ghcr.io/heathermharmon/xtts-runpod:main-aec0837 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ NEW IMAGE IS READY!"
    echo "   Image: ghcr.io/heathermharmon/xtts-runpod:main-aec0837"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Go to RunPod Dashboard → Your Serverless Endpoint"
    echo "2. Terminate ALL existing unhealthy workers"
    echo "3. Purge the 8 jobs in queue"
    echo "4. Update template Docker image to: ghcr.io/heathermharmon/xtts-runpod:main-aec0837"
    echo "5. REMOVE port 8000 from HTTP Ports (Serverless doesn't need it)"
    echo "6. Deploy fresh workers"
    echo ""
else
    echo "⏳ Image still building..."
    echo "   Check build status: https://github.com/heathermharmon/xtts-runpod/actions"
    echo "   Run this script again in a few minutes"
    echo ""
fi
