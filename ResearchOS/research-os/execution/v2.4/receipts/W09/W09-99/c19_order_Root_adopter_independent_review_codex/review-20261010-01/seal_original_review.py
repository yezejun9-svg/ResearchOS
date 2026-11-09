from pathlib import Path
import hashlib,json
N=Path(__file__).parent
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v,raw=False):
 with (N/name).open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
session=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
head=None;calls={};offset=0;found=None;prefix=session.stat().st_size
with session.open('rb') as f:
 for line in f:
  here=offset;offset+=len(line)
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{})
  if v.get('type')=='session_meta' and head is None:head=(here,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('function_call','custom_tool_call'):calls[p.get('call_id')]=(here,line,v)
  if v.get('type')=='response_item' and p.get('type') in ('function_call_output','custom_tool_call_output') and 'c20be4' in str(p.get('output','')) and p.get('call_id') in calls:
   found=[head,calls[p['call_id']],(here,line,v)];break
assert found is not None
capture=save('actual-c20be4.raw.jsonl',b''.join(x[1] for x in found),True)
save('actual-c20be4.binding.json',dict(schema='researchos.independent-source-review-actual-tool-binding.v1',
 actor_id='codex:/root/attach_restore_independent_review',source_audit_path=str(session),source_prefix_size_observed=prefix,
 source_line_offsets=[x[0] for x in found],source_line_bytes=[len(x[1]) for x in found],
 original_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in found],original_call_id=found[1][2]['payload']['call_id'],
 original_capture_ref=capture,outer_exit=0,Python_exit=0,Native_exit=None,SQL_exit=None,TP_exit=None,
 Root_stage_invocations=0,root_authority=False))
closed=json.loads((N/'input-guard.closed.json').read_bytes())
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
for ref in json.loads((N/'input-pins.json').read_bytes())['refs']:assert pin(ref['path'])==ref
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
save('HDF.json',dict(schema='researchos.c19-root-adopter-independent-source-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',source_author='codex:/root',decision='REQUEST_CHANGES_SOURCE_ONLY',
 source_ref=json.loads((N/'decision.json').read_bytes())['source_ref'],manifest_ref=mf,decision_ref=pin(N/'decision.json'),
 findings_ref=pin(N/'findings.json'),controls_ref=pin(N/'finite-controls.json'),guard_closed_ref=pin(N/'input-guard.closed.json'),
 input_refs_count=9,guardclosed0=True,finite_counterexamples=6,raw_actual_binding_ref=pin(N/'actual-c20be4.binding.json'),
 CAND_independent_review_substituted=False,Main_Canon_writes=0,Native_Go_SQL_TP_Rootstage_invocations=0,
 formal_acceptance=False,parent_acceptance=False,execution_grant=False,postseal_tool_io_excluded=True,STOP=True))
assert all(pin(ref['path'])==ref for ref in members)
print(json.dumps(dict(HDF_ref=pin(N/'HDF.json'),MF_ref=mf,decision_ref=pin(N/'decision.json'),members=len(members),all_members_match=True),ensure_ascii=False))

