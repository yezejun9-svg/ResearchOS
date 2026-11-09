from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
P=R.parent
T=P.parent
A=T/'product-v1-cli-same-host-caps-prepare-revision-02-20261104'
O=T/'product-v1-cli-same-host-caps-prepare-20261104'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
 p=R/name;assert not p.exists(),str(p)
 p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(A/'MANIFEST.json')=='997e27aba6fd76ed2ca26f1e18f0411f28261d07a020b5b7eed2a6138002e1ad'
assert sha(A/'same-host-caps.mjs')=='52641e53bef0d8d0b35835644e6a9270e68dc806ea77276403a14b07377c3877'
for directory,pin in [(A,'997e27aba6fd76ed2ca26f1e18f0411f28261d07a020b5b7eed2a6138002e1ad'),(O,'b1d828c537a3dced70e5b11e76a133be68a3553eb111939a38d0bad02e18332e')]:
 assert sha(directory/'MANIFEST.json')==pin
 m=json.loads((directory/'MANIFEST.json').read_text(encoding='utf-8-sig'))
 for row in m['files']:
  p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
result=json.loads((R/'result.json').read_text());assert result['exit_code']==0
assert sha(R/'stdout.raw')==result['stdout_sha256'] and sha(R/'stderr.raw')==result['stderr_sha256']
assert json.loads((R/'stdout.raw').read_text())['passed']==7
old=json.loads((P/'result.json').read_text());assert old['exit_code']==0
assert sha(P/'stdout.raw')=='acbf960c3e4564ce1c4f285e98bd822f2860b22b5bfd0e844c69fcf02812aa32'
put('report.json',{
 'schema':'researchos.independent-source-review.v1','decision':'APPROVED_SOURCE_FIXTURE_ONLY','formal_increment':0,'product_increment':0,'pending_blockers':[],
 'source_sha256':{'same-host-caps.mjs':sha(A/'same-host-caps.mjs')},
 'manifest_ref':str(A/'MANIFEST.json'),'manifest_sha256':sha(A/'MANIFEST.json'),'freeze_sha256':sha(A/'MANIFEST.json'),'freeze_basis':'construction_frozen true in the pinned MANIFEST; source_modification_permitted false',
 'scope_ref':str(A/'scope.template.json'),'scope_template_sha256':sha(A/'scope.template.json'),'runtime_authorized':False,
 'manifest_files_verified':9,'old_manifest_files_verified':6,'no_drift':True,
 'findings':[
  {'severity':'P2','status':'RESOLVED_IN_REVISION02','origin_key':'same-host-cli-caps-secret-output-persistence','old_ref':'same-host-caps.mjs freeze01 cli-streams write before refs guard','evidence':str(P/'stdout.raw'),'evidence_sha256':sha(P/'stdout.raw'),'result':'Synthetic credential_value was persisted in freeze01 stdout_text before rejection. Revision02 persists counts and SHA-256 only; fixed public projection follows checks; client_secret/camel variants are refused. Original evidence and source remain unchanged. No real CLI leakage occurred in this review.'},
  {'ref':'same-host-caps.mjs:45','result':'Actual parsePublicCaps errors are fixed input-independent codes. Unknown fields and reason-code free text are excluded from persisted output; only codex, boolean can_submit and reason count are projected.'},
  {'ref':'same-host-caps.mjs:38','result':'Discovery code is byte-identical. Actual Core DTO has four keys url/pid/data_dir/host_instance_id; all four are accepted, optional started_at remains compatible. PID/Host/data-root identity mismatches or extra private metadata are refused.'},
  {'ref':'same-host-caps.mjs run','result':'Scope requires fixed build05/CLI hashes, one caps invocation, zero task/model/retry budgets, fresh C data and owned Root supervision. Fixed spawn argv is only harness caps. It does not read/copy auth files, run the imported R04 flow or call chooser/project/submit.'},
  {'ref':'same-host-caps.mjs finally','result':'CLI close and app.close must be observed; otherwise status is blocked. External original Root Job exit accounting remains explicit. No arbitrary PID kill/retry or network/pipe server-PID identity claim.'}
 ],
 'independent_checks':{'case_groups':7,'exit_code':0,'ref':str(R/'result.json'),'command_ref':str(R/'command.json'),'stdout_ref':str(R/'stdout.raw'),'stdout_sha256':sha(R/'stdout.raw'),'stderr_ref':str(R/'stderr.raw'),'stderr_sha256':sha(R/'stderr.raw'),'raw_tool_chunk':'7d2779','test_sha256':sha(R/'pure.mjs'),'method':'VM-extracted actual parsePublicCaps and actual output write fragment only; no imports or wrapper entry execution'},
 'reused_evidence':{'old_pure_ref':str(P/'result.json'),'old_pure_exit_code':0,'old_pure_raw_chunk':'758518','reason':'Actual four-key and optional-five-key discovery, foreign PID/Host/root/private-field/alias negatives and the original secret-log counterexample. publicDiscovery bytes unchanged.'},
 'second_static_reader':{'agent':'prompt_flow_review','result':'No additional P1/P2. Raw streams no longer persisted; parse errors input-independent; secret variants refused and unknown free text excluded. Public summary is not a complete rev2 DTO or raw CLI response.','runtime_or_test_execution':0},
 'qualification_limits':[
  'Review executed no SDK, Electron, CLI, native process, model, auth file or DB access. No login, capability value, real same-Host CLI journey or actual Windows enforcement is qualified.',
  'READY listener registration race remains fail-closed timeout, not proof of discovery absence. A separate Root exact-source scope is required to perform the one caps observation.',
  'Host identity basis is app-internal original-Core report plus fixed explicit discovery and existing native bootstrap checks; no independent network/pipe PID interception was performed.',
  'Summary intentionally keeps reason-code count only, not free-form login/provider descriptions. It cannot establish account/login status or replace full task flow qualification.',
  'Any spawn/close uncertainty or outer Job nonzero prevents runtime success. The immutable old failure, old snapshots and diagnostic counts must be retained.'
 ],
 'diagnostic_events':[
  {'origin_key':'same-host-cli-caps-secret-output-persistence','classification':'SOURCE_SECURITY_P2_FOUND_AND_FIXED_BEFORE_RUNTIME','counterexample_ref':str(P/'stdout.raw'),'counterexample_sha256':sha(P/'stdout.raw'),'status':'RESOLVED_SOURCE_FIXTURE_ONLY','real_cli_calls':0},
  {'origin_key':'same-host-cli-caps-revision02-patch-context','classification':'C_PATCH_CONTEXT_MISMATCH_NOT_RUNTIME','ref':str(A/'DIAGNOSTICS.json'),'raw_tool_chunk':None,'status':'Author readback confirmed no partial change before the corrected C-only patch; retained, not reset.'}
 ],
 'counter_reset':False,'pending_operations':[],'uncertain_outcomes':[]
})
files=[]
for p in sorted(P.rglob('*')):
 if p.is_file() and p.name not in ['EVIDENCE-MANIFEST.json','archive-file-list.json']:
  files.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
put('EVIDENCE-MANIFEST.json',{'schema':'researchos.independent-review-evidence.v1','files':files})
put('archive-file-list.json',[v['path'] for v in files]+[str(R/'EVIDENCE-MANIFEST.json')])
print(json.dumps({name:sha(R/name) for name in ['report.json','EVIDENCE-MANIFEST.json','archive-file-list.json']}))
