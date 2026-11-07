"""Refresh Python dependency metadata after deliberately updating requirements.lock.

Metadata is not a substitute for reviewing license files and exact model terms.
"""
import importlib.metadata as metadata
import json
from pathlib import Path


def main():
    path=Path('LICENSES.json')
    data=json.loads(path.read_text())
    dependencies=[]
    for line in Path('requirements.lock').read_text().splitlines():
        if '==' not in line:continue
        name,version=line.split('==')
        dist=metadata.distribution(name)
        if dist.version!=version:raise ValueError('Install the exact lock before regenerating metadata: '+name)
        meta=dist.metadata
        license=meta.get('License-Expression') or meta.get('License') or '; '.join(c.removeprefix('License :: ') for c in meta.get_all('Classifier',[]) if c.startswith('License :: '))
        dependencies.append({'name':name,'version':dist.version,'license':license or 'See upstream installed dist-info license files','source':meta.get('Home-page') or meta.get_all('Project-URL',[])})
    data['dependencies']=dependencies
    path.write_text(json.dumps(data,indent=2)+'\n')


if __name__=='__main__':main()
