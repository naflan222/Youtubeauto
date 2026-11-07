# One-time setup (including GitHub on Android)

## 1. Review a complete preview

In this repository, open **Actions → Preview and tests → latest successful run**. Expand the steps, then download the preview ZIP in **Artifacts**. If needed, choose **Run workflow → main** first. GitHub may ask you to enable Actions for the repository. Use Android Chrome's **Desktop site** if settings or download buttons are hidden.

Unzip and play `preview.mp4`. Read its script and `validation.json`. This pipeline does not treat a green unit test alone as a successful video preview. Uploads remain off while you review.

## 2. Prepare Google and YouTube

1. Sign in to the Google account that manages the intended YouTube channel. Create the channel first if necessary. Find its channel ID in **YouTube → Settings → Advanced settings**; it starts with `UC`.
2. In [Google Cloud Console](https://console.cloud.google.com/), create a project (for example, `Little Wonder Shorts`). Creating this project and using the default YouTube Data API quota does not require attaching billing. Do not enable paid services.
3. Open **APIs & Services → Library**, find **YouTube Data API v3**, and enable it.
4. Open **Google Auth platform** (or **APIs & Services → OAuth consent screen**). Configure branding, your support email, and your developer contact. Choose the appropriate audience, normally External for a personal account. Add yourself as a test user while setting up.
5. Add only these scopes: `https://www.googleapis.com/auth/youtube.upload` and `https://www.googleapis.com/auth/youtube.readonly`. Upload is needed to create/publish; read-only is needed to verify the channel and reconcile its uploads. No full channel-management scope or API key is required.
6. Create an OAuth **Desktop app** client and download its client JSON. Keep it private. Do not select a web/server client just to avoid the local consent step.

**Important for unattended operation:** an External OAuth app with publishing status **Testing** normally receives refresh tokens that expire after **7 days** for these scopes. Move the consent configuration to **In production**, satisfy any Google verification requirements shown for your use, and then authorize again to obtain a suitable refresh token. An unverified-app warning, user cap, organization policy, or consent verification requirement may still apply. Follow Google's current console guidance; do not bypass it. OAuth consent verification is distinct from YouTube quota/compliance audits.

## 3. Authorize once — Android or computer

**Using Android? Follow [ANDROID.md](ANDROID.md) for Termux, Chrome consent, and copying Secrets, then continue with section 4 below.** You do not need to install the video-rendering stack on the phone.

For the computer alternative, use a trusted computer with a browser, Python 3.12, and a local terminal. No video editing, paid machine, or always-on runtime is needed. This helper also works on a trusted Linux desktop environment with a local browser; a remote/headless environment needs its own correctly forwarded loopback browser access and is not the beginner default.

```bash
git clone https://github.com/naflan222/Youtubeauto.git
cd Youtubeauto
python -m venv .venv
```

Activate it:

```bash
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-oauth.txt
python tools/authorize.py --client /path/to/client_secret_download.json --expected-channel UC_YOUR_REAL_CHANNEL_ID
```

The browser opens Google's official consent screen. Choose the correct account and YouTube channel/Brand Account. The helper displays the actual authorized channel name and ID, rejects a mismatch, and saves the three values in local `oauth-secrets.txt` with private file permissions where supported. It does not print tokens. Never share the browser callback URL, client JSON, refresh token, or secret file in an issue or chat.

## 4. Add Secrets and channel configuration — Android is enough

In GitHub, use **Settings → Secrets and variables → Actions → Secrets → New repository secret** for each line in the local file:

| Secret name | Value |
| --- | --- |
| `YOUTUBE_CLIENT_ID` | Desktop client ID |
| `YOUTUBE_CLIENT_SECRET` | Desktop client secret |
| `YOUTUBE_REFRESH_TOKEN` | Offline refresh token |

Copy only the value after `=`, without quotes. Delete the local secret output afterward. Retain the client JSON securely only if needed for future reauthorization. Git ignores common credential filenames, but this is not a substitute for keeping secrets outside the checkout.

Edit `config.toml` with GitHub's pencil icon. Set `expected_channel_id` to your exact `UC…` ID. Change the channel branding if desired. Keep English unless you add a reviewed language pack. Commit the change. This triggers another credential-free preview.

## 5. Explicitly enable publication after a successful preview

1. Edit `config.toml`: change `upload_enabled = false` to `upload_enabled = true`.
2. Under **Settings → Secrets and variables → Actions → Variables**, create `UPLOAD_ENABLED` with value `true`. This is a variable, not a Google secret.
3. Open **Actions → Daily original Short → Run workflow**. Choose `publish`, then start it. The workflow checks that both opt-ins are enabled and the correct channel is authorized.
4. Watch the job summary. A successful live run includes the actual video URL and saves it on `shorts-state`. No upload has been proven until this happens with your account.
5. Daily runs use 12:45 UTC, approximately 6:15 PM Sri Lanka time. They upload privately first, wait for successful processing, and then request public status. Account restrictions can prevent publication; the job fails rather than claiming success.

To pause uploads, set the variable `UPLOAD_ENABLED` to `false`. Scheduled runs then render preview only, unless you disable the workflow entirely. Manual preview also never uploads, regardless of this variable. Pending recovery must be completed before another new daily upload.

Repository rules must allow the workflow's token to create/update `shorts-state`. If rules prohibit this, grant a narrowly scoped exception for that branch or adjust your own repository policy. Do not disable main-branch protection broadly. Actions workflow edits may require a GitHub credential with workflow permission when pushed from your own computer.

## 6. Occasional maintenance

The pack contains 40 unused episodes, so approximately 40 successful publishing days are available. The job fails clearly on exhaustion. Add new, substantively different reviewed episodes in `shorts/content.py`, source educational claims, run tests/preview, and inspect the result. Do not reset state to republish the pack. No daily editing or uploading is required during normal operation.

Watch GitHub's failure notifications and summaries. Re-enable inactive schedules when necessary. Google can revoke refresh tokens, impose account-level limits, or require additional verification. Reauthorize with the same helper and replace Secrets if that happens. Dependency and model hosts are external availability dependencies even though no service is billed.
