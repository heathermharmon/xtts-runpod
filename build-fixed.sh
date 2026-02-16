#!/bin/bash
set -e

echo "🔧 XTTS RunPod Docker Build - FIXED VERSION"
echo "============================================"
echo ""

# Check which deployment type
echo "Select deployment type:"
echo "1) RunPod Serverless (handler.py) - RECOMMENDED"
echo "2) RunPod HTTP API (xtts_server_improved.py)"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "📦 Building RunPod SERVERLESS image..."
    echo ""

    cat > Dockerfile << 'EOF'
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    TTS \
    flask \
    numpy \
    requests \
    torch \
    runpod

WORKDIR /app
COPY handler.py .

EXPOSE 8000

CMD ["python3", "-u", "handler.py"]
EOF

    IMAGE_TAG="ghcr.io/heathermharmon/xtts-runpod:latest"

elif [ "$choice" = "2" ]; then
    echo ""
    echo "📦 Building RunPod HTTP API image..."
    echo ""

    cat > Dockerfile << 'EOF'
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    TTS \
    flask \
    numpy \
    requests \
    torch \
    runpod

WORKDIR /app
COPY xtts_server_improved.py .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "-u", "xtts_server_improved.py"]
EOF

    IMAGE_TAG="ghcr.io/heathermharmon/xtts-runpod:http-api"

else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi

echo "🔨 Building Docker image: $IMAGE_TAG"
echo ""
docker build -t "$IMAGE_TAG" .

echo ""
echo "✅ Build complete!"
echo ""
echo "To push to GitHub Container Registry:"
echo "  docker push $IMAGE_TAG"
echo ""
echo "To test locally (requires NVIDIA GPU):"
echo "  docker run --rm --gpus all -p 8000:8000 $IMAGE_TAG"
echo ""
