#!/usr/bin/env python3
"""Mux an externally-generated voice.wav (e.g. from F5-TTS-THAI Colab) into clip_silent.mp4.

Usage:
    python3 merge_audio.py voice.wav        # outputs clip.mp4
    python3 merge_audio.py voice.wav out.mp4
"""
import subprocess, sys, os

voice = sys.argv[1] if len(sys.argv) > 1 else "voice.wav"
out = sys.argv[2] if len(sys.argv) > 2 else "clip.mp4"

if not os.path.exists(voice):
    sys.exit(f"not found: {voice}")
if not os.path.exists("clip_silent.mp4"):
    sys.exit("not found: clip_silent.mp4 (run build_mp4.py first)")

subprocess.run([
    "ffmpeg", "-y",
    "-i", "clip_silent.mp4",
    "-i", voice,
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart",
    out,
], check=True)
print(f"wrote {out}")
