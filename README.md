# Best Phone Ringtones

GitHub Actions-based Instagram Reels automation scaffold for the **Best Phone Ringtones** account.

## Current scope

- 9:16 (1080×1920) branded visual workflow.
- Scheduled/manual GitHub Actions entry point.
- Instagram Graph API publishing flow with an explicit dry-run safety default.
- `src/audio_provider.py` requests trending audio from Meta's Instagram Audio API and selects one returned record; the workflow passes that returned audio ID and metadata to captioning/publishing.
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

## Meta Audio API: how song selection works\n\nThe workflow calls `GET /{ig-user-id}/ig_audio?audio_type=music` using the configured Graph API version and user access token. Meta returns a list of audio records; the workflow selects one record from that response and uses its exact ID, title, and artist metadata when available. Set the optional Actions variable `META_AUDIO_TYPE` to `original_sound` to request original sounds instead of music. With no search query, Meta's documented behavior is to return trending audio. The API's eligible catalog can differ from the music picker in the Instagram app.\n\nRequirements include an Instagram Business or Creator account, a connected Facebook Page, a Facebook app using **Facebook Login**, and the `instagram_basic` and `instagram_content_publish` permissions. Meta documents that the Audio API is not supported through Instagram Login. The app/token must actually have access; this repository change does not prove that your account's credentials are configured or that a live request succeeds. See [Meta Audio API documentation](https://developers.facebook.com/docs/instagram-platform/content-publishing/audio-api).

## Reel captions: lyrics, emojis, SEO hashtags

The caption builder creates an emoji-styled caption with the track title/artist, a short hook, and relevant hashtags such as `#iPhoneRingtone`, `#Ringtone`, `#PhoneSounds`, plus artist/track tags. Hashtags are selected from the title and artist metadata and deduplicated.

**Lyrics handling:** Meta's Audio API provides audio selection/metadata, not lyrics. Automatic lyrics scraping is currently paused because public pages and search results were unreliable in GitHub Actions. This does not block caption generation: when `LYRIC_EXCERPT` is empty, the caption builder uses an original promotional hook. Only provide an excerpt you have permission to use. `SONG_TITLE` and `ARTIST_NAME` come from Meta's selected audio response when available. The lyrics-source probe is now manual and separate from the publishing workflow.

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
