FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    torch==2.0.1 \
    transformers==4.33.2 \
    TTS \
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
