"""Seal a contiguous diagnostic suffix without changing Canon or old captures."""
from pathlib import Path
import hashlib,json,os
S=Path(__file__).resolve().parent;V=S.parents[4];B=V/'receipts/W05/W05-99'
D=B/'public23_to24_composition_helper_source_codex/source-20261010-01/diagnostics'
O=S/'cp399-w09-closeout-preparation-live1260'
def pin(p):
 b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
 return pin(p)
def original(d):
 ref=d.get('original_capture_ref',d.get('raw_capture_ref'));assert pin(ref['path'])==ref
 lines=Path(ref['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
 events=[json.loads(x) for x in lines];assert events[0]['type']=='session_meta'
 cid=d.get('original_call_id',d.get('call_id'));assert events[1]['payload']['call_id']==events[2]['payload']['call_id']==cid
 audit=Path(d.get('source_audit_path',d.get('source_session_path')))
 offsets=d.get('source_line_offsets')
 if offsets is None:offsets=[0,d['source_call_range']['offset'],d['source_result_range']['offset']]
 with audit.open('rb') as f:
  for offset,line in zip(offsets,lines):f.seek(offset);assert f.readline()==line
 return ref,lines
spec=[
 (1251,S/'original1251.fixed-actual.binding.root.json','ae6906',1,1,'Publication registration rejected historical previous index hash as a current-file pin; no TP mutation.'),
 (1252,S/'original1252.fixed-actual.binding.root.json','c56032',1,1,'Precheck was invoked before CP index registration and rejected index HASH_MISMATCH; terminal Python marker absent, separate start-result proves Python1.'),
 (1253,D/'original-1253.binding.json','d0e269',1,None,'Read-only upper AGENTS.md lookup absent; no product invocation.'),
 (1254,D/'original-1254.observed.json',None,None,None,'history.search_contents schema refusal; exact observed args/result retained; raw original call ID and 3LF unavailable.'),
 (1255,D/'original-1255.observed.json',None,None,None,'history.get_schema schema refusal; exact observed args/result retained; raw original call ID and 3LF unavailable.'),
 (1256,D/'original-1256.binding.json',None,None,None,'JavaScript compiler rejected unescaped markdown backticks; no nested tool or process started.'),
 (1257,D/'tool-5f6da1.binding.json','5f6da1',1,1,'Metadata seal duplicate actual_result keyword; successful immutable prefix retained.'),
 (1258,D/'tool-80fd5e.binding.json','80fd5e',1,1,'Metadata delta uniqueness refused quoted duplicate error text; no new writes.'),
 (1259,S/'w09.literal02-derive-actual.actual-audit.root.json','bc5257',1,1,'Overall derived formal status PARTIAL yields process1; W09 C19/A06 independently VALID_ACCEPTED, 2/42. No automatic replay.')]
assert not O.exists();O.mkdir()
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='f7a2027f5fe21fe5b0524d1731eba7304327e067f0ea937489b234e07dc2983e'
assert current[2]['sha256']=='168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e'
rows=[];refs=[]
for ordinal,p,chunk,outer,py,description in spec:
 br=pin(p);d=json.loads(p.read_bytes());facts=[br]
 if ordinal in (1254,1255):
  assert d['process_started'] is False and d['call_id'] is None and d['original_3lf_capture_ref'] is None
  assert d['actual_outer_exit'] is None and d['actual_Python_exit'] is None
  ref=br;selector='observed_tool_schema_rejection='+d['toolname']+';ordinal='+str(ordinal);completeness='OBSERVED_ARGS_RESULT_ONLY_ORIGINAL_CALL_ID_3LF_UNAVAILABLE'
 else:
  ref,lines=original(d);facts.append(ref)
  if chunk:assert chunk in lines[2].decode('utf-8')
  selector='actual_host_chunk_id='+chunk if chunk else 'original_call_id='+d['call_id']
  completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_WITH_EXACT_SOURCE_OFFSETS'
  if py is not None and ordinal!=1252:assert ('PYTHON_EXIT='+str(py)) in lines[2].decode('utf-8')
  if ordinal==1252:
   extra=pin(S/'w09.maincheck-literal02-start-result.actual-audit.root.json');ed=json.loads(Path(extra['path']).read_bytes());er,el=original(ed)
   assert 'ROOT_ACTUAL_PYTHON_EXIT=1' in el[2].decode('utf-8');facts.extend([extra,er])
  if ordinal==1259:
   dr=pin(S.parents[1]/'w09_br8_actual_root/actual-20261010-01/derive-7f3a638965a04675ac21860b0e09f01e/result.json')
   dd=json.loads(Path(dr['path']).read_bytes());assert dd['integrity']=='PARTIAL' and dd['accepted_case_ids']==['A06','C19'] and dd['formal_cases_accepted']==2 and dd['bridge_CAS']=={'status':'PASS'};facts.append(dr)
 rows.append(dict(ordinal=ordinal,origin_ref=ref,origin_selector=selector,capture_binding_ref=br,description=description,capture_completeness=completeness,source_fact_refs=facts,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
 refs.extend(facts)
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1250,next_original_failure_ordinal=1260,pending=rows)
pr=save(O/'pending.root.json',pending)
allocation=save(O/'allocation.root.json',dict(schema='researchos.root-diagnostic-ordinal-allocation.v1',issued_by='codex:/root',assignments={'5f6da1':1257,'80fd5e':1258,'bc5257':1259},sealed_source_bindings_not_overwritten=True,original_1254_1255_3lf_unavailable=True,counter_reset=False))
print(json.dumps(dict(pending_ref=pr,allocation_ref=allocation,expected_current4=current,Canon_written=False),ensure_ascii=False))

