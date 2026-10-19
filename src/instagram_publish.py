"""Guarded Instagram Reels publishing via the Graph API."""
from __future__ import annotations
import os, sys, time
from urllib.parse import urlparse
import requests

def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def validate_public_video_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("PUBLIC_VIDEO_URL must be a publicly accessible HTTPS URL.")

def publish_reel(video_url: str, caption: str, audio_id: str | None = None) -> str:
    dry_run = os.getenv("DRY_RUN", "true").strip().lower() != "false"
    validate_public_video_url(video_url)
    user_id = require_env("IG_USER_ID")
    token = require_env("IG_ACCESS_TOKEN")
    version = require_env("META_GRAPH_VERSION")
    base = f"https://graph.facebook.com/{version}"
    if dry_run:
        print("DRY RUN: validated configuration; no API requests were sent.")
        print(f"Account ID: {user_id}")
        print(f"Video URL: {video_url}")
        print(f"Caption: {caption}")
        print(f"Audio ID supplied: {'yes' if audio_id else 'no'}")
        return "DRY_RUN"
    if not audio_id:
        raise RuntimeError("No API-returned audio ID supplied. Production publishing is blocked until the authorized Meta audio flow is verified.")
    payload = {"media_type":"REELS", "video_url":video_url, "caption":caption,
               "audio_id":audio_id, "access_token":token}
    response = requests.post(f"{base}/{user_id}/media", data=payload, timeout=60)
    response.raise_for_status()
    container_id = response.json().get("id")
    if not container_id:
        raise RuntimeError(f"Meta did not return a media container ID: {response.text[:500]}")
    for _ in range(30):
        r = requests.get(f"{base}/{container_id}",
                         params={"fields":"status_code,status","access_token":token}, timeout=30)
        r.raise_for_status()
        status = r.json()
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code in {"ERROR","EXPIRED"}:
            raise RuntimeError(f"Meta media processing failed: {status}")
        time.sleep(10)
    else:
        raise TimeoutError("Timed out waiting for Reel processing.")
    published = requests.post(f"{base}/{user_id}/media_publish",
                              data={"creation_id":container_id,"access_token":token}, timeout=60)
    published.raise_for_status()
    media_id = published.json().get("id")
    if not media_id:
        raise RuntimeError(f"Meta did not return a published media ID: {published.text[:500]}")
    print(f"Published Reel media ID: {media_id}")
    return str(media_id)

if __name__ == "__main__":
    url = os.getenv("PUBLIC_VIDEO_URL", "").strip()
    if not url:
        print("Set PUBLIC_VIDEO_URL to a publicly accessible MP4 URL.", file=sys.stderr)
        sys.exit(2)
    caption = os.getenv("REEL_CAPTION", "Best Phone Ringtones 🎵 Which ringtone would you choose? #iPhoneRingtone #Ringtones")
    publish_reel(url, caption, os.getenv("META_AUDIO_ID") or None)
