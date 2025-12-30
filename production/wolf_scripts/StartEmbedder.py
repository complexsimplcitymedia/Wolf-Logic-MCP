#!/usr/bin/env python3
"""
Button 1: Start Embedder Agent
Auto-populated Complex Logic script - runs the memory embedding agent
"""

import asyncio
import sys
sys.path.append('/mnt/r/memory_layer/mem0')

from openmemory.Memory_Logic.agents.embedder_agent import EmbedderAgent

async def run():
    print("🚀 Starting EmbedderAgent...")
    
    agent = EmbedderAgent(
        api_url='http://localhost:8765',
        user_id='wolf_logic_user',
        batch_size=5,
        poll_interval=2.0
    )

    # Add some test memories to get started
    agent.add_bulk([
        'User prefers Complex Logic AI interface',
        'User works with memory agents daily',
        'User values 6-minute setup time'
    ])

    print("✅ EmbedderAgent started - processing memories...")
    await agent.start()

if __name__ == "__main__":
    asyncio.run(run())