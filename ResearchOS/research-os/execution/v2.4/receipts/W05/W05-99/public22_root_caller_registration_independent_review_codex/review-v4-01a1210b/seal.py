"""Seal real review hostpair and test published review schema; no Root fact issued."""
import copy
import json
from pathlib import Path
import runpy
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'review.py'),run_name='seal_definitions');pin,read,save=x['pin'],x['read'],x['save']
previous=x['mod'](x['R']/'execution/v2.4/receipts/W09/W09-99/cp370_actual_registration_independent_review_codex/actualr4-01a120ab/review.py');previous.N=N
audit=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
cap=previous.capture(audit,40928429,'26a701','review-complete');assert cap['result']['exit_code']==0
lines=cap['result']['output'].splitlines();published=json.loads(lines[0]);assert lines[-1]=='ROOT_SOURCE_PYTHON_EXIT=0'
refs=[pin(N/k) for k in ('HDF.json','MF.json','source-decision.json','findings.json','independent-controls.json','sourceguard.closed.json','review.py','seal.py')]
for k,n in [('HDF','HDF.json'),('MF','MF.json'),('decision','source-decision.json'),('findings','findings.json')]:assert published[k]==pin(N/n)
refs.extend((cap['cap_ref'],cap['binding_ref']))
refs.extend(read(N/'MF.json')['source_input_refs'])
refs=list({r['path'].casefold():r for r in refs}.values())
guardmod=x['mod'](x['B']/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py');guard=guardmod.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
try:
 binding=read(cap['binding_ref']['path']);raw=Path(cap['cap_ref']['path']).read_bytes().splitlines(keepends=True)
 assert len(raw)==3
 with audit.open('rb') as f:
  for offset,b in zip(binding['source_line_offsets'],raw):f.seek(offset);assert f.read(len(b))==b
 d=read(N/'source-decision.json');gclosed=read(N/'sourceguard.closed.json');checks=read(N/'independent-controls.json')
 assert all(pin(r['path'])==r for r in d['current_canonical_refs'])
 assert gclosed['closed'] and gclosed['retained_handles_count']==0 and gclosed['errors']==[]
 assert all(z['passed'] for z in checks['checks'])
 sourcehdf=read(x['S']/'HDF.json');g=x['mod'](sourcehdf['registrar_ref']['path']);c=x['mod'](sourcehdf['caller_ref']['path'])
 # ONLY the not-yet-issued Root witness is an in-memory fixture. Every Source,
 # reviewer HDF/MF/decision/member is the real immutable file and real hash.
 witnessref=dict(path=str(g.ROOT_INPUT/'__finite_source_shape_witness_not_issued__.json'),sha256='f'*64,bytes=1)
 witness=dict(issued_by='codex:/root',review_hdf_ref=published['HDF'],review_mf_ref=published['MF'],review_decision_ref=published['decision'],original_capture_ref=cap['cap_ref'],original_call_id=cap['call']['payload']['call_id'])
 request=dict(source_hdf_ref=pin(x['S']/'HDF.json'),source_mf_ref=sourcehdf['manifest_ref'],review_hdf_ref=published['HDF'],review_mf_ref=published['MF'],review_decision_ref=published['decision'],review_hostpair_binding_ref=witnessref)
 scope=dict(source_hdf_ref=sourcehdf['runner_review_ref'],caller_hdf_ref=request['source_hdf_ref'],caller_mf_ref=request['source_mf_ref'],caller_review_ref=published['decision'],caller_review_hdf_ref=published['HDF'],caller_review_mf_ref=published['MF'],root_review_hostpair_binding_ref=witnessref,caller_reviewer=x['ACTOR'],calling_contract_ref=sourcehdf['contract_ref'],registrar_ref=sourcehdf['registrar_ref'])
 oldread,oldexact,olddoc=g.read,g.exact,c.doc
 try:
  g.exact=lambda ref:ref if ref==witnessref else oldexact(ref)
  g.read=lambda ref:copy.deepcopy(witness) if ref==witnessref else oldread(ref)
  c.doc=lambda ref:copy.deepcopy(witness) if ref==witnessref else olddoc(ref)
  result=g.verify_source(request)
  assert result[0]==sourcehdf and result[1]==request['source_mf_ref'] and result[2]==published['decision'] and result[3]==x['ACTOR']
  result2=c.source_and_review(scope)
  assert len(result2)==5 and result2[0]==read(sourcehdf['runner_review_ref']['path'])
  g.read=lambda ref:dict(d,actor_id=g.AUTHOR) if ref==published['decision'] else (copy.deepcopy(witness) if ref==witnessref else oldread(ref))
  try:g.verify_source(request)
  except ValueError as e:assert str(e)=='NONAUTHOR_REVIEW_NOT_BOUND'
  else:raise AssertionError('Source author accepted as independent reviewer')
 finally:g.read,g.exact,c.doc=oldread,oldexact,olddoc
 for r in refs:assert pin(r['path'])==r
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('seal-sourceguard.closed.json',closed)
shape=save('published-schema-check.json',dict(scope='PURE_REVIEW_SHAPE_VALIDATION_ONLY',real_review_HDF_MF_decision_and_source_pins=True,registrar_verify_source_shape_passed=True,caller_source_and_review_shape_passed=True,Source_author_as_reviewer_rejected=True,Root_witness_in_memory_synthetic=True,Root_witness_issued=False,Root_registration_executed=False,execution_grant=False,formal_acceptance=False))
sr=save('complete-hostpair-seal.json',dict(decision='ACCEPTED_SOURCE_ONLY',review_refs={k:published[k] for k in ('HDF','MF','decision','findings')},actual_review_host_capture_ref=cap['cap_ref'],actual_review_host_binding_ref=cap['binding_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,source_guard_ref=gr,published_schema_check_ref=shape,checks=checks['count'],read_refs_held=d['held_read_refs'],blocking_findings=0,new_original_failures=[],Source_pending_cutoff=1018,Root_next_observed=1020,canonical_unchanged=True,formal_acceptance=False,execution_grant=False))
print(json.dumps(dict(seal=sr,HDF=published['HDF'],MF=published['MF'],decision=published['decision'],host_capture=cap['cap_ref'],host_binding=cap['binding_ref'],schema_check=shape),ensure_ascii=False),flush=True)
