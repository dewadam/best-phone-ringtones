#!/usr/bin/env python3
"""Persistent history of songs already posted (data/used_audio.json, committed back to the repo by the workflow)."""
from __future__ import annotations
import datetime, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "used_audio.json"


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def load() -> list[dict]:
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return []
    return data if isinstance(data, list) else []


def is_used(audio_id: str = "", title: str = "", artist: str = "") -> bool:
    """True if this audio_id, or the same title+artist (other ids of the same song), was posted before."""
    name = _norm(title) + "|" + _norm(artist)
    for entry in load():
        if audio_id and str(entry.get("audio_id", "")) == str(audio_id):
            return True
        if title and name == _norm(entry.get("title", "")) + "|" + _norm(entry.get("artist", "")):
            return True
    return False


def record(audio_id: str, title: str, artist: str, media_id: str = "") -> None:
    data = load()
    data.append({
        "audio_id": str(audio_id), "title": title, "artist": artist, "media_id": str(media_id),
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    })
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
