#!/usr/bin/env python3
"""
Button 10: Agent Status
Check status of all running agents and services
"""

import requests

def run():
    print("📊 Checking Agent Status...")

    status = {
        "ollama": False,
        "qdrant": False,
        "embedder": "unknown",
        "retriever": "unknown"
    }

    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            status["ollama"] = True
            print("✅ Ollama: Running")
        else:
            print("⚠️ Ollama: Responding but unhealthy")
    except:
        print("❌ Ollama: Not running")

    # Check Qdrant
    try:
        response = requests.get("http://localhost:6333/health", timeout=2)
        if response.status_code == 200:
            status["qdrant"] = True
            print("✅ Qdrant: Running")
        else:
            print("⚠️ Qdrant: Responding but unhealthy")
    except:
        print("❌ Qdrant: Not running")

    print("\n📈 System Status Summary:")
    print(f"   Ollama: {'✅' if status['ollama'] else '❌'}")
    print(f"   Qdrant: {'✅' if status['qdrant'] else '❌'}")

    if all([status["ollama"], status["qdrant"]]):
        return "All systems operational"
    else:
        return "Some systems offline"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
