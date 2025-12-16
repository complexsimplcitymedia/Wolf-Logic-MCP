#!/usr/bin/env python3
"""
Button 3: Embedder Begin
Initialize and start the Embedder Agent for memory processing
"""

import asyncio
import sys
sys.path.append('/mnt/r/memory_layer/mem0')

def run():
    print("🚀 Starting Embedder Agent...")

    try:
        from openmemory.Memory_Logic.agents.embedder_agent import EmbedderAgent

        print("✅ Imported EmbedderAgent")

        # Initialize the embedder
        agent = EmbedderAgent(
            api_url='http://localhost:8765',
            user_id='wolf_logic_user',
            batch_size=5
        )

        print("✅ Embedder Agent initialized")
        print("📊 Configuration:")
        print(f"   - API URL: http://localhost:8765")
        print(f"   - User ID: wolf_logic_user")
        print(f"   - Batch Size: 5")
        print("\n💡 Use Button 6 (Add Memory) to add memories to the queue")

        return "Embedder initialized successfully"

    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
        print("💡 Check if mem0 is installed in MemZero environment")
        return f"Import error: {str(e)}"
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
