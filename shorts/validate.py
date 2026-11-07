import hashlib
import json
from pathlib import Path
import re
import subprocess
from .graphics import caption_layout, font, lines_for


def validate_content(script, records):
    title=script['title']; description=script['description']
    if not title.strip() or len(title)>65 or any(c in title for c in '<>\x00\n'):
        raise ValueError('Title must be accurate, single-line, and at most 65 characters')
    if len((description+' '.join(script['hashtags'])).encode())>4700 or not description.strip():
        raise ValueError('Description exceeds safe API limits or is empty')
    if not 3<=len(script['hashtags'])<=5 or '#Shorts' not in script['hashtags']:
        raise ValueError('Require 3–5 relevant hashtags including #Shorts')
    if any(not re.fullmatch(r'#[A-Za-z0-9]+',t) for t in script['hashtags']):
        raise ValueError('Invalid hashtag')
    if {'#Viral','#Trending'} & set(script['hashtags']):raise ValueError('Misleading hashtag')
    if sum(len(t)+3 for t in script['tags'])>500:raise ValueError('API tags too long')
    if script['selfDeclaredMadeForKids'] is not True:raise ValueError('Child-directed audience must be true')
    if len(script['scenes'])!=5:raise ValueError('Each reviewed episode must have five coherent scenes')
    for scene in script['scenes']:
        caption_layout(scene['narration'])
    # Title must fit above the scene card, without entering it.
    if len(lines_for(title,29,420))>3:raise ValueError('Title exceeds the safe heading area')
    for record in records.values():
        if record['job_id']==script['job_id']:continue
        if record.get('topic')==script['topic'] or record.get('fingerprint')==script['fingerprint']:
            raise ValueError('Topic or script was previously reserved or uploaded')
    if not Path('LICENSES.json').is_file() or not Path('voice.lock.json').is_file():
        raise ValueError('Required license manifests missing')
    licenses=json.loads(Path('LICENSES.json').read_text())
    if not licenses.get('assets') or not licenses.get('dependencies'):raise ValueError('Incomplete license manifest')
    font(25)
    return True


def validate_media(out, config, script, records):
    validate_content(script,records)
    video=out/'preview.mp4'
    probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,check=True)
    data=json.loads(probe.stdout)
    videos=[s for s in data['streams'] if s['codec_type']=='video']
    audios=[s for s in data['streams'] if s['codec_type']=='audio']
    if len(videos)!=1 or len(audios)!=1:raise ValueError('Require exactly one video and audio track')
    v=videos[0];a=audios[0]
    if (v['width'],v['height'],v['codec_name'],v.get('pix_fmt'))!=(config.width,config.height,'h264','yuv420p'):
        raise ValueError('Invalid video dimensions or codec')
    from fractions import Fraction
    if Fraction(v['avg_frame_rate'])!=config.fps:raise ValueError('Invalid frame rate')
    duration=float(data['format']['duration'])
    if not config.min_duration<=duration<=config.max_duration:raise ValueError('Duration outside configured bounds')
    if a['codec_name']!='aac':raise ValueError('Audio must use AAC')
    if abs(float(v.get('duration',duration))-float(a.get('duration',duration)))>.15:raise ValueError('Audio/video duration mismatch')
    scan=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','volumedetect,silencedetect=noise=-45dB:d=1.4','-vf','blackdetect=d=0.15:pix_th=0.1:pic_th=0.98','-f','null','-'],capture_output=True,text=True,check=True).stderr
    mean=re.search(r'mean_volume: ([\-\d.]+) dB',scan)
    peak=re.search(r'max_volume: ([\-\d.]+) dB',scan)
    if not mean or float(mean[1])< -35:raise ValueError('Narration missing or too quiet')
    if not peak or float(peak[1])>-.5:raise ValueError('Audio may clip; lower the normalization peak')
    if 'silence_start:' in scan:raise ValueError('Unexpected silent gap of at least 1.4 seconds')
    if 'black_start:' in scan:raise ValueError('Unexpected black video gap')
    layouts=json.loads((out/'caption-layout.json').read_text())
    for layout in layouts:
        x1,y1,x2,y2=layout['safe_box']
        if not (80<=x1<x2<=1000 and 150<=y1<y2<=1800 and layout['font_px']>=40 and len(layout['lines'])<=3):
            raise ValueError('Caption outside mobile safe margins')
    timeline=json.loads((out/'timeline.json').read_text())
    previous=0
    for cue in timeline:
        if abs(cue['start']-previous)>.002 or not cue['start']<cue['speech_end']<cue['end']:
            raise ValueError('Caption timeline has missing or overlapping intervals')
        previous=cue['end']
    if abs(previous-duration)>.15:raise ValueError('Caption timeline does not cover media')
    report={'passed':True,'duration_seconds':duration,'dimensions':[v['width'],v['height']],'fps':str(config.fps),'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'mean_volume_db':float(mean[1]),'peak_volume_db':float(peak[1]),'captions':'Measured scene-level synchronization; safe margins passed','sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'selfDeclaredMadeForKids':True}
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
