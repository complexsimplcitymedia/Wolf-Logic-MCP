#!/usr/bin/env python3
"""
Button 2: Start Retriever Agent
Auto-populated Wolf Logic script - runs the memory retrieval agent
"""

import asyncio
import sys
sys.path.append('/mnt/r/memory_layer/mem0')

from openmemory.Memory_Logic.agents.retriever_agent import RetrieverAgent

async def run():
    print("🔍 Starting RetrieverAgent...")
    
    agent = RetrieverAgent(
        api_url='http://localhost:8765',
        user_id='wolf_logic_user',
        app_name='wolf_logic_ai',
        limit=10,
        rerank=True
    )

    print("✅ RetrieverAgent ready for interactive search...")
    await agent.start_interactive()

if __name__ == "__main__":
    asyncio.run(run())