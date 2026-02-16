FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cache buster - forces rebuild of pip install layer
ARG CACHE_BUST=2026-02-16-08:20

RUN pip3 install --no-cache-dir \
    torch==2.1.0 \
    transformers==4.33.2 \
    TTS==0.22.0 \
    flask \
    numpy \
    requests \
    runpod

WORKDIR /app
COPY handler.py .

# Accept Coqui TTS license (non-commercial use)
ENV COQUI_TOS_AGREED=1

EXPOSE 8000

CMD ["python3", "-u", "handler.py"]
