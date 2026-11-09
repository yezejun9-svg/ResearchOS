import datetime, hashlib, json, pathlib, subprocess, sys
ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).resolve().parent
BASE = ROOT/'execution/v2.4/receipts/W05/W05-99'
OLD = BASE/'approved_combined_desktop_build_codex/20261012-current-chat'
PKG = pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-first-use-combined-c381-20261012')
CTRL = PKG/'apps/desktop/resources/control'
SCOPE = BASE/'resume_cp398_codex/20261012-current-chat/continuation-cp440/qualification-authority-read-lane-source-scope.json'
SPEC = ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p): return {'path':p.as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def put(name,v):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def run(name,argv):
    p=subprocess.run(argv,cwd=ROOT,capture_output=True)
    (OUT/(name+'.stdout.raw')).write_bytes(p.stdout);(OUT/(name+'.stderr.raw')).write_bytes(p.stderr)
    put(name+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'exit':p.returncode})
    return p
files=[SCOPE,ROOT/'AGENTS.md',ROOT/'execution/v2.4/current_spec.json',ROOT/'execution/v2.4/step_state.json',SPEC/'tools/task_packet.py',SPEC/'contracts/execution.plan.json',ROOT/'apps/desktop/build-validator.py',ROOT/'apps/desktop/main/main.js',ROOT/'apps/desktop/main/lib/ipc.js',ROOT/'apps/desktop/main/lib/desktop-management.js',ROOT/'internal/domain/runtime_qualification_execution_windows.go',ROOT/'internal/domain/runtime_qualification_confirmation_windows.go',ROOT/'internal/host/runtime_verifier_process_windows.go',ROOT/'internal/host/runtime_qualification_windows.go']
files += [OLD/n for n in ['manifest.json','correction-01.json','manifest-supplement-01.json','composition.json']]
files += [BASE/'normal_qualification_actual_preflight_review_codex/20261012-current-chat'/n for n in ['report.json','evidence-matrix.json']]
files += [BASE/'qualification_read_lane_scope_assessment_codex/20261012-current-chat/report.json']
files += [BASE/'approved_combined_desktop_root_preflight_codex/20261012-current-chat'/n for n in ['researchos-control.exe.go-version-m.raw','runtime-verifier.exe.go-version-m.raw','installer-acl-readonly.json']]
files += [CTRL/n for n in ['researchos-control.exe','runtime-verifier.exe','runtime-verifier-installation.json','runtime/mu-worker.mjs','runtime/mu-worker.mjs.build.json','runtime/node.exe']]
files += [PKG/'apps/desktop/resources/client-wire/descriptor.json',PKG/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe']
before=[row(p) for p in files]
put('inputs.before.json',before)
git=run('git-identity',['git','rev-parse','HEAD','HEAD^{tree}'])
packet=run('task-packet-next',[sys.executable,'-X','utf8',str(SPEC/'tools/task_packet.py'),'--plan',str(SPEC/'contracts/execution.plan.json'),'next','--state',str(ROOT/'execution/v2.4/step_state.json')])
packet_data=json.loads(packet.stdout) if packet.returncode in [0,3] else {}
acl_script="$p='"+str(CTRL/'runtime-verifier-installation.json')+"';$a=Get-Acl -LiteralPath $p;[pscustomobject]@{owner=$a.Owner;owner_sid=$a.GetOwner([System.Security.Principal.SecurityIdentifier]).Value;protected=$a.AreAccessRulesProtected;rules=@($a.Access|ForEach-Object{[pscustomobject]@{sid=$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value;rights=$_.FileSystemRights.ToString();type=$_.AccessControlType.ToString();inherited=$_.IsInherited}})}|ConvertTo-Json -Depth 5"
acl=run('installer-acl',['powershell','-NoProfile','-Command',acl_script])
acl_data=json.loads(acl.stdout.decode('utf-8-sig',errors='replace')) if acl.returncode==0 else {}
ident=git.stdout.decode().strip().splitlines()
desc=read(PKG/'apps/desktop/resources/client-wire/descriptor.json')
check={
 'scope_sha_matches':sha(SCOPE)=='f83c964c67118aed5f7164519ac96b3bb0c33f46d61df047894a265235815a46',
 'head_matches':ident==['c381cf0d8e8f3ae2bcd437a6e0866b38d7bd9ec0','2936ca3097bc2c2d6cd6fd2e9af40756d25d32f8'],
 'control_hash_matches':sha(CTRL/'researchos-control.exe')=='326f70d5d9097d6f648bc4479a1e9a609c8969f1052a74ff13ddb93f550487a3',
 'verifier_hash_matches':sha(CTRL/'runtime-verifier.exe')=='28ea9cc1af6d7b7bbe96765b19b17e6ac08f77ac9e89dc781407b023910aa9eb',
 'old_descriptor_matches':sha(PKG/'apps/desktop/resources/client-wire/descriptor.json')=='ae09e01e93dee8541fb853d8a81902666cdac8ddc3bfed2c89eed6f544bbfece',
 'old_validator_matches':sha(PKG/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')==desc['binary_sha256'],
 'task_packet_validated':packet_data.get('state_source')=='VALIDATED_FILE',
 'spec_plan_matches':sha(SPEC/'contracts/execution.plan.json')==read(ROOT/'execution/v2.4/current_spec.json')['plan_sha256'],
 'old_installer_acl_protected_owner_only':acl_data.get('protected') is True and len(acl_data.get('rules',[]))==1 and acl_data['rules'][0]['sid']==acl_data.get('owner_sid') and acl_data['rules'][0]['type']=='Allow' and acl_data['rules'][0]['rights']=='FullControl' and not acl_data['rules'][0]['inherited'],
}
after=[{**x,'current_sha256':sha(pathlib.Path(x['path']))} for x in before]
drift=[x for x in after if x['sha256']!=x['current_sha256']]
put('inputs.after.json',after)
put('observations.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':check,'input_drift':drift,'head':ident,'task_packet_exit':packet.returncode,'task_packet_state_source':packet_data.get('state_source'),'next_step':packet_data.get('step',{}).get('id'),'acl':acl_data,'package':'OLD APPROVED PACKAGE ONLY; no new candidate inspected','product_launches':0,'model_calls':0,'external_tool_calls':0,'real_sqlite_reads':0,'source_or_canon_writes':0})
print(json.dumps({'checks':check,'drift_count':len(drift),'task_packet_exit':packet.returncode},ensure_ascii=False))
