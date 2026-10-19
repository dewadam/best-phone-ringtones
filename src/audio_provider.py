"""Discover trending audio through Meta's Instagram Audio API.

The official Audio API is available to eligible professional accounts through
Facebook Login. If no search query is supplied, Meta returns trending audio.
"""
from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import asdict, dataclass

import requests


@dataclass(frozen=True)
class AudioChoice:
    audio_id: str
    title: str = ""
    artist: str = ""
    source: str = "meta_authorized_api"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def fetch_trending_audio() -> list[AudioChoice]:
    user_id = require_env("IG_USER_ID")
    token = require_env("IG_ACCESS_TOKEN")
    version = require_env("META_GRAPH_VERSION")
    audio_type = os.getenv("META_AUDIO_TYPE", "music").strip().lower() or "music"
    if audio_type not in {"music", "original_sound"}:
        raise ValueError("META_AUDIO_TYPE must be 'music' or 'original_sound'.")

    url = f"https://graph.facebook.com/{version}/{user_id}/ig_audio"
    response = requests.get(
        url,
        params={"audio_type": audio_type, "access_token": token},
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        raise RuntimeError(f"Unexpected Meta Audio API response: {json.dumps(payload)[:800]}")

    choices = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        audio_id = str(item.get("id") or item.get("audio_id") or "").strip()
        if not audio_id:
            continue
        choices.append(AudioChoice(
            audio_id=audio_id,
            title=str(item.get("title") or item.get("name") or "").strip(),
            artist=str(item.get("artist_name") or item.get("artist") or "").strip(),
        ))
    if not choices:
        raise RuntimeError(
            "Meta returned no usable audio records. Check app access, permissions, "
            "account eligibility, endpoint version, and the API response schema."
        )
    return choices


def main() -> None:
    choices = fetch_trending_audio()
    # Randomly choose from Meta's returned trending list; never invent an audio ID.
    selected = random.choice(choices)
    print(json.dumps(asdict(selected), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Meta audio discovery failed: {exc}", file=sys.stderr)
        raise
