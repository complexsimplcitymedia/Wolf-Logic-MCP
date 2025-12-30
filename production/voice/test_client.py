#!/usr/bin/env python3
"""
Test client for Piper Voice Server
Demonstrates how to interact with the text-to-speech API
"""

import requests
import json
import sys
from pathlib import Path

SERVER_URL = "http://localhost:5050"
OUTPUT_DIR = Path("/tmp")


def test_health():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_models():
    """Test models endpoint"""
    print("\nTesting models endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/models")
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_version():
    """Test version endpoint"""
    print("\nTesting version endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/version")
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_synthesize():
    """Test text-to-speech synthesis"""
    print("\nTesting synthesis endpoint...")

    test_texts = [
        "This is an AI agent calling on behalf of the Wolf. When can we schedule an interview?",
        "Hello there! How are you today?",
        "The quick brown fox jumps over the lazy dog.",
    ]

    for i, text in enumerate(test_texts):
        print(f"\nSynthesis test {i+1}: '{text[:50]}...'")

        payload = {
            "text": text,
            "length_scale": 1.0,
            "noise_scale": 0.667,
            "volume": 1.0
        }

        try:
            response = requests.post(
                f"{SERVER_URL}/synthesize",
                json=payload,
                timeout=30
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                # Save WAV file
                output_file = OUTPUT_DIR / f"test_{i+1}.wav"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"Saved to: {output_file}")
                print(f"File size: {len(response.content)} bytes")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Error: {e}")
            return False

    return True


def test_synthesis_with_params():
    """Test synthesis with different parameters"""
    print("\nTesting synthesis with various parameters...")

    text = "Speed test: This is a faster version of the AI agent."

    params_list = [
        {"length_scale": 0.8, "label": "faster"},
        {"length_scale": 1.2, "label": "slower"},
        {"volume": 0.5, "label": "quieter"},
        {"volume": 1.5, "label": "louder"},
    ]

    for idx, params in enumerate(params_list):
        label = params.pop("label")
        print(f"\nTest {label}:")

        payload = {
            "text": text,
            "length_scale": 1.0,
            "noise_scale": 0.667,
            "volume": 1.0,
            **params  # Override with test params
        }

        try:
            response = requests.post(
                f"{SERVER_URL}/synthesize",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                output_file = OUTPUT_DIR / f"test_param_{idx}_{label}.wav"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"Saved: {output_file} ({len(response.content)} bytes)")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Error: {e}")

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Piper Voice Server Test Suite")
    print("=" * 60)

    try:
        requests.get(f"{SERVER_URL}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to {SERVER_URL}")
        print("Make sure the server is running on port 5050")
        sys.exit(1)

    results = []
    results.append(("Health", test_health()))
    results.append(("Models", test_models()))
    results.append(("Version", test_version()))
    results.append(("Synthesis", test_synthesize()))
    results.append(("Synthesis with params", test_synthesis_with_params()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:.<50} {status}")

    all_pass = all(r for _, r in results)
    print("\n" + ("All tests passed!" if all_pass else "Some tests failed!"))

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
