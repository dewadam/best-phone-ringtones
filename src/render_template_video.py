#!/usr/bin/env python3
"""Render a vertical MP4 template with song metadata centered in the middle square-safe area."""
import argparse, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="assets/template-reel.mp4")
    p.add_argument("--title", required=True)
    p.add_argument("--artist", required=True)
    p.add_argument("--duration", type=int, default=30)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    src = (ROOT / a.input).resolve()
    out = (ROOT / a.output).resolve()
    if not src.is_file():
        raise SystemExit(f"Template MP4 not found: {src}. Add your uploaded video as assets/template-reel.mp4 in the repository.")
    if not 3 <= a.duration <= 90:
        raise SystemExit("Duration must be between 3 and 90 seconds.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg was not found on PATH.")
    out.parent.mkdir(parents=True, exist_ok=True)
    def esc(s):
        return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%").replace(",", "\\,").replace("[", "\\[").replace("]", "\\]")
    title = esc(a.title[:70]); artist = esc(a.artist[:70])
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    # For a 1080x1920 Reel, the centered 1080x1080 square spans y=420..1500.
    # Keep the full metadata panel centered inside that square-safe region.
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          "drawbox=x=55:y=790:w=970:h=350:color=black@0.72:t=fill,"
          f"drawtext=fontfile={font}:text='{title}':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=840,"
          f"drawtext=fontfile={font}:text='{artist}':fontcolor=0xFF46CD:fontsize=42:x=(w-text_w)/2:y=940,"
          "drawtext=fontfile=" + font + ":text='BEST PHONE RINGTONES':fontcolor=0x00E8FF:fontsize=26:x=(w-text_w)/2:y=1040,"
          "format=yuv420p")
    cmd = [ffmpeg, "-y", "-i", str(src), "-t", str(a.duration), "-vf", vf, "-an", "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"Rendered supplied MP4 template: {out}")

if __name__ == "__main__":
    main()
