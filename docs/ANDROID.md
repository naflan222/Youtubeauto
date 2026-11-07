# Set up from an Android phone

You can manage GitHub and Google Cloud in Chrome, then run the one-time Python authorization helper in **Termux**. Your phone only needs to stay running during authorization. GitHub renders and uploads the daily videos afterward.

This guide uses the same personal Python CLI and Desktop OAuth client as the computer helper; it is not a native Android OAuth app. Helper behavior is tested on Linux, but an actual Android/Google consent session has not been tested with your account. Google's [loopback migration rules](https://developers.google.com/identity/protocols/oauth2/resources/loopback-migration) distinguish Desktop clients from deprecated Android/iOS/Chrome client loopback flows. Follow current Google requirements if your account blocks consent; do not bypass a block or use an embedded sign-in browser.

## 1. Prepare your channel and Google project in Chrome

Use Chrome's **⋮ → Desktop site** when buttons are hidden.

1. Open [YouTube advanced settings](https://www.youtube.com/account_advanced), signed into the intended channel. Copy the **Channel ID**, which is 24 characters starting with `UC`. This is not your `@handle` or a video ID. Keep this ID in a note; it is not a secret.
2. Follow [Google project and OAuth setup, section 2](SETUP.md#2-prepare-google-and-youtube). Enable **YouTube Data API v3**. Create a **Desktop app** OAuth client for this personal Python script, including when using Termux. Do not create an Android client for this helper.
3. Download the client JSON on this phone. In Android's Files app, rename that downloaded file to **`client_secret.json`** and leave it in **Downloads** for the next step. It is private; never attach it to a chat or issue.
4. Check your OAuth publishing status. External apps in **Testing** normally issue seven-day refresh tokens for YouTube scopes. Appropriate Production configuration and a fresh authorization are needed for unattended use beyond that period; comply with any verification Google requires.

## 2. Install Termux and the small authorization environment

Install [Termux from F-Droid](https://f-droid.org/packages/com.termux/), following the [official Termux installation instructions](https://github.com/termux/termux-app#installation). Termux is free. Keep Termux and any Termux add-ons from the same installation source. No add-ons are required here.

Open Termux. Paste these commands, one block at a time. Allow package installation prompts if shown:

```bash
pkg update -y
pkg install -y python git
termux-setup-storage
```

Android will ask for storage permission. Allow it so Termux can read the JSON from Downloads. If permission is not granted, check Android **Settings → Apps → Termux → Permissions** and run `termux-setup-storage` again.

```bash
git clone https://github.com/naflan222/Youtubeauto.git
cd Youtubeauto
python -m venv .venv-oauth
source .venv-oauth/bin/activate
python -m pip install -r requirements-oauth.txt
```

If you already cloned this repository, use `cd ~/Youtubeauto` and `git pull --ff-only` instead of cloning again. Do not install `requirements.lock`, Piper, or FFmpeg on your phone. Those are for the Linux video runner; this smaller file is only for authorization.

Create private local storage and copy in the downloaded client:

```bash
mkdir -p "$HOME/.config/youtubeauto"
chmod 700 "$HOME/.config/youtubeauto"
cp "$HOME/storage/downloads/client_secret.json" "$HOME/.config/youtubeauto/client.json"
chmod 600 "$HOME/.config/youtubeauto/client.json"
```

If the copy says the file is missing, check its exact name in Downloads and storage permission. The destination is private Termux app storage, outside the repository.

## 3. Authorize your channel

Replace `UC_YOUR_REAL_CHANNEL_ID` below with the actual Channel ID copied in step 1. Keep the quotation marks:

```bash
python tools/authorize.py \
  --client "$HOME/.config/youtubeauto/client.json" \
  --expected-channel "UC_YOUR_REAL_CHANNEL_ID" \
  --output "$HOME/.config/youtubeauto/oauth-secrets.txt" \
  --manual-browser
```

Termux prints a Google consent link. Open that entire link in **Chrome on this same phone**. Keep Termux running in the background; do not swipe it away or close its terminal session. If Android kills background apps, temporarily allow Termux unrestricted battery use while authorizing, keep the phone awake, and restore your preferred battery setting afterward.

Choose the correct Google account and YouTube channel/Brand Account. Complete Google's consent process. The browser returns to a local `127.0.0.1` callback on your phone; that is the helper's temporary listener. It waits for up to ten minutes. Return to Termux afterward.

The helper checks the authorized channel against your expected ID. Only a match saves the private `oauth-secrets.txt` file. A mismatch saves no secrets. Do not share the consent link, callback URL, screenshots containing credentials, or output file.

## 4. Copy the values into GitHub Secrets

Only on your own phone, display the private local file:

```bash
cat "$HOME/.config/youtubeauto/oauth-secrets.txt"
```

In Chrome, open [your repository's Actions Secrets](https://github.com/naflan222/Youtubeauto/settings/secrets/actions). If needed, use Desktop site. Tap **New repository secret** for each of these:

| Name | Copy from the local file |
| --- | --- |
| `YOUTUBE_CLIENT_ID` | Value after `YOUTUBE_CLIENT_ID=` |
| `YOUTUBE_CLIENT_SECRET` | Value after `YOUTUBE_CLIENT_SECRET=` |
| `YOUTUBE_REFRESH_TOKEN` | Value after `YOUTUBE_REFRESH_TOKEN=` |

In Termux, long-press to select/copy a value. Paste **only the value**, without the name, `=`, quotation marks, spaces, or line breaks. Do not paste these values here in chat. Delete the local output once all three Secrets have been saved:

```bash
rm "$HOME/.config/youtubeauto/oauth-secrets.txt"
clear
```

Clear any clipboard entry containing a secret. Delete the Downloads copy of `client_secret.json` using Android Files. You can keep `client.json` in the private Termux directory for future reauthorization, or delete that copy too; you can download the Desktop client's JSON again from Cloud Console if needed.

## 5. Configure GitHub and run the first publication

1. Open [`config.toml`](https://github.com/naflan222/Youtubeauto/blob/main/config.toml), tap the pencil/Edit button, and set `expected_channel_id` to the same `UC…` Channel ID. Save the change with **Commit changes**.
2. Open **Actions → Preview and tests**. Wait for a successful run, download its artifact ZIP, and play `preview.mp4`. If artifacts have expired, use **Run workflow** to render another preview.
3. After reviewing that preview, edit `config.toml` again and set `upload_enabled = true`.
4. Under **Settings → Secrets and variables → Actions → Variables**, create a repository variable named `UPLOAD_ENABLED` with value `true`. This is separate from the three Secrets.
5. Open **Actions → Daily original Short → Run workflow**. Select **publish**, then run it. Read the job summary; it must show the real YouTube URL before treating publication as successful.

The daily schedule then targets approximately **6:15 PM Sri Lanka time**. Your phone can be off. To pause uploads, set the variable `UPLOAD_ENABLED` to `false`.

## If something fails

- **Can't see Google Cloud or GitHub controls:** enable Chrome Desktop site and rotate the phone if necessary.
- **Google rejects consent/client type:** verify you downloaded the intended Desktop client for this CLI and follow Google's error guidance. Do not use a third-party token generator or bypass the restriction. A trusted computer is the fallback if this phone/account cannot complete the flow.
- **Callback says connection refused:** Termux may have stopped. Keep it open, check Android battery settings, and start authorization again. Open the link on the same phone, not a second device.
- **Ten minutes passed:** restart the helper and use the new consent link. Old links/callbacks are not reusable.
- **Wrong channel:** rerun and select the intended account/channel. Do not change the expected ID just to suppress the check.
- **Output exists:** check whether you already saved the matching Secrets. Remove the old private output deliberately before generating a replacement.
- **Dependencies fail:** copy the error text with any secrets removed; do not install the full rendering stack as a workaround. Termux package availability varies by Android version/architecture.
- **Live run stops:** read [recovery instructions](RECOVERY.md), especially before retrying an ambiguous upload.

The 40-episode content limit, approximate scheduling, free-service limits, and occasional maintenance still apply; see [LIMITS.md](LIMITS.md).
