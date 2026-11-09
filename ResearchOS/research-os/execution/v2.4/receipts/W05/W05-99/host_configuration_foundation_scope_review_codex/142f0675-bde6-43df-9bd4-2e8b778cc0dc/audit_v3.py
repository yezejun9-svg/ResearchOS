from pathlib import Path
import json,hashlib,datetime,subprocess
ROOT=Path('D:/作品集/ResearchOS/research-os');D=Path(__file__).resolve().parent;P=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_executor_codex/f09f49c581cd4bed83f3f474ae5c5077'
sh=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=json.loads((P/'source_inputs.before.json').read_bytes());a=json.loads((P/'source_inputs.after.json').read_bytes());m=json.loads((P/'manifest.json').read_bytes());proposal=json.loads((P/'proposal.json').read_bytes())
inputs=[{**x,'actual_source_sha256':sh(ROOT/x['path']),'actual_snapshot_sha256':sh(ROOT/x['snapshot']['path'])} for x in v];manifest=[{**x,'actual_sha256':sh(ROOT/x['path'])} for x in m['files']]
sc=json.loads((ROOT/'.local/worktrees/v24-continuation/spec/v2.4/contracts/client.protocol.schema.json').read_bytes());extract=json.loads((P/'frozen_contract_extract.json').read_bytes())
assert all(extract[k]==sc['$defs'][k] for k in extract)
expected={'proposal.json':'8de0a27ada92af37e651057da9199bd4b42de1c68e9fb58bb6c76882f4cafbe6','handoff.json':'3d0d1e925ab2dedcb62eaad59b297cd3b1e815bae7f160cc085f185ac1d937aa','manifest.json':'ca8e93fc9fbf23a0f90c6b5d3e6aacfb06155b89910d0c6e9b49ed823f4e276b'}
assert all(sh(P/k)==h for k,h in expected.items())
print(json.dumps({'counts':[len(v),len(a)],'equal':v==a,'drift':[x['path'] for x in inputs if x['sha256']!=x['actual_source_sha256'] or x['sha256']!=x['actual_snapshot_sha256']],'manifestdrift':[x['path'] for x in manifest if x['sha256']!=x['actual_sha256']]})); assert len(v)==55 and [{k:x[k] for k in ('path','sha256')} for x in v]==[{k:x[k] for k in ('path','sha256')} for x in a] and all(x['sha256']==x['actual_source_sha256']==x['actual_snapshot_sha256'] for x in inputs) and all(x['sha256']==x['actual_sha256'] for x in manifest)
new=[{'path':x['path'],'main_exists':(ROOT/x['path']).exists()} for x in proposal['exact_proposed_source_paths']];assert all(not x['main_exists'] for x in new)
r={'schema':'researchos.independent.read-audit.v1','reviewer_id':'codex:/root/w05_merge_review','read_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head_observed':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'input_count':55,'before_after_path_hash_equal':True,'current_and_snapshot_equal':True,'inputs':inputs,'manifest_count':len(manifest),'manifest':manifest,'root_refs':[{'path':str(P/k),'sha256':h} for k,h in expected.items()],'frozen_extract_recomputed_equal':True,'new_sources_absent':new,'read_only':True,'tests_run':False,'credentials_or_database_read':False}
(D/'read_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'audit_sha256':sh(D/'read_audit.json'),'manifest_entries':len(manifest)}))


