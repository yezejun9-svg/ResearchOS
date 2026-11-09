"""Frozen wrapper source review and pure mock reproduction; no native main."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
from unittest import mock

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent.parent/'product_host_native_20261028'/'driver-v3'/'revision02'
OUT=ROOT/'revision02-efe3999d'
OUT.mkdir(exist_ok=False)
SNAP=OUT/'input-snapshots'
SNAP.mkdir()
def ref(p):
    raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
inputs=[]
for name in ('run-owned.py','lifecycle.mjs','choose-owned-folder.ps1','close-owned-window.ps1','test_postspawn_mock.py','PREPARATION.json'):
    raw=(SOURCE/name).read_bytes()
    (SNAP/name).write_bytes(raw)
    inputs.append(ref(SOURCE/name))
assert inputs[0]['sha256']=='efe3999de1f49979b61c6ecfa0e14d366799c231901756f46091925f64490571'
assert inputs[-1]['sha256']=='5e4b29ad1eb73e4146e6c7db0f7b038788164ca24814e3ca1bbdcfb7bedbb8ce'
v2=SOURCE.parent.parent/'driver-v2'
for name in ('lifecycle.mjs','choose-owned-folder.ps1','close-owned-window.ps1'):
    assert (SNAP/name).read_bytes()==(v2/name).read_bytes()
save('INPUTS.json',inputs)
ast.parse((SNAP/'run-owned.py').read_text(encoding='utf-8'))
argv=[sys.executable,'-B',str(SNAP/'test_postspawn_mock.py'),'-v']
result=subprocess.run(argv,capture_output=True,check=False)
(OUT/'pure-mocks.stdout.raw').write_bytes(result.stdout)
(OUT/'pure-mocks.stderr.raw').write_bytes(result.stderr)
save('PURE-MOCK-COMMAND.json',{'argv':argv,'exit':result.returncode,'product_processes_started':0,
    'stdout':ref(OUT/'pure-mocks.stdout.raw'),'stderr':ref(OUT/'pure-mocks.stderr.raw')})
assert result.returncode==0,result.stderr
g=runpy.run_path(str(SNAP/'run-owned.py'))
class Child:
    pid=1234
    def wait(self): return 0
class Stream:
    def close(self): pass
calls=[]
def writer(path,value):
    calls.append(path.name)
    if path.name=='exit.json': raise OSError('MOCK_EXIT_RECEIPT_FAILURE')
child=Child()
fg=g['observe_started_controller'].__globals__
with mock.patch.dict(fg,{'write_new':writer,'safe_print':lambda *a:None,
    'reference':lambda p:{'sha256':'mock','bytes':0},'hold_postspawn':lambda *a:('HELD',a[3],str(a[-1]))}):
    observed=g['observe_started_controller']({},OUT,OUT,child,{'pid':child.pid},(Stream(),Stream()),'scope',{}, {})
assert observed==('HELD',child,'MOCK_EXIT_RECEIPT_FAILURE')
save('INDEPENDENT-EXIT-RECEIPT-PROBE.json',{'status':'PASS','written_names':calls,
    'exit_receipt_error_reaches_hold_with_same_handle':True,'product_processes_started':0})
report={'schema':'researchos.independent-native-driver-v3-source-review.v2',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'DRIVER_V3_REVISION02_SOURCE_ACCEPTED_FOR_NEW_EXACT_BOUND_SCOPE',
    'driver_source_accepted':True,'fixed_driver_files':inputs,'findings':[],
    'actual_native_runs':0,'formal_increment':0,'product_acceptance':'NOT_ASSERTED',
    'resolved_findings':[
        'A1: scanner queries any bundled executable basename OR any known PID. Reused known PID and additional exact bundle image block release.',
        'A2: successful Popen is immediately stored in OWNED_CONTROLLER; remaining postspawn work is enclosed in persistent catch/hold paths preserving that handle. Spawn receipt, wait, stream-close and exit receipt failures all reach hold.',
        'Reconciliation remains bound to scope, wrapper/controller PIDs, controller exit SHA, nonce, exact known identity list and post-exit time; repeated clean scans required; unchanged lifecycle and WM_CLOSE/chooser helpers.'
    ],
    'evidence_refs':[ref(OUT/'INPUTS.json'),ref(OUT/'PURE-MOCK-COMMAND.json'),ref(OUT/'INDEPENDENT-EXIT-RECEIPT-PROBE.json')],
    'scope_requirements':['Bind these exact revision02 hashes and fresh owned roots; this source review itself grants no execution authority.','Use lifecycle-wrapper Root release schema researchos.native-driver-v3-root-release.v1, not chooser-diagnostic schema.'],
    'limitations':['Five author pure mocks reproduced plus independent exit-receipt-failure probe; no native launch, pipe, GUI, live CIM or actual outer host/job lifetime exercised.',
        'Corrupt/mismatched spawn or exit evidence, absent controller UNRESOLVED identity evidence, or unknown process identity deliberately blocks release indefinitely. Source acceptance is preservation/fail-closed, not proof every failure can be automatically reconciled.',
        'Normal controller exit0 bypasses failure release as before; product behavior and clean shutdown still require actual evidence.']}
save('REVIEW.json',report)
print(json.dumps(ref(OUT/'REVIEW.json'),ensure_ascii=False))
