#!/usr/bin/env python3
"""
Button 4: Retriever Begin
Initialize and start the Retriever Agent for memory search
"""

import asyncio
import sys
sys.path.append('/mnt/r/memory_layer/mem0')

def run():
    print("🔍 Starting Retriever Agent...")

    try:
        from openmemory.Memory_Logic.agents.retriever_agent import RetrieverAgent

        print("✅ Imported RetrieverAgent")

        # Initialize the retriever
        agent = RetrieverAgent(
            api_url='http://localhost:8765',
            user_id='wolf_logic_user'
        )

        print("✅ Retriever Agent initialized")
        print("📊 Configuration:")
        print(f"   - API URL: http://localhost:8765")
        print(f"   - User ID: wolf_logic_user")
        print("\n💡 Use Button 7 (Memory Search) to query memories")

        return "Retriever initialized successfully"

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
