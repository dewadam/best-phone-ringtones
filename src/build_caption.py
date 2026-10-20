#!/usr/bin/env python3
"""Build an emoji-styled Reel caption with track-aware SEO hashtags.

Only use LYRIC_EXCERPT when supplied by the user or cleared for use.
Without it, create an original hook rather than reproducing copyrighted lyrics.
"""
from __future__ import annotations
import os
import re
import unicodedata

GENERIC_TAGS = [
    "iPhoneRingtone", "Ringtone", "PhoneSounds", "ReelsMusic",
    "RingtoneIdeas", "BestPhoneRingtones",
]

def slug_hashtag(value: str) -> str:
    # Preserve the conventional brand casing for this core SEO tag.
    if value.casefold() == "iphoneringtone":
        return "iPhoneRingtone"
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    words = re.findall(r"[A-Za-z0-9]+", value)
    return "".join(word[:1].upper() + word[1:] for word in words)[:45] if words else ""

CTA = (
    "📌 Want to make this your iPhone ringtone? Watch the video pinned on our profile!\n"
    "📌 iPhone'unuza zil sesi nasıl yapılır merak ediyorsanız profilimizde sabitlenmiş videoyu izleyin!"
)

def build_caption(title: str, artist: str, lyric_excerpt: str = "") -> str:
    title = " ".join(title.split()).strip()
    artist = " ".join(artist.split()).strip()
    if not title or not artist:
        raise ValueError("SONG_TITLE and ARTIST_NAME must both be set.")
    excerpt = " ".join(lyric_excerpt.split()).strip()
    if len(excerpt) > 90:
        raise ValueError("LYRIC_EXCERPT must be 90 characters or fewer.")
    hook = f'🎶 “{excerpt}” ✨' if excerpt else "✨ A fresh sound for your next ringtone mood!"
    tags = []
    for raw in (title, artist, *GENERIC_TAGS):
        tag = slug_hashtag(raw)
        if tag and tag.lower() not in {t.lower() for t in tags}:
            tags.append(tag)
    tags = tags[:12]
    return (
        CTA + "\n\n"
        f"🎧 {title} — {artist}\n{hook}\n"
        "📱 Want this vibe as your iPhone ringtone? Save this Reel and explore more sounds! 💫\n\n"
        + " ".join("#" + tag for tag in tags)
    )

if __name__ == "__main__":
    print(build_caption(
        os.getenv("SONG_TITLE", ""),
        os.getenv("ARTIST_NAME", ""),
        os.getenv("LYRIC_EXCERPT", ""),
    ))
