"""Small durable journal; no videos, OAuth tokens, or API discovery data in Git."""
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.request


class StateError(RuntimeError):
    pass


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class LocalState:
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'records.json'
        self.records=json.loads(self.path.read_text()) if self.path.exists() else {}

    def save(self, record):
        self.records[record['job_id']]=record
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.records,indent=2)+'\n')
        temporary.replace(self.path)


class GitHubState:
    branch='shorts-state'
    path='daily-records.json'

    def __init__(self):
        self.repo=os.environ['GITHUB_REPOSITORY']
        self.token=os.environ['GH_STATE_TOKEN']
        self.sha=None
        # Read the ref separately: a missing state file on an existing branch is corruption.
        try:
            self.api('GET',f'git/ref/heads/{self.branch}')
        except urllib.error.HTTPError as error:
            if error.code!=404:raise StateError('Cannot read state branch') from None
            head=self.api('GET','git/ref/heads/'+os.environ.get('GITHUB_DEFAULT_BRANCH','main'))
            self.api('POST','git/refs',{'ref':'refs/heads/'+self.branch,'sha':head['object']['sha']})
            self.records={}
            self._write()
        else:
            try:
                data=self.api('GET',f'contents/{self.path}?ref={self.branch}')
                self.sha=data['sha']
                self.records=json.loads(base64.b64decode(data['content']))
            except (urllib.error.HTTPError,ValueError,KeyError):
                raise StateError('State missing or invalid; restore shorts-state before uploading') from None

    def api(self, method, path, data=None):
        body=json.dumps(data).encode() if data is not None else None
        request=urllib.request.Request(f'https://api.github.com/repos/{self.repo}/{path}',body,method=method,headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=30) as response:
            return json.load(response)

    def _write(self):
        payload={'message':'Record meaningful Shorts pipeline state','branch':self.branch,'content':base64.b64encode((json.dumps(self.records,indent=2)+'\n').encode()).decode()}
        if self.sha:payload['sha']=self.sha
        try:
            result=self.api('PUT','contents/'+self.path,payload)
        except urllib.error.HTTPError:
            raise StateError('State save failed or conflicted; no new upload may start') from None
        self.sha=result['content']['sha']

    def save(self,record):
        self.records[record['job_id']]=record
        self._write()
