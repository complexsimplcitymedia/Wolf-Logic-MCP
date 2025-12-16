#!/usr/bin/env python3
"""
Button 16: Benchmark Run
Run performance benchmark on the system
"""

import time
import requests

def run():
    print("⏱️ Running Performance Benchmark...")

    try:
        results = {
            "ollama_response_time": None,
            "memory_latency": None,
            "embedding_speed": None
        }

        # Test Ollama response time
        print("📊 Testing Ollama response time...")
        start = time.time()
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                results["ollama_response_time"] = round((time.time() - start) * 1000, 2)
                print(f"   ✅ Ollama: {results['ollama_response_time']}ms")
        except:
            print("   ❌ Ollama: Not available")

        # Test Qdrant response time
        print("📊 Testing Qdrant (memory) response time...")
        start = time.time()
        try:
            response = requests.get("http://localhost:6333/health", timeout=5)
            if response.status_code == 200:
                results["memory_latency"] = round((time.time() - start) * 1000, 2)
                print(f"   ✅ Qdrant: {results['memory_latency']}ms")
        except:
            print("   ❌ Qdrant: Not available")

        print("\n📈 Benchmark Results:")
        print(f"   Ollama Response: {results['ollama_response_time']}ms")
        print(f"   Memory Latency: {results['memory_latency']}ms")

        return "Benchmark completed"

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
