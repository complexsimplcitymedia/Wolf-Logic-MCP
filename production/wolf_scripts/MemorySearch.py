#!/usr/bin/env python3
"""
Button 3: Memory Search
Auto-populated Complex Logic script - quick memory search
"""

import asyncio
import sys
sys.path.append('/mnt/r/memory_layer/mem0')

from openmemory.Memory_Logic.agents.retriever_agent import RetrieverAgent

async def run():
    print("🔎 Quick Memory Search...")
    
    agent = RetrieverAgent(
        api_url='http://localhost:8765',
        user_id='wolf_logic_user'
    )

    # Example search - you can modify this
    query = "What are my preferences?"
    print(f"Searching for: {query}")
    
    results = await agent.search(query, limit=5)
    
    print("📋 Search Results:")
    for i, memory in enumerate(results, 1):
        print(f"{i}. {memory.get('content', 'No content')}")
    
    print("✅ Search complete")

if __name__ == "__main__":
    asyncio.run(run())