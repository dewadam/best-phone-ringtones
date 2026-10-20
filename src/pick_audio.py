#!/usr/bin/env python3
"""Pick the audio file that will be mixed into the Reel.

Audio comes from the repository (assets/audio/), NOT from Instagram's catalog.
Name files like "Artist - Title.mp3" so title/artist can be filled automatically.

Env in : AUDIO_FILE (optional, path relative to repo root), SONG_TITLE, ARTIST_NAME
Env out: AUDIO_PATH, SONG_TITLE, ARTIST_NAME (written to $GITHUB_ENV)
"""
import os, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / "assets" / "audio"
EXTS = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac"}

choice = os.getenv("AUDIO_FILE", "").strip()
if choice:
    path = (ROOT / choice).resolve()
    if ROOT not in path.parents:
        raise SystemExit("AUDIO_FILE must be inside the repository.")
    if not path.is_file():
        raise SystemExit(f"Audio file not found: {choice}")
else:
    files = sorted(p for p in AUDIO_DIR.glob("*") if p.suffix.lower() in EXTS)
    if not files:
        raise SystemExit("No audio found. Upload an .mp3 to assets/audio/ (e.g. 'Artist - Title.mp3').")
    path = random.choice(files)

title = os.getenv("SONG_TITLE", "").strip()
artist = os.getenv("ARTIST_NAME", "").strip()
stem = path.stem
if " - " in stem:
    guess_artist, guess_title = (s.strip() for s in stem.split(" - ", 1))
else:
    guess_artist, guess_title = "", stem.strip()
title = title or guess_title
artist = artist or guess_artist or "Unknown artist"

lines = f"AUDIO_PATH={path.relative_to(ROOT)}\nSONG_TITLE={title}\nARTIST_NAME={artist}\n"
env_file = os.getenv("GITHUB_ENV")
if env_file:
    with open(env_file, "a", encoding="utf-8") as f:
        f.write(lines)
print(lines)
