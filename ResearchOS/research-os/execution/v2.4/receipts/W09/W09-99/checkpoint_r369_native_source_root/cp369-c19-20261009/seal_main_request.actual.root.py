"""Seal a current four-document vector and exact Root single Main C19 request."""
import hashlib, json
from pathlib import Path
import sys, types
N=Path(__file__).resolve().parent
p=N/'register_cp369.source.py';raw=p.read_bytes()
assert len(raw)==14628 and hashlib.sha256(raw).hexdigest()=='b0c4e3efdc5a1500d57ad804a9b6f56c7d46f20e10e887db70ee9c1735ac4adb'
m=types.ModuleType('root_main_c19_vector');m.__file__=str(p);sys.modules[m.__name__]=m
exec(compile(raw,str(p),'exec'),m.__dict__)
proof_ref=dict(path=str((N/'canonical_pair.activate.json').resolve(strict=True)),sha256='af5f3abdf92bb1d6a349ecc57e362d873ba660aa1e603745f840cc198b1fafe2',bytes=1588)
proof=m.load(proof_ref)
m.require(proof['mode']=='activate' and proof['all_handles_closed'] is True and proof['registered_count']==963 and proof['highest_cutoff']==965 and proof['live_next']==970 and proof['Native_executed'] is False,'ACTUAL_REGISTRATION_CLOSED')
facts=m.load(m.pin(N/'checkpoint.execution.facts.json'));scope,owner,worker=m.scope_bindings(facts)
refs=[m.pin(path) for path in m.CANON]
m.require(refs[:2]==proof['proposed_refs'] and refs[2:]==facts['canonical_refs'][2:],'EXACT_CURRENT_AFTER_VECTOR')
cp,ow=[m.load(ref) for ref in refs[:2]]
m.require(cp['revision']==369 and ow['revision']==173 and ow['card_path_bindings']['W09-99']['subtasks'][m.KEY]==owner and [v for v in cp['workers'] if v.get('slice_id')==m.SLICE]==[worker],'EXACT_CURRENT_ROOT_OWNER')
vr=m.save('Main-C19-current-canonical-vector.actual.root.json',dict(schema='researchos.w09-main-c19-native-canonical-vector.v1',checkpoint_revision=369,ownership_revision=173,refs=refs))
request=dict(schema='researchos.root-w09-main-c19-native-request.v1',issued_by=m.ACTOR,scope_ref=facts['scope_ref'],canonical_vector_ref=vr,calling_contract_ref=facts['calling_contract_ref'])
qr=m.save('Main-C19-single-native-request.actual.root.json',request)
contract=m.load(facts['calling_contract_ref']);argv={}
for kind in ('prepare','run'):
    v=contract['future_argv'][kind]
    m.require(v[-3:]==['ROOT_REQUEST_ABSOLUTE_PATH','ROOT_REQUEST_BARE_SHA256','ROOT_REQUEST_BYTES'],'EXACT_CALLING_CONTRACT_ARGV')
    argv[kind]=v[:-3]+[qr['path'],qr['sha256'],str(qr['bytes'])]
for key in ('receipt_root','scratch_root','output_root'):m.require(not Path(scope[key]).exists(),'FRESH_'+key)
ar=m.save('Main-C19-two-stage-argv.actual.root.json',dict(schema='researchos.root-main-c19-two-stage-argv.v1',argv=argv,cwd=contract['future_CWD'],request_ref=qr,canonical_vector_ref=vr,scope_ref=facts['scope_ref'],calling_contract_ref=facts['calling_contract_ref'],canonical_refs=refs,maximum_go_list_runs=1,maximum_go_test_runs=1,automatic_retry=False,formal_case_accepted_delta=0))
print(json.dumps(dict(argv_ref=ar,request_ref=qr,canonical_vector_ref=vr,current_canonical_refs=refs,formal_case_accepted_delta=0,Native_started=False),ensure_ascii=False),flush=True)
