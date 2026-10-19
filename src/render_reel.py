#!/usr/bin/env python3
"""Render a branded 9:16 still template into an MP4 Reel using FFmpeg."""
from __future__ import annotations
import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "template-9x16.png"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--artist", required=True)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--output", default="output/reel.mp4")
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg was not found on PATH.")
    if not TEMPLATE.exists():
        raise SystemExit(f"Missing {TEMPLATE}. Upload the approved 9:16 template image to assets/template-9x16.png.")
    if not 3 <= args.duration <= 90:
        raise SystemExit("Duration must be between 3 and 90 seconds.")
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.00015,1.025)':d=1:s=1080x1920:fps=30,format=yuv420p"
    cmd = [ffmpeg, "-y", "-loop", "1", "-i", str(TEMPLATE), "-t", str(args.duration),
           "-vf", vf, "-r", "30", "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-movflags", "+faststart", str(output)]
    subprocess.run(cmd, check=True)
    print(f"Rendered silent Reel: {output}")
    print(f"Requested title metadata: {args.title} — {args.artist}")
    print("Note: dynamic title/artist overlay is not implemented in this first scaffold.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
