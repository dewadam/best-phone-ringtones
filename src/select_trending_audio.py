#!/usr/bin/env python3
"""Select a random trending licensed music item using Meta's Instagram Audio API."""
import json, os, random, sys
import requests

version = os.getenv("META_API_VERSION", "v24.0")
token = os.getenv("IG_ACCESS_TOKEN", "").strip()
if not token:
    raise SystemExit("Missing IG_ACCESS_TOKEN secret.")
url = f"https://graph.facebook.com/{version}/ig_audio"
r = requests.get(url, params={"audio_type": "music", "access_token": token}, timeout=60)
try:
    data = r.json()
except ValueError:
    raise SystemExit(f"Meta audio endpoint returned non-JSON HTTP {r.status_code}: {r.text[:500]}")
if not r.ok or "error" in data:
    raise SystemExit("Meta audio search failed: " + json.dumps(data, ensure_ascii=False)[:1500])
items = data.get("data") or data.get("audio") or []
if isinstance(items, dict):
    items = [items]
items = [x for x in items if isinstance(x, dict) and x.get("id")]
if not items:
    raise SystemExit("Meta returned no eligible trending music tracks: " + json.dumps(data, ensure_ascii=False)[:1000])
track = random.choice(items)
title = str(track.get("title") or track.get("name") or "Trending audio").replace("\n", " ").strip()
artist = str(track.get("artist_name") or track.get("artist") or track.get("username") or "Instagram audio").replace("\n", " ").strip()
audio_id = str(track["id"])
# Write values safely to GitHub Actions environment and log only non-sensitive metadata.
with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
    f.write(f"SONG_TITLE={title}\nARTIST_NAME={artist}\nIG_AUDIO_ID={audio_id}\n")
print(json.dumps({"title": title, "artist": artist, "audio_id": audio_id}, ensure_ascii=False))
