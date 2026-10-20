#!/usr/bin/env python3
"""Find a track in Meta's Instagram Audio API (GET /ig_audio) and export its audio_id.

Docs: https://developers.facebook.com/docs/instagram-platform/content-publishing/audio-api/
- Needs Instagram API *with Facebook Login* (graph.facebook.com), Graph API v22.0+.
- Params are `audio_type`, `user_id`, optional `search_query` (NOT ig_user_id / q).

Modes
- SONG_TITLE/ARTIST_NAME set  -> search and pick the closest match (explicit request; repeats are only warned about).
- both empty (automatic mode) -> pick a random trending track that was NOT posted before
  (data/used_audio.json). If every trending track was used, try generic search terms until a new one is found.
"""
import difflib, json, os, random, sys
import requests

sys.path.insert(0, os.path.dirname(__file__))
import used_audio

version = os.getenv("META_API_VERSION", "v24.0")
token = os.getenv("IG_ACCESS_TOKEN", "").strip()
user_id = os.getenv("IG_USER_ID", "").strip()
title_in = os.getenv("SONG_TITLE", "").strip()
artist_in = os.getenv("ARTIST_NAME", "").strip()
if not token:
    raise SystemExit("Missing IG_ACCESS_TOKEN secret.")
if not user_id:
    raise SystemExit("Missing IG_USER_ID secret.")

# Used only when trending is exhausted (automatic mode).
FALLBACK_TERMS = """love remix sped up slowed hip hop pop rock dance summer night acoustic instrumental lofi edm latin kpop
arabic turkish bollywood country rnb party sad happy baby heart dream fire girl boy money city rain sun moon star
gold blue red black white wild crazy angel devil dance floor radio phone call tonight tomorrow forever home road
car beach ocean sky light dark ghost queen king mama papa friend stranger memory secret story song music beat bass
drill trap afro reggaeton salsa funk soul jazz blues metal punk indie folk gospel house techno trance remix vip
cover version mix edit extended original live piano guitar violin""".split()
FALLBACK_TERMS = list(dict.fromkeys(FALLBACK_TERMS))  # de-duplicate, keep order


def fetch(search_query: str = "") -> list[dict]:
    params = {"audio_type": "music", "user_id": user_id, "access_token": token}
    if search_query:
        params["search_query"] = search_query
    r = requests.get(f"https://graph.facebook.com/{version}/ig_audio", params=params, timeout=60)
    try:
        data = r.json()
    except ValueError:
        raise SystemExit(f"Meta audio endpoint returned non-JSON HTTP {r.status_code}: {r.text[:500]}")
    if not r.ok or "error" in data:
        raise SystemExit("Meta audio search failed: " + json.dumps(data, ensure_ascii=False)[:1500])
    return [i for i in (data.get("audio") or data.get("data") or [])
            if isinstance(i, dict) and (i.get("audio_id") or i.get("id"))]


def aid(i):   return str(i.get("audio_id") or i.get("id"))
def name(i):  return str(i.get("title") or "").strip()
def who(i):   return str(i.get("display_artist") or i.get("ig_username") or "").strip()
def unused(items):  return [i for i in items if not used_audio.is_used(aid(i), name(i), who(i))]


query = " ".join(p for p in (title_in, artist_in) if p)
if query:
    items = fetch(query)
    if not items:
        raise SystemExit(f"Meta returned no audio for '{query}'. This song may not be in the API catalog. "
                         "Use audio_source=file with your own MP3 instead.")

    def score(i):
        t = difflib.SequenceMatcher(None, title_in.lower(), name(i).lower()).ratio() if title_in else 1
        a = difflib.SequenceMatcher(None, artist_in.lower(), who(i).lower()).ratio() if artist_in else 1
        return 0.6 * t + 0.4 * a
    track = max(items, key=score)
    if score(track) < 0.6:
        found = "; ".join(f"{name(i)} - {who(i)}" for i in items[:5])
        raise SystemExit(f"No close match for '{query}'. Meta returned: {found}")
    if used_audio.is_used(aid(track), name(track), who(track)):
        print("NOTE: this song was already posted before (explicit request, posting anyway).")
else:
    trending = fetch()
    pool = unused(trending)
    print(f"Trending tracks: {len(trending)}, not used before: {len(pool)}")
    if not pool:
        terms = FALLBACK_TERMS[:]
        random.shuffle(terms)
        for term in terms[:30]:
            found = unused(fetch(term))
            print(f"Search '{term}': {len(found)} unused")
            if found:
                pool = found
                break
    if not pool:
        raise SystemExit("No unused track found (all results were posted before). Try again later or post a specific song.")
    track = random.choice(pool)

audio_id = aid(track)
title = (name(track) or "Trending audio").replace("\n", " ")
artist = (who(track) or "Instagram audio").replace("\n", " ")
with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
    f.write(f"SONG_TITLE={title}\nARTIST_NAME={artist}\nIG_AUDIO_ID={audio_id}\n")
print(json.dumps({"title": title, "artist": artist, "audio_id": audio_id}, ensure_ascii=False))
