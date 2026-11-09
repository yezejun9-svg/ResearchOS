"""Independent frozen environment helper source review; no helper/native execution."""
import ast,datetime,hashlib,json,re,runpy
from pathlib import Path
from unittest import mock

OUT=Path(__file__).resolve().parent
BASE=OUT.parent.parent
PREP=BASE/'product_host_native_20261028'/'native-init-diagnosis-02'/'environment-probe'/'preparation01'
SCOPE=BASE/'resume_cp528_codex'/'20261025-current-chat'/'continuation-cp570'/'Native-folder-environment-preparation-scope.json'
SNAP=OUT/'preparation01-input-snapshots'
SNAP.mkdir(exist_ok=False)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
prep=json.loads((PREP/'PREPARATION.json').read_text(encoding='utf-8'))
scope=json.loads(SCOPE.read_text(encoding='utf-8'))
assert ref(SCOPE)['sha256']=='433ea19532a2804e3d9fb8666561f227e42cd30e08aec48f2e4cc9c97cf9e792'
assert ref(PREP/'PREPARATION.json')['sha256']=='22ef3e57580307f88607886ebf8b724dc4a5082ca7fc16294151736b79a229bf'
assert ref(PREP/'controller.py')['sha256']=='c73c1631455c2dc6a52b57fdc72ec5936dd5b0dd819a6ea481bc1d7519bff6bc'
refs=[]
for name in ('PREPARATION.json','controller.py','RUN-SCOPE-TEMPLATE.json','REPORT.md'):
    p=PREP/name;(SNAP/name).write_bytes(p.read_bytes());refs.append(ref(p))
for label,row in prep['files'].items():
    p=Path(row['path']);actual=ref(p)
    assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']
    if label in ('source','transformed','main'):(SNAP/(label+'-'+p.name)).write_bytes(p.read_bytes())
    refs.append(actual)
source=Path(prep['files']['source']['path']).read_bytes()
transformed=Path(prep['files']['transformed']['path']).read_bytes()
assert source.count(b'package host')==1
assert transformed==source.replace(b'package host',b'package main',1)
main=Path(prep['files']['main']['path']).read_text(encoding='utf-8')
assert main.count('chooseNativeFolderWindows(')==1
assert 'errors.New("INVALID_REQUEST")' in main
management=Path(scope['management_ref']['path'])
assert ref(management)['sha256']==scope['management_ref']['sha256']
management_source=management.read_text(encoding='utf-8')
assert "['SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA']" in management_source
(SNAP/'desktop-management.js').write_bytes(management.read_bytes())
refs.append(ref(management))
save('PREPARATION01-INPUTS.json',refs)
ast.parse((PREP/'controller.py').read_text(encoding='utf-8'))
g=runpy.run_path(str(PREP/'controller.py'))
class FakeChild:
    pid=1234
    def poll(self):return None
    def wait(self):raise AssertionError('must not wait in this probe')
escaped=False
fg=g['unresolved_hold'].__globals__
with mock.patch.dict(fg,{'save':lambda *a,**k:(_ for _ in ()).throw(OSError('MOCK_RECEIPT_IO_FAILURE'))}):
    try:g['unresolved_hold'](OUT,'scope',FakeChild(),RuntimeError('initial failure'))
    except OSError as error:
        escaped=True;message=str(error)
assert escaped and message=='MOCK_RECEIPT_IO_FAILURE'
save('PREPARATION01-PURE-PROBE.json',{'status':'FAILURE_REPRODUCED','case':'hold receipt I/O failure',
    'helper_mock_alive':True,'unresolved_hold_escaped':True,'exception':message,'actual_helper_runs':0,'actual_native_runs':0})
save('PREPARATION01-REVIEW.json',{
    'schema':'researchos.independent-native-folder-environment-preparation-review.v1',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'NEEDS_REVISION_BEFORE_NATIVE_SCOPE','controller_source_accepted':False,
    'chooser_source_fidelity_accepted':True,'build_provenance_accepted':False,
    'actual_native_runs':0,'actual_helper_runs':0,'formal_increment':0,
    'verified':['All supplied file lengths and SHA256 values match frozen preparation manifest.',
        'Copied chooser is exactly original bytes with sole package host to package main replacement; main has one chooser call and matching INVALID_REQUEST sentinel.',
        'A uses actual frozen Core seven-key Windows allowlist; B is dict(A) plus verified SystemDrive only. Same hint/state paths and SW_HIDE startup requested.',
        'Fixed A/B loop contains one process launch per case, no automatic retry; explicit error branches abort sequence.',
        'Owned dialog cancellation filters exact PID, class, visibility/rectangle; retained process handle creation-time and fresh HWND rechecked before one WM_COMMAND/IDCANCEL.',
        'Run preflight requires Root authorization, exact preparation/controller/helper hashes, candidate commit/clean worktree, fresh bounded roots; template remains unauthorized.'],
    'findings':[
        {'id':'E1','priority':1,'file':str(PREP/'controller.py'),'symbol':'unresolved_hold / run_case except',
         'issue':'Both initial save calls precede the protected hold loop. A receipt I/O error escapes unresolved_hold while the mocked helper remains live; run_case then unwinds and main exits. The error-handling sleep can also be interrupted outside a persistent boundary.',
         'required':'Enclose every post-Popen failure in an outer persistent guard retaining the same child; make reporting and sleeps best-effort; Root release plus natural terminal evidence required for release, with no kill/retry.'},
        {'id':'E2','priority':2,'file':str(PREP/'PREPARATION.json'),'symbol':'offline_build_args / checks',
         'issue':'Build evidence currently contains only declared args/toolchain path and boolean success; no captured command/cwd/environment/exit/stdout/stderr or pinned go.mod/go.sum/toolchain identity for recomputation.',
         'required':'Append a fresh source/build preparation revision with raw offline build receipt and exact module/toolchain refs; independently verify or reproduce binary build before accepting build provenance.'}
    ],
    'limitations':['No binary was executed or rebuilt in this first review; helper hash verified only.','A/B share state and fixed ordering, so differential behavior is diagnostic evidence, not automatic proof of product causality; any A2 remains separately scoped.','Direct helper observation cannot be accepted as successful product/native workspace flow.'],
    'evidence_refs':[ref(OUT/'PREPARATION01-INPUTS.json'),ref(OUT/'PREPARATION01-PURE-PROBE.json')]
})
print(json.dumps(ref(OUT/'PREPARATION01-REVIEW.json'),ensure_ascii=False))
