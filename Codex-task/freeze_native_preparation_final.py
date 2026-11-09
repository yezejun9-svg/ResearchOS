from pathlib import Path
import hashlib,json,shutil,re
base=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
main=Path('D:/作品集/ResearchOS/research-os')
wt=main/'.local/worktrees/product-v1-native-preparation-wiring-20261105'
rev3=base/'product-v1-native-preparation-wiring-author-20261105-rev3'
out=base/'product-v1-native-preparation-wiring-author-20261105-final'
if out.exists(): raise SystemExit('final archive exists; refusing overwrite')
out.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest()
entries={}
def copy(src,rel):
    src=Path(src); dst=out/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    raw=src.read_bytes();dst.write_bytes(raw)
    entries[rel]={'origin':str(src),'bytes':len(raw),'sha256':sha(raw)}
paths=['internal/domain/harness_preparation_windows.go','internal/domain/harness_preparation_windows_test.go','internal/domain/runtime_harness_windows.go','internal/host/harness_windows.go','internal/host/harness_windows_test.go']
author=json.loads((rev3/'MANIFEST.json').read_text(encoding='utf-8'))
for p in paths:
    copy(rev3/'source'/p,'source/'+p)
    copy(rev3/'baseline'/p,'baseline/'+p)
    if sha((wt/p).read_bytes())!=author['paths'][p]['source_sha256']:raise SystemExit('WT drift '+p)
    if (main/p).exists() and sha((main/p).read_bytes())!=author['paths'][p]['baseline_sha256']:raise SystemExit('Main baseline drift '+p)
for p in ['MANIFEST.json','forward.patch','inverse.patch']:
    copy(rev3/p,'rev3/'+('AUTHOR-MANIFEST.json' if p=='MANIFEST.json' else p))
copy(main/'execution/product-v1/receipts/single-harness-20261104/native-preparation-wiring/scope.json','scopes/source-lease.json')
copy(base/'product-v1-native-qualification-producer-author-20261105-rev4/MANIFEST.json','pins/b3-rev4-MANIFEST.json')
copy(base/'product-v1-native-preparation-overlay-directory-setup.json','evidence/physical-overlay-directory-setup.json')
for number,rev in [('01','rev2'),('02','rev3')]:
    prefix='product-v1-native-preparation-tests-'+number
    rundir=base/'product-v1-owned-verification-20261104/runs'/prefix
    for name in ['RESULT.json','stdout.raw','stderr.raw','CONSUMED.json']:
        src=rundir/name
        if src.exists():copy(src,'runs/'+number+'/'+name)
    copy(base/'product-v1-owned-verification-20261104/scopes'/(prefix+'.json'),'scopes/'+prefix+'.json')
    copy(base/(prefix+'-registration')/'REGISTRATION.json','runs/'+number+'/REGISTRATION.json')
    copy(base/('product-v1-native-preparation-test'+number+'-'+rev+'-overlay')/'overlay.json','overlays/'+number+'.json')
for rev in ['rev2','rev3']:
    src=base/('product-v1-native-preparation-wiring-'+rev+'-review-20261105/review-report.json')
    if src.exists():copy(src,'reviews/'+rev+'.json')
# Independently replay every unified hunk against raw UTF-8 bytes, both ways.
def apply_unified(old,patch,reverse=False):
    src=old.decode('utf-8').splitlines(keepends=True);dst=[];pos=0
    lines=patch.splitlines(keepends=True);i=0
    while i<len(lines):
        line=lines[i]
        if not line.startswith('@@ '):i+=1;continue
        m=re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@',line)
        if not m:raise ValueError('invalid hunk')
        start=int(m.group(2 if reverse else 1));start=start-1 if start else 0
        if start<pos:raise ValueError('overlapping hunk')
        dst.extend(src[pos:start]);pos=start;i+=1
        while i<len(lines) and not lines[i].startswith('@@ '):
            row=lines[i]
            if row.startswith('--- ') or row.startswith('+++ '):break
            if row.startswith('\\ No newline'):i+=1;continue
            if not row or row[0] not in ' +-':raise ValueError('invalid patch line')
            kind=row[0];payload=row[1:]
            if reverse:kind={'-':'+','+':'-',' ':' '}[kind]
            if kind in ' -':
                if pos>=len(src) or src[pos]!=payload:raise ValueError('patch context mismatch')
                pos+=1
            if kind in ' +':dst.append(payload)
            i+=1
    dst.extend(src[pos:]);return ''.join(dst).encode('utf-8')
def perfile(patch,p):
    lines=patch.splitlines(keepends=True);start=None;end=None
    for i,line in enumerate(lines):
        if line.startswith('--- ') and line[4:].strip().endswith('/'+p):start=i
        elif start is not None and line.startswith('--- '):end=i;break
    if start is None:return ''
    return ''.join(lines[start:end])
forward=(rev3/'forward.patch').read_text(encoding='utf-8')
inverse=(rev3/'inverse.patch').read_text(encoding='utf-8')
proof={}
for p in paths:
    old=(rev3/'baseline'/p).read_bytes();new=(rev3/'source'/p).read_bytes()
    f=apply_unified(old,perfile(forward,p));b=apply_unified(new,perfile(inverse,p))
    if f!=new or b!=old:raise SystemExit('inverse proof failed '+p)
    proof[p]={'forward_reconstructs_sha256':sha(f),'inverse_reconstructs_sha256':sha(b) if b else 'ABSENT_BEFORE'}
(out/'INVERSE-PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
entries['INVERSE-PROOF.json']={'origin':'generated from archived patches/source/baseline','bytes':(out/'INVERSE-PROOF.json').stat().st_size,'sha256':sha((out/'INVERSE-PROOF.json').read_bytes())}
results={n:json.loads((out/'runs'/n/'RESULT.json').read_text(encoding='utf-8')) for n in ['01','02']}
manifest={'schema':'researchos.native-preparation-wiring-final-author.v1','decision':'SOURCE_FIXTURE_ONLY','base_head':author['base_head'],'source_scope_sha256':author['scope_sha256'],'b3_rev4_manifest_sha256':author['b3_rev4_manifest_sha256'],'exact_paths':paths,'source_hashes':{p:author['paths'][p]['source_sha256'] for p in paths},'test01':{'status':results['01']['status'],'exit':results['01']['root_exit_code'],'scope_sha256':results['01']['scope_sha256'],'stop_proved':results['01']['stop_proved'],'input_drift':results['01']['input_drift'],'diagnostic':'test counted data.items; Events returns data.events'},'test02':{'status':results['02']['status'],'exit':results['02']['root_exit_code'],'scope_sha256':results['02']['scope_sha256'],'stop_proved':results['02']['stop_proved'],'input_drift':results['02']['input_drift'],'job_active_zero':results['02']['job_active_zero'],'job_total_processes':results['02']['job_total_processes']},'actual_native_or_model_runs':0,'archive_entries':entries}
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selection={'schema':'researchos.native-preparation-wiring-archive-selection.v1','manifest_sha256':sha((out/'MANIFEST.json').read_bytes()),'file_count_excluding_selection':len(entries)+1,'files':{p:v['sha256'] for p,v in entries.items()}}
selection['files']['MANIFEST.json']=selection['manifest_sha256']
(out/'ARCHIVE-SELECTION.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'directory':str(out),'manifest_sha256':selection['manifest_sha256'],'selection_sha256':sha((out/'ARCHIVE-SELECTION.json').read_bytes()),'files':len(selection['files']),'inverse_proved':len(proof),'test02':results['02']['status']},ensure_ascii=False))
