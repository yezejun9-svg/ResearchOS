from pathlib import Path
import hashlib,json,re
base=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
main=Path('D:/作品集/ResearchOS/research-os')
wt=main/'.local/worktrees/product-v1-native-prelaunch-intent-20261105'
rev2=base/'product-v1-native-prelaunch-intent-author-20261105-rev2'
out=base/'product-v1-native-prelaunch-intent-author-20261105-final'
if out.exists():raise SystemExit('final archive exists')
out.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
entries={}
def cp(src,rel):
 src=Path(src);dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 raw=src.read_bytes();dst.write_bytes(raw);entries[rel]={'origin':str(src),'bytes':len(raw),'sha256':sha(raw)}
paths=['adapters/runtime/codex_qualification_windows.go','adapters/runtime/codex_qualification_capture_windows.go','adapters/runtime/codex_qualification_capture_windows_test.go']
author=json.loads((rev2/'MANIFEST.json').read_text(encoding='utf-8'))
for p in paths:
 cp(rev2/'source'/p,'source/'+p);cp(rev2/'baseline'/p,'baseline/'+p)
 if sha((wt/p).read_bytes())!=author['paths'][p]['source_sha256']:raise SystemExit('WT drift '+p)
 if sha((main/p).read_bytes())!=author['paths'][p]['baseline_sha256']:raise SystemExit('Main baseline drift '+p)
for p in ['MANIFEST.json','forward.patch','inverse.patch']:cp(rev2/p,'rev2/'+('AUTHOR-MANIFEST.json' if p=='MANIFEST.json' else p))
cp(main/'execution/product-v1/receipts/single-harness-20261104/native-prelaunch-intent/scope.json','scopes/source-lease.json')
cp(main/'execution/product-v1/contracts/native-prelaunch-intent.v1.md','contracts/native-prelaunch-intent.v1.md')
for n in ['01','02']:
 prefix='product-v1-native-prelaunch-intent-tests-'+n
 run=base/'product-v1-owned-verification-20261104/runs'/prefix
 for name in ['RESULT.json','stdout.raw','stderr.raw','CONSUMED.json']:cp(run/name,'runs/'+n+'/'+name)
 cp(base/'product-v1-owned-verification-20261104/scopes'/(prefix+'.json'),'scopes/'+prefix+'.json')
 cp(base/(prefix+'-registration')/'REGISTRATION.json','runs/'+n+'/REGISTRATION.json')
for n in ['rev1','rev2']:
 p=base/('product-v1-native-prelaunch-intent-'+n+'-review-20261105/review-report.json')
 if p.exists():cp(p,'reviews/'+n+'.json')
# Replay both unified patch directions against the archived raw bytes.
def perfile(allpatch,p):
 lines=allpatch.splitlines(keepends=True);start=None;end=None
 for i,line in enumerate(lines):
  if line.startswith('--- ') and line[4:].strip().endswith('/'+p):start=i
  elif start is not None and line.startswith('--- '):end=i;break
 return ''.join(lines[start:end]) if start is not None else ''
def apply(old,patch,reverse=False):
 src=old.decode('utf-8').splitlines(keepends=True);dst=[];pos=0;lines=patch.splitlines(keepends=True);i=0
 while i<len(lines):
  if not lines[i].startswith('@@ '):i+=1;continue
  m=re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@',lines[i]);assert m
  n=int(m.group(2 if reverse else 1));start=n-1 if n else 0
  assert start>=pos;dst.extend(src[pos:start]);pos=start;i+=1
  while i<len(lines) and not lines[i].startswith('@@ '):
   row=lines[i]
   if row.startswith('--- ') or row.startswith('+++ '):break
   if row.startswith('\\ No newline'):i+=1;continue
   assert row and row[0] in ' +-';kind=row[0];payload=row[1:]
   if reverse:kind={'-':'+','+':'-',' ':' '}[kind]
   if kind in ' -':assert pos<len(src) and src[pos]==payload;pos+=1
   if kind in ' +':dst.append(payload)
   i+=1
 dst.extend(src[pos:]);return ''.join(dst).encode('utf-8')
forward=(rev2/'forward.patch').read_text(encoding='utf-8');inverse=(rev2/'inverse.patch').read_text(encoding='utf-8')
proof={}
for p in paths:
 old=(rev2/'baseline'/p).read_bytes();new=(rev2/'source'/p).read_bytes()
 f=apply(old,perfile(forward,p));b=apply(new,perfile(inverse,p))
 if f!=new or b!=old:raise SystemExit('inverse proof failed '+p)
 proof[p]={'forward_sha256':sha(f),'inverse_sha256':sha(b)}
(out/'INVERSE-PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
entries['INVERSE-PROOF.json']={'origin':'generated raw patch replay','bytes':(out/'INVERSE-PROOF.json').stat().st_size,'sha256':sha((out/'INVERSE-PROOF.json').read_bytes())}
results={n:json.loads((out/'runs'/n/'RESULT.json').read_text(encoding='utf-8')) for n in ['01','02']}
diagnostics=[{'origin':'native-prelaunch-intent:test01-compiler-heap-oom','classification':'RESOURCE_COMPILE_OOM','detail':'Go compiler heap arena map failed before tests ran; original raw retained; 38 owned processes stopped; no Native/model.'},{'origin':'native-prelaunch-intent:valid-binding-mutation-test-assumption','classification':'RESOLVED_STATIC_FIXTURE_DEFECT','detail':'Creation has one trusted typed context and checks digest format; final link rejects a different valid source binding against persisted intent.'},{'origin':'native-prelaunch-intent:atomic-patch-context-mismatch','classification':'RESOLVED_TOOL_DIAGNOSTIC','detail':'One apply_patch failed before mutation because gofmt text differed; rev1 hashes stayed unchanged.'}]
manifest={'schema':'researchos.native-prelaunch-intent-final-author.v1','decision':'SOURCE_FIXTURE_ONLY','base_head':author['base_head'],'source_scope_sha256':author['scope_sha256'],'contract_sha256':author['contract_sha256'],'exact_paths':paths,'source_hashes':{p:author['paths'][p]['source_sha256'] for p in paths},'test01':{'status':results['01']['status'],'exit':results['01']['root_exit_code'],'scope_sha256':results['01']['scope_sha256'],'stop_proved':results['01']['stop_proved'],'input_drift':results['01']['input_drift'],'tests_executed':0},'test02':{'status':results['02']['status'],'exit':results['02']['root_exit_code'],'scope_sha256':results['02']['scope_sha256'],'stop_proved':results['02']['stop_proved'],'job_active_zero':results['02']['job_active_zero'],'input_drift':results['02']['input_drift'],'selected_top_tests_passed':8},'actual_native_helper_model_runs':0,'diagnostics':diagnostics,'archive_entries':entries}
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selection={'schema':'researchos.native-prelaunch-intent-archive-selection.v1','manifest_sha256':sha((out/'MANIFEST.json').read_bytes()),'file_count_excluding_selection':len(entries)+1,'files':{p:v['sha256'] for p,v in entries.items()}}
selection['files']['MANIFEST.json']=selection['manifest_sha256']
(out/'ARCHIVE-SELECTION.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'directory':str(out),'manifest_sha256':selection['manifest_sha256'],'selection_sha256':sha((out/'ARCHIVE-SELECTION.json').read_bytes()),'files':len(selection['files']),'inverse_proved':len(proof),'test02':results['02']['status']},ensure_ascii=False))
