"""Best-effort lyrics-page fetcher; no third-party lyrics API required.

Searches public web results, fetches a page from an allowlisted lyrics domain,
extracts a small excerpt, and gracefully returns empty text on failure.
Respect site terms, robots guidance, and copyright requirements.
"""
from __future__ import annotations

import html
import re
import sys
import time
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "BestPhoneRingtonesBot/1.0 (public metadata lookup; contact via repository)"
ALLOWED_HOSTS = {"lyricstranslate.com", "www.lyricstranslate.com", "azlyrics.com", "www.azlyrics.com"}
MAX_EXCERPT_CHARS = 90
TIMEOUT = 15


class LyricsFetchError(RuntimeError):
    pass


def _clean(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\[[^\]]{1,40}\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS


def _get(url: str) -> requests.Response:
    if not _allowed_url(url):
        raise LyricsFetchError("Lyrics URL is not on the allowlist.")
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"},
        timeout=TIMEOUT,
    )
    if response.status_code in (403, 429):
        raise LyricsFetchError(f"Lyrics site denied automated access (HTTP {response.status_code}).")
    response.raise_for_status()
    return response


def extract_lyrics_from_html(url: str, page_html: str) -> str:
    if not _allowed_url(url):
        raise LyricsFetchError("Lyrics URL is not on the allowlist.")
    soup = BeautifulSoup(page_html, "html.parser")
    candidates = []

    host = urlparse(url).hostname or ""
    if "lyricstranslate.com" in host:
        selectors = (
            ".lyric-text", ".lyrics", "[class*='lyric-text']",
            "[class*='LyricsText']", "article",
        )
        for selector in selectors:
            for node in soup.select(selector):
                text = _clean(node.get_text(" ", strip=True))
                if len(text) > 80:
                    candidates.append(text)
    elif "azlyrics.com" in host:
        # AZLyrics commonly places lyrics in an unclassed div after the album metadata.
        for node in soup.select("div:not([class]):not([id])"):
            text = _clean(node.get_text(" ", strip=True))
            if len(text) > 80 and ("<" not in text and ">" not in text):
                candidates.append(text)

    if not candidates:
        # Generic fallback for common lyrics-page containers, without bypassing blocks.
        for selector in ("[data-lyrics-container='true']", "div[class^='Lyrics__Container']", ".lyrics"):
            for node in soup.select(selector):
                text = _clean(node.get_text(" ", strip=True))
                if len(text) > 80:
                    candidates.append(text)

    if not candidates:
        raise LyricsFetchError("No recognizable lyrics container found in the returned HTML.")
    # Choose the smallest plausible lyrics block, avoiding the whole page/article.
    lyrics = min(candidates, key=len)
    return lyrics[:MAX_EXCERPT_CHARS].rstrip()


def find_lyrics_excerpt(title: str, artist: str) -> dict[str, str]:
    query = f'site:lyricstranslate.com OR site:azlyrics.com "{title}" "{artist}" lyrics'
    search_url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    response = requests.get(
        search_url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.8"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for anchor in soup.select("a.result__a, a[href]"):
        href = anchor.get("href", "").strip()
        parsed = urlparse(href)
        if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            href = unquote(target) if target else ""
        if _allowed_url(href) and href not in links:
            links.append(href)
    if not links:
        raise LyricsFetchError("Search returned no allowed lyrics-page links.")

    errors = []
    for url in links[:5]:
        try:
            page = _get(url)
            excerpt = extract_lyrics_from_html(url, page.text)
            if excerpt:
                return {"excerpt": excerpt, "source_url": url}
        except (requests.RequestException, LyricsFetchError) as exc:
            errors.append(f"{url}: {exc}")
        time.sleep(1.0)

    raise LyricsFetchError("No lyrics excerpt could be extracted. " + " | ".join(errors[:3]))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python src/lyrics_scraper.py \"SONG TITLE\" \"ARTIST NAME\"", file=sys.stderr)
        sys.exit(2)
    try:
        result = find_lyrics_excerpt(sys.argv[1], sys.argv[2])
        print(result["excerpt"])
        print(f"Source: {result['source_url']}", file=sys.stderr)
    except Exception as exc:
        print(f"Lyrics lookup unavailable: {exc}", file=sys.stderr)
        sys.exit(1)
