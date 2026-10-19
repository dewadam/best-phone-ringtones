"""Audio-provider boundary: use only audio IDs returned by authorized Meta API."""
from dataclasses import dataclass

@dataclass(frozen=True)
class AudioChoice:
    audio_id: str
    title: str | None = None
    artist: str | None = None
    source: str = "meta_authorized_api"

def validate_audio_choice(choice: AudioChoice) -> AudioChoice:
    if not choice.audio_id or not choice.audio_id.strip():
        raise ValueError("A non-empty audio ID returned by the authorized API is required.")
    if choice.source != "meta_authorized_api":
        raise ValueError("Only audio from the configured authorized Meta API is accepted.")
    return choice

def find_trending_audio() -> list[AudioChoice]:
    """Not enabled until the connected app's audio endpoint and permissions are verified."""
    raise NotImplementedError(
        "Configure and verify the official Meta audio endpoint, app permissions, "
        "and response schema before enabling automatic audio discovery."
    )
