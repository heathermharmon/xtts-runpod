#!/usr/bin/env python3
"""
XTTS Voice Cloning Server for RunPod
Improved version with better error handling and logging
Supports both HTTP API and RunPod Serverless formats
"""

import os
# CRITICAL: Accept Coqui TTS license before importing TTS
# This prevents interactive prompt that crashes Docker containers
os.environ['COQUI_TOS_AGREED'] = '1'

from flask import Flask, request, send_file, jsonify
from TTS.api import TTS
import tempfile
import base64
import time
import torch
import sys

app = Flask(__name__)

# Global variables
tts = None
device = None
load_time = None
model_ready = False

def initialize_model():
    """Initialize XTTS model with proper error handling"""
    global tts, device, load_time, model_ready

    try:
        print("🚀 Loading XTTS v2 model...", flush=True)
        start_time = time.time()

        # Check for GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎮 Using device: {device}", flush=True)

        if device == "cuda":
            print(f"   GPU: {torch.cuda.get_device_name(0)}", flush=True)
            print(f"   CUDA Version: {torch.version.cuda}", flush=True)
            print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB", flush=True)

        # Download and load model
        print("📥 Downloading model (this may take 2-5 minutes on first run)...", flush=True)
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device=="cuda"))

        load_time = time.time() - start_time
        model_ready = True
        print(f"✅ Model loaded successfully in {load_time:.2f}s", flush=True)
        print(f"   Ready to serve requests!", flush=True)

        return True

    except Exception as e:
        print(f"❌ FATAL: Failed to load model: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Initialize model on startup
initialize_model()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - responds immediately once model is loaded"""
    if not model_ready:
        return jsonify({
            'status': 'loading',
            'message': 'Model is still loading, please wait...'
        }), 503

    return jsonify({
        'status': 'healthy',
        'model': 'xtts_v2',
        'device': device,
        'load_time': load_time,
        'model_ready': model_ready
    })

@app.route('/v1/audio/speech', methods=['POST'])
def generate_speech():
    """
    Generate speech using voice cloning

    Request JSON (Standard format):
    {
        "text": "Text to speak",
        "voice_reference": "base64_encoded_audio_data",
        "language": "en"
    }

    Request JSON (RunPod Serverless format):
    {
        "input": {
            "text": "Text to speak",
            "voice_reference": "base64_encoded_audio_data",
            "language": "en"
        }
    }

    Returns: WAV audio file (standard) or JSON with base64 audio (serverless)
    """
    if not model_ready:
        return jsonify({'error': 'Model not ready yet'}), 503

    try:
        data = request.get_json()

        # Support both formats
        if 'input' in data:
            # RunPod Serverless format
            input_data = data['input']
            return_format = 'serverless'
        else:
            # Standard format
            input_data = data
            return_format = 'standard'

        text = input_data.get('text', '')
        voice_ref_b64 = input_data.get('voice_reference', '')
        language = input_data.get('language', 'en')

        if not text:
            error_response = {'error': 'Missing text parameter'}
            if return_format == 'serverless':
                return jsonify({'status': 'FAILED', 'output': error_response}), 400
            return jsonify(error_response), 400

        if not voice_ref_b64:
            error_response = {'error': 'Missing voice_reference parameter'}
            if return_format == 'serverless':
                return jsonify({'status': 'FAILED', 'output': error_response}), 400
            return jsonify(error_response), 400

        print(f"🎤 Generating speech: {len(text)} chars, language={language}", flush=True)

        # Decode reference audio
        try:
            voice_ref_data = base64.b64decode(voice_ref_b64)
        except Exception as e:
            error_response = {'error': f'Invalid base64 voice_reference: {str(e)}'}
            if return_format == 'serverless':
                return jsonify({'status': 'FAILED', 'output': error_response}), 400
            return jsonify(error_response), 400

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as ref_file:
            ref_file.write(voice_ref_data)
            ref_path = ref_file.name

        # Generate speech
        output_path = tempfile.mktemp(suffix='.wav')

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

        print(f"✅ Generated {duration:.2f}s audio in {gen_time:.2f}s ({duration/gen_time:.1f}x realtime)", flush=True)

        # Cleanup reference file
        os.unlink(ref_path)

        # Return based on format
        if return_format == 'serverless':
            # RunPod Serverless format - return base64
            with open(output_path, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode('utf-8')

            os.unlink(output_path)

            return jsonify({
                'status': 'COMPLETED',
                'output': {
                    'success': True,
                    'audio_base64': audio_b64,
                    'duration': duration,
                    'generation_time': gen_time,
                    'text_length': len(text),
                    'device': device,
                    'realtime_factor': duration / gen_time if gen_time > 0 else 0
                }
            })
        else:
            # Standard format - return audio file
            return send_file(output_path, mimetype='audio/wav')

    except Exception as e:
        print(f"❌ Error: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()

        error_response = {'error': str(e)}
        if return_format == 'serverless':
            return jsonify({'status': 'FAILED', 'output': error_response}), 500
        return jsonify(error_response), 500

@app.route('/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': 'XTTS server is running!',
        'device': device,
        'model': 'xtts_v2',
        'model_ready': model_ready,
        'endpoints': ['/health', '/v1/audio/speech', '/test']
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with server info"""
    return jsonify({
        'service': 'XTTS Voice Cloning Server',
        'version': '2.0',
        'model': 'xtts_v2',
        'device': device,
        'model_ready': model_ready,
        'load_time': load_time,
        'endpoints': {
            'health': '/health',
            'generate': '/v1/audio/speech',
            'test': '/test'
        },
        'usage': {
            'method': 'POST',
            'url': '/v1/audio/speech',
            'body': {
                'text': 'Your text here',
                'voice_reference': 'base64_encoded_wav_audio',
                'language': 'en'
            }
        }
    })

if __name__ == '__main__':
    print("🚀 Starting XTTS server on 0.0.0.0:8000...", flush=True)
    print("   Endpoints available:", flush=True)
    print("   - GET  /           (server info)", flush=True)
    print("   - GET  /health     (health check)", flush=True)
    print("   - GET  /test       (simple test)", flush=True)
    print("   - POST /v1/audio/speech (generate TTS)", flush=True)
    print("", flush=True)

    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
