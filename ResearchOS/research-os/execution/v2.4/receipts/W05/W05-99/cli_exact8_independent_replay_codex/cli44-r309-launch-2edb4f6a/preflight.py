from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
N=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/closure-and-finite-continuation-r309'
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(p.read_bytes())
def save(n,x):
    with (HERE/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
scope=N/'cli_continuation_scope.v2.json'
handoff=N/'handoff-r309-running.json'
if ref(scope)['sha256']!='29ffca39b944aeebaac5055905cb286516c673b0d807ba210c12dca2a016b083':raise RuntimeError('scope SHA')
if ref(handoff)['sha256']!='6b36e2f605359991d7e1f3ffb91cb06a136f52531746b353c618117f4ac52d69':raise RuntimeError('handoff SHA')
h=read(handoff);canon=[]
for row in h['canonical_refs']:
    p=ROOT/row['path'];a=ref(p)
    if a['sha256']!=row['sha256'] or a['bytes']!=row['bytes']:raise RuntimeError('canonical differs')
    if p.name in ('checkpoint.json','path_ownership.json'):
        if p.read_bytes()!=(N/(p.stem+'.desired.json')).read_bytes():raise RuntimeError('desired mismatch')
    else:
        if p.read_bytes()!=(N/(p.stem+'.original.json')).read_bytes():raise RuntimeError('unchanged mismatch')
    with (HERE/('before-'+p.name)).open('xb') as f:f.write(p.read_bytes())
    canon.append(a)
cp=read(ROOT/'execution/v2.4/checkpoint.json');ow=read(ROOT/'execution/v2.4/path_ownership.json')
if [cp['revision'],ow['revision'],len(cp['failure_counters'])]!=[309,137,379]:raise RuntimeError('state tuple')
pin=cp['work_in_progress']['cli44_continuation_scope_ref']
if (ROOT/pin['path']).resolve()!=scope.resolve() or pin['sha256']!=ref(scope)['sha256']:raise RuntimeError('CP scope binding')
s=read(scope)
if Path(s['cli44_continuation']['output']).exists():raise RuntimeError('OUTPUT_ALREADY_EXISTS')
for key in ('runner_ref','prepared_handoff_ref','prepared_spec_ref'):
    r=s[key];a=ref(ROOT/r['path'])
    if a['sha256']!=r['sha256'] or a['bytes']!=r['bytes']:raise RuntimeError('prepared ref '+key)
lock=read(ROOT/'execution/toolchains/locked.json')['tools']
for key in ('python','git'):
    if ref(Path(lock[key]['path']))['sha256']!=lock[key]['sha256']:raise RuntimeError('tool pin')
if Path(sys.executable).resolve()!=Path(lock['python']['path']).resolve():raise RuntimeError('Python path')
env={k:os.environ[k] for k in ('SystemRoot','WINDIR','ComSpec','PATH','PATHEXT') if k in os.environ}
env.update(GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_OPTIONAL_LOCKS='0')
argv=[lock['git']['path'],'-C',str(ROOT),'rev-parse','HEAD']
with (HERE/'head.stdout.raw').open('xb') as out,(HERE/'head.stderr.raw').open('xb') as err:
    child=subprocess.run(argv,env=env,stdout=out,stderr=err)
save('head.invocation.json',{'argv':argv,'actual_exit':child.returncode,'stdout':ref(HERE/'head.stdout.raw'),'stderr':ref(HERE/'head.stderr.raw')})
head=(HERE/'head.stdout.raw').read_text(encoding='utf-8').strip()
if child.returncode!=0 or head!=h['Main_head'] or head!=cp['head']:raise RuntimeError('HEAD mismatch')
save('preflight.json',{'decision':'ACTUAL_ROOT309_INPUTS_MATCH_SINGLE_EXECUTION_AUTHORIZED',
 'scope':ref(scope),'handoff':ref(handoff),'canonical':canon,'HEAD':head,
 'actual_before':[309,137,379],'output_absent':True,'source_compile_case_execution':0,
 'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps(ref(HERE/'preflight.json'),ensure_ascii=False))
