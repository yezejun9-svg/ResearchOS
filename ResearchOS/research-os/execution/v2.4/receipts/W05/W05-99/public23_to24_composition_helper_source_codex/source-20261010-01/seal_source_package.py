import ast,hashlib,json,os
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path(r'D:/作品集/ResearchOS/research-os')
M=O.parent.parent/'public23_to24_main_merge_preparation_codex/prepare-20261010-01'
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=sha(b),bytes=len(b))
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 assert p.read_bytes()==b
 return pin(p)
def doc(p,v):return save(p,(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
helper=pin(O/'compose_main24.source.py')
controls=json.loads((O/'new-pure-controls.json').read_bytes())
assert controls['source_ref']==helper and controls['status']=='PASS'
tree=ast.parse((O/'compose_main24.source.py').read_bytes())
paths=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PATHS' for t in n.targets))
merge=pin(M/'file-merge-map.json')
assert merge['sha256']=='44471d2f2fcb80ee96b8fd2515ea3decba7e258433c4ba3993c619676a7cb61c'
doc(O/'request.template.json',dict(schema='researchos.main24-compose-request.v1',actor_id='codex:/root',repo_root=str(R),project_identity_ref=pin(R/'execution/project_identity.json'),source_helper_ref=helper,merge_map_ref=merge,native_revision='b1599aaf259c435db5a0a5313ab0ea65',output_directory=None))
doc(O/'grant.template.json',dict(schema='researchos.root-main24-composition-grant.v1',issued_by='codex:/root',project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',operation_id=None,source_helper_ref=helper,prepared_ref=None,independent_source_review_ref=None,root_authorization_observation_ref=None,target_paths=list(paths),issued_at=None,expires_at=None))
doc(O/'future-result.template.json',dict(source_helper_ref=helper,request_ref=None,prepared_ref=None,grant_ref=None,TargetProgram=None,apply_result_ref=None,build_result_ref=None,test_result_ref=None,independent_actual_review_ref=None,formal_acceptance=False,Main_applied=False,Canon_written=False))
contract='''# Main24 Root composition helper
Status: SOURCE_AUTHORED_PENDING_INDEPENDENT_REVIEW. This package neither grants execution nor accepts Source or Main.

## Scope and external authority
Fixed project aede0678-7308-43dc-b9f2-cfe3d90cfdfb, repository D:/作品集/ResearchOS/research-os, Root-selected Native v2 b1599aaf259c435db5a0a5313ab0ea65. Ordered forty targets and final layers derive from the exact pinned merge map. Ten existing targets receive pinned byte increments; thirty additions require absence. Drift refuses before Main writes. Root keeps other Main writers quiescent. This author has not run prepare/apply or accepted Source.

## Preparation and grant
Obtain an actual independent Source review of this exact helper SHA and contract. Any source change requires a new revision and review. Root materializes request.template.json in its own new evidence directory, filling output_directory with a never-used W05-99/integration_codex/main24-compose-<32 lowercase hex> path. Pin that completed request.
Run with the known Python 3.14 executable:
python -I -S -B -X utf8 <helper> prepare --request <request.json> --request-sha256 <sha> --request-bytes <n>
Capture actual argv, result and separate outer/Python exits. Prepare writes only its new evidence output. It archives ten complete raw existing files, forty desired byte streams, inverse operations, prepared.json and prepare journal, with all-target preflight before and after archival. Inspect these concrete outputs before issuing a grant.

Only Root fills grant.template.json after validating actual independent Source-review provenance/verdict and Root authorization. Pin those exact evidence records. Actor strings and hashes establish content binding, not actor authentication; Root validates external authority, which the helper cannot discover from conversation. Use a fresh 32-lowercase-hex operation_id and explicit-timezone issued/expires timestamps at most one hour apart. All future grant, TargetProgram and execution/result fields remain null in author templates.
Run only in the authorized Root action:
python -I -S -B -X utf8 <helper> apply --prepared <prepared.json> --prepared-sha256 <sha> --prepared-bytes <n> --grant <grant.json> --grant-sha256 <sha> --grant-bytes <n>

## Apply mechanics
Hold immutable Source/request/identity/grant/archive refs using the pinned e75ae3 SourceReadGuard (256 MiB/file; 2 GiB total). Serialize helper calls using root-main24-composition.lock beside Source. Open all ten existing target handles READ|WRITE with FILE_SHARE_READ and OPEN_EXISTING, without truncation, before the full forty-target preflight. Conflicting write/delete sharing refuses. Additions use CREATE_NEW semantics. Check final handle paths and single-link status. Recompute each increment from pinned current raw bytes, preserving untouched spans, bind to selected Source, and read back exact bytes. Save intent and per-write receipts.

## Partial failure and inverse
Forty writes are not one filesystem transaction. Stop on any error, preserve partial state, attempted target, completed receipts, primary exception and secondary cleanup/persistence failures. No automatic retry, rollback or delete. Complete original archives and inverse byte operations support a separately authorized Root repair; addition inverses describe removal only after separate Root authorization. A failing new-file operation may leave an empty/partial file; existing writes may be partial. Inspect actual files and journal; do not retry with a fresh operation_id to conceal previous partial work. Existing operation output refuses retry. Abrupt process termination may prevent failure.json; retain intent, raw archives and actual outer tool evidence.
Source-guard closure errors remain failures even after all writes. Validation errors before apply's guarded try print the actual Python exception before any Main mutation. Root retains actual tool failures; helper artifacts never replace tool audit.

## Post-apply and evidence limits
Success means APPLIED_PENDING_BUILD_TEST_AND_INDEPENDENT_REVIEW. No Go, gofmt, build, test, SQL, runtime/native program or product case is invoked. Root separately performs authorized formatting/testing and binds any resultant byte changes and actual results to independent review. No Canon/SS/Owner/Spec/formal-acceptance mutation occurs.
Fourteen new synthetic pure-byte/JSON and helper-contract checks passed. Only Refusal, need, sha, decode and apply_edits AST definitions were extracted into an isolated memory environment. No helper module import, prepare/apply, Windows handles or SourceReadGuard execution occurred. Prior successful Source controls were not replayed. These results are source-level evidence only.
Original1253 has raw actual three-line call/output evidence. Tool schema rejections1254/1255 and the later JS compile rejection are retained with exact observed arguments/results; unavailable raw call ids/three-line captures are explicitly unverified and exits remain null.
'''
save(O/'ROOT-EXECUTION-CONTRACT.md',contract.encode())
session=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl')
with session.open('rb') as f:
 header=f.readline();size=os.fstat(f.fileno()).st_size
 start=max(0,size-4*1024*1024);f.seek(start)
 if start:f.readline()
 entries=[]
 while f.tell()<size:
  offset=f.tell();raw=f.readline()
  if not raw:break
  try:v=json.loads(raw)
  except ValueError:continue
  entries.append((offset,raw,v))
def texts(payload):
 x=payload.get('output',[])
 return x if isinstance(x,str) else '\n'.join(i.get('text','') for i in x if isinstance(i,dict))
outputs=[x for x in entries if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type')=='custom_tool_call_output' and '"chunk_id":"d0e269"' in texts(x[2]['payload'])]
assert len(outputs)==1
def capture(result,stem):
 callid=result[2]['payload']['call_id']
 calls=[x for x in entries if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type')=='custom_tool_call' and x[2]['payload'].get('call_id')==callid]
 assert len(calls)==1
 call=calls[0]
 rawref=save(O/('diagnostics/'+stem+'.actual-3lf.jsonl'),header+call[1]+result[1])
 return dict(call_id=callid,actual_call=call[2]['payload'],actual_result=result[2]['payload'],raw_capture_ref=rawref,source_session_path=str(session),source_snapshot_bytes=size,source_session_header_sha256=sha(header),source_call_range=dict(offset=call[0],bytes=len(call[1]),sha256=sha(call[1])),source_result_range=dict(offset=result[0],bytes=len(result[1]),sha256=sha(result[1])))
d=capture(outputs[0],'original-1253')
doc(O/'diagnostics/original-1253.binding.json',dict(schema='researchos.actual-tool-diagnostic-binding.v1',original_ordinal=1253,chunk_id='d0e269',actual_outer_exit=1,actual_Python_exit=None,actual_Native_exit=None,actual_SQL_exit=None,reason='Read-only missing upper AGENTS.md; no replay, writes or product call.',**d))
argses=[{'query':'Root可审','role':'user','window_id':'01a123d5-fe70-71c3-b34e-76cf807f73d6','max_matches':3,'limit':3},{'query':'Root可审','window_id':'01a123d5-fe70-71c3-b34e-76cf807f73d6','max_matches':4}]
for ordinal,args in zip((1254,1255),argses):
 doc(O/('diagnostics/original-'+str(ordinal)+'.observed.json'),dict(schema='researchos.observed-tool-schema-rejection.v1',original_ordinal=ordinal,toolname='history.search_contents',actual_args=args,actual_result='Unexpected argument. Use only fields defined in the tool schema.',call_id=None,actual_outer_exit=None,actual_Python_exit=None,actual_Native_exit=None,actual_SQL_exit=None,process_started=False,original_3lf_capture_ref=None,original_raw_capture_status='UNAVAILABLE_IN_BOUNDED_SESSION_TAIL',provenance='Exact observed current-turn arguments and returned text; no invented call id, original record, offsets or process exit. Rejected tool supplied no data.'))
js=[x for x in entries if x[2].get('type')=='response_item' and x[2].get('payload',{}).get('type')=='custom_tool_call_output' and "SyntaxError: Unexpected identifier 'aede0678'" in texts(x[2]['payload'])]
if len(js)==1:
 jscapture=capture(js[0],'js-compile-rejection')
else:jscapture=dict(call_id=None,raw_capture_ref=None,original_raw_capture_status='UNAVAILABLE_IN_BOUNDED_SESSION_TAIL')
doc(O/'diagnostics/original-1256.binding.json',dict(schema='researchos.observed-js-tool-rejection.v1',original_ordinal=1256,toolname='functions.exec',actual_result="Script failed\nWall time 0.0 seconds\nOutput:\nScript error:\nSyntaxError: Unexpected identifier 'aede0678'",actual_outer_exit=None,actual_Python_exit=None,actual_Native_exit=None,actual_SQL_exit=None,process_started=False,mutations_started=False,reason='Unescaped markdown backtick inside JS template literal; no nested call executed; seal draft rewritten without executing any successful checks again.',**jscapture))
hdf=dict(schema='researchos.main24-composition-helper-handoff.v1',status='SOURCE_AUTHORED_PENDING_INDEPENDENT_REVIEW',author='codex:/root/attach_restore_independent_review',source_helper_ref=helper,merge_map_ref=merge,contract_ref=pin(O/'ROOT-EXECUTION-CONTRACT.md'),request_template_ref=pin(O/'request.template.json'),grant_template_ref=pin(O/'grant.template.json'),future_result_template_ref=pin(O/'future-result.template.json'),new_pure_controls_ref=pin(O/'new-pure-controls.json'),targets=40,existing_increment_targets=10,new_absent_only_targets=30,selected_native_revision='b1599aaf259c435db5a0a5313ab0ea65',prepare_executed=False,apply_executed=False,Main_Canon_writes=0,Go_SQL_Native_product_calls=0,prior_successful_Source_controls_replayed=0,execution_grant_ref=None,TargetProgram=None,build_result_ref=None,test_result_ref=None,formal_acceptance=False,diagnostic_refs=[pin(p) for p in sorted((O/'diagnostics').glob('*.json'))],manifest_exclusions=['MF.json','postseal-tool-io.json'],required_next='Root independent Source review; Root metadata preparation and explicit qualified grant before apply.')
h=doc(O/'HDF.json',hdf)
members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ('MF.json','postseal-tool-io.json')]
mf=doc(O/'MF.json',dict(schema='researchos.source-package-manifest.v1',status='SEALED_SOURCE_ONLY',HDF_ref=h,files=members,exclusions=['MF.json','postseal-tool-io.json'],self_hash_not_embedded=True))
print(json.dumps(dict(HDF_ref=h,MF_ref=mf,source_helper_ref=helper,new_pure_controls_ref=pin(O/'new-pure-controls.json'),contract_ref=pin(O/'ROOT-EXECUTION-CONTRACT.md'),diagnostics=hdf['diagnostic_refs'],status=hdf['status']),ensure_ascii=True))

