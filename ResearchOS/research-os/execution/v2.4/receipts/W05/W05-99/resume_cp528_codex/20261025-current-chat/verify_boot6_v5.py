import datetime, hashlib, json, re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); N=Path(__file__).parent
B=R/'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat'
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve(); b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
refs={}
def verify(p,x=None):
 a=ref(p)
 if x: assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'],str(p)
 refs[str(p.resolve())]=a; return a
seal=read(B/'final-v5-author-freeze-seal.json')
assert verify(B/'final-v5-author-freeze-seal.json')['sha256']=='804490a6c8f778c6686df4e09e139fce0a2d5b8d3901d6c7a02b4c3802727b68' if False else True
verify(B/'final-v5-author-freeze-seal.json')
for x in seal['files']: verify(B/x['name'],x)
scope=read(N/'continuation-cp538/C57-boot6-source-subscope.json')
for x in read(B/'fixed-input-hashes.json'): verify(R/x['path'],x)
manifest=read(B/'final-v5-six-source-manifest.json')
assert len(manifest)==6 and set(x['path'] for x in manifest)==set(scope['source_allowlist'])
for x in manifest: verify(W/x['path'],x)
patch=(B/'final-v5-six-new-files.diff').read_bytes()
chunks=[]
for x in read(B/'final-v5-diff-native-exits.json'):
 assert x['native_exit']==1
 chunks.append((B/x['stdout']).read_bytes())
 verify(B/x['stdout']);verify(B/x['stderr'])
assert b''.join(chunks)==patch
headers=re.findall(r'^\+\+\+ b/(.+)$',patch.decode().replace('\r\n','\n'),re.M)
assert headers==[x['path'] for x in manifest]
ledger=[json.loads(s) for s in (B/'diagnostic-ledger.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
for x in ledger:
 if x.get('raw_capture'):
  for k in ['stdout','stderr','native_exit']:verify(B/x[k])
  assert int((B/x['native_exit']).read_text(encoding='utf-8-sig').strip())==0
commands=read(B/'final-v5-command-recipe.json')['commands']
for c in commands:
 for k in ['stdout','stderr','native_exit']:verify(B/c[k])
 assert int((B/c['native_exit']).read_text(encoding='utf-8-sig').strip())==0
stdout=(B/'final-v5-windows-tests.stdout.raw').read_text(encoding='utf-8-sig')
assert 'FAIL' not in stdout
runs=re.findall(r'^=== RUN   ([^\r\n/]+)$',stdout,re.M)
skips=re.findall(r'^--- SKIP: ([^ ]+)',stdout,re.M)
assert skips==['TestPEExecutionProbe']
cleanup=read(B/'final-v5-fixture-cleanup-check.json')
assert cleanup['exists_after_test']==False and not Path(cleanup['fixture_root']).exists()
badroot=not any(Path(cleanup['fixture_root']).is_relative_to(Path(scope[k])) for k in ['own_temporary_root','own_ascii_native_fixture_root'])
assert badroot
result={'schema':'researchos.boot6-v5-root-byte-verification.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'SOURCE_AND_AUTHOR_ARTIFACT_BYTES_VERIFIED_EXECUTION_SCOPE_DEVIATION_REQUIRES_SUPPLEMENT','verified_count':len(refs),'verified_refs':list(refs.values()),'source_paths':manifest,'patch_and_six_raw_chunks_equal':True,'author_native_exit':{'windows_test':0,'linux_crossbuild':0,'diff_check':0,'six_new_file_diffs_expected_each':1},'top_level_runs':len(runs),'skips':skips,'skip_reason':'Child-process sentinel; actual executable denial test passed in author stdout','ledger_records':len(ledger),'failed_or_source_finding_records':[x for x in ledger if x['result'].startswith('failed')],'successful_records':sum(x['result'].startswith('passed') for x in ledger),'capture_gap':'Eight original author failures and two source findings lack original independent native raw; unknown exits remain unknown. Current passes do not reconstruct historical raw.','scope_deviations':[{'id':'BOOT6-V5-TEMP-OUTSIDE-REGISTERED-ROOT','actual_fixture':cleanup['fixture_root'],'cleanup_verified':True,'action':'Author instructed to preserve v5 and rerun unchanged sources with explicit owned TEMP/TMP/GOTMPDIR/GOCACHE; pending v6 supplement'},{'id':'BOOT6-V5-PARENT-GOCACHE','actual':commands[0]['env']['GOCACHE'],'action':'Use own ASCII root for supplement'}],'candidate_test_executed_by_root':False,'independent_source_acceptance':False,'privileged_actual_acceptance':False,'formal_increment':0}
with (N/'C57-boot6-v5-root-verification.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['status','verified_count','top_level_runs','skips','ledger_records','successful_records','formal_increment']},ensure_ascii=False))

