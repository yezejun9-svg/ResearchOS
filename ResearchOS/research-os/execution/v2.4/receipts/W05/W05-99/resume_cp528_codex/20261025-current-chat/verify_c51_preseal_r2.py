import datetime,hashlib,json,re,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
B=R/'execution/v2.4/receipts/W05/W05-99/qualification_maintenance_c57_codex/20261025-current-chat'
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
refs={}
def verify(p,x=None,record=True):
 b=p.read_bytes();a={'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if x:
  assert a['sha256']==x['sha256'],str(p)
  if 'bytes'in x:assert a['bytes']==x['bytes'],str(p)
 if record:refs[a['path']]=a
 return a
seal=read(B/'C51-PRESEAL.json');verify(B/'C51-PRESEAL.json',{'sha256':'cd99649c24552dbd6394ba97daf04bb835da16170cd02c4ef0808684614b29fb'})
scope=read(N/'continuation-cp533/C57-source-scope.json');boot=read(N/'continuation-cp538/C57-boot6-source-subscope.json')
assert set(x['path']for x in seal['owned_files'])==set(scope['source_allowlist'])-set(boot['source_allowlist'])
assert len(seal['owned_files'])==51 and len(seal['changed_paths'])==46
source=[verify(W/x['path'],x,False)for x in seal['owned_files']]
assert seal['inherited43_exact_pins']==sorted(scope['inherited43_other_paths_must_remain_exact'],key=lambda x:x['path'])
pins=[verify(W/x['path'],x,False)for x in seal['inherited43_exact_pins']]
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *a:subprocess.check_output(git+list(a),cwd=W)
assert g('rev-parse','HEAD').decode().strip()==seal['base_commit']
assert g('rev-parse','HEAD^{tree}').decode().strip()==seal['base_tree']
assert not g('diff','--cached','--name-only')
changed=set(g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0)))|set(g('ls-files','--others','--exclude-standard','-z').decode().strip(chr(0)).split(chr(0)))
changed.discard('');assert changed<=set(scope['source_allowlist'])
assert changed-set(boot['source_allowlist'])==set(seal['changed_paths'])
verify(Path(seal['patch']['path']),seal['patch'])
headers=re.findall(r'^\+\+\+ b/(.+)$',Path(seal['patch']['path']).read_text().replace('\r\n','\n'),re.M)
assert set(headers)==set(seal['changed_paths']) and len(headers)==46
check=subprocess.run(git+['apply','--cached','--check','--whitespace=error',seal['patch']['path']],cwd=W,capture_output=True)
for stream in ['stdout','stderr']:
 p=N/('C51-root-patch-check-r2.'+stream+'.raw')
 with p.open('xb')as f:f.write(getattr(check,stream))
 verify(p)
assert check.returncode==0,(check.stdout,check.stderr)
ledger=(B/'C51-DIAGNOSTIC-LEDGER.jsonl').read_bytes();lines=ledger.splitlines(keepends=True)
prefix_sha=hashlib.sha256(b''.join(lines[:86])).hexdigest()
assert prefix_sha!='ee17964a2dec0902a1cbbefc3f227a2953054e5a175d6914a58c179bdecee939'
reconstructed=B/'C51-DIAGNOSTIC-LEDGER-RECONSTRUCTED-86.jsonl'
verify(reconstructed,{'sha256':'ee17964a2dec0902a1cbbefc3f227a2953054e5a175d6914a58c179bdecee939','bytes':60297})
verify(B/'C51-LEDGER-REWRITE-INCIDENT.json',{'sha256':'7466aeb459790a67caf0e9eb2b4c99722b8ad3d65040980957bdb777ac939141'})
verify(B/'C51-DIAGNOSTIC-INCREMENT-053.jsonl',{'sha256':'8cb37c0c2001bfd4c407d4320cc9bd0a7aafcb0c2df0fd3754ea312609a761df'})
verify(B/'C51-EARLY-RAW-ADDENDUM.md')
assert hashlib.sha256(ledger).hexdigest()=='a203004e23dd3b26d4508a7680808a0e083bec924f93f6359f3e08698829c6e7'
assert len(lines)==89

snapshot=N/'C51-DIAGNOSTIC-LEDGER.root-snapshot-89.jsonl'
with snapshot.open('xb')as f:f.write(ledger)
verify(snapshot);rows=[json.loads(s)for s in ledger.decode('utf-8-sig').splitlines()if s.strip()]
for x in rows:
 for item in x.get('files',[]):verify(B/item['name'],item)
for name in ['C51-DIAGNOSTIC-CROSSWALK.md','FORMAT-DIAGNOSTIC.md','042-049-source-snapshot.json']:
 verify(B/name)
 if name=='042-049-source-snapshot.json':assert verify(B/name)['sha256']==seal['test_source_snapshot_042_049_sha256']
raw_failures=[]
for x in rows:
 if x['kind']=='early_numbered_command':
  terminal=[f for f in x['files']if f['name'].endswith('.stdout.raw') and (B/f['name']).read_text(encoding='utf-8-sig').rstrip().endswith('FAIL')]
  if terminal:raw_failures.append({'ordinal':x['ordinal'],'native_exit':None,'observed':'Raw Go test output ends FAIL','files':terminal})
assert [x['ordinal']for x in raw_failures]==[2,7,13,15]
for x in rows:
 if x.get('native_exit_persisted'):
  exits=[f for f in x.get('files',[])if f['name'].endswith('.native-exit.txt')]
  assert len(exits)==1,x
  assert int((B/exits[0]['name']).read_text(encoding='utf-8-sig').strip())==x['native_exit']
out={'schema':'researchos.C51-root-preseal-verification.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'AUTHOR51_PRESEAL_AND_EVIDENCE_VERIFIED_NOT_INDEPENDENT_SOURCE_ACCEPTANCE','verified_count':len(refs),'verified_refs':list(refs.values()),'source51_observed':source,'inherited40_observed':pins,'base_commit':seal['base_commit'],'base_tree':seal['base_tree'],'changed_owned_paths':seal['changed_paths'],'patch_readonly_check_native_exit':0,'ledger_snapshot_entries':len(rows),'ledger_first86_current_bytes_preserved':False,'original86_reconstruction_hash_matches_original_announced_hash':True,'reconstruction_is_not_original_file_continuity':True,'current89_prefix_sha256':prefix_sha,'early_raw_FAIL_unknown_numeric_exit':raw_failures,'captured_nonzero_commands':[{k:x[k]for k in ['ordinal','native_exit','cause']}for x in rows if x.get('native_exit')not in [None,0]],'interim_failures_unknown_native_exit':[x for x in rows if x['kind']=='interim_tool_observation' and x.get('observed_exit_text')not in [None,'0']],'capture_gap_entries':sum(bool(x.get('capture_gap'))for x in rows),'no_current_tests_executed':True,'limitations':['Combined57 not frozen or committed','050-052 partial tests reportedly overlap Boot6 mutable source; no one frozen57 build claimed','Parent ledger crosswalk used later for dedup; historical unknown numeric exits stay unknown','007 and009 formatting history now detailed in additive report; current40pins exact, original pre-restore full diff capture still missing'],'formal_increment':0}
with(N/'C51-root-preseal-verification-r2.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write(chr(10))
print(json.dumps({k:out[k]for k in ['status','verified_count','ledger_snapshot_entries','capture_gap_entries','patch_readonly_check_native_exit','formal_increment']},ensure_ascii=False))

