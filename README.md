# Best Phone Ringtones

GitHub Actions Reel builder for the **Best Phone Ringtones** Instagram account.

## Current workflow

- Builds a 1080×1920, 30 FPS vertical MP4.
- Displays the selected song title and artist.
- Creates a caption/hashtag file.
- Validates the MP4 with FFmpeg/ffprobe.
- Supports preview-only builds by default.
- Has an optional Instagram publishing step using Meta's Instagram API with Facebook Login and Audio API.
- Contains no Azure dependency.

## Run a preview

Open **Actions → Best Phone Ringtones Reel Builder → Run workflow**.

Inputs:
- `song_title`: track title (example: `TRALALA`)
- `artist_name`: artist (example: `Manifest`)
- `duration`: 3–90 seconds (default 30)
- `publish_now`: leave unchecked to create a preview only; check it only after the Meta app, account, permissions and repository secrets are configured.

The MP4 contains the soundtrack from `assets/audio/` (see below). It is saved as a GitHub Actions artifact when publishing is not requested.

## Adding sound (important)

The template MP4's own audio track is digital silence, so the video is silent unless a soundtrack is added. Two modes (`audio_source` input):

- **instagram** (default, also used by the daily schedule): Meta's [Instagram Audio API](https://developers.facebook.com/docs/instagram-platform/content-publishing/audio-api/) searches the catalog (`GET /ig_audio?audio_type=music&user_id=...&search_query=...`) and the Reel is created with `audio_configuration={"audio_id":...}`. Needs Facebook Login, Graph API v22+ and `instagram_basic` + `instagram_content_publish`. Only audio authorized for third-party use is returned, so a specific song may not exist; then the run fails instead of posting silently.
- **file**: upload `Artist - Title.mp3` to `assets/audio/`; it is mixed into the MP4 (fade + loudness normalisation). The run fails if the result is silent. Use music you own/licensed; Instagram may mute copyrighted audio.

**How instagram mode uploads:** Meta documents `audio_configuration` only with `video_url`, so on publish the MP4 is pushed to a temporary `reel-staging` branch and Instagram downloads it from `raw.githubusercontent.com` (the repository must be **public**; the branch is deleted after the run). The resumable upload is only a fallback and does not attach catalog music.

## Configure Instagram API publishing

The publishing step is deliberately opt-in. Before using it:

1. Use an Instagram **Business or Creator** account and connect the required Facebook Page for the Facebook Login flow.
2. Create/configure a Meta developer app and obtain the appropriate access token and permissions for Instagram audio search and content publishing.
3. In GitHub repository **Settings → Secrets and variables → Actions → Secrets**, add:
   - `IG_USER_ID`: Instagram professional account ID.
   - `IG_ACCESS_TOKEN`: valid token with the required permissions.
4. Optionally set repository variable `META_API_VERSION` to the Graph API version enabled for your app (default in workflow: `v24.0`).
5. Run a manual workflow with the exact song title and artist. Enable `publish_now` only when you intend to publish publicly.

The script searches Instagram's available catalog audio using the song title and artist, chooses the closest returned match, creates a resumable Reel container with the selected audio, waits for processing, then publishes. Audio catalog availability can differ from the Instagram mobile app and may be restricted by account type, region, licensing, app review, or permissions. If lookup/attachment is rejected or no usable result is returned, the workflow fails rather than intentionally publishing without the requested track.

**Important:** API support and access must be validated for the specific Meta app/account. Do not paste access tokens into source code, workflow inputs, issues, or logs. Keep tokens in GitHub Actions secrets. The first live run publishes a real Reel; there is no simulated publishing mode once `publish_now` is enabled.

## Template video

The renderer currently uses `assets/template-9x16.png` as a still background if present, otherwise it generates a fallback background. To use the user-supplied 30-second MP4 as the actual template, commit it to the repository and update the renderer to preserve its existing animation while overlaying only the song title. The supplied MP4 has not yet been added to this repository, so the current renderer does **not** use it.

## Local render

Requires Python 3.10+ and FFmpeg.

```bash
python -m pip install -r requirements.txt
python src/render_reel.py --title "Song Title" --artist "Artist Name" --duration 30 --output output/reel.mp4
```
