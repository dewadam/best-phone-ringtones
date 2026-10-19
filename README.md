# Best Phone Ringtones

GitHub Actions Reel builder for the **Best Phone Ringtones** Instagram page.

## Scope

This repository currently builds a vertical Reel visual and saves it as a downloadable GitHub Actions artifact. Instagram API integration is intentionally the only major remaining stage.

- Fixed 9:16 layout at 1080×1920, 30 FPS.
- Displays the selected song title and artist on the visual.
- Uses `assets/template-9x16.png` as the background when that file exists; otherwise the renderer generates its built-in neon background.
- Builds an original caption and relevant hashtags.
- Validates the rendered MP4 and retains the artifact for 7 days.
- No Azure dependency, cloud storage uploader, API token, or Instagram publish call is included in this stage.

## Run a Reel build

Open **Actions → Best Phone Ringtones Reel Builder → Run workflow** and provide:
- `song_title`: song title to display.
- `artist_name`: artist to display.
- `duration`: 3–90 seconds (default 15).

The daily schedule creates a default sample artifact. A manually dispatched run can use the chosen track details.

## Instagram music and publishing: next stage

The current MP4 is a silent visual. Song title/artist text is only metadata shown on the image; it does not select or attach the corresponding Instagram catalog track.

The next integration must use Meta's currently authorized Instagram publishing/audio flow to:
1. Search/select the exact catalog audio track by title and artist (where the connected account and API permissions support it).
2. Create the Reel using the existing visual and selected catalog audio.
3. Publish it and verify the resulting media status.

Do not assume a generic `audio_id` parameter is supported just because an audio lookup endpoint returns an ID. Verify the current official Meta API flow and account eligibility before wiring publishing. Until that integration is implemented and tested, this workflow does not publish to Instagram.

## Local render

Requires Python 3.10+ and FFmpeg.

```bash
python -m pip install -r requirements.txt
python src/render_reel.py --title "Song Title" --artist "Artist Name" --duration 15 --output output/reel.mp4
```
