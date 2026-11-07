#!/usr/bin/env python3
"""One-time local OAuth on a computer or Android/Termux; never run in Actions."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import webbrowser

# A cloned checkout plus requirements-oauth.txt is enough on Android. Do not
# import the renderer or require an editable installation of the full project.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shorts.oauth import SCOPES
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession
from google.auth.exceptions import GoogleAuthError
from requests.exceptions import RequestException


def configure_browser(manual):
    """Use Termux's external browser launcher when available, never a WebView."""
    launcher = shutil.which('termux-open-url')
    if not manual and launcher:
        webbrowser.register('termux', None, webbrowser.BackgroundBrowser([launcher, '%s']), preferred=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True, help='Downloaded Desktop OAuth client JSON')
    parser.add_argument('--expected-channel', required=True)
    parser.add_argument('--output', type=Path, default=Path('oauth-secrets.txt'))
    parser.add_argument('--manual-browser', action='store_true', help='Print the consent link; open it in Chrome on this same phone/computer')
    args = parser.parse_args()
    if not re.fullmatch(r'UC[A-Za-z0-9_-]{22}', args.expected_channel):
        raise SystemExit('Expected channel ID must be the 24-character UC… ID from YouTube advanced settings')
    if args.output.exists():
        raise SystemExit('Output exists; remove it securely before authorizing again')
    if not args.output.parent.is_dir():
        raise SystemExit('Create a private output directory first; see docs/ANDROID.md')
    try:
        client = json.loads(args.client.read_text())
    except (OSError, ValueError):
        raise SystemExit('Cannot read client JSON. Check --client and download a Desktop app OAuth client.') from None
    if 'installed' not in client:
        raise SystemExit('Use a Desktop app OAuth client, including on Termux; other client types are not supported by this helper')
    configure_browser(args.manual_browser)
    flow = InstalledAppFlow.from_client_config(client, SCOPES)
    print('Keep this terminal running. Complete consent in your external browser on this same device.')
    print('The local callback waits up to ten minutes. Do not share the consent or callback URLs.')
    try:
        credentials = flow.run_local_server(
            host='127.0.0.1', bind_addr='127.0.0.1', port=0,
            access_type='offline', prompt='consent',
            open_browser=not args.manual_browser, timeout_seconds=600,
            authorization_prompt_message='Open this link in Chrome on this same device:\n{url}',
            success_message='Google consent completed. Return to your terminal for the channel verification result.',
        )
    except Exception:
        # OAuth exceptions can include request details. Keep private data out of logs.
        raise SystemExit('Consent did not complete. Keep Termux running, use Chrome on this same device, and retry. See docs/ANDROID.md.') from None
    if credentials is None or not credentials.refresh_token:
        raise SystemExit('No offline refresh token returned. Check consent completion; revoke this client grant and retry if necessary.')
    try:
        with AuthorizedSession(credentials) as session:
            response = session.get('https://www.googleapis.com/youtube/v3/channels', params={'part':'snippet', 'mine':'true'}, timeout=30)
            response.raise_for_status()
            channels = response.json().get('items', [])
    except (RequestException, ValueError, GoogleAuthError):
        raise SystemExit('Google channel lookup failed. Check internet access, API enablement, and consent, then retry.') from None
    if len(channels) != 1:
        raise SystemExit('Authorization must identify one YouTube channel. No secrets saved.')
    channel = channels[0]
    print('Authorized channel:', channel['snippet']['title'], '(' + channel['id'] + ')')
    if channel['id'] != args.expected_channel:
        raise SystemExit('Wrong channel. No secrets saved; repeat with the correct channel.')
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        output.write('YOUTUBE_CLIENT_ID=' + credentials.client_id + '\nYOUTUBE_CLIENT_SECRET=' + credentials.client_secret + '\nYOUTUBE_REFRESH_TOKEN=' + credentials.refresh_token + '\n')
    print('Saved private Secrets values to', str(args.output.resolve()))
    print('Copy these three values into GitHub Actions Secrets, then delete the local output. Never paste them in chat or commit them.')


if __name__ == '__main__':
    main()
