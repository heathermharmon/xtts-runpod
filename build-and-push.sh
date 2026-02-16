#!/bin/bash

# Build and push XTTS Docker image to Docker Hub
# Usage: ./build-and-push.sh [your-dockerhub-username]

DOCKER_USERNAME=${1:-"coharmonify"}
IMAGE_NAME="xtts-runpod"
VERSION="v1.0.0"

echo "🐳 Building XTTS Docker image..."
docker build -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} .
docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION} ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo "📤 Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest

echo "✅ Done!"
echo ""
echo "Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""
echo "Next steps:"
echo "1. Go to RunPod.io → Serverless → New Endpoint"
echo "2. Use image: ${DOCKER_USERNAME}/${IMAGE_NAME}:latest"
echo "3. GPU: RTX 3090 or RTX 4090"
echo "4. Container Disk: 30GB"
echo "5. Get Endpoint ID and add to wp-config.php"
