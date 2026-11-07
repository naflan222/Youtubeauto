from datetime import datetime, timezone
import hashlib
import re
from .content import TOPICS

# Only map a small vocabulary to independently authored, reviewed episodes.
SIGNALS={'butterfly':'butterfly','rainbow':'rainbow','triangle':'triangles','counting':'count-three','turtle':'turtle-shell','moon':'moon-light','seed':'seed-journey'}
UNSAFE=re.compile(r'\b(war|death|kill|sexy|sex|adult|prank|challenge|horror|scary|gun|violence|disaster|politic|election|crime|murder|drug|casino|gambling)\w*\b',re.I)


def discover(youtube, region):
    if youtube is None:
        return [], 'No authenticated discovery client; evergreen fallback'
    try:
        # One list call, no search, no video downloads and no popularity metrics requested.
        data=youtube.videos().list(part='snippet',chart='mostPopular',regionCode=region,maxResults=10,fields='items(id,snippet(title))').execute()
    except Exception:
        return [], 'Official discovery unavailable; evergreen fallback'
    signals=[]
    for item in data.get('items',[]):
        title=item['snippet']['title'].lower()
        if UNSAFE.search(title):continue
        for term,key in SIGNALS.items():
            if re.search(r'\b'+re.escape(term)+r's?\b',title):
                signals.append({'topic':key,'source':'https://www.googleapis.com/youtube/v3/videos?chart=mostPopular&regionCode='+region,'retrieved_at':datetime.now(timezone.utc).isoformat(),'source_video_id':item['id'],'meaning':'Observed topic inspiration only; not evidence of suitability or search volume'})
    return signals, 'No approved inspiration in discovery results; evergreen fallback'


def select_topic(job, records, signals=(), fallback='Evergreen fallback'):
    used_topics={r.get('topic') for r in records.values()}
    used_scripts={r.get('fingerprint') for r in records.values()}
    available=[t for t in TOPICS if t.key not in used_topics and t.fingerprint not in used_scripts]
    if not available:
        raise ValueError('Reviewed topic library exhausted. Add reviewed original episodes; publication skipped.')
    previous=[r for r in records.values() if r.get('theme')]
    previous.sort(key=lambda r:r['job_id'])
    last_theme=previous[-1]['theme'] if previous else None
    rotated=[t for t in available if t.theme!=last_theme] or available
    for signal in signals:
        match=next((t for t in rotated if t.key==signal['topic']),None)
        if match:
            return match, {'mode':'observed-topic-inspiration','signal':signal}
    # Deterministic day seed, but choose a theme first so all eight themes get represented.
    themes=sorted({t.theme for t in rotated})
    seed=int(hashlib.sha256(job.encode()).hexdigest(),16)
    theme=themes[seed%len(themes)]
    candidates=sorted((t for t in rotated if t.theme==theme),key=lambda t:t.key)
    return candidates[(seed//len(themes))%len(candidates)], {'mode':'evergreen-fallback','reason':fallback}
