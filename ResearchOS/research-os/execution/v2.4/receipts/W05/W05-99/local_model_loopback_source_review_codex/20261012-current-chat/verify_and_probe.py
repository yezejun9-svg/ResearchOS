"""Pin frozen candidate and probe only the missing redirect/proxy boundary."""
import collections
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
SRC=REPO/'execution/v2.4/receipts/W05/W05-99/local_model_resource_qualification_codex/20261012-current-chat/source-candidate'
WT=REPO/'.local/worktrees/w05-loopback-local-model-20261012'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(p):
    raw=p.read_bytes();return {'path':p.relative_to(REPO).as_posix(),'sha256':sha(raw),'bytes':len(raw)}
def git(*args):return subprocess.check_output(['git','-C',str(WT),*args])
manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
assert ref(SRC/'manifest.json')['sha256']=='d48a3181350ed1bf54960c99a685889feba1de1e6b2d61a4ebdd74e77424cfdd'
commit=manifest['candidate_commit'];base=manifest['base_commit']
assert git('rev-parse','HEAD').decode().strip()==commit=='2825d2aad972c435268f29349a1e649605be347e'
assert git('rev-parse','HEAD^').decode().strip()==base
assert not git('status','--porcelain')
changed=set(git('diff','--name-only',base,commit).decode().splitlines())
claims=manifest['source_files']+manifest['test_files'];assert len(changed)==9 and changed=={r['path'] for r in claims}
for r in claims:
    raw=(WT/r['path']).read_bytes();assert sha(raw)==r['sha256'] and git('show',commit+':'+r['path'])==raw
assert sha((SRC/'candidate.patch').read_bytes())==manifest['patch']['sha256']
log=SRC/manifest['tests']['raw_log'];assert sha(log.read_bytes())==manifest['tests']['raw_sha256']
events=[json.loads(line) for line in log.read_bytes().splitlines()]
runs={};passes=[]
for ev in events:
    assert ev['Action'] not in ('fail','skip','build-fail')
    name=ev.get('Test')
    if name and ev['Action']=='run':assert name not in runs;runs[name]=ev
    if name and ev['Action']=='pass':assert name in runs and name not in passes;passes.append(name)
assert set(n for n in passes if '/' not in n)==set(manifest['tests']['top_level_pass_tests']) and len([n for n in passes if '/' not in n])==10
assert any(e['Action']=='pass' and not e.get('Test') for e in events)
assert manifest['tests']['exit_code']==0
assert not any(p.startswith(('spec/','internal/api/contracts/')) for p in changed)

# Build an independent temporary copy from the exact committed bytes. Test additions
# are reviewer-only and retained separately; no author tree, Main, or Canon writes.
archive=git('archive','--format=zip',commit,'go.mod','go.sum','internal','adapters','migrations','spec/v2.0','evaluation','ops')
fixture=OUT/'isolated-source';assert not fixture.exists()
fixture.mkdir()
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    for item in z.infolist():
        target=(fixture/item.filename).resolve();assert target==fixture.resolve() or fixture.resolve() in target.parents
    z.extractall(fixture)
extra=OUT/'independent_loopback_windows_test.go.txt'
(fixture/'internal/domain/independent_loopback_windows_test.go').write_bytes(extra.read_bytes())
go=REPO/'.local/tools/go1.27.1/go/bin/go.exe'
node=Path('C:/Program Files/nodejs/node.exe')
bundle=WT/'.local/w1401-mu-worker/mu-worker.mjs'
argv=[str(go),'test','-json','./internal/domain','-run','^TestIndependent(LoopbackRedirectProxyFence|LiveLoopbackAndRemoteGate)$','-count=1']
env=os.environ.copy();env.update(GOWORK='off',RESEARCHOS_NODE=str(node),RESEARCHOS_MU_BUNDLE=str(bundle))
started=datetime.now(timezone.utc).isoformat()
completed=subprocess.run(argv,cwd=fixture,env=env,capture_output=True)
ended=datetime.now(timezone.utc).isoformat()
attempt=OUT/'attempt-002';assert not attempt.exists();attempt.mkdir()
(attempt/'independent-go-test.jsonl').write_bytes(completed.stdout)
(attempt/'independent-go-test.stderr.txt').write_bytes(completed.stderr)
inv={'argv':argv,'cwd':str(fixture),'started_at':started,'ended_at':ended,'exit_code':completed.returncode,
 'source_commit':commit,'archive_sha256':sha(archive),'extra_test_ref':ref(extra),
 'env_overrides':{k:env[k] for k in ('GOWORK','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE')},
 'go_sha256':sha(go.read_bytes()),'node_sha256':sha(node.read_bytes()),'bundle_sha256':sha(bundle.read_bytes()),
 'stdout_ref':ref(attempt/'independent-go-test.jsonl'),'stderr_ref':ref(attempt/'independent-go-test.stderr.txt'),
 'prior_failed_setup_ref':ref(OUT/'independent-invocation.json'),
 'reason':'Add omitted committed ops/supervisor dependency; no test had run in attempt001.'}
(attempt/'independent-invocation.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Verified absolute cleanup boundary, exactly this newly created disposable copy.
assert fixture.resolve().parent==OUT.resolve() and fixture.name=='isolated-source'
shutil.rmtree(fixture)
assert not git('status','--porcelain')
for r in claims:assert sha((WT/r['path']).read_bytes())==r['sha256']
probe=[json.loads(line) for line in completed.stdout.splitlines() if line]
probe_pass=[e['Test'] for e in probe if e['Action']=='pass' and e.get('Test')]
assert completed.returncode==0 and len(probe_pass)==2 and not any(e['Action'] in ('fail','skip','build-fail') for e in probe)
summary={'schema':'researchos.w05.loopback-independent-source-audit.v1','reviewer_id':'/root/w09_header_gate_review',
 'author_id':'/root/w05_main24','candidate_commit':commit,'base_commit':base,
 'manifest_ref':ref(SRC/'manifest.json'),'nine_commit_files_verified':claims,
 'original_top_level_passes':manifest['tests']['top_level_pass_tests'],'original_raw_ref':ref(log),
 'supplemental_passes':probe_pass,'supplemental_invocation_ref':ref(attempt/'independent-invocation.json'),
 'preserved_setup_failure_ref':ref(OUT/'independent-invocation.json'),
 'main_or_canon_modified':False,'author_tree_modified':False,'paid_or_real_model_calls':0,
 'mode':'SOURCE_AND_LOCAL_FIXTURE_ONLY','source_candidate_frozen_after_review':True}
(OUT/'evidence-audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'audit_ref':ref(OUT/'evidence-audit.json'),'original_tests':10,'independent_tests':probe_pass,'exit_code':completed.returncode},ensure_ascii=False,indent=2))
