#!/usr/bin/env python3
"""
Simple Gradio GUI for Speaches Speech-to-Text
Connects to local Speaches server at localhost:10300
"""

import gradio as gr
from openai import OpenAI
import os

# Configure OpenAI client to use local Speaches server
client = OpenAI(
    base_url="http://localhost:10300/v1/",
    api_key="cant-be-empty"  # Speaches doesn't need real key
)

MODELS = [
    "Systran/faster-whisper-tiny",
    "Systran/faster-whisper-base",
    "Systran/faster-whisper-small",
    "Systran/faster-whisper-medium",
    "Systran/faster-whisper-large-v3",
]

LANGUAGES = [
    "auto",
    "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
    "ar", "hi", "nl", "pl", "tr", "vi", "th", "id", "ms", "tl",
]

def transcribe_audio(audio_file, model, language, format_type):
    """Transcribe audio file using Speaches"""
    if audio_file is None:
        return "Please upload an audio file"

    try:
        # Open the audio file
        with open(audio_file, "rb") as f:
            # Call Speaches API
            kwargs = {
                "model": model,
                "file": f,
                "response_format": format_type,
            }

            # Only add language if not auto
            if language != "auto":
                kwargs["language"] = language

            response = client.audio.transcriptions.create(**kwargs)

        return response if isinstance(response, str) else response.text

    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Speaches Speech-to-Text") as demo:
    gr.Markdown("# 🎙️ Speaches Speech-to-Text")
    gr.Markdown("Upload an audio file to transcribe using local Whisper models")

    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Audio Input (supports: mp3, mp4, m4a, wav, webm)"
            )

            model_dropdown = gr.Dropdown(
                choices=MODELS,
                value="Systran/faster-whisper-large-v3",
                label="Model"
            )

            language_dropdown = gr.Dropdown(
                choices=LANGUAGES,
                value="auto",
                label="Language (auto-detect or specify)"
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

    # Connect button to function
    transcribe_btn.click(
        fn=transcribe_audio,
        inputs=[audio_input, model_dropdown, language_dropdown, format_dropdown],
        outputs=output_text
    )

    gr.Markdown("""
    ### Tips:
    - **tiny/base**: Fast, lower accuracy
    - **small/medium**: Balanced speed/accuracy
    - **large-v3**: Highest accuracy, slower
    - First use of a model will download it (may take time)
    - Supports: mp3, mp4, wav, m4a, webm
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=10301,
        share=False
    )
