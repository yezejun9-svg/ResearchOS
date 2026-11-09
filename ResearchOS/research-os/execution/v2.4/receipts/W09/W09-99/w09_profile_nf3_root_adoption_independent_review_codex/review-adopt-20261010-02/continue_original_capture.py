"""Preserve original1112 and resolve only original1109 direct-call uniqueness."""
import hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(D/name)
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
previous=doc(D/'finite-delta-controls.json');failed=[x for x in previous['checks'] if not x['passed']]
assert previous['passed']==40 and len(failed)==1 and failed[0]['name']=='actual Root original1109 unique complete failed host preserved'
oldguard=doc(D/'independent-delta-Source-guard.closed.json');assert oldguard['closed'] and oldguard['retained_handles_count']==0 and not oldguard['errors']
capture=module(D.parent/'review-adopt-20261010-01/preserve_originals.py','AD02_original1112_capture');capture.D=D
original_save=capture.save
def corrected_save(path,value):
 if value.get('original_failure_ordinal')==1112:
  value.pop('guard_created',None);value.pop('diagnostic',None)
  value.update(original_script_ref=pin(D/'review_delta.py'),successful_and_failed_result_ref=pin(D/'finite-delta-controls.json'),successful_and_failed_progress_ref=pin(D/'checks.progress.jsonl'),finally_guard_closed_ref=pin(D/'independent-delta-Source-guard.closed.json'),
   diagnostic='Recursive host search counted later copies of Root original1109; original1112 script and false result retained; no Source or product failure inferred.')
 return original_save(path,value)
capture.save=corrected_save;original1112=capture.capture('745e8a',1112,1,1)
s=D.parent.parent/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02';h=doc(s/'HDF.json');inputs=doc(h['input_pins_ref']['path']);gm=module(inputs['refs']['guard']['path'],'AD02_finite_continuation_guard')
refs=[pin(D/x) for x in ('finite-delta-controls.json','independent-delta-Source-guard.closed.json','original-Root1109.raw.jsonl','original-Root1109.observation.json')]
guard=gm.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(refs);obs=doc(D/'original-Root1109.observation.json');raw=Path(obs['original_capture_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True)
 assert pin(obs['original_capture_ref']['path'])==obs['original_capture_ref'] and len(lines)==3
 with Path(obs['source_audit_path']).open('rb') as f:
  for offset,line in zip(obs['source_line_offsets'],lines):f.seek(offset);assert f.read(len(line))==line
 header,call,result=[json.loads(x) for x in lines]
 hosts=[x for x in capture.docs(result['payload']['output']) if x.get('chunk_id')=='b312e8'] if hasattr(capture,'docs') else [x for x in capture.documents(result['payload']['output']) if x.get('chunk_id')=='b312e8']
 assert len(hosts)==1 and hosts[0]['exit_code']==1 and 'ROOT_ACTUAL_PYTHON_EXIT=1' in hosts[0]['output']
 assert header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98' and call['payload']['call_id']==result['payload']['call_id']==obs['original_call_id']=='call_5044ab2351be4517b1c16bd3bc57efae'
 resolved=save('finite-delta-controls.resolved.json',dict(schema='researchos.w09-adoption-independent-delta-resolution.v1',prior_result_ref=pin(D/'finite-delta-controls.json'),prior40_successes_reexecuted=False,
  prior_failed_check_preserved=True,resolution='Original Root call_id plus original offsets identify the actual b312e8 invocation; later copies of the same host output are not additional invocations.',
  new_controls_passed=1,new_controls_failed=0,resolved_original1112=True,original1112_refs=original1112,original1109_ref=pin(D/'original-Root1109.observation.json'),old68_author25_Task78_Q_NF3_reexecuted=False,
  RootScope_lease_grant_written=False,live_Canon_held=0,actual_product_calls=0,execution_grant=False,formal_acceptance=False))
finally:
 closed=guard.close();guard_ref=save('continuation-Source-guard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(result_ref=resolved,guard_ref=guard_ref,original1112_refs=original1112,closed0=True,old40_reexecuted=False,actual_product_calls=0,execution_grant=False,formal_acceptance=False),ensure_ascii=False))
