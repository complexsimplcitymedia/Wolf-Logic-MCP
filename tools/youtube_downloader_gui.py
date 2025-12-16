#!/usr/bin/env python3
"""
Simple YouTube Downloader GUI
Uses yt-dlp backend with tkinter interface (no OpenGL needed)
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import subprocess
import threading
import os

class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("800x600")

        # URL input
        url_frame = ttk.Frame(root, padding="10")
        url_frame.pack(fill=tk.X)

        ttk.Label(url_frame, text="Video URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Download path
        path_frame = ttk.Frame(root, padding="10")
        path_frame.pack(fill=tk.X)

        ttk.Label(path_frame, text="Save to:").pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.insert(0, os.path.expanduser("~/wolfbook-wd"))
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ttk.Button(path_frame, text="Browse", command=self.browse_path).pack(side=tk.LEFT)

        # Quality selection
        quality_frame = ttk.Frame(root, padding="10")
        quality_frame.pack(fill=tk.X)

        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value="best")
        qualities = ["best", "1080p", "720p", "480p", "360p", "audio-only"]
        quality_menu = ttk.Combobox(quality_frame, textvariable=self.quality_var, values=qualities, width=15)
        quality_menu.pack(side=tk.LEFT, padx=5)

        # Download button
        button_frame = ttk.Frame(root, padding="10")
        button_frame.pack(fill=tk.X)

        self.download_btn = ttk.Button(button_frame, text="Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel_download, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Progress
        progress_frame = ttk.Frame(root, padding="10")
        progress_frame.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X)

        # Output log
        log_frame = ttk.Frame(root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(log_frame, text="Output:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.process = None

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.path_entry.get())
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            self.log("Error: Enter a URL")
            return

        save_path = self.path_entry.get().strip()
        quality = self.quality_var.get()

        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_bar.start()

        self.log(f"Starting download: {url}")
        self.log(f"Quality: {quality}")
        self.log(f"Save to: {save_path}")

        thread = threading.Thread(target=self.download_thread, args=(url, save_path, quality))
        thread.daemon = True
        thread.start()

    def download_thread(self, url, save_path, quality):
        # Build yt-dlp command
        cmd = ["yt-dlp", "--no-check-certificate"]

        if quality == "audio-only":
            cmd.extend(["-x", "--audio-format", "mp3"])
        elif quality == "best":
            cmd.extend(["-f", "bestvideo+bestaudio/best"])
        else:
            height = quality.replace("p", "")
            cmd.extend(["-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"])

        cmd.extend(["-o", f"{save_path}/%(title)s.%(ext)s", url])

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in self.process.stdout:
                self.root.after(0, self.log, line.strip())

            self.process.wait()

            if self.process.returncode == 0:
                self.root.after(0, self.log, "✓ Download complete!")
            else:
                self.root.after(0, self.log, f"Error: Process exited with code {self.process.returncode}")

        except Exception as e:
            self.root.after(0, self.log, f"Error: {e}")

        finally:
            self.root.after(0, self.download_complete)

    def cancel_download(self):
        if self.process:
            self.process.terminate()
            self.log("Download cancelled")

    def download_complete(self):
        self.progress_bar.stop()
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.process = None

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()
