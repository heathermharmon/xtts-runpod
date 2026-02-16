FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Coqui TTS and dependencies
RUN pip3 install --no-cache-dir \
    TTS==0.22.0 \
    flask==3.0.0 \
    numpy==1.24.3 \
    torch==2.1.0 \
    torchaudio==2.1.0

# Create app directory
WORKDIR /app

# Copy XTTS API server
COPY xtts_server.py .

# Pre-download XTTS model to speed up cold starts
RUN python3 -c "from TTS.api import TTS; TTS(model_name='tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)"

# Expose port
EXPOSE 8880

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8880/health')"

# Run server
CMD ["python3", "xtts_server.py"]
