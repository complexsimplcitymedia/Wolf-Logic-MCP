#!/usr/bin/env python3
"""
Button 5: Memory Init
Initialize the Memory System
"""

import sys
sys.path.append('/mnt/r/memory_layer/mem0')

def run():
    print("💾 Initializing Memory System...")

    try:
        from mem0 import Memory

        # Initialize memory
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "100.110.82.181",
                    "port": 6333,
                }
            },
        }

        memory = Memory.from_config(config)
        print("✅ Memory system initialized")
        print("📊 Configuration: Qdrant vector store on localhost:6333")

        return "Memory system ready"

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
