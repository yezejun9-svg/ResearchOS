from pathlib import Path
import hashlib,json,types
O=Path(__file__).parent
R=Path(r'D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
H=B/'public23_to24_handoff_source_codex/handoff-20261010-01'
Q=B/'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6'
V=B/'prepared_run_abandonment_source_v4_codex/f1cd47ca0f9544bfbe94b51a80d7c492'
N=B/'prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864'
N2=B/'prepared_abandonment_native_authority_source_codex/b1599aaf259c435db5a0a5313ab0ea65'
C=B/'integration_codex/public22-continuation-862bd0e97cad44eab8e28b37f8063f20'
F=B/'integration_codex/fresh-main23-3ef8ee61a94e4adca86a00f55a8b7a13'
inputs={}
def pin(p):
 b=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):
 b=p.read_bytes(); inputs[str(p)]=pin(p); return b
def doc(p): return json.loads(read(p))
def save(name,v):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
tiers=[]
final={}
for tier,root,key in [('PRA4',V,'source_refs'),('Native-v1-lineage',N,'candidate_files'),('Native-v2-candidate',N2,'source_refs'),('Q-schema24-revision',Q,'source_refs')]:
 h=doc(root/'HDF.json'); read(root/'MF.json')
 refs=h[key]
 if isinstance(refs,list):refs={Path(x['path']).relative_to(root/'candidate-root').as_posix():x for x in refs}
 rows=[]
 for rel,ref in refs.items():
  rel=rel.removeprefix('candidate-root/')
  src=root/'candidate-root'/rel
  actual=pin(src); assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'],rel
  read(src)
  main=R/rel
  row=dict(repo_relative_path=rel,source_ref=actual,Main_observed_ref=pin(main) if main.is_file() else None,
   expected_base_ref=ref.get('previous_ref',ref.get('base_ref')),
   declared_base_sha256=ref.get('base_sha256'))
  rows.append(row)
  if tier!='Native-v1-lineage':final[rel]=dict(tier=tier,source_ref=actual)
 tiers.append(dict(tier=tier,HDF_ref=pin(root/'HDF.json'),MF_ref=pin(root/'MF.json'),files=rows))
targets=doc(H/'integration-targets.json')
read(H/'HDF.json');read(H/'MF.json');read(H/'CONTRACT.md')
for row in targets['targets']:
 rel=row['repo_relative_path'];src=H/'candidate-root'/rel;read(src)
 assert pin(src)['sha256']==row['candidate_ref']['sha256']
 final[rel]=dict(tier='Public-handoff',source_ref=pin(src))
# This is a manifest recipe only. No candidate source is copied or executable invoked.
composition=save('composition-map.json',dict(schema='researchos.main24-composition-recipe.v1',status='METADATA_ONLY_NOT_ADOPTED',
 tiers=tiers,handoff_targets=targets['targets'],proposed_overlay_order=['preserved Main baseline','PRA4','Root-selected-reviewed Native authority (v2 candidate mapped, acceptance unresolved here)','Q-schema24-revision','Public-handoff four targets'],
 proposed_final_files=final,Root_must_resolve_Native_revision=True,source_acceptance=False,Main_writes=0))
case=doc(C/'case.closed.json')
assert pin(C/'case.closed.json')['sha256']=='2fe607aa52fe6beceaa45e2791d56f8d9d2825e074fbd4ea3ed0bcb6444bd70a'
call=next(x for x in case['calls'] if x['phase']=='backup23')
assert call['argv'][1]=='create' and call['actual_exit']==0
result=doc(Path(call['result_ref']['path']))
stdout=read(Path(call['stdout_ref']['path']))
manifest=doc(Path(case['backup23_manifest_ref']['path']))
assert json.loads(stdout)==manifest
for ref in [call['result_ref'],call['stdout_ref'],case['backup23_manifest_ref']]:
 actual=pin(Path(ref['path'])); assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
binary=Path(call['argv'][0]);bpin=pin(binary)
assert bpin['sha256']=='c6eaec594aba4ef3585314e24edbae2139395529d336c0e489e2fd200f0c90ee'
inputs[str(binary)]=bpin
assert manifest['migrations']==list(range(1,24)) and not manifest.get('purpose')
def product(ref):return dict(path=ref['path'],sha256='sha256:'+ref['sha256'],bytes=ref['bytes'])
def arg(flag):return call['argv'][call['argv'].index(flag)+1]
binding=dict(schema='researchos.public23-to24-backup-handoff.v1',source_database=arg('--db'),backup_directory=arg('--out'),
 source_program_sha256='sha256:'+bpin['sha256'],target_program_sha256=None,
 backup_manifest_sha256='sha256:'+case['backup23_manifest_ref']['sha256'],backup_manifest_bytes=case['backup23_manifest_ref']['bytes'],
 backup_id=manifest['id'],source_backup_operation='create',observed_backup_exit=call['actual_exit'],
 producer_stdout=product(call['stdout_ref']),producer_observation=product(call['result_ref']))
save('binding.actual-source.template.json',binding)
save('binding-field-map.json',dict(schema='researchos.main24-binding-field-map.v1',
 case_ref=pin(C/'case.closed.json'),source_program_ref=bpin,
 fields={'source_database':'/calls/1/argv/3','backup_directory':'/calls/1/argv/5','source_backup_operation':'/calls/1/argv/1','observed_backup_exit':'/calls/1/actual_exit','producer_stdout':'/calls/1/stdout_ref','producer_observation':'/calls/1/result_ref','backup_manifest_sha256':'/backup23_manifest_ref/sha256 (prepend sha256:)','backup_manifest_bytes':'/backup23_manifest_ref/bytes','backup_id':'referenced manifest /id','source_program_sha256':'sha256 of /calls/1/argv/0 binary; verified c6ea','target_program_sha256':'NULL until actual Root Main24 build/pin'},
 stdout_semantically_matches_manifest=True,stdout_bytes=len(stdout),manifest_bytes=case['backup23_manifest_ref']['bytes'],
 root_must_independently_qualify_original_producer=True,metadata_pins_do_not_prove_execution=True,
 future_target_program_ref=None,future_handoff_result_ref=None,future_backup24_ref=None,future_restore24_ref=None))
# Finite original audit capture, preserving the actual two tool records.
S=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
def values(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from values(x)
 elif isinstance(v,list):
  for x in v:yield from values(x)
 elif isinstance(v,str):
  try:x=json.loads(v)
  except (ValueError,TypeError):return
  if not isinstance(x,str):yield from values(x)
wanted={'83dd39':(1237,0),'d9c645':(1238,1)}
prefix=S.stat().st_size;start=max(0,prefix-32*1024*1024);calls={};found={}
with S.open('rb') as f:
 header=f.readline();f.seek(start)
 if start:f.readline()
 while f.tell()<prefix:
  off=f.tell();line=f.readline()
  if not line or f.tell()>prefix:break
  try:v=json.loads(line)
  except ValueError:continue
  payload=v.get('payload',{});typ=payload.get('type');cid=payload.get('call_id')
  if typ in ('function_call','custom_tool_call'):calls[cid]=(off,line)
  if typ not in ('function_call_output','custom_tool_call_output') or cid not in calls:continue
  for d in values(payload.get('output')):
   chunk=d.get('chunk_id')
   if chunk not in wanted or chunk in found or d.get('exit_code')!=wanted[chunk][1]:continue
   callraw=calls[cid];inp=str(json.loads(callraw[1]).get('payload',{}))
   if 'build_recipe.py' in inp:continue
   found[chunk]=(cid,callraw,(off,line),d)
diagnostics=[]
for chunk,(ordinal,outer) in wanted.items():
 cid,c,r,d=found[chunk];rows=[(0,header),c,r]
 raw=O/'diagnostic-appendix'/('original-'+str(ordinal)+'.raw.jsonl')
 raw.parent.mkdir(exist_ok=True)
 with raw.open('xb') as f:f.write(b''.join(x[1] for x in rows))
 diagnostics.append(save('diagnostic-appendix/original-'+str(ordinal)+'.binding.json',dict(Root_assigned_ordinal=ordinal,
 source_audit_path=str(S),source_prefix_size=prefix,finite_tail_start=start,source_line_offsets=[x[0] for x in rows],
 source_line_bytes=[len(x[1]) for x in rows],source_line_sha256=[hashlib.sha256(x[1]).hexdigest() for x in rows],
 original_call_id=cid,original_capture_ref=pin(raw),original_result=d,outer_exit=outer,Python_exit=None,Native_exit=None,SQL_exit=None,
 non_product_diagnostic=True,successful_prefix_preserved=True,original_not_rerun=True)))
save('input-pins.json',dict(schema='researchos.main24-recipe-inputs.v1',refs=list(inputs.values())))
print(json.dumps(dict(status='METADATA_WRITTEN',composition=composition,final_path_count=len(final),tier_counts={x['tier']:len(x['files']) for x in tiers},diagnostics=diagnostics),ensure_ascii=False))

