"""Read-only review of CP569 receipts. Writes only this review directory."""
import datetime
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
BASE=OUT.parent.parent
SCOPE=BASE/'resume_cp528_codex'/'20261025-current-chat'/'continuation-cp569'/'Owned-chooser-diagnostic-scope.json'
RECEIPTS=BASE/'product_host_native_20261028'/'native-init-diagnosis-02'/'execution-cp569-01'
SNAP=OUT/'initial-input-snapshots'
SNAP.mkdir(exist_ok=False)
def ref(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
assert ref(SCOPE)['sha256']=='5a9aed86237a69c78ae5932cd0645c085c033180276c3cf576c8be0111ef6668'
scope=json.loads(SCOPE.read_text(encoding='utf-8'))
refs=[]
paths=[SCOPE,*sorted(p for p in RECEIPTS.iterdir() if p.is_file())]
for path in paths:
    raw=path.read_bytes()
    target=SNAP/path.name
    target.write_bytes(raw)
    after=path.read_bytes()
    refs.append({'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                 'stable_on_second_read':raw==after,'snapshot':str(target)})
save('INITIAL-INPUTS.json',refs)
bindings=[]
for item in scope['bound_files']:
    actual=ref(Path(item['path']))
    assert actual['bytes']==item['bytes'] and actual['sha256']==item['sha256'],item['path']
    bindings.append(actual)
save('BOUND-FILES-VERIFIED.json',bindings)

worktree=Path(scope['worktree'])
source_refs=[]
for name in ('native_folder_windows.go','native_pipe_windows.go'):
    source=worktree/'internal'/'host'/name
    raw=source.read_bytes()
    (SNAP/name).write_bytes(raw)
    source_refs.append(ref(source))
save('INTERPRETATION-SOURCE-REFS.json',source_refs)
wait=json.loads((SNAP/'WAITING_FOR_ROOT.json').read_text(encoding='utf-8'))
witness_path=Path(scope['state_root'])/'LocalAppData'/'ResearchOS'/'data'/'product-supervisor.json'
if witness_path.exists():
    witness=json.loads(witness_path.read_text(encoding='utf-8'))
    save('CURRENT-WITNESS-OBSERVATION.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'exists':True,'path':str(witness_path),'value':witness,'ref':ref(witness_path)})
else:
    save('CURRENT-WITNESS-OBSERVATION.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'exists':False,'path':str(witness_path)})
reply=json.loads((SNAP/'native-reply.raw').read_bytes())
request=json.loads((SNAP/'native-request.raw').read_bytes())
exchange=json.loads((SNAP/'exchange-result.json').read_text(encoding='utf-8'))
assert reply['kind']=='NATIVE_ERROR' and reply['error']['message']=='INVALID_REQUEST: folder selection cancelled'
assert request['kind']=='NATIVE_WORKSPACE_CHOOSE_REQUEST'
assert exchange['client_exit']==1 and exchange['folder_exit']==1
assert wait['scope_sha256']==ref(SCOPE)['sha256']
save('INITIAL-REVIEW.json',{
    'schema':'researchos.independent-owned-chooser-execution-review.v1',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'RAW_DIAGNOSTIC_CAPTURED_CHOOSER_FAILED_CLOSE_UNRESOLVED',
    'native_chooser_success':False,'clean_close_accepted':False,'formal_increment':0,
    'reviewer_product_process_actions':0,'scope_ref':ref(SCOPE),
    'request':request,'raw_reply':reply,'exchange':exchange,
    'observed_facts':[
        'Raw reply is NATIVE_ERROR / INVALID_REQUEST / INVALID_REQUEST: folder selection cancelled.',
        'Folder confirmation helper exits1 with EXACT_OWNED_FOLDER_DIALOG_NOT_FOUND.',
        'Native client exits1 with PIPE_SERVER_CHANGED_AFTER_REPLY, after saving raw reply.',
        'Normal-close helper exits1 with EXACT_OWNED_PRODUCT_WINDOW_NOT_FOUND; no successful WM_CLOSE receipt exists.',
        'Controller31236 writes WAITING_FOR_ROOT with original scope SHA, exact known identity list and no retry/forced termination.'
    ],
    'source_interpretation':[
        'native_folder_windows.go emits this cancellation text when SHBrowseForFolderW returns selected==0; this does not identify user cancellation versus other native causes.',
        'native_pipe_windows.go flushes, disconnects and closes each pipe after serving one frame. Post-reply PID query failure is compatible with that normal disconnect.',
        'Diagnostic code merges GetNamedPipeServerProcessId false and mismatching PID into one error and did not retain GetLastWin32Error; an actual identity change cannot be concluded.'
    ],
    'inferences_not_confirmed':['SystemDrive omission causing relative shell caches or chooser failure','Native pipe query failing specifically because server disconnected','Mechanism of any subsequent process disappearance'],
    'remaining':['Root-only reconciliation of exact owned process identities','Independent final review of release/exit evidence if produced'],
    'evidence_refs':[ref(OUT/'INITIAL-INPUTS.json'),ref(OUT/'BOUND-FILES-VERIFIED.json'),ref(OUT/'INTERPRETATION-SOURCE-REFS.json'),ref(OUT/'CURRENT-WITNESS-OBSERVATION.json')]
})
print(json.dumps(ref(OUT/'INITIAL-REVIEW.json'),ensure_ascii=False))
