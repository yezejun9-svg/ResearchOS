from pathlib import Path
import json,hashlib,types
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def values(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from values(x)
 elif isinstance(v,list):
  for x in v:yield from values(x)
 elif isinstance(v,str):
  try:x=json.loads(v)
  except (ValueError,TypeError):
   for line in v.splitlines():
    if line.startswith('{') or line.startswith('['):
     try:x=json.loads(line)
     except ValueError:continue
     yield from values(x)
   return
  if not isinstance(x,str):yield from values(x)
S=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
wanted={'d9c645':(1238,1,None),'84c5b7':(1239,0,1)}
prefix=S.stat().st_size;start=max(0,prefix-16*1024*1024);calls={};found={}
with S.open('rb') as f:
 h=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:v=json.loads(line)
  except ValueError:continue
  p=v.get('payload',{});t=p.get('type');cid=p.get('call_id')
  if t in ('function_call','custom_tool_call'):calls[cid]=(off,line)
  if t not in ('function_call_output','custom_tool_call_output') or cid not in calls:continue
  for d in values(p.get('output')):
   chunk=d.get('chunk_id')
   if chunk not in wanted or chunk in found or d.get('exit_code')!=wanted[chunk][1]:continue
   inp=str(json.loads(calls[cid][1]).get('payload',{}))
   if 'seal_recipe.py' in inp:continue
   found[chunk]=(cid,calls[cid],(off,line),d)
for chunk,(ordinal,outer,py) in wanted.items():
 cid,c,r,d=found[chunk];rows=[(0,h),c,r]
 raw=O/'diagnostic-appendix'/('original-'+str(ordinal)+'.raw.jsonl')
 with raw.open('xb') as f:f.write(b''.join(x[1] for x in rows))
 save('diagnostic-appendix/original-'+str(ordinal)+'.binding.json',dict(Root_assigned_ordinal=ordinal,source_audit_path=str(S),
 source_prefix_size=prefix,finite_tail_start=start,source_line_offsets=[x[0] for x in rows],source_line_bytes=[len(x[1]) for x in rows],
 source_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],original_call_id=cid,original_capture_ref=pin(raw),
 original_result=d,outer_exit=outer,Python_exit=py,Native_exit=None,SQL_exit=None,non_product_diagnostic=True,
 successful_prefix_preserved=True,original_not_rerun=True,
 original_outer_tool_truncation_notice_preserved=(ordinal==1238),selected_inner_tool_result_complete=True))
comp=json.loads((O/'composition-map.json').read_bytes()); fmap=json.loads((O/'binding-field-map.json').read_bytes())
refs={}
def add(ref):
 p=Path(ref['path']);actual=pin(p)
 assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'],str(p)
 refs[str(p)]=actual
for tier in comp['tiers']:
 add(tier['HDF_ref']);add(tier['MF_ref'])
 for row in tier['files']:add(row['source_ref'])
for row in comp['handoff_targets']:add(row['candidate_ref'])
add(fmap['case_ref']);add(fmap['source_program_ref'])
bind=json.loads((O/'binding.actual-source.template.json').read_bytes())
for k in ('producer_stdout','producer_observation'):
 r=dict(bind[k]);r['sha256']=r['sha256'].removeprefix('sha256:');add(r)
manifest=Path(bind['backup_directory'])/'manifest.json'
add(dict(path=str(manifest),sha256=bind['backup_manifest_sha256'].removeprefix('sha256:'),bytes=bind['backup_manifest_bytes']))
H=B/'public23_to24_handoff_source_codex/handoff-20261010-01'
for n in ('HDF.json','MF.json','CONTRACT.md','integration-targets.json'):add(pin(H/n))
frozen=Path(fmap['source_program_ref']['path']).parent/'frozen_main'
frozen_sources=[]
for rel in ('migrations/sqlite','spec/v2.0/contracts'):
 for p in sorted((frozen/rel).rglob('*')):
  if p.is_file():frozen_sources.append(pin(p))
# Frozen release is a source-root candidate; no executor or DB invoked.
save('preserved-main23-release-inputs.json',dict(root=str(frozen),refs=frozen_sources,
 status='READONLY_INVENTORY_LOCATED_ROOT_QUALIFICATION_REQUIRED',inventories_are_not_binary_execution_proof=True))
for ref in frozen_sources:add(ref)
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
graw=G.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
add(pin(G))
mod=types.ModuleType('main24_recipe_read_guard');exec(compile(graw,str(G),'exec'),mod.__dict__)
guard=mod.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=256*1024*1024)
guard.acquire(list(refs.values()))
try:
 assert len(comp['handoff_targets'])==4 and len(comp['proposed_final_files'])==40
 guide=(O/'ROOT_INTEGRATION_GUIDE.md').read_text(encoding='utf-8')
 assert all(x['candidate_ref']['sha256'] in guide for x in comp['handoff_targets'])
 assert bind['target_program_sha256'] is None
 assert json.loads(Path(bind['producer_stdout']['path']).read_bytes())==json.loads(manifest.read_bytes())
 assert len([p for p in (frozen/'migrations/sqlite').glob('[0-9][0-9][0-9][0-9]_*.sql')])==23
 for ordinal,outer,py in ((1237,0,None),(1238,1,None),(1239,0,1)):
  b=json.loads((O/'diagnostic-appendix'/('original-'+str(ordinal)+'.binding.json')).read_bytes())
  assert b['outer_exit']==outer and b['Python_exit']==py
  raw=Path(b['original_capture_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True)
  assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
  assert [hashlib.sha256(x).hexdigest() for x in lines]==b['source_line_sha256']
 controls=save('metadata-checks.json',dict(status='METADATA_ONLY_CHECKS_PASSED',four_handoff_targets=4,conditional_final_paths=40,
 candidate_source_inputs_held=len(refs),frozen_source_numbered_migrations=23,source_program_pin_verified=True,
 stdout_and_manifest_semantic_equality=True,target_program_unknown=True,original_diagnostic_count=3,
 Go_SQL_Native_model_Rootstage_calls=0,Main_Canon_writes=0,old_successes_replayed=False,
 input_main_observations_are_time_of_read_only=True,source_acceptance=False,formal_acceptance=False))
finally:closed=guard.close()
guardref=save('source-guard.closed.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
save('input-pins.json',dict(schema='researchos.main24-recipe-inputs.v1',refs=list(refs.values())))
members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.main24-recipe-manifest.v1',members=members,
 excludes=['MF.json','HDF.json','postseal-tool-io.json'],source_only=True))
hdf=save('HDF.json',dict(schema='researchos.main24-root-integration-preparation.v1',actor_id='codex:/root/attach_restore_independent_review',
 status='METADATA_ONLY_PENDING_ROOT_REVIEW',manifest_ref=mf,guide_ref=pin(O/'ROOT_INTEGRATION_GUIDE.md'),
 composition_ref=pin(O/'composition-map.json'),binding_template_ref=pin(O/'binding.actual-source.template.json'),
 field_map_ref=pin(O/'binding-field-map.json'),frozen_source23_ref=pin(O/'preserved-main23-release-inputs.json'),
 checks_ref=controls,source_guard_ref=guardref,diagnostic_binding_refs=[pin(O/'diagnostic-appendix'/('original-'+str(x)+'.binding.json')) for x in (1237,1238,1239)],
 Main_writes=0,Canon_writes=0,Go_SQL_Native_model_Rootstage_calls=0,Main24_executed=False,
 Native_v2_selection_requires_Root_existing_acceptance=True,source_acceptance=False,formal_acceptance=False,
 future_target_program_ref=None,future_Main24_result_ref=None,execution_grant=False,STOP=True))
print(json.dumps(dict(status='SEALED_METADATA_ONLY',HDF=hdf,MF=mf,checks=controls,source_guard=guardref),ensure_ascii=False))

