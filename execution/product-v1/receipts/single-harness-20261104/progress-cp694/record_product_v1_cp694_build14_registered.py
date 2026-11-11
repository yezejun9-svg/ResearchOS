import contextlib,hashlib,io,json,os,runpy
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp694'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.cp694.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==693 and cp['current_Main_HEAD']=='360c3eefd06ba82255352357c05ece00dae00d3a' and len(cp['failure_counters'])==2648 and not OUT.exists()
scope=HERE/'product-v1-owned-verification-20261104/scopes/product-v1-build-14.json';assert sha(scope)=='3338c07aa9fbcec4f96c149265b6865aae2d8e5121ecc9c15ce6313f417489fa';s=read(scope)
assert not (HERE/'product-v1-owned-verification-20261104/runs/product-v1-build-14').exists()
for item in s['inputs']:assert sha(Path(item['path']))==item['sha256']
audit=HERE/'reconnect-control-audit-20261106';assert sha(audit/'ROOT-FILEMAP.json')=='53c0fd6ef924bf8b5f350ef2da2559a5452f574fd6936734249abf412ac43e5a'
stream=io.StringIO()
with contextlib.redirect_stdout(stream):runpy.run_path(str(HERE/'product_v1_memory_readback.py'),run_name='__main__')
memory=json.loads(stream.getvalue());assert memory['available_commit_bytes']>=2*1024**3
now=datetime.now(timezone.utc).isoformat();OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for p in audit.iterdir():
 if p.is_file():(OUT/p.name).write_bytes(p.read_bytes())
progress=dict(checkpoint_revision=694,at=now,status='RECONNECTED_READONLY_AUDIT_PASS_NEW_BUILD14_REGISTERED_NOT_EXECUTED',main_head=cp['current_Main_HEAD'],source_count=70,source_union_sha256='954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2',build14_scope_path=str(scope),build14_scope_sha256=sha(scope),build14_inputs=len(s['inputs']),build14_registration_ref='execution/product-v1/receipts/single-harness-20261104/build14-scope/registration.json',memory=memory,old_controlled_roots_and_core='All5savedPIDscurrentlyabsent; historicalJobactive0/stopproved verified. No restored handles or globalprocessclaim.',old_changes_preserved=True,active_source_owners=[],real_model_requests=2,real_model_requests_unit='CONFIRMED_HOST_TASK_SUBMISSIONS_NOT_INFERENCE_COUNT',new_native_model_calls=0,product_journeys_accepted=0,legacy_formal_accepted=0,historical_records=2648,old_records_reset=False,next='Before execution inspect original-f13 runs/product-v1-build-14 CONSUMED/RESULT. If consumed never replay: reconcile current output/Job outcome. If absent execute the exact registered scope3338 once. After completed ownedJob0 perform producer/manifest/index/noextras/source70 verification and independent review, then bind NEW zero-model visual06 using reviewedcontroller12. New modelTask only under separately reviewed fresh synthetic scope; never resubmit oldTask or echo2of2. No OS/userprocess/security changes.')
put(OUT/'RESUME.json',progress);sf=ROOT/'execution/product-v1/state.json';sr=sf.read_bytes();st=read(sf);(OUT/'state.before.json').write_bytes(sr);st.update(revision=st['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
cp.update(revision=694,expected_previous_revision=693,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],formal_increment=0)
assert cpf.read_bytes()==raw and sf.read_bytes()==sr;put(sf,st);put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp694.new');assert not t.exists();t.write_bytes(('# Current resume CP694 - RECONNECTED; BUILD14 REGISTERED\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Main360c/70sourceunion954c verified, oldprotected18 intact. Readonlysavedprocessidentityaudit showsoldownedroots/coreabsent; no userprocesschange. Build14scope3338 registered; ALWAYS inspectCONSUMED/RESULTbeforelaunch, never replay. Newwindow/modelnotverified, journeys0/13 formal0/42.\n\n').encode('utf8')+old);os.replace(t,hf);(OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(dict(checkpoint=694,status=progress['status'],available_commit_bytes=memory['available_commit_bytes'],build14_scope_sha256=sha(scope),new_native_model_calls=0)))
