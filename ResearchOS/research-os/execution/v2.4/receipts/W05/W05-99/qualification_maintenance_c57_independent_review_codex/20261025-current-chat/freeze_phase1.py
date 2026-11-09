import hashlib, json, pathlib
BASE=pathlib.Path(__file__).parent
REPO=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
def digest(p):
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def create(name,obj):
    with (BASE/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(obj,f,ensure_ascii=False,indent=2); f.write('\n')
scopep=REPO/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp539/C57-independent-review-preparation-scope.json'
scope=read(scopep)
assert digest(scopep)['sha256']=='b0861156ead5dd71fb081a4aea92abec37510ed5c0a263eff07d07f4f7a973de'
sourcep=REPO/scope['source_scope_ref']['path']; source=read(sourcep)
refs=[scope['source_scope_ref'],scope['boot6_subscope_ref'],source['source43_independent_adoption_ref']]+source['inputs']+source['frozen_input_refs']
audit=[]
for ref in refs:
    p=pathlib.Path(ref['path'])
    if not p.is_absolute(): p=REPO/p
    actual=digest(p)
    ok=actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
    audit.append({'expected':ref,'actual':actual,'match':ok})
    assert ok, str(p)
for dirname,filenames in [
    ('qualification_failure_revision02_architecture_codex',['C-ARCHITECTURE.md','C-test-cuts.json']),
    ('qualification_failure_revision03_architecture_codex',['C-lease-test-cuts.json','F01-claims.json']),
    ('qualification_recovery_boot_supplement_architecture_codex',['BOOT-C-ARCHITECTURE.md'])
]:
    d=REPO/'execution/v2.4/receipts/W05/W05-99'/dirname/'20261015-current-chat'
    manifest=read(d/'FINAL-manifest.json')
    entries=manifest['entries'] if 'entries' in manifest else manifest['files']
    for filename in filenames:
        ref=next(x for x in entries if pathlib.Path(x['path']).name==filename)
        actual=digest(d/filename)
        ok=actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
        audit.append({'parent_manifest':str(d/'FINAL-manifest.json'),'expected':ref,'actual':actual,'match':ok})
        assert ok,filename
create('PHASE1-input-hash-audit.json',{'status':'EXACT_MATCH','preparation_scope':digest(scopep),'checked_refs':audit})
matrix=(BASE/'PHASE1-independent-matrix.md').read_text(encoding='utf-8')
ids=[]
for line in matrix.splitlines():
    if line.startswith('| ') and not line.startswith('| ID') and not line.startswith('|---'):
        ids.append(line.split('|')[1].strip())
assert len(ids)==len(set(ids))
create('PHASE1-status.json',{'status':'PREPARED_NOT_EXECUTED_NOT_SOURCE_ACCEPTANCE','owner':'codex:/root/c57_independent_review_20261025','matrix_rows':len(ids),'matrix_ids':ids,'frozen_candidate':'NOT_YET_FROZEN','tests_executed':0,'source_acceptance':False,'actual_authority':False,'formal_increment':0,'native_nonzero_count':2,'tool_diagnostic_count':0,'next_action':'WAIT_ROOT_EXACT_COMMIT_TREE_SOURCE_MANIFEST_SEAL_AMENDMENT'})
entries=[]
for p in sorted(BASE.rglob('*')):
    if not p.is_file() or '013-phase1-finalizer' in p.parts or p.name.startswith('PHASE1-manifest') or p.name.startswith('PHASE1-seal'): continue
    row=digest(p); row['path']=p.relative_to(BASE).as_posix(); entries.append(row)
create('PHASE1-manifest.json',{'status':'PHASE1_PREPARATION_FROZEN_NO_ACCEPTANCE','entries':entries,'entry_count':len(entries),'excluded':['PHASE1-manifest.json','PHASE1-seal.json','013-phase1-finalizer (active finalizer capture; retain separately and verify native_exit after return)'],'formal_increment':0})
create('PHASE1-seal.json',{'status':'PHASE1_PREPARATION_ONLY','manifest':digest(BASE/'PHASE1-manifest.json'),'matrix':digest(BASE/'PHASE1-independent-matrix.md'),'diagnostics':digest(BASE/'PHASE1-diagnostics.json'),'diagnostics_addendum':digest(BASE/'PHASE1-diagnostics-addendum-01.json'),'input_audit':digest(BASE/'PHASE1-input-hash-audit.json'),'candidate_tests_executed':0,'source_acceptance':False,'formal_increment':0})
print(json.dumps({'matrix_rows':len(ids),'refs_verified':len(audit),'manifest':digest(BASE/'PHASE1-manifest.json'),'seal':digest(BASE/'PHASE1-seal.json'),'matrix':digest(BASE/'PHASE1-independent-matrix.md')},ensure_ascii=False,indent=2))
