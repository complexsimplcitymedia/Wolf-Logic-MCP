#!/usr/bin/env python3
"""
GPU Resource Check - Avoid collisions with MCP/YouTube processes
Checks VRAM usage before running heavy Ollama operations
"""

import subprocess
import re

def get_gpu_usage():
    """
    Get current GPU VRAM usage
    Returns: (used_gb, total_gb, usage_percent)
    """
    try:
        # Use rocm-smi for AMD GPU
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout

        # Parse VRAM usage (format: "GPU[0] : VRAM Total Memory (B): 23008493568")
        total_match = re.search(r'VRAM Total Memory.*?(\d+)', output)
        used_match = re.search(r'VRAM Total Used Memory.*?(\d+)', output)

        if total_match and used_match:
            total_bytes = int(total_match.group(1))
            used_bytes = int(used_match.group(1))

            total_gb = total_bytes / (1024**3)
            used_gb = used_bytes / (1024**3)
            usage_percent = (used_bytes / total_bytes) * 100

            return used_gb, total_gb, usage_percent

    except Exception as e:
        # Fallback: Check running processes
        pass

    return None, None, None

def check_mcp_youtube_running():
    """Check if MCP or YouTube vision models are running"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout.lower()

        # Check for MCP server or YouTube processing
        mcp_running = "mcp" in output and "youtube" in output
        vision_running = "llava" in output or "llama3.2-vision" in output

        return mcp_running or vision_running

    except Exception:
        return False

def safe_to_run_monitor():
    """
    Determine if it's safe to run system monitor
    Returns: (safe: bool, reason: str, vram_used: float)
    """
    # Check for MCP/YouTube processes
    if check_mcp_youtube_running():
        return False, "MCP/YouTube vision models running", 0

    # Check GPU VRAM usage
    used_gb, total_gb, usage_percent = get_gpu_usage()

    if used_gb is not None:
        # Threshold: Don't run if VRAM > 15GB used (leaves 6GB for monitor)
        if used_gb > 15.0:
            return False, f"High VRAM usage: {used_gb:.1f}GB / {total_gb:.1f}GB ({usage_percent:.1f}%)", used_gb

        return True, f"VRAM available: {used_gb:.1f}GB / {total_gb:.1f}GB ({usage_percent:.1f}%)", used_gb

    # If can't determine GPU usage, check process list only
    return True, "GPU check inconclusive, proceeding", 0

if __name__ == "__main__":
    safe, reason, vram = safe_to_run_monitor()
    print(f"Safe to run: {safe}")
    print(f"Reason: {reason}")

    if not safe:
        exit(1)  # Exit with error code if not safe
    exit(0)
