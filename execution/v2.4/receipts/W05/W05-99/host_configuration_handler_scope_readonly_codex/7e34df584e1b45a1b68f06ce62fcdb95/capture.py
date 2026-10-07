import datetime, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path(r'D:/作品集/ResearchOS/research-os')
WT=ROOT/'.local/worktrees/codex-w0599-host-configuration-upgrade'
OUT=Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def save(name,obj):
    with (OUT/name).open('xb') as f: f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def ref(p):
    b=p.read_bytes(); return {'path':str(p),'sha256':sha(b),'bytes':len(b)}
mapping=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-handler-readonly-r270'
old=json.loads((mapping/'source_before.json').read_bytes())
paths=list(map(Path,old))
main=['AGENTS.md','execution/project_identity.json','internal/api/server.go','apps/control/main.go','internal/host/surface.go','internal/host/vault.go','internal/host/native.go','internal/domain/runtime_model.go','internal/domain/runtime_coordinator_windows.go','internal/domain/client_command_queue.go','internal/domain/client_protocol_control.go','apps/cli/cli_contract.go','apps/cli/cli_v2.go','apps/desktop/main/lib/v2.js','apps/desktop/main/lib/first-use.js','apps/web/src/v2client.js','apps/web/src/workbench.jsx','apps/web/src/continuity.jsx','.local/worktrees/v24-continuation/spec/v2.4/19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md','.local/worktrees/v24-continuation/spec/v2.4/contracts/client.protocol.schema.json','.local/worktrees/v24-continuation/spec/v2.4/contracts/domain.schema.json','internal/domain/backup_upgrade_test.go']
paths += [ROOT/p for p in main]
paths += [mapping/p for p in ['source_before.json','source_after.json','read_mapping.json']]
paths += [ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-schema-mirror-scope-r271/scope_registration.json']
candidate=['internal/domain/backup_upgrade.go','internal/domain/backup_migration.go','internal/domain/backup.go','internal/domain/store.go','internal/domain/backup_configuration_upgrade.go','internal/domain/backup_configuration_upgrade_test.go','internal/domain/backup_host_configuration.go','internal/domain/backup_host_configuration_test.go','internal/domain/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.domain.schema.json','internal/domain/client_configuration_test.go','internal/domain/client_command_identity_test.go']
paths += [WT/p for p in candidate]
paths += [ROOT/'execution/v2.4/receipts/W05/W05-99/resume_review_codex/historical_fixture_source_review_2ba70c50-03f2-4a3a-b0c4-0a21ed85e2c0/review.json']
rows=[]; missing=[]; (OUT/'snapshots').mkdir()
for p in dict.fromkeys(paths):
    if not p.is_file(): missing.append(str(p)); continue
    b=p.read_bytes(); copy=OUT/'snapshots'/f'{len(rows):03d}-{p.name}.txt'; copy.write_bytes(b)
    rows.append({'path':str(p),'sha256':sha(b),'bytes':len(b),'snapshot':str(copy.relative_to(OUT)),'immediate_second_sha256':sha(p.read_bytes()),'old_mapping_sha256':old.get(str(p))})
save('inputs.before.json',rows); save('missing_inputs.json',missing)
save('prior_mapping_comparison.json',[{'path':p,'old_sha256':v,'current_sha256':sha(Path(p).read_bytes()),'same':v==sha(Path(p).read_bytes())} for p,v in old.items()])
commands=[]
for tag,cwd,argv in [('main-head',ROOT,['git','rev-parse','HEAD']),('candidate-head',WT,['git','rev-parse','HEAD']),('candidate-status',WT,['git','status','--porcelain','--untracked-files=no']),('legacy-buildinfo',ROOT,[str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe'),'version','-m',str(ROOT/'.local/bin/researchos-remote.exe')])]:
    start=datetime.datetime.now(datetime.timezone.utc).isoformat(); r=subprocess.run(argv,cwd=cwd,capture_output=True)
    (OUT/(tag+'.stdout.raw')).write_bytes(r.stdout); (OUT/(tag+'.stderr.raw')).write_bytes(r.stderr)
    commands.append({'argv':argv,'cwd':str(cwd),'start':start,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':r.returncode,'stdout':ref(OUT/(tag+'.stdout.raw')),'stderr':ref(OUT/(tag+'.stderr.raw'))})
save('read_invocations.json',commands)
save('legacy_resource_recheck.json',{'artifact':ref(ROOT/'.local/bin/researchos-remote.exe'),'expected_sha256':'aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032','review':ref(paths[-1]),'environment_selector':'RESEARCHOS_HISTORICAL_SCHEMA14_CONTROL','artifact_executed':False,'rebuilt':False,'buildinfo_only':True})
protocol=json.loads((ROOT/'internal/api/contracts/client.protocol.schema.json').read_bytes()); defs=protocol['$defs']
save('frozen_contract_extract.json',{'schema':ref(ROOT/'internal/api/contracts/client.protocol.schema.json'),'method':protocol['x-method-contracts']['host.configure'],'defs':{k:defs[k] for k in ['ConfigurePayload','ConfigureResult','HostStatusResult','CreateSessionPayload','SessionSnapshot','ModelConfiguration','CredentialSummary'] if k in defs}})
save('capture_result.json',{'input_count':len(rows),'missing':missing,'immediate_drift':[r['path'] for r in rows if r['sha256']!=r['immediate_second_sha256']],'source_edits':0,'private_resource_reads':0,'network_calls':0})
print(json.dumps({'out':str(OUT),'inputs':len(rows),'missing':missing}))
