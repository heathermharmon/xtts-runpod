#!/bin/bash
# Build XTTS Docker image and push to GitHub Container Registry
# Matching your existing Kokoro setup (ghcr.io)

set -e

GITHUB_USERNAME="remsky"  # Change if different
IMAGE_NAME="xtts-fastapi-gpu"
VERSION="v1.0.0"

echo "🐳 Building XTTS Docker image..."
cd "$(dirname "$0")"

docker build -t ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION} .
docker tag ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION} ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:latest

echo "📤 Pushing to GitHub Container Registry..."
echo "Make sure you're logged in: docker login ghcr.io -u ${GITHUB_USERNAME}"

docker push ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION}
docker push ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:latest

echo "✅ Done!"
echo ""
echo "Image: ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
echo ""
echo "Next: Create RunPod Serverless endpoint with this image"
