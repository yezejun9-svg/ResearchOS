import ast,difflib,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';B=R/'execution/v2.4/receipts/W05/W05-99';N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/n)
def obj(p):return json.loads(Path(p).read_bytes())
def verified(ref):
 actual=pin(ref['path']);assert (actual['sha256'],actual['bytes'])==(ref['sha256'].removeprefix('sha256:'),ref['bytes']);return actual
C=W/'w09_c19_consumer_contract_readonly_codex/w09c19-consumer-20261009';S=W/'w09_c19_caller_source_revision_codex/w09c19r2-1a11f08'
assert pin(C/'HDF.json')['sha256']=='9833fa83bfeeac84fdc15162d71c0fed045093c42c9f1d210c01eb8960b62769'
assert pin(C/'MF.json')['sha256']=='2aad4b568bf99bb4dfda5a70612c2c5045ae7db5ef153aaac5e6ac324b3d0f2f'
assert pin(S/'HDF.json')['sha256']=='bfb479d0c441c0eeec03858ee41f1d12150e50c8b7b2cee563c16025525e58f2'
assert pin(S/'MF.json')['sha256']=='455553ae51eb98c6ead665c7f9dfde0d9e6b5e765418d760f335d5f8845b0ab8'
h=obj(C/'HDF.json');contract_ref=verified(h['contract_ref']);mode_fields_ref=verified(h['mode_fields_ref']);contract=obj(contract_ref['path'])
source_choice=obj(S/'source.integration.choice.json')
gp=pin(B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py');hp=pin(B/'integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py')
assert gp['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and hp['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'
refs=[pin(p) for p in (C/'HDF.json',C/'MF.json',S/'HDF.json',S/'MF.json',S/'source.integration.choice.json',S/'run_w09_c19.actual_owned.py')]+[contract_ref,mode_fields_ref,gp,hp]
for mf in (C/'MF.json',S/'MF.json'):
 members=obj(mf)['members'];members=members.values() if isinstance(members,dict) else members
 refs += [verified(v) for v in members]
six={rel:verified(v) for rel,v in source_choice['sources'].items()};refs+=list(six.values())
canonical=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
assert obj(canonical[0]['path'])['revision']==365 and obj(canonical[1]['path'])['revision']==169
future=[W/'integration_codex/w09c19-consumers-1a11f30',R/'.local/w09c19-consumers-env-1a11f30']
assert all(not p.exists() for p in future)
dedup={v['path']:v for v in refs};choice=dict(schema='researchos.w09-c19-component-consumer-source-choice.v1',contract_ref=contract_ref,mode_fields_ref=mode_fields_ref,guard_ref=gp,owned_helper_ref=hp,six_source_refs=six,input_refs=list(dedup.values()),canonical_at_source_preparation=canonical,fixed_future_paths=[str(p) for p in future],actual_Git_Go_SQL_API_model_consumer=False)
cr=save('source.choice.json',choice)
p=N/'run_c19_consumers.actual_owned.py';s=p.read_text(encoding='utf-8');assert s.count('SOURCE_CHOICE_SHA_REPLACED_BEFORE_SEAL')==1 and s.count('CHOICE_BYTES=0')==1
s=s.replace('SOURCE_CHOICE_SHA_REPLACED_BEFORE_SEAL',cr['sha256']).replace('CHOICE_BYTES=0','CHOICE_BYTES='+str(cr['bytes']));ast.parse(s);p.write_bytes(s.encode())
base=S/'run_w09_c19.actual_owned.py';old=base.read_bytes();a=old.decode().splitlines(keepends=True);b=s.splitlines(keepends=True);ops=[]
for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_start=i,old_end=j,new_start=k,new_end=l,old_lines=a[i:j],new_lines=b[k:l]))
assert ''.join(x for v in ops for x in v['old_lines']).encode()==old and ''.join(x for v in ops for x in v['new_lines']).encode()==p.read_bytes()
save('source-provenance.json',dict(base_ref=pin(base),candidate_ref=pin(p),opcodes=ops,full_original_inverse=True,full_candidate_forward=True,reused_guard_ref=gp,reused_owned_helper_ref=hp,base_producer_overlay_Go_compilation_removed=True,actual_consumer_executed=False))
for v in list(dedup.values())+canonical:assert pin(v['path'])==v
save('source-input-pins.original.json',list(dedup.values())+canonical)
print(json.dumps(dict(status='CONSUMER_CALLER_SOURCE_PREPARED',caller_ref=pin(p),choice_ref=cr,static_inputs=len(dedup)+4,future_paths_absent=True)))
