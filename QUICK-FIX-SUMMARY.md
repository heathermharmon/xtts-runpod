# 🎯 XTTS RunPod "Unhealthy Worker" Fix - SOLVED

## The Problem
Your RunPod workers were failing with "unhealthy" status because:

1. ❌ **Missing Python library**: Healthcheck used `requests` but it wasn't installed
2. ❌ **Model loading timeout**: XTTS v2 model takes 2-5 minutes to download (~2GB), but healthcheck only waited 60 seconds
3. ❌ **Wrong architecture**: Missing RunPod Serverless handler for optimal performance

## The Solution - 3 New Files

### ✅ 1. `handler.py` (NEW - RunPod Serverless Handler)
- Proper RunPod Serverless architecture
- Pre-loads model once at worker startup
- Returns base64 audio in RunPod format
- **USE THIS for serverless endpoints**

### ✅ 2. `xtts_server_improved.py` (IMPROVED Flask Server)
- Better error handling and logging
- Health check that reports model loading status
- Supports both RunPod and standard formats
- **USE THIS for HTTP API endpoints**

### ✅ 3. `Dockerfile.fixed` (CORRECTED)
- Installs missing libraries: `requests`, `curl`, `runpod`
- Increases healthcheck `start-period` from 60s → 300s
- Proper CMD for each deployment type

## Quick Start - Deploy in 5 Minutes

### Step 1: Build the Fixed Image
```bash
cd /home/elevatf7/staging/xtts-test/docker
./build-fixed.sh
```
Choose: **Option 1 (Serverless)** ← RECOMMENDED

### Step 2: Push to Registry
```bash
docker push ghcr.io/heathermharmon/xtts-runpod:latest
```

### Step 3: Create RunPod Template
Go to RunPod Dashboard → Templates → New Template:

**Settings:**
- Name: `XTTS Voice Cloning - FIXED`
- Docker Image: `ghcr.io/heathermharmon/xtts-runpod:latest`
- GPU Type: 24GB VRAM (RTX A5000/A6000/4090/6000 Ada)
- Container Disk: 20 GB
- Template Type: **Serverless**
- Volume Path: `/workspace` (optional)

**Advanced Settings:**
- Max Workers: 3 (or as needed)
- Idle Timeout: 5 seconds
- Active Timeout: 300 seconds (5 minutes)

### Step 4: Deploy Worker
- Click "Deploy" on your new template
- Wait 5-10 minutes for first model download
- Watch logs for: `✅ Model loaded successfully`

### Step 5: Test the Endpoint
```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "This is a test!",
      "voice_reference": "BASE64_AUDIO_HERE",
      "language": "en"
    }
  }'
```

## Expected Logs (Healthy Worker)
```
🚀 [HANDLER] Loading XTTS v2 model...
🎮 [HANDLER] Using device: cuda
   GPU: NVIDIA RTX A5000
   CUDA Version: 11.8
   Memory: 24.0 GB
📥 Downloading model (this may take 2-5 minutes on first run)...
✅ [HANDLER] Model loaded in 142.35s
🚀 [HANDLER] Starting RunPod Serverless Handler...
```

## Integration with Your Audiobook Platform

Update `/home/elevatf7/staging/xtts-test/test-voice-clone.php`:

```php
<?php
$runpod_endpoint = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run";
$runpod_api_key = "YOUR_RUNPOD_API_KEY";

// Get voice sample from user upload
$voice_sample = base64_encode(file_get_contents($_FILES['voice_sample']['tmp_name']));

$payload = [
    'input' => [
        'text' => $_POST['text_to_speak'],
        'voice_reference' => $voice_sample,
        'language' => 'en'
    ]
];

$ch = curl_init($runpod_endpoint);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Authorization: Bearer ' . $runpod_api_key,
    'Content-Type: application/json'
]);

$response = curl_exec($ch);
$result = json_decode($response, true);

if ($result['status'] === 'COMPLETED') {
    // Decode base64 audio and save/stream
    $audio_data = base64_decode($result['output']['audio_base64']);
    header('Content-Type: audio/wav');
    echo $audio_data;
} else {
    http_response_code(500);
    echo json_encode(['error' => $result['output']['error']]);
}
```

## Why This Fixes the "Unhealthy" Status

| Issue | Before | After |
|-------|--------|-------|
| **Missing library** | `import requests` → crash | ✅ `requests` installed |
| **Healthcheck timeout** | Model loads in 120s, healthcheck fails at 60s | ✅ Healthcheck waits 300s |
| **Architecture** | Generic Flask server | ✅ RunPod Serverless handler |
| **Error handling** | Basic error messages | ✅ Detailed logging + error handling |
| **Model loading** | No status reporting | ✅ `/health` endpoint shows loading status |

## Files Location

All fixed files are in: `/home/elevatf7/staging/xtts-test/docker/`

- ✅ `handler.py` - RunPod Serverless (RECOMMENDED)
- ✅ `xtts_server_improved.py` - HTTP API alternative
- ✅ `Dockerfile.fixed` - Corrected Dockerfile
- ✅ `build-fixed.sh` - Automated build script
- ✅ `DEPLOYMENT-FIX.md` - Detailed deployment guide
- ✅ `QUICK-FIX-SUMMARY.md` - This file

## Need Help?

**Common Issues:**

1. **"Worker still unhealthy"**
   - Check logs for actual error (click "Logs" in RunPod dashboard)
   - Ensure you pushed the NEW image: `docker push ghcr.io/heathermharmon/xtts-runpod:latest`
   - Verify GPU has 24GB VRAM (not 16GB)

2. **"Model download stuck"**
   - RunPod datacenter might have slow connection to Hugging Face
   - Try different region/datacenter
   - First download takes 5-10 minutes (subsequent starts: 30-60 seconds)

3. **"Container keeps restarting"**
   - Check RunPod template has enough Container Disk (20GB minimum)
   - Verify CUDA version matches GPU (11.8 works with most modern GPUs)

4. **"No such image"**
   - Make sure you pushed: `docker push ghcr.io/heathermharmon/xtts-runpod:latest`
   - Verify image is public on GitHub Container Registry
   - Check for typos in image name

---

**Ready to deploy?** Run: `cd /home/elevatf7/staging/xtts-test/docker && ./build-fixed.sh`
