import pathlib,json,hashlib,subprocess,datetime
E=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W17/W17-03/mu_m1_02_activation_admission_review_codex/20261014-current-chat');S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-core-20261014');ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
sha=lambda b:hashlib.sha256(b).hexdigest();files=[]
selected=['internal/domain/runtime_admission.go','internal/domain/runtime_dispatch.go','internal/domain/runtime_pause.go','internal/domain/runtime_pause_windows.go','internal/domain/runtime_coordinator_windows.go','internal/domain/contracts/runtime_pause_activations.sql','internal/domain/durability.go','spec/v2.0/03_DATA_CONTRACTS.md','spec/v2.0/07_OPERATIONS_AND_EVOLUTION.md','.local/m1-02/attempt-004-native.log']
for name in selected:
 p=S/name;data=p.read_bytes();o=E/'snapshot'/name;o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(data);files.append({'path':str(p),'evidence':o.relative_to(E).as_posix(),'sha256':sha(data),'bytes':len(data)})
for p,loc in [(pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-02-proposal-20261014/report.md'),'proposal-report.md'),(ROOT/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp469/mu-m1-02-source-scope-v2.json','cp469-source-scope-v2.json')]:
 b=p.read_bytes();(E/loc).write_bytes(b);files.append({'path':str(p),'evidence':loc,'sha256':sha(b),'bytes':len(b)})
r={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_head':subprocess.check_output(['git','-C',str(S),'rev-parse','HEAD']).decode().strip(),'source_status':subprocess.check_output(['git','-C',str(S),'status','--short']).decode(),'source_snapshot_only':True,'source_writes':False,'files':files}
(E/'review-inputs.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print('bound files',len(files))
