#!/usr/bin/env python3
"""Find a track in Meta's Instagram Audio API (GET /ig_audio) and export its audio_id.

Docs: https://developers.facebook.com/docs/instagram-platform/content-publishing/audio-api/
- Needs Instagram API *with Facebook Login* (graph.facebook.com), Graph API v22.0+.
- Params are `audio_type`, `user_id`, optional `search_query` (NOT ig_user_id / q).
- Only audio authorized for third-party use is returned; the catalog can differ from the app.

If SONG_TITLE/ARTIST_NAME are set -> search and pick the closest match (fails if nothing is close).
If both are empty -> pick a random trending track.
"""
import difflib, json, os, random
import requests

version = os.getenv("META_API_VERSION", "v24.0")
token = os.getenv("IG_ACCESS_TOKEN", "").strip()
user_id = os.getenv("IG_USER_ID", "").strip()
title_in = os.getenv("SONG_TITLE", "").strip()
artist_in = os.getenv("ARTIST_NAME", "").strip()
if not token:
    raise SystemExit("Missing IG_ACCESS_TOKEN secret.")
if not user_id:
    raise SystemExit("Missing IG_USER_ID secret.")

params = {"audio_type": "music", "user_id": user_id, "access_token": token}
query = " ".join(p for p in (title_in, artist_in) if p)
if query:
    params["search_query"] = query

r = requests.get(f"https://graph.facebook.com/{version}/ig_audio", params=params, timeout=60)
try:
    data = r.json()
except ValueError:
    raise SystemExit(f"Meta audio endpoint returned non-JSON HTTP {r.status_code}: {r.text[:500]}")
if not r.ok or "error" in data:
    raise SystemExit("Meta audio search failed: " + json.dumps(data, ensure_ascii=False)[:1500])

items = [i for i in (data.get("audio") or data.get("data") or [])
         if isinstance(i, dict) and (i.get("audio_id") or i.get("id"))]
if not items:
    raise SystemExit(f"Meta returned no audio for '{query or 'trending'}'. This song may not be in the "
                     "API catalog. Use audio_source=file with your own MP3 instead.")

def name(i):  return str(i.get("title") or "").strip()
def who(i):   return str(i.get("display_artist") or i.get("ig_username") or "").strip()

if query:
    def score(i):
        t = difflib.SequenceMatcher(None, title_in.lower(), name(i).lower()).ratio() if title_in else 1
        a = difflib.SequenceMatcher(None, artist_in.lower(), who(i).lower()).ratio() if artist_in else 1
        return 0.6 * t + 0.4 * a
    track = max(items, key=score)
    if score(track) < 0.6:
        found = "; ".join(f"{name(i)} - {who(i)}" for i in items[:5])
        raise SystemExit(f"No close match for '{query}'. Meta returned: {found}")
else:
    track = random.choice(items)

audio_id = str(track.get("audio_id") or track.get("id"))
title = (name(track) or "Trending audio").replace("\n", " ")
artist = (who(track) or "Instagram audio").replace("\n", " ")
with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
    f.write(f"SONG_TITLE={title}\nARTIST_NAME={artist}\nIG_AUDIO_ID={audio_id}\n")
print(json.dumps({"title": title, "artist": artist, "audio_id": audio_id}, ensure_ascii=False))
