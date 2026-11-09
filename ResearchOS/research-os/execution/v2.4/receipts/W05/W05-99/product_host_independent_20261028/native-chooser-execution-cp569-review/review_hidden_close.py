"""Source-only boundary review of one Root-owned hidden-window WM_CLOSE."""
import ast, ctypes, datetime, hashlib, json
from ctypes import wintypes as w
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent.parent/'product_host_native_20261028'/'native-init-diagnosis-02'/'reconcile-cp569'/'preparation'
OUT=ROOT/'hidden-close-source-review'
OUT.mkdir(exist_ok=False)
def ref(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
inputs=[]
for name in ('close_hidden_owned.py','SCOPE.json'):
    raw=(SOURCE/name).read_bytes();(OUT/name).write_bytes(raw);inputs.append(ref(SOURCE/name))
assert inputs[0]['sha256']=='5dbafbffc6b773b1046a07647455c8910bb04c0243e9ac6aaf8c7490f45928b7'
assert inputs[1]['sha256']=='c13e7ef1151a71f2718464945f95ccda85fa5ffc66d7217f113ef3ade545861d'
ast.parse((OUT/'close_hidden_owned.py').read_text(encoding='utf-8'))
scope=json.loads((OUT/'SCOPE.json').read_text(encoding='utf-8'))
for row in scope['bound_files']:
    actual=ref(Path(row['path']))
    assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']
widths={name:ctypes.sizeof(typ) for name,typ in [('pointer',ctypes.c_void_p),('HANDLE',w.HANDLE),('HWND',w.HWND),('WPARAM',w.WPARAM),('LPARAM',w.LPARAM),('DWORD_PTR',ctypes.c_size_t)]}
assert len(set(widths.values()))==1 and widths['pointer']==8
save('REVIEW.json',{'schema':'researchos.independent-root-hidden-close-source-review.v1',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'SOURCE_ACCEPTED_FOR_EXACT_CP569_ROOT_RECONCILIATION_ONLY','source_accepted':True,
    'fixed_inputs':inputs,'pointer_widths':widths,'findings':[],
    'checks':['No code executed: Python AST parse and binding hashes verified; local ctypes widths all64bit.',
        'OpenProcess returns HANDLE and uses only QUERY_LIMITED_INFORMATION|SYNCHRONIZE. Pointer arguments for FILETIME/image-buffer/size and exit-code are declared; default C int return is appropriate for BOOL APIs.',
        'EnumWindows callback uses HWND/LPARAM pointer-width types; SendMessageTimeoutW HWND/WPARAM/LPARAM/result pointer and LRESULT return are declared correctly.',
        'Both exact process identities checked by creation time/image/hash and live handles. Enumerated singleton title/class/PID and exact observed HWND1183294 are checked; hidden visibility is recorded without show/hide mutation.',
        'PID and live handles checked again before single WM_CLOSE with5second SendMessageTimeout; no retry or force terminate.',
        'Success requires retained original Electron/Core process handles signalled with exit0 and witness absence; any incomplete close remains unresolved and does not alter original diagnostic failure.'],
    'operational_requirements':['Root keeps original controller31236/session90789 alive throughout; this short reconciliation helper does not replace its hold mechanism.',
        'Invoke plain Python without -O/PYTHONOPTIMIZE; scope/hash must remain exact; no re-run if the WM_CLOSE outcome is uncertain.'],
    'limitations':['Source review only; no WM_CLOSE or process action executed by reviewer.','normal-close-message.last_error may be stale when sent=true; do not interpret it as a failure unless sent=false.'],
    'actual_native_actions':0,'formal_increment':0})
print(json.dumps(ref(OUT/'REVIEW.json'),ensure_ascii=False))
