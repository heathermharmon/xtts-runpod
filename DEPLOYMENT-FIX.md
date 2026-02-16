# XTTS RunPod Deployment Fix

## Problems Identified

1. **Missing `requests` library** - Healthcheck imports it but it wasn't installed
2. **Model loading timeout** - XTTS v2 takes 2-5 minutes to download (~2GB), but healthcheck only waited 60 seconds
3. **No RunPod Handler** - RunPod Serverless needs a `handler.py` with proper `handler()` function

## Files Fixed

- ✅ `Dockerfile.fixed` - Added `requests`, `curl`, `runpod` libraries + 300s healthcheck start period
- ✅ `handler.py` - NEW RunPod Serverless handler (recommended for serverless workers)
- ✅ `xtts_server_improved.py` - Better Flask server with improved logging and error handling

## Deployment Options

### Option 1: RunPod Serverless (Recommended)
Use `handler.py` for auto-scaling serverless workers.

**Build:**
```bash
cd /home/elevatf7/staging/xtts-test/docker

# Update Dockerfile to use handler
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

# RunPod Serverless uses port 8000 by default
EXPOSE 8000

CMD ["python3", "-u", "handler.py"]
EOF

# Build and push
docker build -t ghcr.io/heathermharmon/xtts-runpod:latest .
docker push ghcr.io/heathermharmon/xtts-runpod:latest
```

**RunPod Template Settings:**
- Docker Image: `ghcr.io/heathermharmon/xtts-runpod:latest`
- GPU: 24GB VRAM (A5000/A6000/RTX 4090/RTX 6000 Ada)
- Container Disk: 20GB
- Max Workers: As needed
- Idle Timeout: 5 seconds
- **No custom healthcheck needed** (RunPod Serverless handles this automatically)

### Option 2: RunPod HTTP API (Traditional)
Use `xtts_server_improved.py` for always-on HTTP API workers.

**Build:**
```bash
cd /home/elevatf7/staging/xtts-test/docker

# Use the fixed Dockerfile
cp Dockerfile.fixed Dockerfile

# Update to use improved server
sed -i 's/xtts_server\.py/xtts_server_improved.py/g' Dockerfile

# Build and push
docker build -t ghcr.io/heathermharmon/xtts-runpod:http-api .
docker push ghcr.io/heathermharmon/xtts-runpod:http-api
```

**RunPod Template Settings:**
- Docker Image: `ghcr.io/heathermharmon/xtts-runpod:http-api`
- GPU: 24GB VRAM
- Container Disk: 20GB
- **Template Type: HTTP**
- Expose HTTP Ports: 8000
- Healthcheck: Container healthcheck (already in Dockerfile)

## Testing After Deployment

### Test Serverless Worker:
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello, this is a test of voice cloning!",
      "voice_reference": "BASE64_ENCODED_WAV_AUDIO_HERE",
      "language": "en"
    }
  }'
```

### Test HTTP API Worker:
```bash
# Health check
curl http://YOUR_WORKER_IP:8000/health

# Generate speech
curl -X POST http://YOUR_WORKER_IP:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test!",
    "voice_reference": "BASE64_ENCODED_WAV_AUDIO_HERE",
    "language": "en"
  }' \
  --output test_output.wav
```

## Expected Worker Logs

Successful startup should show:
```
🚀 Loading XTTS v2 model...
🎮 Using device: cuda
   GPU: NVIDIA RTX A5000
   CUDA Version: 11.8
   Memory: 24.0 GB
📥 Downloading model (this may take 2-5 minutes on first run)...
✅ Model loaded successfully in 142.35s
   Ready to serve requests!
```

## Common Issues

**"Worker unhealthy"** - Model loading timed out
- Solution: Increase healthcheck `start-period` to 300s (already done in fixed Dockerfile)

**"Import error: No module named 'requests'"**
- Solution: Add `requests` to pip install (already done in fixed Dockerfile)

**"Model download stuck"**
- Solution: Check internet connectivity, ensure RunPod datacenter can reach Hugging Face

**"CUDA out of memory"**
- Solution: Use GPU with 24GB VRAM minimum (not 16GB)

## Integration with CoHarmonify

Update your PHP test file at `/home/elevatf7/staging/xtts-test/test-voice-clone.php`:

```php
<?php
// RunPod Serverless Endpoint
$endpoint = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run";
$api_key = "YOUR_RUNPOD_API_KEY";

// Voice reference (sample WAV audio encoded as base64)
$voice_reference = base64_encode(file_get_contents('/path/to/voice_sample.wav'));

$data = [
    'input' => [
        'text' => 'This is a test of the XTTS voice cloning system.',
        'voice_reference' => $voice_reference,
        'language' => 'en'
    ]
];

$ch = curl_init($endpoint);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Authorization: Bearer ' . $api_key,
    'Content-Type: application/json'
]);

$response = curl_exec($ch);
$result = json_decode($response, true);

if ($result['status'] === 'COMPLETED') {
    $audio_base64 = $result['output']['audio_base64'];
    $audio_data = base64_decode($audio_base64);

    // Save or stream audio
    file_put_contents('output.wav', $audio_data);
    echo "✅ Voice cloning successful! Saved to output.wav";
} else {
    echo "❌ Error: " . print_r($result, true);
}
```

## Next Steps

1. Choose deployment option (Serverless recommended)
2. Build and push Docker image
3. Create RunPod template with fixed settings
4. Deploy worker and test
5. Monitor logs for successful model loading
6. Integrate endpoint into CoHarmonify audiobook platform
