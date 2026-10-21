#!/usr/bin/env python3
"""Find a track in Meta's Instagram Audio API (GET /ig_audio) and export its audio_id.

Docs: https://developers.facebook.com/docs/instagram-platform/content-publishing/audio-api/
- Needs Instagram API *with Facebook Login* (graph.facebook.com), Graph API v22.0+.
- The API has NO country filter, only `search_query`. Turkish songs are therefore recognised by
  (a) an artist from data/turkish_artists.txt or (b) Turkish-only letters (ş ğ ı İ) in title/artist.

CATEGORY (env): turkish | foreign | any
- turkish: trending tracks that look Turkish, otherwise searches Turkish artists from the list.
- foreign: trending tracks that are NOT Turkish, otherwise generic search terms.
Automatic mode never picks a track already posted (data/used_audio.json) and skips tracks shorter than the
Reel (29 s). If SONG_TITLE/ARTIST_NAME are set it searches for exactly that song instead.
"""
import difflib, json, os, random, sys
from pathlib import Path
import requests

sys.path.insert(0, os.path.dirname(__file__))
import used_audio
from used_audio import norm

ROOT = Path(__file__).resolve().parents[1]
version = os.getenv("META_API_VERSION", "v24.0")
token = os.getenv("IG_ACCESS_TOKEN", "").strip()
user_id = os.getenv("IG_USER_ID", "").strip()
title_in = os.getenv("SONG_TITLE", "").strip()
artist_in = os.getenv("ARTIST_NAME", "").strip()
category = os.getenv("CATEGORY", "any").strip().lower() or "any"
MIN_TRACK_MS = 29_000   # shorter tracks would end before the 29 s Reel does
if category not in ("turkish", "foreign", "any"):
    raise SystemExit(f"Unknown CATEGORY '{category}' (use turkish, foreign or any).")
if not token:
    raise SystemExit("Missing IG_ACCESS_TOKEN secret.")
if not user_id:
    raise SystemExit("Missing IG_USER_ID secret.")

# Used when trending has nothing new (foreign / any).
FALLBACK_TERMS = """love remix sped up slowed hip hop pop rock dance summer night acoustic instrumental lofi edm latin kpop
arabic bollywood country rnb party sad happy baby heart dream fire girl boy money city rain sun moon star
gold blue red black white wild crazy angel devil floor radio phone call tonight tomorrow forever home road
car beach ocean sky light dark ghost queen king mama papa friend stranger memory secret story song music beat bass
drill trap afro reggaeton salsa funk soul jazz blues metal punk indie folk gospel house techno trance vip
cover version mix edit extended original live piano guitar violin""".split()
FALLBACK_TERMS = list(dict.fromkeys(FALLBACK_TERMS))

TR_ONLY_LETTERS = set("ğĞıİşŞ")
TR_WORDS = {"gonul", "sevgilim", "canim", "gozlerin", "kalbim", "degil", "askim", "yalniz", "ozledim", "seviyorum"}


def load_turkish_artists() -> list[str]:
    f = ROOT / "data" / "turkish_artists.txt"
    names = []
    if f.is_file():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line not in names:
                names.append(line)
    return names


TURKISH_ARTISTS = load_turkish_artists()
ARTIST_KEYS = [(a, norm(a)) for a in TURKISH_ARTISTS if len(norm(a)) >= 4]


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


def is_turkish(i) -> bool:
    text = f"{name(i)} {who(i)}"
    if any(c in TR_ONLY_LETTERS for c in text):
        return True
    artist_key = norm(who(i))
    if any(key in artist_key for _, key in ARTIST_KEYS):
        return True
    return any(w in norm(name(i)) for w in TR_WORDS)


def long_enough(i) -> bool:
    d = i.get("duration_in_ms")
    return not isinstance(d, int) or d >= MIN_TRACK_MS


def in_category(i) -> bool:
    return category == "any" or (category == "turkish") == is_turkish(i)


def candidates(items):
    return [i for i in items
            if in_category(i) and long_enough(i) and not used_audio.is_used(aid(i), name(i), who(i))]


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
    pool = candidates(trending)
    print(f"[{category}] trending: {len(trending)}, usable (right category, long enough, unused): {len(pool)}")
    if not pool:
        if category == "turkish":
            terms = TURKISH_ARTISTS[:]
        else:
            terms = FALLBACK_TERMS[:]
        random.shuffle(terms)
        for term in terms[:40]:
            found = candidates(fetch(term))
            print(f"Search '{term}': {len(found)} usable")
            if found:
                # results come ranked by Meta's relevance: prefer the top few (= most popular) for Turkish artists
                pool = found[:5] if category == "turkish" else found
                break
    if not pool:
        raise SystemExit(f"No unused {category} track found right now. Try again later"
                         + (" or add more artists to data/turkish_artists.txt." if category == "turkish" else "."))
    track = random.choice(pool)

audio_id = aid(track)
title = (name(track) or "Trending audio").replace("\n", " ")
artist = (who(track) or "Instagram audio").replace("\n", " ")
with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as f:
    f.write(f"SONG_TITLE={title}\nARTIST_NAME={artist}\nIG_AUDIO_ID={audio_id}\n")
print(json.dumps({"title": title, "artist": artist, "audio_id": audio_id, "category": category,
                  "looks_turkish": is_turkish(track)}, ensure_ascii=False))
