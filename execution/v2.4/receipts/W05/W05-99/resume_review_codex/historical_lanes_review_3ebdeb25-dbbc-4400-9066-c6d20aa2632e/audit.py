from pathlib import Path
import hashlib,json,subprocess,re,base64
ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/codex-w0599-command-queue';R=WT/'execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex';OUT=Path(__file__).resolve().parent;C='3d4f330f86cb132b5fd7c96acc333b2909997472'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def check(v):
 p=Path(v['path']);p=p if p.is_absolute() else WT/p
 b=p.read_bytes();assert sha(b)==v['sha256'].removeprefix('sha256:'),str(p)
 if 'bytes'in v:assert len(b)==v['bytes']
 return ref(p)
def git(*args,cwd=WT):return subprocess.check_output(['git',*args],cwd=cwd)
def batch(rev,paths,cwd=WT):
 b=subprocess.check_output(['git','cat-file','--batch'],cwd=cwd,input=''.join(rev+':'+p+'\n' for p in paths).encode());o={};i=0
 for p in paths:
  j=b.index(b'\n',i);h=b[i:j].decode().split();assert h[1]=='blob';n=int(h[2]);i=j+1;o[p]=b[i:i+n];i+=n+1
 return o
assert sha((R/'historical-final-audit.json').read_bytes())=='f80c17edc0a7160f8b0563dbe164c19925f6969824ca7adc22f8f2c94193c4b0'
manifest=R/'historical-receipt-manifest.json';assert sha(manifest.read_bytes())=='6586da57df111d656290d32d73e977ca521f1ce3e73261242d7b87810b5b5757'
paths=git('diff-tree','--no-commit-id','--name-only','-r',C).decode().splitlines();assert len(paths)==51 and all(p.startswith('execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/') for p in paths)
blobs=batch(C,paths)
for p,b in blobs.items():assert b==(WT/p).read_bytes()
for v in read(manifest)['files']:check(v)
source='internal/domain/backup_upgrade_test.go';assert git('show',C+':'+source)==git('show','3dffadd250cb4e5c312baf87e9136f7cfa8ba40a:'+source)
priorpath=ROOT/'execution/receipts/W16/current-control-admission/attempt-10-first-evaluation/actual-build.json';prior=read(priorpath);inputs=prior['source_provenance']['files'];assert len(inputs)==206
lanes=[]
for version in [14,20]:
 d=R/('schema'+str(version));prov=read(d/'snapshot-provenance.json');after=read(d/'source-after.json');before=prov['source_before'];assert before==after
 snapshot=Path(before[0]['path']);rel=prov['files'][0]['path']
 # use fixed registered source-only location, never old authority directories
 snapshot=WT/('.local/historical-fixtures-lanes/schema'+str(version)+'/source')
 assert {p.relative_to(snapshot).as_posix() for p in snapshot.rglob('*') if p.is_file()}=={v['path'] for v in prov['files']}
 assert sorted(int(Path(p).name[:4]) for p in prov['numbered_migrations'])==list(range(1,version+1))
 assert not any(Path(v['path']).suffix in ['.db','.sqlite','.exe'] for v in prov['files'])
 srcpaths=[v['path'] for v in prov['files']];origin=Path(prov['origin']);rev='09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0' if version==14 else '5c6d274a91f9f13d11e880a037133d1246f31811';oldblobs=batch(rev,srcpaths,cwd=ROOT)
 original_matches=0
 for v in prov['files']:
  p=v['path'];b=(snapshot/p).read_bytes();assert sha(b)==v['sha256']
  if version==20 and p in inputs:assert 'sha256:'+sha(b)==inputs[p]
  else:assert b==oldblobs[p]
  if (origin/p).is_file():assert (origin/p).read_bytes()==b;original_matches+=1
 for v in before:check(v)
 depbefore=read(d/'dependencies-before.json');depafter=read(d/'dependencies-after.json');assert depbefore==depafter
 for v in depbefore['files']:check(v)
 depraw=(d/'dependencies/stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();i=0;expected=set();missing=[]
 while depraw[i:].strip():
  i+=len(depraw[i:])-len(depraw[i:].lstrip());o,i=dec.raw_decode(depraw,i)
  for key in ['GoFiles','CgoFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:
   for name in o.get(key,[]):
    p=Path(name) if Path(name).is_absolute() else Path(o.get('Dir',''))/name
    if p.is_file():expected.add(str(p.resolve()))
    else:missing.append({'package':o.get('ImportPath'),'kind':key,'path':str(p)})
 assert expected=={v['path'] for v in depbefore['files']};assert missing==depbefore['generated_or_absent']
 assert all(p.relative_to(snapshot).as_posix() in srcpaths for p in map(Path,expected) if p.is_relative_to(snapshot))
 commands=[]
 for name in ['dependencies','test-build','original-tests']+(['control-reference-build'] if version==20 else []):
  command=read(d/name/'command.json');res=read(d/name/'result.json');assert res['exit_code']==0;check(command['executable']);check(command['runner']);check(res['stdout']);check(res['stderr']);assert 'W16_CONTROL_PROTECTED_EVIDENCE_DIR' not in command['environment'];assert command['environment']['GOPROXY']=='off'
  commands.append({'name':name,'command':ref(d/name/'command.json'),'result':ref(d/name/'result.json'),'stdout':ref(d/name/'stdout.raw'),'stderr':ref(d/name/'stderr.raw'),'exit':0})
 events=[json.loads(l) for l in (d/'original-tests/stdout.raw').read_text(encoding='utf-8').splitlines() if l.strip()];txt=''.join(v.get('Output','') for v in events);marker='W17_UPGRADE_ASSERTION ' if version==14 else 'W16_CONTROL_ASSERTION '
 assertions=[json.loads(l.split(marker,1)[1]) for l in txt.splitlines() if marker in l];assert len(assertions)==(7 if version==14 else 21)
 assert all(v['status']=='PASS' and v['actual']==v['expected'] and v['provider_calls']==0 for v in assertions)
 counts={s:len([e for e in events if e.get('Test') and e.get('Action')==s]) for s in ['pass','fail','skip']};assert counts=={'pass':1 if version==14 else 2,'fail':0,'skip':0}
 report=read(d/'report.json');binary=check(report['test_binary']);control=check(report['control_reference_binary']) if version==20 else None
 test=snapshot/('internal/domain/backup_upgrade_test.go' if version==14 else 'internal/domain/evolution_control_test.go');assert sha(test.read_bytes())==('9698a4a3fd7fe1aa22fbe2ea632d7799792413a31cc9a9b69ab19adaa67d9fb5' if version==14 else '8a578b7c3fa35a639fafc976998b4b1442606bbb002029f84bd02744426145ea')
 lanes.append({'version':version,'source_count':len(before),'source_provenance':ref(d/'snapshot-provenance.json'),'source_after':ref(d/'source-after.json'),'origin_existing_source_matches':original_matches,'exact_migrations':list(range(1,version+1)),'source_only_census_matches':True,'dependencies_count':len(expected),'dependencies_before':ref(d/'dependencies-before.json'),'dependencies_after':ref(d/'dependencies-after.json'),'generated_missing':missing,'all_current_hashes_match':True,'unchanged_test':ref(test),'binary':binary,'control':control,'commands':commands,'counts':counts,'assertions':assertions})
proofpath=R/'schema20/new-public-evidence/public-control-native-proof.json';proof=read(proofpath);h='sha256:'+lanes[1]['control']['sha256'];assert proof['stable_hash']==proof['candidate_hash']==h
assert read(R/'schema20/report.json')['control_reference_matches_actual_proof']==False
processes=[]
for pair in proof['pairs']:
 for side in ['baseline','candidate']:
  v=pair[side];receipt=v['receipt'];assert v['build_hash']==h;assert 'sha256:'+sha(v['raw'].encode())==v['raw_hash'];assert base64.b64decode(receipt['stdout'])==v['raw'].encode();assert receipt['exit_code']==0 and all(receipt[k] for k in ['streams_drained','cleanup_complete','output_copied','children_stopped']);assert not receipt['timed_out'];assert receipt['pid']==v['suspended_identity']['pid'];assert receipt['process_created_ns']==v['suspended_identity']['process_created_ns'];assert receipt['appcontainer_sid']==v['suspended_identity']['appcontainer_sid'];processes.append({'side':side,'pid':receipt['pid'],'build_hash':v['build_hash'],'raw_hash':v['raw_hash'],'exit':0,'cleanup_complete':True})
oldraw=WT/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/final-combined-regression-03/stdout.raw';assert sha(oldraw.read_bytes())=='ea95fc8deeecfca3b28ead5286b70e3f29d3f318cf61bf8e50359d97068897cb'
old_events=[json.loads(l) for l in oldraw.read_text(encoding='utf-8').splitlines() if l.strip()];oldfail=[e['Test'] for e in old_events if e.get('Test') and e.get('Action')=='fail'];assert set(['TestW17UpgradeActiveRecovery','TestW17UpgradeCLI','TestW16ControlReplayNative','TestW16ControlBusinessNoGain']).issubset(oldfail)
a={'candidate':C,'source_candidate':'3dffadd250cb4e5c312baf87e9136f7cfa8ba40a','all51_commit_receipt_blobs_current':True,'commit_blobs':[{'path':p,'sha256':sha(b),'bytes':len(b)} for p,b in blobs.items()],'manifest':ref(manifest),'manifest_refs_checked':len(read(manifest)['files']),'final_executor_audit':ref(R/'historical-final-audit.json'),'schema20_actual_build_provenance':ref(priorpath),'schema20_recorded_production_inputs':206,'lanes':lanes,'public_process_proof':ref(proofpath),'same_source_control_hash':h,'processes':processes,'original_main_failure_raw':ref(oldraw),'original_failures_retained':oldfail,'no_existing_private_DB_or_holdout_read_by_review':True,'review_product_reexecution':False}
(OUT/'audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'audit':ref(OUT/'audit.json'),'counts':[v['counts'] for v in lanes],'processes':len(processes)}))
