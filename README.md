# Best Phone Ringtones

GitHub Actions automation scaffold for producing branded vertical Reels for the **Best Phone Ringtones** account.

## What is implemented

- Scheduled/manual GitHub Actions workflow.
- Neon/cyberpunk 1080×1920 visual with dynamic title/artist overlay.
- Caption and SEO hashtag generation, with lyrics optional.
- MP4 artifact retained for 7 days.
- Optional Azure Blob Storage upload that creates a read-only, time-limited SAS URL for Meta to fetch the video.
- Instagram publishing step guarded by explicit configuration; it is **not live-verified**.

## Important audio limitation

Meta's Audio API lookup in this repository is used for audio metadata discovery only. It does not download a music track or place the track's actual sound into the MP4. The current renderer creates a silent visual. Do **not** enable Instagram publishing for a real ringtone/music post until a licensed audio asset and a verified audio-mux step are configured. The Instagram publishing endpoint's standard Reels flow uses a publicly fetchable video URL; don't assume the audio metadata ID can be passed as a substitute for an actual audio track.

Use music you own or have permission to use. Do not scrape or redistribute copyrighted recordings or lyrics without permission.

## Azure setup

In repository **Settings → Secrets and variables → Actions**, add:

### Secret
- `AZURE_STORAGE_CONNECTION_STRING`: connection string for a storage account you control. Keep it in GitHub Secrets; never commit it.

### Variable
- `AZURE_STORAGE_CONTAINER`: existing blob container name. The uploader creates a short-lived, read-only SAS URL (default 48 hours) for the uploaded MP4. The account must permit the selected SAS authentication method. Azure SDK docs: [Get started with Azure Blob Storage and Python](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-python-get-started).

### Instagram configuration
Secrets:
- `IG_USER_ID`: Instagram professional account ID.
- `IG_ACCESS_TOKEN`: access token with the required publishing permissions.

Variables:
- `META_GRAPH_VERSION`: currently supported Graph API version for your Meta app.
- `META_AUDIO_TYPE`: optional; `music` (default) or `original_sound`.
- `DRY_RUN`: leave `true` until production checks are complete.
- `ENABLE_INSTAGRAM_PUBLISH`: leave `false` until the real audio path, account permissions, public video URL and test publish are verified.

Meta publishing reference: [Reels Publishing](https://www.postman.com/meta/instagram/folder/y6xustx/reels-publishing). Publishing requires an eligible professional account, the correct app/token permissions, and a video URL that Meta can fetch directly over HTTPS.

## Workflow behavior

1. Attempts to discover trending audio metadata through the configured Meta Audio API.
2. Uses fallback branding if the API call fails, so visual rendering can still be tested.
3. Builds the caption and hashtags.
4. Renders a 15-second, 1080×1920 MP4.
5. Uploads the MP4 as a GitHub Actions artifact.
6. If Azure settings are present, uploads the MP4 and creates a time-limited read URL.
7. Instagram publish is only attempted when `ENABLE_INSTAGRAM_PUBLISH=true`, `DRY_RUN=false`, Azure upload succeeds, and required Instagram settings exist. Audio is not yet production-ready, so keep this disabled.

The schedule is every two hours, at minute 17. GitHub Actions schedules are not exact-time guarantees. Reduce the frequency to once per day before running a production publishing account.

## Local rendering

Requires Python 3.10+ and FFmpeg on PATH.

```bash
python -m pip install -r requirements.txt
python src/render_reel.py --title "SONG TITLE" --artist "ARTIST NAME" --duration 15 --output output/reel.mp4
```

The renderer creates its own neon background if `assets/template-9x16.png` is absent. The output is currently silent and is for visual/pipeline testing only.
