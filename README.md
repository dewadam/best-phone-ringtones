# Best Phone Ringtones

GitHub Actions-based Instagram Reels automation scaffold for the **Best Phone Ringtones** account.

## Current scope

- 9:16 (1080×1920) branded visual workflow.
- Scheduled/manual GitHub Actions entry point.
- Instagram Graph API publishing flow with an explicit dry-run safety default.
- Audio discovery and attachment are kept behind a provider adapter: only audio actually returned and permitted by the connected Meta API integration should be used.
- Publishing remains disabled until credentials, public video hosting, account permissions, and audio API access are configured and tested.

## Repository layout

- `assets/`: add the approved vertical neon template image as `template-9x16.png`.
- `src/render_reel.py`: creates a short vertical MP4 from the template using FFmpeg.
- `src/instagram_publish.py`: guarded Instagram Reels publishing flow.
- `src/audio_provider.py`: audio-provider interface and capability notes.
- `src/build_caption.py`: emoji-styled caption and SEO hashtag builder.
- `config/settings.json`: safe defaults.
- `.github/workflows/reels.yml`: scheduled/manual workflow.

## Setup

1. Upload the approved 9:16 poster to `assets/template-9x16.png`. Do not commit copyrighted audio files.
2. In repository **Settings → Secrets and variables → Actions**, configure the secrets below.
3. Configure a publicly accessible HTTPS base URL for rendered MP4 files. Instagram must be able to fetch the video URL directly.
4. Test with `DRY_RUN=true`. Confirm the generated video and API permissions before enabling publishing.

### Required secrets

- `IG_USER_ID`: Instagram professional account ID.
- `IG_ACCESS_TOKEN`: access token with the required publishing permissions.
- `PUBLIC_VIDEO_URL`: public HTTPS location where the rendered video can be fetched.
- `META_GRAPH_VERSION`: Graph API version approved for your app, e.g. `vXX.X` (set a currently supported version; do not copy an obsolete example).

Audio API availability may require additional app setup and permissions. Do not assume every sound shown in the Instagram mobile app is available through API. The integration should use the exact audio identifiers and parameters returned by Meta's authorized API.

## Reel captions: lyrics, emojis, SEO hashtags

The caption builder creates an emoji-styled caption with the track title/artist, a short hook, and relevant hashtags such as `#iPhoneRingtone`, `#Ringtone`, `#PhoneSounds`, plus artist/track tags. Hashtags are selected from the title and artist metadata and deduplicated.

**Lyrics handling:** do not scrape or reproduce full copyrighted lyrics. The builder accepts only a short lyric excerpt supplied by you or cleared for use; if none is supplied, it generates an original track-related hook instead.

Set `SONG_TITLE`, `ARTIST_NAME`, and optionally `LYRIC_EXCERPT` in repository Actions variables. Keep the excerpt short and authorized.

## Publishing safety

- Workflow defaults to dry-run; no Reel is published until `DRY_RUN=false` is explicitly configured.
- Check the account's live publishing quota and schedule before posting. Do not hardcode a universal daily limit.
- GitHub Actions schedule is a trigger, not a precise clock guarantee; hosted runners can start late.
- The visual template is promotional creative, not proof of music rights or account eligibility.
- Never put tokens in source files or commit them.

## Local rendering

Requires Python 3.10+ and FFmpeg on PATH.

```bash
python -m pip install -r requirements.txt
python src/render_reel.py --title "SONG TITLE" --artist "ARTIST NAME" --duration 15 --output output/reel.mp4
```

The renderer expects `assets/template-9x16.png`. Publishing is intentionally not part of this local command.
