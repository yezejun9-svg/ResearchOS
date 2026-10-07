"""Read-only evidence/Git audit; writes only beside this script; executes no tests."""
from pathlib import Path
import collections, hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
TARGET = 'f510491'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)
def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def blobset(ref):
    result={}
    for item in git('ls-tree','-r','-z',ref).split(b'\0'):
        if not item: continue
        meta,path=item.split(b'\t',1)
        mode,kind,oid=meta.decode().split()
        if kind=='blob': result[path.decode()] = oid
    return result
target_ref=git('rev-parse',TARGET).decode().strip()
head=git('rev-parse','HEAD').decode().strip()
trees={target_ref:blobset(target_ref)}
def tree(ref):
    if ref not in trees: trees[ref]=blobset(ref)
    return trees[ref]
blob_cache={}
def blobs(oids):
    missing=sorted(set(oids)-blob_cache.keys())
    if not missing:return
    data=git('cat-file','--batch') if False else subprocess.run(['git','cat-file','--batch'],input=('\n'.join(missing)+'\n').encode(),stdout=subprocess.PIPE,check=True,cwd=ROOT).stdout
    pos=0
    for oid in missing:
        end=data.index(b'\n',pos); info=data[pos:end].split(); n=int(info[2]); pos=end+1
        blob_cache[oid]=data[pos:pos+n];pos+=n+1
def byte_forms(raw):
    lf=raw.replace(b'\r\n',b'\n')
    return {'git':sha(raw),'lf':sha(lf),'crlf':sha(lf.replace(b'\n',b'\r\n'))}
status=load('execution/acceptance_status.json')
ledger=load('execution/bootstrap_ledger.json')
commands=load('execution/command_verifications.json')
all_receipts={}
for ref in ledger['task_receipt_refs']:
    p=ROOT/ref
    all_receipts[ref]={'exists':p.is_file(),'sha256':sha(p.read_bytes()) if p.is_file() else None}
ext={}
for v in ledger['external_verifier_acceptances']:
    ref=v if isinstance(v,str) else v['reference']; expected=None if isinstance(v,str) else v.get('sha256')
    p=ROOT/ref;actual=sha(p.read_bytes()) if p.is_file() else None
    ext[ref]={'exists':p.is_file(),'declared_sha256':expected,'actual_sha256':actual,'hash_match':actual==expected if expected else None}
rows=[]
for case,s in status['cases'].items():
    row={'case':case,'historical_status':s['status'],'accepted_mode':s.get('mode'),'accepted_revision':s.get('executed_code_revision'),'case_index':s,'evidence_refs':[]}
    envs=[]
    for ref in s.get('evidence',[]):
        p=ROOT/ref; e={'ref':ref,'exists':p.is_file(),'sha256':sha(p.read_bytes()) if p.is_file() else None}
        if ref in ext:e['ledger_external_binding']=ext[ref]
        row['evidence_refs'].append(e)
        if '/receipts/' in ref and ref.endswith('/'+case+'.json') and p.is_file():envs.append((ref,load(ref)))
    if envs:
        ref,d=envs[-1];vm=d.get('version_manifest',{}); inv=vm.get('source_sha256',{})
        rev=vm.get('git_head') or row['accepted_revision']; oldtree=tree(rev); newtree=tree(target_ref)
        blobs([oldtree[p] for p in inv if p in oldtree]+[newtree[p] for p in inv if p in newtree])
        files=[]
        for p,expected in inv.items():
            old=oldtree.get(p);new=newtree.get(p);oldforms=byte_forms(blob_cache[old]) if old else {};newforms=byte_forms(blob_cache[new]) if new else {}
            disk=sha((ROOT/p).read_bytes()) if (ROOT/p).is_file() else None
            files.append({'path':p,'declared_sha256':expected,'old_git_blob':old,'target_git_blob':new,'same_git_blob':bool(old and old==new),'old_declared_byte_match':expected in oldforms.values(),'old_byte_forms':oldforms,'target_byte_forms':newforms,'target_disk_sha256':disk,'exact_declared_disk_match':expected==disk,'tracked_source_changed':old!=new})
        row.update(envelope_ref=ref,envelope_revision=rev,source_inventory_count=len(inv),source_files=files,declared_hash_mismatch=[f['path'] for f in files if not f['old_declared_byte_match']],changed_inventory_paths=[f['path'] for f in files if f['tracked_source_changed']],git_changes_since_envelope=[p for p in sorted(set(oldtree)|set(newtree)) if oldtree.get(p)!=newtree.get(p) and not p.startswith(('execution/','.local/'))],command_receipt=d.get('command_receipt'),assertions=d.get('assertion_results'),limits=d.get('limits'))
    else:row['inventory_status']='UNKNOWN_NO_CASE_ENVELOPE_INVENTORY'
    rows.append(row)
command_rows=[]
for key,v in commands['commands'].items():
    ref=v['receipt'];p=ROOT/ref;actual=sha(p.read_bytes()) if p.is_file() else None
    d=load(ref) if p.is_file() else {}
    command_rows.append({'key':key,'registered':v,'actual_sha256':actual,'hash_match':actual==v.get('sha256'),'receipt':d})
report={'verdict':'READ_ONLY_VERSION_REUSE_AUDIT','target_source':target_ref,'sampled_head':head,'tracked_status':git('status','--porcelain','-uno').decode(),'head_delta_from_source':git('diff','--name-only',target_ref,head).decode().splitlines(),'input_hashes':{p:sha((ROOT/p).read_bytes()) for p in ['execution/acceptance_status.json','execution/bootstrap_ledger.json','execution/command_verifications.json']},'historical_status_counts':dict(collections.Counter(r['historical_status'] for r in rows)),'task_receipt_refs':all_receipts,'external_acceptance_bindings':ext,'command_verifications':command_rows,'cases':rows,'limits':['No tests, native/private/provider/S2 execution.','Git byte differences are not automatic behavior failures. Missing inventory coverage is UNKNOWN, not historical PASS revocation.','Git LF/CRLF normalization is explicitly compared; exact on-disk SHA256 is retained.']}
(OUT/'inventory-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for r in rows:
    print(r['case'],r['historical_status'],r.get('source_inventory_count',0),'changed',len(r.get('changed_inventory_paths',[])),'oldhash-mismatch',len(r.get('declared_hash_mismatch',[])))
print('external_hash_mismatch',[k for k,v in ext.items() if v['hash_match'] is False])
print('commands_hash_mismatch',[v['key'] for v in command_rows if not v['hash_match']])
