from pathlib import Path
import ast,hashlib,importlib.util,json
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).resolve().parent
inputs={};checks=[]
def check(name,value):checks.append(dict(name=name,passed=bool(value)))
def norm(ref):return dict(path=str(Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
def add(ref):
 ref=norm(ref);key=ref['path'].casefold();assert key not in inputs or inputs[key]==ref;inputs[key]=ref;return ref
def read(ref):
 ref=add(ref)
 with Path(ref['path']).open('rb') as f:raw=f.read(ref['bytes']+1)
 assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'];return raw
def obj(ref):return json.loads(read(ref))
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def members(m):return list(m['members'].values()) if isinstance(m['members'],dict) else m['members']
def fixed(folder,name,sha,size):return dict(path=str(B/folder/name),sha256=sha,bytes=size)
def save(name,v):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
oldref=fixed('native_grant_public_pin_archive_independent_review_codex/gpa-review-01a11ee7','HDF.json','b9d59d5ac11e90c6a47599e26690265d387e93dc91a158a61bec6649ea10f2c0',2336);old=obj(oldref)
oldmf=obj(old['manifest_ref']);read(old['report_ref']);finding=obj(old['finding_ref'])
for ref in members(oldmf):read(ref)
check('old GPA basis exact RequestChanges reused',old['decision']=='REQUEST_CHANGES')
gbh=obj(fixed('native_grant_bounded_read_revision_codex/gbr-1a11ee4f162766098eda3028b0679f2','HDF.json','0319c53ef7c5900922c07a1509e71f39edd5bff7856dbdcd250b38573cb8927b',4171));gbmf=obj(gbh['manifest_ref'])
for ref in members(gbmf):read(ref)
helper=read(gbh['source_ref']);check('bounded delta all independent checks pass',all(x['passed'] for x in json.loads((O/'bounded-delta-checks.json').read_bytes())))
afref=fixed('native_grant_request_builder_independent_review_codex/gqbr-20261009-source-review','HDF.json','839dda15700bc325c22f20bf479efb639aa38da2280de488b75d8acca8ac3e8d',2515);af=obj(afref);afmf=obj(af['manifest_ref'])
check('AF exact MF pin',norm(af['manifest_ref'])['sha256']=='d4a016ded2fae79d6ac2b0713034cebcba6884d77e540129b9e5f4bf88fde424' and af['manifest_ref']['bytes']==8061)
for ref in members(afmf):read(ref)
check('AF Source accepted and stopped',af['status']=='SOURCE_ACCEPTED_FOR_ROOT_INERT_REQUEST_GENERATION' and af['STOP_FINAL'] is True and af['check_count']==153)
afinputs=obj(af['inputs_ref']);afrefs=afinputs if isinstance(afinputs,list) else afinputs['refs']
for ref in afrefs:read(ref)
check('AF binds new helper exact',any(norm(ref)==norm(gbh['source_ref']) for ref in afrefs))
gqbh=obj(fixed('native_grant_archive_request_builder_source_codex/gqb-1a11ee4f162766098eda3028b0679f2','HDF.json','50981bdb61b1a0cdd0c9ce183f4bd464ffcdf1817c2025478d5b531bd41508c6',4119))
gqbmf=obj(fixed('native_grant_archive_request_builder_source_codex/gqb-1a11ee4f162766098eda3028b0679f2','MF.json','ddaba804b9bc820952aa1c26cf347bc34801f4ac91ba308ecafa3e4d9e7f4731',4949))
for ref in members(gqbmf):read(ref)
builder=read(af['candidate_source_ref']);check('AF exact builder Source pin',norm(af['candidate_source_ref'])['sha256']=='732694a07b89813c39e794e21f7edb1bc3ee7a335a0d8a0b8cf1c503fcd002cc' and len(builder)==24509)
prelaunchref=fixed('native_c12_final_prelaunch_independent_review_codex/c12pre-20261009-final-review','HDF.json','e96a4f488b1c73cbfc0ca003f11edb01c1be584e9cf1c8f4df10c1b342bd7e35',4055);pre=obj(prelaunchref);pmf=obj(pre['manifest_ref'])
for ref in members(pmf):read(ref)
check('C12 prior final prelaunch accepted',pre['status']=='FINAL_PRELAUNCH_SOURCE_ACCEPTED_FOR_ONE_ROOT_SYNTHETIC_CASE')
cfg=obj(pre['config_ref']);check('fixed config exact',norm(pre['config_ref'])['sha256']=='38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256' and pre['config_ref']['bytes']==1106152)
check('FrozenInputs4185 inventory retained',len(cfg['FrozenInputs'])==pre['frozen_input_count']==4185 and len({norm(ref)['path'].casefold() for ref in cfg['FrozenInputs']})==4185)
for ref in cfg['FrozenInputs']:add(ref)
manual=obj(pre['candidate_handoff_ref']);mmf=obj(pre['candidate_manifest_ref'])
for ref in members(mmf):read(ref)
manualrefs={key:manual[key] for key in ('serve_ref','api_ref','preparer_ref')}
for ref in manualrefs.values():read(ref)
check('C12 manual callers unchanged',manual['actual_config_pin']==pre['config_ref'])
oldcanonical=json.loads((B/'historical20_r2_caller_independent_review_codex/h20r2-caller-01a11ee7/canonical.observed.json').read_bytes())['refs']
for ref in oldcanonical.values():read(ref)
check('CP364 and other canonical exact',obj(oldcanonical['checkpoint'])['revision']==364)
tree=ast.parse(helper);constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('CONFIG_SHA','CONFIG_BYTES','CASE_ID','INVENTORY')}
check('helper current C12 constants',constants['CONFIG_SHA']=='sha256:'+norm(pre['config_ref'])['sha256'] and constants['CONFIG_BYTES']==1106152 and constants['CASE_ID']=='t12cl149d6f49321')
inventory=constants['INVENTORY'];sourcecount=sum(not name.startswith('migrations/sqlite/0024_') for name in inventory);targetcount=len(inventory)
check('TEMP 57 inventory entries',sourcecount==28 and targetcount==29 and sourcecount+targetcount==57)
text=helper.decode('utf-8')
check('archive output still gated on closed guard',text.index('cleanup = guard.close()')<text.index('result["source_guard_cleanup"] = cleanup')<text.index('return emit_new(output / "archive.public.manifest.json"'))
check('full temp closure and backup ciphers retained',all(s in text for s in ('"FULL_TEMP_PIN_CLOSURE" if not missing else "PARTIAL"','"backup ciphertext closure"','"fixture release already requested"','"encrypted-backup-manifest"','"isolated-restore-rehearsal"')))
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';gref=pin(G);assert gref['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85';add(gref)
s=importlib.util.spec_from_file_location('sourceguard',G);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(list(inputs.values()))
 for ref in cfg['FrozenInputs']:check('live FrozenInput exact:'+ref['path'],hashlib.sha256(guard.get_buffer(ref['path'])).hexdigest()==ref['sha256'].removeprefix('sha256:'))
finally:cleanup=guard.close()
check('resource guard released',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
save('resource-gate-checks.json',checks);save('resource-gate-input-pins.json',list(inputs.values()));save('resource-gate-guard.final.json',cleanup)
save('resource-gate-binding.json',dict(old_GPA_review_ref=oldref,bounded_helper_ref=gbh['source_ref'],AF_review_ref=afref,AF_manifest_ref=af['manifest_ref'],builder_ref=af['candidate_source_ref'],C12_prelaunch_ref=prelaunchref,config_ref=pre['config_ref'],frozen_input_count=4185,manual_refs=manualrefs,canonical_refs=oldcanonical,checkpoint_revision=364,required_before_fixture_release=['Root reviews concrete inert request','Root separately executes exact bounded helper','57 inventory + backup + original rehearsal + every ciphertext archived raw','FULL_TEMP_PIN_CLOSURE with missing_roles empty and archived count equals required count','original/archive SHA256 and byte lengths equal and output reread succeeds','guard actual closed with no errors','archive manifest exact pin retained','existing matching whole-fixture inspection and explicit release remain mandatory'],resource_gate_kind='Source acceptance only; mandatory Root actual gate, no automatic phase approval or manual-script change',Native_actual_success=False))
print(json.dumps(dict(checks=len(checks),failed=[x['name'] for x in checks if not x['passed']],input_count=len(inputs),frozen_input_count=4185,guard_closed=cleanup['closed'],guard_retained=cleanup['retained_handles_count'],CP=364,native_actual=False)))
