#!/usr/bin/env python3
"""Run once on your own computer; local secret file is ignored by Git."""
import argparse
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from shorts.youtube import SCOPES


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--client',type=Path,required=True,help='Downloaded Desktop OAuth client JSON')
    parser.add_argument('--expected-channel',required=True)
    parser.add_argument('--output',type=Path,default=Path('oauth-secrets.txt'))
    args=parser.parse_args()
    if args.output.exists():raise SystemExit('Output exists; remove it securely before authorizing again')
    flow=InstalledAppFlow.from_client_secrets_file(str(args.client),SCOPES)
    credentials=flow.run_local_server(port=0,access_type='offline',prompt='consent',open_browser=True)
    youtube=build('youtube','v3',credentials=credentials,cache_discovery=False)
    channels=youtube.channels().list(part='snippet',mine=True).execute().get('items',[])
    if len(channels)!=1:raise SystemExit('Authorization must identify one YouTube channel')
    channel=channels[0]
    print('Authorized channel:',channel['snippet']['title'],'('+channel['id']+')')
    if channel['id']!=args.expected_channel:raise SystemExit('Wrong channel. No secrets saved; repeat with the correct channel.')
    if not credentials.refresh_token:raise SystemExit('No offline refresh token returned; revoke this client grant and retry')
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    fd=os.open(args.output,flags,0o600)
    with os.fdopen(fd,'w') as output:
        output.write('YOUTUBE_CLIENT_ID='+credentials.client_id+'\nYOUTUBE_CLIENT_SECRET='+credentials.client_secret+'\nYOUTUBE_REFRESH_TOKEN='+credentials.refresh_token+'\n')
    print('Saved private Secrets values to',str(args.output.resolve()))
    print('Copy these three values into GitHub Actions Secrets, then securely delete this file. Never paste them in chat or commit them.')


if __name__=='__main__':main()
