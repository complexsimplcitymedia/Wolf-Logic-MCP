#!/usr/bin/env python3
"""
Visual Agent - The Lighting Department
Single vision model: LLaVA 13b solo
Push the GPU. No conservative bullshit.

Usage:
    from visual_agent import analyze_frame, analyze_frames_batch
"""

import os
import ollama
import threading

print_lock = threading.Lock()
def safe_print(msg):
    with print_lock:
        print(msg)

# Single model per video - full context
VISION_MODELS = ["benzie/llava-phi-3:latest"]


def analyze_frame(frame_path: str, position: int = 0, timestamp_str: str = "0:00", model: str = None) -> dict:
    """Analyze a single frame with specified vision model"""
    use_model = model or VISION_MODELS[0]
    try:
        response = ollama.chat(
            model=use_model,
            messages=[{
                'role': 'user',
                'content': 'What is in this frame? One sentence only.',
                'images': [frame_path]
            }]
        )

        return {
            "position": position,
            "timestamp_str": timestamp_str,
            "analysis": response['message']['content'],
            "model": use_model,
            "status": "success"
        }

    except Exception as e:
        return {
            "position": position,
            "timestamp_str": timestamp_str,
            "analysis": "",
            "model": use_model,
            "status": "error",
            "error": str(e)
        }


def analyze_frames_batch(frames: list, max_workers: int = 6) -> list:
    """
    Analyze multiple frames with dual vision models alternating.

    Odd frames → LLaVA 13b
    Even frames → Llama 3.2 Vision

    Push the GPU. No conservative bullshit.

    frames: list of dicts with 'path', 'position', 'timestamp_str'
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    safe_print(f"[LIGHTING] Analyzing {len(frames)} frames with dual models: {VISION_MODELS}")
    safe_print(f"[LIGHTING] Workers: {max_workers} | Alternating between models")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                analyze_frame,
                f['path'],
                f.get('position', i),
                f.get('timestamp_str', '0:00'),
                VISION_MODELS[i % len(VISION_MODELS)]  # Alternate between models
            ): i
            for i, f in enumerate(frames)
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            model_short = result.get('model', '').split(':')[0]
            if result['status'] == 'success':
                safe_print(f"  [LIGHTING] Frame {result['position']} @ {result['timestamp_str']} [{model_short}] ✓")
            else:
                safe_print(f"  [LIGHTING] Frame {result['position']} [{model_short}] failed: {result.get('error', 'unknown')}")

    # Sort by position
    results.sort(key=lambda x: x['position'])
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = analyze_frame(sys.argv[1])
        print(result['analysis'])
