#!/usr/bin/env python3
"""
YouTube Analyst - LLaVA variant
Forces use of llava:13b for full context
"""
import sys
import os

# Override visual agent models before import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Monkey patch before import
import visual_agent
visual_agent.VISION_MODELS = ["llava:13b"]

# Now import and run main analyst
from youtube_analyst import main

if __name__ == "__main__":
    sys.exit(main())
