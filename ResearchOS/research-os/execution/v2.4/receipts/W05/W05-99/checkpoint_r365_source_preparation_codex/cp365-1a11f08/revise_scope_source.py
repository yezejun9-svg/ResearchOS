import ast,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
P=N/'checkpoint_c12_failed_archived.atomic.py'
stage1=P.read_bytes();s=stage1.decode();changes=[]
def replace(a,b):
 global s
 assert a in s,a
 changes.append(dict(before=a,after=b,count=s.count(a)));s=s.replace(a,b)
for a,b in [('range(903,925)','range(903,926)'),('==922','==923'),('=922', '=923'),('==924','==925'),('=924','=925'),('==925\n','==926\n'),('next_failure_ordinal_at_cutoff=925','next_failure_ordinal_at_cutoff=926'),('root_next_failure_ordinal_live=925','root_next_failure_ordinal_live=926'),('live_next_failure_ordinal=925','live_next_failure_ordinal=926')]:
 replace(a,b)
replace('import json,hashlib,types','import json,hashlib,types,copy')
replace('before=json.loads(old[0]);','before_ownership=json.loads(old[1]);before=json.loads(old[0]);')
replace('refs += [verify(v["origin_ref"]) for v in pending]', 'refs += [verify(facts["w09_scope_registration"]["scope_ref"])]\nrefs += [verify(v["origin_ref"]) for v in pending]')
replace(' c["note"]=facts["checkpoint_note"];return c,o', ''' scope=facts["w09_scope_registration"]
 assert scope["owner_subtask"]["owner"]=="codex:/root" and scope["owner_subtask"]["current_source_writer"] is None
 assert scope["worker"]["step_id"]=="W09-99" and scope["worker"]["slice_id"]=="C19_FIXTURE_PRODUCER" and scope["worker"]["owner"]=="codex:/root"
 assert scope["worker"]["state"]=="ROOT_REGISTERED_PENDING_ACTUAL"
 subtasks=o["card_path_bindings"]["W09-99"]["subtasks"];assert "c19_fixture_producer" not in subtasks
 assert not any(w.get("step_id")=="W09-99" and w.get("slice_id")=="C19_FIXTURE_PRODUCER" for w in c["workers"])
 subtasks["c19_fixture_producer"]=copy.deepcopy(scope["owner_subtask"])
 o.update(revision=169,updated_at=c["updated_at"],updated_by="codex:/root")
 c["workers"].append(copy.deepcopy(scope["worker"]))
 assert c["work_in_progress"]["construction_active_parents"]==["W04","W05"]
 c["work_in_progress"]["construction_active_parents"]=["W05","W09"]
 inverse=copy.deepcopy(o);del inverse["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"]
 for k in ("revision","updated_at","updated_by"):inverse[k]=before_ownership[k]
 assert inverse==before_ownership and (json.dumps(inverse,ensure_ascii=False,indent=2)+"\\n").encode()==old[1]
 c["note"]=facts["checkpoint_note"];return c,o''')
replace('assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==365','assert json.loads(ow.read_bytes())["revision"]==169 and [p.read_bytes() for p in others]==other_bytes and json.loads(cp.read_bytes())["revision"]==365')
replace('ownership_revision=168','ownership_revision=169')
replace('W09r2_Source="PENDING_INDEPENDENT_SOURCE_REVIEW_NO_ACTUAL_SCOPE"','W09r2_Source="INDEPENDENTLY_ACCEPTED_573_CHECKS",W09C19_scope="ROOT_REGISTERED_PENDING_EXPLICIT_FOUR_CANONICAL_VECTOR_AND_ACTUAL",construction_active_parents=["W05","W09"]')
ast.parse(s)
assert 'registered_after"]==923' in s and 'next_failure_ordinal"]==926' in s
assert 'highest_observed_ordinal"]==925' in s
with (N/'writer.stage1.original.py').open('xb') as f:f.write(stage1)
P.write_bytes(s.encode())
base=json.loads((N/'writer-source-provenance.json').read_bytes())['base_ref']
original=Path(base['path']).read_bytes()
ops=[];a=original.decode().splitlines(keepends=True);b=s.splitlines(keepends=True)
for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():ops.append(dict(op=op,old_start=i,old_end=j,new_start=k,new_end=l,old_lines=a[i:j],new_lines=b[k:l]))
assert ''.join(x for v in ops for x in v['old_lines']).encode()==original
assert ''.join(x for v in ops for x in v['new_lines']).encode()==P.read_bytes()
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
with (N/'writer-source-provenance.final.json').open('xb') as f:f.write((json.dumps(dict(base_ref=base,new_ref=pin(P),stage1_ref=pin(N/'writer.stage1.original.py'),scope_and_925_changes=changes,opcodes=ops,whole_original_byte_inverse=True,whole_candidate_byte_forward=True,writer_executed=False),ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(pin(P)))
