#!/usr/bin/env python3
"""
Button 8: Chat Begin
Launch llama.complexsimplicityai.com in browser
"""

import webbrowser
import sys

def run():
    print("💬 Launching Chat Interface...")

    try:
        url = "https://llama.complexsimplicityai.com"
        print(f"🌐 Opening: {url}")

        # Open in default browser
        webbrowser.open(url)

        print("✅ Chat interface launched")
        print("💡 Browser window should open automatically")

        return "Chat launched successfully"

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
