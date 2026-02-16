#!/usr/bin/env python3
"""
XTTS Voice Cloning Server for RunPod
Supports both synchronous and RunPod Serverless formats
"""

from flask import Flask, request, send_file, jsonify
from TTS.api import TTS
import os
import tempfile
import base64
import time
import torch

app = Flask(__name__)

# Initialize XTTS model (loads on startup)
print("🚀 Loading XTTS v2 model...")
start_time = time.time()

# Check for GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🎮 Using device: {device}")

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=(device=="cuda"))
load_time = time.time() - start_time
print(f"✅ Model loaded in {load_time:.2f}s")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': 'xtts_v2',
        'device': device,
        'load_time': load_time
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

        print(f"🎤 Generating speech: {len(text)} chars, language={language}")

        # Decode reference audio
        voice_ref_data = base64.b64decode(voice_ref_b64)

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

        print(f"✅ Generated {duration:.2f}s audio in {gen_time:.2f}s")

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
                    'device': device
                }
            })
        else:
            # Standard format - return audio file
            return send_file(output_path, mimetype='audio/wav')

    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
        'endpoints': ['/health', '/v1/audio/speech', '/test']
    })

if __name__ == '__main__':
    print("🚀 Starting XTTS server on port 8880...")
    app.run(host='0.0.0.0', port=8880, debug=False)
