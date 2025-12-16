#!/usr/bin/env python3
"""
Button 2: Start Mistral
Load and verify Mistral model in Ollama
"""

import requests
import json

def run():
    print("🧠 Starting Mistral Model...")

    try:
        # Check if model is available
        response = requests.get("http://localhost:11434/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]

            # Look for Mistral variants
            mistral_models = [m for m in model_names if 'mistral' in m.lower()]

            if mistral_models:
                print(f"✅ Found Mistral models: {mistral_models}")

                # Test the first Mistral model
                model_name = mistral_models[0]
                print(f"🔄 Testing {model_name}...")

                test_payload = {
                    "model": model_name,
                    "prompt": "Hello",
                    "stream": False
                }

                test_response = requests.post(
                    "http://localhost:11434/api/generate",
                    json=test_payload,
                    timeout=30
                )

                if test_response.status_code == 200:
                    print(f"✅ {model_name} is ready!")
                    print(f"📊 Model: {model_name}")
                    return f"Mistral ready: {model_name}"
                else:
                    print(f"⚠️ Model test failed: {test_response.status_code}")
                    return "Model test failed"
            else:
                print("❌ No Mistral models found!")
                print("💡 Pull a model with: ollama pull mistral")
                return "No Mistral models"

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama!")
        print("💡 Start Ollama first (Button 1)")
        return "Ollama not running"
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
