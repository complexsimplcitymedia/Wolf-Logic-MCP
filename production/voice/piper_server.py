#!/usr/bin/env python3
"""
Piper Text-to-Speech Server for Voice AI Agents
Runs on port 5050, serves high-quality English voice synthesis
"""

import json
import logging
import os
import sys
import wave
from io import BytesIO
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from piper.voice import PiperVoice
from piper.config import SynthesisConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Configuration
VOICE_DIR = Path(__file__).parent / "models"
MODEL_NAME = "en_US-ljspeech-high"
MODEL_PATH = VOICE_DIR / f"{MODEL_NAME}.onnx"
CONFIG_PATH = VOICE_DIR / f"{MODEL_NAME}.onnx.json"
PORT = 5050

# Global voice instance
voice = None


def load_voice():
    """Load the Piper voice model"""
    global voice
    try:
        if not MODEL_PATH.exists():
            logger.error(f"Model not found at {MODEL_PATH}")
            sys.exit(1)

        logger.info(f"Loading voice model from {MODEL_PATH}")
        voice = PiperVoice.load(str(MODEL_PATH), config_path=str(CONFIG_PATH) if CONFIG_PATH.exists() else None)
        logger.info(f"Voice model loaded successfully: {MODEL_NAME}")
        return True
    except Exception as e:
        logger.error(f"Failed to load voice model: {e}")
        sys.exit(1)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': MODEL_NAME,
        'voice_loaded': voice is not None
    }), 200


@app.route('/synthesize', methods=['POST'])
def synthesize():
    """
    Synthesize text to speech

    Request JSON:
    {
        "text": "Text to synthesize",
        "speaker_id": 0,  # optional, default 0
        "length_scale": 1.0,  # optional, controls speed (< 1.0 = faster)
        "noise_scale": 0.667,  # optional, controls variation
        "volume": 1.0  # optional, volume multiplier
    }

    Response: WAV audio file
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'Missing required field: text'}), 400

        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400

        # Optional parameters
        speaker_id = data.get('speaker_id', None)
        length_scale = float(data.get('length_scale', 1.0))
        noise_scale = float(data.get('noise_scale', 0.667))
        volume = float(data.get('volume', 1.0))

        logger.info(f"Synthesizing text: {text[:100]}...")

        # Create synthesis config
        config = SynthesisConfig(
            speaker_id=speaker_id,
            length_scale=length_scale,
            noise_scale=noise_scale,
            volume=volume
        )

        # Synthesize audio - get audio chunks
        wav_file = BytesIO()
        audio_chunks = list(voice.synthesize(text, config))

        if not audio_chunks:
            return jsonify({'error': 'No audio generated'}), 500

        # Get audio parameters from first chunk
        first_chunk = audio_chunks[0]
        sample_rate = first_chunk.sample_rate
        channels = first_chunk.sample_channels
        sample_width = first_chunk.sample_width

        with wave.open(wav_file, 'wb') as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(sample_width)
            wav.setframerate(sample_rate)

            # Write all audio chunks
            for chunk in audio_chunks:
                wav.writeframes(chunk.audio_int16_bytes)

        # Reset position to beginning for reading
        wav_file.seek(0)

        logger.info(f"Successfully synthesized {len(text)} characters")

        return send_file(
            wav_file,
            mimetype='audio/wav',
            as_attachment=True,
            download_name='speech.wav'
        )

    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON'}), 400
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Synthesis error: {e}", exc_info=True)
        return jsonify({'error': f'Synthesis failed: {str(e)}'}), 500


@app.route('/models', methods=['GET'])
def get_models():
    """Get information about available models"""
    return jsonify({
        'models': [
            {
                'name': MODEL_NAME,
                'language': 'en_US',
                'quality': 'high',
                'sample_rate': 22050,
                'speakers': 1,
                'loaded': voice is not None
            }
        ]
    }), 200


@app.route('/version', methods=['GET'])
def get_version():
    """Get server version information"""
    try:
        import piper
        piper_version = getattr(piper, '__version__', 'unknown')
    except:
        piper_version = 'unknown'

    return jsonify({
        'server': 'piper-voice-server',
        'version': '1.0.0',
        'piper_version': piper_version,
        'model': MODEL_NAME
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def main():
    """Main entry point"""
    logger.info("Starting Piper Text-to-Speech Server")
    logger.info(f"Model directory: {VOICE_DIR}")
    logger.info(f"Model name: {MODEL_NAME}")

    # Load voice model
    load_voice()

    # Start Flask server
    logger.info(f"Starting Flask server on 0.0.0.0:{PORT}")
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    main()
