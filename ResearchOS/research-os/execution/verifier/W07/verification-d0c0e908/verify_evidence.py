"""Independent, offline W07 evidence verification. Never opens credential tables."""
import base64
import hashlib
import json
import pathlib
import sqlite3
import subprocess
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
CODE = '6773532d193f05d778ad23bfcc0fe39f5c562ae2'
CANDIDATE = '2c93abd7550fd69d474620af8713a572226c26f2'
BASE = ROOT / 'execution/receipts/W07/d0c0e908-9e50-4202-88e4-fcbc6a7b9990'
LIVE = ROOT / 'execution/receipts/W07/run-3c1540e6c5d44deeaed6fbe97f0d0f2b'
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def git(path): return subprocess.check_output(['git','show',CODE+':'+path],cwd=ROOT)
def jcs(value):
    def check(v):
        if isinstance(v,dict):
            assert all(k.isascii() for k in v)
            for x in v.values(): check(x)
        elif isinstance(v,list):
            for x in v: check(x)
        else: assert v is None or isinstance(v,(str,bool)) or type(v) is int and abs(v)<2**53
    check(value)
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

receipt=load(BASE/'receipt.json'); manifest=load(BASE/'artifacts.json'); global_e=load(BASE/'A05.json'); env=load(BASE/'environment-before.json')
assert len(manifest)==34 and len({a['path'] for a in manifest})==34
for a in manifest: assert sha((ROOT/a['path']).read_bytes())==a['sha256'],a['path']
assert sha((BASE/'artifacts.json').read_bytes())==receipt['artifact_manifest_hash'].removeprefix('sha256:')
body={k:v for k,v in receipt.items() if k!='receipt_hash'}
assert sha(jcs(body))=='d601f995bf832daeb36ef9ac4547d4e0abcbb18cc93c4ebab3182cff11400a39'
assert env['git_head']==CODE and env['tracked_status_porcelain']==''
assert datetime.fromisoformat(env['sampled_at']) < datetime.fromisoformat(receipt['started_at'])
for path,digest in env['source_sha256'].items():
    assert sha(git(path))==digest.removeprefix('sha256:'),path
    assert sha(subprocess.check_output(['git','show',CANDIDATE+':'+path],cwd=ROOT))==digest.removeprefix('sha256:'),path
assert not subprocess.check_output(['git','diff','15f1d9769da069d423ed4c52ace6ed0c722e1c2a',CANDIDATE,'--','spec/v2.0'],cwd=ROOT)
acceptance=load(ROOT/'spec/v2.0/contracts/acceptance.json')
package=load(ROOT/'spec/v2.0/PACKAGE_MANIFEST.json')
for item in package['files']:
    payload=git('spec/v2.0/'+item['path'])
    assert sha(payload)==item['sha256'] and len(payload)==item['size_bytes'],item['path']
assert len(acceptance['cases'])==42 and all(c['status']=='NOT_RUN' for c in acceptance['cases'])
case=next(c for c in acceptance['cases'] if c['id']=='A05')
assert global_e['global_evidence_id']=='GLOBAL_EVIDENCE_V1'
assert global_e['version_manifest']==env
assert global_e['acceptance_receipt']['reference']=='execution/verifier/W07/d0c0e908-9e50-4202-88e4-fcbc6a7b9990.json'
for group in ['lock_files','input_snapshots']:
    for path,digest in env[group].items(): assert sha(git(path))==digest
assert {a['assertion_id'] for a in global_e['assertion_results']}=={a['id'] for a in case['assertions']}
for actual,expected in zip(global_e['assertion_results'],case['assertions']):
    assert actual['expected']==expected['expected'] and actual['status']=='PASS'
    for a in actual['raw_evidence']: assert sha((ROOT/a['path']).read_bytes())==a['sha256']
invocations=[]
for a in manifest:
    if a['path'].startswith('execution/invocations/') and a['path'].endswith('/receipt.json'):
        i=load(ROOT/a['path']); assert i['code_revision']==CODE and i['status']=='PASS' and i['exit_code']==0 and i['assertion_ids']
        for stream in ['stdout','stderr']: assert sha((ROOT/i[stream]['path']).read_bytes())==i[stream]['sha256']
        assert i['registered_command_revision']==sha(git('execution/commands.json'))
        assert i['toolchain_revision']==sha(git('execution/toolchains/locked.json'))
        for item in i['input_versions']: assert sha(git(item['path']))==item['sha256']
        invocations.append({'id':i['invocation_id'],'command_key':i['command_key'],'assertions':len(i['assertion_ids']),'mode':i.get('reported_scope')})

sources={}
for name in ['GITHUB','PAPER','X']:
    report=load(LIVE/('report-'+name+'.json'))
    db=sqlite3.connect((LIVE/('live-'+name+'.sqlite')).as_uri()+'?mode=ro&immutable=1',uri=True)
    project=report['project_id']
    def obj(kind,id,revision=None):
        sql='SELECT body FROM '+('domain_versions' if revision else 'domain_objects')+' WHERE project=? AND kind=? AND id=?'
        args=[project,kind,id]
        if revision: sql+=' AND revision=?'; args.append(revision)
        row=db.execute(sql,args).fetchone(); assert row,(kind,id,revision)
        return json.loads(row[0])
    def ref(r):
        o=obj(r['entity_type'],r['id'],r['revision']); assert o.get('content_hash')==r['content_hash']; return o
    def content(a):
        row=db.execute('SELECT bytes,content_hash,sealed FROM uploaded_content WHERE project=? AND storage_key=?',(project,a['storage_key'])).fetchone()
        assert row and row[2]==1 and row[1]==a['content_hash']=='sha256:'+sha(row[0]) and len(row[0])==a['byte_size']
        assert a['validity']=='CURRENT' and a['sealed_at'] and a['measurement_mode']=='LIVE'
        return row[0]
    artifacts=[json.loads(x[0]) for x in db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact'",(project,))]
    for a in artifacts:
        content(a)
        for r in a['input_refs']+a['source_refs']: ref(r)
    items=[]
    for item in report['items']:
        e=obj('Evidence',item['evidence_id']); a=ref(e['snapshot_artifact_ref']); b=content(a)
        assert a['content_hash']==item['body_sha256'] and len(b)==item['body_bytes']
        assert e['canonical_url']==item['url'] and e['publisher']==item['author'] and e['upstream_revision']==item['upstream_revision']
        assert e['published_at']==item['published_at'] and e['retrieved_at']==item['retrieved_at']
        assert e['stance']=='CONTEXT' and e['verification_status']=='UNVERIFIED' and e['origin_evidence_id'] is None
        assert e['validity']=='CURRENT'
        items.append({'evidence_id':e['id'],'artifact_id':a['id'],'body_bytes':len(b),'sha256':sha(b),'url':e['canonical_url'],'upstream_revision':e['upstream_revision']})
    m=json.loads(content(obj('Artifact',report['manifest']['artifact_id'])))
    assert m['window_from']==report['window_from'] and m['window_to']==report['window_to'] and m['observed_from']==report['observed_from'] and m['observed_to']==report['observed_to']
    assert m['complete']==report['page_complete'] and m['request_urls']==report['request_urls'] and m['final_urls']==report['final_urls']
    raw=content(ref(m['raw_artifact_ref'])); assert 'sha256:'+sha(raw)==report['raw_page']['sha256']
    page=db.execute('SELECT complete,page_cursor_out,raw_artifact_id FROM source_pages WHERE project=? AND cursor_id=?',(project,report['cursor_id'])).fetchone()
    if name=='X': assert page is None and not m['complete']
    else: assert page and bool(page[0])==m['complete'] and page[1]==m['page_cursor_out'] and page[2]==m['raw_artifact_ref']['id']
    cursor=obj('SourceCursor',report['cursor_id'])
    if not report['page_complete']: assert cursor['covered_until'] is None
    else: assert cursor['covered_until']==report['covered_until']==report['window_to']
    detail={'items':items,'sealed_artifacts_checked':len(artifacts),'requested':[m['window_from'],m['window_to']],'observed':[m['observed_from'],m['observed_to']],'page_complete':m['complete'],'covered_until':cursor['covered_until'],'raw_page_sha256':sha(raw)}
    if name=='GITHUB':
        raw_obj=json.loads(raw)
        body_bytes=content(ref(obj('Evidence',report['items'][0]['evidence_id'])['snapshot_artifact_ref']))
        release=next(x for x in raw_obj if str(x['id'])==report['items'][0]['upstream_id'])
        assert release['body'].encode()==body_bytes and release['html_url']==report['items'][0]['url']
        detail['raw_json_shape']=type(raw_obj).__name__
    if name=='PAPER':
        b=content(ref(obj('Evidence',report['items'][0]['evidence_id'])['snapshot_artifact_ref']))
        assert b.startswith(b'%PDF-') and b.rstrip().endswith(b'%%EOF') and len(b)>10000000
        detail['full_pdf_bytes']=len(b)
    if name=='X':
        c=report['claim_check']; ca=ref(c['artifact_ref']); claim=json.loads(content(ca))
        assert ca['kind']=='MANIFEST' and ca['evidence_kind']=='GENERATED'
        xe=ref(claim['x_evidence_ref']); pe=ref(claim['primary_evidence_ref']); xb=content(ref(claim['x_snapshot_ref'])); pa=ref(claim['primary_snapshot_ref']); pb=content(pa)
        assert ca['source_refs']==ca['input_refs']==[claim['x_evidence_ref'],claim['primary_evidence_ref']]
        assert xe['snapshot_artifact_ref']==claim['x_snapshot_ref'] and pe['snapshot_artifact_ref']==claim['primary_snapshot_ref']
        assert claim['conclusion']=='SUPPORTED_NARROW_SCOPE' and claim['adoption_authority'] is False
        assert pe['upstream_revision']==claim['primary_commit']==c['primary_commit'] and pe['canonical_url']==claim['primary_url']
        assert b'#2 paperclipai/paperclip' in xb and b'Agent management and memory' in xb
        heading='# Paperclip is the app people use to manage AI agents for work.'
        assert heading.encode() in pb
        pr=json.loads(content(ref(pa['source_refs'][0])))
        assert pr['commits'][0]['sha']==claim['primary_commit']
        decoded=base64.b64decode(pr['readme']['content']); assert decoded==pb
        assert hashlib.sha1(b'blob '+str(len(pb)).encode()+b'\0'+pb).hexdigest()==pr['readme']['sha']
        assert xe['verification_status']=='UNVERIFIED' and xe['stance']=='CONTEXT'
        assert any('+2,251' in x and '93,960' in x for x in claim['unverified_claims'])
        assert db.execute("SELECT count(*) FROM domain_objects WHERE kind='Task'").fetchone()[0]==0
        detail['claim_check']={'manifest_id':ca['id'],'manifest_sha256':sha(content(ca)),'primary_commit':claim['primary_commit'],'readme_bytes':len(pb),'readme_heading':heading,'readme_sha256':sha(pb),'git_blob_sha1':pr['readme']['sha'],'x_status':xe['verification_status'],'x_stance':xe['stance'],'adoption_authority':False,'typed_refs_valid':True,'unverified_claims':claim['unverified_claims'],'x_section':xb.decode().split('#2 paperclipai/paperclip')[1].split('Model selection')[0]}
    sources[name]=detail
    db.close()
result={'status':'PASS','candidate_revision':CANDIDATE,'executed_code_revision':CODE,'artifact_hash_count':len(manifest),'source_hash_count':len(env['source_sha256']),'executor_receipt_jcs_sha256':sha(jcs(body)),'baseline_case_count':42,'baseline_NOT_RUN_count':42,'spec_unchanged_since_W03':True,'environment_precedes_execution':True,'invocations':invocations,'sources':sources,'limits':['No external service rerun; archived live evidence independently inspected.','Fault injections remain FIXTURE.','Only narrow agent-management categorization supported; stars/growth/effectiveness/adoption not verified.','No credential tables accessed.']}
print(json.dumps(result,ensure_ascii=False,indent=2))
