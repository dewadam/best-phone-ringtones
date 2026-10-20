#!/usr/bin/env python3
"""Publish a Reel through Meta's Instagram API with Facebook Login.

Required environment: IG_USER_ID, IG_ACCESS_TOKEN
Optional: META_API_VERSION, SONG_TITLE, ARTIST_NAME, REEL_CAPTION,
VIDEO_PATH, INSTAGRAM_PUBLISH
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
from typing import Any
import requests

GRAPH_BASE = "https://graph.facebook.com"
API_VERSION = os.getenv("META_API_VERSION", "v26.0")
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
        raise InstagramAPIError(f"Instagram API request failed (HTTP {response.status_code}): " + json.dumps(payload, ensure_ascii=False)[:2500])
    return payload

def upload_resumable(user_id: str, token: str, video_path: Path, caption: str, audio_id: str = "") -> str:
    size = video_path.stat().st_size
    create_url = f"{GRAPH_BASE}/{API_VERSION}/{user_id}/media"
    payload = {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "share_to_feed": "true", "access_token": token}
    if audio_id:
        # Meta Audio API: audio is attached via the audio_configuration JSON object (not a bare audio_id field).
        payload["audio_configuration"] = json.dumps({"audio_id": audio_id, "audio_volume": 100})
    container = api_request("POST", create_url, data=payload)
    print("Container created:", json.dumps({k: v for k, v in container.items() if k != "access_token"}))
    print("audio_configuration sent:", payload.get("audio_configuration", "NONE"))
    container_id = container.get("id")
    if not container_id:
        raise InstagramAPIError("Container creation response did not include an ID.")
    upload_url = f"https://rupload.facebook.com/ig-api-upload/{API_VERSION}/{container_id}"
    with video_path.open("rb") as video:
        response = requests.post(upload_url, data=video, headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size), "Content-Type": "application/octet-stream"}, timeout=180)
    try:
        upload_payload = response.json()
    except ValueError:
        upload_payload = {"raw_response": response.text[:1000]}
    if not response.ok or upload_payload.get("error"):
        raise InstagramAPIError(f"Resumable video upload failed (HTTP {response.status_code}): " + json.dumps(upload_payload, ensure_ascii=False)[:2000])
    return str(container_id)

def create_container_from_url(user_id: str, token: str, video_url: str, caption: str, audio_id: str = "") -> str:
    """Documented Meta flow for audio_configuration: Instagram downloads the Reel from a public video_url."""
    create_url = f"{GRAPH_BASE}/{API_VERSION}/{user_id}/media"
    payload = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true", "access_token": token}
    if audio_id:
        payload["audio_configuration"] = json.dumps({"audio_id": audio_id, "audio_volume": 100})
    container = api_request("POST", create_url, data=payload)
    print("Container created (video_url):", json.dumps(container))
    print("audio_configuration sent:", payload.get("audio_configuration", "NONE"))
    container_id = container.get("id")
    if not container_id:
        raise InstagramAPIError("Container creation response did not include an ID.")
    return str(container_id)

def wait_until_ready(container_id: str, token: str, timeout_seconds: int = 300) -> None:
    url = f"{GRAPH_BASE}/{API_VERSION}/{container_id}"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        payload = api_request("GET", url, params={"fields": "status_code,status", "access_token": token})
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
    missing = [name for name, value in {"IG_USER_ID": user_id, "IG_ACCESS_TOKEN": token}.items() if not value]
    if missing:
        raise InstagramAPIError("Missing required environment variables: " + ", ".join(missing))
    if not video_path.is_file() or video_path.stat().st_size == 0:
        raise InstagramAPIError(f"Video file missing or empty: {video_path}")
    audio_id = os.getenv("IG_AUDIO_ID", "").strip()
    if os.getenv("AUDIO_SOURCE", "instagram") != "file" and not audio_id:
        raise InstagramAPIError("No IG_AUDIO_ID selected; refusing to publish a silent Reel.")
    print(f"Publishing Reel: {title} — {artist} | audio: {'Instagram catalog id ' + audio_id if audio_id else 'baked into MP4'}")
    video_url = os.getenv("VIDEO_URL", "").strip()
    if video_url:
        print(f"Using video_url upload: {video_url}")
        container_id = create_container_from_url(user_id, token, video_url, caption, audio_id)
    else:
        print("WARNING: no VIDEO_URL; falling back to resumable upload (audio_configuration is not documented for it).")
        container_id = upload_resumable(user_id, token, video_path, caption, audio_id)
    wait_until_ready(container_id, token)
    publish = api_request("POST", f"{GRAPH_BASE}/{API_VERSION}/{user_id}/media_publish", data={"creation_id": container_id, "access_token": token})
    media_id = publish.get("id")
    if not media_id:
        raise InstagramAPIError("Publish response did not include the resulting media ID.")
    print(f"Published Reel successfully. Instagram media ID: {media_id}")
    # Verify Instagram really attached catalog music (Meta field: media_audio_type = MUSIC | ORIGINAL_SOUND)
    if audio_id:
        kind = "UNKNOWN"
        for attempt in range(1, 7):  # the field can lag a few seconds behind publishing
            try:
                info = api_request("GET", f"{GRAPH_BASE}/{API_VERSION}/{media_id}", params={"fields": "media_audio_type,permalink", "access_token": token})
                kind = str(info.get("media_audio_type", "UNKNOWN")).upper()
                print(f"Check {attempt}: media_audio_type={kind} permalink={info.get('permalink')}")
            except InstagramAPIError as exc:
                kind = f"UNKNOWN ({exc})"
            if kind.startswith("MUSIC"):
                break
            time.sleep(10)
        print(f"media_audio_type reported by Instagram: {kind}")
        if not kind.startswith("MUSIC"):
            print(f"::error::Reel was published but Instagram did NOT report catalog music (audio_id {audio_id}).", file=sys.stderr)
            return 2
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstagramAPIError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
