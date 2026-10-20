#!/usr/bin/env python3
"""Render a vertical MP4 template with centered metadata while preserving source audio."""
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
    p.add_argument("--audio", default="", help="Audio file to use as the Reel soundtrack (replaces the template's silent track).")
    p.add_argument("--audio-start", type=float, default=0.0, help="Start offset (seconds) inside the audio file.")
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
    title = esc(a.title[:50]); artist = esc(a.artist[:50])
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    # No rectangle/panel: place compact text directly inside the template's central square screen.
    # 1080x1920 canvas; the square display is approximately x=240..840, y=540..1110.
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"drawtext=fontfile={font}:text='{title}':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=790:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
          f"drawtext=fontfile={font}:text='{artist}':fontcolor=0xFF46CD:fontsize=38:x=(w-text_w)/2:y=860:shadowcolor=black@0.9:shadowx=2:shadowy=2,"
          "drawtext=fontfile=" + font + ":text='BEST PHONE RINGTONES':fontcolor=0x00E8FF:fontsize=23:x=(w-text_w)/2:y=920:shadowcolor=black@0.9:shadowx=1:shadowy=1,"
          "format=yuv420p")
    audio = (ROOT / a.audio).resolve() if a.audio else None
    if audio and not audio.is_file():
        raise SystemExit(f"Audio file not found: {audio}")
    cmd = [ffmpeg, "-y", "-i", str(src)]
    if audio:
        cmd += ["-ss", str(a.audio_start), "-i", str(audio)]
    cmd += ["-t", str(a.duration), "-vf", vf, "-map", "0:v:0"]
    if audio:
        fade_out = max(a.duration - 1, 0)
        af = f"afade=t=in:d=0.3,afade=t=out:st={fade_out}:d=1,loudnorm=I=-14:TP=-1.5:LRA=11"
        # The template's own audio track is digital silence, so it is replaced, not mixed.
        cmd += ["-map", "1:a:0", "-af", af]
    else:
        cmd += ["-map", "0:a?"]
    cmd += ["-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"Rendered supplied MP4 template with source audio preserved when present: {out}")

if __name__ == "__main__":
    main()
