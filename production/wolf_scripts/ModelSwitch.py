#!/usr/bin/env python3
"""
Button 14: Model Switch
Switch between available Mistral models
"""

import requests

def run():
    print("🔄 Switching Mistral Model...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)

        if response.status_code == 200:
            models = response.json().get('models', [])
            mistral_models = [m['name'] for m in models if 'mistral' in m['name'].lower()]

            if mistral_models:
                print(f"📋 Available Mistral models:")
                for i, model in enumerate(mistral_models, 1):
                    print(f"   {i}. {model}")

                print(f"\n✅ Currently using: {mistral_models[0]}")
                print("💡 Edit this script to switch models")

                return f"Current model: {mistral_models[0]}"
            else:
                print("❌ No Mistral models found")
                return "No Mistral models"
        else:
            print("❌ Cannot connect to Ollama")
            return "Ollama connection failed"

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
