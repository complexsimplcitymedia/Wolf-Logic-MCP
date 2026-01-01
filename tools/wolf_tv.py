#!/usr/bin/env python3
"""
WOLF TV - The Pipeline Watcher
Real-time TUI for the YouTube Analysis Pipeline.

Usage: python wolf_tv.py <youtube_url> [--fps 1.0]
"""

import time
import subprocess
import threading
import sys
import os
import argparse
from queue import Queue, Empty

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.align import Align

# Config
PIPELINE_SCRIPT = "/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/analysis/youtube_analyst.py"
MESSIAH_ENV = "/home/thewolfwalksalone/anaconda3/envs/messiah/bin/python"

console = Console()

class PipelineState:
    def __init__(self):
        self.title = "Initializing..."
        self.status = "Idle"
        self.grip_status = "Waiting..."
        self.camera_status = "Waiting..."
        self.sound_status = "Waiting..."
        self.lighting_log = []
        self.sound_log = []
        self.system_log = []
        self.progress = 0
        self.total_frames = 0
        self.frames_done = 0

    def add_log(self, dept, msg):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        
        if dept == "LIGHTING":
            self.lighting_log.append(entry)
            if len(self.lighting_log) > 10: self.lighting_log.pop(0)
        elif dept == "SOUND":
            self.sound_log.append(entry)
            if len(self.sound_log) > 10: self.sound_log.pop(0)
        else:
            self.system_log.append(entry)
            if len(self.system_log) > 10: self.system_log.pop(0)

def run_pipeline(url, target_fps, state, output_queue):
    """Runs the analysis script and captures output"""
    cmd = [MESSIAH_ENV, PIPELINE_SCRIPT, url, "--target-fps", str(target_fps), "--store"]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        line = line.strip()
        if not line: continue
        output_queue.put(line)
        
        # Parse output for state updates
        if "[GRIP]" in line:
            state.grip_status = line.split("[GRIP]")[-1].strip()
            if "Title:" in line: state.title = line.split("Title:")[-1].strip()
        
        elif "[CAMERA]" in line:
            state.camera_status = line.split("[CAMERA]")[-1].strip()
            if "frames total" in line:
                try:
                    state.total_frames = int(line.split("~")[1].split("frames")[0].strip())
                except (IndexError, ValueError) as e:
                    # Unable to parse frame count from output, continue with default
                    pass
        
        elif "[SOUND]" in line:
            msg = line.split("[SOUND]")[-1].strip()
            state.sound_status = msg
            state.add_log("SOUND", msg)
            
        elif "[LIGHTING]" in line:
            msg = line.split("[LIGHTING]")[-1].strip()
            state.add_log("LIGHTING", msg)
            if "Frame" in msg and "✓" in msg:
                state.frames_done += 1
        
        elif "[ARCHIVE]" in line:
            state.status = "Archiving..."
            state.add_log("SYSTEM", line.split("[ARCHIVE]")[-1].strip())

    process.wait()
    state.status = "Complete"
    output_queue.put("DONE")

def make_layout():
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )
    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1)
    )
    layout["left"].split(
        Layout(name="grip", ratio=1),
        Layout(name="camera", ratio=1),
        Layout(name="sound", ratio=2)
    )
    layout["right"].split(
        Layout(name="lighting", ratio=1)
    )
    return layout

def update_ui(layout, state):
    # Header
    layout["header"].update(
        Panel(
            Align.center(Text(f"WOLF TV: {state.title}", style="bold green")),
            style="green"
        )
    )

    # Departments
    layout["grip"].update(
        Panel(Text(state.grip_status, style="cyan"), title="[GRIP] Download")
    )
    
    camera_text = f"{state.camera_status}\nProgress: {state.frames_done}/{state.total_frames}"
    layout["camera"].update(
        Panel(Text(camera_text, style="magenta"), title="[CAMERA] Frames")
    )

    sound_text = "\n".join(state.sound_log)
    layout["sound"].update(
        Panel(Text(sound_text, style="yellow"), title="[SOUND] Audio/Transcript")
    )

    lighting_text = "\n".join(state.lighting_log)
    layout["lighting"].update(
        Panel(Text(lighting_text, style="blue"), title="[LIGHTING] Visual Analysis")
    )

    # Footer
    layout["footer"].update(
        Panel(Align.center(Text(f"Status: {state.status}", style="bold white")), style="white")
    )

def main():
    parser = argparse.ArgumentParser(description="Wolf TV - Watch the Pipeline")
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("--fps", type=float, required=True, help="Analysis FPS")
    args = parser.parse_args()

    state = PipelineState()
    output_queue = Queue()
    
    # Start pipeline thread
    t = threading.Thread(target=run_pipeline, args=(args.url, args.fps, state, output_queue))
    t.daemon = True
    t.start()

    layout = make_layout()

    with Live(layout, refresh_per_second=4, screen=True) as live:
        while True:
            try:
                msg = output_queue.get_nowait()
                if msg == "DONE":
                    time.sleep(2) # Show complete state briefly
                    break
            except Empty:
                pass
            
            update_ui(layout, state)
            time.sleep(0.1)

if __name__ == "__main__":
    main()
