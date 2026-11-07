from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch
import json
import pytest
import yaml
from shorts.config import Config, job_id
from shorts.content import TOPICS, save_script
from shorts.graphics import frame, caption_layout
from shorts.selection import select_topic, discover
from shorts.state import LocalState, StateError
from shorts.validate import validate_content, validate_media
from shorts.youtube import publish, RecoveryRequired, verify_channel, marker, reconcile, resumable_insert, processing_and_publish


def test_colombo_day_boundary_and_naive_rejection():
    config=Config()
    assert job_id(config,datetime(2026,11,7,18,29,tzinfo=timezone.utc))=='wonder-2026-11-07'
    assert job_id(config,datetime(2026,11,7,18,30,tzinfo=timezone.utc))=='wonder-2026-11-08'
    with pytest.raises(ValueError):job_id(config,datetime(2026,11,7))


def test_schedule_and_preview_permissions():
    workflow=yaml.safe_load(Path('.github/workflows/daily.yml').read_text())
    # PyYAML's YAML 1.1 parser treats GitHub's "on" key as True.
    triggers=workflow.get('on',workflow.get(True))
    assert triggers['schedule'][0]['cron']=='45 12 * * *'
    from zoneinfo import ZoneInfo
    assert datetime(2026,11,7,12,45,tzinfo=timezone.utc).astimezone(ZoneInfo('Asia/Colombo')).strftime('%H:%M')=='18:15'
    preview=yaml.safe_load(Path('.github/workflows/preview.yml').read_text())
    assert preview['permissions']=={'contents':'read'}
    assert 'YOUTUBE_REFRESH_TOKEN' not in Path('.github/workflows/preview.yml').read_text()


def test_upload_requires_both_opt_ins(monkeypatch):
    monkeypatch.setenv('UPLOAD_ENABLED','true')
    assert not Config().live_enabled()
    assert replace(Config(),upload_enabled=True).live_enabled()
    monkeypatch.delenv('UPLOAD_ENABLED')
    assert not replace(Config(),upload_enabled=True).live_enabled()


def test_selection_is_deterministic_rotates_and_exhausts():
    records={};seen=set();last=None
    for day in range(len(TOPICS)):
        job=f'wonder-{day:04}'
        a,_=select_topic(job,records);b,_=select_topic(job,records)
        assert a==b and a.key not in seen
        if len({t.theme for t in TOPICS if t.key not in seen})>1:assert a.theme!=last
        seen.add(a.key);last=a.theme
        records[job]={'job_id':job,'topic':a.key,'theme':a.theme,'fingerprint':a.fingerprint}
    with pytest.raises(ValueError,match='exhausted'):select_topic('next',records)


def test_script_fingerprint_blocks_renamed_topic():
    used=TOPICS[0]
    records={'old':{'job_id':'old','topic':'renamed','fingerprint':used.fingerprint}}
    for day in range(20):
        chosen,_=select_topic(str(day),records)
        assert chosen.fingerprint!=used.fingerprint


def test_discovery_failure_and_unsafe_filter():
    youtube=Mock()
    youtube.videos.return_value.list.return_value.execute.return_value={'items':[{'id':'unsafe','snippet':{'title':'Dangerous butterfly challenge'}},{'id':'safe','snippet':{'title':'Beautiful butterfly garden'}}]}
    signals,_=discover(youtube,'US')
    assert [s['source_video_id'] for s in signals]==['safe']
    assert signals[0]['retrieved_at'] and signals[0]['source'].startswith('https://')
    youtube.videos.return_value.list.return_value.execute.side_effect=OSError('offline')
    assert discover(youtube,'US')[0]==[]
    assert discover(None,'US')[0]==[]


@pytest.mark.parametrize('topic',TOPICS,ids=lambda t:t.key)
def test_all_authored_scripts_have_valid_mobile_layouts_and_visuals(topic,tmp_path):
    script=save_script(topic,Config(),{'mode':'evergreen-fallback'},'test',tmp_path)
    assert validate_content(script,{})
    timeline=[{'start':i*6,'speech_end':i*6+5.8,'end':(i+1)*6,'text':b,'visual':v,'scene':i} for i,(b,v) in enumerate(zip(topic.beats,topic.visuals))]
    for i,cue in enumerate(timeline):
        lines,size=caption_layout(cue['text'])
        assert len(lines)<=3 and size>=20
        image=frame(script,timeline,i*6+3)
        assert image.size==(540,960)
    assert topic.source or topic.theme not in ['facts','nature']


def fixture_script(tmp_path):
    return save_script(TOPICS[0],Config(),{'mode':'evergreen-fallback'},'wonder-2026-11-07',tmp_path)


def record(script,status='upload-intent',video_id=None):
    return {'job_id':script['job_id'],'topic':script['topic'],'fingerprint':script['fingerprint'],'status':status,'video_id':video_id}


def test_crash_after_upload_before_state_save_reconciles_without_insert(tmp_path):
    script=fixture_script(tmp_path);store=LocalState(tmp_path/'state');store.save(record(script))
    config=replace(Config(),expected_channel_id='UCexpected')
    with patch('shorts.youtube.reconcile',return_value='existing'),patch('shorts.youtube.processing_and_publish',return_value='https://example/video'),patch('shorts.youtube.resumable_insert') as insert:
        result=publish(Mock(),'uploads',store,script['job_id'],None,None,config,'27')
    insert.assert_not_called()
    assert result['video_id']=='existing' and result['status']=='published'


def test_ambiguous_missing_upload_blocks_duplicate(tmp_path):
    script=fixture_script(tmp_path);store=LocalState(tmp_path/'state');store.save(record(script,'ambiguous'))
    with patch('shorts.youtube.reconcile',return_value=None),patch('shorts.youtube.resumable_insert') as insert:
        with pytest.raises(RecoveryRequired,match='Unresolved'):publish(Mock(),'uploads',store,script['job_id'],None,None,Config(),'27')
    insert.assert_not_called()


def test_failed_durable_intent_write_prevents_upload(tmp_path):
    script=fixture_script(tmp_path);store=Mock(records={});store.save.side_effect=StateError('conflict')
    with patch('shorts.youtube.reconcile',return_value=None),patch('shorts.youtube.resumable_insert') as insert:
        with pytest.raises(StateError):publish(Mock(),'uploads',store,script['job_id'],script,tmp_path/'video.mp4',Config(),'27')
    insert.assert_not_called()


def test_known_video_id_resumes_processing_not_upload(tmp_path):
    script=fixture_script(tmp_path);store=LocalState(tmp_path/'state');store.save(record(script,'uploaded','known'))
    with patch('shorts.youtube.reconcile',return_value=None),patch('shorts.youtube.processing_and_publish',return_value='url'),patch('shorts.youtube.resumable_insert') as insert:
        result=publish(Mock(),'uploads',store,script['job_id'],None,None,Config(),'27')
    assert result['publication_url']=='url';insert.assert_not_called()


def test_upload_body_is_private_child_directed_then_published(tmp_path):
    script=fixture_script(tmp_path);store=LocalState(tmp_path/'state')
    with patch('shorts.youtube.reconcile',return_value=None),patch('shorts.youtube.resumable_insert',return_value='new-id') as insert,patch('shorts.youtube.processing_and_publish',return_value='url'):
        result=publish(Mock(),'uploads',store,script['job_id'],script,tmp_path/'video',Config(),'27')
    body=insert.call_args.args[1]
    assert body['status']=={'privacyStatus':'private','selfDeclaredMadeForKids':True,'containsSyntheticMedia':False}
    assert marker(script['job_id']) in body['snippet']['description']
    assert result['status']=='published'


def test_lost_response_leaves_ambiguous_record(tmp_path):
    script=fixture_script(tmp_path);store=LocalState(tmp_path/'state')
    with patch('shorts.youtube.reconcile',return_value=None),patch('shorts.youtube.resumable_insert',side_effect=RecoveryRequired('ambiguous')):
        with pytest.raises(RecoveryRequired):publish(Mock(),'uploads',store,script['job_id'],script,tmp_path/'video',Config(),'27')
    reloaded=LocalState(tmp_path/'state')
    assert reloaded.records[script['job_id']]['status']=='ambiguous'


def test_wrong_channel_and_multiple_matches_fail_closed():
    youtube=Mock()
    youtube.channels.return_value.list.return_value.execute.return_value={'items':[{'id':'UCwrong'}]}
    with pytest.raises(ValueError,match='does not match'):verify_channel(youtube,'UCexpected')
    youtube.playlistItems.return_value.list.return_value.execute.return_value={'items':[{'snippet':{'description':marker('job'),'resourceId':{'videoId':v}}} for v in ['a','b']]}
    with pytest.raises(RecoveryRequired,match='Multiple'):reconcile(youtube,'uploads','job')


def test_resumable_retry_is_bounded(tmp_path):
    from googleapiclient.errors import HttpError
    from httplib2 import Response
    video=tmp_path/'clip.mp4';video.write_bytes(b'test')
    youtube=Mock();request=youtube.videos.return_value.insert.return_value
    request.next_chunk.side_effect=HttpError(Response({'status':'503'}),b'unavailable')
    sleeps=[]
    with pytest.raises(RecoveryRequired):resumable_insert(youtube,{},video,sleeper=sleeps.append)
    assert request.next_chunk.call_count==5
    assert sleeps==[2,4,8,16]


def test_processing_timeout_preserves_private_video():
    youtube=Mock()
    youtube.videos.return_value.list.return_value.execute.return_value={'items':[{'snippet':{'channelId':'UCexpected'},'status':{'selfDeclaredMadeForKids':True,'privacyStatus':'private','uploadStatus':'uploaded'},'processingDetails':{'processingStatus':'processing'}}]}
    with pytest.raises(RecoveryRequired,match='not complete'):processing_and_publish(youtube,'id','UCexpected',sleeper=lambda _:None,attempts=2)
    youtube.videos.return_value.update.assert_not_called()


def test_content_duplicate_and_audience_validation(tmp_path):
    script=fixture_script(tmp_path)
    with pytest.raises(ValueError,match='previously'):validate_content(script,{'old':{'job_id':'old','fingerprint':script['fingerprint']}})
    script['selfDeclaredMadeForKids']=False
    with pytest.raises(ValueError,match='audience'):validate_content(script,{})


def test_real_render_validation_if_present():
    out=Path('output')
    if not (out/'preview.mp4').exists():pytest.skip('Full media smoke test runs in the preview CLI')
    script=json.loads((out/'script.json').read_text())
    assert validate_media(out,Config(),script,{})['passed']


def test_publication_preserves_synthetic_disclosure():
    youtube=Mock()
    initial={'snippet':{'channelId':'UCexpected'},'status':{'selfDeclaredMadeForKids':True,'containsSyntheticMedia':True,'privacyStatus':'private','uploadStatus':'processed','license':'youtube','embeddable':True},'processingDetails':{'processingStatus':'succeeded'}}
    final={'status':{'selfDeclaredMadeForKids':True,'containsSyntheticMedia':True,'privacyStatus':'public'}}
    youtube.videos.return_value.list.return_value.execute.side_effect=[{'items':[initial]},{'items':[final]}]
    assert processing_and_publish(youtube,'id','UCexpected',sleeper=lambda _:None).endswith('/id')
    updated=youtube.videos.return_value.update.call_args.kwargs['body']['status']
    assert updated['containsSyntheticMedia'] is True and updated['license']=='youtube'
