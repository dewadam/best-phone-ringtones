#!/usr/bin/env python3
"""Select a random music item returned by Meta's Instagram Audio API."""
import json, os, random, sys
import requests

version = os.getenv("META_API_VERSION", "v26.0")
token = os.getenv("IG_ACCESS_TOKEN", "").strip()
user_id = os.getenv("IG_USER_ID", "").strip()
if not token:
    raise SystemExit("Missing IG_ACCESS_TOKEN secret.")
if not user_id:
    raise SystemExit("Missing IG_USER_ID secret.")

url = f"https://graph.facebook.com/{version}/ig_audio"
r = requests.get(url, params={"ig_user_id": user_id, "audio_type": "music", "access_token": token}, timeout=60)
try:
    data = r.json()
except ValueError:
    raise SystemExit(f"Meta audio endpoint returned non-JSON HTTP {r.status_code}: {r.text[:500]}")
if not r.ok or "error" in data:
    raise SystemExit("Meta audio search failed: " + json.dumps(data, ensure_ascii=False)[:1500])

# Meta may return the list as audio with audio_id, rather than data with id.
items = data.get("data") or data.get("audio") or []
if isinstance(items, dict):
    items = [items]
items = [item for item in items if isinstance(item, dict) and (item.get("id") or item.get("audio_id"))]
if not items:
    raise SystemExit("Meta returned no eligible music tracks: " + json.dumps(data, ensure_ascii=False)[:1500])

track = random.choice(items)
title = str(track.get("title") or track.get("name") or "Trending audio").replace("\n", " ").strip()
artist = str(track.get("artist_name") or track.get("display_artist") or track.get("artist") or track.get("ig_username") or track.get("username") or "Instagram audio").replace("\n", " ").strip()
audio_id = str(track.get("id") or track.get("audio_id"))

with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
    f.write(f"SONG_TITLE={title}\nARTIST_NAME={artist}\nIG_AUDIO_ID={audio_id}\n")
print(json.dumps({"title": title, "artist": artist, "audio_id": audio_id}, ensure_ascii=False))
