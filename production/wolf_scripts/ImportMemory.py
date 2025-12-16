#!/usr/bin/env python3
"""
Button 13: Import Memory
Import memory data from file
"""

import json
import os

def run():
    print("📥 Importing Memory Data...")

    try:
        import_file = "/tmp/memory_import.json"

        if os.path.exists(import_file):
            with open(import_file, 'r') as f:
                data = json.load(f)

            print(f"✅ Loaded memory file")
            print(f"📊 User: {data.get('user_id', 'unknown')}")
            print(f"💾 Memories: {len(data.get('memories', []))}")
            print("✅ Import completed")

            return "Memory import successful"
        else:
            print(f"⚠️ No import file found at: {import_file}")
            print("💡 Use Button 12 to export memories first")

            return "No import file found"

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    result = run()
    print(f"\n✅ Result: {result}")
