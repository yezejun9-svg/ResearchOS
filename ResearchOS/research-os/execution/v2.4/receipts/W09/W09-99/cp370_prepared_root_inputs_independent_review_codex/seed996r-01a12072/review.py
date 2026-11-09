"""Finite read-only Seed provenance and diagnostic qualification audit."""
import ast,hashlib,json,re,sys,types
from datetime import datetime
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
N=Path(__file__).resolve().parent
ROOT_ID='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
refs=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 assert type(r) is dict and set(r)=={'path','sha256','bytes'} and type(r['bytes']) is int and type(r['path']) is str and type(r['sha256']) is str
 assert pin(r['path'])==r;refs.append(r);return Path(r['path']).read_bytes()
def fixed(p,s,n):
 r=dict(path=str(p.resolve(strict=True)),sha256=s,bytes=n);read(r);return r
def load(r):return json.loads(read(r))
def save(name,d):
 with (N/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
qr=fixed(S/'original-diagnostic-qualifications.seed.live996.root.json','29ccebbd4fa089e2bb579b8cbbfe7253b14d5b2364f1c5f26895e7cbbe91f81d',55750)
wr=fixed(S/'seed.actual-observation-witness.live996.root.json','3ce20e7889e14d922e4f176405a5879ea3877b76cfcaea572b3722f839111b33',2639)
q,w=load(qr),load(wr);binding=load(w['capture_binding_ref']);raw=read(w['actual_host_capture_ref']);io=load(w['original_tool_io_ref']);pending=load(q['source_pending_ref'])
canon=w['canonical_refs'];cp,ow,ss,cm=[load(r) for r in canon]
origin_bytes={r['ordinal']:read(r['origin_ref']) for r in q['rows']}
lines=raw.splitlines(keepends=True);host=[json.loads(line) for line in lines]
call_input=host[1]['payload']['input']
patch_match=re.search(r'tools\.apply_patch\(("(?:\\.|[^"\\])*")\)',call_input,re.S)
patch=json.loads(patch_match.group(1));patchlines=patch.splitlines()
creator_path=Path(next(line.removeprefix('*** Add File: ') for line in patchlines if line.startswith('*** Add File: ')))
creator_bytes=('\n'.join(line[1:] for line in patchlines if line.startswith('+'))+'\n').encode()
creator_ref=pin(creator_path);read(creator_ref)
creator_text=creator_bytes.decode()
partial_name=re.search(r"partial_ref=pin\(N/'([^']+)'\)",creator_text).group(1)
partial_ref=pin(creator_path.parent/partial_name);partial=load(partial_ref)
returned=json.loads(io['result']['output'].splitlines()[0]);resume=load(returned['resume_ref'])
gp=fixed(R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py','e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
py=fixed(Path(sys.executable),'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',106328)
refs.append(pin(__file__))
gm=types.ModuleType('seed996_review_guard');gm.__file__=gp['path'];sys.modules[gm.__name__]=gm;exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
for module in tuple(sys.modules.values()):
 for attr in ('__file__','__cached__'):
  p=getattr(module,attr,None)
  if p and Path(p).is_file():refs.append(pin(p))
unique={}
for ref in list(refs):
 read(ref);key=ref['path'].casefold();assert key not in unique or unique[key]==ref;unique[key]=ref
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
checks=[];row_checks=[]
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def results_in(value):
 if isinstance(value,dict):
  if {'chunk_id','exit_code','output'}<=set(value):yield value
  for v in value.values():yield from results_in(v)
 elif isinstance(value,list):
  for v in value:yield from results_in(v)
 elif isinstance(value,str):
  try:d=json.loads(value)
  except (ValueError,TypeError):return
  if not isinstance(d,str):yield from results_in(d)
def audit_ranges():
 observed=[]
 with Path(binding['source_audit_path']).open('rb') as f:
  for offset,size in zip(binding['source_line_offsets'],binding['source_line_bytes']):
   assert type(offset) is int and type(size) is int and offset>=0 and size>0
   f.seek(offset);observed.append(f.read(size))
 return observed
guard.acquire(list(unique.values()))
try:
 check('all_four_initial_exact_refs',w['qualification_ref']==qr and w['actual_host_capture_ref']['sha256']=='60cfc44640a7c2be4229082ad8dc057c7d28bbfeb1a09ae27194846c993dd50a' and binding['original_capture_ref']==w['actual_host_capture_ref'] and w['capture_binding_ref']['sha256']=='e543d1709ec6d862627da547fe6dc9f50bb2d5df52ad387daa16535a36e93f71')
 check('Seed_only_no_activation_or_formal_grant',w['phase']=='SEED' and w['registrar_review_refs']==[] and w['formal_acceptance'] is False and w['parent_acceptance'] is False and q['formal_acceptance'] is False and q['parent_acceptance'] is False and q['counter_reset'] is False and binding['formal_authority'] is False)
 check('root_identity',w['issued_by']==q['issued_by']==binding['issued_by']=='codex:/root' and w['root_thread_id']==q['root_thread_id']==binding['root_thread_id']==ROOT_ID)
 check('actual_header_and_custom_tool_pair',len(host)==3 and host[0]['type']=='session_meta' and host[0]['payload']['id']==ROOT_ID and host[0]['payload']['session_id']==ROOT_ID and host[1]['type']==host[2]['type']=='response_item' and host[1]['payload']['type']=='custom_tool_call' and host[2]['payload']['type']=='custom_tool_call_output' and host[1]['payload']['name']=='exec' and host[1]['payload']['call_id']==host[2]['payload']['call_id']==binding['original_call_id'])
 observed_before=audit_ranges()
 check('original_three_ranges_match_exact_capture',observed_before==lines and [hashlib.sha256(b).hexdigest() for b in lines]==binding['original_line_sha256'] and [len(b) for b in lines]==binding['source_line_bytes'] and binding['source_line_offsets'][0]==0)
 check('actual_capture_time_and_prefix_binding',host[1]['timestamp']==binding['tool_call_timestamp'] and host[2]['timestamp']==binding['tool_result_timestamp'] and max(o+n for o,n in zip(binding['source_line_offsets'],binding['source_line_bytes']))<=binding['source_prefix_size_observed'])
 actual_results=[x for x in results_in(host[2]['payload']['output']) if x['chunk_id']=='a26bfb']
 check('actual_host_result_equals_original_IO',len(actual_results)==1 and actual_results[0]==io['result'])
 args_text=call_input[call_input.index('const args='):]
 cmd_match=re.search(r'cmd:("(?:\\.|[^"\\])*")',args_text,re.S)
 original_cmd=json.loads(cmd_match.group(1))
 check('actual_host_call_exact_original_command',original_cmd==io['args']['cmd'] and 'max_output_tokens":'+str(io['args']['max_output_tokens']) in args_text and '-I -S -B -X utf8' in original_cmd)
 check('creator_actual_source_bytes_preserved',creator_path.read_bytes()==creator_bytes)
 check('actual_creator_outer_and_SourcePy_zero',io['result']['exit_code']==0 and type(io['result']['exit_code']) is int and 'ROOT_SOURCE_PYTHON_EXIT=0' in io['result']['output'].splitlines() and io['actual_outer_exit']==io['actual_python_exit']==0 and all(io[k] is None for k in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit')))
 check('actual_result_returns_exact_qualification_and_pending',returned['qualification_ref']==qr and returned['pending_ref']==q['source_pending_ref'] and returned['next_original']==996 and returned['formal_delta']==0)
 check('Seed_created_within_original_call_interval',datetime.fromisoformat(host[1]['timestamp'].replace('Z','+00:00'))<=datetime.fromisoformat(q['created_utc'])<=datetime.fromisoformat(host[2]['timestamp'].replace('Z','+00:00'))<=datetime.fromisoformat(w['created_utc']))
 check('thirty_original_ordinals_complete_once',[r['ordinal'] for r in q['rows']]==list(range(966,996)) and [r['ordinal'] for r in pending['pending']]==list(range(966,996)) and q['next_original_failure_ordinal']==pending['next_original_failure_ordinal']==w['next_original_failure_ordinal']==996)
 identities=[(r['origin_ref']['path'].casefold(),r['origin_ref']['sha256'],r['origin_selector']) for r in q['rows']]
 check('unique_original_identity_ref_plus_selector',len(identities)==len(set(identities))==30)
 check('original966_969_Canon_three_fields_preserved',all({k:r[k] for k in ('ordinal','origin_ref','description')}==cp['work_in_progress']['later_diagnostics_observed_after_cutoff'][i] for i,r in enumerate(q['rows'][:4])))
 check('partial_pending995_preserved_and_extended_once',[r['ordinal'] for r in partial['pending']]==list(range(966,995)) and partial['next_original_failure_ordinal']==995 and partial['pending']==pending['pending'][:-1] and pending['pending'][-1]['ordinal']==995)
 fields=('actual_outer_exit','actual_python_exit','actual_native_exit','actual_dispatcher_exit','actual_model_exit')
 for row,prow in zip(q['rows'],pending['pending']):
  n=row['ordinal'];eq=row['exit_qualification'];text=origin_bytes[n].decode('utf-8');selector=row['origin_selector']
  check('qualification_refs_and_selector_'+str(n),eq['source_capture_ref']==row['origin_ref'] and eq['source_capture_selector']==selector and eq['diagnostic_source_ref']==q['source_pending_ref'] and eq['diagnostic_source_selector']=='pending[ordinal='+str(n)+']' and eq['unknown_is_null'] is True and eq['authority']=='ROOT_OBSERVED_DIAGNOSTIC_ONLY')
  check('typed_nullable_exits_and_unchanged_legacy_origin_'+str(n),all(row[k] is None or type(row[k]) is int for k in fields) and row['origin_ref']==prow['origin_ref'] and row['description']==prow['description'])
  check('no_invented_native_dispatcher_model_exit_'+str(n),all(row[k] is None for k in fields[2:]))
  if n>=970:check('Root_pending_numeric_and_selector_match_'+str(n),row['origin_selector']==prow['origin_selector'] and all(row[k]==prow.get(k) for k in fields))
  try:doc=json.loads(text)
  except ValueError:doc=None
  observed=[];kind='JSON_ORIGINAL_TOOL_IO'
  if n in (987,991):
   item=next(x for x in doc['observations'] if x['root_ordinal']==n)
   expected='OBSERVED_TRUNCATED_NOT_FULL' if n==987 else 'OBSERVED_NOT_FULL'
   ok=row['capture_completeness']==expected and all(row[k] is None for k in fields) and eq.get('observed_failed_child_exit')==1 and item['native_exit'] is None and item['python_exit'] is None
   kind=expected
  else:
   if doc is not None:observed=list(results_in(doc))
   else:
    kind='SOURCE_RECORDED_MARKDOWN'
    if n in (971,972,973):section=re.split(r'^## ',text,flags=re.M)[n-970]
    elif n==974:section=text.split('## Unassigned original after 973',1)[1]
    elif n in (976,977,978,979):section=next(part for part in re.split(r'^## ',text,flags=re.M) if part.startswith(str(n)+':'))
    else:section=text
    for block in re.findall(r'```json\s*(.*?)```',section,re.S):
     observed+=list(results_in(json.loads(block)))
    if n in (971,974):
     ok=all(row[k] is None for k in fields) and 'apply_patch' in section and 'verification failed' in section and 'NULL' in section
    elif not observed:
     ok=(re.search(r'outer exit\s*'+str(row['actual_outer_exit'])+r'\b',section,re.I) is not None and 'ROOT_SOURCE_PYTHON_EXIT='+str(row['actual_python_exit']) in section and selector in section)
    else:ok=True
   if observed:
    specific=[x for x in observed if selector==x['chunk_id'] or x['chunk_id'] in selector]
    selected=specific or observed
    # Duplicate nested copies represent the same original result, not new invocations.
    distinct={json.dumps(x,sort_keys=True,ensure_ascii=False):x for x in selected};selected=list(distinct.values())
    exits={x['exit_code'] for x in selected}
    ok=len(exits)==1 and row['actual_outer_exit'] in exits
    if row['actual_python_exit'] is not None:
     stdout='\n'.join(x['output'] for x in selected)
     markers=re.findall(r'(?:ROOT_SOURCE_PYTHON_EXIT|PYTHON_NATIVE_EXIT|PYTHON_EXIT)\s*=\s*(-?\d+)',stdout)
     if markers:ok=ok and int(markers[-1])==row['actual_python_exit']
     elif n==994:ok=ok and doc['exit_codes']['python']==row['actual_python_exit'] and 'KeyError' in stdout and 'python' in doc['args']['cmd']
     else:ok=False
   if n==993:ok=ok and row['capture_completeness']=='VISIBLE_TRANSCRIPTION_NOT_HOST_RAW' and 'not a raw host tool capture' in text;kind='VISIBLE_TRANSCRIPTION_NOT_HOST_RAW'
  check('original_format_numeric_evidence_'+str(n),ok,dict(kind=kind,selector=selector))
  row_checks.append(dict(ordinal=n,selector=selector,origin_ref=row['origin_ref'],evidence_kind=kind,numeric_evidence_matched=bool(ok),capture_completeness=row['capture_completeness']))
 check('same_MD_distinct_calls_preserved',q['rows'][5]['origin_ref']==q['rows'][6]['origin_ref'] and q['rows'][5]['origin_selector']!=q['rows'][6]['origin_selector'] and q['rows'][10]['origin_ref']==q['rows'][11]['origin_ref'] and q['rows'][10]['origin_selector']!=q['rows'][11]['origin_selector'])
 final995=json.loads(origin_bytes[995]);check('original995_full_failed_call_retained',final995['ordinal']==995 and final995['result']['chunk_id']=='6a22ad' and final995['result']['exit_code']==1 and 'KeyError' in final995['result']['output'] and "origin_selector" in final995['result']['output'] and 'ROOT_SOURCE_PYTHON_EXIT=1' in final995['result']['output'] and 'qualify_originals.live995.root.py' in final995['args']['cmd'])
 observed_after=audit_ranges();check('actual_Root_source_ranges_unchanged_after_review',observed_before==observed_after)
 for r in canon:read(r)
 check('four_Canon_unchanged',q['before_canonical_refs']==canon and cp['revision']==369 and ow['revision']==173)
 rr=save('prepared-root-input-checks.json',dict(schema='researchos.cp370-prepared-root-input-checks.v1',checks=checks,rows=row_checks,qualification_ref=qr,witness_ref=wr,partial_pending995_ref=partial_ref,creator_ref=creator_ref,actual_root_ranges=dict(binding_ref=w['capture_binding_ref'],whole_active_audit_log_locked=False,readback_twice=True),formal_acceptance=False,parent_acceptance=False,activation_grant=False,RootScopeCreated=False,RuntimeExecuted=False))
finally:
 closure=guard.close();gr=save('sourceguard.final.json',closure)
assert closure['closed'] is True and closure['retained_handles_count']==0 and not closure['errors']
failed=[c for c in checks if not c['passed']]
fr=save('findings.json',dict(blocking_count=len(failed),findings=failed))
dr=save('prepared-root-input-decision.json',dict(schema='researchos.cp370-prepared-root-input-decision.v1',decision='PREPARED_ROOT_SEED_INPUTS_VERIFIED_NONAUTHORITATIVE' if not failed else 'PREPARED_ROOT_SEED_INPUTS_REQUEST_CHANGES',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',qualification_ref=qr,witness_ref=wr,checks_ref=rr,findings_ref=fr,actual_SourceGuard_ref=gr,retained_handles_count=0,checks=len(checks),original_ordinals=[966,995],Root_next_original=996,phase='SEED',activation_grant=False,registrar_SourceAccepted=False,formal_acceptance=False,parent_acceptance=False,Main_or_Canon_written=False,Native_or_dispatcher_executed=False,new_original_failures=[],STOP=True,FINAL=True))
print(json.dumps(dict(decision_ref=dr,findings_ref=fr,checks_ref=rr,guard_ref=gr,checks=len(checks),failed=failed,held_refs=len(unique)),ensure_ascii=False))
