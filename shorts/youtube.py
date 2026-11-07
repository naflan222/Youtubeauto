"""Official OAuth client and conservative resumable upload recovery."""
import os
import time
import socket
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from .state import utcnow

SCOPES=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.readonly']


class RecoveryRequired(RuntimeError):
    pass


def client_from_env():
    names=['YOUTUBE_CLIENT_ID','YOUTUBE_CLIENT_SECRET','YOUTUBE_REFRESH_TOKEN']
    if any(not os.getenv(name) for name in names):
        raise ValueError('Missing YouTube Secrets; see docs/SETUP.md')
    credentials=Credentials(None,refresh_token=os.environ[names[2]],token_uri='https://oauth2.googleapis.com/token',client_id=os.environ[names[0]],client_secret=os.environ[names[1]],scopes=SCOPES)
    import google_auth_httplib2
    import httplib2
    http=google_auth_httplib2.AuthorizedHttp(credentials,http=httplib2.Http(timeout=60))
    return build('youtube','v3',http=http,cache_discovery=False)


def verify_channel(youtube, expected):
    if not expected or not expected.startswith('UC'):
        raise ValueError('Set a valid expected_channel_id before enabling uploads')
    data=youtube.channels().list(part='id,contentDetails',mine=True,maxResults=50).execute()
    items=data.get('items',[])
    if len(items)!=1 or items[0]['id']!=expected:
        raise ValueError('Authorized YouTube channel does not match expected_channel_id; reauthorize the correct channel')
    return items[0]['contentDetails']['relatedPlaylists']['uploads']


def category_id(youtube, config):
    data=youtube.videoCategories().list(part='snippet',regionCode=config.region,hl='en_US').execute()
    choices=[item['id'] for item in data.get('items',[]) if item['snippet']['title']==config.category_name and item['snippet'].get('assignable')]
    if len(choices)!=1:raise ValueError('Configured category is not available or assignable in this region')
    return choices[0]


def marker(job):
    return '[LittleWonderJob:'+job+']'


def reconcile(youtube, uploads, job):
    """Inspect up to 500 recent uploads; a negative result never clears an ambiguous intent."""
    page=None; matches=[]
    for _ in range(10):
        data=youtube.playlistItems().list(part='snippet',playlistId=uploads,maxResults=50,pageToken=page).execute()
        for item in data.get('items',[]):
            if marker(job) in item['snippet'].get('description',''):
                matches.append(item['snippet']['resourceId']['videoId'])
        page=data.get('nextPageToken')
        if not page:break
    matches=list(dict.fromkeys(matches))
    if len(matches)>1:raise RecoveryRequired('Multiple videos have this job marker; inspect YouTube Studio before any publication')
    return matches[0] if matches else None


def resumable_insert(youtube, body, video, sleeper=time.sleep):
    request=youtube.videos().insert(part='snippet,status',body=body,media_body=MediaFileUpload(str(video),mimetype='video/mp4',chunksize=8*1024*1024,resumable=True))
    response=None; retries=0
    while response is None:
        try:
            _,response=request.next_chunk(num_retries=0)
            retries=0
        except HttpError as error:
            if error.resp.status not in [429,500,502,503,504] or retries>=4:
                raise RecoveryRequired('Upload response failed; inspect/reconcile this job before retrying') from None
            retries+=1;sleeper(min(2**retries,16))
        except (OSError,socket.timeout):
            # Retrying a new insertion after a lost final response could duplicate the upload.
            raise RecoveryRequired('Upload response ambiguous; reconcile uploads before retrying') from None
    if not response.get('id'):raise RecoveryRequired('Upload returned no video ID; reconciliation required')
    return response['id']


def processing_and_publish(youtube, video_id, expected, sleeper=time.sleep, attempts=12):
    ready=False
    for _ in range(attempts):
        data=youtube.videos().list(part='snippet,status,processingDetails',id=video_id).execute()
        if len(data.get('items',[]))!=1:raise RecoveryRequired('Uploaded video is not visible to this authorization; retain its ID and inspect Studio')
        video=data['items'][0]
        if video['snippet']['channelId']!=expected:raise RecoveryRequired('Uploaded video channel mismatch')
        status=video['status']
        if status.get('selfDeclaredMadeForKids') is not True:raise RecoveryRequired('Made-for-kids audience setting was not confirmed')
        if status.get('uploadStatus') in ['failed','rejected','deleted']:
            raise RecoveryRequired('YouTube rejected or removed the video; inspect YouTube Studio')
        processing=video.get('processingDetails',{}).get('processingStatus')
        if processing in ['failed','terminated']:raise RecoveryRequired('YouTube processing failed; inspect Studio')
        if processing=='succeeded' or status.get('uploadStatus')=='processed':
            ready=True;break
        sleeper(15)
    if not ready:raise RecoveryRequired('Processing not complete yet; rerun to verify the existing video ID')
    if status.get('privacyStatus')!='public':
        update={'privacyStatus':'public','selfDeclaredMadeForKids':True}
        for field in ['license','embeddable','publicStatsViewable','containsSyntheticMedia']:
            if field in status:update[field]=status[field]
        youtube.videos().update(part='status',body={'id':video_id,'status':update}).execute()
    result=youtube.videos().list(part='status',id=video_id).execute()['items'][0]['status']
    if result.get('privacyStatus')!='public' or result.get('selfDeclaredMadeForKids') is not True:
        raise RecoveryRequired('Public publication was not confirmed; inspect account restrictions in Studio')
    return 'https://www.youtube.com/shorts/'+video_id


def publish(youtube,uploads,store,job,script,video,config,category):
    record=store.records.get(job)
    found=reconcile(youtube,uploads,job)
    if record and record.get('video_id') and found and record['video_id']!=found:
        raise RecoveryRequired('State and channel video IDs disagree; inspect before continuing')
    if not record:
        record={'job_id':job,'topic':script['topic'],'theme':script['theme'],'fingerprint':script['fingerprint'],'status':'selected','video_id':None,'publication_url':None,'completion_time':None}
    if found:
        record.update(video_id=found,status='uploaded')
        store.save(record)
    if record.get('video_id'):
        url=processing_and_publish(youtube,record['video_id'],config.expected_channel_id)
        record.update(status='published',publication_url=url,completion_time=utcnow())
        store.save(record)
        return record
    if record['status'] in ['upload-intent','ambiguous','uploaded','published']:
        raise RecoveryRequired('Unresolved upload intent: no matching video found. Inspect Studio, wait for API visibility, then use the documented recovery procedure. No duplicate upload attempted.')
    record.update(status='upload-intent',started_at=utcnow())
    store.save(record)  # A failed durable write MUST prevent insertion.
    body={'snippet':{'title':script['title'],'description':script['description']+'\n\n'+' '.join(script['hashtags'])+'\n\n'+marker(job),'tags':script['tags'],'categoryId':category,'defaultLanguage':'en','defaultAudioLanguage':'en'},'status':{'privacyStatus':'private','selfDeclaredMadeForKids':True,'containsSyntheticMedia':config.contains_synthetic_media}}
    try:
        video_id=resumable_insert(youtube,body,video)
    except Exception:
        record['status']='ambiguous'
        store.save(record)
        raise
    record.update(video_id=video_id,status='uploaded')
    store.save(record)
    url=processing_and_publish(youtube,video_id,config.expected_channel_id)
    record.update(status='published',publication_url=url,completion_time=utcnow())
    store.save(record)
    return record
