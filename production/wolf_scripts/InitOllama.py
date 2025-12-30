#!/usr/bin/env python3
"""
Button 1: Init Ollama
Initialize Ollama connection and verify service is running
"""

import subprocess
import requests
import time

def run():
    print("🔥 Initializing Ollama Connection...")

    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running!")
            print(f"📋 Available models: {len(models)}")

            for model in models:
                print(f"   - {model.get('name', 'unknown')}")

            return "Ollama initialized successfully"
        else:
            print(f"⚠️ Ollama responded with status: {response.status_code}")
            return "Ollama connection issue"

    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running!")
        print("💡 Start Ollama with: ollama serve")
        return "Ollama not running"
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
