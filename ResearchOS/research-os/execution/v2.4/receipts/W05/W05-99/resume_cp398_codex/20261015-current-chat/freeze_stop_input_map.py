import datetime,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_input_map_codex/20261015-current-chat';E.mkdir(parents=True,exist_ok=False)
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
inputs=['ops/supervisor/release_process_windows.go','ops/supervisor/release_drain_windows.go','ops/supervisor/process_observation_windows_test.go','apps/control/main.go','internal/host/desktop_management_windows.go','internal/domain/runtime_drain_windows.go']
new(E/'input-hashes.json',{'schema':'researchos.owned-stop-input-map.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_commit':'4f4023c956f84d65743f39ce77d6c8899a21ada1','files':[ref(R/p) for p in inputs]})
body='''# Owned Core stop follow-up map

DISCOVERY_ONLY. No stop/helper fixture/actual signal/Source write is authorized by this note. The complete B/C/STOP architecture is under independent review at CP498. Original Core and Desktop continue running; prior PID observations are not current authority.

Existing ops/supervisor ObserveProcess obtains creation time through one transient handle and later image hash through a second transient handle. It returns PID/CreatedNS/ImageSHA256 only. It is useful observational input; an actual stop must open and retain ONE exact target handle, obtain identity and SID/path from that handle, validate the plan, signal only after native console census revalidation, then wait that same handle. Do not use ObserveProcess's PID observation alone as a stop capability.

release_process_windows.go already has bounded image hashing and no-reparse checks; exactImage is fixture launch policy with 128MiB bound, while observedProcessImageDigest supports a distinct 256MiB observation bound for Electron. Keep those purposes separate. NativeFixtureDriver uses CREATE_NEW_PROCESS_GROUP, which is not proof of a dedicated console or safe console-wide Ctrl-C target.

apps/control/main.go:220 subscribes to os.Interrupt. A separately reviewed helper can fixture-test AttachConsole + GetConsoleProcessList + one GenerateConsoleCtrlEvent(CTRL_C_EVENT,0) only when exact Core/helper are the only attached processes. Source and native fixture acceptance must establish behavior before any original Core action. A third process or unavailable console means zero signals. No automatic force fallback after timeout/unavailability.

The proposed stop can be an independent supervisor library and standalone helper, avoiding early control main flag overlap with C. Exact file/command/plan format remains undecided, requires revised Source scope and independent review. A controlled crash-stop, if needed, requires its own exact operation mode and reviewed plan, SQLite online consistent backup and committed/in-flight WAL fixture evidence; it must never be reported as graceful shutdown.

Original native worker closure and all external effect outcome proof are prerequisites. UNKNOWN money on a confirmed MODEL is separate from UNKNOWN effect outcome. Existing request/Run/effects/ledger and raw bridge/native receipts must remain append-only. Stop is only a means to obtain native DataRootLease for an official terminal-only maintenance command; it neither resolves nor retries the old Run.
'''
with (E/'STOP-INPUT-MAP.md').open('x',encoding='utf8') as f:f.write(body)
new(E/'diagnostic-ledger.json',{'schema':'researchos.root-readonly-diagnostics.v1','attempts':[{'origin_key':'20261015|root-stop-discovery-guessed-process-file-01','native_exit':0,'cmdlet_failure':True,'tool_chunk_id':'84e56c','operation':'Get-Content -LiteralPath ops/supervisor/process_windows.go after rg --files listed actual release_process_windows.go','error':'PowerShell nonterminating missing-path error; later successful read left overall command exit0. This is a preserved failed read, not PASS.','correction':'rg -n located ObserveProcess in release_drain_windows.go; exact discovered paths were then read successfully','source_or_actual_mutation':False}]})
new(E/'evidence-manifest.json',{'schema':'researchos.readonly-map-manifest.v1','status':'DISCOVERY_ONLY_NO_SOURCE_OR_ACTUAL_AUTHORITY','files':[ref(E/p) for p in ['STOP-INPUT-MAP.md','input-hashes.json','diagnostic-ledger.json']],'formal_increment':0})
print(json.dumps(ref(E/'evidence-manifest.json')))
