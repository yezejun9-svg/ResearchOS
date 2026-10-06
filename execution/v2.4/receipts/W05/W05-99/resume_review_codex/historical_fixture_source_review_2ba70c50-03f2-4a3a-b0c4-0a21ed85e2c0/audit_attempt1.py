from pathlib import Path
import hashlib,json,subprocess,datetime
ROOT=Path('D:/作品集/ResearchOS/research-os');WT=ROOT/'.local/worktrees/codex-w0599-command-queue';OUT=Path(__file__).resolve().parent
C='3dffadd250cb4e5c312baf87e9136f7cfa8ba40a';P='internal/domain/backup_upgrade_test.go';R=WT/'execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def git(*args):return subprocess.check_output(['git',*args],cwd=WT)
def checkref(v):
 p=Path(v['path']);p=p if p.is_absolute() else WT/p
 assert sha(p.read_bytes())==v['sha256'],str(p)
 assert len(p.read_bytes())==v['bytes'],str(p)
 return ref(p)
registration=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/historical_fixture_root_registration.json'
assert sha(registration.read_bytes())=='ddc9b7130680bd5ad1506ac41ccf35fe7255cbd1dc5296e233da068df0c8b679'
scope=read(registration);sr=ROOT/scope['review_ref']['path'];assert sha(sr.read_bytes())==scope['review_ref']['sha256']
old=git('show',C+'^:'+P);new=git('show',C+':'+P);assert new==(WT/P).read_bytes()
lines=old.splitlines(keepends=True);prefix=b''.join(lines[:974]);suffix=b''.join(lines[981:]);span=b''.join(lines[974:981])
assert sha(old)==scope['source_boundary']['source_sha256'];assert sha(span)==scope['source_boundary']['old_span_sha256']
assert new.startswith(prefix) and new.endswith(suffix)
assert sha(prefix)==scope['source_boundary']['protected_exterior']['prefix_through_line974'];assert sha(suffix)==scope['source_boundary']['protected_exterior']['suffix_from_line982_to_EOF']
for s in scope['source_boundary']['protected_assertion_spans']:
 b=b''.join(lines[s['start_line']-1:s['end_line']]);assert sha(b)==s['sha256'] and len(b)==s['bytes'] and b in new
changed=git('diff-tree','--no-commit-id','--name-only','-r',C).decode().splitlines();assert [p for p in changed if not p.startswith('execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/')]==[P]
blobs=[]
for p in changed:
 b=git('show',C+':'+p);assert b==(WT/p).read_bytes();blobs.append({'path':p,'sha256':sha(b),'bytes':len(b)})
manifest=read(R/'selector-receipt-manifest.json');refs=[checkref(v) for v in manifest['files']]
a=read(R/'selector-inputs-before.json');b=read(R/'selector-inputs-after.json');assert a==b
inputs=[checkref(v) for v in a['files']]
binary=checkref(read(R/'selector-test-binary.json'))
runs=[]
for name in ['selector-dependencies','selector-build','valid-artifact','missing-artifact','wrong-hash-artifact']:
 d=R/name;c=read(d/'command.json');r=read(d/'result.json');checkref(c['exe']);checkref(c['source_file']);checkref(r['stdout']);checkref(r['stderr'])
 assert r['exit_code']==(1 if name in ['missing-artifact','wrong-hash-artifact'] else 0)
 item={'name':name,'command':ref(d/'command.json'),'result':ref(d/'result.json'),'stdout':ref(d/'stdout.raw'),'stderr':ref(d/'stderr.raw'),'exit':r['exit_code']}
 if name.endswith('artifact'):
  events=[json.loads(l) for l in (d/'stdout.raw').read_text().splitlines() if l.strip()];texts=''.join(e.get('Output','') for e in events)
  item['counts']={s:len([e for e in events if e.get('Test') and e.get('Action')==s]) for s in ['pass','fail','skip']};assert item['counts']['skip']==0
  item['assertions']=[json.loads(l.split('W17_UPGRADE_ASSERTION ',1)[1]) for l in texts.splitlines() if 'W17_UPGRADE_ASSERTION ' in l]
  if name=='valid-artifact':
   assert item['counts']=={'pass':1,'fail':0,'skip':0};assert len(item['assertions'])==5 and all(x['actual']==x['expected'] and x['status']=='PASS' and x['provider_calls']==0 and x['private_body_read']==False for x in item['assertions'])
   item['fixed_artifact']=ref(Path(c['environment']['RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL']));assert item['fixed_artifact']['sha256']=='aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032'
  else:
   assert item['counts']=={'pass':0,'fail':1,'skip':0};assert not item['assertions'];assert ('historical schema14 artifact read:' if name=='missing-artifact' else 'historical schema14 artifact hash mismatch') in texts
 runs.append(item)
# Preserve the original build branch verbatim modulo its required extra indentation inside else.
oldbuild=b''.join(lines[975:980]);newspan=new[len(prefix):-len(suffix)]
assert b''.join(b'\t'+l for l in oldbuild.splitlines(keepends=True)) in newspan
result={'schema':'researchos.independent-historical-selector-audit.v1','actor':'codex:/root/w05_merge_review','candidate_commit':C,'registration':ref(registration),'scope_review':ref(sr),'source':ref(WT/P),'old_source_sha256':sha(old),'prefix_sha256':sha(prefix),'suffix_sha256':sha(suffix),'protected_exterior_exact':True,'no_env_build_branch_unchanged_except_nesting_indent':True,'commit_blobs':blobs,'receipt_manifest':ref(R/'selector-receipt-manifest.json'),'manifest_refs_checked':len(refs),'source_inputs_count':len(inputs),'source_before_after_equal':True,'all_input_hashes_current':True,'inputs_before':ref(R/'selector-inputs-before.json'),'inputs_after':ref(R/'selector-inputs-after.json'),'test_binary':binary,'runs':runs,'independent_reexecution':False,'executor_raw_independently_reparsed':True}
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'audit':ref(OUT/'audit.json'),'source':result['source'],'blobs':len(blobs),'inputs':len(inputs)}))
