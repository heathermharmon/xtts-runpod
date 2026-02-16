#!/usr/bin/env python3
"""
RunPod Serverless Handler for XTTS Voice Cloning
This is the entry point for RunPod Serverless workers
"""

import os
# CRITICAL: Accept Coqui TTS license before importing TTS
# This prevents interactive prompt that crashes Docker containers
os.environ['COQUI_TOS_AGREED'] = '1'

import runpod
from TTS.api import TTS
import tempfile
import base64
import time
import torch

# Initialize XTTS model (loads once at worker startup)
print("🚀 [HANDLER] Loading XTTS v2 model...")
start_time = time.time()

# Check for GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🎮 [HANDLER] Using device: {device}")

# Pre-download model to avoid timeout on first request
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device=="cuda"))
load_time = time.time() - start_time
print(f"✅ [HANDLER] Model loaded in {load_time:.2f}s")

def handler(event):
    """
    RunPod Serverless Handler Function

    Expected input format:
    {
        "input": {
            "text": "Text to speak",
            "voice_reference": "base64_encoded_audio_data",
            "language": "en"  (optional, default: "en")
        }
    }

    Returns:
    {
        "success": True,
        "audio_base64": "base64_encoded_wav_audio",
        "duration": 5.23,
        "generation_time": 2.15,
        "text_length": 123,
        "device": "cuda"
    }
    """
    try:
        input_data = event.get('input', {})

        text = input_data.get('text', '')
        voice_ref_b64 = input_data.get('voice_reference', '')
        language = input_data.get('language', 'en')

        # Validation
        if not text:
            return {'error': 'Missing text parameter', 'success': False}

        if not voice_ref_b64:
            return {'error': 'Missing voice_reference parameter', 'success': False}

        print(f"🎤 [HANDLER] Generating speech: {len(text)} chars, language={language}")

        # Decode reference audio
        voice_ref_data = base64.b64decode(voice_ref_b64)

        # Save reference audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as ref_file:
            ref_file.write(voice_ref_data)
            ref_path = ref_file.name

        # Generate output path
        output_path = tempfile.mktemp(suffix='.wav')

        # Generate speech
        gen_start = time.time()
        tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=ref_path,
            language=language
        )
        gen_time = time.time() - gen_start

        # Get audio duration
        import wave
        with wave.open(output_path, 'r') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)

        print(f"✅ [HANDLER] Generated {duration:.2f}s audio in {gen_time:.2f}s")

        # Read generated audio and encode to base64
        with open(output_path, 'rb') as f:
            audio_b64 = base64.b64encode(f.read()).decode('utf-8')

        # Cleanup temporary files
        os.unlink(ref_path)
        os.unlink(output_path)

        # Return result in RunPod format
        return {
            'success': True,
            'audio_base64': audio_b64,
            'duration': duration,
            'generation_time': gen_time,
            'text_length': len(text),
            'device': device,
            'model': 'xtts_v2'
        }

    except Exception as e:
        print(f"❌ [HANDLER] Error: {str(e)}")
        return {
            'error': str(e),
            'success': False
        }

if __name__ == '__main__':
    print("🚀 [HANDLER] Starting RunPod Serverless Handler...")
    runpod.serverless.start({"handler": handler})
