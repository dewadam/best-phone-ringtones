#!/usr/bin/env python3
"""Publish a Reel through Meta's Instagram API with Facebook Login.

Required environment:
  IG_USER_ID, IG_ACCESS_TOKEN
Optional:
  META_API_VERSION (defaults to v24.0)
  SONG_TITLE, ARTIST_NAME, REEL_CAPTION
  VIDEO_PATH (defaults to output/best-phone-ringtones-reel.mp4)
  INSTAGRAM_PUBLISH (must equal "true" to publish)

Audio lookup and attachment follow Meta's Instagram Audio API. If the account,
app permissions, audio result, or API version does not support the operation,
the script fails closed instead of publishing a Reel without the requested song.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

GRAPH_BASE = "https://graph.facebook.com"
API_VERSION = os.getenv("META_API_VERSION", "v24.0")
TIMEOUT = 60


class InstagramAPIError(RuntimeError):
    pass


def api_request(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw_response": response.text[:1000]}
    if not response.ok or "error" in payload:
        raise InstagramAPIError(
            f"Instagram API request failed (HTTP {response.status_code}): "
            + json.dumps(payload, ensure_ascii=False)[:2500]
        )
    return payload


def search_audio(user_id: str, token: str, title: str = "", artist: str = "") -> dict[str, Any]:
    """Choose a random currently trending licensed music track from Meta's IG Audio API."""
    url = f"{GRAPH_BASE}/{API_VERSION}/ig_audio"
    params: dict[str, Any] = {
        "audio_type": "music",
        "access_token": token,
    }
    # When a title is explicitly provided, search for it; otherwise Meta returns trending music.
    query = " ".join(part for part in (title.strip(), artist.strip()) if part)
    if query:
        params["q"] = query
    payload = api_request("GET", url, params=params)
    results = payload.get("data") or payload.get("audio") or []
    if isinstance(results, dict):
        results = [results]
    if not isinstance(results, list) or not results:
        raise InstagramAPIError(
            "Meta returned no eligible trending music. "
            + json.dumps(payload, ensure_ascii=False)[:1500]
        )
    usable = [item for item in results if isinstance(item, dict) and item.get("id")]
    if not usable:
        raise InstagramAPIError("Meta audio response contained no usable audio IDs.")
    # Random selection across the eligible results, as requested.
    import random
    chosen = random.choice(usable)
    chosen["title"] = chosen.get("title") or chosen.get("name") or "Trending audio"
    chosen["artist_name"] = chosen.get("artist_name") or chosen.get("artist") or chosen.get("username") or "Instagram audio"
    print("Selected Instagram trending audio:", json.dumps({
        "id": chosen.get("id"),
        "title": chosen.get("title"),
        "artist_name": chosen.get("artist_name"),
    }, ensure_ascii=False))
    return chosen


def upload_resumable(user_id: str, token: str, video_path: Path,
                     caption: str, audio_id: str) -> str:
    size = video_path.stat().st_size
    # Create an upload container, explicitly attaching the catalog audio.
    create_url = f"{GRAPH_BASE}/{API_VERSION}/{user_id}/media"
    container = api_request(
        "POST", create_url,
        data={
            "media_type": "REELS",
            "upload_type": "resumable",
            "caption": caption,
            "audio_id": audio_id,
            "share_to_feed": "true",
            "access_token": token,
        },
    )
    container_id = container.get("id")
    if not container_id:
        raise InstagramAPIError("Container creation response did not include an ID.")

    upload_url = f"https://rupload.facebook.com/ig-api-upload/{API_VERSION}/{container_id}"
    with video_path.open("rb") as video:
        response = requests.post(
            upload_url,
            data=video,
            headers={
                "Authorization": f"OAuth {token}",
                "offset": "0",
                "file_size": str(size),
                "Content-Type": "application/octet-stream",
            },
            timeout=180,
        )
    try:
        upload_payload = response.json()
    except ValueError:
        upload_payload = {"raw_response": response.text[:1000]}
    if not response.ok or upload_payload.get("error"):
        raise InstagramAPIError(
            f"Resumable video upload failed (HTTP {response.status_code}): "
            + json.dumps(upload_payload, ensure_ascii=False)[:2000]
        )
    return str(container_id)


def wait_until_ready(container_id: str, token: str, timeout_seconds: int = 300) -> None:
    url = f"{GRAPH_BASE}/{API_VERSION}/{container_id}"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        payload = api_request(
            "GET", url,
            params={"fields": "status_code,status", "access_token": token},
        )
        status = str(payload.get("status_code", "")).upper()
        print(f"Instagram container status: {status or payload.get('status')}")
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise InstagramAPIError(f"Instagram container not publishable: {payload}")
        time.sleep(5)
    raise InstagramAPIError("Timed out waiting for Instagram to process the Reel.")


def main() -> int:
    if os.getenv("INSTAGRAM_PUBLISH", "").lower() != "true":
        print("SAFE MODE: set INSTAGRAM_PUBLISH=true to publish. No post was made.")
        return 0

    user_id = os.getenv("IG_USER_ID", "").strip()
    token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    title = os.getenv("SONG_TITLE", "").strip()
    artist = os.getenv("ARTIST_NAME", "").strip()
    caption = os.getenv("REEL_CAPTION", "").strip()
    video_path = Path(os.getenv("VIDEO_PATH", "output/best-phone-ringtones-reel.mp4"))

    missing = [name for name, value in {
        "IG_USER_ID": user_id, "IG_ACCESS_TOKEN": token,
    }.items() if not value]
    if missing:
        raise InstagramAPIError("Missing required environment variables: " + ", ".join(missing))
    if not video_path.is_file() or video_path.stat().st_size == 0:
        raise InstagramAPIError(f"Video file missing or empty: {video_path}")

    audio = search_audio(user_id, token, title, artist)
    # Fill metadata from the selected trending track when workflow inputs were left blank.
    if not title:
        title = str(audio.get("title", "Trending audio"))
    if not artist:
        artist = str(audio.get("artist_name", "Instagram audio"))
    print(f"Publishing with selected track: {title} — {artist}")
    container_id = upload_resumable(user_id, token, video_path, caption, str(audio["id"]))
    wait_until_ready(container_id, token)

    publish = api_request(
        "POST", f"{GRAPH_BASE}/{API_VERSION}/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
    )
    media_id = publish.get("id")
    if not media_id:
        raise InstagramAPIError("Publish response did not include the resulting media ID.")
    print(f"Published Reel successfully. Instagram media ID: {media_id}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstagramAPIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
