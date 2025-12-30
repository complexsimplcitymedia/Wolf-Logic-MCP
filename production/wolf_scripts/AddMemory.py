#!/usr/bin/env python3
"""
Add Memory Script - Add a new memory to the Mem0 system
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mem0 import Memory

def main():
    print("=" * 60)
    print("🧠 ADD MEMORY TO MEM0")
    print("=" * 60)

    try:
        # Load config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'openmemory', 'api', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Initialize Memory
        memory = Memory.from_config(config['mem0'])
        print("✓ Memory system initialized")

        # Get memory input
        print("\nEnter memory content (or provide as command line arg):")
        if len(sys.argv) > 1:
            memory_text = ' '.join(sys.argv[1:])
        else:
            memory_text = input("> ")

        if not memory_text.strip():
            print("❌ No memory content provided")
            return 1

        # Add memory
        print(f"\n📝 Adding memory: {memory_text}")
        result = memory.add(memory_text, user_id="wolf_logic_user")

        print("\n✓ Memory added successfully!")
        print(f"Memory ID: {result}")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
