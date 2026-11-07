# Little Wonder Friends — daily original YouTube Shorts

A free-software Python pipeline that makes a complete original educational Short locally, validates it, and can publish it using the official YouTube Data API. **Uploads are OFF by default.** No LLM API, purchased assets, credit card, background server, or daily editing is needed.

Pip Bunny and Tilly Turtle explore counting, colors, shapes, animal facts, kindness, visual puzzles, nature, space, and short stories. The repository includes **40 distinct, authored episodes**, five scenes each. It deliberately stops after these are used: add another reviewed content pack for continued operation. It does not pretend a finite template library can create unlimited original stories.

## Verified sample and workflows

[Download the complete video artifact ZIP](https://github.com/naflan222/Youtubeauto/actions/runs/42343665314/artifacts/13562124110) · [Script and metadata](examples/sample/script.json) · [Sample story](docs/SAMPLE.md)

Unzip the artifact and play `preview.mp4`. Artifacts expire after three days; rerun **Preview and tests** for a new video. Small sample scripts/reports remain in `examples/sample/`; videos are never committed to Git.

Both the [preview workflow](https://github.com/naflan222/Youtubeauto/actions/runs/42343665314) and the [daily workflow in preview mode](https://github.com/naflan222/Youtubeauto/actions/runs/42343665116) succeeded. The sample is 31.9 seconds, 1080 × 1920, 30 fps, with narrated captions. Local tests: 58 passed. See [observed verification and remaining account-dependent checks](docs/VERIFICATION.md). No live YouTube upload has been attempted.

## Start here

1. Open **Actions → Preview and tests**. A push to `main` automatically renders a complete sample; alternatively choose **Run workflow**. Download the `preview-…` artifact to watch `preview.mp4` and read `script.json`, captions, and the validation report.
2. Follow **[one-time account setup](docs/SETUP.md)**. For Android, use the dedicated **[phone-only Termux guide](docs/ANDROID.md)** for the one-time consent step. A computer is an alternative; no always-on device is needed afterward.
3. Set your expected YouTube channel ID in `config.toml`. Add the three Google values to **Actions Secrets**. Never commit them.
4. After reviewing a successful preview, change `upload_enabled = true` in `config.toml` and create repository **Actions variable** `UPLOAD_ENABLED` with value `true`. Both opt-ins are required. Manually run **Daily original Short → publish** for the first live test.
5. The daily workflow then runs at **12:45 UTC / 6:15 PM Asia/Colombo**, approximately. YouTube processing adds time; GitHub does not guarantee exact starts or publication times.

**Before enabling:** [limits and current platform documentation](docs/LIMITS.md), [recovery and troubleshooting](docs/RECOVERY.md), [asset and dependency rights](docs/LICENSES.md).

## What it produces

- 1080 × 1920 portrait MP4, 30 fps, approximately 32 seconds (configurable within 25–40).
- Original Pillow graphics, recurring characters, gentle motion, safe text margins, and a complete final frame. Graphics use a 540 × 960 logical canvas and Lanczos scaling to the 1080p delivery frame.
- Offline Piper narration with a pinned, checksum-verified LJSpeech model. No music or third-party video clips.
- Captions burned into the video and an SRT sidecar. Captions use **measured sentence/scene timing**, not word-level highlighting.
- Accurate title under 65 characters, description, three relevant hashtags including `#Shorts`, and API tags.
- `script.json`, `script.txt`, `timeline.json`, `caption-layout.json`, sample scene images, `validation.json`, and, after publication, `result.json`.

The category is resolved separately through `videoCategories.list` (Education by default). There is no Reels or Shorts upload endpoint; the official API receives a short portrait video. YouTube decides how it is presented. No growth, monetization, viral performance, or YouTube Kids placement is promised.

## Run a preview on a computer

Linux / Python 3.12:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu-core python3-venv
git clone https://github.com/naflan222/Youtubeauto.git
cd Youtubeauto
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
python -m shorts.cli preview
```

The first preview downloads the approximately 63 MB voice model from Hugging Face. Later previews use its verified cache. On Windows/macOS, install Python and FFmpeg and provide the DejaVu font paths in `shorts/graphics.py`, or use an Ubuntu environment. GitHub-hosted Ubuntu is the supported unattended runtime.

`python -m shorts.cli preview` uses no OAuth credentials and never uploads or changes live state. Direct local publication is intentionally blocked because it would evade the serialized workflow's duplicate protection.

## Configuration and daily operation

`config.example.toml` documents all defaults; `config.toml` is the active file. Channel branding, audience description, duration bounds, expected channel, region, category, and schedule are configurable. The reviewed content and default voice support simple English only: unsupported languages fail instead of silently publishing English under a different label. A new audience or language needs an appropriately reviewed content/voice pack. Child-directed uploads always remain made for kids.

Changing `timezone` or `target_time` does **not** rewrite Actions YAML. Update the cron in `.github/workflows/daily.yml` too, calculating UTC for the intended timezone; test the new conversion. Asia/Colombo has no daylight-saving adjustment. Dimensions and frame rate are deliberately locked to the tested Shorts profile.

The live stages check credentials/channel, choose an unused story, generate metadata, synthesize narration/captions, render, validate, reconcile channel uploads, upload privately, verify processing, publish, and persist the URL. Known unfinished uploads are resumed before new rendering. An unresolved earlier day blocks later publication until recovered.

State is small JSON on **`shorts-state`**, separate from source. It records the daily job ID, topic, theme, script fingerprint, status, video ID, URL, and completion time. The branch is created automatically on the first enabled run. Do not delete it or force-push it. Rendered videos and credential files are ignored by Git. Review artifacts expire after **3 days**; download samples you wish to keep.

Discovery makes at most one ten-result `mostPopular` API request per new live episode, using observed terms only as inspiration for independently reviewed stories. It never downloads trending media or claims search volume. Unsafe results and unrelated topics are ignored. Missing or unsuitable data leads to an explicitly labeled `evergreen-fallback`. Preview uses that fallback without credentials. Discovery provenance is in short-lived `script.json`, never in permanent state.

## Project layout

| Area | Responsibility |
| --- | --- |
| `shorts/content.py`, `selection.py` | Reviewed episodes, metadata, conservative trend inspiration, no-repeat selection |
| `shorts/narration.py`, `graphics.py`, `render.py` | Offline speech, synchronized captions, original graphics, FFmpeg |
| `shorts/validate.py` | ffprobe, audio/black-gap checks, captions, metadata, licenses, duplicates |
| `shorts/youtube.py`, `state.py`, `cli.py` | OAuth client, resumable upload, recovery, durable journal, stages |
| `tools/authorize.py` | One-time local consent helper |
| `.github/workflows/` | Credential-free preview and serialized daily/manual publication |
| `tests/` | Content layouts, schedule, duplicate prevention, interrupted upload recovery |
| `LICENSES.json`, `voice.lock.json`, `requirements.lock` | Dependency/asset rights, model checksums, pinned Python versions |

The renderer validates mechanical quality, not every educational or artistic judgment. Facts and scripts are authored and source-linked; review additions before enabling them. Occasional maintenance includes adding original episodes, checking workflow inactivity, updating dependencies or platform policies, and renewing revoked Google authorization. See the limits guide for details.
