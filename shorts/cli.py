import argparse
import json
import os
from pathlib import Path
import sys
from googleapiclient.errors import HttpError
from .config import Config, job_id
from .content import save_script, TOPICS
from .selection import discover, select_topic
from .state import LocalState, GitHubState, StateError
from .youtube import client_from_env, verify_channel, category_id, publish, RecoveryRequired, describe_api_error
from .narration import narrate
from .render import render
from .validate import validate_content, validate_media


def summary(text):
    print(text,flush=True)
    target=os.getenv('GITHUB_STEP_SUMMARY')
    if target:
        with open(target,'a') as output:output.write(text+'\n\n')


def main():
    parser=argparse.ArgumentParser(description='Render original kids Shorts; preview never uploads')
    parser.add_argument('mode',choices=['preview','publish','recover'])
    parser.add_argument('--config',default='config.toml')
    parser.add_argument('--out',type=Path,default=Path('output'))
    parser.add_argument('--state-dir',type=Path,default=Path('state-local'))
    parser.add_argument('--recover-job',help='Existing job ID to reconcile; never creates a new upload')
    args=parser.parse_args()
    stage='configuration'
    try:
        config=Config.load(args.config)
        live=args.mode in ['publish','recover']
        if live and not config.live_enabled():
            raise ValueError('Uploads disabled. Set upload_enabled=true AND repository variable UPLOAD_ENABLED=true after a successful preview.')
        if live and os.getenv('GITHUB_ACTIONS')!='true':
            raise ValueError('Live publishing must use the serialized GitHub workflow and durable GitHub state')
        job=job_id(config)
        youtube=None;uploads=None;category=None
        if live:
            stage='credentials and expected channel'; summary('Stage: '+stage)
            youtube=client_from_env()
            uploads=verify_channel(youtube,config.expected_channel_id)
            category=category_id(youtube,config)
            stage='durable state'; summary('Stage: '+stage)
            store=GitHubState()
        else:
            store=LocalState(args.state_dir)
        if args.mode=='recover':
            if not args.recover_job or args.recover_job not in store.records:
                raise ValueError('Recovery requires an existing --recover-job')
            job=args.recover_job
            record=store.records[job]
            if record['status'] not in ['upload-intent','ambiguous','uploaded','published']:
                raise ValueError('This job has no upload to recover')
            stage='reconcile and recover';summary('Stage: '+stage)
            result=publish(youtube,uploads,store,job,None,None,config,category)
            summary('Recovered publication: '+result['publication_url']);return
        # Resolve unfinished earlier days before allowing any new insertion.
        pending=[r for r in store.records.values() if r['job_id']!=job and r.get('status') in ['upload-intent','ambiguous','uploaded']]
        if live and pending:
            raise RecoveryRequired('An earlier job is unfinished: '+pending[0]['job_id']+'. Run manual recover mode first.')
        existing=store.records.get(job)
        if live and existing and existing.get('status') in ['upload-intent','ambiguous','uploaded','published']:
            stage='reconcile existing daily upload';summary('Stage: '+stage)
            result=publish(youtube,uploads,store,job,None,None,config,category)
            summary('Existing daily publication: '+result['publication_url']);return
        args.out.mkdir(parents=True,exist_ok=True)
        # Prevent a stale successful report from being uploaded after a failed rerun.
        for name in ['validation.json','result.json']:
            (args.out/name).unlink(missing_ok=True)
        stage='topic selection';summary('Stage: '+stage)
        signals,fallback=discover(youtube,config.region)
        if existing and existing.get('status')=='selected':
            topic=next((t for t in TOPICS if t.key==existing.get('topic') and t.fingerprint==existing.get('fingerprint')),None)
            if topic is None:raise ValueError('Reserved story changed; inspect state before retrying')
            selection={'mode':'evergreen-fallback','reason':'Resuming the same reserved original story'}
        else:
            topic,selection=select_topic(job,store.records,signals,fallback)
        script=save_script(topic,config,selection,job,args.out)
        validate_content(script,store.records)
        stage='local narration and captions';summary('Stage: '+stage)
        timeline=narrate(script,config,args.out)
        stage='procedural animation and encoding';summary('Stage: '+stage)
        render(script,timeline,config,args.out)
        stage='content and media validation';summary('Stage: '+stage)
        report=validate_media(args.out,config,script,store.records)
        summary(f"Preview validated: {script['title']} — {report['duration_seconds']:.1f}s, 1080×1920, 30 fps. Selection: {selection['mode']}.")
        if live:
            stage='reconcile, upload, processing, publication';summary('Stage: '+stage)
            result=publish(youtube,uploads,store,job,script,args.out/'preview.mp4',config,category)
            (args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            summary('Published: '+result['publication_url'])
        else:
            summary('Preview only: no YouTube credentials used, no upload attempted, no live state changed.')
    except Exception as error:
        # Never print Google/HTTP exception bodies: they can contain credentials or request data.
        if isinstance(error,HttpError):
            safe=describe_api_error(error)
        else:
            safe=str(error) if isinstance(error,(ValueError,RecoveryRequired,StateError)) else type(error).__name__+' (details suppressed to protect secrets)'
        summary('FAILED stage: '+stage+'. '+safe)
        sys.exit(1)


if __name__=='__main__':main()
