#!/usr/bin/env python3
"""
Simple Gradio GUI for Speech-to-Text using Ollama
"""

import gradio as gr
import subprocess
import tempfile
import os

def transcribe_audio(audio_file):
    """Transcribe audio using Ollama"""
    if audio_file is None:
        return "Please upload an audio file"

    try:
        # Use Ollama's whisper model
        result = subprocess.run(
            ['ollama', 'run', 'whisper', audio_file],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"

    except Exception as e:
        return f"Error: {str(e)}"

# Create simple Gradio interface
with gr.Blocks(title="Whisper Speech-to-Text") as demo:
    gr.Markdown("# 🎙️ Speech-to-Text via Ollama")
    gr.Markdown("Upload audio (mp3, m4a, wav, webm) to transcribe")

    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Audio Input"
            )
            transcribe_btn = gr.Button("Transcribe", variant="primary")

        with gr.Column():
            output_text = gr.Textbox(
                label="Transcription",
                lines=20
            )

    transcribe_btn.click(
        fn=transcribe_audio,
        inputs=audio_input,
        outputs=output_text
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=10301,
        share=False
    )
