import pathlib,json,hashlib,datetime
E=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat')
def pin(p):return dict(path=str(p.relative_to(E)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def write(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
index=[];nonzero=[]
for recipe in sorted(E.glob('*.recipe.json')):
    rec=json.loads(recipe.read_text(encoding='utf-8-sig')); i=rec['id']; item=dict(kind='shell',id=i,recipe=pin(recipe),stdout=str(E/rec['stdout']),stderr=str(E/rec['stderr']),nativeexit=str(E/rec['nativeexit']))
    if i=='0024':item['seal_capture_note']='This terminal sealing capture closes after manifest generation; raw streams and native exit remain adjacent and deliberately outside frozen hash set.'
    else:
        code=int((E/rec['nativeexit']).read_text(encoding='utf-8-sig').strip());item['exit_code']=code;item['captures']=[pin(E/rec[k]) for k in ['stdout','stderr','nativeexit']]
        if code:nonzero.append(dict(kind='shell',id=i,exit_code=code,classification='reviewer_missing_parent_agents_diagnostic'))
    index.append(item)
for folder in sorted((E/'command-captures').iterdir()):
    if not folder.is_dir():continue
    rec=json.loads((folder/'result.json').read_text());assert rec['stdout_sha256']==hashlib.sha256((folder/'stdout.txt').read_bytes()).hexdigest();assert rec['stderr_sha256']==hashlib.sha256((folder/'stderr.txt').read_bytes()).hexdigest()
    index.append(dict(kind='native_child',id=folder.name,argv=rec['argv'],cwd=rec['cwd'],relevant_environment=rec['relevant_environment'],exit_code=rec['exit_code'],captures=[pin(folder/n) for n in ['command.json','result.json','stdout.txt','stderr.txt']]))
    if rec['exit_code']:nonzero.append(dict(kind='native_child',id=folder.name,exit_code=rec['exit_code'],argv=rec['argv'],classification='expected_phase_denial'))
assert sum(x['kind']=='native_child' for x in nonzero)==2,nonzero
assert sum(x['kind']=='shell' for x in nonzero)==1,nonzero
write('command-index.json',dict(schema='researchos.command-index.v1',commands=index,nonzero=nonzero,prior_counters_not_recounted=True,seal_envelope_excluded='0024 stdout/stderr/exit are completed after freeze; recipe and script pinned; parent may inspect terminal capture after return.'))
ledger=json.loads((E/'failure-ledger.json').read_text());ledger['current_nonzero_commands']=nonzero;write('failure-ledger.json',ledger)
r=json.loads((E/'review.json').read_text());r['failure_ledger']=dict(path=str(E/'failure-ledger.json'),sha256=hashlib.sha256((E/'failure-ledger.json').read_bytes()).hexdigest(),bytes=(E/'failure-ledger.json').stat().st_size);r['command_index']=dict(path=str(E/'command-index.json'),sha256=hashlib.sha256((E/'command-index.json').read_bytes()).hexdigest());write('review.json',r)
v=json.loads((E/'source-fixture-verification.json').read_text())
for item in v['source_files']:
    assert hashlib.sha256(pathlib.Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
for item in v['input_pins']:
    assert hashlib.sha256(pathlib.Path(item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
excluded={'FINAL-manifest.json','0024.stdout.txt','0024.stderr.txt','0024.exit.txt'}
files=[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name not in excluded]
manifest=dict(schema='researchos.owned-core-stop-r5-independent-final.v1',frozen_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=r['source_commit'],source_tree=r['source_tree'],verdict=r['verdict'],review=pin(E/'review.json'),review_md=pin(E/'review.md'),files=files,file_count=len(files),excluded_terminal_envelope=sorted(excluded),actual_authority=False,formal_increment=0,parent_acceptance=False)
write('FINAL-manifest.json',manifest)
for item in files:
    assert hashlib.sha256((E/item['path']).read_bytes()).hexdigest()==item['sha256']
print(json.dumps(dict(verdict=r['verdict'],file_count=len(files),command_count=len(index),nonzero=len(nonzero),manifest_sha256=hashlib.sha256((E/'FINAL-manifest.json').read_bytes()).hexdigest(),review_sha256=hashlib.sha256((E/'review.json').read_bytes()).hexdigest(),review_md_sha256=hashlib.sha256((E/'review.md').read_bytes()).hexdigest()),indent=2))
