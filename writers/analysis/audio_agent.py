#!/usr/bin/env python3
"""
Audio Agent - Post-Production Sound Department
One job: Analyze audio characteristics. Mood, energy, tempo. That's it.

Usage:
    from audio_agent import analyze_audio
"""

import numpy as np


def analyze_audio(audio_path: str, duration_limit: int = 120) -> dict:
    """
    Analyze audio characteristics

    Returns mood indicators, energy profile, tempo estimate
    """
    analysis = {
        "has_music": False,
        "energy_profile": "unknown",
        "tempo_estimate": None,
        "mood_indicators": [],
        "status": "success"
    }

    try:
        import librosa

        print(f"[POST-SOUND] Analyzing audio characteristics...")

        # Load audio (limit duration for efficiency)
        y, sr = librosa.load(audio_path, sr=22050, duration=duration_limit)

        # Energy analysis
        rms = librosa.feature.rms(y=y)[0]
        avg_energy = float(np.mean(rms))
        energy_variance = float(np.var(rms))

        if avg_energy > 0.1:
            analysis["energy_profile"] = "high"
        elif avg_energy > 0.05:
            analysis["energy_profile"] = "medium"
        else:
            analysis["energy_profile"] = "low"

        # Tempo estimation
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Handle both scalar and array returns
            if hasattr(tempo, '__len__'):
                tempo = float(tempo[0]) if len(tempo) > 0 else 0
            else:
                tempo = float(tempo)
            if tempo > 0:
                analysis["tempo_estimate"] = round(tempo)
                analysis["has_music"] = True
        except:
            pass

        # Spectral analysis for mood
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        avg_centroid = float(np.mean(spectral_centroid))

        if avg_centroid > 3000:
            analysis["mood_indicators"].append("bright/energetic")
        elif avg_centroid < 1500:
            analysis["mood_indicators"].append("dark/mellow")
        else:
            analysis["mood_indicators"].append("balanced")

        if energy_variance > 0.01:
            analysis["mood_indicators"].append("dynamic")
        else:
            analysis["mood_indicators"].append("consistent")

        print(f"[POST-SOUND] Energy: {analysis['energy_profile']}, Tempo: {analysis['tempo_estimate']} BPM")

    except ImportError:
        analysis["status"] = "error"
        analysis["error"] = "librosa not installed"
        print("[POST-SOUND] Error: librosa not installed")
    except Exception as e:
        analysis["status"] = "error"
        analysis["error"] = str(e)
        print(f"[POST-SOUND] Error: {e}")

    return analysis


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        result = analyze_audio(sys.argv[1])
        print(json.dumps(result, indent=2))
