#!/usr/bin/env python3
"""
Gradio GUI for Speech Note Whisper
Uses Speech Note's ROCm-accelerated Whisper via D-Bus
"""

import gradio as gr
import subprocess
import dbus
import tempfile
import shutil
import os

# Map to Speech Note model IDs
MODEL_MAP = {
    "tiny": "en_whisper_tiny",
    "base": "en_whisper_base",
    "small": "en_whisper_small",
    "medium": "en_whisper_medium",
    "distil-small": "en_whisper_distil_small",
    "distil-medium": "en_whisper_distil_medium",
    "distil-large-v2": "en_whisper_distil_large2",
    "distil-large-v3": "en_whisper_distil_large3",
}

MODELS = list(MODEL_MAP.keys())

LANGUAGES = [
    "auto",
    "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
    "ar", "hi", "nl", "pl", "tr", "vi", "th", "id", "ms", "tl",
]

def transcribe_audio(audio_file, model_size, language, format_type):
    """Transcribe audio file using Speech Note's Whisper"""
    if audio_file is None:
        return "Please upload an audio file"

    try:
        # Get Speech Note model ID
        model_id = MODEL_MAP.get(model_size, "en_whisper_base")

        # Set the model via D-Bus
        bus = dbus.SessionBus()
        proxy = bus.get_object("net.mkiol.SpeechNote", "/net/mkiol/SpeechNote")

        # Set STT model
        subprocess.run([
            "flatpak", "run", "net.mkiol.SpeechNote",
            "--action", "set-stt-model",
            "--id", model_id
        ], check=False, capture_output=True)

        # Copy file to temp location Speech Note can access
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, os.path.basename(audio_file))
        shutil.copy2(audio_file, temp_file)

        # Process audio file with Speech Note
        result = subprocess.run([
            "flatpak", "run", "net.mkiol.SpeechNote",
            temp_file
        ], capture_output=True, text=True, timeout=300)

        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

        if result.returncode == 0:
            # Speech Note returns transcription
            transcription = result.stdout.strip()

            # Format based on requested output
            if format_type == "text":
                return transcription
            elif format_type in ["json", "verbose_json"]:
                import json
                return json.dumps({"text": transcription}, indent=2)
            elif format_type == "srt":
                return f"1\n00:00:00,000 --> 99:59:59,999\n{transcription}\n\n"
            elif format_type == "vtt":
                return f"WEBVTT\n\n00:00:00.000 --> 99:59:59.999\n{transcription}\n\n"
            else:
                return transcription
        else:
            return f"Error: {result.stderr}"

    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Whisper Transcription") as demo:
    gr.Markdown("# 🎙️ Whisper Speech-to-Text")
    gr.Markdown("Upload audio to transcribe using Speech Note (AMD RX 7900 XT ROCm accelerated)")

    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Audio Input (mp3, mp4, m4a, wav, webm)"
            )

            model_dropdown = gr.Dropdown(
                choices=MODELS,
                value="distil-large-v3",
                label="Model"
            )

            language_dropdown = gr.Dropdown(
                choices=LANGUAGES,
                value="auto",
                label="Language"
            )

            format_dropdown = gr.Dropdown(
                choices=["text", "json", "verbose_json", "srt", "vtt"],
                value="text",
                label="Output Format"
            )

            transcribe_btn = gr.Button("Transcribe", variant="primary")

        with gr.Column():
            output_text = gr.Textbox(
                label="Transcription",
                lines=20
            )

    transcribe_btn.click(
        fn=transcribe_audio,
        inputs=[audio_input, model_dropdown, language_dropdown, format_dropdown],
        outputs=output_text
    )

    gr.Markdown("""
    ### Models (ROCm GPU-accelerated via Speech Note):
    - **tiny/base**: Fastest
    - **small/medium**: Balanced
    - **distil-large-v2/v3**: Best accuracy (distilled)

    Uses Speech Note's pre-downloaded models with AMD ROCm acceleration.
    Supports: mp3, mp4, m4a, wav, webm, flac
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=10301,
        share=False
    )
