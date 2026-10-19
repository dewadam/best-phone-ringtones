#!/usr/bin/env python3
"""Render a branded 9:16 Reel with dynamic track text using Pillow and FFmpeg."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "template-9x16.png"
WIDTH, HEIGHT = 1080, 1920


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "C:/Windows/Fonts/arialbd.ttf"] if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "C:/Windows/Fonts/arial.ttf"]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont,
              max_width: int) -> str:
    """Shorten long metadata safely so it stays within the branded panel."""
    text = " ".join(text.split()).strip()
    if not text:
        return ""
    while text and draw.textbbox((0, 0), text, font=font)[2] > max_width:
        text = text[:-2].rstrip() + "…" if len(text) > 2 else ""
    return text


def create_branded_frame(template: Path, title: str, artist: str, destination: Path) -> None:
    """Crop a template to 9:16 and draw readable, dynamic title/artist metadata."""
    with Image.open(template) as source:
        image = source.convert("RGB")
    ratio = max(WIDTH / image.width, HEIGHT / image.height)
    resized = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2
    image = resized.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGBA")

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    panel = (64, 1320, 1016, 1690)
    draw.rounded_rectangle(panel, radius=38, fill=(5, 8, 25, 218),
                           outline=(0, 232, 255, 235), width=4)
    draw.rounded_rectangle((88, 1350, 100, 1660), radius=6, fill=(255, 35, 190, 255))

    title_font = _font(64, bold=True)
    artist_font = _font(42, bold=False)
    kicker_font = _font(24, bold=True)
    max_width = 850
    safe_title = _fit_text(draw, title, title_font, max_width)
    safe_artist = _fit_text(draw, artist, artist_font, max_width)

    draw.text((132, 1360), "NOW PLAYING  •  BEST PHONE RINGTONES",
              font=kicker_font, fill=(0, 232, 255, 255), stroke_width=0)
    draw.text((132, 1415), safe_title, font=title_font, fill=(255, 255, 255, 255),
              stroke_width=2, stroke_fill=(8, 12, 35, 255))
    draw.text((132, 1510), safe_artist, font=artist_font, fill=(255, 70, 205, 255))
    draw.text((132, 1615), "SAVE THIS SOUND  •  FIND YOUR VIBE",
              font=_font(22, bold=True), fill=(225, 235, 255, 255))

    result = Image.alpha_composite(image, overlay).convert("RGB")
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, format="PNG", optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--artist", required=True)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--output", default="output/reel.mp4")
    parser.add_argument("--template", default=str(TEMPLATE),
                        help="Optional 9:16 template path (useful for tests).")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg was not found on PATH.")
    template = Path(args.template).expanduser().resolve()
    if not template.exists():
        raise SystemExit(f"Missing {template}. Upload the approved 9:16 template image to assets/template-9x16.png.")
    if not 3 <= args.duration <= 90:
        raise SystemExit("Duration must be between 3 and 90 seconds.")

    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = output.with_name(output.stem + ".branded-frame.png")
    create_branded_frame(template, args.title, args.artist, frame)

    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.00015,1.025)':d=1:s=1080x1920:fps=30,format=yuv420p"
    cmd = [ffmpeg, "-y", "-loop", "1", "-i", str(frame), "-t", str(args.duration),
           "-vf", vf, "-r", "30", "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-movflags", "+faststart", str(output)]
    try:
        subprocess.run(cmd, check=True)
    finally:
        frame.unlink(missing_ok=True)

    print(f"Rendered branded Reel: {output}")
    print(f"On-screen title: {args.title}")
    print(f"On-screen artist: {args.artist}")
    print("Note: output is a silent visual; Instagram audio/publishing is a separate step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
